"""Company models for TEIF system with contacts and references."""

from typing import List, Optional, Dict, Any
from sqlalchemy import String, ForeignKey, Text, CheckConstraint, Index, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates, Session
from sqlalchemy.sql import func

from .base import BaseModel, CreatedAtModel

class Company(BaseModel):
    """Company entity for TEIF system with TEIF 1.8.8 compliance."""
    __tablename__ = 'companies'
    
    # ===== Identifiers =====
    identifier: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Unique company identifier (I-01 for TEIF)"
    )
    
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Company name (PartnerName in TEIF)"
    )
    
    vat_number: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        index=True,
        comment="VAT registration number (I-1602 in TEIF)"
    )
    
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Tax identification number (I-01 in TEIF)"
    )
    
    commercial_register: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Commercial register number (I-815 in TEIF)"
    )
    
    # ===== Address Information =====
    address_street: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Street address (Street in TEIF)"
    )
    
    address_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="City name (CityName in TEIF)"
    )
    
    address_postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="Postal/ZIP code (PostalCode in TEIF)"
    )
    
    address_country_code: Mapped[str] = mapped_column(
        String(2), 
        default='TN',
        comment="ISO 3166-1 alpha-2 country code (Country in TEIF)"
    )
    
    address_language: Mapped[str] = mapped_column(
        String(2), 
        default='FR',
        comment="Language code for address (lang attribute in TEIF)"
    )
    
    # ===== Contact Information =====
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Primary phone number (I-101 in TEIF)"
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Primary email address (I-102 in TEIF)"
    )
    
    fax: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Fax number (I-118 in TEIF)"
    )
    
    website: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Company website URL (I-104 in TEIF)"
    )
    
    # ===== Additional TEIF-specific fields =====
    function_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Function code for TEIF (e.g., 'I-62' for seller, 'I-64' for buyer)"
    )
    
    additional_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional TEIF-specific information in JSON format"
    )
    
    # ===== Relationships =====
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
    
    # Relationships with Invoice model (viewonly to prevent conflicts)
    supplier_invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", 
        foreign_keys="[Invoice.supplier_id]", 
        viewonly=True
    )
    
    customer_invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", 
        foreign_keys="[Invoice.customer_id]", 
        viewonly=True
    )
    
    # ===== Table Configuration =====
    __table_args__ = (
        # Single column indexes
        Index('idx_company_vat', 'vat_number'),
        Index('idx_company_identifier', 'identifier'),
        Index('idx_company_tax_id', 'tax_id'),
        Index('idx_company_commercial_register', 'commercial_register'),
        
        # Composite index for common search patterns
        Index('idx_company_name_city', 'name', 'address_city'),
        
        # Unique constraints
        UniqueConstraint('vat_number', name='uq_company_vat', deferrable=True, initially='DEFERRED'),
        UniqueConstraint('identifier', name='uq_company_identifier', deferrable=True, initially='DEFERRED'),
        
        # Email validation constraint
        CheckConstraint("email IS NULL OR email LIKE '%@%.%'", name='valid_email_check'),
        
        {
            'comment': 'Companies and organizations that are suppliers or customers in the system',
            'sqlite_autoincrement': True
        }
    )
    
    # ===== Methods =====
    def to_teif_dict(self, function_code: str = None) -> Dict[str, Any]:
        """Convert company to TEIF-compatible dictionary."""
        return {
            "identifier": self.identifier,
            "name": self.name,
            "vat_number": self.vat_number,
            "function_code": function_code or self.function_code,
            "address": {
                "street": self.address_street or "",
                "city": self.address_city or "",
                "postal_code": self.address_postal_code or "",
                "country_code": self.address_country_code,
                "lang": self.address_language
            },
            "references": [
                {
                    "type": ref.reference_type,
                    "value": ref.reference_value,
                    "description": ref.description
                }
                for ref in self.references
            ],
            "contacts": [
                {
                    "function_code": contact.function_code,
                    "name": contact.contact_name,
                    "identifier": contact.contact_identifier,
                    "communications": [
                        {
                            "type": comm.communication_type,
                            "value": comm.communication_value
                        }
                        for comm in contact.communications
                    ]
                }
                for contact in self.contacts
            ]
        }
    
    @validates('email')
    def validate_email(self, key: str, email: Optional[str]) -> Optional[str]:
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email
    
    @classmethod
    def get_or_create(
        cls, 
        db: Session, 
        identifier: str, 
        defaults: Optional[Dict[str, Any]] = None
    ) -> 'Company':
        """Get or create a company with the given identifier."""
        company = db.query(cls).filter(cls.identifier == identifier).first()
        if company:
            return company
            
        if not defaults:
            defaults = {}
            
        company = cls(identifier=identifier, **defaults)
        db.add(company)
        db.flush()
        return company
    
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
