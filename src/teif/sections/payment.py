"""
Module pour la gestion dynamique des conditions de paiement TEIF.
"""
from typing import Dict, Any, List, Optional, Union
#import xml.etree.ElementTree as ET
from lxml import etree as ET

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
        # Create the payment term element
        pyt = ET.SubElement(parent, 'Pyt')
        
        # Add payment term code
        pyt_code = ET.SubElement(pyt, 'PaymentTermsTypeCode')
        pyt_code.text = term['code']
        
        # Add description if provided
        if 'description' in term and term['description']:
            desc = ET.SubElement(pyt, 'Description')
            desc.text = term['description']
        
        # Add due date if provided
        if 'due_date' in term and term['due_date']:
            due_date = ET.SubElement(pyt, 'DueDate')
            due_date.text = term['due_date']
        
        # Add amount if provided
        if 'amount' in term and term['amount'] is not None:
            # Create Moa element for payment amount
            moa = ET.SubElement(pyt, 'Moa', amountTypeCode='PAYMENT_AMOUNT')
            
            # Add amount element
            amount = ET.SubElement(moa, 'Amount')
            amount.set('currencyIdentifier', term.get('currency', self.currency))
            amount.text = str(term['amount'])
            
            # Add amount description
            desc = ET.SubElement(moa, 'AmountDescription', lang='FR')
            desc.text = 'Montant du paiement'
    
    def _add_financial_institution_element(self, parent: ET.Element, fi_data: Dict[str, Any]) -> None:
        """
        Helper method to add a financial institution element according to TEIF 1.8.8 specs.
        
        Args:
            parent: The parent XML element
            fi_data: Dictionary containing financial institution data with keys:
                - function_code: The function code (e.g., 'I-141')
                - account: Dictionary with 'number' and 'holder' keys
                - institution: Dictionary with 'name' and optional 'branch_code'
                - attributes: Optional additional attributes
        """
        # Create PytFii element with function code attribute
        pyt_fii = ET.SubElement(parent, 'PytFii')
        pyt_fii.set('functionCode', fi_data['function_code'])  # Add function code as attribute
        
        # Add attributes if any
        for key, value in fi_data.get('attributes', {}).items():
            pyt_fii.set(key, str(value))
        
        # Add account holder information
        account_holder = ET.SubElement(pyt_fii, 'AccountHolder')
        account_holder.text = str(fi_data['account']['holder'])
        
        # Add account number
        account_number = ET.SubElement(pyt_fii, 'AccountNumber')
        account_number.text = str(fi_data['account']['number'])
        
        # Add institution information
        institution = fi_data['institution']
        institution_elem = ET.SubElement(pyt_fii, 'Institution')
        
        # Add institution name
        inst_name = ET.SubElement(institution_elem, 'InstitutionName')
        inst_name.text = institution['name']
        
        # Add branch code if provided
        if institution.get('branch_code'):
            branch = ET.SubElement(institution_elem, 'Branch')
            branch_id = ET.SubElement(branch, 'BranchIdentifier')
            branch_id.text = str(institution['branch_code'])

def add_payment_terms(parent: ET.Element, payment_data: Dict[str, Any]) -> None:
    """
    Ajoute dynamiquement la section des conditions de paiement TEIF.
    
    Args:
        parent: L'élément parent XML
        payment_data: Dictionnaire contenant les configurations de paiement
            - code: Code du type de paiement (obligatoire, ex: 'I-10')
            - description: Description des conditions de paiement (obligatoire)
            - due_date: Date d'échéance (optionnelle, format YYYY-MM-DD)
            - discount_percent: Pourcentage de remise (optionnel)
            - discount_due_date: Date limite pour la remise (optionnelle, format YYYY-MM-DD)
    """
    if not payment_data:
        return
    
    # Vérifier les champs obligatoires
    if 'code' not in payment_data or 'description' not in payment_data:
        raise ValueError("Les champs 'code' et 'description' sont obligatoires pour les conditions de paiement")
    
    # Créer la structure de base PytSection > PytSectionDetails > Pyt
    pyt_section = ET.SubElement(parent, "PytSection")
    pyt_section_details = ET.SubElement(pyt_section, "PytSectionDetails")
    pyt = ET.SubElement(pyt_section_details, "Pyt")
    
    # Ajouter le code du type de paiement (correction de la faute de frappe)
    payment_terms_type = ET.SubElement(pyt, "PaymentTermsTypeCode")  # Correction ici
    payment_terms_type.text = str(payment_data['code'])
    
    # Ajouter la description des conditions de paiement (correction de la faute de frappe)
    payment_terms_desc = ET.SubElement(pyt, "PaymentTermsDescription")  # Correction ici
    payment_terms_desc.text = str(payment_data['description'])
    
    # Ajouter la date d'échéance si fournie
    if 'due_date' in payment_data and payment_data['due_date']:
        pyt_dtm = ET.SubElement(pyt, "PytDtm")
        date_text = ET.SubElement(pyt_dtm, "DateText", 
                               format="ddMMyy",  # Format cohérent avec le reste du document
                               functionCode="I-32")  # I-32 = Date d'échéance
        # Convertir la date au format ddMMyy
        due_date = datetime.strptime(payment_data['due_date'], "%Y-%m-%d")
        date_text.text = due_date.strftime("%d%m%y")
    
    # Ajouter les informations de remise si fournies
    if 'discount_percent' in payment_data and payment_data['discount_percent'] is not None:
        pyt_moa = ET.SubElement(pyt, "PytMoa", 
                              amountTypeCode="I-114",  # I-114 = Montant de la remise
                              percentageBasis="true",  # Indique qu'il s'agit d'un pourcentage
                              currencyCodeList="ISO_4217")  # Utilisation de la norme ISO
        
        # Ajouter le montant de la remise
        amount = ET.SubElement(pyt_moa, "Amount")
        amount.text = str(payment_data['discount_percent'])
        
        # Ajouter la description de la remise
        amount_desc = ET.SubElement(pyt_moa, "AmountDescription")
        amount_desc.text = f"Remise de {payment_data['discount_percent']}%"
        
        # Ajouter la date limite de remise si fournie
        if 'discount_due_date' in payment_data and payment_data['discount_due_date']:
            pyt_dtm = ET.SubElement(pyt, "PytDtm")
            date_text = ET.SubElement(pyt_dtm, "DateText",
                                   format="ddMMyy",  # Format cohérent
                                   functionCode="I-33")  # I-33 = Date limite de remise
            # Convertir la date au format ddMMyy
            discount_date = datetime.strptime(payment_data['discount_due_date'], "%Y-%m-%d")
            date_text.text = discount_date.strftime("%d%m%y")

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
    Ajoute dynamiquement les informations sur l'institution financière selon les spécifications TEIF 1.8.8.
    
    Args:
        parent: L'élément parent XML
        fi_data: Dictionnaire contenant les données de l'institution financière
            - payment_means_code: Code du moyen de paiement (ex: 'I-30' pour virement)
            - payment_id: Identifiant du paiement (obligatoire)
            - due_date: Date d'échéance (optionnelle, format YYYY-MM-DD)
            - payee_financial_account: Dictionnaire des informations de compte
                - iban: Numéro IBAN (obligatoire)
                - account_holder: Nom du titulaire du compte (obligatoire)
                - financial_institution: Nom de l'institution financière (obligatoire)
                - branch_code: Code de l'agence (optionnel)
            - attributes: Attributs supplémentaires (optionnel)
    """
    # Vérification des champs obligatoires
    required_fields = ['payment_means_code', 'payment_id', 'payee_financial_account']
    for field in required_fields:
        if field not in fi_data:
            raise ValueError(f"Le champ '{field}' est obligatoire pour l'institution financière")
    
    account_data = fi_data['payee_financial_account']
    required_account_fields = ['iban', 'account_holder', 'financial_institution']
    for field in required_account_fields:
        if field not in account_data:
            raise ValueError(f"Le champ '{field}' est obligatoire pour le compte bancaire")
    
    # Création de la structure de base
    pyt_section = ET.SubElement(parent, "PytSection")
    pyt_section_details = ET.SubElement(pyt_section, "PytSectionDetails")
    pyt = ET.SubElement(pyt_section_details, "Pyt")
    
    # Ajout du code de moyen de paiement
    payment_means = ET.SubElement(pyt, "PaymentMeansCode")
    payment_means.text = str(fi_data['payment_means_code'])
    
    # Ajout de l'identifiant de paiement
    payment_id = ET.SubElement(pyt, "PaymentID")
    payment_id.text = str(fi_data['payment_id'])
    
    # Ajout de la date d'échéance si fournie
    if 'due_date' in fi_data and fi_data['due_date']:
        pyt_dtm = ET.SubElement(pyt, "PytDtm")
        date_text = ET.SubElement(pyt_dtm, "DateText",
                               format="ddMMyy",
                               functionCode="I-32")  
        # Convertir la date au format ddMMyy
        due_date = datetime.strptime(fi_data['due_date'], "%Y-%m-%d")
        date_text.text = due_date.strftime("%d%m%y")
    
    # Ajout des informations sur l'institution financière
    pyt_fii = ET.SubElement(pyt, "PytFii", functionCode="I-141") 
    
    # Ajout des informations sur le titulaire du compte
    account_holder = ET.SubElement(pyt_fii, "AccountHolder")
    ET.SubElement(account_holder, "AccountNumber").text = account_data['iban']
    ET.SubElement(account_holder, "OwnerIdentifier").text = account_data['account_holder']
    
    # Ajout des informations sur l'institution financière
    institution = ET.SubElement(pyt_fii, "InstitutionIdentification")
    ET.SubElement(institution, "InstitutionName").text = account_data['financial_institution']
    
    # Ajout du code d'agence si fourni
    if 'branch_code' in account_data and account_data['branch_code']:
        ET.SubElement(institution, "BranchIdentifier").text = str(account_data['branch_code'])
    
    # Ajout des attributs personnalisés si fournis
    if 'attributes' in fi_data:
        for key, value in fi_data['attributes'].items():
            pyt_fii.set(key, str(value))

def create_invoice_moa(parent: ET.Element, amounts: Dict[str, float], currency: str = 'TND') -> None:
    """
    Create the InvoiceMOA section with monetary amounts.
    
    Args:
        parent: The parent XML element
        amounts: Dictionary containing amount types and values
        currency: Currency code (default: 'TND')
    """
    invoice_moa = ET.SubElement(parent, "InvoiceMoa")
    
    # Capital amount (I-179)
    if 'capital' in amounts:
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa", 
                          amountTypeCode="I-179",
                          currencyCodeList="ISO_4217")
        ET.SubElement(moa, "Amount", currencyIdentifier=currency).text = f"{amounts['capital']:.3f}"
    
    # Total amount with tax (I-180)
    if 'total_with_tax' in amounts:
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa",
                          amountTypeCode="I-180",
                          currencyCodeList="ISO_4217")
        ET.SubElement(moa, "Amount", currencyIdentifier=currency).text = f"{amounts['total_with_tax']:.3f}"
        # Add amount description in French
        amount_desc = ET.SubElement(moa, "AmountDescription", lang="fr")
        amount_desc.text = "Montant total avec taxe"
    
    # Total amount without tax (I-176)
    if 'total_without_tax' in amounts:
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa",
                          amountTypeCode="I-176",
                          currencyCodeList="ISO_4217")
        ET.SubElement(moa, "Amount", currencyIdentifier=currency).text = f"{amounts['total_without_tax']:.3f}"
    
    # Tax base amount (I-182)
    if 'tax_base' in amounts:
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa",
                          amountTypeCode="I-182",
                          currencyCodeList="ISO_4217")
        ET.SubElement(moa, "Amount", currencyIdentifier=currency).text = f"{amounts['tax_base']:.3f}"
    
    # Tax amount (I-181)
    if 'tax_amount' in amounts:
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa",
                          amountTypeCode="I-181",
                          currencyCodeList="ISO_4217")
        ET.SubElement(moa, "Amount", currencyIdentifier=currency).text = f"{amounts['tax_amount']:.3f}"

def create_invoice_tax(parent: ET.Element, taxes: List[Dict[str, Any]], currency: str = 'TND') -> None:
    """
    Create the InvoiceTax section with tax details.
    
    Args:
        parent: The parent XML element
        taxes: List of tax dictionaries
        currency: Currency code (default: 'TND')
    """
    invoice_tax = ET.SubElement(parent, "InvoiceTax")
    
    for tax in taxes:
        tax_details = ET.SubElement(invoice_tax, "InvoiceTaxDetails")
        
        # Create Tax element
        tax_elem = ET.SubElement(tax_details, "Tax")
        
        # Add tax type name with code
        tax_type = ET.SubElement(tax_elem, "TaxTypeName", code=tax.get('code', 'I-1603'))
        tax_type.text = tax.get('name', 'Autre taxe')
        
        # Add tax details
        tax_detail = ET.SubElement(tax_elem, "TaxDetails")
        ET.SubElement(tax_detail, "TaxRate").text = f"{tax.get('rate', 0):.1f}"
        
        # Add amount details
        if 'amount' in tax:
            amount_details = ET.SubElement(tax_details, "AmountDetails")
            moa = ET.SubElement(amount_details, "Moa",
                              amountTypeCode="I-178",  # Montant de la taxe
                              currencyCodeList="ISO_4217")
            ET.SubElement(moa, "Amount", currencyIdentifier=currency).text = f"{tax['amount']:.3f}"

# Add to __all__ to make it available for import
__all__ = [
    'add_payment_terms',
    'add_payment_term',
    'add_financial_institution',
    'create_invoice_moa',
    'create_invoice_tax',
    'PaymentSection'
]
