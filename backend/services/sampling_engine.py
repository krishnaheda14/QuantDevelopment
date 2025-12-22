"""Sampling engine - aggregates tick data into OHLC bars"""
import asyncio
import json
import logging
from typing import Optional, List, Dict
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class SamplingEngine:
    def __init__(self, redis_client: Optional[object] = None):
        self.redis = redis_client
        self._running = False
        self._intervals = ["1m"]  # Start with 1m only
        self._last_sample_time = None
        self._current_bars = defaultdict(lambda: defaultdict(lambda: {
            'open': None,
            'high': None,
            'low': None,
            'close': None,
            'volume': 0.0,
            'trades': 0,
            'timestamp': None
        }))
        self._sampling_task = None
        self._snapshot_task = None

    async def start_sampling(self):
        """Start OHLC aggregation from Redis pubsub ticks"""
        self._running = True
        
        if not self.redis:
            logger.warning("Redis not available, sampling engine in stub mode")
            return
        
        self._sampling_task = asyncio.create_task(self._aggregate_ticks())
        # start periodic snapshot publisher so frontend can render in-progress bars
        self._snapshot_task = asyncio.create_task(self._publish_snapshots())
        logger.info("✅ Sampling engine started - aggregating ticks to OHLC")

    async def _aggregate_ticks(self):
        """Subscribe to market_data and aggregate into 1m bars"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe("market_data")
            
            logger.info("Sampling engine subscribed to market_data")
            
            async for message in pubsub.listen():
                if not self._running:
                    break
                    
                if message["type"] != "message":
                    continue
                
                try:
                    # Parse tick
                    raw_data = message.get("data")
                    if isinstance(raw_data, (bytes, bytearray)):
                        tick_data = json.loads(raw_data.decode())
                    elif isinstance(raw_data, str):
                        tick_data = json.loads(raw_data)
                    else:
                        tick_data = raw_data
                    
                    if not isinstance(tick_data, dict) or 'symbol' not in tick_data:
                        continue
                    
                    symbol = tick_data['symbol']
                    price = float(tick_data.get('price', 0))
                    quantity = float(tick_data.get('quantity', 0))
                    timestamp = int(tick_data.get('timestamp', datetime.now().timestamp() * 1000))
                    
                    # Round to 1-minute bucket
                    minute_ts = (timestamp // 60000) * 60000
                    
                    bar = self._current_bars[symbol]['1m']
                    
                    # Initialize bar if new minute
                    if bar['timestamp'] is None or bar['timestamp'] != minute_ts:
                        # Publish completed bar if exists
                        if bar['timestamp'] is not None and bar['open'] is not None:
                            await self._publish_bar(symbol, '1m', bar)
                        
                        # Start new bar
                        bar['open'] = price
                        bar['high'] = price
                        bar['low'] = price
                        bar['close'] = price
                        bar['volume'] = quantity
                        bar['trades'] = 1
                        bar['timestamp'] = minute_ts
                    else:
                        # Update existing bar
                        bar['high'] = max(bar['high'], price)
                        bar['low'] = min(bar['low'], price)
                        bar['close'] = price
                        bar['volume'] += quantity
                        bar['trades'] += 1
                    
                    self._last_sample_time = datetime.now().isoformat()
                    
                except Exception as e:
                    logger.exception(f"Error processing tick for OHLC: {e}")
                    
        except Exception as e:
            logger.exception(f"Sampling engine error: {e}")
            await asyncio.sleep(5)
            if self._running:
                asyncio.create_task(self._aggregate_ticks())
    
    async def _publish_bar(self, symbol: str, interval: str, bar: Dict):
        """Publish completed OHLC bar to Redis"""
        try:
            bar_data = {
                'symbol': symbol,
                'interval': interval,
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume'],
                'trades': bar['trades'],
                'timestamp': bar['timestamp'],
                'final': True,
            }
            # Store completed bar in Redis sorted set for historical queries
            try:
                key = f"ohlc:{symbol}:{interval}"
                await self.redis.zadd(key, {json.dumps(bar_data): int(bar['timestamp'])})
                # Keep recent history
                await self.redis.zremrangebyrank(key, 0, -501)
            except Exception:
                logger.debug("Failed to store OHLC in Redis, continuing")

            await self.redis.publish('ohlc', json.dumps(bar_data))
            logger.info(f"Published {interval} bar for {symbol}: close={bar['close']:.2f}, ts={bar['timestamp']}")
        except Exception as e:
            logger.exception(f"Failed to publish bar: {e}")

    async def stop(self):
        self._running = False
        if self._sampling_task:
            self._sampling_task.cancel()
            try:
                await self._sampling_task
            except asyncio.CancelledError:
                pass
        if self._snapshot_task:
            self._snapshot_task.cancel()
            try:
                await self._snapshot_task
            except asyncio.CancelledError:
                pass

    async def _publish_snapshots(self):
        """Periodically publish in-progress OHLC bars so frontend charts can render live bars before minute closes"""
        try:
            while self._running:
                try:
                    # iterate over current bars and publish snapshot
                    snapshot_count = 0
                    for symbol, intervals in list(self._current_bars.items()):
                        bar = intervals.get('1m')
                        if bar and bar['timestamp'] is not None and bar['open'] is not None:
                            snapshot = {
                                'symbol': symbol,
                                'interval': '1m',
                                'open': bar['open'],
                                'high': bar['high'],
                                'low': bar['low'],
                                'close': bar['close'],
                                'volume': bar['volume'],
                                'trades': bar['trades'],
                                'timestamp': bar['timestamp'],
                                'final': False,
                            }
                            try:
                                await self.redis.publish('ohlc', json.dumps(snapshot))
                                snapshot_count += 1
                            except Exception:
                                # if publishing fails, ignore for this cycle
                                pass
                    if snapshot_count:
                        logger.debug(f"Published {snapshot_count} OHLC snapshots")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.exception(f"Error publishing OHLC snapshots: {e}")
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            return

    def is_running(self) -> bool:
        return bool(self._running)

    def get_active_intervals(self) -> List[str]:
        return list(self._intervals)

    def get_last_sample_time(self):
        return self._last_sample_time
