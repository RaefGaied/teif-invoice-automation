"""Invoice models for TEIF system with support for multi-line items, taxes, and documents."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    String, ForeignKey, Text, Date, DateTime, Numeric, 
    CheckConstraint, Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import BaseModel

if TYPE_CHECKING:
    from .company import Company

class Invoice(BaseModel):
    """Main invoice entity according to TEIF 1.8.8 standard."""
    __tablename__ = 'invoices'
    
    # Version and control
    teif_version: Mapped[str] = mapped_column(
        String(10), 
        default='1.8.8',
        comment="TEIF standard version"
    )
    controlling_agency: Mapped[str] = mapped_column(
        String(10), 
        default='TTN',
        comment="Controlling agency (e.g., TTN)"
    )
    
    # Message header
    sender_identifier: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Sender's unique identifier"
    )
    receiver_identifier: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Receiver's unique identifier"
    )
    message_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Unique message identifier"
    )
    message_datetime: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        comment="Message creation timestamp"
    )
    
    # Document information
    document_number: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Invoice document number"
    )
    document_type: Mapped[str] = mapped_column(
        String(10), 
        default='I-11',
        comment="Document type code (e.g., I-11 for invoice)"
    )
    document_type_label: Mapped[str] = mapped_column(
        String(100), 
        default='Facture',
        comment="Document type label"
    )
    
    # Date information
    invoice_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False, 
        index=True,
        comment="Invoice issue date"
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Payment due date"
    )
    period_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Start date of the billing period"
    )
    period_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="End date of the billing period"
    )
    
    # Business partners
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'), 
        nullable=False, 
        index=True,
        comment="Supplier company ID"
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'), 
        nullable=False, 
        index=True,
        comment="Customer company ID"
    )
    
    # Currency information
    currency: Mapped[str] = mapped_column(
        String(3), 
        default='TND',
        comment="Invoice currency code (ISO 4217)"
    )
    currency_code_list: Mapped[str] = mapped_column(
        String(20), 
        default='ISO_4217',
        comment="Currency code list name"
    )
    
    # Financial amounts
    capital_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Total capital amount (I-179)"
    )
    total_with_tax: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Total amount including tax (I-180)"
    )
    total_without_tax: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Total amount excluding tax (I-176)"
    )
    tax_base_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Tax base amount (I-182)"
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Total tax amount (I-181)"
    )
    
    # Status and tracking
    status: Mapped[str] = mapped_column(
        String(50), 
        default='draft', 
        index=True,
        comment="Invoice status (draft, sent, paid, etc.)"
    )
    pdf_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Path to the generated PDF file"
    )
    xml_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Path to the generated XML file"
    )
    ttn_validation_ref: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="TTN validation reference number"
    )
    
    # Relationships
    supplier: Mapped["Company"] = relationship(
        "Company", 
        foreign_keys=[supplier_id], 
        back_populates="supplier_invoices"
    )
    customer: Mapped["Company"] = relationship(
        "Company", 
        foreign_keys=[customer_id], 
        back_populates="customer_invoices"
    )
    
    # Related entities
    dates: Mapped[List["InvoiceDate"]] = relationship(
        "InvoiceDate", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    references: Mapped[List["InvoiceReference"]] = relationship(
        "InvoiceReference", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    additional_documents: Mapped[List["AdditionalDocument"]] = relationship(
        "AdditionalDocument", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    special_conditions: Mapped[List["SpecialCondition"]] = relationship(
        "SpecialCondition", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    
    # Financial relationships
    taxes: Mapped[List["InvoiceTax"]] = relationship(
        "InvoiceTax", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    monetary_amounts: Mapped[List["InvoiceMonetaryAmount"]] = relationship(
        "InvoiceMonetaryAmount", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    payment_terms: Mapped[List["PaymentTerm"]] = relationship(
        "PaymentTerm", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    payment_means: Mapped[List["PaymentMean"]] = relationship(
        "PaymentMean", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    
    # Signatures and XML
    signatures: Mapped[List["InvoiceSignature"]] = relationship(
        "InvoiceSignature", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    xml_files: Mapped[List["GeneratedXmlFile"]] = relationship(
        "GeneratedXmlFile", 
        back_populates="invoice", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(number='{self.document_number}', date='{self.invoice_date}')>"


class InvoiceDate(BaseModel):
    """Date information for invoices (DTM section)."""
    __tablename__ = 'invoice_dates'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Reference to the parent invoice"
    )
    date_text: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Date in specified format (ddMMyy or ddMMyy-ddMMyy)"
    )
    function_code: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment="Date function code (I-31, I-32, I-36, etc.)"
    )
    date_format: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Date format (ddMMyy, ddMMyy-ddMMyy, etc.)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Optional description of the date"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="dates")
    
    def __repr__(self) -> str:
        return f"<InvoiceDate(code='{self.function_code}', date='{self.date_text}')>"


class InvoiceLine(BaseModel):
    """Invoice line items with support for sub-lines."""
    __tablename__ = 'invoice_lines'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True,
        comment="Reference to the parent invoice"
    )
    line_number: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="Line number in the invoice"
    )
    parent_line_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('invoice_lines.id'), 
        index=True,
        comment="Reference to parent line for sub-lines"
    )
    
    # Item identification
    item_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Item identifier (e.g., 'DDM-001', 'DDR-001', 'KIT-001')"
    )
    item_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Item code (same as item_identifier)"
    )
    description: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="Detailed item description"
    )
    
    # Quantity and price
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), 
        nullable=False,
        comment="Item quantity"
    )
    unit: Mapped[str] = mapped_column(
        String(10), 
        default='PCE',
        comment="Unit of measure (e.g., 'PCE', 'KIT')"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        nullable=False,
        comment="Unit price excluding tax"
    )
    
    # Amounts
    line_total_ht: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        nullable=False,
        comment="Line total excluding tax (quantity * unit_price)"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Discount amount for this line"
    )
    discount_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Reason for discount (e.g., 'Special 10% discount')"
    )
    
    # Currency
    currency: Mapped[str] = mapped_column(
        String(3), 
        default='TND',
        comment="Currency code (ISO 4217)"
    )
    currency_code_list: Mapped[str] = mapped_column(
        String(20), 
        default='ISO_4217',
        comment="Currency code list name"
    )
    
    # Metadata
    line_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Date specific to this line (e.g., service date)"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    parent_line: Mapped[Optional["InvoiceLine"]] = relationship(
        "InvoiceLine", 
        remote_side="InvoiceLine.id", 
        back_populates="sub_lines"
    )
    sub_lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine", 
        back_populates="parent_line",
        cascade="all, delete-orphan"
    )
    taxes: Mapped[List["LineTax"]] = relationship(
        "LineTax", 
        back_populates="line", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(number={self.line_number}, desc='{self.description[:50]}...')>"


class InvoiceReference(BaseModel):
    """Additional references for invoices."""
    __tablename__ = 'invoice_references'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Reference to the parent invoice"
    )
    reference_type: Mapped[str] = mapped_column(
        String(10), 
        nullable=False,
        comment="Reference type (e.g., 'ON', 'ABO')"
    )
    reference_value: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Reference value (e.g., 'CMD-2023-456')"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Optional description of the reference"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="references")
    
    def __repr__(self) -> str:
        return f"<InvoiceReference(type='{self.reference_type}', value='{self.reference_value}')>"


class AdditionalDocument(BaseModel):
    """Additional documents related to an invoice."""
    __tablename__ = 'additional_documents'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Reference to the parent invoice"
    )
    document_id: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Document identifier (e.g., 'DOC-001')"
    )
    document_type: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Document type code (e.g., 'I-201')"
    )
    document_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Document name (e.g., 'Proforma Invoice')"
    )
    document_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Document date (converted from YYYYMMDD)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Document description (e.g., 'Sent 5 days before')"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Path to the document file"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="additional_documents")
    
    def __repr__(self) -> str:
        return f"<AdditionalDocument(id='{self.document_id}', name='{self.document_name}')>"


class SpecialCondition(BaseModel):
    """Special conditions or notes for an invoice."""
    __tablename__ = 'special_conditions'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Reference to the parent invoice"
    )
    condition_text: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="The condition or note text"
    )
    language_code: Mapped[str] = mapped_column(
        String(2), 
        default='fr',
        comment="Language code for the condition text"
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer, 
        default=1,
        comment="Order of this condition in the list"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="special_conditions")
    
    def __repr__(self) -> str:
        text_preview = (self.condition_text[:47] + '...') if len(self.condition_text) > 50 else self.condition_text
        return f"<SpecialCondition(seq={self.sequence_number}, text='{text_preview}')>"


# Import these here to avoid circular imports
from .tax import InvoiceTax, LineTax, InvoiceMonetaryAmount
from .payment import PaymentTerm, PaymentMean
from .signature import InvoiceSignature, GeneratedXmlFile
