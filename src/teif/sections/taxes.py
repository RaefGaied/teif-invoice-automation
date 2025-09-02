"""
Module pour la gestion des taxes dans les documents TEIF.
"""
from typing import Dict, Any, List, Optional
#import xml.etree.ElementTree as ET
from lxml import etree as ET

class TaxesSection:
    """
    A class to handle tax-related operations in TEIF documents.
    
    This class provides methods to create and manage tax information
    according to the TEIF 1.8.8 standard.
    """
    
    def __init__(self, currency: str = 'TND'):
        """
        Initialize a new TaxesSection instance.
        
        Args:
            currency: Currency code (default: 'TND' for Tunisian Dinar)
        """
        self.currency = currency
        self.taxes = []
    
    def add_tax(self,
                tax_code: str,
                tax_type: str,
                rate: float,
                amount: float,
                taxable_amount: float,
                tax_category: Optional[str] = None,
                exemption_reason: Optional[str] = None) -> None:
        """
        Add a tax entry to the section.
        
        Args:
            tax_code: Tax code according to TEIF standard (e.g., 'I-1602' for VAT)
            tax_type: Type of tax (e.g., 'TVA', 'Droit de timbre')
            rate: Tax rate as a percentage
            amount: Tax amount
            taxable_amount: Taxable amount
            tax_category: Optional tax category
            exemption_reason: Optional exemption reason code
        """
        self.taxes.append({
            'code': tax_code,
            'type': tax_type,
            'rate': rate,
            'amount': amount,
            'taxable_amount': taxable_amount,
            'tax_category': tax_category,
            'exemption_reason': exemption_reason,
            'currency': self.currency
        })
    
    def add_tax_detail(self, parent: ET.Element, tax_data: Dict[str, Any]) -> None:
        """
        Add tax details to a parent XML element.
        
        Args:
            parent: The parent XML element
            tax_data: Dictionary containing tax data
        
        Raises:
            ValueError: If tax data is invalid
        """
        # Validate required fields
        required_fields = ['code', 'type', 'rate', 'amount']
        for field in required_fields:
            if field not in tax_data or tax_data[field] is None:
                raise ValueError(f"Required tax field '{field}' is missing")

        # Create InvoiceTaxDetails element
        tax_details = ET.SubElement(parent, "InvoiceTaxDetails")
        
        # Add Tax element
        tax_elem = ET.SubElement(tax_details, "Tax")
        
        # Add TaxTypeName with code
        tax_type = ET.SubElement(tax_elem, "TaxTypeName", code=tax_data['code'])
        tax_type.text = tax_data['type']
        
        # Add TaxDetails with TaxRate
        tax_detail = ET.SubElement(tax_elem, "TaxDetails")
        ET.SubElement(tax_detail, "TaxRate").text = f"{float(tax_data['rate']):.1f}"
        
        # Add TaxableAmount if provided
        if 'taxable_amount' in tax_data and tax_data['taxable_amount'] is not None:
            tax_base = ET.SubElement(tax_detail, "TaxRateBasis")
            tax_base.text = f"{float(tax_data['taxable_amount']):.2f}"
        
        # Add AmountDetails with Moa for tax amount
        amount_details = ET.SubElement(tax_details, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa", 
                          amountTypeCode="I-178",  # Montant de la taxe
                          currencyCodeList="ISO_4217")
        ET.SubElement(moa, "Amount", 
                     currencyIdentifier=self.currency).text = f"{float(tax_data['amount']):.3f}"
        
        # Add tax category if provided
        if 'tax_category' in tax_data and tax_data['tax_category']:
            ET.SubElement(tax_elem, "TaxCategory").text = tax_data['tax_category']
        
        # Add exemption reason if provided
        if 'exemption_reason' in tax_data and tax_data['exemption_reason']:
            ET.SubElement(tax_elem, "TaxExemptionReason").text = tax_data['exemption_reason']

    def build(self, parent: ET.Element) -> None:
        """
        Build the tax section and add it to the parent element.
        
        Args:
            parent: The parent XML element to add the tax section to
        """
        if not self.taxes:
            return
            
        invoice_tax = ET.SubElement(parent, "InvoiceTax")
        
        for tax in self.taxes:
            self.add_tax_detail(invoice_tax, tax)

    def to_xml(self, parent: ET.Element = None) -> ET.Element:
        """
        Generate the XML representation of the taxes section.
        
        Args:
            parent: The parent XML element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            taxes_section = ET.Element('TaxesSection')
        else:
            taxes_section = ET.SubElement(parent, 'TaxesSection')
        
        self.build(taxes_section)
        
        return taxes_section

def add_tax_detail(parent: ET.Element, tax_data: Dict[str, Any], currency: str = 'TND') -> None:
    """
    Ajoute les détails de taxe à un élément parent.
    
    Args:
        parent: L'élément parent XML
        tax_data: Dictionnaire contenant les données de taxe
        currency: Code devise (défaut: 'TND')
    
    Raises:
        ValueError: Si les données de taxe sont invalides
    """
    from .amounts import create_amount_element
    
    # Validation des champs obligatoires
    required_fields = ['code', 'rate', 'amount']
    missing_fields = [field for field in required_fields if field not in tax_data]
    
    if missing_fields:
        raise ValueError(
            f"Champs de taxe manquants: {', '.join(missing_fields)}. "
            "Les champs 'code', 'rate' et 'amount' sont obligatoires."
        )
    
    try:
        # Création de l'élément de taxe
        tax_elem = ET.SubElement(parent, "TaxTotal")
        
        # Montant de la taxe
        create_amount_element(
            tax_elem,
            {
                'amount': tax_data['amount'],
                'currency': currency,
                'amount_type': 'I-160',  # Montant de la taxe
                'amount_type_name': 'Montant de la taxe'
            }
        )
        
        # Détails de la taxe
        tax_subtotal = ET.SubElement(tax_elem, "TaxSubtotal")
        
        # Montant taxable
        if 'taxable_amount' in tax_data:
            create_amount_element(
                tax_subtotal,
                {
                    'amount': tax_data['taxable_amount'],
                    'currency': currency,
                    'amount_type': 'I-162',  # Montant taxable
                    'amount_type_name': 'Montant taxable'
                }
            )
        
        # Taux de taxe
        tax_category = ET.SubElement(tax_subtotal, "TaxCategory")
        tax_scheme = ET.SubElement(tax_category, "TaxScheme")
        ET.SubElement(
            tax_scheme,
            "ID",
            schemeID=tax_data.get('code_scheme', 'I-1600')
        ).text = str(tax_data['code'])
        
        # Taux de taxe
        tax_percent = ET.SubElement(tax_category, "Percent")
        tax_percent.text = str(tax_data['rate'])
        
        # Libellé de la taxe
        if 'name' in tax_data:
            ET.SubElement(tax_category, "TaxExemptionReason").text = str(tax_data['name'])
    
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de données de taxe invalide: {str(e)}")

def add_invoice_tax_section(parent: ET.Element, tax_data: Dict[str, Any], currency: str = 'TND') -> None:
    """
    Ajoute une section de taxe à la facture selon le standard TEIF 1.8.8.
    
    Args:
        parent: L'élément parent XML (InvoiceBody)
        tax_data: Dictionnaire contenant les informations de taxe
            - code: Code de taxe (obligatoire, selon le référentiel I16)
            - type_name: Nom du type de taxe (obligatoire, max 35 caractères)
            - category: Catégorie de taxe (optionnel, max 6 caractères)
            - rate: Taux de taxe (obligatoire)
            - basis: Base de calcul de la taxe (optionnel)
            - amount: Montant de la taxe (obligatoire)
            - currency: Code devise (optionnel, défaut: 'TND')
    """
    if not tax_data or 'code' not in tax_data or 'type_name' not in tax_data or 'rate' not in tax_data or 'amount' not in tax_data:
        return
    
    # Créer l'élément InvoiceTax
    invoice_tax = ET.SubElement(parent, 'InvoiceTax')
    
    # Créer la section des détails de taxe
    tax_details = ET.SubElement(invoice_tax, 'InvoiceTaxDetails')
    
    # Créer l'élément Tax
    tax = ET.SubElement(tax_details, 'Tax')
    
    # Ajouter le type de taxe avec son code
    tax_type = ET.SubElement(tax, 'TaxTypeName', code=str(tax_data['code']))
    tax_type.text = str(tax_data['type_name'])[:35]  # Limité à 35 caractères
    
    # Ajouter la catégorie de taxe si fournie
    if 'category' in tax_data and tax_data['category']:
        category = ET.SubElement(tax, 'TaxCategory')
        category.text = str(tax_data['category'])[:6]  # Limité à 6 caractères
    
    # Ajouter les détails de la taxe (taux et base de calcul)
    tax_details_elem = ET.SubElement(tax, 'TaxDetails')
    
    # Taux de taxe
    rate = ET.SubElement(tax_details_elem, 'TaxRate')
    rate.text = str(tax_data['rate'])
    
    # Base de calcul si fournie
    if 'basis' in tax_data and tax_data['basis'] is not None:
        basis = ET.SubElement(tax_details_elem, 'TaxRateBasis')
        basis.text = str(tax_data['basis'])
    
    # Créer la section des montants
    amount_details = ET.SubElement(tax, 'AmountDetails')
    
    # Ajouter le montant de la taxe
    moa = ET.SubElement(amount_details, 'Moa', amountTypeCode='TAX_AMOUNT')
    
    # Montant de la taxe
    amount = ET.SubElement(moa, 'Amount')
    amount.set('currencyIdentifier', tax_data.get('currency', currency))
    amount.text = str(tax_data['amount'])
    
    # Description du montant
    desc = ET.SubElement(moa, 'AmountDescription', lang='FR')
    desc.text = 'Montant de la taxe'

def add_invoice_tax_section_old(parent: ET.Element, tax_data: Dict[str, Any], currency: str = 'TND') -> None:
    """
    Ajoute une section de taxe à la facture.
    
    Args:
        parent: L'élément parent XML
        tax_data: Dictionnaire contenant les informations de taxe
        currency: Code devise (défaut: 'TND')
    """
    tax_total = ET.SubElement(parent, "TaxTotal")
    
    # Montant total des taxes
    if 'amount' in tax_data:
        from .amounts import create_amount_element
        create_amount_element(
            tax_total,
            {
                'amount': tax_data['amount'],
                'currency': currency,
                'amount_type': 'I-160',  # Montant total des taxes
                'amount_type_name': 'Montant total des taxes'
            }
        )
    
    # Détails des taxes
    if 'taxes' in tax_data and isinstance(tax_data['taxes'], list):
        for tax in tax_data['taxes']:
            add_tax_detail(tax_total, tax, currency)

__all__ = [
    'add_tax_detail',
    'add_invoice_tax_section',
    'TaxesSection'
]
