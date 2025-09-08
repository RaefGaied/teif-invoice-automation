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

from .base import BaseModel, TimestampMixin
from .company import Company, CompanyReference, CompanyContact, ContactCommunication
from .invoice import Invoice, InvoiceDate, InvoiceLine, InvoiceReference, AdditionalDocument, SpecialCondition
from .tax import LineTax, InvoiceTax, InvoiceMonetaryAmount
from .payment import PaymentTerm, PaymentMean
from .signature import InvoiceSignature, GeneratedXmlFile

__all__ = [
    # Base
    'BaseModel', 'TimestampMixin',
    
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
    'InvoiceSignature', 'GeneratedXmlFile'
]
