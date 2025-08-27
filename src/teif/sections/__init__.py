"""
Package contenant les modules pour la génération des sections TEIF.

Ce package suit la structure du standard TEIF 1.8.8 avec les sections principales :
1. En-tête (header.py)
2. Partenaires (partner.py)
3. Références (references.py)
4. Lignes de facture (lines.py)
5. Paiements (payment.py)
6. Taxes (taxes.py)
7. Montants (amounts.py)
8. Signature (signature.py)
9. Utilitaires communs (common.py, common_sections.py)
"""

# Import des modules de section pour les rendre disponibles au niveau du package
from .header import (
    create_header_element,
    create_bgm_element,
    create_dtm_element,
    HeaderSection
)  # noqa: F401
from .partner import (
    create_partner_section,
    add_seller_party,
    add_buyer_party,
    add_delivery_party,
    PartnerSection
)  # noqa: F401
from .lines import (
    LinSection,
    LinItem,
    add_invoice_lines,
    _add_invoice_line,
    add_invoice_lines_from_dict,
    ItemDescription,
    Quantity
)  # noqa: F401
from .amounts import (
    create_amount_element,
    create_tax_amount,
    create_line_amount,
    create_adjustment,
    create_invoice_totals,
    AmountsSection
)  # noqa: F401
from .taxes import (
    add_tax_detail,
    add_invoice_tax_section,
    TaxesSection
)  # noqa: F401
from .payment import (
    add_payment_terms,
    PaymentSection
)  # noqa: F401
from .references import (
    create_reference,
    add_ttn_reference,
    add_document_reference,
    ReferencesSection
)  # noqa: F401
from .signature import (
    create_signature,
    add_signature,
    SignatureError,
    SignatureSection
)  # noqa: F401
from .common import (
    format_date,
    format_currency,
    clean_text
)  # noqa: F401
from .common_sections import (
    create_nad_section,
    create_loc_section,
    create_rff_section,
    create_cta_section
)  # noqa: F401

__all__ = [
    # header.py
    'create_header_element',
    'create_bgm_element',
    'create_dtm_element',
    'HeaderSection',
    
    # partner.py
    'create_partner_section',
    'add_seller_party',
    'add_buyer_party',
    'add_delivery_party',
    'PartnerSection',
    
    # lines.py
    'LinSection',
    'LinItem',
    'add_invoice_lines',
    '_add_invoice_line',
    'add_invoice_lines_from_dict',
    'ItemDescription',
    'Quantity',
    
    # amounts.py
    'create_amount_element',
    'create_tax_amount',
    'create_line_amount',
    'create_adjustment',
    'create_invoice_totals',
    'AmountsSection',
    
    # taxes.py
    'add_tax_detail',
    'add_invoice_tax_section',
    'TaxesSection',
    
    # payment.py
    'add_payment_terms',
    'PaymentSection',
    
    # references.py
    'create_reference',
    'add_ttn_reference',
    'add_document_reference',
    'ReferencesSection',
    
    # signature.py
    'create_signature',
    'add_signature',
    'SignatureError',
    'SignatureSection',
    
    # common.py
    'format_date',
    'format_currency',
    'clean_text'
]
