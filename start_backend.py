"""
Start Backend Server
Launches FastAPI backend with all services
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("GEMSCAP Backend Server - Starting...")
    print("=" * 60)
    print()
    
    backend_path = Path(__file__).parent / "backend" / "main.py"
    
    if not backend_path.exists():
        print(f"Error: Backend file not found at {backend_path}")
        sys.exit(1)
    
    print("Starting FastAPI server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down backend...")
    except subprocess.CalledProcessError as e:
        print(f"Error running backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
