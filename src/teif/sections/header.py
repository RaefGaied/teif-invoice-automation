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

# Document type codes as per TEIF 1.8.8 (Referential-I1)
DOCUMENT_TYPES = {
    # Commercial Documents
    "INVOICE": "380",
    "CREDIT_NOTE": "381",
    "DEBIT_NOTE": "383",
    "SELF_BILLING": "389",
    "PRO_FORMA": "325",
    "COMMERCIAL_INVOICE": "325",
    "COMMERCIAL_CREDIT_NOTE": "381",
    "COMMERCIAL_DEBIT_NOTE": "383",
    
    # Transport Documents
    "TRANSPORT_DOCUMENT": "703",
    "BILL_OF_LADING": "730",
    "AIR_WAYBILL": "721",
    "ROAD_TRANSPORT_DOCUMENT": "740",
    
    # Other Documents
    "ORDER": "220",
    "ORDER_RESPONSE": "231",
    "CONTRACT": "9",
    "AGREEMENT": "AG",
    "QUOTATION": "QT",
    "DELIVERY_NOTE": "351"
}

# Document reference types (Referential-I1)
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

# DTM Function Codes (Referential-I3)
DTM_FUNCTION_CODES = {
    # Document Date/Times
    "3": "Requested Delivery Date",
    "35": "Payment Due Date",
    "50": "Shipping Date",
    "63": "Estimated Delivery Date",
    "64": "Nominal Delivery Date",
    "137": "Invoice Date",
    "171": "Agreement Date",
    "198": "Validity Start Date",
    "199": "Validity End Date",
    
    # Additional Common Codes
    "2": "Delivery Requested",
    "4": "Purchase Order Date",
    "5": "Sales Order Date",
    "7": "Effective Date",
    "9": "Processing Date",
    "10": "Shipment Date",
    "11": "Despatch Date",
    "12": "Terms Discount Due Date",
    "13": "Settlement Date"
}

# Valid DTM formats
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

def validate_tax_identifier(tax_id: str) -> None:
    """
    Validate Tunisian tax identification number format.
    
    The tax ID should follow the format: 7 digits + 1 letter (A-Z, excluding I, O, U) + 
    1 letter (A, P, B, F, or N) + 1 letter (M, P, C, N, or E) + 3 digits.
    
    Args:
        tax_id: The tax identification number to validate
        
    Raises:
        ValueError: If the tax ID format is invalid
    """
    if not tax_id or len(tax_id) != 13:
        raise ValueError("Tax ID must be exactly 13 characters long")
    
    # Validate components
    numeric_part = tax_id[:7]
    if not numeric_part.isdigit():
        raise ValueError("First 7 characters of tax ID must be digits")
        
    control_char = tax_id[7].upper()
    if control_char in 'IOU' or not control_char.isalpha():
        raise ValueError("8th character must be a letter (A-Z except I, O, U)")
        
    vat_code = tax_id[8].upper()
    if vat_code not in ['A', 'P', 'B', 'F', 'N']:
        raise ValueError("9th character must be one of: A, P, B, F, N")
        
    category_code = tax_id[9].upper()
    if category_code not in ['M', 'P', 'C', 'N', 'E']:
        raise ValueError("10th character must be one of: M, P, C, N, E")
        
    establishment = tax_id[10:]
    if not establishment.isdigit():
        raise ValueError("Last 3 characters must be digits")

def create_header_element(data: Dict[str, Any]) -> ET.Element:
    """
    Create the root InvoiceHeader element as per TEIF 1.8.8 standard.
    
    This mandatory section includes:
    - Message identification
    - Sender identification (tax ID, required)
    - Receiver identification (tax ID or other ID, optional)
    
    Args:
        data: Dictionary containing header data with keys:
            - sender_identifier (str, required): Sender's tax ID (13 characters)
            - receiver_identifier (str, optional): Receiver's ID (CIN, carte de séjour, or tax ID)
            - receiver_identifier_type (str, optional): Type of receiver ID (default: 'I-01' for tax ID)
            
    Returns:
        ET.Element: The InvoiceHeader XML element
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    validate_required_fields(data, ['sender_identifier'])
    
    # Create root element
    header = ET.Element("InvoiceHeader")
    
    # 1. Message Sender Identifier (Mandatory, tax ID)
    sender_id = str(data['sender_identifier']).strip()
    validate_tax_identifier(sender_id)
    sender_elem = ET.SubElement(header, "MessageSenderIdentifier")
    sender_elem.set("type", "I-01")  # I-01 = Matricule Fiscal
    sender_elem.text = sender_id
    
    # 2. Message Receiver Identifier (Optional)
    if 'receiver_identifier' in data and data['receiver_identifier']:
        receiver_id = str(data['receiver_identifier']).strip()
        if len(receiver_id) > 35:
            raise ValueError("Receiver ID must not exceed 35 characters")
            
        receiver_elem = ET.SubElement(header, "MessageRecieverIdentifier")
        # Default to tax ID type if not specified
        receiver_type = data.get('receiver_identifier_type', 'I-01')
        receiver_elem.set("type", receiver_type)
        receiver_elem.text = receiver_id
        
    return header

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
    
    if code not in DTM_FUNCTION_CODES and not code.isdigit():
        raise ValueError(
            f"Invalid DTM function code: {code}. "
            f"Must be one of {list(DTM_FUNCTION_CODES.keys())} or a valid numeric code"
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

def create_dtm_element(parent: ET.Element, dtm_data: Dict[str, Any]) -> ET.Element:
    """
    Create DTM (Date/Time/Period) section as per TEIF 1.8.8 standard.
    
    This section can be used to specify various dates related to the document.
    
    Args:
        parent: Parent XML element
        dtm_data: Dictionary containing DTM data with keys:
            - date_text (str, required): The date value in the specified format
            - function_code (str, required): Code specifying the date's function (Referential-I3)
            - format (str, required): Format of the date (e.g., 'DDMMYY', 'YYYYMMDD')
            - 
    Returns:
        ET.Element: The DTM XML element
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    validate_required_fields(dtm_data, ['date_text', 'function_code', 'format'])
    
    # Validate function code
    _validate_dtm_function_code(dtm_data['function_code'])
    
    # Validate format
    _validate_dtm_format(dtm_data['format'])
    
    # Create DTM element
    dtm = ET.SubElement(parent, "DTM")
    
    # Create DateText element with attributes
    date_text_elem = ET.SubElement(dtm, "DateText")
    date_text_elem.text = str(dtm_data['date_text']).strip()
    date_text_elem.set("functionCode", str(dtm_data['function_code']).strip())
    date_text_elem.set("format", str(dtm_data['format']).strip().upper())
    
    return dtm

def create_bgm_element(parent: ET.Element, bgm_data: Dict[str, Any]) -> ET.Element:
    """
    Create BGM (Document Identification) section as per TEIF 1.8.8 standard.
    
    This mandatory section includes:
    - Document identifier (invoice number, max 70 chars)
    - Document type with code (from Référentiel-I1)
    
    Args:
        parent: Parent XML element
        bgm_data: Dictionary containing BGM data with keys:
            - document_number (str, required): Document number (max 70 chars)
            - document_type (str, required): Document type code from Référentiel-I1
            - document_type_label (str, optional): Human-readable document type
            
    Returns:
        ET.Element: The BGM XML element
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    validate_required_fields(bgm_data, ['document_number', 'document_type'])
    
    # Create BGM element
    bgm = ET.SubElement(parent, "Bgm")
    
    # 1. Document Identifier (Mandatory, max 70 chars)
    doc_id = str(bgm_data['document_number']).strip()
    if len(doc_id) > 70:
        raise ValueError(f"Document number cannot exceed 70 characters: {doc_id}")
    ET.SubElement(bgm, "DocumentIdentifier").text = doc_id
    
    # 2. Document Type (Mandatory with code from Référentiel-I1)
    doc_type = _validate_document_type(bgm_data['document_type'])
    doc_type_elem = ET.SubElement(bgm, "DocumentType")
    doc_type_elem.set("code", doc_type)  # Code from Référentiel-I1
    
    # Add document type label if provided, otherwise use the code
    doc_type_elem.text = bgm_data.get('document_type_label', doc_type)
    
    return bgm

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
        dt = datetime.strptime(date_str, default_format)
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        # Try parsing with common formats
        for fmt in ('%Y%m%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    # If we get here, all parsing attempts failed
    raise ValueError(
        f"Invalid date format: {date_str}. "
        f"Expected format: {default_format} or other common date formats"
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
            header = ET.Element('InvoiceHeader')
        else:
            header = ET.SubElement(parent, 'InvoiceHeader')
        
        # Add message identification
        msg_id = ET.SubElement(header, 'MessageIdentification')
        ET.SubElement(msg_id, 'MessageIdentifier').text = str(uuid.uuid4())
        ET.SubElement(msg_id, 'MessageType').text = 'INVOIC'
        ET.SubElement(msg_id, 'MessageVersion').text = TEIF_VERSION
        
        # Add sender identification
        sender = ET.SubElement(header, 'SenderIdentification')
        ET.SubElement(sender, 'TaxIdentifier').text = self.sender_identifier
        
        # Add receiver identification if provided
        if self.receiver_identifier:
            receiver = ET.SubElement(header, 'ReceiverIdentification')
            ET.SubElement(receiver, 'IdentifierTypeCode').text = self.receiver_identifier_type
            ET.SubElement(receiver, 'Identifier').text = self.receiver_identifier
        
        # Add document information if available
        if self.document_number and self.document_type:
            doc = ET.SubElement(header, 'DocumentIdentification')
            ET.SubElement(doc, 'DocumentNumber').text = self.document_number
            ET.SubElement(doc, 'DocumentType').text = self.document_type
        
        # Add dates
        for date_info in self.dates:
            create_dtm_element(header, date_info)
        
        # Add test indicator
        ET.SubElement(header, 'TestIndicator').text = self.test_indicator
        
        # Add language and currency
        ET.SubElement(header, 'LanguageCode').text = self.language
        ET.SubElement(header, 'CurrencyCode').text = self.currency
        
        return header
