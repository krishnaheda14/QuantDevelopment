"""
Check cointegration and ADF stability for a pair.
Usage:
    python tools/check_cointegration_adf.py BTCUSDT ETHUSDT --lookback 500

This script queries the local API and prints results. It also polls ADF across rolling windows to estimate stability.
"""
import sys
import time
import argparse
import requests

BASE = "http://localhost:8000"


def cointegration(symbol1, symbol2, lookback):
    url = f"{BASE}/api/analytics/cointegration/{symbol1}/{symbol2}?lookback={lookback}"
    r = requests.get(url, timeout=10)
    return r.status_code, r.text


def adf(symbol, lookback):
    url = f"{BASE}/api/analytics/adf/{symbol}?lookback={lookback}"
    r = requests.get(url, timeout=10)
    return r.status_code, r.text


def rolling_adf(symbol, lookback, windows=5, step=60):
    """Request ADF repeatedly with sliding end-time by asking backend for same lookback.
    Backend uses most recent data; by polling we simulate repeated evaluations over time."""
    results = []
    for i in range(windows):
        try:
            status, body = adf(symbol, lookback)
            if status == 200:
                results.append(body)
            else:
                results.append(f"HTTP {status}: {body}")
        except Exception as e:
            results.append(str(e))
        time.sleep(step / 1000.0)  # step in ms -> seconds
    return results


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('symbol1')
    p.add_argument('symbol2')
    p.add_argument('--lookback', type=int, default=500)
    p.add_argument('--adf-windows', type=int, default=5)
    p.add_argument('--adf-step-ms', type=int, default=1000)
    args = p.parse_args()

    print('Checking cointegration...')
    try:
        status, body = cointegration(args.symbol1, args.symbol2, args.lookback)
        print('Cointegration status:', status)
        print(body)
    except Exception as e:
        print('Cointegration request failed:', e)

    print('\nChecking ADF rolling windows...')
    try:
        res = rolling_adf(args.symbol1, args.lookback, windows=args.adf_windows, step=args.adf_step_ms)
        for i, r in enumerate(res):
            print(f'[{i}]', r)
    except Exception as e:
        print('ADF rolling check failed:', e)
