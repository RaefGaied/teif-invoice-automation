"""
Signature and XML generation models for TEIF system.

This module contains models for handling electronic signatures and generated XML files
in the Tunisian Electronic Invoice Format (TEIF) system.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, ForeignKey, Text, DateTime, Boolean, 
    BigInteger, Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .invoice import Invoice


class InvoiceSignature(BaseModel):
    """
    Electronic signatures for invoices.
    
    Represents digital signatures applied to invoices for authentication
    and non-repudiation according to TEIF standards.
    """
    __tablename__ = 'invoice_signatures'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to the signed invoice"
    )
    signature_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unique identifier for the signature"
    )
    signer_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Role of the signer (e.g., 'Fournisseur')"
    )
    signer_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Name of the signer"
    )
    
    # Cryptographic data
    x509_certificate: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="X.509 certificate in base64 format"
    )
    private_key_data: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Private key data (for testing only)"
    )
    key_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Key password (encrypted)"
    )
    
    # Signature metadata
    signing_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="Timestamp when the signature was created (ISO format)"
    )
    signature_value: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Computed signature value"
    )
    
    # Status
    signature_status: Mapped[str] = mapped_column(
        String(50),
        default='pending',
        index=True,
        comment="Signature status: 'pending', 'signed', 'verified', or 'invalid'"
    )
    verification_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="When the signature was last verified"
    )
    verification_result: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Detailed result of the signature verification"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", 
        back_populates="signatures"
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceSignature(id='{self.signature_id}', status='{self.signature_status}')>"


class GeneratedXmlFile(BaseModel):
    """
    Generated XML files for invoices.
    
    Stores XML representations of invoices along with validation
    and generation metadata.
    """
    __tablename__ = 'generated_xml_files'
    
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the source invoice"
    )
    xml_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual XML content of the invoice"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Filesystem path where the XML is stored"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        comment="Size of the XML file in bytes"
    )
    xml_version: Mapped[str] = mapped_column(
        String(10),
        default='1.8.8',
        comment="TEIF XML schema version"
    )
    validation_status: Mapped[str] = mapped_column(
        String(50),
        default='pending',
        comment="Current validation status"
    )
    validation_errors: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Any validation errors encountered"
    )
    schema_validation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether the XML passed schema validation"
    )
    signature_validation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether the XML signature is valid"
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="When this XML file was generated"
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", 
        back_populates="xml_files"
    )
    
    def __repr__(self) -> str:
        return f"<GeneratedXmlFile(invoice_id={self.invoice_id}, status='{self.validation_status}')>"
