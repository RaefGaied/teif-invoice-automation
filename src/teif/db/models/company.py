"""Company models for TEIF system with contacts and references."""

from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import BaseModel, CreatedAtModel

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
    
    # Contact Information
    address_street: Mapped[Optional[str]] = mapped_column(String(500))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    address_country_code: Mapped[str] = mapped_column(String(2), default='TN')
    address_language: Mapped[str] = mapped_column(String(2), default='FR')
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    fax: Mapped[Optional[str]] = mapped_column(String(50))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationships
    references: Mapped[List["CompanyReference"]] = relationship(
        "CompanyReference", 
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    contacts: Mapped[List["CompanyContact"]] = relationship(
        "CompanyContact", 
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    supplier_invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", 
        foreign_keys="[Invoice.supplier_id]", 
        back_populates="supplier",
        cascade="all, delete-orphan"
    )
    
    customer_invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", 
        foreign_keys="[Invoice.customer_id]", 
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    
    # Table metadata
    __table_args__ = (
        # Single column indexes
        Index('idx_company_vat', 'vat_number'),
        Index('idx_company_identifier', 'identifier'),
        Index('idx_company_tax_id', 'tax_id'),
        Index('idx_company_commercial_register', 'commercial_register'),
        
        # Composite index for common search patterns
        Index('idx_company_name_city', 'name', 'address_city'),
        
        # Unique constraints
        UniqueConstraint('vat_number', name='uq_company_vat'),
        UniqueConstraint('identifier', name='uq_company_identifier'),
        
        # Email validation constraint
        CheckConstraint("email IS NULL OR email LIKE '%@%.%'", name='valid_email_check'),
        
        {
            'comment': 'Companies and organizations that are suppliers or customers in the system',
            'sqlite_autoincrement': True
        }
    )
    
    @validates('email')
    def validate_email(self, key, email):
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email
    
    def __repr__(self) -> str:
        return f"<Company(name='{self.name}', vat='{self.vat_number}')>"

class CompanyReference(CreatedAtModel):
    """References for companies according to TEIF standard."""
    __tablename__ = 'company_references'
    
    company_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id', ondelete='CASCADE'), 
        nullable=False
    )
    reference_type: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment="Reference type (e.g., 'VA' for VAT, 'FC' for Fiscal Code)"
    )
    reference_value: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="The reference value"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Optional description of the reference"
    )
    
    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="references")
    
    def __repr__(self) -> str:
        return f"<CompanyReference(type='{self.reference_type}', value='{self.reference_value}')>"

class CompanyContact(CreatedAtModel):
    """Contact persons for a company."""
    __tablename__ = 'company_contacts'
    
    company_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id', ondelete='CASCADE'), 
        nullable=False
    )
    function_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Contact function code (e.g., 'BU' for buyer, 'SU' for supplier)"
    )
    contact_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Full name of the contact person"
    )
    contact_identifier: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Unique identifier for the contact"
    )
    
    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="contacts")
    communications: Mapped[List["ContactCommunication"]] = relationship(
        "ContactCommunication", 
        back_populates="contact", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<CompanyContact(name='{self.contact_name}', function='{self.function_code}')>"

class ContactCommunication(CreatedAtModel):
    """Communication methods for company contacts."""
    __tablename__ = 'contact_communications'
    
    contact_id: Mapped[int] = mapped_column(
        ForeignKey('company_contacts.id', ondelete='CASCADE'), 
        nullable=False
    )
    communication_type: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment="Type of communication (e.g., 'TE' for telephone, 'EM' for email)"
    )
    communication_value: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="The communication value (e.g., phone number, email)"
    )
    
    # Relationships
    contact: Mapped["CompanyContact"] = relationship("CompanyContact", back_populates="communications")
    
    def __repr__(self) -> str:
        return f"<ContactCommunication(type='{self.communication_type}', value='{self.communication_value}')>"
