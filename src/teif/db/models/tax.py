"""
Tax-related models for TEIF system.

This module contains models for handling tax calculations and monetary amounts
in the Tunisian Electronic Invoice Format (TEIF) system.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, ForeignKey, Numeric, Integer, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import CreatedAtModel


class LineTax(CreatedAtModel):
    """
    Tax information for invoice lines.
    
    Represents taxes applied to specific line items in an invoice,
    such as VAT or stamp duties.
    """
    __tablename__ = 'line_taxes'
    
    line_id: Mapped[int] = mapped_column(
        ForeignKey('invoice_lines.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the invoice line"
    )
    tax_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Tax code (e.g., 'I-1602' for VAT, 'I-1601' for Stamp Duty)"
    )
    tax_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of tax (e.g., 'TVA', 'Droit de timbre')"
    )
    tax_category: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Tax category (e.g., 'S' for Standard, 'E' for Exempt, 'Z' for Zero-rated)"
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Tax rate as a percentage (e.g., 19.0 for 19%)"
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Taxable base amount"
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Calculated tax amount"
    )
    currency_code_list: Mapped[str] = mapped_column(
        String(20),
        default='ISO_4217',
        comment="Currency code list identifier"
    )
    
    # Relationships
    line: Mapped["InvoiceLine"] = relationship("InvoiceLine", back_populates="taxes")
    
    def __repr__(self) -> str:
        return f"<LineTax(code='{self.tax_code}', rate={self.tax_rate}%, amount={self.tax_amount})>"


class InvoiceTax(CreatedAtModel):
    """
    Tax information at the invoice level.
    
    Represents taxes that apply to the entire invoice, as opposed to
    individual line items.
    """
    __tablename__ = 'invoice_taxes'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to the invoice"
    )
    tax_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Tax code (e.g., 'I-1602' for VAT, 'I-1601' for Stamp Duty)"
    )
    tax_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of tax (e.g., 'TVA', 'Droit de timbre')"
    )
    tax_category: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Tax category (e.g., 'S' for Standard, 'E' for Exempt, 'Z' for Zero-rated)"
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Tax rate as a percentage (e.g., 19.0 for 19%)"
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Taxable base amount"
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Calculated tax amount"
    )
    currency_code_list: Mapped[str] = mapped_column(
        String(20),
        default='ISO_4217',
        comment="Currency code list identifier"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="taxes")
    
    def __repr__(self) -> str:
        return f"<InvoiceTax(type='{self.tax_type}', rate={self.tax_rate}%, amount={self.tax_amount})>"


class InvoiceMonetaryAmount(CreatedAtModel):
    """
    Monetary amounts related to an invoice (MOA section).
    
    Represents various financial amounts associated with an invoice,
    such as totals, discounts, and allowances.
    """
    __tablename__ = 'invoice_monetary_amounts'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to the invoice"
    )
    amount_type_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Type code (e.g., 'I-181' for Tax Amount, 'I-182' for Taxable Amount)"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        comment="Monetary amount"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Description of the amount (e.g., 'Total hors taxes')"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default='TND',
        comment="Currency code (ISO 4217)"
    )
    currency_code_list: Mapped[str] = mapped_column(
        String(20),
        default='ISO_4217',
        comment="Currency code list identifier"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="monetary_amounts")
    
    def __repr__(self) -> str:
        return f"<InvoiceMonetaryAmount(type='{self.amount_type_code}', amount={self.amount} {self.currency})>"
