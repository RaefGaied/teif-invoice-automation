#!/usr/bin/env python3
"""
Example: Sign a TEIF invoice with XAdES signature

This script demonstrates how to:
1. Create a sample TEIF invoice
2. Add a XAdES-BES signature
3. Save the signed invoice to a file

Prerequisites:
- Python 3.8+
- Install requirements: pip install -r requirements.txt
- Generate test certificates using scripts/generate_test_cert.py
"""
import os
import sys
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.teif.sections.signature import SignatureSection
from src.teif.sections.header import HeaderSection as InvoiceSection
from src.teif.sections.partner import add_seller_party, add_buyer_party
from src.teif.sections.lines import LinSection, LinItem
from src.teif.sections.amounts import add_invoice_moa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_teif_invoice():
    """Create a sample TEIF invoice for testing purposes."""
    # Create a root element for the invoice with proper namespaces
    root = ET.Element("Invoice", {
        "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })
    
    # Create invoice with sample data
    invoice = InvoiceSection(
        sender_identifier="1234567890123",  # Example Tunisian tax ID (13 digits)
        receiver_identifier="9876543210123",  # Example receiver tax ID
        receiver_identifier_type="I-01"  # I-01 for Tunisian tax ID
    )
    invoice.invoice_number = "INV-2023-001"
    invoice.issue_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    invoice.due_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    invoice.currency = "TND"
    
    # Set document info
    invoice.set_document_info(
        document_number="INV-2023-001",
        document_type="I-11"  # I-11 for standard invoice
    )
    
    # Add dates
    invoice.add_date(
        date_text=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        function_code="I-31",  # I-31 for invoice date
        date_format="YYYY-MM-DD"
    )
    
    # Create seller data
    seller_data = {
        'identifier': '1234567890123',
        'identifier_type': 'I-01',
        'name': 'ACME Corporation',
        'vat_number': '12345678',
        'address': {
            'street': '123 Business St',
            'city': 'Tunis',
            'postal_code': '1000',
            'country_code': 'TN',
            'lang': 'fr'
        },
        'contacts': [{
            'name': 'John Doe',
            'function_code': 'I-91',  # I-91 for billing contact
            'communications': [
                {'type': 'TE', 'value': '+21612345678'},  # Telephone
                {'type': 'EM', 'value': 'billing@acme.tn'}  # Email
            ]
        }]
    }
    
    # Create buyer data
    buyer_data = {
        'identifier': '9876543210123',
        'identifier_type': 'I-01',
        'name': 'Test Customer',
        'address': {
            'street': '456 Customer Ave',
            'city': 'Sousse',
            'postal_code': '4000',
            'country_code': 'TN',
            'lang': 'fr'
        }
    }
    
    # Add seller and buyer parties directly to the root element
    add_seller_party(root, seller_data)
    add_buyer_party(root, buyer_data)
    
    # Add invoice sections to root
    invoice.to_xml(root)
    
    # Create and add line items
    lines = LinSection()
    line_item = LinItem(line_number=1)
    line_item.set_item_info(
        item_identifier="PROD-001",
        item_code="P001",
        description="Product A"
    )
    line_item.set_quantity(2, "PCE")
    line_item.unit_price = 100.0
    line_item.currency = "TND"
    line_item.add_tax(
        type_name="TVA",
        code="I-1602",
        category="S",
        details=[{"rate": 0.19, "amount": 38.0, "currency": "TND"}]
    )
    lines.lines.append(line_item)
    
    # Add lines to the invoice
    lines_section = ET.SubElement(root, "cac:InvoiceLine")
    for line in lines.lines:
        line.to_xml(lines_section)
    
    # Add amounts section
    amounts = {
        'amounts': [
            {
                'amount_type_code': 'I-183',  # Montant total HT
                'amount': '200.00',
                'currency': 'TND',
                'description': 'Montant hors taxes',
                'lang': 'FR'
            },
            {
                'amount_type_code': 'I-184',  # Montant total TTC
                'amount': '238.00',
                'currency': 'TND',
                'description': 'Montant toutes taxes comprises',
                'lang': 'FR'
            }
        ]
    }
    add_invoice_moa(root, amounts)
    
    return root

def sign_teif_invoice(xml_root, cert_file, key_file, key_password=None):
    """
    Sign a TEIF invoice with XAdES signature.
    
    Args:
        xml_root: The root element of the XML document to sign
        cert_file: Path to the certificate file (PEM format)
        key_file: Path to the private key file (PEM format)
        key_password: Password for the private key (if encrypted)
        
    Returns:
        The signed XML as an ElementTree Element
    """
    # Load certificate and key
    with open(cert_file, 'rb') as f:
        cert_data = f.read()
    
    with open(key_file, 'rb') as f:
        key_data = f.read()
    
    # Create signature section
    signature_section = SignatureSection()
    
    # Generate a consistent signature ID
    signature_id = f"SIG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Add signature to the invoice
    signature_section.add_signature(
        cert_data=cert_data,
        key_data=key_data,
        key_password=key_password,
        signature_id=signature_id,
        role="supplier",
        name="ACME Corporation",
        date=datetime.now(timezone.utc)
    )
    
    # Sign the document with the same signature ID
    signature_section.sign_document(xml_root, signature_id=signature_id)
    
    return xml_root

def save_xml(xml_root, output_file):
    """Save XML to file with proper formatting."""
    # Convert to string with pretty printing
    from xml.dom import minidom
    xml_str = ET.tostring(xml_root, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra newlines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    logger.info(f"Signed invoice saved to: {output_file}")

def main():
    # Paths to certificate and key files
    cert_dir = os.path.join(project_root, 'certs')
    cert_file = os.path.join(cert_dir, 'server.crt')
    key_file = os.path.join(cert_dir, 'server.key')
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if certificate and key files exist
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        logger.error("Certificate or key file not found. Please generate test certificates first.")
        logger.info(f"Run: python {os.path.join(project_root, 'scripts', 'generate_test_cert.py')}")
        sys.exit(1)
    
    try:
        # Create a sample TEIF invoice
        logger.info("Creating sample TEIF invoice...")
        invoice_xml = create_sample_teif_invoice()
        
        # Sign the invoice
        logger.info("Signing invoice with XAdES signature...")
        signed_invoice = sign_teif_invoice(
            invoice_xml,
            cert_file=cert_file,
            key_file=key_file,
            key_password=None  # Add password if key is encrypted
        )
        
        # Save the signed invoice
        output_file = os.path.join(output_dir, 'signed_invoice.xml')
        save_xml(signed_invoice, output_file)
        
        logger.info("Invoice signed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
