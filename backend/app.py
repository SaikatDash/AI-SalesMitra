"""Compatibility entry point for `uvicorn app:main` from any working folder."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import app as main

# Optional: expose the app also as `app` for other conventions
app = main


