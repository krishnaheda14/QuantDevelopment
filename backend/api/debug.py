"""
Debug/Validation API Endpoints
Debugging layer for system diagnostics and data validation
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
import psutil
import sys

router = APIRouter()


@router.get("/system/status")
async def system_status():
    """
    Get comprehensive system status
    CPU, memory, disk, network stats
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_mb": memory.total / (1024**2),
                "used_mb": memory.used / (1024**2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "percent": disk.percent
            },
            "python_version": sys.version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/status")
async def redis_status():
    """
    Get Redis connection status and stats
    """
    from ..main import redis_client
    
    try:
        if not redis_client:
            return {"status": "disconnected", "mode": "fallback"}
        
        info = await redis_client.info()
        return {
            "status": "connected",
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_mb": info.get("used_memory") / (1024**2) if info.get("used_memory") else 0,
            "total_commands_processed": info.get("total_commands_processed"),
            "keys_count": await redis_client.dbsize()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/status")
async def services_status():
    """
    Get status of all background services
    """
    from ..main import data_service, sampling_service, alert_service
    
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "data_ingestion": {
                "running": data_service.is_running() if data_service else False,
                "websocket_connected": data_service.is_connected() if data_service else False,
                "symbols": data_service.get_active_symbols() if data_service else [],
                "tick_count": data_service.get_tick_count() if data_service else 0
            },
            "sampling_engine": {
                "running": sampling_service.is_running() if sampling_service else False,
                "intervals": sampling_service.get_active_intervals() if sampling_service else [],
                "last_sample_time": sampling_service.get_last_sample_time() if sampling_service else None
            },
            "alert_engine": {
                "running": alert_service.is_running() if alert_service else False,
                "active_rules": alert_service.get_rule_count() if alert_service else 0,
                "active_alerts": alert_service.get_alert_count() if alert_service else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/validation/{symbol}")
async def validate_data(symbol: str, interval: str = "1m", limit: int = 100):
    """
    Validate data quality for a symbol
    Checks for gaps, outliers, consistency
    """
    from ..services.data_ingestion import data_service
    
    try:
        data = await data_service.get_ohlc(symbol, interval, limit)
        
        if not data:
            return {
                "symbol": symbol,
                "status": "no_data",
                "issues": ["No data available for this symbol"]
            }
        
        issues = []
        warnings = []
        
        # Check for gaps
        timestamps = [d['timestamp'] for d in data]
        interval_ms = {'1s': 1000, '1m': 60000, '5m': 300000}.get(interval, 60000)
        gaps = []
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i-1]
            if diff > interval_ms * 1.5:
                gaps.append({
                    "index": i,
                    "gap_ms": diff,
                    "expected_ms": interval_ms
                })
        
        if gaps:
            warnings.append(f"Found {len(gaps)} gaps in data")
        
        # Check for outliers (price jumps > 10%)
        outliers = []
        for i in range(1, len(data)):
            price_change = abs(data[i]['close'] - data[i-1]['close']) / data[i-1]['close']
            if price_change > 0.1:
                outliers.append({
                    "index": i,
                    "price_change_pct": price_change * 100,
                    "from": data[i-1]['close'],
                    "to": data[i]['close']
                })
        
        if outliers:
            warnings.append(f"Found {len(outliers)} potential outliers (>10% price jump)")
        
        # Check OHLC consistency
        inconsistent = []
        for i, bar in enumerate(data):
            if not (bar['low'] <= bar['open'] <= bar['high'] and
                    bar['low'] <= bar['close'] <= bar['high']):
                inconsistent.append({
                    "index": i,
                    "bar": bar
                })
        
        if inconsistent:
            issues.append(f"Found {len(inconsistent)} bars with OHLC inconsistencies")
        
        return {
            "symbol": symbol,
            "interval": interval,
            "bars_checked": len(data),
            "status": "healthy" if not issues else "issues_found",
            "issues": issues,
            "warnings": warnings,
            "gaps": gaps[:5],  # First 5 gaps
            "outliers": outliers[:5],  # First 5 outliers
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(limit: int = 100):
    """
    Get recent application logs
    """
    # This would read from a log file or database
    # For now, return placeholder
    return {
        "message": "Log retrieval not implemented yet",
        "logs": []
    }


@router.post("/test/alert")
async def trigger_test_alert(severity: str = "medium", message: str = "Test alert"):
    """
    Trigger a test alert for debugging
    """
    from ..services.alert_engine import alert_engine
    
    try:
        alert_id = await alert_engine.create_test_alert(severity, message)
        return {
            "alert_id": alert_id,
            "status": "triggered",
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
