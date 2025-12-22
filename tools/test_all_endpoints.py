"""
Comprehensive API Endpoint Test Suite
Tests all analytics endpoints and verifies responses
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, path: str, params: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
    """Test an endpoint and return results"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=10)
        
        return {
            "status": response.status_code,
            "ok": response.ok,
            "data": response.json() if response.ok else response.text[:200]
        }
    except Exception as e:
        return {
            "status": 0,
            "ok": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("GEMSCAP API Endpoint Test Suite")
    print("=" * 80)
    
    tests = [
        ("Health Check", "GET", "/health", None, None),
        ("Symbols List", "GET", "/symbols", None, None),
        ("Spread Analysis", "GET", "/api/analytics/spread", {"symbol1": "BTCUSDT", "symbol2": "ETHUSDT", "lookback": 120}, None),
        ("OLS Regression", "POST", "/api/analytics/ols", None, {"symbol1": "BTCUSDT", "symbol2": "ETHUSDT", "lookback": 120}),
        ("ADF Test", "POST", "/api/analytics/adf", None, {"symbol": "BTCUSDT", "lookback": 100}),
        ("Cointegration", "GET", "/api/analytics/cointegration", {"symbol1": "BTCUSDT", "symbol2": "ETHUSDT", "lookback": 100}, None),
        ("Indicators", "GET", "/api/analytics/indicators", {"symbol": "BTCUSDT", "lookback": 50}, None),
        ("Backtest", "POST", "/api/analytics/backtest", None, {"symbol1": "BTCUSDT", "symbol2": "ETHUSDT", "lookback": 200, "entry_threshold": 2.0, "exit_threshold": 0.5}),
    ]
    
    results = {}
    for name, method, path, params, json_data in tests:
        print(f"\nTesting: {name}")
        print(f"  {method} {path}")
        result = test_endpoint(method, path, params, json_data)
        results[name] = result
        
        if result["ok"]:
            print(f"  ✓ Status: {result['status']}")
            data = result["data"]
            if isinstance(data, dict):
                print(f"  ✓ Keys: {list(data.keys())[:5]}")  # Show first 5 keys
            elif isinstance(data, list):
                print(f"  ✓ Items: {len(data)}")
        else:
            print(f"  ✗ Status: {result['status']}")
            print(f"  ✗ Error: {result.get('error', result.get('data', 'Unknown error'))}")
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    passed = sum(1 for r in results.values() if r["ok"])
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
        for name, result in results.items():
            if not result["ok"]:
                print(f"  - {name}: {result.get('error', result.get('data'))}")

if __name__ == "__main__":
    main()
