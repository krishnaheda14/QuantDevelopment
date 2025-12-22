import requests, json

URL = 'http://localhost:8000/api/analytics/backtest'
payload = {
    'symbol1': 'BTCUSDT',
    'symbol2': 'ETHUSDT',
    'entry_z': 2.0,
    'exit_z': 0.5,
    'stoploss_z': 3.0,
    'lookback': 500,
    'strategy': 'macd',
    'trade_size': 1.0,
    'commission': 0.0,
    'slippage': 0.0,
    'initial_capital': 100000.0,
    'params': {
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bollinger_window': 20,
        'rsi_period': 14
    }
}

print('Posting backtest payload to', URL)
resp = requests.post(URL, json=payload, timeout=60)
print('Status:', resp.status_code)
try:
    data = resp.json()
except Exception as e:
    print('Failed to decode JSON:', e)
    print(resp.text)
    raise

print('\nSummary:')
for k,v in data.get('summary', {}).items():
    print(' ', k, ':', v)

trades = data.get('trades', [])
print('\nTrades:', len(trades))
for t in trades[:10]:
    print(' ', {k: t.get(k) for k in ['entry_index','exit_index','pnl','pnl_pct','pnl_per_unit']})

equity = data.get('equity_curve', [])
print('\nEquity length:', len(equity))
if len(equity) > 1:
    changes = [equity[i] - equity[i-1] for i in range(1,len(equity))]
    non_zero = sum(1 for c in changes if abs(c) > 1e-9)
    print('Equity non-zero steps:', non_zero)
    print('Equity min/max:', min(equity), max(equity))

print('\nIndicator keys:', list(data.get('indicator_series', {}).keys()))
print('\nDone')
