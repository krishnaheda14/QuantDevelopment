"""Analytics service stub
Provides async methods expected by API routers. Returns minimal synthetic results for testing.
"""
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

class AnalyticsService:
    def __init__(self):
        pass

    async def compute_ols(self, symbol1: str, symbol2: str, lookback: int) -> Dict[str, Any]:
        # Return synthetic OLS result
        return {
            "hedge_ratio": 1.0,
            "alpha": 0.0,
            "r_squared": 0.5,
            "adj_r_squared": 0.48,
            "p_value": 0.01,
            "std_err": 0.1,
            "correlation": 0.6,
            "observations": lookback,
            "timestamp": datetime.now().isoformat()
        }

    async def compute_spread(self, symbol1: str, symbol2: str, lookback: int, hedge_ratio: float = None) -> Dict[str, Any]:
        # synthetic time series
        n = min(max(lookback, 10), 500)
        timestamps = [int(datetime.now().timestamp()*1000) - i*60000 for i in range(n)][::-1]
        spread = list(np.random.normal(0,1,size=n))
        zscore = list((np.array(spread) - np.mean(spread))/ (np.std(spread)+1e-9))
        return {
            'spread': spread,
            'zscore': zscore,
            'bollinger_upper': (np.array(spread) + 2*np.std(spread)).tolist(),
            'bollinger_lower': (np.array(spread) - 2*np.std(spread)).tolist(),
            'bollinger_ma': (np.mean(spread)).tolist() if isinstance(np.mean(spread), (float,int)) else float(np.mean(spread)),
            'timestamps': timestamps,
            'current_zscore': float(zscore[-1]),
            'signal': 'NEUTRAL'
        }

    async def adf_test(self, symbol: str, lookback: int) -> Dict[str, Any]:
        return {
            'adf_statistic': -3.5,
            'p_value': 0.02,
            'critical_values': {'1%': -3.5, '5%': -2.9, '10%': -2.6},
            'is_stationary': True,
            'observations': lookback
        }

    async def cointegration_test(self, symbol1: str, symbol2: str, lookback: int) -> Dict[str, Any]:
        return {'trace_stat': 10.0, 'crit_values': {'5%': 15.0}, 'is_cointegrated': False}

    async def rolling_correlation(self, symbol1: str, symbol2: str, window: int, lookback: int) -> Dict[str, Any]:
        n = min(max(lookback, 10), 500)
        corr = list(np.random.uniform(-1,1,size=n))
        timestamps = [int(datetime.now().timestamp()*1000) - i*60000 for i in range(n)][::-1]
        return {'correlation': corr, 'timestamps': timestamps}

    async def compute_indicators(self, symbol: str, indicators: List[str], lookback: int) -> Dict[str, Any]:
        # return minimal indicator shapes
        n = min(max(lookback, 10), 500)
        timestamps = [int(datetime.now().timestamp()*1000) - i*60000 for i in range(n)][::-1]
        return {ind: [0]*n for ind in indicators}

# single instance used by API
analytics_service = AnalyticsService()
