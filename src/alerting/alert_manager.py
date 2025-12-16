"""Alert manager with periodic checking."""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alert rules and triggers alerts based on real-time data.
    """
    
    def __init__(self, redis_manager, database, rules: List):
        self.redis = redis_manager
        self.db = database
        self.rules = rules
        self.scheduler = AsyncIOScheduler()
        self.alert_history = []
        self.check_count = 0
    
    def start(self, check_interval: float = 0.5):
        """Start periodic alert checking."""
        self.scheduler.add_job(
            self.check_all_rules,
            'interval',
            seconds=check_interval,
            id="alert_checker"
        )
        
        self.scheduler.start()
        logger.info(f"✅ Alert manager started (checking every {check_interval}s)")
    
    def stop(self):
        """Stop alert manager."""
        self.scheduler.shutdown()
        logger.info("Alert manager stopped")
    
    async def check_all_rules(self):
        """Check all alert rules against current data."""
        self.check_count += 1
        
        try:
            # Get latest analytics data from Redis
            # This would be populated by analytics engine
            analytics_key = "latest_analytics"
            analytics_data_str = await self.redis.get_value(analytics_key)
            
            if not analytics_data_str:
                return
            
            import json
            analytics_data = json.loads(analytics_data_str)
            
            # Check each rule
            for rule in self.rules:
                if rule.check(analytics_data):
                    await self.trigger_alert(rule, analytics_data)
                    
        except Exception as e:
            logger.error(f"Alert check failed: {e}")
    
    async def trigger_alert(self, rule, data: Dict[str, Any]):
        """Trigger an alert."""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        
        message = rule.format_message(data)
        
        alert = {
            "rule_name": rule.name,
            "rule_condition": rule.condition.__name__,
            "symbol": data.get("symbol") or f"{data.get('symbol1')}-{data.get('symbol2')}",
            "triggered_value": data.get("zscore") or data.get("spread"),
            "threshold": rule.threshold,
            "message": message,
            "timestamp": timestamp
        }
        
        # Store in database
        await self.db.insert_alert(alert)
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > 100:
            self.alert_history.pop(0)
        
        # Broadcast via WebSocket
        from src.api.websocket_handler import broadcast_alert
        await broadcast_alert(alert)
        
        logger.warning(f"🚨 ALERT: {message}")
    
    def add_rule(self, rule):
        """Add a new alert rule."""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    async def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts from database."""
        return await self.db.get_recent_alerts(limit)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert manager statistics."""
        # Ensure values are JSON-serializable and include small debug snapshots
        try:
            rule_names = [str(r.name) for r in self.rules]
        except Exception:
            rule_names = [repr(r) for r in self.rules]

        return {
            "active_rules": int(len(self.rules)),
            "rule_names": rule_names,
            "checks_performed": int(self.check_count),
            "recent_alerts_count": int(len(self.alert_history)),
            "scheduler_running": bool(self.scheduler.running),
            "recent_alerts_sample": self.alert_history[-5:]
        }
