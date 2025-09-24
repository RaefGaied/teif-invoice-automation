#!/usr/bin/env python3
"""
TEIF API Main Module

This module serves as the entry point for the TEIF API application.
It initializes the FastAPI application and runs the development server.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Configure logging with ASCII characters
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Force UTF-8 output
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TEIF API",
        description="API for Tunisian Electronic Invoice Format (TEIF) processing",
        version="1.0.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173","http://localhost:3000"],  # In production, replace with your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Dynamically import and include only existing routers
    try:
        from teif.api.routers import dashboard_router
        app.include_router(
            dashboard_router,
            prefix="/api/v1",
            tags=["dashboard"]
        )
        logger.info("[OK] Dashboard router loaded")
    except ImportError as e:
        logger.warning(f"[!] Dashboard router not loaded: {str(e)}")

    try:
        from teif.api.routers import invoices_router
        app.include_router(
            invoices_router,
            prefix="/api/v1/invoices",
            tags=["invoices"]
        )
        logger.info("[OK] Invoices router loaded")
    except ImportError as e:
        logger.warning(f"[!] Invoices router not loaded: {str(e)}")

    try:
        from teif.api.routers import companies_router
        app.include_router(
            companies_router,
            prefix="/api/v1/companies",
            tags=["companies"]
        )
        logger.info("[OK] Companies router loaded")
    except ImportError as e:
        logger.warning(f"[!] Companies router not loaded: {str(e)}")

    # Add health check endpoint
    @app.get("/health", status_code=status.HTTP_200_OK)
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}

    # Add root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "TEIF API Service",
            "docs": "/api/v1/docs",
            "health": "/health"
        }

    # Global exception handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    return app

def start():
    """Start the FastAPI application with Uvicorn."""
    # Load environment variables
    debug = os.getenv("DEBUG", "true").lower() == "true"
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # SSL configuration
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    
    if ssl_enabled and (not ssl_keyfile or not ssl_certfile):
        logger.warning("SSL is enabled but keyfile or certfile is missing. Falling back to HTTP.")
        ssl_enabled = False

    app = create_app()
    
    # Log startup information
    protocol = "https" if ssl_enabled else "http"
    logger.info("\n" + "="*50)
    logger.info("TEIF API Service Starting...")
    logger.info(f"Environment: {'Development' if debug else 'Production'}")
    logger.info(f"Server: {protocol}://{host}:{port}")
    logger.info(f"API Documentation: {protocol}://{host}:{port}/api/v1/docs")
    logger.info("="*50 + "\n")

    # For development with auto-reload
    if debug:
        uvicorn.run(
            "teif.api.main:create_app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=["src/teif"],
            ssl_keyfile=ssl_keyfile if ssl_enabled else None,
            ssl_certfile=ssl_certfile if ssl_enabled else None,
            log_level="debug"
        )
    else:
        # For production
        uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_keyfile=ssl_keyfile if ssl_enabled else None,
            ssl_certfile=ssl_certfile if ssl_enabled else None,
            workers=(os.cpu_count() or 1) * 2 + 1,
            log_level="info"
        )

if __name__ == "__main__":
    start()