"""
Setup Verification Script

Checks that all dependencies and files are in place before running the app.
Run with: python check_setup.py
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version >= 3.9"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False

def check_dependencies():
    """Check required packages are installed"""
    required = [
        'streamlit',
        'plotly',
        'websockets',
        'pandas',
        'numpy',
        'scipy',
        'statsmodels',
        'psutil'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_files():
    """Check critical files exist"""
    root = Path(__file__).parent
    required_files = [
        'streamlit_main.py',
        'run.py',
        'requirements.txt',
        'src/__init__.py',
        'src/core/__init__.py',
        'src/core/data_manager.py',
        'src/core/strategy_engine.py',
        'src/analytics/__init__.py',
        'src/analytics/indicators.py',
        'src/analytics/backtester.py',
        'src/analytics/statistical.py',
    ]
    
    missing = []
    for file in required_files:
        path = root / file
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (missing)")
            missing.append(file)
    
    return len(missing) == 0, missing

def check_imports():
    """Check custom modules can be imported"""
    try:
        from src.core import DataManager, StrategyEngine
        from src.analytics import TechnicalIndicators, Backtester, StatisticalAnalytics
        print("✓ All custom modules import successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("GEMSCAP Quantitative Trading System - Setup Verification")
    print("=" * 60)
    print()
    
    print("1. Checking Python version...")
    py_ok = check_python_version()
    print()
    
    print("2. Checking dependencies...")
    deps_ok, missing_deps = check_dependencies()
    print()
    
    print("3. Checking project files...")
    files_ok, missing_files = check_files()
    print()
    
    print("4. Checking module imports...")
    imports_ok = check_imports()
    print()
    
    print("=" * 60)
    if py_ok and deps_ok and files_ok and imports_ok:
        print("✓ ALL CHECKS PASSED - Ready to run!")
        print()
        print("To start the application, run:")
        print("  python run.py")
        print("  OR")
        print("  streamlit run streamlit_main.py")
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        if not deps_ok:
            print()
            print("Missing dependencies:")
            for dep in missing_deps:
                print(f"  - {dep}")
            print()
            print("Install with: pip install -r requirements.txt")
        
        if not files_ok:
            print()
            print("Missing files:")
            for file in missing_files:
                print(f"  - {file}")
        
        if not imports_ok:
            print()
            print("Import errors - check that all files are present and valid")
        
        return 1
    
    print("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
