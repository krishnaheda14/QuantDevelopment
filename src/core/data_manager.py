"""
Data Manager - Simplified architecture without Redis
Uses in-memory deque for recent data + SQLite for persistence
"""

import asyncio
import websockets
import json
import sqlite3
import time
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import numpy as np

class DataManager:
    """Manages WebSocket ingestion and data storage"""
    
    # Extended symbol list
    SYMBOLS = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
        'DOTUSDT', 'MATICUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT',
        'ATOMUSDT', 'LTCUSDT', 'XRPUSDT'
    ]
    
    def __init__(self, db_path='data/gemscap.db', max_ticks=10000):
        self.db_path = db_path
        self.max_ticks = max_ticks
        
        # In-memory tick storage (per symbol)
        self.ticks = defaultdict(lambda: deque(maxlen=max_ticks))
        
        # Aggregated OHLC (per symbol per interval)
        self.ohlc_1s = defaultdict(lambda: deque(maxlen=3600))  # 1 hour
        self.ohlc_1m = defaultdict(lambda: deque(maxlen=1440))  # 24 hours
        self.ohlc_5m = defaultdict(lambda: deque(maxlen=288))   # 24 hours
        
        # Connection status
        self.ws_connected = False
        self.ws_thread = None
        self.running = False
        
        # Stats
        self.start_time = time.time()
        self.tick_count = 0
        
        # Initialize database
        self._init_db()
        
        # Start WebSocket in background
        self._start_websocket()
    
    def _init_db(self):
        """Initialize SQLite database"""
        import os
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ohlc_1m (
                symbol TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                tick_count INTEGER,
                PRIMARY KEY (symbol, timestamp)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ohlc_5m (
                symbol TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                tick_count INTEGER,
                PRIMARY KEY (symbol, timestamp)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _start_websocket(self):
        """Start WebSocket connection in background thread"""
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_websocket_loop, daemon=True)
        self.ws_thread.start()
    
    def _run_websocket_loop(self):
        """Run WebSocket event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect_websocket())
    
    async def _connect_websocket(self):
        """Connect to Binance WebSocket"""
        # Build combined stream URL
        streams = [f"{s.lower()}@trade" for s in self.SYMBOLS]
        url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    self.ws_connected = True
                    print(f"[DataManager] Connected to Binance WebSocket ({len(self.SYMBOLS)} symbols)")
                    
                    while self.running:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        await self._handle_message(msg)
                        
            except Exception as e:
                print(f"[DataManager] WebSocket error: {e}. Reconnecting in 5s...")
                self.ws_connected = False
                await asyncio.sleep(5)
    
    async def _handle_message(self, msg: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(msg)
            if 'data' in data:
                trade = data['data']
                symbol = trade['s']
                
                tick = {
                    'symbol': symbol,
                    'price': float(trade['p']),
                    'quantity': float(trade['q']),
                    'timestamp': trade['T'],
                    'is_buyer_maker': trade['m']
                }
                
                # Store tick
                self.ticks[symbol].append(tick)
                self.tick_count += 1
                
                # Debug print every 100 ticks
                if self.tick_count % 100 == 0:
                    print(f"[DataManager] Received {self.tick_count} ticks. Latest: {symbol} @ ${tick['price']}")
                
                # Aggregate OHLC
                self._aggregate_ticks(symbol)
                
        except Exception as e:
            print(f"[DataManager] Message parse error: {e}")
    
    def _aggregate_ticks(self, symbol: str):
        """Aggregate ticks into OHLC bars"""
        if not self.ticks[symbol]:
            return
        
        current_time = time.time() * 1000  # ms
        
        # 1-second bars
        last_1s = self.ohlc_1s[symbol][-1] if self.ohlc_1s[symbol] else None
        if not last_1s or current_time - last_1s['timestamp'] >= 1000:
            bar = self._create_bar(symbol, 1000)
            if bar:
                self.ohlc_1s[symbol].append(bar)
        
        # 1-minute bars
        last_1m = self.ohlc_1m[symbol][-1] if self.ohlc_1m[symbol] else None
        if not last_1m or current_time - last_1m['timestamp'] >= 60000:
            bar = self._create_bar(symbol, 60000)
            if bar:
                self.ohlc_1m[symbol].append(bar)
                print(f"[DataManager] New 1m bar: {symbol} @ ${bar['close']:.2f}, total bars: {len(self.ohlc_1m[symbol])}")
                self._persist_bar(bar)
        
        # 5-minute bars
        last_5m = self.ohlc_5m[symbol][-1] if self.ohlc_5m[symbol] else None
        if not last_5m or current_time - last_5m['timestamp'] >= 300000:
            bar = self._create_bar(symbol, 300000)
            if bar:
                self.ohlc_5m[symbol].append(bar)
    
    def _create_bar(self, symbol: str, window_ms: int) -> Optional[Dict]:
        """Create OHLC bar from recent ticks"""
        current_time = time.time() * 1000
        cutoff = current_time - window_ms
        
        recent_ticks = [t for t in self.ticks[symbol] if t['timestamp'] > cutoff]
        if not recent_ticks:
            return None
        
        prices = [t['price'] for t in recent_ticks]
        volumes = [t['quantity'] for t in recent_ticks]
        
        return {
            'symbol': symbol,
            'timestamp': int(current_time),
            'open': prices[0],
            'high': max(prices),
            'low': min(prices),
            'close': prices[-1],
            'volume': sum(volumes),
            'tick_count': len(recent_ticks)
        }
    
    def _persist_bar(self, bar: Dict):
        """Persist 1m bar to SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ohlc_1m 
                (symbol, timestamp, open, high, low, close, volume, tick_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bar['symbol'], bar['timestamp'], bar['open'], bar['high'], 
                  bar['low'], bar['close'], bar['volume'], bar['tick_count']))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DataManager] Persist error: {e}")
    
    def get_ohlc(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """Get OHLC data for symbol"""
        if interval == '1s':
            data = list(self.ohlc_1s[symbol])
        elif interval == '1m':
            data = list(self.ohlc_1m[symbol])
        elif interval == '5m':
            data = list(self.ohlc_5m[symbol])
        else:
            data = list(self.ohlc_1m[symbol])
        
        result = data[-limit:] if len(data) >= limit else data
        print(f"[DataManager] get_ohlc({symbol}, {interval}, limit={limit}) -> {len(result)} bars")
        
        # Return last N bars
        return result
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols"""
        return self.SYMBOLS
    
    def get_connection_status(self) -> Dict:
        """Get WebSocket connection status"""
        return {
            'connected': self.ws_connected,
            'active_symbols': len([s for s in self.SYMBOLS if self.ticks[s]]),
            'total_ticks': self.tick_count,
            'symbols': len(self.SYMBOLS)
        }
    
    def get_db_stats(self) -> Dict:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM ohlc_1m')
            count = cursor.fetchone()[0]
            conn.close()
            
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            uptime = int(time.time() - self.start_time)
            uptime_str = f"{uptime//3600}h {(uptime%3600)//60}m"
            
            return {
                'total_records': count,
                'memory_mb': memory_mb,
                'uptime': uptime_str
            }
        except:
            return {'total_records': 0, 'memory_mb': 0, 'uptime': '0h 0m'}
    
    def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
