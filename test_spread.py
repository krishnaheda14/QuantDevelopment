"""Test script for spread analysis endpoints."""
import requests
import json
import sys

BASE = "http://localhost:8000"

def test_debug_endpoint():
    """Test the debug endpoint with synthetic data."""
    print("=" * 60)
    print("1. Testing /debug/test-data (analytics with synthetic data)")
    print("=" * 60)
    
    try:
        r = requests.get(f"{BASE}/debug/test-data", timeout=5)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"\n✓ SUCCESS! Analytics modules working correctly\n")
            print(f"OLS Results:")
            print(f"  - Hedge Ratio: {data['ols']['hedge_ratio']:.6f}")
            print(f"  - R²: {data['ols']['r_squared']:.6f}")
            print(f"  - Alpha: {data['ols']['alpha']:.6f}")
            print(f"\nSpread Stats:")
            print(f"  - Current Spread: {data['spread']['current_spread']:.6f}")
            print(f"  - Z-Score: {data['spread']['zscore']['current_zscore']:.6f}")
            return True
        else:
            print(f"\n✗ ERROR: Status {r.status_code}")
            print(f"Response: {r.text[:500]}")
            return False
    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")
        return False


def test_spread_endpoint():
    """Test the spread endpoint with real market data."""
    print("\n" + "=" * 60)
    print("2. Testing /analytics/spread (BTCUSDT vs ETHUSDT)")
    print("=" * 60)
    
    try:
        params = {
            "symbol1": "BTCUSDT",
            "symbol2": "ETHUSDT",
            "interval": "1m",
            "limit": 100
        }
        
        r = requests.get(f"{BASE}/analytics/spread", params=params, timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"\n✓ SUCCESS! Spread analysis completed\n")
            print(f"OLS Results:")
            print(f"  - Hedge Ratio: {data['data']['ols']['hedge_ratio']:.6f}")
            print(f"  - R²: {data['data']['ols']['r_squared']:.6f}")
            print(f"  - Alpha: {data['data']['ols']['alpha']:.6f}")
            print(f"\nSpread Stats:")
            print(f"  - Current Spread: {data['data']['spread']['current_spread']:.6f}")
            print(f"  - Z-Score: {data['data']['spread']['zscore']['current_zscore']:.6f}")
            print(f"\nDebug Info:")
            print(f"  - Query Time: {data['debug']['query_time_ms']:.2f} ms")
            print(f"  - Data Points: {data['debug']['data_points']}")
            return True
        else:
            print(f"\n✗ ERROR: Status {r.status_code}")
            print(f"Response: {r.text}")
            
            # Check for error log file
            print("\n--- Checking for error logs ---")
            try:
                with open('last_spread_error.log', 'r', encoding='utf-8') as f:
                    print(f.read())
            except FileNotFoundError:
                print("No last_spread_error.log file found")
            
            return False
    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adf_endpoint():
    """Test the ADF stationarity test endpoint."""
    print("\n" + "=" * 60)
    print("3. Testing /analytics/adf (BTCUSDT)")
    print("=" * 60)
    
    try:
        params = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 100
        }
        
        r = requests.get(f"{BASE}/analytics/adf", params=params, timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"\n✓ SUCCESS! ADF test completed\n")
            print(f"ADF Results:")
            print(f"  - ADF Statistic: {data['data']['adf_statistic']:.6f}")
            print(f"  - P-Value: {data['data']['p_value']:.6f}")
            print(f"  - Is Stationary: {data['data']['is_stationary']}")
            print(f"  - Interpretation: {data['data']['interpretation']}")
            return True
        else:
            print(f"\n✗ ERROR: Status {r.status_code}")
            print(f"Response: {r.text[:500]}")
            return False
    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GEMSCAP QUANT - ENDPOINT TESTS")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Debug endpoint (synthetic data)
    results.append(("Debug Endpoint", test_debug_endpoint()))
    
    # Test 2: Spread endpoint (real data)
    results.append(("Spread Endpoint", test_spread_endpoint()))
    
    # Test 3: ADF endpoint
    results.append(("ADF Endpoint", test_adf_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if all(p for _, p in results) else 1


if __name__ == "__main__":
    sys.exit(main())
