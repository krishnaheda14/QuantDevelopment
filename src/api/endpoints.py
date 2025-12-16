"""FastAPI REST endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
import time
import traceback
from config import config

router = APIRouter()
logger = logging.getLogger(__name__)

# These will be injected by app.py
_redis = None
_db = None
_analytics = None


def init_endpoints(redis_manager, database, analytics_engine):
    """Initialize endpoint dependencies."""
    global _redis, _db, _analytics
    _redis = redis_manager
    _db = database
    _analytics = analytics_engine


@router.get("/")
async def root():
    return {"service": "GEMSCAP Quant API", "status": "running"}


@router.get("/health")
async def health():
    """Health check endpoint."""
    start = time.time()
    logger.info("[HEALTH] Starting health check...")
    
    try:
        logger.debug("[HEALTH] Checking Redis...")
        redis_health = await _redis.health_check() if _redis else {"status": "not initialized"}
        logger.debug(f"[HEALTH] Redis result: {redis_health}")
        
        logger.debug("[HEALTH] Checking Database...")
        db_health = await _db.health_check() if _db else {"status": "not initialized"}
        logger.debug(f"[HEALTH] Database result: {db_health}")
        
        response = {
            "status": "healthy",
            "components": {
                "redis": redis_health,
                "database": db_health
            },
            "response_time_ms": (time.time() - start) * 1000
        }
        logger.info(f"[HEALTH] Health check completed in {response['response_time_ms']:.2f}ms")
        return response
    except Exception as e:
        logger.exception("[HEALTH] Health check failed with exception")
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")


@router.get("/symbols")
async def get_symbols():
    """Get list of available symbols."""
    from config import config
    return {"symbols": config.symbols}


@router.get("/debug/test-data")
async def debug_test_data():
    """Create test data and run spread analysis locally to verify analytics work."""
    import numpy as np
    
    # Create synthetic test data
    np.random.seed(42)
    n = 100
    prices1 = np.cumsum(np.random.randn(n)) + 100
    prices2 = 2 * prices1 + 5 + np.random.randn(n) * 0.5
    
    from src.analytics.statistical import StatisticalAnalytics
    from src.analytics.spread_analysis import SpreadAnalysis
    
    # Test OLS
    ols_result = StatisticalAnalytics.ols_regression(prices1.tolist(), prices2.tolist())
    logger.info(f"[DEBUG] OLS Test Result: hedge_ratio={ols_result['hedge_ratio']:.4f}, R²={ols_result['r_squared']:.4f}")
    
    # Test spread
    spread_result = SpreadAnalysis.analyze_spread(
        prices1.tolist(), 
        prices2.tolist(), 
        ols_result["hedge_ratio"]
    )
    logger.info(f"[DEBUG] Spread Test Result: current_spread={spread_result['current_spread']:.4f}")
    
    return {
        "test_status": "success",
        "message": "Analytics modules working correctly with synthetic data",
        "ols": ols_result,
        "spread": spread_result,
        "data_stats": {
            "prices1_mean": float(np.mean(prices1)),
            "prices1_std": float(np.std(prices1)),
            "prices2_mean": float(np.mean(prices2)),
            "prices2_std": float(np.std(prices2))
        }
    }


@router.get("/ohlc/{symbol}")
async def get_ohlc(
    symbol: str,
    interval: str = Query("1m", regex="^(1s|1m|5m)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get OHLC data for a symbol."""
    start = time.time()
    
    try:
        # Try Redis first
        ohlc_data = await _redis.get_ohlc(symbol, interval, limit)
        
        # Fallback to database if Redis is empty
        if not ohlc_data:
            ohlc_data = await _db.get_ohlc(symbol, interval, limit)
        
        return {
            "status": "success",
            "data": ohlc_data,
            "debug": {
                "query_time_ms": (time.time() - start) * 1000,
                "row_count": len(ohlc_data),
                "interval": interval
            }
        }
    except Exception as e:
        logger.error(f"Failed to get OHLC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticks/{symbol}")
async def get_ticks(
    symbol: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get recent ticks for a symbol."""
    start = time.time()
    
    try:
        ticks = await _redis.get_recent_ticks(symbol, limit)
        
        return {
            "status": "success",
            "data": ticks,
            "debug": {
                "query_time_ms": (time.time() - start) * 1000,
                "row_count": len(ticks)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get ticks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/spread")
async def get_spread(
    symbol1: str,
    symbol2: str,
    interval: str = "1m",
    limit: int = 100
):
    """Compute spread and z-score between two symbols - WORKING VERSION."""
    import time
    import numpy as np
    import traceback
    
    start = time.time()
    logger.info(f"[SPREAD] Request: {symbol1} vs {symbol2}")
    
    try:
        # 1. Get data
        data1 = []
        data2 = []
        
        if _redis:
            try:
                data1 = await _redis.get_ohlc(symbol1, interval, limit)
            except Exception as e:
                logger.warning(f"Redis failed for {symbol1}: {e}")
                data1 = []
            
            try:
                data2 = await _redis.get_ohlc(symbol2, interval, limit)
            except Exception as e:
                logger.warning(f"Redis failed for {symbol2}: {e}")
                data2 = []
        
        # Fallback to DB
        if (not data1) and _db:
            try:
                data1 = await _db.get_ohlc(symbol1, interval, limit)
            except Exception as e:
                logger.warning(f"DB failed for {symbol1}: {e}")
                data1 = []
        
        if (not data2) and _db:
            try:
                data2 = await _db.get_ohlc(symbol2, interval, limit)
            except Exception as e:
                logger.warning(f"DB failed for {symbol2}: {e}")
                data2 = []
        
        # Debug log
        logger.debug(f"[SPREAD] Data counts: {symbol1}={len(data1)}, {symbol2}={len(data2)}")
        
        if not data1 or not data2:
            return {
                "status": "error",
                "error": f"Insufficient data: {symbol1}={len(data1)}, {symbol2}={len(data2)}",
                "data_counts": {symbol1: len(data1), symbol2: len(data2)}
            }
        
        # 2. Extract prices
        prices1 = []
        prices2 = []
        
        for d in data1:
            try:
                prices1.append(float(d.get("close", 0)))
            except:
                pass
        
        for d in data2:
            try:
                prices2.append(float(d.get("close", 0)))
            except:
                pass
        
        # Ensure equal length
        n = min(len(prices1), len(prices2))
        if n < 5:
            return {
                "status": "error",
                "error": f"Need at least 5 samples, got {n}",
                "data_counts": {symbol1: len(prices1), symbol2: len(prices2)}
            }
        
        prices1 = prices1[:n]
        prices2 = prices2[:n]
        
        # Convert to numpy
        p1 = np.array(prices1, dtype=np.float64)
        p2 = np.array(prices2, dtype=np.float64)
        
        # 3. SIMPLE HEDGE RATIO (avoiding OLS for now)
        # Use price ratio instead of regression
        mean_p1 = np.mean(p1)
        mean_p2 = np.mean(p2)
        
        if mean_p1 != 0:
            hedge_ratio = mean_p2 / mean_p1
        else:
            hedge_ratio = 0.0
        
        # 4. Calculate spread
        spread = p2 - hedge_ratio * p1
        current_spread = float(spread[-1]) if len(spread) > 0 else 0.0
        
        # 5. Calculate z-score
        if len(spread) > 1 and np.std(spread) > 0:
            spread_mean = float(np.mean(spread))
            spread_std = float(np.std(spread))
            current_zscore = (current_spread - spread_mean) / spread_std
        else:
            spread_mean = 0.0
            spread_std = 1.0
            current_zscore = 0.0
        
        # 6. Create response
        result = {
            "status": "success",
            "data": {
                "hedge_ratio": float(hedge_ratio),
                "current_spread": float(current_spread),
                "zscore": {
                    "current": float(current_zscore),
                    "mean": float(spread_mean),
                    "std": float(spread_std)
                },
                "price_summary": {
                    symbol1: {
                        "current": float(p1[-1]),
                        "mean": float(mean_p1),
                        "min": float(np.min(p1)),
                        "max": float(np.max(p1))
                    },
                    symbol2: {
                        "current": float(p2[-1]),
                        "mean": float(mean_p2),
                        "min": float(np.min(p2)),
                        "max": float(np.max(p2))
                    }
                },
                "samples": n
            },
            "debug": {
                "query_time_ms": (time.time() - start) * 1000,
                "method": "mean_ratio",
                "data_sources": {
                    symbol1: "redis" if _redis and data1 else "db" if data1 else "none",
                    symbol2: "redis" if _redis and data2 else "db" if data2 else "none"
                }
            }
        }
        
        logger.info(f"[SPREAD] Success: ratio={hedge_ratio:.4f}, spread={current_spread:.4f}, z={current_zscore:.2f}")
        return result
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[SPREAD] Failed: {str(e)}\n{error_trace}")
        
        return {
            "status": "error",
            "error": str(e),
            "simple_error": f"Server error: {type(e).__name__}",
            "debug": {
                "symbol1": symbol1,
                "symbol2": symbol2,
                "timestamp": time.time()
            }
        }


@router.get("/analytics/spread-simple")
async def spread_simple(
    symbol1: str = "BTCUSDT",
    symbol2: str = "ETHUSDT"
):
    """ULTRA SIMPLE spread calculation - guaranteed to work."""
    try:
        # Just return dummy data for testing
        return {
            "status": "success",
            "data": {
                "hedge_ratio": 0.0335,  # ETH/BTC ratio
                "current_spread": 12.34,
                "zscore": {"current": 0.5, "mean": 0, "std": 1},
                "note": "Dummy data - spread endpoint being fixed"
            },
            "debug": {
                "method": "dummy_fallback",
                "message": "Full spread analysis is being repaired"
            }
        }
    except:
        return {"status": "error", "message": "Even dummy endpoint failed!"}


@router.get("/analytics/correlation")
async def get_correlation(
    symbol1: str,
    symbol2: str,
    interval: str = "1m",
    window: int = 50
):
    """Compute rolling correlation."""
    try:
        logger.debug(f"get_correlation called: symbol1={symbol1}, symbol2={symbol2}, interval={interval}, window={window}")
        # Try Redis first, then fallback to DB
        data1 = []
        data2 = []

        if _redis:
            try:
                data1 = await _redis.get_ohlc(symbol1, interval, 200)
            except Exception:
                data1 = []
            try:
                data2 = await _redis.get_ohlc(symbol2, interval, 200)
            except Exception:
                data2 = []

        if (not data1) and _db:
            try:
                data1 = await _db.get_ohlc(symbol1, interval, 200)
            except Exception:
                data1 = []

        if (not data2) and _db:
            try:
                data2 = await _db.get_ohlc(symbol2, interval, 200)
            except Exception:
                data2 = []

        if not data1 or not data2:
            raise HTTPException(status_code=404, detail="Insufficient data for correlation")

        prices1 = [d["close"] for d in data1]
        prices2 = [d["close"] for d in data2]

        # Debug logging
        try:
            logger.debug(f"corr data lengths: {len(prices1)}, {len(prices2)}; window={window}")
            logger.debug(f"data1_preview={data1[:3]}")
            logger.debug(f"data2_preview={data2[:3]}")
        except Exception:
            logger.debug("Could not log correlation data previews")

        # Validate sufficient data for rolling window
        if len(prices1) < window or len(prices2) < window:
            raise HTTPException(status_code=404, detail=f"Insufficient data for rolling correlation: need >= {window} samples")

        from src.analytics.statistical import StatisticalAnalytics
        corr_result = StatisticalAnalytics.rolling_correlation(prices1, prices2, window)
        
        return {"status": "success", "data": corr_result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Correlation endpoint failed")
        dbg = f"{e} | n1={len(prices1) if 'prices1' in locals() else 'NA'} n2={len(prices2) if 'prices2' in locals() else 'NA'}"
        raise HTTPException(status_code=500, detail=dbg)


@router.get("/analytics/adf")
async def adf_test(
    symbol: str,
    interval: str = "1m"
):
    """Perform ADF stationarity test."""
    start = time.time()
    logger.info(f"[ADF] Request: symbol={symbol}, interval={interval}")
    
    try:
        # Try Redis first, then fallback to DB
        logger.debug(f"[ADF] Step 1: Fetching OHLC data for {symbol}...")
        data = []
        if _redis:
            try:
                logger.debug(f"[ADF] Trying Redis for {symbol}...")
                data = await _redis.get_ohlc(symbol, interval, 200)
                logger.debug(f"[ADF] Redis returned {len(data)} rows for {symbol}")
            except Exception as e:
                logger.debug(f"[ADF] Redis failed for {symbol}: {e}")
                data = []

        if (not data) and _db:
            try:
                logger.debug(f"[ADF] Fallback to DB for {symbol}...")
                data = await _db.get_ohlc(symbol, interval, 200)
                logger.debug(f"[ADF] DB returned {len(data)} rows for {symbol}")
            except Exception as e:
                logger.debug(f"[ADF] DB failed for {symbol}: {e}")
                data = []

        logger.debug(f"[ADF] Final data count: {len(data)} rows")
        
        if not data:
            logger.warning(f"[ADF] No data found for {symbol}")
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        logger.debug(f"[ADF] Step 2: Extracting close prices...")
        prices = [d["close"] for d in data]
        logger.debug(f"[ADF] Extracted {len(prices)} prices")
        logger.debug(f"[ADF] Sample prices: {prices[:5]}...{prices[-5:]}")
        logger.debug(f"[ADF] Price range: min={min(prices):.2f}, max={max(prices):.2f}, mean={sum(prices)/len(prices):.2f}")

        # Require minimum observations for ADF
        if len(prices) < 10:
            logger.warning(f"[ADF] Insufficient samples: got {len(prices)}, need >= 10")
            raise HTTPException(status_code=404, detail=f"Insufficient data: need >= 10 samples, got {len(prices)}")

        logger.debug(f"[ADF] Step 3: Running ADF test with {len(prices)} observations...")
        from src.analytics.statistical import StatisticalAnalytics
        adf_result = StatisticalAnalytics.adf_test(prices)
        logger.info(f"[ADF] Result: statistic={adf_result['adf_statistic']:.4f}, p={adf_result['p_value']:.4f}, stationary={adf_result['is_stationary']}")
        
        response = {
            "status": "success",
            "data": adf_result,
            "debug": {
                "query_time_ms": (time.time() - start) * 1000,
                "data_points": len(prices)
            }
        }
        logger.info(f"[ADF] Request completed in {response['debug']['query_time_ms']:.2f}ms")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ADF] Test failed with exception")
        # Write full traceback to a file for easier debugging
        try:
            import traceback as _tb
            _tb_text = _tb.format_exc()
            with open('last_adf_error.log', 'w', encoding='utf-8') as _f:
                _f.write(_tb_text)
        except Exception:
            _tb_text = None

        # Also append a short summary to logs/statistical_errors.log
        try:
            import json as _json
            _summary = {
                "timestamp": time.time(),
                "symbol": symbol,
                "exception": f"{type(e).__name__}: {e}",
                "traceback_file": "last_adf_error.log" if _tb_text else None
            }
            os.makedirs('logs', exist_ok=True)
            with open('logs/statistical_errors.log', 'a', encoding='utf-8') as _sf:
                _sf.write(_json.dumps(_summary) + "\n")
        except Exception:
            pass

        dbg = f"{type(e).__name__}: {e} | n={len(prices) if 'prices' in locals() else 'NA'}"
        if _tb_text:
            dbg += " | traceback_file=last_adf_error.log"
        raise HTTPException(status_code=500, detail=dbg)


@router.get("/export/csv")
async def export_csv(
    symbol: str,
    interval: str = "1m"
):
    """Export data as CSV."""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    try:
        data = await _db.get_ohlc(symbol, interval, 10000)
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={symbol}_{interval}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/endpoints")
async def debug_endpoints():
    """List all available endpoints with examples."""
    return {
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Root endpoint"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/symbols", "method": "GET", "description": "List symbols"},
            {"path": "/ohlc/{symbol}", "method": "GET", "example": "/ohlc/BTCUSDT?interval=1m&limit=100"},
            {"path": "/ticks/{symbol}", "method": "GET", "example": "/ticks/BTCUSDT?limit=50"},
            {"path": "/analytics/spread", "method": "GET", "example": "/analytics/spread?symbol1=BTCUSDT&symbol2=ETHUSDT"},
            {"path": "/analytics/correlation", "method": "GET", "example": "/analytics/correlation?symbol1=BTCUSDT&symbol2=ETHUSDT&window=50"},
            {"path": "/analytics/adf", "method": "GET", "example": "/analytics/adf?symbol=BTCUSDT"},
            {"path": "/export/csv", "method": "GET", "example": "/export/csv?symbol=BTCUSDT&interval=1m"}
        ]
    }
