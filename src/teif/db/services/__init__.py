"""Service layer for business logic.

This module provides service classes that implement business logic and coordinate
data access through repositories. Services are responsible for:
- Enforcing business rules
- Transaction management
- Data validation
- Complex operations that span multiple repositories
"""

from .base import BaseService
from .company_service import CompanyService
from .invoice_service import InvoiceService

__all__ = [
    'BaseService',
    'CompanyService',
    'InvoiceService',
]