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
import logging

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

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8502"],
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


@app.get("/health")
async def health_check():
    """Detailed health check"""
    redis_status = "connected"
    try:
        if redis_client:
            await redis_client.ping()
        else:
            redis_status = "fallback_mode"
    except:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "services": {
            "data_ingestion": data_service is not None and data_service.is_running(),
            "sampling_engine": sampling_service is not None and sampling_service.is_running(),
            "alert_engine": alert_service is not None and alert_service.is_running()
        },
        "websocket_connections": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }


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
            await pubsub.subscribe("market_data", "alerts", "analytics")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Forward Redis messages to WebSocket clients
                    await websocket.send_json({
                        "type": "data",
                        "channel": message["channel"],
                        "data": json.loads(message["data"]),
                        "timestamp": datetime.now().isoformat()
                    })
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


# Include API routers
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(debug.router, prefix="/api/debug", tags=["Debug"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
