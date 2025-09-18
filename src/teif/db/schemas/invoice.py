from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from decimal import Decimal


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""
    PROCESSING = "processing"  # Being processed (validation, transformation)
    GENERATED = "generated"    # TEIF XML successfully generated
    ERROR = "error"            # Error during processing/generation
    ARCHIVED = "archived"      # Processed and archived

class InvoiceLineBase(BaseModel):
    description: str
    quantity: float
    unit_price: float
    unit: str = "PCE"
    discount: Optional[float] = 0.0
    tax_rate: Optional[float] = Field(
        None, 
        description="Tax rate as a percentage (e.g., 19.0 for 19%"
    )

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class InvoiceLineCreate(InvoiceLineBase):
    tax_rate: float = Field(..., description="Tax rate as a percentage (e.g., 19.0 for 19%")


class InvoiceLine(InvoiceLineBase):
    id: int
    invoice_id: int
    
    @validator('tax_rate', pre=True, always=True)
    def extract_tax_rate(cls, v, values):
        # If tax_rate is already set, return it
        if v is not None:
            return v
            
        # Try to get tax rate from the taxes relationship if available
        if 'taxes' in values and values['taxes']:
            taxes = values['taxes']
            if isinstance(taxes, list) and taxes:
                # Handle case where taxes is a list of LineTax objects
                tax = taxes[0]
                if hasattr(tax, 'tax_rate'):
                    return float(tax.tax_rate)
                # Handle case where taxes is a list of dictionaries
                elif isinstance(tax, dict) and 'tax_rate' in tax:
                    return float(tax['tax_rate'])
        
        # If no tax rate is found, try to get it from the invoice's taxes
        if 'invoice' in values and values['invoice'] and hasattr(values['invoice'], 'taxes'):
            invoice_taxes = values['invoice'].taxes
            if invoice_taxes and hasattr(invoice_taxes[0], 'tax_rate'):
                return float(invoice_taxes[0].tax_rate)
        
        # Default to 19% if no tax rate is specified
        return 19.0


class InvoiceLineUpdate(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = None
    unit: Optional[str] = None
    discount: Optional[float] = None
    
    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class PaymentTermSchema(BaseModel):
    id: int
    payment_terms_code: Optional[str] = None
    description: Optional[str] = None
    discount_percent: Optional[float] = None
    discount_due_date: Optional[date] = None
    payment_due_date: Optional[date] = None


class InvoiceBase(BaseModel):
    document_number: str
    invoice_date: date
    due_date: date
    supplier_id: int
    customer_id: int
    status: InvoiceStatus = InvoiceStatus.PROCESSING
    currency: str = "TND"
    notes: Optional[str] = None
    terms: Optional[str] = None
    payment_terms: Optional[List[PaymentTermSchema]] = Field(
        None, 
        description="List of payment terms"
    )

    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v is not None else None
        }


class InvoiceCreate(InvoiceBase):
    lines: List[InvoiceLineCreate] = []


class InvoiceUpdate(BaseModel):
    document_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    supplier_id: Optional[int] = None
    customer_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    payment_terms: Optional[List[Dict[str, Any]]] = None
    lines: Optional[List[Dict[str, Any]]] = None


class Invoice(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLine] = []
    
    @validator('payment_terms', pre=True)
    def format_payment_terms(cls, v):
        # If payment_terms is a list of PaymentTerm objects, convert to schema
        if isinstance(v, list) and v and not isinstance(v[0], dict):
            return [{
                'id': term.id,
                'payment_terms_code': term.payment_terms_code,
                'description': term.description,
                'discount_percent': term.discount_percent,
                'discount_due_date': term.discount_due_date,
                'payment_due_date': term.payment_due_date
            } for term in v]
        return v

    class Config(InvoiceBase.Config):
        pass