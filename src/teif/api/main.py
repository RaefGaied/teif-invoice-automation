#!/usr/bin/env python3
"""
TEIF API Main Module

This module serves as the entry point for the TEIF API application.
It initializes the FastAPI application and runs the development server.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn
from teif.api import app

def start():
    """Start the FastAPI application with Uvicorn."""
    # Temporarily disable HTTPS for testing
    ssl_keyfile = None
    ssl_certfile = None
    
    print("\n=== Server Starting ===")
    print("HTTPS is temporarily disabled for testing")
    print(f"Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/api/v1/docs\n")
    
    uvicorn.run(
        "teif.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        reload_dirs=["src/teif"],
        workers=1
    )

if __name__ == "__main__":
    start()