"""Repository layer for database operations.

This module provides repository classes that abstract database operations,
making it easier to work with the database in a clean and maintainable way.
"""

from .base import BaseRepository
from .company_repository import CompanyRepository
from .invoice_repository import InvoiceRepository

__all__ = [
    'BaseRepository',
    'CompanyRepository',
    'InvoiceRepository',
]