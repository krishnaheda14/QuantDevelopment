"""
GEMSCAP Quantitative Trading Backend - FastAPI
Real-time analytics pipeline with WebSocket + REST APIs
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
import asyncio
import json
import redis.asyncio as aioredis
from datetime import datetime
from time import time
import logging
import socketio

from .api import analytics, alerts, export, debug
from .services.data_ingestion import DataIngestionService
from .services.sampling_engine import SamplingEngine
from .services.alert_engine import AlertEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="GEMSCAP Quant Backend",
    description="Real-time crypto pairs trading analytics",
    version="2.0.0"
)


# HTTP request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"HTTP {request.method} {request.url.path} - query={dict(request.query_params)}")
    try:
        response = await call_next(request)
        logger.info(f"HTTP {request.method} {request.url.path} - status={response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"Unhandled error processing {request.method} {request.url.path}: {e}")
        raise
# CORS for frontend (React + Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8501",  # Streamlit
        "http://localhost:8502",  # Streamlit alt
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services (initialized on startup)
redis_client: Optional[aioredis.Redis] = None
data_service: Optional[DataIngestionService] = None
sampling_service: Optional[SamplingEngine] = None
alert_service: Optional[AlertEngine] = None

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Socket.IO server for real-time communication
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global redis_client, data_service, sampling_service, alert_service
    
    logger.info("🚀 Starting GEMSCAP Backend Services...")
    
    # Connect to Redis
    try:
        redis_client = await aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.info("💡 Starting in-memory fallback mode...")
        redis_client = None
    
    # Initialize services
    data_service = DataIngestionService(redis_client)
    sampling_service = SamplingEngine(redis_client)
    alert_service = AlertEngine(redis_client)
    
    # Start background tasks
    asyncio.create_task(data_service.start_ingestion())
    asyncio.create_task(sampling_service.start_sampling())
    asyncio.create_task(alert_service.start_monitoring())
    
    logger.info("✅ All services started")
    
    # Start Socket.IO background tasks
    app_start_ts = time()
    globals()['app_start_ts'] = app_start_ts
    asyncio.create_task(broadcast_pubsub_data())
    asyncio.create_task(broadcast_market_data())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down services...")
    
    if data_service:
        await data_service.stop()
    if sampling_service:
        await sampling_service.stop()
    if alert_service:
        await alert_service.stop()
    if redis_client:
        await redis_client.close()
    
    logger.info("✅ Cleanup complete")


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "GEMSCAP Quant Backend",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/symbols")
async def get_symbols():
    """Get list of available trading symbols"""
    try:
        if data_service and hasattr(data_service, 'get_active_symbols'):
            symbols = data_service.get_active_symbols()
            if asyncio.iscoroutine(symbols):
                symbols = await symbols
            logger.info(f"Returning {len(symbols)} symbols")
            return symbols
        else:
            # Fallback default symbols
            default_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            logger.warning(f"Data service unavailable, returning default symbols: {default_symbols}")
            return default_symbols
    except Exception as e:
        logger.exception(f"Error fetching symbols: {e}")
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]


@app.get("/api/symbols")
async def get_symbols_api():
    """Get list of available trading symbols (with /api prefix)"""
    return await get_symbols()


@app.get("/health")
async def health_check():
    """Detailed health check"""
    redis_status = "connected"
    db_connected = False
    try:
        if redis_client:
            await redis_client.ping()
            db_connected = True
        else:
            redis_status = "fallback_mode"
    except Exception:
        redis_status = "disconnected"

    websocket_connections = len(active_connections)
    socketio_connections = 0
    try:
        if hasattr(sio, 'manager') and getattr(sio, 'manager') is not None:
            # manager.rooms is a dict of rooms; count non-empty
            socketio_connections = sum(len(r) for r in sio.manager.rooms.values()) if isinstance(sio.manager.rooms, dict) else 0
    except Exception:
        socketio_connections = 0

    # Try to infer metrics
    ticks_stored = 0
    ohlc_bars = 0
    try:
        if redis_client:
            # total keys approximate; may include other keys
            ticks_stored = await redis_client.dbsize()
    except Exception:
        ticks_stored = 0

    active_symbols_count = 0
    try:
        if data_service and hasattr(data_service, 'get_active_symbols'):
            syms = data_service.get_active_symbols()
            # support sync or async
            if asyncio.iscoroutine(syms):
                syms = await syms
            active_symbols_count = len(syms) if syms else 0
    except Exception:
        active_symbols_count = 0

    result = {
        "status": "healthy",
        "database": db_connected,
        "redis": redis_status,
        "services": {
            "data_ingestion": data_service is not None and data_service.is_running(),
            "sampling_engine": sampling_service is not None and sampling_service.is_running(),
            "alert_engine": alert_service is not None and alert_service.is_running()
        },
        "websocket": websocket_connections > 0 or socketio_connections > 0,
        "websocket_connections": websocket_connections,
        "socketio_connections": socketio_connections,
        "ticks_stored": ticks_stored,
        "ohlc_bars": ohlc_bars,
        "active_symbols": active_symbols_count,
        "timestamp": datetime.now().isoformat()
    }

    logger.debug(f"Health check: {result}")
    return result


@app.websocket("/ws/live")
async def websocket_live_data(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data streaming
    Frontend connects here to receive live updates
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        # Subscribe to Redis pub/sub for real-time updates
        if redis_client:
            pubsub = redis_client.pubsub()
            # include 'ohlc' channel so completed bars are forwarded to websockets
            await pubsub.subscribe("market_data", "alerts", "analytics", "ohlc")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Forward Redis messages to WebSocket clients
                    try:
                        raw_channel = message.get("channel")
                        channel = raw_channel.decode() if isinstance(raw_channel, (bytes, bytearray)) else str(raw_channel)
                        raw_data = message.get("data")
                        payload = None
                        if isinstance(raw_data, (bytes, bytearray)):
                            try:
                                payload = json.loads(raw_data.decode())
                            except Exception:
                                payload = raw_data.decode(errors='ignore')
                        elif isinstance(raw_data, str):
                            try:
                                payload = json.loads(raw_data)
                            except Exception:
                                payload = raw_data
                        else:
                            payload = raw_data

                        logger.debug(f"Forwarding pubsub message channel={channel} type={type(payload)}")

                        await websocket.send_json({
                            "type": "data",
                            "channel": channel,
                            "data": payload,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.exception(f"Error forwarding pubsub message to websocket: {e}")
        else:
            # Fallback: poll data service directly
            while True:
                if data_service:
                    latest = await data_service.get_latest_ticks(limit=10)
                    await websocket.send_json({
                        "type": "data",
                        "channel": "market_data",
                        "data": latest,
                        "timestamp": datetime.now().isoformat()
                    })
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client removed. Total: {len(active_connections)}")


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle Socket.IO client connection"""
    logger.info(f"Socket.IO client connected: {sid}")
    await sio.emit('connection', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat()
    }, room=sid)


@sio.event
async def disconnect(sid):
    """Handle Socket.IO client disconnect"""
    logger.info(f"Socket.IO client disconnected: {sid}")


async def broadcast_pubsub_data():
    """Background task to forward Redis pubsub to Socket.IO"""
    await asyncio.sleep(2)
    logger.info("Starting Redis pubsub -> Socket.IO forwarder")
    
    while True:
        try:
            if redis_client:
                pubsub = redis_client.pubsub()
                # forward OHLC bars as well so front-end charts receive aggregated bars
                await pubsub.subscribe("market_data", "alerts", "analytics", "ohlc")
                
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            raw_channel = message.get("channel")
                            channel = raw_channel.decode() if isinstance(raw_channel, (bytes, bytearray)) else str(raw_channel)
                            raw_data = message.get("data")
                            if isinstance(raw_data, (bytes, bytearray)):
                                try:
                                    data = json.loads(raw_data.decode())
                                except Exception:
                                    data = raw_data.decode(errors='ignore')
                            elif isinstance(raw_data, str):
                                try:
                                    data = json.loads(raw_data)
                                except Exception:
                                    data = raw_data
                            else:
                                data = raw_data

                            logger.debug(f"Pubsub -> Socket.IO: channel={channel}")

                            await sio.emit('data', {
                                'type': 'data',
                                'channel': channel,
                                'data': data,
                                'timestamp': datetime.now().isoformat()
                            })
                        except Exception as e:
                            logger.exception(f"Error forwarding pubsub: {e}")
            else:
                logger.warning("Redis not available for pubsub")
                await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Pubsub listener error: {e}")
            await asyncio.sleep(5)


async def broadcast_market_data():
    """Periodic status and metrics broadcaster"""
    await asyncio.sleep(3)
    logger.info("Starting periodic status broadcast")
    
    while True:
        try:
            now_ts = time()
            if 'app_start_ts' in globals():
                uptime_seconds = int(now_ts - globals().get('app_start_ts', now_ts))
            else:
                uptime_seconds = 0

            tick_count = 0
            active_symbols = []
            try:
                if data_service:
                    if hasattr(data_service, 'get_tick_count'):
                        tick_count = data_service.get_tick_count() or 0
                    if hasattr(data_service, 'get_active_symbols'):
                        syms = data_service.get_active_symbols()
                        if asyncio.iscoroutine(syms):
                            syms = await syms
                        active_symbols = syms or []
            except Exception as e:
                logger.exception(f"Error getting service stats: {e}")

            status_payload = {
                'connected': True,
                'uptime': uptime_seconds,
                'tick_count': tick_count,
                'active_symbols': len(active_symbols),
                'symbols': active_symbols,
            }

            logger.debug(f"Broadcasting status: uptime={uptime_seconds}s, ticks={tick_count}")

            # Emit both events
            await sio.emit('status', status_payload)
            await sio.emit('data', {
                'type': 'status',
                'channel': 'status',
                'data': status_payload,
                'timestamp': datetime.now().isoformat()
            })

            await asyncio.sleep(5)
        except Exception as e:
            logger.exception(f"Status broadcast error: {e}")
            await asyncio.sleep(5)


# Include API routers
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(debug.router, prefix="/api/debug", tags=["Debug"])

# Also expose same API endpoints without the `/api` prefix to support older frontend paths
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(debug.router, prefix="/debug", tags=["Debug"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
