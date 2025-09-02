"""
TEIF XML Generator Test - Comprehensive Test Data
===============================================

This script demonstrates how to use the TEIFGenerator class to generate a complete
TEIF 1.8.8 compliant XML invoice with all mandatory and optional fields.
"""

from src.teif.generator import TEIFGenerator
from datetime import datetime, timedelta
import os
import lxml.etree as ET
from xml.dom import minidom


def generate_complete_teif_invoice():
    """Generate a complete TEIF invoice with all possible elements."""
    # Invoice data with XML structure
    invoice_data = {
        # Header information
        "version": "1.8.8",
        "controlling_agency": "TTN",
        # Seller information (vendeur)
        "seller": {
            "identifier": "1234567AAM001",  
            "identifier_type": "I-01",  
            "name": "SOCIETE FOURNISSEUR SARL",
            "legal_form": "SARL",
            "vat_number": "12345678",
            "address": {
                "street": "AVENUE HABIB BOURGUIBA",
                "city": "TUNIS",
                "postal_code": "1000",
                "country_code": "TN",  
                "lang": "FR"  
            },
            "contacts": [
                {
                    "function_code": "I-94",  
                    "name": "Service Commercial",
                    "communications": [
                        {"type": "I-101", "value": "+216 70 000 000"},  
                        {"type": "I-102", "value": "commercial@fournisseur.tn"}  
                    ]
                }
            ],
            "references": [
                {"type": "VA", "value": "12345678"}  
            ]
        },

        # Buyer information (acheteur)
        "buyer": {
            "identifier": "9876543BBM002",  
            "identifier_type": "I-01",  
            "name": "SOCIETE CLIENTE SARL",
            "legal_form": "SARL",
            "vat_number": "87654321",
            "address": {
                "street": "AVENUE MOHAMED V",
                "city": "SOUSSE",
                "postal_code": "4000",
                "country_code": "TN",  
                "lang": "FR"  
            },
            "contacts": [
                {
                    "function_code": "I-94",  
                    "name": "Service Achat",
                    "communications": [
                        {"type": "I-101", "value": "+216 71 000 001"},  
                        {"type": "I-104", "value": "achat@client.tn"}  
                    ]
                }
            ],
            "references": [
                {"type": "VA", "value": "87654321"}  
            ]
        },
        
        # Invoice header
        "header": {
            "sender_identifier": "0736202XAM000",
            "receiver_identifier": "0914089JAM000"
        },
        
        # BGM (Beginning of Message) section
        "bgm": {
            "document_number": "FACT-2023-001",  
            "document_type": "I-11",  
            "document_type_label": "Facture"
        },
        
        # Dates section
        "dates": [
            {
                "date_text": datetime.now().strftime("%d%m%y"),
                "function_code": "I-31",  
                "format": "ddMMyy"
            },
            {
                "date_text": f"{(datetime.now() - timedelta(days=30)).strftime('%d%m%y')}-{datetime.now().strftime('%d%m%y')}",
                "function_code": "I-36",  
                "format": "ddMMyy-ddMMyy"
            },
            {
                "date_text": (datetime.now() + timedelta(days=30)).strftime("%d%m%y"),
                "function_code": "I-32",  
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
                        "code": "I-1602",
                        "type_name": "TVA",
                        "category": "S",
                        "rate": 19.0,
                        "amount": 0.38,
                        "currency": "TND"
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
                        "code": "I-1602",
                        "type_name": "TVA",
                        "category": "S",
                        "rate": 19.0,
                        "amount": 17.1,
                        "currency": "TND"
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
                        "code": "I-1602",
                        "type_name": "TVA",
                        "category": "S",
                        "rate": 19.0,
                        "amount": 95.0,
                        "currency": "TND"
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
        
        # Tax information
        "taxes": [
            {
                "code": "I-1602",  
                "type_name": "TVA",
                "category": "S",
                "rate": 19.0,
                "basis": 1000.0,  
                "amount": 190.0,  
                "currency": "TND"
            },
            {
                "code": "I-1603",  
                "type_name": "Droit de timbre",
                "rate": 1.0,
                "amount": 10.0,
                "currency": "TND"
            }
        ],
        
        # Totals
        "totals": {
            "total_without_tax": 1000.0,
            "total_tax": 200.0,
            "total_with_tax": 1200.0,
            "prepaid_amount": 600.0,
            "due_amount": 600.0,
            "currency": "TND"
        },
        
        # Payment terms
        "payment_terms": {
            "code": "I-10",
            "description": "Paiement à 30 jours fin de mois",
            "discount_percent": 2.0,
            "discount_due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        },
        
        # Payment means
        "payment_means": {
            "payment_means_code": "I-30",
            "payment_id": "VIR-2023-001",
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "payee_financial_account": {
                "iban": "TN5904018104003691234567",
                "account_holder": "NOM_DU_TITULAIRE",
                "financial_institution": "BNA",
                "branch_code": "AGENCE_123"
            }
        },
        
        # Additional references
        "references": [
            {
                "type": "ON",  
                "value": "CMD-2023-456"
            },
            {
                "type": "ABO",  
                "value": "ABO-2023-789"
            }
        ],
        
        # Additional documents
        "additional_documents": [
            {
                "id": "DOC-001",
                "type": "I-201",  
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
                "signer_role": "Fournisseur",
                "x509_cert": open(os.path.join(os.path.dirname(__file__), 'test_data', 'test_cert.pem'), 'rb').read(),
                "private_key": open(os.path.join(os.path.dirname(__file__), 'test_data', 'test_key.pem'), 'rb').read(),
                "key_password": None,  # No password for test key
                "signer_name": "Fournisseur Test",
                "date": "2023-01-01T12:00:00Z"
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


def test_generate_teif_xml_with_signature():
    """Test TEIF XML generation with a signature."""
    # Sample certificate and key for testing
    test_cert = """-----BEGIN CERTIFICATE-----\nMIIDXzCCAkegAwIBAgIUQ1Xv2qX5J7jX5X5X5X5X5X0wDQYJKoZIhvcN\n...\n-----END CERTIFICATE-----"""

    test_key = """-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJQ5X5X5X5X5\n...\n-----END PRIVATE KEY-----"""

    try:
        print("\nTest de la génération de la signature...")
        
        # Generate the invoice with signature
        invoice_data = generate_complete_teif_invoice()
        
        # Add signature data in the expected format
        invoice_data['signature'] = {
            'cert_data': test_cert,
            'key_data': test_key,
            'signature_id': 'SIG-001',
            'role': 'supplier',
            'name': 'Test Signer'
        }
        
        # Generate the XML
        teif_generator = TEIFGenerator()
        xml_data = teif_generator.generate_teif_xml(invoice_data)
        
        # Save the XML for inspection
        os.makedirs("output", exist_ok=True)
        debug_path = os.path.join("output", "debug_signed_invoice.xml")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(xml_data)
        
        # Parse with lxml.etree for proper namespace handling
        parser = ET.XMLParser(remove_blank_text=True)
        root = ET.fromstring(xml_data.encode('utf-8'), parser=parser)
        
        # Define namespaces for XPath
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }
        
        # Find signature using XPath with namespaces
        signature = root.xpath('//ds:Signature', namespaces=ns)
        assert len(signature) > 0, "Signature element not found"
        signature = signature[0]
        
        # Debug: Print the signature element and its children
        print("\nDebug - Signature element content:")
        print(ET.tostring(signature, pretty_print=True, encoding='unicode'))
        
        # Debug: Print all namespaces in the document
        print("\nDebug - All namespaces in document:")
        for k, v in root.nsmap.items():
            print(f"{k}: {v}")
        
        # Debug: Print SignedInfo content
        signed_info = signature.xpath('ds:SignedInfo', namespaces=ns)
        print(f"\nDebug - Found {len(signed_info)} SignedInfo elements")
        if signed_info:
            print("Debug - SignedInfo content:", ET.tostring(signed_info[0], pretty_print=True, encoding='unicode'))
        
        assert signed_info, "SignedInfo not found"
        
        # Check for required elements using XPath
        assert signature.xpath('ds:SignatureValue', namespaces=ns), "SignatureValue not found"
        assert signature.xpath('ds:KeyInfo/ds:X509Data/ds:X509Certificate', namespaces=ns), "X509Certificate not found"
        
        # Check XAdES elements
        assert signature.xpath('.//xades:QualifyingProperties', namespaces=ns), "QualifyingProperties not found"
        assert signature.xpath('.//xades:SignedProperties', namespaces=ns), "SignedProperties not found"
        
        print("✓ Tous les éléments de signature requis sont présents")
        return True
        
    except Exception as e:
        print(f"\nError in test_generate_teif_xml_with_signature: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_complete_xml_with_signature():
    """Generate a complete TEIF XML with all required elements and signature."""
    try:
        print("\nGénération d'un fichier XML complet avec signature...")
        
        # 1. Create complete invoice data
        invoice_data = {
            "header": {
                "sender_identifier": "0736202XAM000",
                "receiver_identifier": "0914089JAM000"
            },
            "bgm": {
                "document_number": "FACT-2023-001",
                "document_type": "I-11",
                "document_type_label": "Facture"
            },
            "dates": [
                {
                    "date_text": datetime.now().strftime("%d%m%y"),
                    "function_code": "I-31",
                    "format": "ddMMyy"
                },
                {
                    "date_text": f"{(datetime.now() - timedelta(days=30)).strftime('%d%m%y')}-{datetime.now().strftime('%d%m%y')}",
                    "function_code": "I-36",
                    "format": "ddMMyy-ddMMyy"
                },
                {
                    "date_text": (datetime.now() + timedelta(days=30)).strftime("%d%m%y"),
                    "function_code": "I-32",
                    "format": "ddMMyy"
                }
            ],
            "seller": {
                "name": "Vendeur Test",
                "identifier": "123456789",
                "vat_number": "12345678",
                "address": {
                    "street": "123 Rue du Vendeur",
                    "city": "Tunis",
                    "postal_code": "1000",
                    "country_code": "TN"
                }
            },
            "buyer": {
                "name": "Acheteur Test",
                "identifier": "987654321",
                "vat_number": "87654321",
                "address": {
                    "street": "456 Avenue de l'Acheteur",
                    "city": "Sousse",
                    "postal_code": "4000",
                    "country_code": "TN"
                }
            },
            "lines": [
                {
                    "item_name": "Produit A",
                    "description": "Description du produit A",
                    "quantity": 2,
                    "unit_price": 150.50,
                    "tax_rate": 0.19,
                    "tax_type_code": "T1",
                    "currency": "TND"
                },
                {
                    "item_name": "Service B",
                    "description": "Description du service B",
                    "quantity": 1,
                    "unit_price": 300.75,
                    "tax_rate": 0.07,
                    "tax_type_code": "T2",
                    "currency": "TND"
                }
            ],
            "payment_terms": {
                "payment_means_code": "30",
                "payment_means_text": "Virement bancaire",
                "payment_due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            },
            "monetary_totals": {
                "line_extension_amount": 601.75,
                "tax_exclusive_amount": 601.75,
                "tax_inclusive_amount": 712.25,
                "payable_amount": 712.25,
                "currency": "TND"
            },
            "signature": {
                "cert_data": """-----BEGIN CERTIFICATE-----\nMIIDXzCCAkegAwIBAgIUQ1Xv2qX5J7jX5X5X5X5X5X0wDQYJKoZIhvcN\n...\n-----END CERTIFICATE-----""",
                "key_data": """-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJQ5X5X5X5X5\n...\n-----END PRIVATE KEY-----""",
                "signature_id": 'SIG-001',
                'role': 'supplier',
                'name': 'Signataire Test'
            }
        }
        
        # 2. Generate the XML
        teif_generator = TEIFGenerator()
        xml_data = teif_generator.generate_teif_xml(invoice_data)
        
        # 3. Save the complete XML file
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "complete_invoice_with_signature.xml")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_data)
        
        print(f"✓ Fichier XML généré avec succès : {os.path.abspath(output_path)}")
        
        # 4. Validate the XML structure
        try:
            # Parse with lxml.etree for validation
            parser = ET.XMLParser(remove_blank_text=True)
            root = ET.fromstring(xml_data.encode('utf-8'), parser=parser)
            
            # Define namespaces for validation
            ns = {
                'ds': 'http://www.w3.org/2000/09/xmldsig#',
                'xades': 'http://uri.etsi.org/01903/v1.3.2#',
                'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
            }
            
            # Validate required sections
            assert root.find('.//cac:AccountingSupplierParty', namespaces=ns) is not None, "Fournisseur manquant"
            assert root.find('.//cac:AccountingCustomerParty', namespaces=ns) is not None, "Client manquant"
            assert root.find('.//cac:InvoiceLine', namespaces=ns) is not None, "Lignes de facture manquantes"
            assert root.find('.//cac:TaxTotal', namespaces=ns) is not None, "Total TVA manquant"
            assert root.find('.//cac:LegalMonetaryTotal', namespaces=ns) is not None, "Total général manquant"
            
            # Validate signature
            signature = root.find('.//ds:Signature', namespaces=ns)
            assert signature is not None, "Signature manquante"
            
            print("✓ Structure XML validée avec succès")
            return True
            
        except Exception as e:
            print(f"\nAvertissement lors de la validation : {str(e)}")
            return False
            
    except Exception as e:
        print(f"\nErreur lors de la génération du fichier XML : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def sample_invoice_data():
    # Sample invoice data with signature
    invoice_data = {
        "header": {
            "invoice_number": "INV-2023-001",
            "issue_date": "2023-01-15",
            "due_date": "2023-02-15",
            "invoice_type_code": "I-10",
            "document_currency_code": "TND"
        },
        "seller": {
            "name": "Vendor Inc.",
            "identifier": "12345678",  
            "vat_number": "12345678",
            "address": {
                "street": "123 Vendor St",
                "city": "Tunis",
                "postal_code": "1000",
                "country_code": "TN"
            }
        },
        "buyer": {
            "name": "Customer Co.",
            "identifier": "87654321",  
            "vat_number": "87654321",
            "address": {
                "street": "456 Customer Ave",
                "city": "Sousse",
                "postal_code": "4000",
                "country_code": "TN"
            }
        },
        "lines": [
            {
                "item_name": "Product A",
                "quantity": 2,
                "unit_price": 100.0,
                "tax_rate": 0.19,
                "tax_type_code": "T1"
            }
        ],
        "signature": {
            "x509_cert": open(os.path.join(os.path.dirname(__file__), 'test_data', 'test_cert.pem'), 'rb').read(),
            "private_key": open(os.path.join(os.path.dirname(__file__), 'test_data', 'test_key.pem'), 'rb').read(),
            "signer_name": "Test Signer",
            "signer_role": "Supplier",
            "id": "SIG-001"
        }
    }

    return invoice_data


def main():
    """Main function to generate and save the TEIF XML invoice."""
    try:
        print("Début de la génération de la facture TEIF...")
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        # Test signature generation first
        print("\nTest de la génération de la signature...")
        if not test_generate_teif_xml_with_signature():
            print("✗ Le test de signature a échoué")
            return 1
            
        print("✓ Test de signature réussi")
        
        # Generate and save the complete invoice
        print("\nGénération de la facture complète...")
        invoice_data = generate_complete_teif_invoice()
        teif_generator = TEIFGenerator()
        xml_data = teif_generator.generate_teif_xml(invoice_data)
        
        if xml_data:
            output_path = os.path.join("output", "complete_invoice.xml")
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    if isinstance(xml_data, dict):
                        # Convert dict to XML string if needed
                        xml_string = str(xml_data)
                    else:
                        xml_string = xml_data
                    f.write(xml_string)
                print(f"✓ Facture TEIF générée avec succès : {os.path.abspath(output_path)}")
                
                # Validate the generated XML
                try:
                    # Parse with lxml.etree for validation
                    parser = ET.XMLParser(remove_blank_text=True)
                    root = ET.fromstring(xml_string.encode('utf-8'), parser=parser)
                    print("✓ Validation réussie : Le fichier XML est valide")
                except Exception as e:
                    print(f"✗ La validation a échoué: {str(e)}")
                    
            except IOError as e:
                print(f"✗ Erreur lors de l'écriture du fichier {output_path}: {str(e)}")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
