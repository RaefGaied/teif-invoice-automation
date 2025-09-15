from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

class ContactType(str, Enum):
    PHONE = "phone"
    EMAIL = "email"
    MOBILE = "mobile"
    FAX = "fax"
    WEBSITE = "website"
    OTHER = "other"

class CompanyContactBase(BaseModel):
    """Base model for company contact information."""
    contact_type: ContactType
    value: str
    is_primary: bool = False
    description: Optional[str] = None

class CompanyContactCreate(CompanyContactBase):
    """Schema for creating a new company contact."""
    pass

class CompanyContactUpdate(BaseModel):
    """Schema for updating an existing company contact."""
    contact_type: Optional[ContactType] = None
    value: Optional[str] = None
    is_primary: Optional[bool] = None
    description: Optional[str] = None

class CompanyContact(CompanyContactBase):
    """Schema for returning company contact information."""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CompanyReferenceBase(BaseModel):
    """Base model for company references."""
    reference_type: str
    value: str
    description: Optional[str] = None

class CompanyReferenceCreate(CompanyReferenceBase):
    """Schema for creating a new company reference."""
    pass

class CompanyReference(CompanyReferenceBase):
    """Schema for returning company reference information."""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CompanyBase(BaseModel):
    """Base model for company information."""
    name: str
    legal_name: Optional[str] = None
    tax_identification_number: str
    commerce_registry_number: Optional[str] = None
    vat_number: Optional[str] = None
    legal_form: Optional[str] = None
    activity_sector: Optional[str] = None
    activity_code: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "TN"
    is_active: bool = True

class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    contacts: List[CompanyContactCreate] = []
    references: List[CompanyReferenceCreate] = []

class CompanyUpdate(BaseModel):
    """Schema for updating an existing company."""
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_identification_number: Optional[str] = None
    commerce_registry_number: Optional[str] = None
    vat_number: Optional[str] = None
    legal_form: Optional[str] = None
    activity_sector: Optional[str] = None
    activity_code: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None

class Company(CompanyBase):
    """Schema for returning company information."""
    id: int
    created_at: datetime
    updated_at: datetime
    contacts: List[CompanyContact] = []
    references: List[CompanyReference] = []

    class Config:
        orm_mode = True

class CompanyFinancialOverview(BaseModel):
    """Schema for company financial overview."""
    total_invoices: int = 0
    total_revenue: float = 0.0
    total_paid: float = 0.0
    total_outstanding: float = 0.0
    total_overdue: float = 0.0
    currency: str = "TND"

    class Config:
        orm_mode = True