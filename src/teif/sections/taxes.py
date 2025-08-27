"""
Module pour la gestion des taxes dans les documents TEIF.
"""
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

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
        from .amounts import create_amount_element
        
        # Validation des champs obligatoires
        required_fields = ['code', 'rate', 'amount', 'taxable_amount']
        missing_fields = [field for field in required_fields if field not in tax_data]
        
        if missing_fields:
            raise ValueError(
                f"Champs de taxe manquants: {', '.join(missing_fields)}. "
                "Les champs 'code', 'rate', 'amount' et 'taxable_amount' sont obligatoires."
            )
        
        # Créer l'élément de taxe
        tax = ET.SubElement(parent, 'Tax')
        
        # Ajouter le code de taxe
        code = ET.SubElement(tax, 'TaxTypeCode')
        code.text = str(tax_data['code'])
        
        # Ajouter le type de taxe si fourni
        if 'type' in tax_data and tax_data['type']:
            tax_type = ET.SubElement(tax, 'TaxType')
            tax_type.text = str(tax_data['type'])
        
        # Ajouter le taux de taxe
        rate = ET.SubElement(tax, 'TaxRate')
        rate.text = str(tax_data['rate'])
        
        # Ajouter la catégorie de taxe si fournie
        if 'tax_category' in tax_data and tax_data['tax_category']:
            category = ET.SubElement(tax, 'TaxCategory')
            category.text = str(tax_data['tax_category'])
        
        # Ajouter le motif d'exonération si fourni
        if 'exemption_reason' in tax_data and tax_data['exemption_reason']:
            exemption = ET.SubElement(tax, 'TaxExemptionReason')
            exemption.text = str(tax_data['exemption_reason'])
        
        # Ajouter le montant de la taxe
        amount_data = {
            'amount': tax_data['amount'],
            'amount_type': 'I-1603',  # Montant de la taxe
            'currency': tax_data.get('currency', self.currency)
        }
        create_amount_element(tax, amount_data)
        
        # Ajouter le montant taxable
        taxable_data = {
            'amount': tax_data['taxable_amount'],
            'amount_type': 'I-1601',  # Montant taxable
            'currency': tax_data.get('currency', self.currency)
        }
        create_amount_element(tax, taxable_data)
    
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
        
        # Ajouter chaque taxe
        for tax_data in self.taxes:
            self.add_tax_detail(taxes_section, tax_data)
        
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
