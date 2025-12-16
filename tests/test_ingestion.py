"""Tests for ingestion components."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.ingestion.data_processor import DataProcessor


@pytest.mark.asyncio
async def test_data_processor_process_tick():
    """Test tick processing."""
    redis_mock = AsyncMock()
    processor = DataProcessor(redis_mock)
    
    tick = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "quantity": 0.5,
        "timestamp": 1700000000000
    }
    
    result = await processor.process_tick(tick)
    
    assert result["symbol"] == "BTCUSDT"
    assert result["price"] == 50000.0
    assert "processed_at" in result
    
    # Verify Redis publish was called
    redis_mock.publish.assert_called()


@pytest.mark.asyncio
async def test_data_processor_get_recent_ticks():
    """Test retrieving recent ticks."""
    redis_mock = AsyncMock()
    redis_mock.zrevrange.return_value = [
        b'{"symbol": "BTCUSDT", "price": 50000.0, "quantity": 0.1, "timestamp": 1700000000000}'
    ]
    
    processor = DataProcessor(redis_mock)
    
    ticks = await processor.get_recent_ticks("BTCUSDT", 10)
    
    assert len(ticks) == 1
    assert ticks[0]["symbol"] == "BTCUSDT"


def test_data_processor_get_buffer():
    """Test buffer management."""
    redis_mock = AsyncMock()
    processor = DataProcessor(redis_mock)
    
    # Add to buffer
    processor.tick_buffer["BTCUSDT"] = [{"price": 50000}]
    
    buffer = processor.get_buffer("BTCUSDT")
    assert len(buffer) == 1
    
    # Clear buffer
    processor.clear_buffer("BTCUSDT")
    buffer = processor.get_buffer("BTCUSDT")
    assert len(buffer) == 0


def test_data_processor_stats():
    """Test statistics tracking."""
    redis_mock = AsyncMock()
    processor = DataProcessor(redis_mock)
    
    processor.processing_stats["ticks_processed"] = 100
    processor.processing_stats["errors"] = 5
    
    stats = processor.get_stats()
    
    assert stats["ticks_processed"] == 100
    assert stats["errors"] == 5
    assert "buffer_sizes" in stats
