"""Backend package initialization

Note: avoid importing `main` at package import time to prevent
heavy dependencies (FastAPI) from being required for simple imports
(e.g., during test/import of service modules).
To access the FastAPI app, import `backend.main.app` explicitly.
"""

__version__ = "2.0.0"

__all__ = []
