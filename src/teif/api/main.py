#!/usr/bin/env python3
"""
TEIF API Main Module

This module serves as the entry point for the TEIF API application.
It initializes the FastAPI application and runs the development server.
"""

import uvicorn
from . import app

def start():
    """Start the FastAPI application with Uvicorn."""
    uvicorn.run(
        "teif.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )

if __name__ == "__main__":
    start()
