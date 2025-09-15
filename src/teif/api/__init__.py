"""
TEIF API Package

This package contains the main FastAPI application and API endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="TEIF API",
    description="API for Tunisian Electronic Invoice Format (TEIF) Management",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Add CORS middleware with specific origins
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from .routers import companies, invoices

# API v1 routes
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Add a root endpoint
@app.get("/")
async def root():
    return {"message": "TEIF API is running", "docs": "/api/v1/docs"}
