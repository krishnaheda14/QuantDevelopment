import requests
import json
import time

# Wait for server to be ready
time.sleep(2)

print("Testing spread analysis endpoint...")
url = "http://localhost:8000/analytics/spread?symbol1=BTCUSDT&symbol2=ETHUSDT&interval=1m&limit=100"

try:
    r = requests.get(url)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print("\n✓ SUCCESS! Spread analysis endpoint working!")
        print(f"\nOLS Results:")
        print(f"  - Hedge Ratio: {data.get('ols', {}).get('hedge_ratio')}")
        print(f"  - R²: {data.get('ols', {}).get('r_squared')}")
        print(f"  - Alpha: {data.get('ols', {}).get('alpha')}")
        print(f"\nSpread Stats:")
        print(f"  - Mean: {data.get('spread_stats', {}).get('mean')}")
        print(f"  - Z-Score: {data.get('spread_stats', {}).get('z_score')}")
    else:
        print(f"\n✗ ERROR: Status {r.status_code}")
        print(r.text[:500])
        
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}")
