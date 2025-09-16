"""
Types partagés entre les modèles pour éviter les dépendances circulaires.
"""
from typing import TYPE_CHECKING, List, Optional
from datetime import date, datetime
from decimal import Decimal

# Types pour les imports différés
if TYPE_CHECKING:
    from .invoice import Invoice, InvoiceLine
    from .tax import LineTax, InvoiceTax, InvoiceMonetaryAmount
    from .company import Company, CompanyContact, CompanyAddress, ContactCommunication
    from .payment import PaymentTerm, PaymentMean
    from .signature import InvoiceSignature, GeneratedXmlFile
