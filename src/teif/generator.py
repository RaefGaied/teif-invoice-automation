import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
import re
from xml.dom import minidom

# Import section modules using relative imports
from .sections.header import (
    HeaderSection, 
    create_header_element, 
    create_bgm_element, 
    create_dtm_element,
    create_teif_root
)
from .sections.partner import PartnerSection, add_seller_party, add_buyer_party, add_delivery_party
from .sections.amounts import create_amount_element, create_tax_amount, create_adjustment, create_invoice_totals
from .sections.lines import LinSection, LinItem, add_invoice_lines
from .sections.signature import SignatureSection, create_signature, add_signature
from .sections.payment import add_payment_terms, add_financial_institution

class TEIFGenerator:
    """Générateur de documents XML conformes à la norme TEIF 1.8.8."""
    
    def __init__(self, logging_level=logging.INFO):
        """Initialise le générateur TEIF avec les paramètres par défaut."""
        self.ns = {
            '': 'http://www.tn.gov/teif',
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        self.schema_location = "http://www.tn.gov/teif TEIF.xsd"
        self.version = "1.8.8"
        self.controlling_agency = "TTN"

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)
        
        # Create console handler and set level
        ch = logging.StreamHandler()
        ch.setLevel(logging_level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(ch)

    def generate_teif_xml(self, data: Dict[str, Any]) -> str:
        """
        Generate TEIF XML from the provided data.
        
        Args:
            data: Dictionary containing invoice data
            
        Returns:
            str: Generated XML as a string with proper formatting
        """
        try:
            # Create the root element
            root = create_teif_root(version=data.get('version', '1.8.8'))
            
            # Add header and body sections
            header = ET.SubElement(root, "InvoiceHeader")
            self._add_header(header, data)
            
            body = ET.SubElement(root, "InvoiceBody")
            
            # Add BGM section if document info is available
            #if 'document' in data or any(k in data for k in ['document_number', 'document_type']):
            if 'bgm' in data:
                self._add_bgm_section(body, data['bgm'])
                
            # Add dates if available
            if 'dates' in data and isinstance(data['dates'], list):
                self._add_dates(body, data['dates'])
            
            # Add partners if available (check both 'partners' key and root level)
            if any(k in data for k in ['seller', 'buyer', 'delivery']):
                # Create a partners dict from root level data
                partners_data = {
                    'seller': data.get('seller'),
                    'buyer': data.get('buyer'),
                    'delivery': data.get('delivery')
                }
                self._add_partners(body, partners_data)
            elif 'partners' in data and data['partners']:
                self._add_partners(body, data['partners'])
            
            # Add payment terms if available
            if 'payment_terms' in data and data['payment_terms']:
                self._add_payment_terms(body, data['payment_terms'])
            
            # Add payment means if available
            if 'payment_means' in data and data['payment_means']:
                self._add_payment_means(body, data['payment_means'])
            
            # Add line items if available
            if 'lines' in data and data['lines']:
                self._add_line_items(body, data)
            
            # Add invoice totals if available
            if 'totals' in data:
                self._add_invoice_totals(body, data['totals'])
            
            # Add signature if available
            if 'signature' in data:
                self._add_signature(root, data['signature'])
            
            # Convert to string with proper XML declaration and formatting
            xml_str = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
            
            # Pretty print the XML
            parsed = minidom.parseString(xml_str)
            return parsed.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error generating TEIF XML: {str(e)}")
            raise

    def _add_header(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """
        Add header section to the XML using TEIF 1.8.8 specification.
        
        Args:
            parent: Parent XML element (should be the root TEIF element)
            data: Dictionary containing header data
        """
        try:
            # Extract header data with fallback to root level for backward compatibility
            header_data = data.get('header', {})
            
            # Create InvoiceHeader element
            invoice_header = parent
            
            # Add MessageSenderIdentifier (required)
            sender_id = header_data.get('sender_identifier', data.get('sender_identifier', ''))
            if sender_id:
                sender_elem = ET.SubElement(invoice_header, 'MessageSenderIdentifier', type='I-01')
                sender_elem.text = str(sender_id)
            
            # Add MessageRecipientIdentifier (if available)
            receiver_id = header_data.get('receiver_identifier', data.get('receiver_identifier'))
            if receiver_id:
                receiver_elem = ET.SubElement(invoice_header, 'MessageRecipientIdentifier', 
                                           type=header_data.get('receiver_identifier_type', 'I-01'))
                receiver_elem.text = str(receiver_id)
            
            # Add CreationDateTime (current timestamp if not provided)
            creation_time = header_data.get('creation_datetime', datetime.utcnow().strftime('%Y%m%d%H%M%S'))
            ET.SubElement(invoice_header, 'CreationDateTime').text = creation_time
            
            # Add other optional header fields if provided
            if 'message_identifier' in header_data:
                ET.SubElement(invoice_header, 'MessageIdentifier').text = str(header_data['message_identifier'])
                
            if 'document_currency_code' in header_data:
                ET.SubElement(invoice_header, 'DocumentCurrencyCode').text = str(header_data['document_currency_code'])
            
        except Exception as e:
            self.logger.error(f"Error adding header section: {str(e)}")
            raise

    def _add_bgm_section(self, parent: ET.Element, bgm_data: Dict[str, Any]) -> None:
        """Add BGM (Beginning of Message) section."""
        try:
            create_bgm_element(parent, bgm_data)
        except Exception as e:
            self.logger.error(f"Error adding BGM section: {str(e)}")
            raise

    def _add_dates(self, parent: ET.Element, dates_data: List[Dict[str, Any]]) -> None:
        """Add date elements to the document under a single Dtm element."""
        try:
            if not dates_data:
                return
            
            # Create or find the Dtm element
            dtm = parent.find('Dtm')
            if dtm is None:
                dtm = ET.SubElement(parent, 'Dtm')
            
            # Add all dates to the single Dtm element
            for date_item in dates_data:
                if all(k in date_item for k in ['date_text', 'function_code', 'format']):
                    ET.SubElement(dtm, 'DateText',
                                format=date_item['format'],
                                functionCode=date_item['function_code']).text = date_item['date_text']
                            
        except Exception as e:
            self.logger.error(f"Error adding dates: {str(e)}")
            raise

    def _add_partners(self, parent: ET.Element, partners_data: Dict[str, Any]) -> None:
        """Add partner sections (seller, buyer, delivery)."""
        if not partners_data:
            self.logger.warning("No partners data provided")
            return
            
        try:
            # Add seller if exists and is not None
            if partners_data.get('seller'):
                add_seller_party(parent, partners_data['seller'])
            
            # Add buyer if exists and is not None
            if partners_data.get('buyer'):
                add_buyer_party(parent, partners_data['buyer'])
            
            # Add delivery party if exists and is not None
            if partners_data.get('delivery'):
                add_delivery_party(parent, partners_data['delivery'])
                
        except Exception as e:
            self.logger.error(f"Error adding partners: {str(e)}")
            raise

    def _add_payment_terms(self, parent: ET.Element, payment_terms_data: Dict[str, Any]) -> None:
        """
        Add payment terms section.
        
        Args:
            parent: Parent XML element
            payment_terms_data: Dictionary containing payment terms data
                - description: Payment terms description (required)
                - code: Payment type code (optional, e.g., 'I-10')
                - due_date: Due date (optional)
                - discount_percent: Discount percentage (optional)
                - discount_due_date: Discount due date (optional)
        """
        try:
            from src.teif.sections.payment import add_payment_terms
            add_payment_terms(parent, payment_terms_data)
        except Exception as e:
            self.logger.error(f"Error adding payment terms: {str(e)}")
            raise

    def _add_payment_means(self, parent: ET.Element, payment_means_data: Dict[str, Any]) -> None:
        """
        Add payment means section.
        
        Args:
            parent: Parent XML element
            payment_means_data: Dictionary containing payment means data
                - payment_means_code: Code du moyen de paiement (ex: 'I-30' pour virement)
                - payment_id: Identifiant du paiement (ex: numéro de virement)
                - payee_financial_account: Dictionnaire contenant les informations du compte
                    - iban: Numéro IBAN du compte
                    - financial_institution: Nom de l'institution financière
        """
        try:
            from src.teif.sections.payment import add_financial_institution
            
            # Créer la section PytSection si elle n'existe pas
            pyt_section = parent.find('PytSection')
            if pyt_section is None:
                pyt_section = ET.SubElement(parent, 'PytSection')
                pyt_section_details = ET.SubElement(pyt_section, 'PytSectionDetails')
            else:
                pyt_section_details = pyt_section.find('PytSectionDetails')
                if pyt_section_details is None:
                    pyt_section_details = ET.SubElement(pyt_section, 'PytSectionDetails')
            
            # Ajouter les informations de paiement
            pyt = ET.SubElement(pyt_section_details, 'Pyt')
            
            # Ajouter le code du moyen de paiement
            if 'payment_means_code' in payment_means_data:
                payment_means_code = ET.SubElement(pyt, 'PaymentMeansCode')
                payment_means_code.text = str(payment_means_data['payment_means_code'])
            
            # Ajouter l'identifiant du paiement
            if 'payment_id' in payment_means_data:
                payment_id = ET.SubElement(pyt, 'PaymentID')
                payment_id.text = str(payment_means_data['payment_id'])
            
            # Ajouter les informations du compte bancaire si disponibles
            if 'payee_financial_account' in payment_means_data:
                fi_data = {
                    'function_code': 'I-141',  # Code pour le compte du bénéficiaire
                    'account': {
                        'number': payment_means_data['payee_financial_account'].get('iban', ''),
                        'holder': payment_means_data['payee_financial_account'].get('account_holder', '')
                    },
                    'institution': {
                        'name': payment_means_data['payee_financial_account'].get('financial_institution', '')
                    }
                }
                add_financial_institution(pyt, fi_data)
                
        except Exception as e:
            self.logger.error(f"Error adding payment means: {str(e)}")
            raise

    def _add_line_items(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """Add line items section."""
        try:
            if 'lines' not in data or not data['lines']:
                return
                
            # Get currency from data or use default
            currency = data.get('currency', 'TND')
            
            # Create line items section
            lin_section = LinSection()
            
            # Add each line item
            for line_data in data['lines']:
                line = LinItem(line_number=len(lin_section.lines) + 1)
                
                # Set basic item info
                if 'item_identifier' in line_data and 'description' in line_data:
                    line.set_item_info(
                        item_identifier=line_data['item_identifier'],
                        item_code=line_data.get('item_code', ''),
                        description=line_data['description'],
                        lang=line_data.get('language', 'fr')
                    )
                
                # Set quantity if available - handle both direct value and dictionary formats
                if 'quantity' in line_data:
                    if isinstance(line_data['quantity'], dict) and 'unit' in line_data['quantity']:
                        # Handle dictionary format: {'value': 1.0, 'unit': 'PCE'}
                        line.set_quantity(
                            value=float(line_data['quantity']['value']),
                            unit=line_data['quantity']['unit']
                        )
                    else:
                        # Handle direct value format
                        line.set_quantity(
                            value=float(line_data['quantity']),
                            unit=line_data.get('unit', 'PCE')  # Default unit if not provided
                        )
                
                # Set unit price if available
                if 'unit_price' in line_data:
                    line.add_amount(
                        amount=float(line_data['unit_price']),
                        currency=currency,
                        type_code='I-183'  # Unit price amount
                    )
                
                # Add taxes if available
                if 'taxes' in line_data and isinstance(line_data['taxes'], list):
                    for tax in line_data['taxes']:
                        # Handle both new and old tax formats
                        if 'details' in tax and isinstance(tax['details'], list):
                            # New format with details list
                            for detail in tax['details']:
                                line.add_tax(
                                    type_name=tax.get('type_name', ''),
                                    code=tax.get('code', ''),
                                    category=tax.get('category', ''),
                                    details=[{
                                        'rate': float(detail.get('rate', 0)),
                                        'amount': float(detail.get('amount', 0)),
                                        'currency': detail.get('currency', currency)
                                    }]
                                )
                        else:
                            # Old format with direct tax properties
                            line.add_tax(
                                type_name=tax.get('type_name', ''),
                                code=tax.get('code', ''),
                                category=tax.get('category', ''),
                                details=[{
                                    'rate': float(tax.get('rate', 0)),
                                    'amount': float(tax.get('amount', 0)),
                                    'currency': tax.get('currency', currency)
                                }]
                            )
                
                # Add line to section
                lin_section.add_line(line)
            
            # Add line items to XML
            lin_section.to_xml(parent)
            
        except Exception as e:
            self.logger.error(f"Error adding line items: {str(e)}")
            raise

    def _add_invoice_totals(self, parent: ET.Element, totals_data: Dict[str, Any]) -> None:
        """Add invoice totals section."""
        try:
            create_invoice_totals(parent, totals_data)
        except Exception as e:
            self.logger.error(f"Error adding invoice totals: {str(e)}")
            raise

    def _add_signature(self, parent: ET.Element, signature_data: Dict[str, Any]) -> None:
        """Add signature section."""
        try:
            create_signature_section(parent, signature_data)
        except Exception as e:
            self.logger.error(f"Error adding signature: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a sample invoice
    invoice_data = {
        "version": "1.8.8",
        "header": {
            "sender_identifier": "12345678",
            "receiver_identifier": "87654321"
        },
        "document": {
            "number": "INV-2023-001",
            "type": "I-11"
        },
        "dates": [
            {
                "date_text": datetime.now().strftime("%Y%m%d"),
                "function_code": "I-31",
                "format": "102"
            }
        ],
        "partners": {
            "seller": {
                "id": "12345678",
                "name": "Vendor Company",
                "address": {
                    "street": "123 Vendor St",
                    "city": "Tunis",
                    "postal_code": "1000",
                    "country": "TN"
                },
                "contacts": [
                    {
                        "name": "Sales Department",
                        "email": "sales@vendor.com",
                        "phone": "+216 70 000 000"
                    }
                ]
            },
            "buyer": {
                "id": "87654321",
                "name": "Customer Company",
                "address": {
                    "street": "456 Customer Ave",
                    "city": "Sousse",
                    "postal_code": "4000",
                    "country": "TN"
                }
            }
        },
        "lines": [
            {
                "item_identifier": "ITEM-001",
                "description": "Sample Product",
                "quantity": {
                    "value": 2,
                    "unit": "PCE"
                },
                "unit_price": 100.0,
                "taxes": [
                    {
                        "type_name": "VAT",
                        "category": "S",
                        "rate": 19.0,
                        "amount": 38.0
                    }
                ]
            }
        ],
        "totals": {
            "total_amount_without_tax": 200.0,
            "total_tax_amount": 38.0,
            "total_amount_with_tax": 238.0,
            "currency": "TND"
        }
    }
    
    # Generate the TEIF XML
    generator = TEIFGenerator()
    try:
        xml_output = generator.generate_teif_xml(invoice_data)
        print(xml_output)
    except Exception as e:
        print(f"Error generating TEIF XML: {str(e)}")