"""Alert engine stub
Handles alert rule storage and test alert creation.
"""
import asyncio
from typing import Optional, List, Dict
import uuid

class AlertEngine:
    def __init__(self, redis_client: Optional[object]=None):
        self.redis = redis_client
        self._running = False
        self._rules = {}
        self._alerts = []

    async def start_monitoring(self):
        self._running = True
        # stub: not running loops here
        return

    async def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return bool(self._running)

    async def create_rule(self, rule: Dict) -> str:
        rule_id = rule.get('id') or str(uuid.uuid4())
        self._rules[rule_id] = rule
        return rule_id

    async def get_all_rules(self) -> List[Dict]:
        return list(self._rules.values())

    async def update_rule(self, rule_id: str, rule: Dict):
        if rule_id not in self._rules:
            raise KeyError("rule not found")
        self._rules[rule_id] = rule

    async def delete_rule(self, rule_id: str):
        if rule_id in self._rules:
            del self._rules[rule_id]

    async def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        return [a for a in self._alerts if not a.get('acknowledged')][:limit]

    async def get_alert_history(self, limit: int = 1000) -> List[Dict]:
        return list(self._alerts)[-limit:]

    async def acknowledge_alert(self, alert_id: str):
        for a in self._alerts:
            if a.get('id') == alert_id:
                a['acknowledged'] = True
                return
        raise KeyError('alert not found')

    async def clear_acknowledged(self) -> int:
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.get('acknowledged')]
        return before - len(self._alerts)

    async def create_test_alert(self, severity: str, message: str) -> str:
        alert_id = str(uuid.uuid4())
        alert = {
            'id': alert_id,
            'severity': severity,
            'message': message,
            'timestamp': None,
            'acknowledged': False
        }
        self._alerts.append(alert)
        return alert_id

    # helper counts
    def get_rule_count(self) -> int:
        return len(self._rules)

    def get_alert_count(self) -> int:
        return len(self._alerts)

# single shared instance used by APIs
alert_engine = AlertEngine()
