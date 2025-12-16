"""
Alerts API Endpoints
Backend-driven alerting system with configurable thresholds
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AlertRule(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # "zscore", "rsi", "macd", "correlation"
    symbol1: str
    symbol2: Optional[str] = None
    threshold_upper: Optional[float] = None
    threshold_lower: Optional[float] = None
    enabled: bool = True


class Alert(BaseModel):
    id: str
    rule_id: str
    severity: str  # "low", "medium", "high"
    message: str
    data: dict
    timestamp: str
    acknowledged: bool = False


@router.post("/rules")
async def create_alert_rule(rule: AlertRule):
    """Create a new alert rule"""
    from ..services.alert_engine import alert_engine
    
    try:
        rule_id = await alert_engine.create_rule(rule.dict())
        return {"rule_id": rule_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=List[AlertRule])
async def get_alert_rules():
    """Get all alert rules"""
    from ..services.alert_engine import alert_engine
    
    try:
        rules = await alert_engine.get_all_rules()
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_alert_rule(rule_id: str, rule: AlertRule):
    """Update an existing alert rule"""
    from ..services.alert_engine import alert_engine
    
    try:
        await alert_engine.update_rule(rule_id, rule.dict())
        return {"rule_id": rule_id, "status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule"""
    from ..services.alert_engine import alert_engine
    
    try:
        await alert_engine.delete_rule(rule_id)
        return {"rule_id": rule_id, "status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/active", response_model=List[Alert])
async def get_active_alerts(limit: int = 50):
    """Get active (unacknowledged) alerts"""
    from ..services.alert_engine import alert_engine
    
    try:
        alerts = await alert_engine.get_active_alerts(limit)
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[Alert])
async def get_alert_history(limit: int = 100, offset: int = 0):
    """Get alert history"""
    from ..services.alert_engine import alert_engine
    
    try:
        alerts = await alert_engine.get_alert_history(limit, offset)
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    from ..services.alert_engine import alert_engine
    
    try:
        await alert_engine.acknowledge_alert(alert_id)
        return {"alert_id": alert_id, "status": "acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/clear")
async def clear_alerts():
    """Clear all acknowledged alerts"""
    from ..services.alert_engine import alert_engine
    
    try:
        count = await alert_engine.clear_acknowledged()
        return {"status": "cleared", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
