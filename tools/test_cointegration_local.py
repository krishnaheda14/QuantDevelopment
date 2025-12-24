"""Local test script for cointegration_test using synthetic log-price series.

Run: python tools/test_cointegration_local.py

This script monkeypatches AnalyticsService._fetch_ohlc_closes to return synthetic prices
so the cointegration flow can be exercised without Redis.
"""
import asyncio
import math
import random
import sys
from pathlib import Path
from datetime import datetime

# ensure project root is on sys.path so `backend` package can be imported
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.services.analytics_service import AnalyticsService


def gbm_prices(S0, mu, sigma, n):
    prices = [S0]
    for _ in range(n - 1):
        dt = 1.0
        eps = random.gauss(0, 1)
        Sprev = prices[-1]
        Snew = Sprev * math.exp((mu - 0.5 * sigma * sigma) * dt + sigma * math.sqrt(dt) * eps)
        prices.append(Snew)
    return prices


async def run():
    svc = AnalyticsService()

    # monkeypatch _fetch_ohlc_closes to return synthetic series
    async def fake_fetch(symbol, interval, lookback):
        # produce different scales but cointegrated in log-space
        n = max(lookback, 60)
        if symbol == 'BTCUSDT':
            return gbm_prices(90000, 0.0001, 0.01, n)
        elif symbol == 'ETHUSDT':
            # roughly proportional to BTC but different scale
            base = gbm_prices(3000, 0.0001, 0.01, n)
            # introduce proportional relation: ETH ≈ BTC^0.3 * const (in logs linear)
            return [b ** 0.3 * 0.5 for b in base]
        else:
            return gbm_prices(100, 0.0001, 0.01, n)

    svc._fetch_ohlc_closes = fake_fetch

    # run cointegration test
    res = await svc.cointegration_test('BTCUSDT', 'ETHUSDT', lookback=120, interval='1s')
    print('Cointegration test result:')
    for k, v in res.items():
        print(f"{k}: {v}")

if __name__ == '__main__':
    asyncio.run(run())
