# src/teif/api/routers/__init__.py
from .dashboard import router as dashboard_router
from .invoices import router as invoices_router
from .companies import router as companies_router

__all__ = ["dashboard_router", "invoices_router", "companies_router"]