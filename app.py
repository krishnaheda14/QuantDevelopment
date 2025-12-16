"""Main FastAPI application - orchestrates all components."""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import uvicorn

# Import configuration
from config import config, logger

# Import components
from src.storage.redis_manager import RedisManager
from src.storage.database import Database
from src.storage.data_sampler import DataSampler
from src.ingestion.websocket_client import BinanceWebSocketClient
from src.ingestion.data_processor import DataProcessor
from src.api.endpoints import router, init_endpoints
from src.api.websocket_handler import websocket_endpoint
from src.alerting.alert_manager import AlertManager
from src.alerting.alert_rules import DEFAULT_RULES

# Global components
redis_manager = None
database = None
data_sampler = None
ws_client = None
data_processor = None
alert_manager = None
ws_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global redis_manager, database, data_sampler, ws_client, data_processor, alert_manager, ws_task
    
    logger.info("=" * 60)
    logger.info("GEMSCAP QUANT PROJECT - Starting up...")
    logger.info("=" * 60)
    
    try:
        # 1. Initialize Redis
        logger.info("📡 Initializing Redis...")
        redis_manager = RedisManager(config.redis_url)
        await redis_manager.connect()
        
        # 2. Initialize Database
        logger.info("💾 Initializing Database...")
        database = Database(config.sqlite_path)
        await database.connect()
        
        # 3. Initialize Data Processor
        logger.info("⚙️  Initializing Data Processor...")
        data_processor = DataProcessor(redis_manager)
        
        # 4. Initialize WebSocket Client
        logger.info("🌐 Initializing Binance WebSocket Client...")
        
        async def tick_callback(tick):
            """Callback for incoming ticks."""
            await data_processor.process_tick(tick)
        
        ws_client = BinanceWebSocketClient(
            symbols=config.symbols,
            base_url=config.binance_ws_url,
            mode=config.binance_mode,
            callback=tick_callback
        )
        
        # Start WebSocket in background
        ws_task = asyncio.create_task(ws_client.run())
        
        # 5. Initialize Data Sampler
        logger.info("📊 Starting Data Sampler...")
        data_sampler = DataSampler(redis_manager, database, config.symbols)
        data_sampler.start()
        
        # 6. Initialize Alert Manager
        logger.info("🚨 Starting Alert Manager...")
        alert_manager = AlertManager(redis_manager, database, DEFAULT_RULES)
        alert_manager.start(config.alert_check_interval)
        
        # 7. Initialize API Endpoints
        logger.info("🔌 Initializing API Endpoints...")
        init_endpoints(redis_manager, database, None)
        
        logger.info("=" * 60)
        logger.info("✅ All components initialized successfully!")
        logger.info(f"📡 API Server: http://localhost:{config.api_port}")
        logger.info(f"📊 Streamlit Dashboard: http://localhost:{config.streamlit_port}")
        logger.info(f"🎯 Symbols: {', '.join(config.symbols)}")
        logger.info("=" * 60)
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down...")
        
        if ws_client:
            ws_client.stop()
        
        if ws_task:
            ws_task.cancel()
            try:
                await ws_task
            except asyncio.CancelledError:
                pass
        
        if data_sampler:
            data_sampler.stop()
        
        if alert_manager:
            alert_manager.stop()
        
        if redis_manager:
            await redis_manager.close()
        
        if database:
            await database.close()
        
        logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="GEMSCAP Quant API",
    description="Real-time quantitative analytics system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# WebSocket endpoint
@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket_endpoint(websocket)


# Debug endpoints
@app.get("/debug/system")
async def debug_system():
    """Get system-wide debug information."""
    components = {}

    # Wrap each call to ensure non-serializable objects are converted to safe representations
    try:
        if redis_manager:
            components["redis"] = await redis_manager.health_check()
    except Exception as e:
        components["redis"] = {"error": str(e)}

    try:
        if database:
            components["database"] = await database.health_check()
    except Exception as e:
        components["database"] = {"error": str(e)}

    try:
        if ws_client:
            components["websocket"] = ws_client.get_stats()
    except Exception as e:
        components["websocket"] = {"error": str(e)}

    try:
        if data_processor:
            components["data_processor"] = data_processor.get_stats()
    except Exception as e:
        components["data_processor"] = {"error": str(e)}

    try:
        if data_sampler:
            components["data_sampler"] = data_sampler.get_stats()
    except Exception as e:
        components["data_sampler"] = {"error": str(e)}

    try:
        if alert_manager:
            components["alert_manager"] = alert_manager.get_stats()
    except Exception as e:
        components["alert_manager"] = {"error": str(e)}

    payload = {
        "status": "running",
        "config": {
            "symbols": config.symbols,
            "intervals": config.sampling_intervals,
            "api_port": config.api_port,
            "binance_mode": config.binance_mode,
            "binance_ws_url": config.binance_ws_url
        },
        "components": components
    }

    # Ensure the response is JSON-serializable (converts numpy types, etc.)
    return jsonable_encoder(payload)


@app.get("/debug/diagnostics")
async def debug_diagnostics():
    """Comprehensive diagnostics endpoint."""
    diagnostics = {}
    
    # Redis diagnostics
    try:
        if redis_manager:
            diag = await redis_manager.health_check()
            # Get sample data
            sample_ticks = {}
            for symbol in config.symbols:
                try:
                    ticks = await redis_manager.get_recent_ticks(symbol, 5)
                    sample_ticks[symbol] = {"count": len(ticks), "sample": ticks[:2] if ticks else []}
                except Exception as e:
                    sample_ticks[symbol] = {"error": str(e)}
            diag["sample_data"] = sample_ticks
            diagnostics["redis"] = diag
    except Exception as e:
        diagnostics["redis"] = {"error": str(e)}
    
    # Database diagnostics
    try:
        if database:
            diag = await database.health_check()
            table_counts = await database.get_table_counts()
            diag["table_counts"] = table_counts
            diagnostics["database"] = diag
    except Exception as e:
        diagnostics["database"] = {"error": str(e)}
    
    # WebSocket diagnostics
    try:
        if ws_client:
            stats = ws_client.get_stats()
            diagnostics["websocket"] = stats
    except Exception as e:
        diagnostics["websocket"] = {"error": str(e)}
    
    # Data flow diagnostics
    try:
        if data_processor:
            diagnostics["data_processor"] = data_processor.get_stats()
    except Exception as e:
        diagnostics["data_processor"] = {"error": str(e)}
    
    return jsonable_encoder(diagnostics)


@app.get("/debug/redis/{symbol}")
async def debug_redis_symbol(symbol: str):
    """Debug Redis data for a symbol."""
    if not redis_manager:
        return {"error": "Redis not initialized"}
    
    ticks = await redis_manager.get_recent_ticks(symbol, 10)
    ohlc_1m = await redis_manager.get_ohlc(symbol, "1m", 10)
    
    return {
        "symbol": symbol,
        "recent_ticks": ticks,
        "ohlc_1m": ohlc_1m
    }


@app.get("/debug/db/tables")
async def debug_db_tables():
    """Debug database table counts."""
    if not database:
        return {"error": "Database not initialized"}
    
    counts = await database.get_table_counts()
    
    return {
        "table_counts": counts
    }


def main():
    """Run the application."""
    uvicorn.run(
        "app:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.verbose,
        log_level="info"
    )


if __name__ == "__main__":
    main()
