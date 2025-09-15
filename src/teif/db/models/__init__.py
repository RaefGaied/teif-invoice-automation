"""
TEIF SQLAlchemy Models Package

This package contains all database models for the Tunisian Electronic Invoice Format (TEIF) 1.8.8 system.

Model Categories:
- Base: Common base classes and mixins
- Company: Business entities (sellers, buyers)
- Invoice: Core invoice data and line items
- Tax: Tax-related models and calculations
- Payment: Payment terms and methods
- Signature: Digital signatures and XML generation
"""

# Import base classes first
from .base import Base, BaseModel, TimestampMixin

# Import models that don't have dependencies
from .company import Company, CompanyReference, CompanyContact, ContactCommunication

# Then import models with dependencies
from .tax import LineTax, InvoiceTax, InvoiceMonetaryAmount
from .payment import PaymentTerm, PaymentMean
from .signature import InvoiceSignature, GeneratedXmlFile
from .invoice import Invoice, InvoiceDate, InvoiceLine, InvoiceReference, AdditionalDocument, SpecialCondition

__all__ = [
    # Base classes
    'Base', 'BaseModel', 'TimestampMixin',
    
    # Company models
    'Company', 'CompanyReference', 'CompanyContact', 'ContactCommunication',
    
    # Invoice models
    'Invoice', 'InvoiceDate', 'InvoiceLine', 'InvoiceReference', 
    'AdditionalDocument', 'SpecialCondition',
    
    # Tax models
    'LineTax', 'InvoiceTax', 'InvoiceMonetaryAmount',
    
    # Payment models
    'PaymentTerm', 'PaymentMean',
    
    # Signature models
    'InvoiceSignature', 'GeneratedXmlFile',
]
