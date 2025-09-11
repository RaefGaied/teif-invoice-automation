"""
TEIF API Package

This package contains all API endpoints and related functionality for the TEIF application.
It provides a RESTful interface to interact with the TEIF system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# This will be imported in main.py
app = FastAPI(
    title="TEIF API",
    description="API for Tunisian Electronic Invoice Format (TEIF) processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers here
# from .routers import companies, invoices, etc.

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
