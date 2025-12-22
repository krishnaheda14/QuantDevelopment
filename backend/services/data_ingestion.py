"""Data ingestion service - connects to Binance WebSocket and ingests real-time data"""
import asyncio
import json
import logging
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path to import websocket_client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.ingestion.websocket_client import BinanceWebSocketClient
except ImportError:
    BinanceWebSocketClient = None
    logging.warning("Could not import BinanceWebSocketClient, using fallback mode")

logger = logging.getLogger(__name__)


class DataIngestionService:
    def __init__(self, redis_client: Optional[object] = None):
        self.redis = redis_client
        self._running = False
        self._connected = False
        self._symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        self._tick_count = 0
        self._ws_client = None
        self._ingestion_task = None

    async def _handle_tick(self, tick: Dict):
        """Handle incoming tick data from WebSocket"""
        try:
            self._tick_count += 1
            
            # Publish to Redis if available
            if self.redis:
                await self.redis.publish(
                    "market_data",
                    json.dumps(tick)
                )
            
            # Log every 100 ticks
            if self._tick_count % 100 == 0:
                logger.info(f"Processed {self._tick_count} ticks. Latest: {tick['symbol']} @ {tick['price']}")
                
        except Exception as e:
            logger.exception(f"Error handling tick: {e}")

    async def start_ingestion(self):
        """Start WebSocket ingestion"""
        self._running = True
        
        if BinanceWebSocketClient is None:
            logger.warning("BinanceWebSocketClient not available, using stub mode")
            self._connected = True
            return
        
        try:
            # Initialize WebSocket client
            self._ws_client = BinanceWebSocketClient(
                symbols=self._symbols,
                base_url="wss://stream.binance.com:9443",
                callback=self._handle_tick,
                mode="combined"
            )
            
            # Start ingestion task
            self._ingestion_task = asyncio.create_task(self._ws_client.run())
            self._connected = True
            logger.info(f"✅ Started ingestion for symbols: {self._symbols}")
            
        except Exception as e:
            logger.exception(f"Failed to start ingestion: {e}")
            self._connected = False

    async def stop(self):
        """Stop ingestion"""
        self._running = False
        self._connected = False
        
        if self._ws_client:
            self._ws_client.running = False
        
        if self._ingestion_task:
            self._ingestion_task.cancel()
            try:
                await self._ingestion_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Stopped data ingestion")

    def is_running(self) -> bool:
        return bool(self._running)

    def is_connected(self) -> bool:
        return bool(self._connected)

    def get_active_symbols(self) -> List[str]:
        return list(self._symbols)

    def get_tick_count(self) -> int:
        return int(self._tick_count)

    async def get_latest_ticks(self, limit: int = 10) -> List[Dict]:
        # TODO: Implement fetching from Redis or in-memory buffer
        return []

    async def get_ohlc(self, symbol: str, interval: str, limit: int):
        # TODO: Implement OHLC aggregation
        return []
