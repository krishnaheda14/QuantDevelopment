"""
Analytics API Endpoints
Real-time statistical analysis, spread calculation, OLS, ADF, correlation
"""

from fastapi import APIRouter, HTTPException, Query
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import numpy as np

from ..services.analytics_service import AnalyticsService

router = APIRouter()
analytics_service = AnalyticsService()
logger = logging.getLogger("backend.analytics")


class OLSRequest(BaseModel):
    symbol1: str
    symbol2: str
    lookback: int = 30  # minutes


class OLSResponse(BaseModel):
    hedge_ratio: float
    alpha: float
    r_squared: float
    adj_r_squared: float
    p_value: float
    std_err: float
    correlation: float
    observations: int
    timestamp: str


class SpreadRequest(BaseModel):
    symbol1: str
    symbol2: str
    lookback: int = 30
    hedge_ratio: Optional[float] = None  # If None, will compute OLS first


class SpreadResponse(BaseModel):
    spread: List[float]
    zscore: List[float]
    bollinger_upper: List[float]
    bollinger_lower: List[float]
    bollinger_ma: List[float]
    timestamps: List[int]
    current_zscore: float
    signal: str  # "LONG", "SHORT", "NEUTRAL"


class ADFRequest(BaseModel):
    symbol: str
    lookback: int = 60
    # optional rolling-window check (non-invasive)
    rolling_window: Optional[int] = None
    rolling_step: Optional[int] = None
    rolling_threshold: Optional[float] = 0.7


class ADFResponse(BaseModel):
    adf_statistic: float
    p_value: float
    critical_values: dict
    is_stationary: bool
    observations: int
    # Optional rolling-window summary
    stationary_pct: Optional[float] = None
    is_stationary_by_threshold: Optional[bool] = None


@router.post("/ols", response_model=OLSResponse)
async def compute_ols(request: OLSRequest):
    """
    Compute OLS regression for pairs trading
    Returns hedge ratio, R², correlation, etc.
    """
    logger.info(f"API /ols called - symbol1={request.symbol1} symbol2={request.symbol2} lookback={request.lookback}")
    try:
        result = await analytics_service.compute_ols(
            request.symbol1,
            request.symbol2,
            request.lookback
        )
        logger.debug(f"/ols result keys={list(result.keys())}")
        return result
    except Exception as e:
        logger.exception("/ols failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spread", response_model=SpreadResponse)
async def compute_spread(request: SpreadRequest):
    """
    Compute spread, z-score, and Bollinger Bands
    Generates trading signals based on z-score thresholds
    """
    logger.info(f"API /spread POST called - symbol1={request.symbol1} symbol2={request.symbol2} lookback={request.lookback} hedge_ratio={request.hedge_ratio}")
    try:
        result = await analytics_service.compute_spread(
            request.symbol1,
            request.symbol2,
            request.lookback,
            request.hedge_ratio
        )
        logger.debug(f"/spread result spread_len={len(result.get('spread', []))}")
        return result
    except Exception as e:
        logger.exception("/spread failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spread")
async def compute_spread_get(
    symbol1: Optional[str] = Query(None),
    symbol2: Optional[str] = Query(None),
    lookback: Optional[int] = Query(100),
    hedge_ratio: Optional[float] = Query(None)
):
    """
    GET version: Compute spread, z-score, and Bollinger Bands
    """
    logger.info(f"API /spread GET called - symbol1={symbol1} symbol2={symbol2} lookback={lookback}")
    
    if not symbol1 or not symbol2:
        logger.warning(f"/spread called with missing symbols: symbol1={symbol1}, symbol2={symbol2}")
        raise HTTPException(status_code=400, detail="Both symbol1 and symbol2 are required")
    
    # Ensure lookback is valid
    if lookback is None:
        lookback = 100
    lookback = max(20, min(int(lookback), 1440))
    
    try:
        result = await analytics_service.compute_spread(
            symbol1,
            symbol2,
            lookback,
            hedge_ratio
        )
        logger.info(f"/spread success: spread_len={len(result.get('spread', []))}")
        return result
    except Exception as e:
        logger.exception(f"/spread failed for {symbol1}/{symbol2}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adf", response_model=ADFResponse)
async def adf_test(request: ADFRequest):
    """
    Augmented Dickey-Fuller test for stationarity
    Tests if a time series has a unit root
    """
    logger.info(f"API /adf POST called - symbol={request.symbol} lookback={request.lookback}")
    try:
        result = await analytics_service.adf_test(
            request.symbol,
            request.lookback,
            request.rolling_window,
            request.rolling_step,
            request.rolling_threshold
        )
        logger.debug(f"/adf result keys={list(result.keys())}")
        return result
    except Exception as e:
        logger.exception("/adf failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adf")
async def adf_test_get(
    symbol: Optional[str] = Query(None),
    lookback: Optional[int] = Query(60),
    rolling_window: Optional[int] = Query(None),
    rolling_step: Optional[int] = Query(1),
    rolling_threshold: float = Query(0.7)
):
    """
    GET version: Augmented Dickey-Fuller test for stationarity
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol query parameter is required")
    
    # Ensure lookback is valid
    if lookback is None:
        lookback = 60
    lookback = max(20, min(int(lookback), 1440))
    
    logger.info(f"API /adf GET called - symbol={symbol} lookback={lookback} rolling_window={rolling_window} rolling_step={rolling_step} rolling_threshold={rolling_threshold}")
    try:
        result = await analytics_service.adf_test(
            symbol,
            lookback,
            rolling_window,
            rolling_step,
            rolling_threshold
        )
        logger.debug(f"/adf (GET) result keys={list(result.keys())}")
        return result
    except Exception as e:
        logger.exception("/adf (GET) failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cointegration/{symbol1}/{symbol2}")
async def cointegration_test(
    symbol1: str,
    symbol2: str,
    lookback: int = Query(60, ge=20, le=1440),
    interval: str = Query('1s')
):
    """
    Engle-Granger cointegration test
    Tests if two time series are cointegrated (log prices)
    """
    logger.info(f"[API] GET /cointegration/{symbol1}/{symbol2} - lookback={lookback}, interval={interval}")
    try:
        result = await analytics_service.cointegration_test(
            symbol1,
            symbol2,
            lookback,
            interval
        )
        logger.info(f"[API] /cointegration result: stat={result.get('cointegration_statistic')}, obs={result.get('observations')}")
        from fastapi.responses import JSONResponse
        # Return with no-cache headers to prevent stale responses
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.exception("[API] /cointegration failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cointegration")
async def cointegration_test_query(
    symbol1: Optional[str] = Query(None),
    symbol2: Optional[str] = Query(None),
    lookback: Optional[int] = Query(100),
    interval: str = Query('1s')
):
    """
    Query param version: Engle-Granger cointegration test
    """
    if not symbol1 or not symbol2:
        raise HTTPException(status_code=400, detail="Both symbol1 and symbol2 are required")
    
    # Ensure lookback is valid
    if lookback is None:
        lookback = 100
    lookback = max(20, min(int(lookback), 1440))
    
    logger.info(f"[API] GET /cointegration (query) - {symbol1} vs {symbol2}, lookback={lookback}, interval={interval}")
    try:
        result = await analytics_service.cointegration_test(
            symbol1,
            symbol2,
            lookback,
            interval
        )
        logger.info(f"[API] /cointegration (query) result: stat={result.get('cointegration_statistic')}, obs={result.get('observations')}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.exception("[API] /cointegration (query) failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation/{symbol1}/{symbol2}")
async def rolling_correlation(
    symbol1: str,
    symbol2: str,
    window: int = Query(30, ge=10, le=120),
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Rolling correlation between two symbols
    Returns time series of correlation values
    """
    logger.info(f"API /correlation called - symbol1={symbol1} symbol2={symbol2} window={window} lookback={lookback}")
    try:
        result = await analytics_service.rolling_correlation(
            symbol1,
            symbol2,
            window,
            lookback
        )
        logger.debug(f"/correlation result length={len(result.get('correlation', []))}")
        return result
    except Exception as e:
        logger.exception("/correlation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators/{symbol}")
async def technical_indicators(
    symbol: str,
    indicators: List[str] = Query(["rsi", "macd", "bollinger"]),
    lookback: int = Query(60, ge=20, le=1440)
):
    """
    Compute technical indicators (RSI, MACD, Bollinger, etc.)
    Returns requested indicators for the symbol
    """
    logger.info(f"API /indicators called - symbol={symbol} indicators={indicators} lookback={lookback}")
    try:
        result = await analytics_service.compute_indicators(
            symbol,
            indicators,
            lookback
        )
        logger.debug(f"/indicators result keys={list(result.keys())}")
        return result
    except Exception as e:
        logger.exception("/indicators failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators")
async def technical_indicators_query(
    symbol: Optional[str] = Query(None),
    lookback: Optional[int] = Query(100)
):
    """
    Query param version: Compute technical indicators
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol query parameter is required")
    
    # Ensure lookback is valid
    if lookback is None:
        lookback = 100
    lookback = max(20, min(int(lookback), 1440))
    
    logger.info(f"API /indicators (query) called - symbol={symbol} lookback={lookback}")
    try:
        result = await analytics_service.compute_indicators(
            symbol,
            ["rsi", "macd", "bollinger"],
            lookback
        )
        logger.debug(f"/indicators (query) result keys={list(result.keys())}")
        return result
    except Exception as e:
        logger.exception("/indicators (query) failed")
        raise HTTPException(status_code=500, detail=str(e))


class BacktestRequest(BaseModel):
    symbol1: str
    symbol2: str
    entry_z: float = 2.0
    exit_z: float = 0.5
    stoploss_z: float = 3.0
    lookback: int = 500
    # additional optional parameters
    trade_size: float = 1.0
    commission: float = 0.0
    slippage: float = 0.0
    initial_capital: float = 100000.0
    strategy: Optional[str] = 'zscore'
    params: Optional[Dict[str, Any]] = None


@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a simple pairs trading backtest using z-score entry/exit thresholds.
    Returns trades and summary statistics.
    """
    logger.info(f"API /backtest called: {request.symbol1}/{request.symbol2} entry={request.entry_z} exit={request.exit_z} stop={request.stoploss_z} lookback={request.lookback}")
    try:
        data = await analytics_service.compute_spread(request.symbol1, request.symbol2, request.lookback)
        z = data.get('z_scores') or data.get('zscore') or []
        spread = data.get('spread') or data.get('spread_values') or []
        hedge = float(data.get('hedge_ratio', 1.0))
        timestamps = data.get('timestamps') or []

        # prepare closes for alternative strategies (single-symbol indicators)
        closes1 = await analytics_service._fetch_ohlc_closes(request.symbol1, '1m', request.lookback)
        closes2 = await analytics_service._fetch_ohlc_closes(request.symbol2, '1m', request.lookback)
        indicators = await analytics_service.compute_indicators(request.symbol1, ['rsi', 'macd', 'bollinger'], request.lookback, params=request.params or {})
        rsi = indicators.get('rsi', [])
        macd = indicators.get('macd', [])
        macd_signal = indicators.get('macd_signal', [])
        macd_hist = indicators.get('macd_histogram', [])
        bollinger_upper = indicators.get('bollinger_upper', [])
        bollinger_lower = indicators.get('bollinger_lower', [])

        trades = []
        position = 0  # 1 = long spread (buy symbol2, sell symbol1), -1 = short spread
        entry_idx = None
        entry_spread = None

        # Strategy selector: support 'zscore' (pairs), 'rsi' and 'macd' (single-symbol)
        strat = (request.strategy or 'zscore').lower()
        for i in range(len(z)):
            zi = z[i]
            s = spread[i] if i < len(spread) else None
            if s is None:
                continue
            # z-score pairs strategy
            if strat == 'zscore':
                # entry
                if position == 0 and abs(zi) >= request.entry_z:
                    position = -1 if zi > 0 else 1
                    entry_idx = i
                    entry_spread = s
                # exit
                elif position != 0 and abs(zi) <= request.exit_z:
                    pnl_per_unit = (entry_spread - s) * position
                    pnl = pnl_per_unit * request.trade_size - request.commission - (request.slippage * abs(pnl_per_unit) * request.trade_size)
                    pnl_pct = (pnl / request.initial_capital) if request.initial_capital else 0.0
                    trades.append({'entry_index': entry_idx, 'exit_index': i, 'entry_z': z[entry_idx], 'exit_z': zi, 'pnl': pnl, 'pnl_per_unit': pnl_per_unit, 'pnl_pct': pnl_pct})
                    position = 0
                    entry_idx = None
                    entry_spread = None
                # stoploss
                elif position != 0 and abs(zi) >= request.stoploss_z:
                    pnl_per_unit = (entry_spread - s) * position
                    pnl = pnl_per_unit * request.trade_size - request.commission - (request.slippage * abs(pnl_per_unit) * request.trade_size)
                    pnl_pct = (pnl / request.initial_capital) if request.initial_capital else 0.0
                    trades.append({'entry_index': entry_idx, 'exit_index': i, 'entry_z': z[entry_idx], 'exit_z': zi, 'pnl': pnl, 'pnl_per_unit': pnl_per_unit, 'pnl_pct': pnl_pct, 'stopped': True})
                    position = 0
                    entry_idx = None
                    entry_spread = None
            # RSI single-symbol strategy (on symbol1 closes)
            elif strat == 'rsi':
                # align rsi length to i via offset if necessary
                ri = rsi[i] if i < len(rsi) else None
                price = closes1[i] if i < len(closes1) else None
                if price is None or ri is None:
                    continue
                rsi_buy = float(request.params.get('rsi_buy', 30)) if request.params else 30.0
                rsi_sell = float(request.params.get('rsi_sell', 50)) if request.params else 50.0
                if position == 0 and ri <= rsi_buy:
                    position = 1
                    entry_idx = i
                    entry_spread = price
                elif position == 1 and ri >= rsi_sell:
                    pnl_per_unit = (price - entry_spread) * position
                    pnl = pnl_per_unit * request.trade_size - request.commission - (request.slippage * abs(pnl_per_unit) * request.trade_size)
                    pnl_pct = (pnl / request.initial_capital) if request.initial_capital else 0.0
                    trades.append({'entry_index': entry_idx, 'exit_index': i, 'entry_rsi': rsi[entry_idx] if entry_idx < len(rsi) else None, 'exit_rsi': ri, 'pnl': pnl, 'pnl_per_unit': pnl_per_unit, 'pnl_pct': pnl_pct})
                    position = 0
                    entry_idx = None
                    entry_spread = None
            # MACD histogram strategy (single-symbol)
            elif strat == 'macd':
                mh = macd_hist[i] if i < len(macd_hist) else None
                price = closes1[i] if i < len(closes1) else None
                if price is None or mh is None:
                    continue
                # bullish when hist crosses above 0
                prev_mh = macd_hist[i-1] if i-1 >= 0 and (i-1) < len(macd_hist) else None
                if position == 0 and prev_mh is not None and prev_mh <= 0 and mh > 0:
                    position = 1
                    entry_idx = i
                    entry_spread = price
                elif position == 1 and prev_mh is not None and prev_mh >= 0 and mh < 0:
                    pnl_per_unit = (price - entry_spread) * position
                    pnl = pnl_per_unit * request.trade_size - request.commission - (request.slippage * abs(pnl_per_unit) * request.trade_size)
                    pnl_pct = (pnl / request.initial_capital) if request.initial_capital else 0.0
                    trades.append({'entry_index': entry_idx, 'exit_index': i, 'pnl': pnl, 'pnl_per_unit': pnl_per_unit, 'pnl_pct': pnl_pct})
                    position = 0
                    entry_idx = None
                    entry_spread = None

        # If still in position at the end, close at last
        if position != 0 and entry_idx is not None and len(spread) > 0:
            s = spread[-1]
            pnl_per_unit = (entry_spread - s) * position
            pnl = pnl_per_unit * request.trade_size - request.commission - (request.slippage * abs(pnl_per_unit) * request.trade_size)
            pnl_pct = (pnl / request.initial_capital) if request.initial_capital else 0.0
            trades.append({'entry_index': entry_idx, 'exit_index': len(spread)-1, 'entry_z': z[entry_idx], 'exit_z': z[-1] if z else None, 'pnl': pnl, 'pnl_per_unit': pnl_per_unit, 'pnl_pct': pnl_pct, 'closed_end': True})

        total_pnl = float(sum(float(t.get('pnl', 0.0)) for t in trades))
        wins = sum(1 for t in trades if float(t.get('pnl', 0.0)) > 0)
        losses = sum(1 for t in trades if float(t.get('pnl', 0.0)) <= 0)
        win_rate = (wins / len(trades)) if trades else 0.0
        avg_pnl = (total_pnl / len(trades)) if trades else 0.0
        # percentage returns relative to initial capital (fractions)
        try:
            total_return = (total_pnl / float(request.initial_capital)) if request.initial_capital else 0.0
            avg_trade_return = (avg_pnl / float(request.initial_capital)) if request.initial_capital else 0.0
        except Exception:
            total_return = 0.0
            avg_trade_return = 0.0

        # build equity curve from trades
        zlen = len(z) or len(spread)
        equity = [0.0] * zlen
        cum = 0.0
        # Apply PnL at exit indices
        for t in trades:
            ei = int(t.get('exit_index', -1))
            pnl = float(t.get('pnl', 0.0))
            if 0 <= ei < zlen:
                equity[ei] += pnl
        for i in range(zlen):
            cum += equity[i]
            equity[i] = request.initial_capital + cum

        # compute returns for Sharpe
        returns = []
        for i in range(1, len(equity)):
            returns.append(equity[i] - equity[i-1])
        sharpe = None
        if len(returns) > 1:
            import math
            mean = sum(returns) / len(returns)
            std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
            if std > 0:
                sharpe = (mean / std) * (252 ** 0.5)

        # compute max drawdown
        max_dd = None
        if len(equity) > 0:
            peak = -float('inf')
            maxdd = 0.0
            for v in equity:
                if v > peak:
                    peak = v
                dd = peak - v
                if peak > 0:
                    maxdd = max(maxdd, dd / max(1e-9, peak))
            max_dd = maxdd

        # include the actual strategy params used for transparency
        strategy_params_used = request.params or {}

        summary = {
            'num_trades': len(trades),
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'total_return': total_return,
            'avg_trade_return': avg_trade_return,
            'win_rate': win_rate,
            'hedge_ratio': hedge,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'strategy_params_used': strategy_params_used,
        }

        # also provide percent series for visibility in frontend
        equity_pct = []
        for v in equity:
            try:
                equity_pct.append(((v - request.initial_capital) / request.initial_capital) * 100.0)
            except Exception:
                equity_pct.append(0.0)

        logger.debug(f"backtest summary: num_trades={len(trades)}, total_pnl={total_pnl}, total_return={summary.get('total_return')}, avg_trade_return={summary.get('avg_trade_return')}, equity_len={len(equity)}")

        # return detailed payload including z/spread and equity curve
        return {
            'summary': summary,
            'trades': trades,
            'equity_curve': equity,
            'equity_pct': equity_pct,
            'z_scores': z,
            'spread': spread,
            'timestamps': timestamps,
            'indicator_series': indicators,
        }
    except Exception as e:
        logger.exception('/backtest failed')
        raise HTTPException(status_code=500, detail=str(e))
