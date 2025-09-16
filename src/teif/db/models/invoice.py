"""Invoice models for TEIF system with support for TEIF 1.8.8 compliance."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    String, ForeignKey, Text, Date, DateTime, Numeric, 
    CheckConstraint, Integer, func, JSON, Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates, backref

from .base import BaseModel, CreatedAtModel

if TYPE_CHECKING:
    from .company import Company
    from .tax import LineTax, InvoiceTax, InvoiceMonetaryAmount
    from .payment import PaymentTerm, PaymentMean
    from .signature import InvoiceSignature, GeneratedXmlFile

class InvoiceStatus(str, Enum):
    """Invoice status enumeration focused on processing and generation lifecycle."""
    DRAFT = "draft"            # Initial draft state
    UPLOADING = "uploading"    # Invoice is being uploaded
    UPLOADED = "uploaded"      # Successfully uploaded to the system
    PROCESSING = "processing"  # Being processed (validation, transformation)
    GENERATED = "generated"    # TEIF XML successfully generated
    ERROR = "error"           # Error during processing/generation
    ARCHIVED = "archived"     # Processed and archived
    
class InvoiceType(str, Enum):
    """Invoice type enumeration based on TEIF 1.8.8."""
    INVOICE = "I-11"               # Standard invoice
    CREDIT_NOTE = "I-12"           # Credit note
    DEBIT_NOTE = "I-13"            # Debit note
    PROFORMA = "I-14"              # Proforma invoice
    SELF_BILLING = "I-15"          # Self-billing invoice
    CREDIT_NOTE_RELATED = "I-16"   # Credit note related to invoices
    DEBIT_NOTE_RELATED = "I-17"    # Debit note related to invoices
    
class PaymentMeansCode(str, Enum):
    """Payment means codes as per TEIF 1.8.8."""
    CASH = "I-10"          # Cash payment
    CHECK = "I-20"         # Check
    BANK_TRANSFER = "I-30" # Bank transfer
    CREDIT_CARD = "I-40"   # Credit card
    DIRECT_DEBIT = "I-50"  # Direct debit
    OFFSETTING = "I-60"    # Offsetting
    COMPENSATION = "I-70"  # Compensation
    OTHER = "I-80"         # Other means of payment

class Invoice(BaseModel):
    """Main invoice entity according to TEIF 1.8.8 standard."""
    __tablename__ = 'invoices'
    
    # ===== Version and Control =====
    teif_version: Mapped[str] = mapped_column(
        String(10), 
        default='1.8.8',
        comment="TEIF standard version (I-08)"
    )
    
    controlling_agency: Mapped[str] = mapped_column(
        String(10), 
        default='TTN',
        comment="Controlling agency (e.g., TTN) (I-09)"
    )
    
    # ===== Message Header =====
    sender_identifier: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Sender's unique identifier (I-02)"
    )
    
    receiver_identifier: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Receiver's unique identifier (I-03)"
    )
    
    message_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Unique message identifier (I-04)"
    )
    
    message_datetime: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        comment="Message creation timestamp (I-05)"
    )
    
    # ===== Document Information =====
    document_number: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Invoice document number (I-06)"
    )
    
    document_type: Mapped[InvoiceType] = mapped_column(
        String(10), 
        default=InvoiceType.INVOICE,
        comment="Document type code (I-11)"
    )
    
    document_type_label: Mapped[str] = mapped_column(
        String(100), 
        default='Facture',
        comment="Document type label (I-12)"
    )
    
    document_status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        default=InvoiceStatus.DRAFT,
        comment="Current status of the invoice"
    )
    
    # ===== Date Information =====
    invoice_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False, 
        index=True,
        comment="Invoice issue date (I-31)"
    )
    
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Payment due date (I-32)"
    )
    
    period_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Start date of the billing period (I-33)"
    )
    
    period_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="End date of the billing period (I-34)"
    )
    
    # ===== Business Partners =====
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'),
        nullable=False,
        index=True,
        comment="Reference to the supplier company"
    )
    
    customer_id: Mapped[int] = mapped_column(
        ForeignKey('companies.id'),
        nullable=False,
        index=True,
        comment="Reference to the customer company"
    )
    
    delivery_party_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('companies.id'),
        comment="Delivery party ID if different from customer (I-66)"
    )
    
    # ===== Currency and Amounts =====
    currency: Mapped[str] = mapped_column(
        String(3), 
        default='TND',
        comment="Invoice currency code (ISO 4217) (I-07)"
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
    
    # ===== Payment Information =====
    payment_terms: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Payment terms and conditions (I-37)"
    )
    
    payment_means_code: Mapped[Optional[PaymentMeansCode]] = mapped_column(
        String(10),
        comment="Payment means code (I-38)"
    )
    
    payment_means_text: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Payment means description"
    )
    
    # ===== Additional Information =====
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Additional notes or comments"
    )
    
    additional_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional TEIF-specific information in JSON format"
    )
    
    # ===== Relationships =====
    supplier: Mapped["Company"] = relationship(
        "Company", 
        foreign_keys=[supplier_id],
        backref=backref("supplier_invoices_ref", viewonly=True)
    )
    
    customer: Mapped["Company"] = relationship(
        "Company", 
        foreign_keys=[customer_id],
        backref=backref("customer_invoices_ref", viewonly=True)
    )
    
    delivery_party: Mapped[Optional["Company"]] = relationship(
        "Company", 
        foreign_keys=[delivery_party_id],
        backref=backref("delivery_invoices", lazy="dynamic")
    )
    
    dates: Mapped[List["InvoiceDate"]] = relationship(
        "InvoiceDate", 
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine", 
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.line_number"
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
    
    taxes: Mapped[List["InvoiceTax"]] = relationship(
        "InvoiceTax", 
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    payment_terms_list: Mapped[List["PaymentTerm"]] = relationship(
        "PaymentTerm",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    payment_means: Mapped[List["PaymentMean"]] = relationship(
        "PaymentMean",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    monetary_amounts: Mapped[List["InvoiceMonetaryAmount"]] = relationship(
        "InvoiceMonetaryAmount", 
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    signatures: Mapped[List["InvoiceSignature"]] = relationship(
        "InvoiceSignature", 
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    generated_files: Mapped[List["GeneratedXmlFile"]] = relationship(
        "GeneratedXmlFile", 
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    
    # ===== Table Configuration =====
    __table_args__ = (
        # Indexes
        Index('idx_invoice_document_number', 'document_number'),
        Index('idx_invoice_supplier', 'supplier_id'),
        Index('idx_invoice_customer', 'customer_id'),
        Index('idx_invoice_dates', 'invoice_date', 'due_date'),
        
        # Unique constraints
        UniqueConstraint('supplier_id', 'document_number', name='uq_invoice_supplier_docnum'),
        
        # Check constraints
        CheckConstraint("due_date IS NULL OR due_date >= invoice_date", 
                       name='check_due_date_after_invoice_date'),
        CheckConstraint("period_end_date IS NULL OR period_start_date IS NULL OR period_end_date >= period_start_date",
                       name='check_period_dates'),
        
        {
            'comment': 'Invoices with TEIF 1.8.8 compliance',
            'sqlite_autoincrement': True
        }
    )
    
    # ===== Methods =====
    def to_teif_dict(self) -> Dict[str, Any]:
        """Convert invoice to TEIF-compatible dictionary."""
        return {
            "version": self.teif_version,
            "controlling_agency": self.controlling_agency,
            "sender_identifier": self.sender_identifier,
            "receiver_identifier": self.receiver_identifier,
            "message_identifier": self.message_identifier,
            "message_datetime": self.message_datetime.isoformat() if self.message_datetime else None,
            "document_number": self.document_number,
            "document_type": self.document_type,
            "document_type_label": self.document_type_label,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "period_start_date": self.period_start_date.isoformat() if self.period_start_date else None,
            "period_end_date": self.period_end_date.isoformat() if self.period_end_date else None,
            "currency": self.currency,
            "currency_code_list": self.currency_code_list,
            "capital_amount": str(self.capital_amount),
            "total_with_tax": str(self.total_with_tax),
            "total_without_tax": str(self.total_without_tax),
            "tax_base_amount": str(self.tax_base_amount),
            "tax_amount": str(self.tax_amount),
            "payment_terms": self.payment_terms,
            "payment_means_code": self.payment_means_code,
            "payment_means_text": self.payment_means_text,
            "notes": self.notes,
            "additional_info": self.additional_info or {},
            "seller": self.supplier.to_teif_dict(function_code="I-62") if self.supplier else None,
            "buyer": self.customer.to_teif_dict(function_code="I-64") if self.customer else None,
            "delivery": self.delivery_party.to_teif_dict(function_code="I-66") if self.delivery_party else None,
            "dates": [date.to_teif_dict() for date in sorted(self.dates, key=lambda x: x.function_code)] if self.dates else [],
            "lines": [line.to_teif_dict() for line in self.lines] if self.lines else [],
            "references": [ref.to_teif_dict() for ref in self.references] if self.references else [],
            "additional_documents": [doc.to_teif_dict() for doc in self.additional_documents] if self.additional_documents else [],
            "special_conditions": [cond.to_teif_dict() for cond in self.special_conditions] if self.special_conditions else [],
            "taxes": [tax.to_teif_dict() for tax in self.taxes] if self.taxes else [],
            "payment_terms_list": [term.to_teif_dict() for term in self.payment_terms_list] if self.payment_terms_list else [],
            "payment_means": [pm.to_teif_dict() for pm in self.payment_means] if self.payment_means else [],
            "monetary_amounts": [amt.to_teif_dict() for amt in self.monetary_amounts] if self.monetary_amounts else [],
            "generated_files": [file.to_teif_dict() for file in self.generated_files] if self.generated_files else []
        }
    
    def calculate_totals(self) -> None:
        """Calculate and update invoice totals based on lines and taxes."""
        # Reset totals
        self.total_without_tax = Decimal('0')
        self.tax_amount = Decimal('0')
        
        # Calculate line totals
        for line in self.lines:
            line.calculate_line_totals()
            self.total_without_tax += line.line_total_ht
        
        # Calculate tax totals
        for tax in self.taxes:
            tax.calculate_tax_amount(self.total_without_tax)
            self.tax_amount += tax.tax_amount
        
        # Update total with tax
        self.total_with_tax = self.total_without_tax + self.tax_amount
    
    def add_line(self, **kwargs) -> 'InvoiceLine':
        """Add a new line to the invoice."""
        line = InvoiceLine(invoice=self, **kwargs)
        self.lines.append(line)
        return line
    
    def add_date(self, date_text: str, function_code: str, date_format: str = 'ddMMyy', 
                description: str = None) -> 'InvoiceDate':
        """Add a new date to the invoice."""
        date = InvoiceDate(
            invoice=self,
            date_text=date_text,
            function_code=function_code,
            date_format=date_format,
            description=description
        )
        self.dates.append(date)
        return date
    
    def add_reference(self, reference_type: str, reference_number: str) -> 'InvoiceReference':
        """Add a new reference to the invoice."""
        ref = InvoiceReference(
            invoice=self,
            reference_type=reference_type,
            reference_number=reference_number
        )
        self.references.append(ref)
        return ref
    
    def __repr__(self) -> str:
        return f"<Invoice(number='{self.document_number}', date='{self.invoice_date}', total='{self.total_with_tax} {self.currency}')>"


class InvoiceDate(CreatedAtModel):
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
        default='ddMMyy',
        comment="Date format (ddMMyy, ddMMyy-ddMMyy, etc.)"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Optional description of the date"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="dates")
    
    def to_teif_dict(self) -> Dict[str, Any]:
        """Convert to TEIF-compatible dictionary."""
        return {
            "date_text": self.date_text,
            "function_code": self.function_code,
            "date_format": self.date_format,
            "description": self.description
        }
    
    def __repr__(self) -> str:
        return f"<InvoiceDate(type='{self.function_code}', date='{self.date_text}')>"


class InvoiceLine(CreatedAtModel):
    """Invoice line items with support for TEIF 1.8.8 compliance."""
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
        comment="Line number in the invoice (I-70)"
    )
    
    parent_line_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('invoice_lines.id'), 
        index=True,
        comment="Reference to parent line for sub-lines"
    )
    
    item_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Item identifier (e.g., 'DDM-001', 'DDR-001', 'KIT-001') (I-71)"
    )
    
    item_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Item code (I-72)"
    )
    
    description: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="Detailed item description (I-73)"
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), 
        nullable=False,
        default=1,
        comment="Item quantity (I-74)"
    )
    
    unit: Mapped[str] = mapped_column(
        String(10), 
        default='PCE',
        comment="Unit of measure (e.g., 'PCE', 'KIT') (I-75)"
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        nullable=False,
        default=0,
        comment="Unit price excluding tax (I-76)"
    )
    
    line_total_ht: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        nullable=False,
        default=0,
        comment="Line total excluding tax (quantity * unit_price) (I-77)"
    )
    
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), 
        default=0,
        comment="Discount amount for this line (I-78)"
    )
    
    discount_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        comment="Discount percentage (0-100)"
    )
    
    discount_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Reason for discount (e.g., 'Special 10% discount') (I-79)"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3), 
        default='TND',
        comment="Currency code (ISO 4217)"
    )
    
    line_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Date specific to this line (e.g., service date) (I-80)"
    )
    
    additional_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional line-specific information in JSON format"
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
    
    # Table configuration
    __table_args__ = (
        # Indexes
        Index('idx_invoice_line_number', 'invoice_id', 'line_number'),
        Index('idx_invoice_line_parent', 'parent_line_id'),
        
        # Unique constraints
        UniqueConstraint('invoice_id', 'line_number', name='uq_invoice_line_number'),
        
        # Check constraints
        CheckConstraint("quantity > 0", name='check_positive_quantity'),
        CheckConstraint("unit_price >= 0", name='check_non_negative_price'),
        CheckConstraint("discount_amount >= 0", name='check_non_negative_discount'),
        CheckConstraint("discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)", 
                       name='check_discount_percent_range'),
        
        {
            'comment': 'Invoice line items with TEIF 1.8.8 compliance',
            'sqlite_autoincrement': True
        }
    )
    
    # ===== Methods =====
    def calculate_line_totals(self) -> None:
        """Calculate line totals including any discounts."""
        # Calculate base total
        base_total = self.quantity * self.unit_price
        
        # Apply percentage discount if specified
        if self.discount_percent is not None:
            self.discount_amount = (base_total * self.discount_percent / 100).quantize(Decimal('0.001'))
        
        # Ensure discount doesn't exceed line total
        if self.discount_amount > base_total:
            self.discount_amount = base_total
        
        # Calculate final line total
        self.line_total_ht = (base_total - self.discount_amount).quantize(Decimal('0.001'))
    
    def add_tax(self, tax_type: str, rate: Decimal, amount: Decimal = None, 
               base_amount: Decimal = None) -> 'LineTax':
        """Add a tax to this line."""
        from .tax import LineTax  # Avoid circular import
        
        tax = LineTax(
            line=self,
            tax_type=tax_type,
            rate=rate,
            amount=amount,
            base_amount=base_amount
        )
        
        if amount is None and base_amount is not None:
            tax.amount = (base_amount * rate / 100).quantize(Decimal('0.001'))
        
        self.taxes.append(tax)
        return tax
    
    def to_teif_dict(self) -> Dict[str, Any]:
        """Convert line to TEIF-compatible dictionary."""
        return {
            "line_number": self.line_number,
            "item_identifier": self.item_identifier,
            "item_code": self.item_code,
            "description": self.description,
            "quantity": str(self.quantity),
            "unit": self.unit,
            "unit_price": str(self.unit_price),
            "line_total_ht": str(self.line_total_ht),
            "discount_amount": str(self.discount_amount) if self.discount_amount else None,
            "discount_percent": str(self.discount_percent) if self.discount_percent else None,
            "discount_reason": self.discount_reason,
            "currency": self.currency,
            "line_date": self.line_date.isoformat() if self.line_date else None,
            "additional_info": self.additional_info or {},
            "taxes": [tax.to_teif_dict() for tax in self.taxes] if self.taxes else [],
            "sub_lines": [line.to_teif_dict() for line in self.sub_lines] if self.sub_lines else []
        }
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(number={self.line_number}, desc='{self.description[:30]}...', qty={self.quantity} {self.unit}, total={self.line_total_ht} {self.currency})>"


class InvoiceReference(CreatedAtModel):
    """Reference numbers and identifiers for invoices (RFF section)."""
    __tablename__ = 'invoice_references'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the parent invoice"
    )
    
    reference_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Reference type code (e.g., 'I-04' for Purchase Order, 'I-05' for Contract)"
    )
    
    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Reference number or identifier"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Optional description of the reference"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="references")
    
    # Table configuration
    __table_args__ = (
        Index('idx_invoice_ref_type', 'invoice_id', 'reference_type'),
        UniqueConstraint('invoice_id', 'reference_type', 'reference_number', 
                        name='uq_invoice_reference'),
        {
            'comment': 'Invoice references and identifiers',
            'sqlite_autoincrement': True
        }
    )
    
    def to_teif_dict(self) -> Dict[str, Any]:
        """Convert to TEIF-compatible dictionary."""
        return {
            "type": self.reference_type,
            "value": self.reference_number,
            "description": self.description
        }
    
    def __repr__(self) -> str:
        return f"<InvoiceReference(type='{self.reference_type}', value='{self.reference_number}')>"


class AdditionalDocument(CreatedAtModel):
    """Additional documents related to an invoice (DMS section)."""
    __tablename__ = 'additional_documents'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the parent invoice"
    )
    
    document_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Document type code (e.g., 'I-11' for Invoice, 'I-12' for Credit Note)"
    )
    
    document_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Document number or identifier"
    )
    
    document_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Document date"
    )
    
    document_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="URL or path to the document"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Document description"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="additional_documents")
    
    # Table configuration
    __table_args__ = (
        Index('idx_document_type', 'invoice_id', 'document_type'),
        {
            'comment': 'Additional documents related to invoices',
            'sqlite_autoincrement': True
        }
    )
    
    def to_teif_dict(self) -> Dict[str, Any]:
        """Convert to TEIF-compatible dictionary."""
        return {
            "document_type": self.document_type,
            "document_number": self.document_number,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "document_url": self.document_url,
            "description": self.description
        }
    
    def __repr__(self) -> str:
        return f"<AdditionalDocument(type='{self.document_type}', number='{self.document_number}')>"


class SpecialCondition(CreatedAtModel):
    """Special conditions or terms for an invoice (ALC section)."""
    __tablename__ = 'special_conditions'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the parent invoice"
    )
    
    condition_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Condition type code (e.g., 'I-01' for Discount, 'I-02' for Surcharge)"
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Description of the special condition"
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Amount of the special condition"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default='TND',
        comment="Currency code (ISO 4217)"
    )
    
    base_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        comment="Base amount for percentage calculations"
    )
    
    percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        comment="Percentage rate (0-100) if applicable"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="special_conditions")
    
    # Table configuration
    __table_args__ = (
        {
            'comment': 'Special conditions and terms for invoices',
            'sqlite_autoincrement': True
        }
    )
    
    def to_teif_dict(self) -> Dict[str, Any]:
        """Convert to TEIF-compatible dictionary."""
        return {
            "condition_type": self.condition_type,
            "description": self.description,
            "amount": str(self.amount),
            "currency": self.currency,
            "base_amount": str(self.base_amount) if self.base_amount is not None else None,
            "percentage": str(self.percentage) if self.percentage is not None else None
        }
    
    def __repr__(self) -> str:
        return f"<SpecialCondition(type='{self.condition_type}', amount={self.amount} {self.currency})>"


# Import these here to avoid circular imports
from .tax import InvoiceTax, LineTax, InvoiceMonetaryAmount
from .payment import PaymentTerm, PaymentMean
from .signature import InvoiceSignature, GeneratedXmlFile
