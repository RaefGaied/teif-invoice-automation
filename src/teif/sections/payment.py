"""
Module pour la gestion dynamique des conditions de paiement TEIF.
"""
from typing import Dict, Any, List, Optional, Union
import xml.etree.ElementTree as ET
from datetime import datetime, date

class PaymentSection:
    """
    A class to handle payment-related operations in TEIF documents.
    
    This class provides methods to create and manage payment terms
    and financial institution information according to the TEIF 1.8.8 standard.
    """
    
    def __init__(self, currency: str = 'TND'):
        """
        Initialize a new PaymentSection instance.
        
        Args:
            currency: Currency code (default: 'TND' for Tunisian Dinar)
        """
        self.currency = currency
        self.payment_terms = []
        self.financial_institutions = []
    
    def add_payment_term(self,
                        code: str,
                        description: str,
                        due_date: Optional[str] = None,
                        amount: Optional[float] = None,
                        attributes: Optional[Dict[str, str]] = None) -> None:
        """
        Add a payment term to the section.
        
        Args:
            code: Payment term code (e.g., 'I-114')
            description: Description of the payment term
            due_date: Optional due date in YYYY-MM-DD format
            amount: Optional payment amount
            attributes: Optional additional attributes for the payment term
        """
        term = {
            'code': code,
            'description': description,
            'due_date': due_date,
            'amount': amount,
            'currency': self.currency,
            'attributes': attributes or {}
        }
        self.payment_terms.append(term)
    
    def add_financial_institution(self,
                                function_code: str,
                                account_number: str,
                                account_holder: str,
                                institution_name: str,
                                branch_code: Optional[str] = None,
                                attributes: Optional[Dict[str, str]] = None) -> None:
        """
        Add financial institution information to the section.
        
        Args:
            function_code: Function code (e.g., 'I-141')
            account_number: Bank account number
            account_holder: Account holder identifier
            institution_name: Name of the financial institution
            branch_code: Optional branch code
            attributes: Optional additional attributes
        """
        fi = {
            'function_code': function_code,
            'account': {
                'number': account_number,
                'holder': account_holder
            },
            'institution': {
                'name': institution_name,
                'branch_code': branch_code
            },
            'attributes': attributes or {}
        }
        self.financial_institutions.append(fi)
    
    def to_xml(self, parent: ET.Element = None) -> ET.Element:
        """
        Generate the XML representation of the payment section.
        
        Args:
            parent: The parent XML element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            payment_section = ET.Element('PaymentSection')
        else:
            payment_section = ET.SubElement(parent, 'PaymentSection')
        
        # Add payment terms
        if self.payment_terms:
            pyt_section = ET.SubElement(payment_section, 'PytSection')
            for term in self.payment_terms:
                self._add_payment_term_element(pyt_section, term)
        
        # Add financial institutions
        if self.financial_institutions:
            for fi in self.financial_institutions:
                self._add_financial_institution_element(payment_section, fi)
        
        return payment_section
    
    def _add_payment_term_element(self, parent: ET.Element, term: Dict[str, Any]) -> None:
        """Helper method to add a payment term element."""
        pyt = ET.SubElement(parent, 'Pyt')
        
        # Add attributes if any
        for key, value in term.get('attributes', {}).items():
            pyt.set(key, str(value))
        
        # Add payment term code
        pyt_code = ET.SubElement(pyt, 'PytCode')
        pyt_code.text = term['code']
        
        # Add payment term description
        pyt_desc = ET.SubElement(pyt, 'PytDesc')
        pyt_desc.text = term['description']
        
        # Add due date if provided
        if term.get('due_date'):
            due_date = ET.SubElement(pyt, 'DueDate')
            due_date.text = term['due_date']
        
        # Add amount if provided
        if term.get('amount') is not None:
            from .amounts import create_amount_element
            amount_data = {
                'amount': term['amount'],
                'amount_type': 'I-114',  # Montant du paiement
                'currency': term.get('currency', self.currency)
            }
            create_amount_element(pyt, amount_data)
    
    def _add_financial_institution_element(self, parent: ET.Element, fi_data: Dict[str, Any]) -> None:
        """Helper method to add a financial institution element."""
        pyt_fii = ET.SubElement(parent, 'PytFii')
        
        # Add attributes if any
        for key, value in fi_data.get('attributes', {}).items():
            pyt_fii.set(key, str(value))
        
        # Add function code
        function_code = ET.SubElement(pyt_fii, 'FunctionCode')
        function_code.text = fi_data['function_code']
        
        # Add account information
        account = fi_data['account']
        account_elem = ET.SubElement(pyt_fii, 'Account')
        
        account_number = ET.SubElement(account_elem, 'AccountNumber')
        account_number.text = str(account['number'])
        
        account_holder = ET.SubElement(account_elem, 'AccountHolder')
        account_holder.text = str(account['holder'])
        
        # Add institution information
        institution = fi_data['institution']
        institution_elem = ET.SubElement(pyt_fii, 'FinancialInstitution')
        
        inst_name = ET.SubElement(institution_elem, 'Name')
        inst_name.text = institution['name']
        
        if 'branch_code' in institution and institution['branch_code']:
            branch_code = ET.SubElement(institution_elem, 'BranchCode')
            branch_code.text = str(institution['branch_code'])

def add_payment_terms(parent: ET.Element, payment_data: Dict[str, Any]) -> None:
    """
    Ajoute dynamiquement la section des conditions de paiement TEIF.
    
    Args:
        parent: L'élément parent XML
        payment_data: Dictionnaire contenant les configurations de paiement
            - description: Description des conditions de paiement (obligatoire)
            - type: Type de paiement (optionnel, ex: 'I-10')
            - due_date: Date d'échéance (optionnelle)
            - discount_percent: Pourcentage de remise (optionnel)
            - discount_due_date: Date limite pour la remise (optionnelle)
    """
    if not payment_data:
        return
    
    # Créer la structure de base PytSection > PytSectionDetails > Pyt
    pyt_section = ET.SubElement(parent, "PytSection")
    pyt_section_details = ET.SubElement(pyt_section, "PytSectionDetails")
    pyt = ET.SubElement(pyt_section_details, "Pyt")
    
    # Ajouter la description des conditions de paiement
    if 'description' in payment_data:
        payment_terms_desc = ET.SubElement(pyt, "PaymentTearmsDescription")
        payment_terms_desc.text = str(payment_data['description'])
    
    # Ajouter le type de paiement si fourni
    if 'type' in payment_data:
        payment_terms_type = ET.SubElement(pyt, "PaymentTearmsTypeCode")
        payment_terms_type.text = str(payment_data['type'])
    
    # Ajouter la date d'échéance si fournie
    if 'due_date' in payment_data:
        due_date = ET.SubElement(pyt, "DueDate")
        due_date.text = str(payment_data['due_date'])
    
    # Ajouter les informations de remise si fournies
    if 'discount_percent' in payment_data:
        discount = ET.SubElement(pyt, "DiscountPercent")
        discount.text = str(payment_data['discount_percent'])
        
        if 'discount_due_date' in payment_data:
            discount_date = ET.SubElement(pyt, "DiscountDueDate")
            discount_date.text = str(payment_data['discount_due_date'])

def add_payment_term(parent: ET.Element, term_data: Dict[str, Any]) -> None:
    """
    Ajoute dynamiquement un terme de paiement.
    
    Args:
        parent: L'élément parent XML
        term_data: Dictionnaire contenant les données du terme
            - code: Code du terme de paiement (ex: 'I-114')
            - description: Description du terme
            - attributes: Attributs supplémentaires pour l'élément Pyt (optionnel)
    """
    pyt_detail = ET.SubElement(parent, "PytSectionDetails")
    pyt_attrs = term_data.get('attributes', {})
    pyt = ET.SubElement(pyt_detail, "Pyt", **pyt_attrs)
    
    if 'code' in term_data:
        ET.SubElement(pyt, "PaymentTearmsTypeCode").text = str(term_data['code'])
    
    if 'description' in term_data:
        ET.SubElement(pyt, "PaymentTearmsDescription").text = term_data['description']

def add_financial_institution(parent: ET.Element, fi_data: Dict[str, Any]) -> None:
    """
    Ajoute dynamiquement les informations sur l'institution financière.
    
    Args:
        parent: L'élément parent XML
        fi_data: Dictionnaire contenant les données de l'institution financière
            - function_code: Code de fonction (ex: 'I-141')
            - account: Dictionnaire des informations de compte
                - number: Numéro de compte
                - holder: Identifiant du titulaire
            - institution: Dictionnaire des informations de l'institution
                - name: Nom de l'institution
                - branch_code: Code de l'agence
            - attributes: Attributs supplémentaires pour PytFii (optionnel)
    """
    pyt_detail = ET.SubElement(parent, "PytSectionDetails")
    
    # Add payment term if specified
    if 'term' in fi_data:
        add_payment_term(pyt_detail, fi_data['term'])
    
    # Prepare PytFii attributes
    fii_attrs = {
        'functionCode': fi_data.get('function_code', 'I-141')
    }
    if 'attributes' in fi_data:
        fii_attrs.update(fi_data['attributes'])
    
    pyt_fii = ET.SubElement(pyt_detail, "PytFii", **fii_attrs)
    
    # Add account information if available
    if 'account' in fi_data and fi_data['account']:
        account = fi_data['account']
        holder = ET.SubElement(pyt_fii, "AccountHolder")
        
        if 'number' in account:
            ET.SubElement(holder, "AccountNumber").text = str(account['number'])
        if 'holder' in account:
            ET.SubElement(holder, "OwnerIdentifier").text = str(account['holder'])
    
    # Add institution information if available
    if 'institution' in fi_data and fi_data['institution']:
        inst = fi_data['institution']
        inst_attrs = {}
        
        if 'branch_code' in inst:
            inst_attrs['nameCode'] = str(inst['branch_code'])
        
        inst_elem = ET.SubElement(pyt_fii, "InstitutionIdentification", **inst_attrs)
        
        if 'branch_code' in inst:
            ET.SubElement(inst_elem, "BranchIdentifier").text = str(inst['branch_code'])
        if 'name' in inst:
            ET.SubElement(inst_elem, "InstitutionName").text = inst['name']
    
    # Add custom elements if any
    if 'custom_elements' in fi_data:
        for elem_name, elem_value in fi_data['custom_elements'].items():
            if isinstance(elem_value, dict):
                ET.SubElement(pyt_fii, elem_name, **elem_value)
            else:
                ET.SubElement(pyt_fii, elem_name).text = str(elem_value)

# Add to __all__ to make it available for import
__all__ = [
    'add_payment_terms',
    'add_payment_term',
    'add_financial_institution',
    'PaymentSection'
]
