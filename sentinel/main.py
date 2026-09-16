"""
sentinel/main.py
================
FastAPI app entry point.

Run with:
    uvicorn sentinel.main:app --port 8000
"""
from fastapi.middleware.cors import CORSMiddleware
from sentinel.api import app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

__all__ = ["app"]
