"""
TEIF Reference Data Models.

This module contains reference data models used throughout the TEIF system,
including country codes, currency codes, units of measure, tax rates, and more.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Boolean, Text, DateTime, ForeignKey, 
    CheckConstraint, Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from .company import Company
    from .invoice import Invoice


class TEIFReferenceCode(BaseModel, TimestampMixin):
    """
    Reference codes for TEIF standard (I-0 to I-17).
    
    Contains official codes according to the Tunisian TEIF standard.
    """
    __tablename__ = 'teif_reference_codes'

    code_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of reference code (e.g., 'DOCUMENT_TYPE', 'TAX_TYPE')"
    )
    code_value: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Code value (e.g., 'I-11', 'I-1602')"
    )
    code_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Label in French"
    )
    code_label_ar: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Label in Arabic"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Detailed description of the code"
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this code is mandatory according to TEIF"
    )
    parent_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="Parent code for hierarchical codes"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Display order"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this code is active"
    )

    def __repr__(self) -> str:
        return f"<TEIFReferenceCode({self.code_value}: {self.code_label})>"

    @classmethod
    def get_by_type(cls, code_type: str) -> List["TEIFReferenceCode"]:
        """
        Retrieve all codes of a given type.
        
        Args:
            code_type: The type of codes to retrieve
            
        Returns:
            List of TEIFReferenceCode objects
        """
        return cls.query.filter_by(
            code_type=code_type, 
            is_active=True
        ).order_by(cls.sort_order).all()

    @classmethod
    def get_by_value(cls, code_value: str) -> Optional["TEIFReferenceCode"]:
        """
        Retrieve a code by its value.
        
        Args:
            code_value: The code value to look up
            
        Returns:
            TEIFReferenceCode object if found, None otherwise
        """
        return cls.query.filter_by(
            code_value=code_value, 
            is_active=True
        ).first()


class CountryCode(BaseModel, TimestampMixin):
    """
    Country codes according to ISO 3166-1.
    
    Used for company addresses and other country-related information.
    """
    __tablename__ = 'country_codes'

    iso_code_2: Mapped[str] = mapped_column(
        String(2),
        unique=True,
        nullable=False,
        comment="2-letter ISO country code (e.g., 'TN', 'FR')"
    )
    iso_code_3: Mapped[str] = mapped_column(
        String(3),
        unique=True,
        nullable=False,
        comment="3-letter ISO country code (e.g., 'TUN', 'FRA')"
    )
    name_fr: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Country name in French"
    )
    name_ar: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Country name in Arabic"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Country name in English"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this country is active"
    )

    def __repr__(self) -> str:
        return f"<CountryCode({self.iso_code_2}: {self.name_fr})>"


class CurrencyCode(BaseModel, TimestampMixin):
    """
    Currency codes according to ISO 4217.
    
    Used for invoice amounts and financial transactions.
    """
    __tablename__ = 'currency_codes'

    iso_code: Mapped[str] = mapped_column(
        String(3),
        unique=True,
        nullable=False,
        comment="3-letter ISO currency code (e.g., 'TND', 'EUR', 'USD')"
    )
    name_fr: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Currency name in French"
    )
    name_ar: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Currency name in Arabic"
    )
    symbol: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Currency symbol (e.g., '€', '$', 'د.ت')"
    )
    decimal_places: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="Number of decimal places to display"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this currency is active"
    )

    def __repr__(self) -> str:
        return f"<CurrencyCode({self.iso_code}: {self.name_fr})>"


class UnitOfMeasure(BaseModel, TimestampMixin):
    """
    Units of measure according to TEIF standard.
    
    Used for invoice line items to specify quantities.
    """
    __tablename__ = 'units_of_measure'

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="Unit code (e.g., 'PCE', 'KIT', 'KGM')"
    )
    name_fr: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Unit name in French"
    )
    name_ar: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Unit name in Arabic"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Detailed description of the unit"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Unit category (e.g., 'QUANTITY', 'WEIGHT')"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this unit is active"
    )

    def __repr__(self) -> str:
        return f"<UnitOfMeasure({self.code}: {self.name_fr})>"


class TaxRate(BaseModel, TimestampMixin):
    """
    Tax rates for Tunisian invoices.
    
    Includes VAT, stamp duties, and other applicable taxes.
    """
    __tablename__ = 'tax_rates'

    tax_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Tax code (e.g., 'I-1602', 'I-1601')"
    )
    tax_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of tax (e.g., 'TVA', 'TIMBRE')"
    )
    rate: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Tax rate (e.g., '19.0', '13.0', '7.0', '0.6')"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Description of the tax rate"
    )
    effective_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="Date when this rate becomes effective"
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="Date when this rate expires (if applicable)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this tax rate is active"
    )

    def __repr__(self) -> str:
        return f"<TaxRate({self.tax_type}: {self.rate}%)>"

    @classmethod
    def get_active_rates(cls, tax_type: Optional[str] = None) -> List["TaxRate"]:
        """
        Retrieve active tax rates, optionally filtered by type.
        
        Args:
            tax_type: Optional tax type to filter by
            
        Returns:
            List of active TaxRate objects
        """
        query = cls.query.filter_by(is_active=True)
        if tax_type:
            query = query.filter_by(tax_type=tax_type)
        return query.all()


class PaymentMethod(BaseModel, TimestampMixin):
    """
    Payment methods according to TEIF standard.
    
    Used to specify how an invoice should be paid.
    """
    __tablename__ = 'payment_methods'

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="TEIF payment method code (e.g., 'I-30')"
    )
    name_fr: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Payment method name in French"
    )
    name_ar: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Payment method name in Arabic"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Detailed description of the payment method"
    )
    requires_iban: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this payment method requires an IBAN"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this payment method is active"
    )

    def __repr__(self) -> str:
        return f"<PaymentMethod({self.code}: {self.name_fr})>"


def setup_reference_relationships() -> None:
    """
    Configure relationships with reference models.
    
    This function should be called after all models have been imported.
    """
    from .company import Company
    from .invoice import Invoice
    
    # Configure Company -> CountryCode relationship
    Company.country = relationship(
        "CountryCode",
        foreign_keys=[Company.address_country_code],
        primaryjoin="Company.address_country_code == CountryCode.iso_code_2",
        viewonly=True
    )
    
    # Configure Invoice -> CurrencyCode relationship
    Invoice.currency_ref = relationship(
        "CurrencyCode",
        foreign_keys=[Invoice.currency],
        primaryjoin="Invoice.currency == CurrencyCode.iso_code",
        viewonly=True
    )
