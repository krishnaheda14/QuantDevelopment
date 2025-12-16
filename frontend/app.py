"""Frontend entrypoint for GEMSCAP Streamlit app.
Delegates to the existing `streamlit_main.py` file so
`start_frontend.py` can reliably launch Streamlit.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so we can import `streamlit_main`
# when Streamlit runs from the `frontend` directory.
ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
	sys.path.insert(0, root_str)

# Importing `streamlit_main` executes the Streamlit app definitions
import streamlit_main  # noqa: F401
