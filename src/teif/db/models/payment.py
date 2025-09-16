"""
Payment-related models for TEIF system.

This module contains models for handling payment terms and payment means
in the Tunisian Electronic Invoice Format (TEIF) system.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, ForeignKey, Date, Numeric, 
    CheckConstraint, Integer, func, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, CreatedAtModel

if TYPE_CHECKING:
    from .invoice import Invoice

class PaymentTerm(CreatedAtModel):
    """
    Payment terms for an invoice.
    
    This model stores information about the payment terms and conditions
    for an invoice, including due dates, discounts, and other relevant details.
    """
    __tablename__ = 'payment_terms'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the parent invoice"
    )
    
    # Payment terms information
    payment_terms_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Payment terms code (e.g., 'I-37' for payment terms)"
    )
    
    # Payment due dates
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="The date by which the payment is due"
    )
    
    # Discount information
    discount_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        comment="Discount percentage for early payment (e.g., 2.0 for 2%)"
    )
    
    discount_due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Last date to take advantage of the early payment discount"
    )
    
    # Payment reference information
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Payment reference or identifier"
    )
    
    # Notes and additional information
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Any additional notes about the payment terms"
    )
    
    # Relationship to Invoice
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", 
        back_populates="payment_terms_list"
    )
    
    # Table configuration
    __table_args__ = (
        {
            'comment': 'Payment terms for invoices',
            'sqlite_autoincrement': True
        }
    )
    
    def to_teif_dict(self) -> dict:
        """Convert to TEIF-compatible dictionary."""
        return {
            "payment_terms_code": self.payment_terms_code,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "discount_percent": float(self.discount_percent) if self.discount_percent else None,
            "discount_due_date": self.discount_due_date.isoformat() if self.discount_due_date else None,
            "payment_reference": self.payment_reference,
            "notes": self.notes
        }
    
    def __repr__(self) -> str:
        return f"<PaymentTerm(id={self.id}, invoice_id={self.invoice_id}, due_date={self.due_date})>"


class PaymentMean(BaseModel):
    """
    Payment method information for an invoice.
    
    Represents the payment method details, including bank account information
    for wire transfers or other payment methods.
    """
    __tablename__ = 'payment_means'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the parent invoice"
    )
    payment_means_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Payment means code (e.g., 'I-30')"
    )
    payment_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Payment reference or transaction ID (e.g., 'VIR-2023-001')"
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="Due date for this payment method"
    )
    
    # Payee financial account information
    iban: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="IBAN of the beneficiary's account (e.g., 'TN5904018104003691234567')"
    )
    account_holder: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Name of the account holder"
    )
    financial_institution: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Name of the financial institution (e.g., 'BNA')"
    )
    branch_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Branch code or identifier (e.g., 'AGENCE_123')"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", 
        back_populates="payment_means"
    )
    
    def __repr__(self) -> str:
        return f"<PaymentMean(code='{self.payment_means_code}', id='{self.payment_id}')>"


# Import the remaining models that reference these ones
from .invoice import InvoiceMonetaryAmount
