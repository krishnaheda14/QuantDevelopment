"""Central configuration for GEMSCAP Quant System."""
import logging
import sys
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    # WebSocket
    # Use base URL (no /ws) so client can build combined-stream URL: /stream?streams=...
    binance_ws_url: str = "wss://stream.binance.com:9443"
    # Mode: 'combined' -> single combined stream (/stream?streams=...)
    # 'per_symbol' -> open one websocket per symbol (e.g., futures wss://fstream.binance.com/ws/{symbol}@trade)
    binance_mode: str = "combined"
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    
    # Storage
    sqlite_path: str = "data/tick_data.db"
    redis_url: str = "redis://localhost:6379/0"
    redis_max_ticks: int = 1000
    redis_max_ohlc: int = 100
    
    # Sampling
    sampling_intervals: List[str] = field(default_factory=lambda: ["1s", "1m", "5m"])
    
    # Analytics
    rolling_window: int = 50
    correlation_window: int = 100
    adf_significance: float = 0.05
    
    # Alerting
    alert_check_interval: float = 0.5  # seconds
    zscore_threshold: float = 2.0
    spread_threshold: float = 0.005  # 0.5%
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501
    
    # Debug
    verbose: bool = True
    log_level: str = "INFO"


def setup_logging(config: Config):
    """Setup centralized logging."""
    # If verbose mode is enabled, prefer DEBUG level regardless of log_level
    if getattr(config, 'verbose', False):
        level = logging.DEBUG
    else:
        level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Ensure file handler uses utf-8 and attach to root logger
    handlers = [logging.StreamHandler(sys.stdout), logging.FileHandler('gemscap_quant.log', encoding='utf-8')]
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=handlers)
    # Make sure root logger also uses the desired level
    logging.getLogger().setLevel(level)
    
    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded successfully")
    logger.info(f"Symbols: {config.symbols}")
    logger.info(f"Redis: {config.redis_url}")
    logger.info(f"SQLite: {config.sqlite_path}")
    return logger


# Global config instance
config = Config()
logger = setup_logging(config)


if __name__ == "__main__":
    print("=== Configuration Debug ===")
    print(f"Symbols: {config.symbols}")
    print(f"Intervals: {config.sampling_intervals}")
    print(f"Redis URL: {config.redis_url}")
    print(f"SQLite Path: {config.sqlite_path}")
    print(f"Alert Z-Score Threshold: {config.zscore_threshold}")
