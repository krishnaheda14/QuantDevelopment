"""
Start Frontend Application
Launches Streamlit frontend that connects to backend APIs
"""

import subprocess
import sys
from pathlib import Path
import time
import socket

def check_backend_running():
    """Check if backend is running on port 8000"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print("=" * 60)
    print("GEMSCAP Frontend - Starting...")
    print("=" * 60)
    print()
    
    # Check if backend is running
    if not check_backend_running():
        print("⚠ Warning: Backend not detected on localhost:8000")
        print("  Please start the backend first with: python start_backend.py")
        print()
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    else:
        print("✓ Backend detected at http://localhost:8000")
        print()
    
    frontend_path = Path(__file__).parent / "frontend" / "app.py"
    
    if not frontend_path.exists():
        print(f"Error: Frontend file not found at {frontend_path}")
        sys.exit(1)
    
    print("Starting Streamlit on http://localhost:8501")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(frontend_path),
            "--server.port=8501",
            "--server.address=localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down frontend...")
    except subprocess.CalledProcessError as e:
        print(f"Error running frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
