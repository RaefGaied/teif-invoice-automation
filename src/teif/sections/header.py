"""
TEIF 1.8.8 Header Section Implementation

This module implements the InvoiceHeader (Level 1) and BGM (Level 2) sections
as per TEIF 1.8.8 standard. It handles document identification and related
information for the TEIF XML structure.
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import xml.etree.ElementTree as ET
from ..utils.validators import (
    validate_required_fields,
    validate_date_format,
    validate_code_list,
    validate_email,
    validate_phone_number
)

# TEIF 1.8.8 Constants
TEIF_VERSION = "1.8.8"
CONTROLLING_AGENCY = "TTN"
DEFAULT_TEST_INDICATOR = "0"
DEFAULT_LANGUAGE = "fr"
DEFAULT_CURRENCY = "TND"

# ============================================================================
# I-0: Types d'Identifiants Partenaires
# ============================================================================
PARTNER_IDENTIFIER_TYPES = {
    "I-01": "Matricule Fiscal Tunisien",
    "I-02": "Carte d'identité nationale",
    "I-03": "Carte de séjour",
    "I-04": "Matricule Fiscal non tunisien"
}

# ============================================================================
# I-1: Types de Documents
# ============================================================================
DOCUMENT_TYPES = {
    # Standard TEIF 1.8.8 document types
    "I-11": "Facture",
    "I-12": "Facture d'avoir",
    "I-13": "Note d'honoraire",
    "I-14": "Décompte (marché public)",
    "I-15": "Facture Export",
    "I-16": "Bon de commande",
    
    # Legacy document types (for backward compatibility)
    "INVOICE": "380",
    "CREDIT_NOTE": "381",
    "DEBIT_NOTE": "383",
    "SELF_BILLING": "389",
    "PRO_FORMA": "325",
    "COMMERCIAL_INVOICE": "325",
    "COMMERCIAL_CREDIT_NOTE": "381",
    "COMMERCIAL_DEBIT_NOTE": "383"
}

# ============================================================================
# I-2: Codes de Langues
# ============================================================================
LANGUAGE_CODES = {
    "ar": "Arabe",
    "fr": "Français",
    "en": "Anglais",
    "or": "Autre"
}

# ============================================================================
# I-3: Fonctions de Dates (DTM Function Codes)
# ============================================================================
DTM_FUNCTION_CODES = {
    # Standard TEIF 1.8.8 date function codes
    "I-31": "Date d'émission du document",
    "I-32": "Date limite de paiement",
    "I-33": "Date de confirmation",
    "I-34": "Date d'expiration",
    "I-35": "Date du fichier joint",
    "I-36": "Période de facturation",
    "I-37": "Date de la génération de la référence",
    "I-38": "Autre",
    
    # Legacy numeric codes (for backward compatibility)
    "3": "Requested Delivery Date",
    "35": "Payment Due Date",
    "50": "Shipping Date",
    "63": "Estimated Delivery Date",
    "64": "Nominal Delivery Date",
    "137": "Invoice Date",
    "171": "Agreement Date",
    "198": "Validity Start Date",
    "199": "Validity End Date"
}

# ============================================================================
# I-4: Sujets de Texte Libre
# ============================================================================
FREE_TEXT_SUBJECTS = {
    "I-41": "Description marchandise/service",
    "I-42": "Description acquittement",
    "I-43": "Conditions du prix",
    "I-44": "Description de l'erreur",
    "I-45": "Période de temps",
    "I-46": "Formule de calcul du prix",
    "I-47": "Code incoterme livraison",
    "I-48": "Observation"
}

# ============================================================================
# I-5: Fonctions de Localisation
# ============================================================================
LOCATION_FUNCTIONS = {
    "I-51": "Adresse de livraison",
    "I-52": "Adresse de paiement",
    "I-53": "Pays de provenance",
    "I-54": "Pays d'achat",
    "I-55": "Pays",
    "I-56": "Ville",
    "I-57": "Adresse de courrier",
    "I-58": "Pays première destination",
    "I-59": "Pays destination définitive"
}

# ============================================================================
# I-6: Fonctions Partenaires
# ============================================================================
PARTNER_FUNCTIONS = {
    "I-61": "Acheteur",
    "I-62": "Fournisseur",
    "I-63": "Vendeur",
    "I-64": "Client",
    "I-65": "Receveur de la facture",
    "I-66": "Émetteur de la facture",
    "I-67": "Exportateur",
    "I-68": "Importateur",
    "I-69": "Inspecteur"
}

# ============================================================================
# I-13: Moyens de Paiement
# ============================================================================
PAYMENT_MEANS = {
    "I-131": "Espèce",
    "I-132": "Chèque",
    "I-133": "Chèque certifié",
    "I-134": "Prélèvement bancaire",
    "I-135": "Virement bancaire",
    "I-136": "Swift",
    "I-137": "Autre"
}

# ============================================================================
# I-16: Types de Taxes
# ============================================================================
TAX_TYPES = {
    "I-161": "Droit de consommation",
    "I-162": "Taxe professionnelle de compétitivité FODEC",
    "I-163": "Taxe sur les emballages métalliques",
    "I-164": "Taxe pour la protection de l'environnement TPE",
    "I-165": "Taxe FODET (secteur tourisme)",
    "I-166": "Taxe sur les climatiseurs",
    "I-167": "Taxes sur les lampes et tubes",
    "I-168": "Taxes sur fruits et légumes (TFL)",
    "I-169": "Taxes sur les produits de la pêche",
    "I-160": "Taxes RB (non soumis à la TVA)",
    "I-1601": "Droit de timbre",
    "I-1602": "TVA",  # Le plus utilisé
    "I-1603": "Autre",
    "I-1604": "Retenue à la source"
}

# ============================================================================
# I-17: Types de Montants
# ============================================================================
AMOUNT_TYPES = {
    "I-171": "Montant total HT de l'article",
    "I-172": "Montant total HT des articles",
    "I-173": "Montant payé",
    "I-174": "Montant HT de la charge/Service",
    "I-175": "Montant total HT des charges/Services",
    "I-176": "Montant total HT facture",  # Important
    "I-177": "Montant base taxe",
    "I-178": "Montant Taxe",
    "I-179": "Capital de l'entreprise",
    "I-180": "Montant Total TTC facture",  # Important
    "I-181": "Montant total Taxe",
    "I-182": "Montant total base taxe",
    "I-183": "Montant HT article unitaire",
    "I-184": "Montant total TTC des charges/Services",
    "I-185": "Montant total exonéré",
    "I-186": "Montant de crédit",
    "I-187": "Montant objet de suspension de la TVA",
    "I-188": "Montant net de l'article",
    "I-189": "Montant total HT toutes charges comprises"
}

# ============================================================================
# Valid DTM formats
# ============================================================================
DTM_FORMATS = [
    "DDMMYY",
    "DDMMYYHHMM",
    "DDMMYY-DDMMYY",
    "YYYYMMDD",
    "YYYYMMDDHHMM",
    "YYYYMMDD-HHMM",
    "YYYYMMDDHHMMSS",
    "YYMMDD",
    "YYMMDDHHMM",
    "YYMMDDHHMMSS"
]

# ============================================================================
# Most Used Codes (for quick reference)
# ============================================================================
MOST_USED_CODES = {
    # Document Types
    "I-11": "Facture",
    "I-31": "Date d'émission du document",
    "I-32": "Date limite de paiement",
    
    # Partner Identifiers
    "I-01": "Matricule Fiscal Tunisien",
    
    # Partner Functions
    "I-61": "Acheteur",
    "I-62": "Fournisseur",
    
    # Tax Types
    "I-1602": "TVA",
    
    # Amount Types
    "I-176": "Montant total HT facture",
    "I-180": "Montant Total TTC facture"
}

# ============================================================================
# Legacy Reference Types (for backward compatibility)
# ============================================================================
REFERENCE_TYPES = {
    "AWB": "Air Waybill",
    "BN": "Bill of Lading Number",
    "CD": "Credit Note Number",
    "CN": "Consignment Note",
    "CR": "Customer Reference",
    "CT": "Contract Number",
    "DN": "Debit Note Number",
    "IV": "Invoice Number",
    "ON": "Order Number",
    "PL": "Packing List",
    "PO": "Purchase Order",
    "RFQ": "Request for Quotation",
    "SI": "Shipping Instruction",
    "SO": "Sales Order",
    "VN": "Vendor Number"
}

def validate_tax_identifier(tax_id: str) -> None:
    """
    Validate Tunisian tax identification number format according to TEIF 1.8.8 spec.
    
    Format: 7 digits + 1 control character (A-Z except I,O,U) + 
            1 VAT code (A,P,B,F,N) + 1 category code (M,P,C,N,E) + 3 digits
    """
    if not tax_id or len(tax_id) != 13:
        raise ValueError("Matricule fiscal doit contenir exactement 13 caractères")
    
    # 1. First 7 digits (identifier)
    identifier = tax_id[:7]
    if not identifier.isdigit():
        raise ValueError("Les 7 premiers caractères doivent être des chiffres")
    
    # 2. Control character (8th character)
    control_char = tax_id[7].upper()
    if control_char in 'IOU' or not control_char.isalpha():
        raise ValueError("Le 8ème caractère doit être une lettre (A-Z sauf I, O, U)")
    
    # 3. VAT code (9th character)
    vat_code = tax_id[8].upper()
    if vat_code not in ['A', 'P', 'B', 'F', 'N']:
        raise ValueError("Code TVA invalide. Doit être A, P, B, F ou N")
    
    # 4. Category code (10th character)
    category_code = tax_id[9].upper()  # Convertir en majuscules pour la validation
    if category_code not in ['M', 'P', 'C', 'N', 'E']:
        raise ValueError("Code catégorie invalide. Doit être M, P, C, N ou E")
    
    # 5. Establishment number (last 3 digits)
    establishment = tax_id[10:]
    if not establishment.isdigit() or len(establishment) != 3:
        raise ValueError("Numéro d'établissement invalide. Doit être composé de 3 chiffres")
        
    # Additional validation for secondary establishments
    if category_code == 'E' and establishment == '000':
        raise ValueError("Un établissement secondaire doit avoir un numéro différent de 000")

def create_teif_root(version: str = "1.8.8") -> ET.Element:
    """
    Create the root TEIF element with proper attributes.
    
    Args:
        version: TEIF version (default: "1.8.8")
        
    Returns:
        ET.Element: Root TEIF element with proper XML declaration
    """
    # Create XML with proper declaration
    ET.register_namespace('', 'http://www.tn.gov/teif')
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    
    # Create root element with attributes
    root = ET.Element("TEIF", 
                     attrib={
                         "controlingAgency": "TTN",
                         "version": version
                     })
    
    # Add schema location
    root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", 
            "http://www.tn.gov/teif TEIF_1.8.8.xsd")
    
    return root

def create_invoice_header(parent: ET.Element, 
                         sender_identifier: str,
                         receiver_identifier: str = None,
                         receiver_type: str = 'I-01') -> ET.Element:
    """
    Create InvoiceHeader section according to TEIF 1.8.8 specification.
    
    Args:
        parent: Parent XML element
        sender_identifier: Sender's tax identifier (required)
        receiver_identifier: Receiver's identifier (optional)
        receiver_type: Type of receiver identifier (default: 'I-01' for tax ID)
        
    Returns:
        ET.Element: Created InvoiceHeader element
    """
    invoice_header = ET.SubElement(parent, 'InvoiceHeader')
    
    # Add sender identifier (required)
    sender = ET.SubElement(invoice_header, 'MessageSenderIdentifier', type='I-01')
    sender.text = sender_identifier
    
    # Add receiver identifier (optional)
    if receiver_identifier:
        receiver = ET.SubElement(invoice_header, 'MessageRecieverIdentifier', 
                               type=receiver_type)
        receiver.text = receiver_identifier
    
    return invoice_header

def create_invoice_body(parent: ET.Element) -> ET.Element:
    """
    Create InvoiceBody section.
    
    Args:
        parent: Parent XML element
        
    Returns:
        ET.Element: Created InvoiceBody element
    """
    return ET.SubElement(parent, 'InvoiceBody')

def create_bgm_section(parent: ET.Element, 
                      document_number: str, 
                      document_type: str = 'I-11') -> ET.Element:
    """
    Create BGM (Beginning of Message) section.
    
    Args:
        parent: Parent XML element
        document_number: Document number (required)
        document_type: Document type code (default: 'I-11' for invoice)
        
    Returns:
        ET.Element: Created Bgm element
    """
    bgm = ET.SubElement(parent, 'Bgm')
    
    # Add document identifier
    doc_id = ET.SubElement(bgm, 'DocumentIdentifier')
    doc_id.text = document_number
    
    # Add document type
    doc_type = ET.SubElement(bgm, 'DocumentType', code=document_type)
    doc_type.text = DOCUMENT_TYPES.get(document_type, 'Facture')
    
    return bgm

def add_date_section(parent: ET.Element, 
                    date_text: str, 
                    function_code: str, 
                    date_format: str) -> ET.Element:
    """
    Add a date section to the parent element.
    
    Args:
        parent: Parent XML element (should be InvoiceBody)
        date_text: Date value in specified format
        function_code: Date function code (e.g., 'I-31' for invoice date)
        date_format: Date format (e.g., 'ddMMyy')
        
    Returns:
        ET.Element: The parent Dtm element containing all dates
    """
    # Find or create Dtm element directly under InvoiceBody
    dtm = parent.find('Dtm')
    if dtm is None:
        dtm = ET.SubElement(parent, 'Dtm')
    
    # Add the date text with its attributes
    date_elem = ET.SubElement(dtm, 'DateText', 
                             format=date_format,
                             functionCode=function_code)
    date_elem.text = date_text
    
    return dtm

# Example usage:
# root = create_teif_root()
# invoice_header = create_invoice_header(root, "0736202XAM000", "0914089JAM000")
# invoice_body = create_invoice_body(root)
# bgm = create_bgm_section(invoice_body, "INV-2023-001")
# add_date_section(invoice_body, "070612", "I-31", "ddMMyy")
# add_date_section(invoice_body, "010512-310512", "I-36", "ddMMyy-ddMMyy")
# add_date_section(invoice_body, "070712", "I-32", "ddMMyy")

def create_header_element(data: Dict[str, Any]) -> ET.Element:
    """
    Create the InvoiceHeader element as per TEIF 1.8.8 standard.
    
    Args:
        data: Dictionary containing:
            - sender_identifier (str): Matricule fiscal de l'émetteur (required)
            - receiver_identifier (str, optional): Identifiant du destinataire
            - receiver_identifier_type (str, optional): Type d'identifiant (default: 'I-01')
            
    Returns:
        ET.Element: InvoiceHeader XML element
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    validate_required_fields(data, ['sender_identifier'])
    
    root = create_teif_root()
    invoice_header = create_invoice_header(root, data['sender_identifier'], data.get('receiver_identifier'), data.get('receiver_identifier_type'))
    
    return root

def create_bgm_element(parent: ET.Element, bgm_data: Dict[str, Any]) -> ET.Element:
    """
    Create BGM (Document Identification) section as per TEIF 1.8.8 standard.
    
    Args:
        parent: Parent XML element
        bgm_data: Dictionary containing:
            - document_number (str): Numéro du document (required, max 70 chars)
            - document_type (str): Code type de document (e.g., 'I-11' pour facture)
            - document_type_label (str, optional): Libellé du type de document
            - references (list, optional): Liste de références de documents
    """
    validate_required_fields(bgm_data, ['document_number', 'document_type'])
    
    # Create BGM element
    bgm = create_bgm_section(parent, bgm_data['document_number'], bgm_data['document_type'])
    
    # 3. DocumentReferences (optional)
    if 'references' in bgm_data and bgm_data['references']:
        refs_elem = ET.SubElement(bgm, 'DocumentReferences')
        
        for ref in bgm_data['references']:
            if 'reference' not in ref:
                continue
                
            ref_elem = ET.SubElement(refs_elem, 'DocumentReference')
            
            # Reference number (required)
            ref_number = ET.SubElement(ref_elem, 'Reference')
            ref_number.text = str(ref['reference']).strip()
            
            # Reference type (optional)
            if 'reference_type' in ref:
                ref_number.set('type', str(ref['reference_type']).strip())
            
            # Reference date (optional)
            if 'reference_date' in ref and ref['reference_date']:
                ref_date = ET.SubElement(ref_elem, 'ReferenceDate')
                ref_date.text = str(ref['reference_date']).strip()
    
    return bgm

def create_dtm_element(parent: ET.Element, date_data: Dict[str, str]) -> ET.Element:
    """
    Create or update a Dtm element with date information.
    
    Args:
        parent: Parent XML element (should be InvoiceBody)
        date_data: Dictionary containing date information
        
    Returns:
        ET.Element: The Dtm element containing all dates
    """
    # Find existing Dtm element or create a new one
    dtm = parent.find('Dtm')
    if dtm is None:
        dtm = ET.SubElement(parent, 'Dtm')
    
    # Add the date text with its attributes
    date_elem = ET.SubElement(dtm, 'DateText', 
                            format=date_data['format'],
                            functionCode=date_data['function_code'])
    date_elem.text = date_data['date_text']
    
    return dtm

def _validate_and_format_datetime(dt_str: str) -> str:
    """
    Validate and format datetime string to ISO 8601 format with timezone.
    
    Args:
        dt_str: Input datetime string
        
    Returns:
        str: Formatted datetime string in ISO 8601 format with timezone
        
    Raises:
        ValueError: If datetime format is invalid
    """
    try:
        # Try parsing with timezone
        if 'Z' in dt_str.upper() or '+' in dt_str or '-' in dt_str[-6:]:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(dt_str)
            # Assume UTC if no timezone specified
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        
        # Return in ISO 8601 format with timezone
        return dt.isoformat()
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid datetime format: {dt_str}. Expected ISO 8601 format.") from e

def _validate_document_type(doc_type: str) -> str:
    """
    Validate document type against TEIF 1.8.8 standard (Referential-I1).
    
    Args:
        doc_type: Document type code or name (max 6 chars for code)
        
    Returns:
        str: Validated document type code
        
    Raises:
        ValueError: If document type is invalid
    """
    if not doc_type or len(str(doc_type).strip()) == 0:
        raise ValueError("Document type cannot be empty")
        
    doc_type = str(doc_type).strip().upper()
    
    # Check if it's a known document type name
    if doc_type in DOCUMENT_TYPES:
        return DOCUMENT_TYPES[doc_type]
    
    # Check if it's a valid document type code
    if doc_type in DOCUMENT_TYPES.values():
        return doc_type
    
    # Check if it's a valid reference type code
    if doc_type in REFERENCE_TYPES:
        return doc_type
    
    # If custom code, ensure it meets format requirements
    if len(doc_type) > 6:
        raise ValueError(f"Document type code cannot exceed 6 characters: {doc_type}")
    
    # Allow custom 3-digit codes (common in EDIFACT)
    if doc_type.isdigit() and len(doc_type) <= 3:
        return doc_type.zfill(3)
    
    # Allow alphanumeric codes (e.g., 'PO', 'SO')
    if doc_type.isalnum():
        return doc_type
    
    raise ValueError(
        f"Invalid document type: {doc_type}. "
        f"Must be one of {list(DOCUMENT_TYPES.keys())}, a valid code, "
        "or a custom alphanumeric code (max 6 chars)."
    )

def _validate_dtm_function_code(code: str) -> None:
    """
    Validate DTM function code against Referential-I3.
    
    Args:
        code: Function code to validate
        
    Raises:
        ValueError: If function code is invalid
    """
    if not code or len(str(code).strip()) == 0:
        raise ValueError("Function code cannot be empty")
        
    code = str(code).strip()
    
    # Only allow function codes from the DTM_FUNCTION_CODES dictionary
    if code not in DTM_FUNCTION_CODES:
        raise ValueError(
            f"Invalid DTM function code: {code}. "
            f"Must be one of {list(DTM_FUNCTION_CODES.keys())}"
        )

def _validate_dtm_format(fmt: str) -> None:
    """
    Validate DTM format string.
    
    Args:
        fmt: Format string to validate
        
    Raises:
        ValueError: If format is invalid
    """
    if not fmt or len(str(fmt).strip()) == 0:
        raise ValueError("Format cannot be empty")
        
    fmt = str(fmt).strip().upper()
    
    if fmt not in DTM_FORMATS:
        raise ValueError(
            f"Invalid DTM format: {fmt}. "
            f"Must be one of: {', '.join(DTM_FORMATS)}"
        )

def add_dtm_section(parent: ET.Element, dtm_data: Dict[str, Any]) -> ET.Element:
    """
    Add a DTM (Date/Time/Period) section to the TEIF document.
    
    This section can appear multiple times in a TEIF document.
    
    Args:
        parent: Parent XML element to which the DTM section will be added
        dtm_data: Dictionary containing date data with the following keys:
            - type: Date type code (required, see list of common codes below)
            - date: Date in the specified format (required)
            - format: Date format code (optional, defaults to '102' for YYYYMMDD)
            - time_zone: Time zone (optional, e.g., '+01:00')
            - period: Period (optional, for date ranges)
            - description: Human-readable description (optional)
            
    Returns:
        ET.Element: The created DTM element
        
    Raises:
        ValueError: If required fields are missing or invalid
        
    Common date type codes:
        - 3: Requested delivery date
        - 35: Payment due date
        - 50: Shipping date
        - 63: Estimated delivery date
        - 64: Nominal delivery date
        - 137: Invoice date
        - 171: Agreement date
        - 198: Validity start date
        - 199: Validity end date
    """
    # Validate required fields
    validate_required_fields(dtm_data, ['type', 'date'])
    
    # Validate date format
    date_format = dtm_data.get('format', '102')
    date_value = dtm_data['date']
    
    # Common date formats mapping
    date_formats = {
        '101': '%y%m%d',       # YYMMDD
        '102': '%Y%m%d',       # CCYYMMDD
        '201': '%y%m%d%H%M',   # YYMMDDHHMM
        '203': '%Y%m%d%H%M',   # CCYYMMDDHHMM
        '204': '%Y%m%d%H%M%S', # CCYYMMDDHHMMSS
        '301': '%y%m',         # YYMM
        '303': '%y%W',         # YYWW (year, week)
        '306': '%Y%m',         # CCYYMM
        '319': '%Y-%m-%d',     # CCYY-MM-DD
        '325': '%H%M',         # HHMM
        '327': '%H%M%S'        # HHMMSS
    }
    
    # Validate date format
    if date_format in date_formats:
        try:
            datetime.strptime(date_value, date_formats[date_format])
        except ValueError as e:
            raise ValueError(f"Invalid date format for format code {date_format}. {str(e)}")
    
    # Create DTM element
    dtm = ET.SubElement(parent, "DTM")
    
    # 1. Date type (required)
    date_type = ET.SubElement(dtm, "DateTimeTypeCode")
    date_type.text = str(dtm_data['type'])
    
    # 2. Date (required)
    date_elem = ET.SubElement(dtm, "DateTime")
    date_elem.text = date_value
    
    # 3. Date format (required)
    format_elem = ET.SubElement(dtm, "DateTimeFormatCode")
    format_elem.text = date_format
    
    # 4. Time zone (optional)
    if 'time_zone' in dtm_data:
        tz_elem = ET.SubElement(dtm, "TimeZone")
        tz_elem.text = str(dtm_data['time_zone'])
    
    # 5. Period (optional, for date ranges)
    if 'period' in dtm_data:
        period_elem = ET.SubElement(dtm, "Period")
        period_elem.text = str(dtm_data['period'])
    
    # 6. Description (optional)
    if 'description' in dtm_data:
        desc_elem = ET.SubElement(dtm, "Description")
        desc_elem.text = str(dtm_data['description'])
    
    return dtm

class HeaderSection:
    """
    A class to handle the InvoiceHeader section of a TEIF document.
    
    This class provides methods to create and manage the InvoiceHeader element
    and its child elements according to the TEIF 1.8.8 standard.
    """
    
    def __init__(self, 
                 sender_identifier: str,
                 receiver_identifier: Optional[str] = None,
                 receiver_identifier_type: str = 'I-01',
                 test_indicator: str = DEFAULT_TEST_INDICATOR,
                 language: str = DEFAULT_LANGUAGE,
                 currency: str = DEFAULT_CURRENCY):
        """
        Initialize a new HeaderSection instance.
        
        Args:
            sender_identifier: Sender's tax ID (13 characters)
            receiver_identifier: Receiver's ID (CIN, carte de séjour, or tax ID)
            receiver_identifier_type: Type of receiver ID (default: 'I-01' for tax ID)
            test_indicator: Indicates if this is a test document ('0' for production, '1' for test)
            language: Document language code (default: 'fr' for French)
            currency: Document currency code (default: 'TND' for Tunisian Dinar)
        """
        self.sender_identifier = sender_identifier
        self.receiver_identifier = receiver_identifier
        self.receiver_identifier_type = receiver_identifier_type
        self.test_indicator = test_indicator
        self.language = language
        self.currency = currency
        self.dates = []
        self.document_type = None
        self.document_number = None
    
    def add_date(self, date_text: str, function_code: str, date_format: str):
        """
        Add a date to the header.
        
        Args:
            date_text: The date value in the specified format
            function_code: Code specifying the date's function (e.g., 'I-31' for invoice date)
            date_format: Format of the date (e.g., 'ddMMyy', 'yyyyMMdd')
        """
        self.dates.append({
            'date_text': date_text,
            'function_code': function_code,
            'format': date_format
        })
    
    def set_document_info(self, document_number: str, document_type: str):
        """
        Set document information.
        
        Args:
            document_number: The document number (invoice number, etc.)
            document_type: Document type code (e.g., 'I-11' for invoice)
        """
        self.document_number = document_number
        self.document_type = document_type
    
    def to_xml(self, parent: ET.Element = None) -> ET.Element:
        """
        Generate the XML representation of the header section.
        
        Args:
            parent: The parent XML element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            invoice_header = create_teif_root()
        else:
            invoice_header = parent
        
        # Add message identification
        msg_id = ET.SubElement(invoice_header, 'MessageIdentification')
        ET.SubElement(msg_id, 'MessageIdentifier').text = str(uuid.uuid4())
        ET.SubElement(msg_id, 'MessageType').text = 'INVOIC'
        ET.SubElement(msg_id, 'MessageVersion').text = TEIF_VERSION
        
        # Add sender identification
        sender = ET.SubElement(invoice_header, 'SenderIdentification')
        ET.SubElement(sender, 'TaxIdentifier').text = self.sender_identifier
        
        # Add receiver identification if provided
        if self.receiver_identifier:
            receiver = ET.SubElement(invoice_header, 'ReceiverIdentification')
            ET.SubElement(receiver, 'IdentifierTypeCode').text = self.receiver_identifier_type
            ET.SubElement(receiver, 'Identifier').text = self.receiver_identifier
        
        # Add document information if available
        if self.document_number and self.document_type:
            doc = ET.SubElement(invoice_header, 'DocumentIdentification')
            ET.SubElement(doc, 'DocumentNumber').text = self.document_number
            ET.SubElement(doc, 'DocumentType').text = self.document_type
        
        # Add dates
        for date_info in self.dates:
            add_date_section(invoice_header, date_info['date_text'], date_info['function_code'], date_info['format'])
        
        # Add test indicator
        ET.SubElement(invoice_header, 'TestIndicator').text = self.test_indicator
        
        # Add language and currency
        ET.SubElement(invoice_header, 'LanguageCode').text = self.language
        ET.SubElement(invoice_header, 'CurrencyCode').text = self.currency
        
        return invoice_header

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present in the data dictionary.
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of required field names
        
    Raises:
        ValueError: If any required fields are missing
    """
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

def _validate_and_format_date(date_str: str, default_format: str = '%Y-%m-%d') -> str:
    """
    Validate and format date string to YYYY-MM-DD format.
    
    Args:
        date_str: Input date string
        default_format: Expected date format (default: YYYY-MM-DD)
        
    Returns:
        str: Formatted date string in YYYY-MM-DD format
        
    Raises:
        ValueError: If date format is invalid
    """
    if not date_str:
        raise ValueError("Date string cannot be empty")
    
    try:
        # Try parsing with default format
        if 'Z' in date_str.upper() or '+' in date_str or '-' in date_str[-6:]:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str)
            # Assume UTC if no timezone specified
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        
        # Return in ISO 8601 format with timezone
        return dt.isoformat()
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected ISO 8601 format.") from e
