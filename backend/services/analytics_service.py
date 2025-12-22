"""Analytics service
Provides async methods used by API routers. Where possible this implementation
fetches OHLC from Redis (used by the sampling engine) and computes indicators,
ADF and cointegration using statsmodels/pandas. Falls back to synthetic values
when Redis or sufficient data is not available.
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
import statsmodels.api as sm

logger = logging.getLogger("backend.analytics.service")


class AnalyticsService:
    def __init__(self):
        logger.info("AnalyticsService initialized")

    async def _fetch_ohlc_closes(self, symbol: str, interval: str, lookback: int) -> List[float]:
        """Fetch close prices from Redis stored OHLC keys. Returns chronological list."""
        try:
            # import the running redis client from main at runtime to avoid circular import
            from ..main import redis_client

            if not redis_client:
                logger.debug("Redis client not available for analytics fetch")
                return []

            key = f"ohlc:{symbol}:{interval}"
            raw = await redis_client.zrevrange(key, 0, lookback - 1)
            closes = []
            for item in raw:
                try:
                    if isinstance(item, (bytes, bytearray)):
                        item = item.decode('utf-8')
                    o = json.loads(item)
                    closes.append(float(o.get('close', o.get('c', np.nan))))
                except Exception:
                    continue

            # zrevrange returns newest first; reverse to chronological order
            closes = list(reversed(closes))
            logger.debug(f"Fetched {len(closes)} closes for {symbol} {interval}")
            return closes
        except Exception as e:
            logger.exception(f"Error fetching OHLC from Redis: {e}")
            return []

    async def compute_indicators(self, symbol: str, indicators: List[str], lookback: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.info(f"compute_indicators called: {symbol}, indicators={indicators}, lookback={lookback}, params={params}")
        closes = await self._fetch_ohlc_closes(symbol, '1m', lookback)
        n = min(max(lookback, 10), 2000)

        if len(closes) < 20:
            # fallback to zeros if not enough data
            logger.warning(f"Not enough OHLC data for indicators ({symbol}), falling back to zeros")
            return {ind: [0] * n for ind in indicators}

        s = pd.Series(closes)
        result: Dict[str, Any] = {}

        if 'rsi' in indicators:
            period = int(params.get('rsi_period', 14)) if params else 14
            delta = s.diff()
            up = delta.clip(lower=0).fillna(0)
            down = -delta.clip(upper=0).fillna(0)
            ma_up = up.ewm(com=period - 1, adjust=False).mean()
            ma_down = down.ewm(com=period - 1, adjust=False).mean()
            rs = ma_up / (ma_down + 1e-12)
            rsi = 100 - (100 / (1 + rs))
            result['rsi'] = rsi.fillna(50).astype(float).tolist()

        if 'macd' in indicators:
            fast = int(params.get('macd_fast', 12)) if params else 12
            slow = int(params.get('macd_slow', 26)) if params else 26
            sig = int(params.get('macd_signal', 9)) if params else 9
            ema_fast = s.ewm(span=fast, adjust=False).mean()
            ema_slow = s.ewm(span=slow, adjust=False).mean()
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=sig, adjust=False).mean()
            hist = (macd - signal).fillna(0)
            result['macd'] = macd.fillna(0).astype(float).tolist()
            result['macd_signal'] = signal.fillna(0).astype(float).tolist()
            result['macd_histogram'] = hist.astype(float).tolist()

        if 'bollinger' in indicators or 'bollinger_bands' in indicators:
            window = int(params.get('bollinger_window', 20)) if params else 20
            ma = s.rolling(window=window, min_periods=1).mean()
            std = s.rolling(window=window, min_periods=1).std().fillna(0)
            upper = (ma + 2 * std).astype(float).tolist()
            lower = (ma - 2 * std).astype(float).tolist()
            middle = ma.astype(float).tolist()
            result['bollinger_upper'] = upper
            result['bollinger_lower'] = lower
            result['bollinger_middle'] = middle

        # Always include prices for alignment
        result['prices'] = s.astype(float).tolist()

        logger.debug(f"Indicators computed for {symbol}: keys={list(result.keys())}")
        return result

    async def adf_test(self, symbol: str, lookback: int) -> Dict[str, Any]:
        logger.info(f"adf_test called: {symbol}, lookback={lookback}")
        closes = await self._fetch_ohlc_closes(symbol, '1m', lookback)

        if len(closes) < 20:
            logger.warning(f"Not enough data for ADF ({symbol}), returning fallback")
            return {
                'adf_statistic': -1.0,
                'p_value': 1.0,
                'critical_values': {'1%': -3.5, '5%': -2.9, '10%': -2.6},
                'is_stationary': False,
                'observations': len(closes)
            }

        try:
            series = pd.Series(closes).dropna()
            res = adfuller(series.values, autolag='AIC')
            stat = float(res[0])
            pvalue = float(res[1])
            crit = {k: float(v) for k, v in res[4].items()}
            is_stationary = bool(pvalue < 0.05)  # Convert numpy.bool_ to Python bool
            result = {
                'adf_statistic': stat,
                'p_value': pvalue,
                'critical_values': crit,
                'is_stationary': is_stationary,
                'observations': len(series)
            }
            logger.debug(f"ADF result for {symbol}: {result}")
            return result
        except Exception as e:
            logger.exception(f"ADF computation failed: {e}")
            return {
                'adf_statistic': -1.0,
                'p_value': 1.0,
                'critical_values': {'1%': -3.5, '5%': -2.9, '10%': -2.6},
                'is_stationary': False,
                'observations': len(closes)
            }

    async def cointegration_test(self, symbol1: str, symbol2: str, lookback: int) -> Dict[str, Any]:
        logger.info(f"cointegration_test called: {symbol1}, {symbol2}, lookback={lookback}")
        closes1 = await self._fetch_ohlc_closes(symbol1, '1m', lookback)
        closes2 = await self._fetch_ohlc_closes(symbol2, '1m', lookback)

        if len(closes1) < 20 or len(closes2) < 20:
            logger.warning(f"Not enough data for cointegration ({symbol1}, {symbol2}), returning fallback")
            return {'cointegration_statistic': 0.0, 'p_value': 1.0, 'is_cointegrated': False}

        try:
            s1 = pd.Series(closes1)
            s2 = pd.Series(closes2)
            # align lengths
            n = min(len(s1), len(s2))
            s1 = s1.iloc[-n:]
            s2 = s2.iloc[-n:]
            # Basic sanity checks: ensure series have variance
            var1 = float(s1.var())
            var2 = float(s2.var())
            logger.debug(f"Cointegration inputs: n={n}, var1={var1}, var2={var2}")

            if not (np.isfinite(var1) and np.isfinite(var2)) or var1 == 0.0 or var2 == 0.0:
                logger.warning(f"Cointegration skipped - zero or invalid variance (var1={var1}, var2={var2})")
                return {'cointegration_statistic': 0.0, 'p_value': 1.0, 'is_cointegrated': False}

            stat, pvalue, _ = coint(s1.values, s2.values)
            # Handle NaN/None returns defensively
            stat_f = float(stat) if (stat is not None and np.isfinite(stat)) else 0.0
            pvalue_f = float(pvalue) if (pvalue is not None and np.isfinite(pvalue)) else 1.0
            is_cointegrated = bool(pvalue_f < 0.05)  # Convert numpy.bool_ to Python bool
            result = {'cointegration_statistic': stat_f, 'p_value': pvalue_f, 'is_cointegrated': is_cointegrated}
            logger.debug(f"Cointegration result: {result}")
            return result
        except Exception as e:
            logger.exception(f"Cointegration computation failed: {e}")
            return {'cointegration_statistic': 0.0, 'p_value': 1.0, 'is_cointegrated': False}

    async def compute_ols(self, symbol1: str, symbol2: str, lookback: int) -> Dict[str, Any]:
        logger.info(f"compute_ols called: {symbol1}, {symbol2}, lookback={lookback}")
        closes1 = await self._fetch_ohlc_closes(symbol1, '1m', lookback)
        closes2 = await self._fetch_ohlc_closes(symbol2, '1m', lookback)

        len1 = len(closes1)
        len2 = len(closes2)
        logger.debug(f"compute_ols fetched closes lengths: {symbol1}={len1}, {symbol2}={len2}")

        if len1 < 2 or len2 < 2:
            logger.warning(f"Not enough data for OLS ({symbol1}, {symbol2}) - fetched lengths: {len1}, {len2}")
            return {
                "hedge_ratio": 1.0,
                "alpha": 0.0,
                "r_squared": 0.0,
                "adj_r_squared": 0.0,
                "p_value": 1.0,
                "std_err": 0.0,
                "correlation": 0.0,
                "observations": 0,
                "timestamp": datetime.now().isoformat()
            }

        try:
            # We want to model: Symbol2 = alpha + hedge_ratio * Symbol1
            s1 = pd.Series(closes1)
            s2 = pd.Series(closes2)
            n = min(len(s1), len(s2))
            x = s1.iloc[-n:].astype(float)  # Symbol1
            y = s2.iloc[-n:].astype(float)  # Symbol2

            # If we have sufficient points, use statsmodels OLS for full diagnostics
            if n >= 5:
                X = sm.add_constant(x)
                model = sm.OLS(y, X).fit()
                # Access params using .iloc[] since statsmodels returns Series with named index
                hedge_ratio = float(model.params.iloc[1]) if len(model.params) > 1 else 1.0
                alpha = float(model.params.iloc[0]) if len(model.params) > 0 else 0.0
                std_err = float(model.bse.iloc[1]) if len(model.bse) > 1 else 0.0
                result = {
                    "hedge_ratio": hedge_ratio,
                    "alpha": alpha,
                    "r_squared": float(model.rsquared),
                    "adj_r_squared": float(model.rsquared_adj),
                    "p_value": float(model.f_pvalue) if model.f_pvalue is not None else 1.0,
                    "std_err": std_err,
                    "correlation": float(y.corr(x)),
                    "observations": int(n),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Best-effort using numpy.polyfit when few points exist
                try:
                    coef = np.polyfit(x.values, y.values, 1)
                    hedge_ratio = float(coef[0])
                    alpha = float(coef[1])
                    # compute r_squared manually
                    y_pred = hedge_ratio * x.values + alpha
                    ss_res = float(((y.values - y_pred) ** 2).sum())
                    ss_tot = float(((y.values - y.values.mean()) ** 2).sum())
                    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                    result = {
                        "hedge_ratio": hedge_ratio,
                        "alpha": alpha,
                        "r_squared": float(r_squared),
                        "adj_r_squared": float(r_squared),
                        "p_value": 1.0,
                        "std_err": 0.0,
                        "correlation": float(np.corrcoef(x.values, y.values)[0, 1]) if len(x) > 1 else 0.0,
                        "observations": int(n),
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.exception(f"Small-sample polyfit failed: {e}")
                    result = {
                        "hedge_ratio": 1.0,
                        "alpha": 0.0,
                        "r_squared": 0.0,
                        "adj_r_squared": 0.0,
                        "p_value": 1.0,
                        "std_err": 0.0,
                        "correlation": 0.0,
                        "observations": int(n),
                        "timestamp": datetime.now().isoformat()
                    }
            logger.debug(f"OLS result: {result}")
            return result
        except Exception as e:
            logger.exception(f"OLS computation failed: {e}")
            return {
                "hedge_ratio": 1.0,
                "alpha": 0.0,
                "r_squared": 0.0,
                "adj_r_squared": 0.0,
                "p_value": 1.0,
                "std_err": 0.0,
                "correlation": 0.0,
                "observations": 0,
                "timestamp": datetime.now().isoformat()
            }

    async def compute_spread(self, symbol1: str, symbol2: str, lookback: int, hedge_ratio: float = None) -> Dict[str, Any]:
        logger.info(f"compute_spread called: {symbol1}, {symbol2}, lookback={lookback}, hedge_ratio={hedge_ratio}")
        # If no hedge ratio provided, compute OLS
        ols = None
        if hedge_ratio is None:
            ols = await self.compute_ols(symbol1, symbol2, lookback)
            hedge_ratio = ols.get('hedge_ratio', 1.0)

        closes1 = await self._fetch_ohlc_closes(symbol1, '1m', lookback)
        closes2 = await self._fetch_ohlc_closes(symbol2, '1m', lookback)

        n = min(len(closes1), len(closes2))
        if n <= 0:
            logger.warning(f"Not enough data to compute spread ({symbol1},{symbol2})")
            return {
                'hedge_ratio': hedge_ratio,
                'r_squared': 0.0,
                'spread': [],
                'z_scores': [],
                'current_zscore': 0.0,
                'timestamps': []
            }

        s1 = np.array(closes1[-n:], dtype=float)
        s2 = np.array(closes2[-n:], dtype=float)
        # Spread definition: Symbol2 - hedge_ratio * Symbol1
        spread = s2 - hedge_ratio * s1
        mean = float(np.mean(spread))
        std = float(np.std(spread)) if np.std(spread) > 0 else 1e-9
        zscore = ((spread - mean) / std).tolist()
        timestamps = []
        try:
            from ..main import redis_client
            key = f"ohlc:{symbol1}:1m"
            raw = await redis_client.zrevrange(key, 0, n - 1)
            for item in reversed(raw):
                try:
                    if isinstance(item, (bytes, bytearray)):
                        item = item.decode('utf-8')
                    o = json.loads(item)
                    timestamps.append(int(o.get('timestamp')))
                except Exception:
                    timestamps.append(None)
        except Exception:
            timestamps = [None] * n

        boll_upper = (spread + 2 * std).tolist()
        boll_lower = (spread - 2 * std).tolist()

        result = {
            'hedge_ratio': hedge_ratio,
            'intercept': float(ols.get('alpha') if ols and 'alpha' in ols else 0.0),
            'r_squared': float(ols.get('r_squared') if ols and 'r_squared' in ols else 0.0),
            'spread': spread.tolist(),
            'spread_values': spread.tolist(),
            'spread_mean': float(mean),
            'spread_std': float(std),
            'observations': int(n),
            'z_scores': zscore,
            'current_zscore': float(zscore[-1]) if len(zscore) else 0.0,
            'bollinger_upper': boll_upper,
            'bollinger_lower': boll_lower,
            'bollinger_ma': float(mean),
            'timestamps': timestamps,
            'signal': 'LONG' if zscore[-1] <  -2 else 'SHORT' if zscore[-1] > 2 else 'NEUTRAL'
        }
        logger.debug(f"compute_spread result lengths: spread={len(spread)}, timestamps={len(timestamps)}")
        return result


# single instance used by API
analytics_service = AnalyticsService()
