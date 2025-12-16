"""SQLite database operations for persistent storage."""
import aiosqlite
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class Database:
    """
    Manages SQLite operations for persistent tick and OHLC storage.
    """
    
    def __init__(self, db_path: str = "data/tick_data.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Initialize database connection and create tables."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.init_schema()
        logger.info(f"✅ Database connected: {self.db_path}")
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def init_schema(self):
        """Create all necessary tables."""
        
        # Ticks table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                trade_id INTEGER,
                is_buyer_maker INTEGER,
                processed_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticks_symbol_timestamp 
            ON ticks(symbol, timestamp DESC)
        """)
        
        # OHLC tables for different intervals
        for interval in ["1s", "1m", "5m"]:
            await self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS ohlc_{interval} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    tick_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp)
                )
            """)
            
            await self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_ohlc_{interval}_symbol_timestamp 
                ON ohlc_{interval}(symbol, timestamp DESC)
            """)
        
        # Analytics results table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                symbol1 TEXT,
                symbol2 TEXT,
                result_data TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alerts table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                rule_condition TEXT NOT NULL,
                symbol TEXT,
                triggered_value REAL,
                threshold REAL,
                message TEXT,
                timestamp INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.conn.commit()
        logger.info("Database schema initialized")
    
    async def insert_tick(self, tick: Dict[str, Any]):
        """Insert a single tick into the database."""
        await self.conn.execute("""
            INSERT INTO ticks (symbol, price, quantity, timestamp, trade_id, is_buyer_maker, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tick["symbol"],
            tick["price"],
            tick["quantity"],
            tick["timestamp"],
            tick.get("trade_id"),
            tick.get("is_buyer_maker", False),
            tick.get("processed_at")
        ))
        await self.conn.commit()
    
    async def insert_ohlc(self, symbol: str, interval: str, ohlc: Dict[str, Any]):
        """Insert OHLC data for a specific interval."""
        table = f"ohlc_{interval}"
        
        await self.conn.execute(f"""
            INSERT OR REPLACE INTO {table} 
            (symbol, open, high, low, close, volume, timestamp, tick_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            ohlc["open"],
            ohlc["high"],
            ohlc["low"],
            ohlc["close"],
            ohlc["volume"],
            ohlc["timestamp"],
            ohlc.get("tick_count", 0)
        ))
        await self.conn.commit()
    
    async def get_ohlc(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """Retrieve OHLC data for a symbol and interval."""
        table = f"ohlc_{interval}"
        
        cursor = await self.conn.execute(f"""
            SELECT * FROM {table}
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, limit))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_ticks(self, symbol: str, limit: int = 1000) -> List[Dict]:
        """Retrieve recent ticks for a symbol."""
        cursor = await self.conn.execute("""
            SELECT * FROM ticks
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, limit))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def insert_alert(self, alert: Dict[str, Any]):
        """Insert alert record."""
        await self.conn.execute("""
            INSERT INTO alerts (rule_name, rule_condition, symbol, triggered_value, threshold, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["rule_name"],
            alert["rule_condition"],
            alert.get("symbol"),
            alert.get("triggered_value"),
            alert.get("threshold"),
            alert.get("message"),
            alert["timestamp"]
        ))
        await self.conn.commit()
    
    async def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alert records."""
        cursor = await self.conn.execute("""
            SELECT * FROM alerts
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def insert_analytics_result(self, result: Dict[str, Any]):
        """Store analytics computation result."""
        await self.conn.execute("""
            INSERT INTO analytics_results (analysis_type, symbol1, symbol2, result_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            result["analysis_type"],
            result.get("symbol1"),
            result.get("symbol2"),
            result["result_data"],
            result["timestamp"]
        ))
        await self.conn.commit()
    
    async def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        counts = {}
        
        tables = ["ticks", "ohlc_1s", "ohlc_1m", "ohlc_5m", "analytics_results", "alerts"]
        
        for table in tables:
            cursor = await self.conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            row = await cursor.fetchone()
            counts[table] = row["count"]
        
        return counts
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            counts = await self.get_table_counts()
            
            return {
                "status": "healthy",
                "connected": True,
                "db_path": self.db_path,
                "table_counts": counts
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


async def test_database():
    """Test database operations."""
    db = Database("data/test_tick_data.db")
    await db.connect()
    
    # Test tick insertion
    tick = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "quantity": 0.5,
        "timestamp": 1700000000000,
        "trade_id": 123456,
        "is_buyer_maker": False
    }
    
    await db.insert_tick(tick)
    print("✅ Tick inserted")
    
    # Test OHLC insertion
    ohlc = {
        "open": 50000.0,
        "high": 50500.0,
        "low": 49500.0,
        "close": 50200.0,
        "volume": 100.5,
        "timestamp": 1700000000000,
        "tick_count": 150
    }
    
    await db.insert_ohlc("BTCUSDT", "1m", ohlc)
    print("✅ OHLC inserted")
    
    # Health check
    health = await db.health_check()
    print(f"Health: {health}")
    
    await db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(test_database())
