import json
import urllib.request

url_ols = 'http://localhost:8000/api/analytics/ols'
url_spread = 'http://localhost:8000/api/analytics/spread?symbol1=BTCUSDT&symbol2=ETHUSDT&lookback=120'

try:
    data = json.dumps({"symbol1":"BTCUSDT","symbol2":"ETHUSDT","lookback":120}).encode('utf-8')
    req = urllib.request.Request(url_ols, data=data, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req)
    print('OLS response:')
    print(json.dumps(json.load(resp), indent=2))
except Exception as e:
    print('OLS error:', e)

try:
    resp = urllib.request.urlopen(url_spread)
    print('\nSPREAD response:')
    print(json.dumps(json.load(resp), indent=2))
except Exception as e:
    print('SPREAD error:', e)
