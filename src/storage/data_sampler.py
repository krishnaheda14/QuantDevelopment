"""Data sampling for 1s, 1m, 5m OHLC aggregation."""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class DataSampler:
    """
    Periodically samples tick data and computes OHLC for different intervals.
    """
    
    def __init__(self, redis_manager, database, symbols: List[str]):
        self.redis = redis_manager
        self.db = database
        self.symbols = symbols
        self.scheduler = AsyncIOScheduler()
        self.sample_stats = {"1s": 0, "1m": 0, "5m": 0}
    
    def start(self):
        """Start sampling schedulers."""
        # 1-second sampling
        self.scheduler.add_job(
            self.sample_all_symbols,
            IntervalTrigger(seconds=1),
            args=["1s"],
            id="sample_1s"
        )
        
        # 1-minute sampling
        self.scheduler.add_job(
            self.sample_all_symbols,
            IntervalTrigger(minutes=1),
            args=["1m"],
            id="sample_1m"
        )
        
        # 5-minute sampling
        self.scheduler.add_job(
            self.sample_all_symbols,
            IntervalTrigger(minutes=5),
            args=["5m"],
            id="sample_5m"
        )
        
        self.scheduler.start()
        logger.info("✅ Data sampler started (1s, 1m, 5m intervals)")
    
    def stop(self):
        """Stop sampling scheduler."""
        self.scheduler.shutdown()
        logger.info("Data sampler stopped")
    
    async def sample_all_symbols(self, interval: str):
        """Sample OHLC for all symbols at specified interval."""
        for symbol in self.symbols:
            try:
                await self.sample_symbol(symbol, interval)
            except Exception as e:
                logger.error(f"Error sampling {symbol} at {interval}: {e}")
    
    async def sample_symbol(self, symbol: str, interval: str):
        """
        Compute OHLC for a symbol at specified interval.
        """
        # Get recent ticks from Redis
        ticks = await self.redis.get_recent_ticks(symbol, count=1000)
        
        if not ticks:
            logger.debug(f"No ticks available for {symbol} to sample")
            return
        
        # Filter ticks within interval window
        now = datetime.utcnow().timestamp() * 1000
        interval_ms = self.interval_to_ms(interval)
        start_time = now - interval_ms
        
        relevant_ticks = [
            t for t in ticks
            if t["timestamp"] >= start_time
        ]
        
        if not relevant_ticks:
            logger.debug(f"No recent ticks for {symbol} in {interval} window")
            return
        
        # Compute OHLC
        ohlc = self.compute_ohlc(relevant_ticks, now)
        ohlc["symbol"] = symbol
        
        # Store in Redis
        await self.redis.store_ohlc(symbol, interval, ohlc)
        
        # Store in SQLite
        await self.db.insert_ohlc(symbol, interval, ohlc)
        
        self.sample_stats[interval] += 1
        
        logger.debug(
            f"[{interval}] Sampled {symbol}: O={ohlc['open']:.2f}, "
            f"H={ohlc['high']:.2f}, L={ohlc['low']:.2f}, C={ohlc['close']:.2f}, "
            f"V={ohlc['volume']:.4f}, Ticks={ohlc['tick_count']}"
        )
    
    def compute_ohlc(self, ticks: List[Dict[str, Any]], timestamp: float) -> Dict[str, Any]:
        """
        Compute OHLC from tick data.
        
        Args:
            ticks: List of tick dictionaries sorted by timestamp
            timestamp: Current timestamp for this OHLC sample
        
        Returns:
            OHLC dictionary
        """
        if not ticks:
            raise ValueError("Cannot compute OHLC from empty ticks")
        
        # Sort by timestamp (oldest first)
        sorted_ticks = sorted(ticks, key=lambda t: t["timestamp"])
        
        prices = [t["price"] for t in sorted_ticks]
        quantities = [t["quantity"] for t in sorted_ticks]
        
        ohlc = {
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "volume": sum(quantities),
            "tick_count": len(ticks),
            "timestamp": int(timestamp)
        }
        
        return ohlc
    
    @staticmethod
    def interval_to_ms(interval: str) -> int:
        """Convert interval string to milliseconds."""
        mapping = {
            "1s": 1000,
            "1m": 60000,
            "5m": 300000
        }
        return mapping.get(interval, 1000)
    
    def get_stats(self) -> Dict[str, Any]:
        """Return sampling statistics."""
        return {
            "samples_computed": self.sample_stats,
            "scheduler_running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }


async def test_sampler():
    """Test data sampler."""
    from unittest.mock import AsyncMock
    
    redis_mock = AsyncMock()
    redis_mock.get_recent_ticks.return_value = [
        {"symbol": "BTCUSDT", "price": 50000.0, "quantity": 0.1, "timestamp": 1700000000000},
        {"symbol": "BTCUSDT", "price": 50100.0, "quantity": 0.2, "timestamp": 1700000001000},
        {"symbol": "BTCUSDT", "price": 49900.0, "quantity": 0.15, "timestamp": 1700000002000},
    ]
    
    db_mock = AsyncMock()
    
    sampler = DataSampler(redis_mock, db_mock, ["BTCUSDT"])
    
    # Test manual sampling
    await sampler.sample_symbol("BTCUSDT", "1s")
    
    print(f"Stats: {sampler.get_stats()}")
    
    # Test scheduler
    sampler.start()
    await asyncio.sleep(3)  # Let it run for 3 seconds
    sampler.stop()
    
    print(f"Final stats: {sampler.get_stats()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_sampler())
