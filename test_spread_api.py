"""Test spread API to debug the error."""
import sys
import requests
import importlib

# Get actual data from API
print('Fetching BTCUSDT data...')
r1 = requests.get('http://localhost:8000/ohlc/BTCUSDT?interval=1m&limit=100')
data1 = r1.json()['data']

print('Fetching ETHUSDT data...')
r2 = requests.get('http://localhost:8000/ohlc/ETHUSDT?interval=1m&limit=100')
data2 = r2.json()['data']

prices1 = [d['close'] for d in data1]
prices2 = [d['close'] for d in data2]

print(f'Testing with {len(prices1)} samples')
print(f'Price1 range: [{min(prices1):.2f}, {max(prices1):.2f}]')
print(f'Price2 range: [{min(prices2):.2f}, {max(prices2):.2f}]')

# Import latest code
import src.analytics.statistical as stat_module
importlib.reload(stat_module)

from src.analytics.statistical import StatisticalAnalytics

print('\nTesting OLS regression...')
try:
    result = StatisticalAnalytics.ols_regression(prices1, prices2)
    print(f'SUCCESS!')
    print(f'  Hedge ratio: {result["hedge_ratio"]:.6f}')
    print(f'  R-squared: {result["r_squared"]:.6f}')
    print(f'  Fallback used: {result.get("fallback_used", False)}')
    if result.get("fallback_used"):
        print(f'  Fallback method: {result.get("fallback_method")}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# Now test the full spread analysis
print('\n\nTesting full spread analysis...')
try:
    r = requests.get('http://localhost:8000/analytics/spread?symbol1=BTCUSDT&symbol2=ETHUSDT&interval=1m&limit=100')
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        print('SUCCESS!')
        import json
        print(json.dumps(r.json(), indent=2)[:500])
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
