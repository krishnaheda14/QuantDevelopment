"""Redis manager for real-time data caching."""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from redis.asyncio import Redis, ConnectionPool

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages Redis operations for tick data and OHLC storage.
    """
    
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.url = url
        self.redis: Optional[Redis] = None
        self.pool: Optional[ConnectionPool] = None
    
    async def connect(self):
        """Initialize Redis connection pool."""
        try:
            self.pool = ConnectionPool.from_url(self.url, decode_responses=False)
            self.redis = Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis.ping()
            logger.info(f"✅ Redis connected: {self.url}")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def close(self):
        """Close Redis connections."""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Redis connection closed")
    
    async def add_tick(self, tick: Dict[str, Any]):
        """Add tick to sorted set with timestamp as score."""
        symbol = tick["symbol"]
        key = f"ticks:{symbol}"
        timestamp = tick["timestamp"]
        
        tick_json = json.dumps(tick)
        await self.redis.zadd(key, {tick_json: timestamp})
        
        # Keep only recent ticks
        await self.redis.zremrangebyrank(key, 0, -1001)
    
    async def get_recent_ticks(self, symbol: str, count: int = 100) -> List[Dict]:
        """Retrieve most recent ticks for a symbol."""
        key = f"ticks:{symbol}"
        data = await self.redis.zrevrange(key, 0, count - 1)
        
        ticks = []
        for item in data:
            if isinstance(item, bytes):
                item = item.decode('utf-8')
            ticks.append(json.loads(item))
        
        return ticks
    
    async def store_ohlc(self, symbol: str, interval: str, ohlc: Dict[str, Any]):
        """Store OHLC data in Redis with interval-specific key."""
        key = f"ohlc:{symbol}:{interval}"
        timestamp = ohlc["timestamp"]
        
        ohlc_json = json.dumps(ohlc)
        await self.redis.zadd(key, {ohlc_json: timestamp})
        
        # Keep only recent OHLC samples
        await self.redis.zremrangebyrank(key, 0, -101)
    
    async def get_ohlc(self, symbol: str, interval: str, count: int = 100) -> List[Dict]:
        """Retrieve OHLC data for a symbol and interval."""
        key = f"ohlc:{symbol}:{interval}"
        data = await self.redis.zrevrange(key, 0, count - 1)
        
        ohlc_list = []
        for item in data:
            if isinstance(item, bytes):
                item = item.decode('utf-8')
            ohlc_list.append(json.loads(item))
        
        return ohlc_list
    
    async def publish(self, channel: str, message: str):
        """Publish message to Redis Pub/Sub channel."""
        await self.redis.publish(channel, message)
    
    async def subscribe(self, channel: str):
        """Subscribe to Redis Pub/Sub channel."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    async def set_value(self, key: str, value: str, expire: Optional[int] = None):
        """Set a key-value pair with optional expiration."""
        await self.redis.set(key, value, ex=expire)
    
    async def get_value(self, key: str) -> Optional[str]:
        """Get value by key."""
        value = await self.redis.get(key)
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        return value
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get Redis memory statistics."""
        info = await self.redis.info('memory')
        return {
            "used_memory": info.get("used_memory_human", "N/A"),
            "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
            "total_keys": await self.redis.dbsize()
        }
    
    async def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern."""
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            keys.append(key)
        return keys
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health and return stats."""
        try:
            await self.redis.ping()
            memory = await self.get_memory_usage()
            
            return {
                "status": "healthy",
                "connected": True,
                "memory": memory
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


async def test_redis():
    """Test Redis manager."""
    manager = RedisManager()
    await manager.connect()
    
    # Test tick storage
    tick = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "quantity": 0.5,
        "timestamp": 1700000000000
    }
    
    await manager.add_tick(tick)
    ticks = await manager.get_recent_ticks("BTCUSDT", 10)
    print(f"Stored and retrieved {len(ticks)} ticks")
    
    # Test OHLC storage
    ohlc = {
        "symbol": "BTCUSDT",
        "open": 50000.0,
        "high": 50500.0,
        "low": 49500.0,
        "close": 50200.0,
        "volume": 100.5,
        "timestamp": 1700000000000
    }
    
    await manager.store_ohlc("BTCUSDT", "1m", ohlc)
    ohlc_data = await manager.get_ohlc("BTCUSDT", "1m", 10)
    print(f"Stored and retrieved {len(ohlc_data)} OHLC samples")
    
    # Health check
    health = await manager.health_check()
    print(f"Health: {health}")
    
    await manager.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_redis())
