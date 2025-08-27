"""
Test script to verify quantity formatting in TEIF XML output.
"""
import sys
import os
import xml.etree.ElementTree as ET

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.generator import TEIFGenerator

def test_quantity_formatting():
    """Test different quantity formats in invoice lines."""
    # Initialize the generator
    generator = TEIFGenerator()
    
    # Create a test invoice with different quantity formats
    invoice_data = {
        # En-tête obligatoire
        'document_id': 'TEST-001',
        'invoice_number': 'TEST-001',
        'invoice_date': '2024-01-01',
        'invoice_type': 'I-11',  # Code pour facture commerciale
        'currency': 'TND',
        
        # Section vendeur (obligatoire)
        'seller': {
            'name': 'Test Seller SARL',
            'tax_id': '12345678',
            'tax_id_scheme': 'VAT',
            'address': {
                'street': '123 Avenue Habib Bourguiba',
                'city': 'Tunis',
                'postal_code': '1000',
                'country': 'TN'
            },
            'contact': {
                'name': 'Service Facturation',
                'email': 'facturation@testseller.tn',
                'phone': '+21670123456'
            },
            'legal_form': 'SARL',
            'registration_number': 'A12345678',
            'fiscal_code': 'MF12345678'
        },
        
        # Section acheteur (obligatoire)
        'buyer': {
            'name': 'Test Buyer SA',
            'tax_id': '87654321',
            'tax_id_scheme': 'VAT',
            'address': {
                'street': '456 Avenue de la Liberté',
                'city': 'Sousse',
                'postal_code': '4000',
                'country': 'TN'
            }
        },
        
        # Lignes de facture (au moins une requise)
        'lines': [
            # Article 1 - Produit avec quantité en kilogrammes
            {
                'line_number': 1,
                'item': {
                    'name': 'Café Arabica Premium',
                    'id': 'CAFE-ARAB-1KG'
                },
                'quantity': {'value': 2.5, 'unit': 'KGM'},  # Kilogrammes
                'unit_price': 10.0,
                'line_total': 25.0,
                'taxes': [{
                    'type': 'TVA',
                    'rate': 19.0,
                    'amount': 4.75,
                    'scheme': 'TVA'
                }]
            },
            # Article 2 - Service avec quantité en unités
            {
                'line_number': 2,
                'item': {
                    'name': 'Maintenance serveur',
                    'id': 'SVC-MAINT-3H'
                },
                'quantity': {'value': 3, 'unit': 'HUR'},  # Heures
                'unit_price': 15.0,
                'line_total': 45.0,
                'taxes': [{
                    'type': 'TVA',
                    'rate': 7.0,
                    'amount': 3.15,
                    'scheme': 'TVA'
                }]
            },
            # Article 3 - Service avec quantité par défaut (pièces)
            {
                'line_number': 3,
                'item': {
                    'name': 'Consultation technique',
                    'id': 'CONSULT-TECH-01'
                },
                'quantity': 1.5,  # Utilisera l'unité par défaut (C62 = pièce)
                'unit_price': 20.0,
                'line_total': 30.0,
                'taxes': [{
                    'type': 'TVA',
                    'rate': 19.0,
                    'amount': 5.70,
                    'scheme': 'TVA'
                }]
            }
        ]
    }
    
    # Generate the XML with proper XML declaration and encoding
    xml_str = generator.generate_teif_xml(invoice_data)
    
    # Print the XML for debugging
    print("\n=== XML Généré ===")
    print(xml_str[:1000] + "..." if len(xml_str) > 1000 else xml_str)
    
    # Parse the XML to verify the structure
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f"\n❌ Erreur de parsing XML: {e}")
        with open('error_xml.xml', 'w', encoding='utf-8') as f:
            f.write(xml_str)
        print("Le XML avec erreur a été enregistré dans 'error_xml.xml'")
        return
    
    # Register the TEIF namespace
    namespaces = {'teif': 'urn:tunisiandatastandard:standard:teif:teif-invoice:1.8.8'}
    
    # Vérification de la structure de base
    print("\n=== Vérification de la structure TEIF 1.8.8 ===")
    
    # Vérification des éléments racines obligatoires
    required_sections = ['InvoiceHeader', 'InvoiceBody']
    missing_sections = [sect for sect in required_sections if root.find(f'teif:{sect}', namespaces) is None]
    if missing_sections:
        print(f"❌ Sections manquantes: {', '.join(missing_sections)}")
    else:
        print("✅ Toutes les sections obligatoires sont présentes")
    
    # Vérification du corps de la facture
    body = root.find('teif:InvoiceBody', namespaces)
    if body is not None:
        # Vérification des sections obligatoires dans le corps
        required_body_sections = ['Bgm', 'LinSection']
        missing_body_sections = [sect for sect in required_body_sections 
                               if body.find(f'teif:{sect}', namespaces) is None]
        
        if missing_body_sections:
            print(f"❌ Sections manquantes dans InvoiceBody: {', '.join(missing_body_sections)}")
        else:
            print("✅ Toutes les sections obligatoires sont présentes dans InvoiceBody")
            
            # Vérification des lignes de facture
            lines = body.findall('.//teif:InvoiceLine', namespaces)
            if not lines:
                print("❌ Aucune ligne de facture trouvée")
            else:
                print(f"✅ {len(lines)} ligne(s) de facture trouvée(s)")
                
                # Vérification détaillée de la première ligne
                first_line = lines[0]
                line_id = first_line.find('teif:LineNumber', namespaces)
                item = first_line.find('teif:Item/teif:Description', namespaces)
                qty = first_line.find('teif:InvoicedQuantity', namespaces)
                price = first_line.find('teif:Price/teif:PriceAmount', namespaces)
                line_total = first_line.find('teif:LineTotalAmount', namespaces)
                
                print("\n=== Détails de la première ligne ===")
                print(f"Numéro de ligne: {line_id.text if line_id is not None else 'Non spécifié'}")
                print(f"Description: {item.text if item is not None else 'Non spécifiée'}")
                print(f"Quantité: {qty.text if qty is not None else 'Non spécifiée'} "
                      f"({qty.get('unitCode') if qty is not None else 'unité inconnue'})")
                print(f"Prix unitaire: {price.text if price is not None else 'Non spécifié'} "
                      f"{price.get('currencyID') if price is not None else ''}")
                print(f"Montant total: {line_total.text if line_total is not None else 'Non spécifié'} "
                      f"{line_total.get('currencyID') if line_total is not None else ''}")
                
                # Vérification des taxes
                taxes = first_line.findall('teif:TaxTotal', namespaces)
                if taxes:
                    print(f"\nTaxes appliquées: {len(taxes)}")
                    for i, tax in enumerate(taxes, 1):
                        tax_amt = tax.find('teif:TaxAmount', namespaces)
                        tax_cat = tax.find('teif:TaxCategory', namespaces)
                        print(f"  Taxe {i}: {tax_amt.text if tax_amt is not None else 'Montant inconnu'} "
                              f"({tax_amt.get('currencyID') if tax_amt is not None else 'devise inconnue'})")
                        if tax_cat is not None:
                            print(f"  Catégorie: {tax_cat.get('ID') or 'Non spécifiée'}")
                else:
                    print("\n⚠ Aucune taxe spécifiée sur la première ligne")
    
    # Save the test XML for inspection
    with open('test_quantity_formatting.xml', 'w', encoding='utf-8') as f:
        f.write(xml_str)
    print("\nTest XML saved to 'test_quantity_formatting.xml'")

if __name__ == "__main__":
    test_quantity_formatting()
