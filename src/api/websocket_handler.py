"""WebSocket handler for real-time streaming."""
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from typing import Set

logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time updates."""
    await websocket.accept()
    active_connections.add(websocket)
    
    logger.info(f"WebSocket connected. Total connections: {len(active_connections)}")
    
    try:
        # Send initial message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Real-time stream active"
        })
        
        # Keep connection alive
        while True:
            try:
                # Receive messages (heartbeat/ping)
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(active_connections)}")


async def broadcast_tick(tick: dict):
    """Broadcast tick to all connected clients."""
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "tick",
        "data": tick
    })
    
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            disconnected.add(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.discard(conn)


async def broadcast_alert(alert: dict):
    """Broadcast alert to all connected clients."""
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "alert",
        "data": alert
    })
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            pass
