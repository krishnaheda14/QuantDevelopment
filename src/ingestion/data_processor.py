"""Real-time data processing and Redis streaming."""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Subscribes to tick stream, buffers ticks, and triggers sampling.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.tick_buffer = {}  # {symbol: [ticks]}
        self.processing_stats = {"ticks_processed": 0, "errors": 0}
    
    async def process_tick(self, tick: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and validate a single tick.
        
        Returns: Processed tick with additional metadata
        """
        try:
            # Add processing timestamp
            tick["processed_at"] = datetime.utcnow().isoformat()
            
            # Validate required fields
            required = ["symbol", "price", "quantity", "timestamp"]
            for field in required:
                if field not in tick:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add to buffer
            symbol = tick["symbol"]
            if symbol not in self.tick_buffer:
                self.tick_buffer[symbol] = []
            
            self.tick_buffer[symbol].append(tick)
            
            # Publish to Redis stream
            await self.publish_tick(tick)
            
            self.processing_stats["ticks_processed"] += 1
            
            return tick
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            self.processing_stats["errors"] += 1
            raise
    
    async def publish_tick(self, tick: Dict[str, Any]):
        """Publish tick to Redis channel for consumers."""
        try:
            channel = "tick_stream"
            message = json.dumps(tick)
            await self.redis.publish(channel, message)

            # Also store via RedisManager helper so implementation details stay encapsulated
            try:
                await self.redis.add_tick(tick)
            except AttributeError:
                # Fallback: if an underlying Redis client was passed instead of RedisManager
                symbol = tick["symbol"]
                key = f"ticks:{symbol}"
                score = tick["timestamp"]
                await self.redis.zadd(key, {message: score})
                await self.redis.zremrangebyrank(key, 0, -1001)
            
        except Exception as e:
            logger.error(f"Failed to publish tick to Redis: {e}")
    
    async def get_recent_ticks(self, symbol: str, count: int = 100) -> list:
        """Retrieve recent ticks for a symbol from Redis."""
        try:
            # Prefer RedisManager high-level method if available
            if hasattr(self.redis, "get_recent_ticks"):
                return await self.redis.get_recent_ticks(symbol, count)

            key = f"ticks:{symbol}"
            data = await self.redis.zrevrange(key, 0, count - 1)

            ticks = []
            for item in data:
                if isinstance(item, bytes):
                    item = item.decode('utf-8')
                ticks.append(json.loads(item))

            return ticks
            
        except Exception as e:
            logger.error(f"Failed to retrieve ticks: {e}")
            return []
    
    def get_buffer(self, symbol: str) -> list:
        """Get buffered ticks for a symbol."""
        return self.tick_buffer.get(symbol, [])
    
    def clear_buffer(self, symbol: str):
        """Clear buffer for a symbol after sampling."""
        if symbol in self.tick_buffer:
            self.tick_buffer[symbol] = []
    
    def get_stats(self) -> dict:
        """Return processing statistics."""
        buffer_sizes = {sym: len(ticks) for sym, ticks in self.tick_buffer.items()}
        
        return {
            "ticks_processed": self.processing_stats["ticks_processed"],
            "errors": self.processing_stats["errors"],
            "buffer_sizes": buffer_sizes,
            "total_buffered": sum(buffer_sizes.values())
        }


async def test_processor():
    """Test data processor with mock Redis."""
    from unittest.mock import AsyncMock
    
    redis_mock = AsyncMock()
    processor = DataProcessor(redis_mock)
    
    # Test tick
    tick = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "quantity": 0.5,
        "timestamp": 1700000000000
    }
    
    result = await processor.process_tick(tick)
    print(f"Processed tick: {result}")
    print(f"Stats: {processor.get_stats()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_processor())
