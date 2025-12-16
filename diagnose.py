"""Diagnostic script for testing spread endpoint."""
import requests
import sys
import json

BASE = "http://localhost:8000"

print("=== DIAGNOSING SPREAD ENDPOINT ===")

# Check server
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    print(f"✓ Server health: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"✗ Server not reachable: {e}")
    sys.exit(1)

print("\n=== Testing Spread Endpoint ===")

# Try spread endpoint
try:
    params = {
        "symbol1": "BTCUSDT",
        "symbol2": "ETHUSDT",
        "interval": "1m",
        "limit": 10
    }
    
    r = requests.get(f"{BASE}/analytics/spread", params=params, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}...")  # First 500 chars
    
    if r.status_code == 200:
        data = r.json()
        print("\n✓ Spread endpoint WORKING!")
        print(f"Hedge Ratio: {data.get('data', {}).get('hedge_ratio')}")
        print(f"Current Spread: {data.get('data', {}).get('current_spread')}")
        print(f"Z-Score: {data.get('data', {}).get('zscore', {}).get('current')}")
        print(f"\nFull response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\n✗ Spread endpoint FAILED")
        
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing Simple Spread (Dummy) ===")
try:
    r = requests.get(f"{BASE}/analytics/spread-simple", timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✓ Simple spread works: {r.json()}")
    else:
        print(f"✗ Simple spread failed: {r.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

print("\n=== Check Data Availability ===")
# Check individual symbols
for symbol in ["BTCUSDT", "ETHUSDT"]:
    try:
        r = requests.get(f"{BASE}/ohlc/{symbol}", params={"interval": "1m", "limit": 3}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            count = len(data.get('data', []))
            print(f"✓ {symbol}: {count} OHLC bars available")
            if count > 0:
                print(f"  Sample: {data['data'][0]}")
        else:
            print(f"✗ {symbol}: Failed ({r.status_code})")
    except Exception as e:
        print(f"✗ {symbol}: Error - {e}")

print("\n=== Testing Debug Endpoint ===")
try:
    r = requests.get(f"{BASE}/debug/test-data", timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Debug endpoint works!")
        print(f"  OLS hedge_ratio: {data.get('ols', {}).get('hedge_ratio')}")
        print(f"  Test status: {data.get('test_status')}")
    else:
        print(f"✗ Debug endpoint failed: {r.text[:200]}")
except Exception as e:
    print(f"✗ Debug endpoint error: {e}")

print("\n=== DIAGNOSIS COMPLETE ===")
