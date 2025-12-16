"""
GEMSCAP Quantitative Trading System - Launcher

Simple launcher that starts the Streamlit application.
Run with: python run.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit application."""
    app_file = Path(__file__).parent / "streamlit_main.py"
    
    if not app_file.exists():
        print(f"Error: Application file not found at {app_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("GEMSCAP Quantitative Trading System")
    print("Starting Streamlit application...")
    print("=" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--server.port=8501",
            "--server.address=localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
