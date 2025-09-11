"""Company models for TEIF system with contacts and references."""

from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from teif.db.models.invoice import Invoice
from .base import BaseModel

class Company(BaseModel):
    """Company entity for TEIF system."""
    __tablename__ = 'companies'
    
    # Identifiers
    identifier: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, 
                                         comment="Unique company identifier")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50))
    commercial_register: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Address
    address_street: Mapped[Optional[str]] = mapped_column(String(500))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    address_country_code: Mapped[str] = mapped_column(String(2), default='TN')
    address_language: Mapped[str] = mapped_column(String(2), default='FR')
    
    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    fax: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        server_default='1',
        comment='Indicates if the company is active'
    )
    
    # Relationships
    references: Mapped[List["CompanyReference"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    contacts: Mapped[List["CompanyContact"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    supplier_invoices: Mapped[List["Invoice"]] = relationship(foreign_keys="Invoice.supplier_id", back_populates="supplier")
    customer_invoices: Mapped[List["Invoice"]] = relationship(foreign_keys="Invoice.customer_id", back_populates="customer")
    
    # Table metadata
    __table_args__ = (
        # Single column indexes
        Index('idx_company_vat', 'vat_number'),
        Index('idx_company_identifier', 'identifier'),
        Index('idx_company_tax_id', 'tax_id'),
        Index('idx_company_commercial_register', 'commercial_register'),
        
        # Composite index for common search patterns
        Index('idx_company_name_city', 'name', 'address_city'),
        
        # Simple index on is_active instead of partial index
        Index('idx_company_active', 'is_active'),
        
        # Unique constraints
        UniqueConstraint('vat_number', name='uq_company_vat'),
        UniqueConstraint('identifier', name='uq_company_identifier'),
        
        # Email validation constraint
        CheckConstraint("email IS NULL OR email LIKE '%@%.%'", name='valid_email_check'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email
    
    def __repr__(self) -> str:
        return f"<Company(identifier='{self.identifier}', name='{self.name}')>"

class CompanyReference(BaseModel):
    """References for companies according to TEIF standard."""
    __tablename__ = 'company_references'
    
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(10), nullable=False)
    reference_value: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    company: Mapped["Company"] = relationship("Company", back_populates="references")
    
    def __repr__(self) -> str:
        return f"<CompanyReference(type='{self.reference_type}', value='{self.reference_value}')>"

class CompanyContact(BaseModel):
    """Contact persons for a company."""
    __tablename__ = 'company_contacts'
    
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    function_code: Mapped[Optional[str]] = mapped_column(String(10))
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_identifier: Mapped[Optional[str]] = mapped_column(String(50))
    
    company: Mapped["Company"] = relationship("Company", back_populates="contacts")
    communications: Mapped[List["ContactCommunication"]] = relationship(
        "ContactCommunication", 
        back_populates="contact", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<CompanyContact(name='{self.contact_name}')>"

class ContactCommunication(BaseModel):
    """Communication methods for company contacts."""
    __tablename__ = 'contact_communications'
    
    contact_id: Mapped[int] = mapped_column(ForeignKey('company_contacts.id', ondelete='CASCADE'), nullable=False)
    communication_type: Mapped[str] = mapped_column(String(10), nullable=False)
    communication_value: Mapped[str] = mapped_column(String(255), nullable=False)
    
    contact: Mapped["CompanyContact"] = relationship("CompanyContact", back_populates="communications")
    
    def __repr__(self) -> str:
        return f"<ContactCommunication(type='{self.communication_type}')>"
