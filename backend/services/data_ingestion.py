"""Data ingestion service stub
This is a lightweight stub to allow imports and basic status checks.
Real implementation should connect to Binance WS and push to Redis pub/sub.
"""
import asyncio
from typing import List, Dict, Optional

class DataIngestionService:
    def __init__(self, redis_client: Optional[object]=None):
        self.redis = redis_client
        self._running = False
        self._connected = False
        self._symbols = []
        self._tick_count = 0

    async def start_ingestion(self):
        """Start ingestion background task (stub). In real service this would open WS.
        Here we only set running flags and return to avoid long-running loops during import tests."""
        self._running = True
        # Do not block: just simulate initial connected state
        self._connected = True
        # Example default symbols
        self._symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    async def stop(self):
        self._running = False
        self._connected = False

    def is_running(self) -> bool:
        return bool(self._running)

    def is_connected(self) -> bool:
        return bool(self._connected)

    def get_active_symbols(self) -> List[str]:
        return list(self._symbols)

    def get_tick_count(self) -> int:
        return int(self._tick_count)

    async def get_latest_ticks(self, limit: int = 10) -> List[Dict]:
        # Return empty list in stub
        return []

    async def get_ohlc(self, symbol: str, interval: str, limit: int):
        # Return empty data for now
        return []
