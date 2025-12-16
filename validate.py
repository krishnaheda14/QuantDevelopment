"""System validation and pre-flight checks."""
import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        return False
    else:
        print("✅ Python version OK")
        return True


def check_redis():
    """Check if Redis is accessible."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        r.ping()
        print("✅ Redis connection OK")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Start Redis with: redis-server")
        return False


def check_dependencies():
    """Check if key dependencies are installed."""
    required = [
        'fastapi', 'uvicorn', 'streamlit', 'redis', 'pandas',
        'numpy', 'statsmodels', 'plotly', 'websockets'
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed")
        return True


def check_file_structure():
    """Check if all required files exist."""
    required_files = [
        'app.py',
        'streamlit_app.py',
        'config.py',
        'requirements.txt',
        'src/ingestion/websocket_client.py',
        'src/storage/redis_manager.py',
        'src/storage/database.py',
        'src/analytics/statistical.py',
        'src/api/endpoints.py'
    ]
    
    missing = []
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} not found")
            missing.append(file)
    
    if missing:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All required files present")
        return True


def test_imports():
    """Test if local modules can be imported."""
    try:
        from config import config
        print(f"✅ Config loaded: {len(config.symbols)} symbols")
        
        from src.storage.redis_manager import RedisManager
        print("✅ RedisManager importable")
        
        from src.analytics.statistical import StatisticalAnalytics
        print("✅ StatisticalAnalytics importable")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("  GEMSCAP QUANT PROJECT - VALIDATION")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("File Structure", check_file_structure),
        ("Module Imports", test_imports),
        ("Redis Connection", check_redis)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n📋 Checking: {name}")
        print("-" * 60)
        result = check_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("  VALIDATION SUMMARY")
    print("=" * 60)
    print()
    
    all_passed = True
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 All checks passed! System is ready to run.")
        print()
        print("Next steps:")
        print("  1. Start Redis: redis-server")
        print("  2. Run backend: python app.py")
        print("  3. Run dashboard: streamlit run streamlit_app.py")
        print()
        print("Or use the startup script: .\\start.ps1")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
