"""
TEIF XML Generator Test - Comprehensive Test Data
===============================================

This script demonstrates how to use the TEIFGenerator class to generate a complete
TEIF 1.8.8 compliant XML invoice with all mandatory and optional fields.
"""

from src.teif.generator import TEIFGenerator
from datetime import datetime, timedelta
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


def generate_complete_teif_invoice():
    """Generate a complete TEIF invoice with all possible elements."""
    # Invoice data with XML structure
    invoice_data = {
        # Header information
        "version": "1.8.8",
        "controlling_agency": "TTN",
        
        # Invoice header
        "header": {
            "sender_identifier": "0736202XAM000",
            "receiver_identifier": "0914089JAM000"
        },
        
        # BGM (Beginning of Message) section
        "bgm": {
            "document_number": "FACT-2023-001",  # Required field
            "document_type": "I-11",  # I-11 = Facture
            "document_type_label": "Facture"
        },
        
        # Dates section
        "dates": [
            {
                "date_text": datetime.now().strftime("%d%m%y"),
                "function_code": "I-31",  # Date de facture
                "format": "ddMMyy"
            },
            {
                "date_text": f"{(datetime.now() - timedelta(days=30)).strftime('%d%m%y')}-{datetime.now().strftime('%d%m%y')}",
                "function_code": "I-36",  # Période de facturation (début-fin)
                "format": "ddMMyy-ddMMyy"
            },
            {
                "date_text": (datetime.now() + timedelta(days=30)).strftime("%d%m%y"),
                "function_code": "I-32",  # Date d'échéance
                "format": "ddMMyy"
            },
        ],
        
        # Invoice lines with various scenarios
        "lines": [
            # Simple line item with basic information
            {
                "item_identifier": "DDM-001",
                "item_code": "DDM-001",
                "description": "Dossier Délivrance de Marchandises",
                "quantity": 1.0,
                "unit": "PCE",
                "unit_price": 2.0,
                "currency": "TND",
                "taxes": [
                    {
                        "type_name": "TVA",
                        "category": "S",
                        "details": [
                            {
                                "amount": 0.38,
                                "rate": 19.0,
                                "currency": "TND"
                            }
                        ]
                    }
                ]
            },
            # Line item with discount
            {
                "item_identifier": "DDR-001",
                "item_code": "DDR-001",
                "description": "Droits de Douane et Taxes",
                "quantity": 1.0,
                "unit": "PCE",
                "unit_price": 100.0,
                "currency": "TND",
                "additional_info": [
                    {
                        "code": "DISCOUNT",
                        "description": "Remise spéciale de 10%",
                        "lang": "fr"
                    }
                ],
                "taxes": [
                    {
                        "type_name": "TVA",
                        "category": "S",
                        "details": [
                            {
                                "amount": 17.1,
                                "rate": 19.0,
                                "currency": "TND"
                            }
                        ]
                    }
                ]
            },
            # Line item with sub-lines
            {
                "item_identifier": "KIT-001",
                "item_code": "KIT-001",
                "description": "Kit d'installation professionnel",
                "quantity": 1.0,
                "unit": "KIT",
                "unit_price": 500.0,
                "currency": "TND",
                "taxes": [
                    {
                        "type_name": "TVA",
                        "category": "S",
                        "details": [
                            {
                                "amount": 95.0,
                                "rate": 19.0,
                                "currency": "TND"
                            }
                        ]
                    }
                ],
                "sub_lines": [
                    {
                        "item_identifier": "KIT-001-1",
                        "item_code": "KIT-001-1",
                        "description": "Support mural",
                        "quantity": 1.0,
                        "unit": "PCE",
                        "unit_price": 200.0,
                        "currency": "TND"
                    },
                    {
                        "item_identifier": "KIT-001-2",
                        "item_code": "KIT-001-2",
                        "description": "Câble d'alimentation",
                        "quantity": 2.0,
                        "unit": "PCE",
                        "unit_price": 150.0,
                        "currency": "TND"
                    }
                ]
            }
        ],
        
        # Invoice totals
        "totals": {
            "currency": "TND",
            "line_extension_amount": 702.0,
            "tax_exclusive_amount": 590.0,
            "tax_inclusive_amount": 702.0,
            "allowance_total_amount": 10.0,
            "payable_amount": 702.0,
            "taxes": [
                {
                    "type_name": "TVA",
                    "category": "S",
                    "rate": 19.0,
                    "taxable_amount": 590.0,
                    "amount": 112.1,
                    "currency": "TND"
                }
            ]
        },
        
        # Payment terms
        "payment_terms": {
            "type": "I-10",  # Paiement à réception
            "description": "Paiement à 30 jours fin de mois",
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "discount_percent": 2.0,
            "discount_due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        },
        
        # Payment means
        "payment_means": {
            "payment_means_code": "I-30",  # Virement bancaire
            "payment_id": "VIR-2023-001",
            "payee_financial_account": {
                "iban": "TN5904018104003691234567",
                "financial_institution": "BNA"
            }
        },
        
        # Additional references
        "references": [
            {
                "type": "ON",  # Numéro de commande
                "value": "CMD-2023-456"
            },
            {
                "type": "ABO",  # Numéro d'abonnement
                "value": "ABO-2023-789"
            }
        ],
        
        # Additional documents
        "additional_documents": [
            {
                "id": "DOC-001",
                "type": "I-201",  # Facture proforma
                "name": "Facture proforma",
                "date": (datetime.now() - timedelta(days=5)).strftime("%Y%m%d"),
                "description": "Facture proforma envoyée le 5 jours avant"
            }
        ],
        
        # Special conditions
        "special_conditions": [
            "Les prix sont exprimés en dinars tunisiens (TND) toutes taxes comprises",
            "Tout retard de paiement entraînera l'application d'une pénalité de 3 fois le taux d'intérêt légal",
            {
                "text": "En cas de litige, les tribunaux tunisiens sont seuls compétents",
                "language": "fr"
            }
        ],
        
        # Signature information
        "signatures": [
            {
                "id": "SigFrs",
                "signer_role": "Fournisseur",
                "signature_policy": {
                    "policy_identifier": "1.8.8",
                    "policy_description": "Politique de signature TEIF 1.8.8"
                },
                # In a real scenario, these would be actual certificate and signature values
                "x509_cert": "MIIE...",
                "signature_value": "MIIE...",
                "digest_value": "MIIE..."
            }
        ]
    }
    
    return invoice_data


def validate_lin_section(xml_root):
    """
    Validate the LinSection in the generated XML.
    
    Args:
        xml_root: The root element of the XML document
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Find the LinSection
        lin_section = xml_root.find('.//LinSection')
        if lin_section is None:
            print("Error: LinSection not found in XML")
            return False
        
        # Check that we have line items
        line_items = lin_section.findall('Lin')
        if not line_items:
            print("Error: No line items found in LinSection")
            return False
        
        # Check the first line item
        first_line = line_items[0]
        
        # Check line number attribute
        line_number = first_line.get('lineNumber')
        if line_number != '1':
            print(f"Error: Expected lineNumber='1', got '{line_number}'")
            return False
        
        # Check item identifier
        item_identifier = first_line.find('ItemIdentifier')
        if item_identifier is None or item_identifier.text != 'DDM-001':
            print("Error: ItemIdentifier not found or incorrect")
            return False
        
        # Check item description
        imd = first_line.find('LinImd')
        if imd is None or imd.find('ItemDescription') is None:
            print("Error: Item description (LinImd) not found")
            return False
        
        # Check quantity
        qty = first_line.find('LinQty/Quantity')
        if qty is None or qty.text != '1.0':
            print("Error: Quantity not found or incorrect")
            return False
        
        # Check amount
        moa = first_line.find('LinMoa/MoaDetails/Moa')
        if moa is None or moa.find('Amount') is None:
            print("Error: Monetary amount not found")
            return False
        
        # Check tax
        tax = first_line.find('LinTax')
        if tax is None:
            print("Error: Tax information not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False


def main():
    """Main function to generate and save the TEIF XML invoice."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # Generate the invoice data
        invoice_data = generate_complete_teif_invoice()
        
        # Create TEIF generator instance
        generator = TEIFGenerator()
        
        # Generate the XML
        xml_content = generator.generate_teif_xml(invoice_data)
        
        # Save to file
        output_file = os.path.join('output', 'complete_invoice.xml')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"TEIF XML invoice has been generated successfully: {output_file}")
        
        # Validate the LinSection
        try:
            root = ET.fromstring(xml_content.encode('utf-8'))
            if validate_lin_section(root):
                print("LinSection validation: PASSED")
            else:
                print("LinSection validation: FAILED")
        except Exception as e:
            print(f"Error during validation: {str(e)}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating TEIF XML: {str(e)}")
        return 1


if __name__ == "__main__":
    main()
