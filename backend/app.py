"""
Compatibility shim so you can run the backend with:

    uvicorn app:main --reload

This file exposes the FastAPI app from `main.py` as the name `main`.
"""
from main import app as main

# Optional: expose the app also as `app` for other conventions
app = main
