"""
Module for handling TEIF 1.8.8 invoice lines with required and optional elements.
"""
from typing import Dict, Any, List, Optional, Union
import xml.etree.ElementTree as ET


class ItemDescription:
    """Represents an item description with language support."""
    
    def __init__(self, text: str, language_code: str = 'fr'):
        """
        Initialize an item description.
        
        Args:
            text: The description text
            language_code: ISO 639-1 language code (default: 'fr')
        """
        self.text = text
        self.language_code = language_code


class Quantity:
    """Represents a quantity with unit of measure."""
    
    def __init__(self, value: float, unit: str):
        """
        Initialize a quantity.
        
        Args:
            value: The numeric value of the quantity
            unit: The unit of measure (e.g., 'PCE' for pieces)
        """
        self.value = value
        self.unit = unit


class LinSection:
    """
    Represents the LinSection of a TEIF invoice, containing all line items.
    """
    
    def __init__(self):
        """Initialize an empty LinSection."""
        self.lines: List[LinItem] = []
    
    def add_line(self, line: 'LinItem') -> None:
        """
        Add a line item to the section.
        
        Args:
            line: The LinItem to add to the section
        """
        self.lines.append(line)
    
    def to_xml(self, parent: ET.Element) -> None:
        """
        Convert the LinSection to XML and append to the parent element.
        
        Args:
            parent: The parent XML element
        """
        if not self.lines:
            return
            
        lin_section = ET.SubElement(parent, 'LinSection')
        
        for line in self.lines:
            line.to_xml(lin_section)


class LinItem:
    """
    Represents a single line item in an invoice.
    """
    
    def __init__(self, line_number: int):
        """
        Initialize a new line item.
        
        Args:
            line_number: The line number in the invoice (1-based index)
        """
        self.line_number = line_number
        self.item_identifier: Optional[str] = None
        self.item_code: Optional[str] = None
        self.description: Optional[str] = None
        self.quantity: Dict[str, Any] = {}
        self.unit_price: Optional[float] = None
        self.currency: str = 'TND'
        self.taxes: List[Dict[str, Any]] = []
        self.additional_info: List[Dict[str, str]] = []
        self.sub_lines: List['LinItem'] = []
        self.amounts: List[Dict[str, Any]] = []
        self.language: str = 'fr'  # Default language
    
    def set_item_info(self, item_identifier: str, item_code: str, description: str, lang: str = 'fr') -> None:
        """
        Set basic item information.
        
        Args:
            item_identifier: Unique identifier for the item
            item_code: Item code
            description: Item description
            lang: Language code (default: 'fr')
        """
        self.item_identifier = item_identifier
        self.item_code = item_code
        self.description = description
        self.language = lang
    
    def set_quantity(self, value: float, unit: str) -> None:
        """
        Set the quantity and unit for the line item.
        
        Args:
            value: The quantity value
            unit: The unit of measure (e.g., 'PCE' for pieces)
        """
        self.quantity = {
            'value': value,
            'unit': unit
        }
    
    def add_tax(self, type_name: str, code: str, category: str, details: List[Dict[str, Any]]) -> None:
        """
        Add tax information to the line item.
        
        Args:
            type_name: Type of tax (e.g., 'TVA')
            code: Tax code (e.g., 'I-1602')
            category: Tax category (e.g., 'S' for standard rate)
            details: List of tax details (rate, amount, currency)
        """
        self.taxes.append({
            'type_name': type_name,
            'code': code,
            'category': category,
            'details': details
        })
    
    def add_amount(self, amount: float, currency: str, type_code: str) -> None:
        """
        Add a monetary amount to the line item.
        
        Args:
            amount: The amount
            currency: Currency code
            type_code: Type code for the amount
        """
        self.amounts.append({
            'amount': amount,
            'currency': currency,
            'type_code': type_code
        })
    
    def add_additional_info(self, code: str, description: str, lang: str = 'fr') -> None:
        """
        Add additional information to the line item.
        
        Args:
            code: Info code
            description: Info description
            lang: Language code (default: 'fr')
        """
        self.additional_info.append({
            'code': code,
            'description': description,
            'lang': lang
        })
    
    def add_sub_line(self, sub_line: 'LinItem') -> None:
        """
        Add a sub-line to this line item.
        
        Args:
            sub_line: The sub-line to add
        """
        self.sub_lines.append(sub_line)
    
    def to_xml(self, parent: ET.Element) -> None:
        """
        Convert the line item to XML and append to the parent element.
        
        Args:
            parent: The parent XML element
        """
        # Create Lin element with lineNumber attribute
        lin = ET.SubElement(parent, 'Lin', attrib={'lineNumber': str(self.line_number)})
        
        # Add item identifier if available
        if self.item_identifier:
            item_id = ET.SubElement(lin, 'ItemIdentifier')
            item_id.text = self.item_identifier
        
        # Add item code and description if available
        if self.item_code or self.description:
            # Create LinImd with lang attribute if language is set
            lin_imd_attrs = {}
            if hasattr(self, 'language'):
                lin_imd_attrs['lang'] = self.language
                
            lin_imd = ET.SubElement(lin, 'LinImd', attrib=lin_imd_attrs)
            
            # Add item code if available
            if self.item_code:
                item_code = ET.SubElement(lin_imd, 'ItemCode')
                item_code.text = self.item_code
            
            # Add item description if available
            if self.description:
                item_desc = ET.SubElement(lin_imd, 'ItemDescription')
                item_desc.text = self.description
        
        # Add quantity if available
        if self.quantity and 'value' in self.quantity and 'unit' in self.quantity:
            lin_qty = ET.SubElement(lin, 'LinQty')
            qty = ET.SubElement(lin_qty, 'Quantity', attrib={'measurementUnit': self.quantity['unit']})
            qty.text = f"{float(self.quantity['value']):.1f}"
        
        # Add amounts if any
        if self.amounts:
            moa_details = ET.SubElement(lin, 'MoaDetails')
            for amount in self.amounts:
                self._add_amount_element(moa_details, amount)
        
        # Add taxes if any
        for tax in self.taxes:
            self._add_tax_element(lin, tax)
        
        # Add additional info if any
        for info in self.additional_info:
            self._add_additional_info(lin, info)
        
        # Add sub-lines if any
        for sub_line in self.sub_lines:
            sub_line.to_xml(lin)
    
    def _add_tax_element(self, parent: ET.Element, tax_data: Dict[str, Any]) -> None:
        """
        Add tax information to the parent XML element.
        
        Args:
            parent: The parent XML element
            tax_data: Dictionary containing tax information
        """
        tax = ET.SubElement(parent, 'LinTax')
        
        # Add tax type with code attribute
        tax_type = ET.SubElement(tax, 'TaxTypeName', attrib={'code': tax_data.get('code', 'I-1602')})
        tax_type.text = tax_data.get('type_name', 'TVA')
        
        # Add tax category
        tax_cat = ET.SubElement(tax, 'TaxCategory')
        tax_cat.text = tax_data.get('category', 'S')
        
        # Add tax details with TaxDetail/TaxRate structure
        tax_details = ET.SubElement(tax, 'TaxDetails')
        
        # Get the first tax detail for rate
        details = tax_data.get('details', [])
        if details and len(details) > 0:
            tax_detail = ET.SubElement(tax_details, 'TaxDetail')
            tax_rate = ET.SubElement(tax_detail, 'TaxRate')
            tax_rate.text = str(int(details[0].get('rate', 0)))  # Remove decimal for rate

    def _add_amount_element(self, parent: ET.Element, amount_data: Dict[str, Any]) -> None:
        """
        Add amount information to the parent XML element.
        
        Args:
            parent: The parent XML element
            amount_data: Dictionary containing amount information with keys:
                - amount: The amount value
                - type_code: The amount type code (e.g., 'I-183')
                - currency: The currency code (default: 'TND')
        """
        moa = ET.SubElement(parent, 'Moa', {
            'amountTypeCode': amount_data.get('type_code', ''),
            'currencyCodeList': 'ISO_4217'
        })
        
        # Add amount with currency identifier
        amount = ET.SubElement(moa, 'Amount', {
            'currencyIdentifier': amount_data.get('currency', 'TND')
        })
        amount.text = f"{amount_data.get('amount', 0):.3f}"
    
    def _add_additional_info(self, parent: ET.Element, info_data: Dict[str, str]) -> None:
        """
        Add additional information to the parent XML element.
        
        Args:
            parent: The parent XML element
            info_data: Dictionary containing additional information
        """
        # Create LinApi element
        lin_api = ET.SubElement(parent, 'LinApi')
        
        # Create ApiDetails element
        api_details = ET.SubElement(lin_api, 'ApiDetails')
        
        # Create Api element with language attribute
        api = ET.SubElement(api_details, 'Api', attrib={'lang': info_data.get('lang', 'fr')})
        
        # Add API code
        api_code = ET.SubElement(api, 'ApiCode')
        api_code.text = info_data.get('code', '')
        
        # Add API description
        api_desc = ET.SubElement(api, 'ApiDescription')
        api_desc.text = info_data.get('description', '')


def add_invoice_lines(parent: ET.Element, lines: List[Dict[str, Any]], currency: str = 'TND') -> None:
    """
    Add invoice lines to the parent XML element.
    
    Args:
        parent: The parent XML element
        lines: List of dictionaries containing line data
        currency: Currency code (default: 'TND')
    """
    lin_section = LinSection()
    
    for line_data in lines:
        line = LinItem(line_data['line_number'])
        
        # Add item identifier if available
        if 'item_identifier' in line_data:
            line.item_identifier = line_data['item_identifier']
        
        # Add item code if available
        if 'item_code' in line_data:
            line.item_code = line_data['item_code']
        
        # Add description if available
        if 'description' in line_data:
            line.description = line_data['description']
        
        # Add quantity if available
        if 'quantity' in line_data:
            line.quantity = {
                'value': line_data['quantity'],
                'unit': line_data.get('unit', 'C62')
            }
        
        # Add unit price if available
        if 'unit_price' in line_data:
            line.unit_price = line_data['unit_price']
        
        # Add taxes if any
        if 'taxes' in line_data:
            for tax in line_data['taxes']:
                line.add_tax(tax['type_name'], tax['code'], tax['category'], tax['details'])
        
        # Add additional info if any
        if 'additional_info' in line_data:
            for info in line_data['additional_info']:
                line.add_additional_info(info['code'], info['description'], info.get('lang', 'fr'))
        
        lin_section.add_line(line)
    
    lin_section.to_xml(parent)


def _add_invoice_line(parent: ET.Element, line_data: Dict[str, Any], currency: str) -> None:
    """
    Add a single invoice line to the parent XML element.
    
    Args:
        parent: The parent XML element
        line_data: Dictionary containing line data
        currency: Currency code
    """
    line = LinItem(line_data['line_number'])
    
    # Add item identifier if available
    if 'item_identifier' in line_data:
        line.item_identifier = line_data['item_identifier']
    
    # Add item code if available
    if 'item_code' in line_data:
        line.item_code = line_data['item_code']
    
    # Add description if available
    if 'description' in line_data:
        line.description = line_data['description']
    
    # Add quantity if available
    if 'quantity' in line_data:
        line.quantity = {
            'value': line_data['quantity'],
            'unit': line_data.get('unit', 'C62')
        }
    
    # Add unit price if available
    if 'unit_price' in line_data:
        line.unit_price = line_data['unit_price']
    
    # Add taxes if any
    if 'taxes' in line_data:
        for tax in line_data['taxes']:
            line.add_tax(tax['type_name'], tax['code'], tax['category'], tax['details'])
    
    # Add additional info if any
    if 'additional_info' in line_data:
        for info in line_data['additional_info']:
            line.add_additional_info(info['code'], info['description'], info.get('lang', 'fr'))
    
    line.to_xml(parent)


def add_invoice_lines_from_dict(parent: ET.Element, lines_dict: Dict[str, Any], currency: str = 'TND') -> None:
    """
    Add invoice lines from a dictionary to the parent XML element.
    
    Args:
        parent: The parent XML element
        lines_dict: Dictionary containing line data
        currency: Currency code (default: 'TND')
    """
    lines = []
    
    for line_number, line_data in lines_dict.items():
        line = {
            'line_number': line_number,
            'item_identifier': line_data.get('item_identifier'),
            'item_code': line_data.get('item_code'),
            'description': line_data.get('description'),
            'quantity': line_data.get('quantity'),
            'unit': line_data.get('unit'),
            'unit_price': line_data.get('unit_price'),
            'taxes': line_data.get('taxes', []),
            'additional_info': line_data.get('additional_info', [])
        }
        
        lines.append(line)
    
    add_invoice_lines(parent, lines, currency)
