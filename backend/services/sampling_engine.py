"""Sampling engine stub
Provides interface for sampling/aggregation (1s/1m/5m etc.).
"""
import asyncio
from typing import Optional, List

class SamplingEngine:
    def __init__(self, redis_client: Optional[object]=None):
        self.redis = redis_client
        self._running = False
        self._intervals = ["1s", "1m", "5m"]
        self._last_sample_time = None

    async def start_sampling(self):
        self._running = True
        # stub: do not run an infinite loop here
        return

    async def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return bool(self._running)

    def get_active_intervals(self) -> List[str]:
        return list(self._intervals)

    def get_last_sample_time(self):
        return self._last_sample_time
