"""
Test module for TEIF invoice lines section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.lines import (
    add_invoice_lines,
    _add_invoice_line,
    _add_line_tax,
    _add_line_discount
)

class TestInvoiceLinesSection(unittest.TestCase):
    """Test cases for the invoice lines section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.currency = 'TND'

    def test_add_minimal_invoice_line(self):
        """Test adding a minimal invoice line with required fields only."""
        line_data = {
            'line_number': 1,
            'item': {
                'id': 'P001',
                'name': 'Produit de test'
            },
            'quantity': 2.0,
            'unit_price': 150.0,
            'line_total': 300.0
        }
        
        _add_invoice_line(self.parent, line_data, self.currency)
        
        # Vérifier la structure de base
        line = self.parent.find('InvoiceLine')
        self.assertIsNotNone(line)
        
        # Vérifier le numéro de ligne
        self.assertEqual(line.find('LineNumber').text, '1')
        
        # Vérifier l'article
        item = line.find('Item')
        self.assertEqual(item.find('ID').text, 'P001')
        self.assertEqual(item.find('Name').text, 'Produit de test')
        
        # Vérifier la quantité
        qty = line.find('InvoicedQuantity')
        self.assertEqual(qty.text, '2.0')
        self.assertEqual(qty.get('unitCode'), 'C62')  # Unité par défaut
        
        # Vérifier le prix unitaire
        price = line.find('Price/PriceAmount')
        self.assertEqual(price.text, '150.0')
        self.assertEqual(price.get('currencyID'), 'TND')
        
        # Vérifier le montant total de la ligne
        total = line.find('LineTotalAmount')
        self.assertEqual(total.text, '300.0')
        self.assertEqual(total.get('currencyID'), 'TND')

    def test_add_invoice_line_with_tax_and_discount(self):
        """Test adding an invoice line with tax and discount."""
        line_data = {
            'line_number': 2,
            'item': {
                'id': 'P002',
                'name': 'Produit avec TVA et remise'
            },
            'quantity': {
                'value': 3.0,
                'unit': 'KGM'  # Kilogrammes
            },
            'unit_price': 100.0,
            'line_total': 270.0,  # 300 - 10% de remise
            'discount': {
                'amount': 30.0,
                'reason': 'Remise spéciale'
            },
            'taxes': [{
                'amount': 51.3,  # 19% de (300-30)
                'type': 'VAT',
                'scheme': 'I-1602',
                'rate': 19.0
            }]
        }
        
        _add_invoice_line(self.parent, line_data, self.currency)
        
        # Vérifier la remise
        discount = self.parent.find('.//AllowanceCharge')
        self.assertIsNotNone(discount)
        self.assertEqual(discount.find('ChargeIndicator').text, 'false')
        self.assertEqual(discount.find('Amount').text, '30.0')
        
        # Vérifier la taxe
        tax = self.parent.find('.//TaxTotal')
        self.assertIsNotNone(tax)
        self.assertEqual(tax.find('TaxAmount').text, '51.3')
        self.assertEqual(tax.find('TaxCategory/ID').text, 'VAT')
        self.assertEqual(tax.find('TaxCategory/Percent').text, '19.0')
        self.assertEqual(tax.find('TaxCategory/TaxScheme/ID').text, 'I-1602')

    def test_add_multiple_lines(self):
        """Test adding multiple invoice lines at once."""
        lines = [
            {
                'line_number': 1,
                'item': {'id': 'P001', 'name': 'Produit 1'},
                'quantity': 1.0,
                'unit_price': 100.0,
                'line_total': 100.0
            },
            {
                'line_number': 2,
                'item': {'id': 'P002', 'name': 'Produit 2'},
                'quantity': 2.0,
                'unit_price': 200.0,
                'line_total': 400.0
            }
        ]
        
        add_invoice_lines(self.parent, lines, self.currency)
        
        # Vérifier le nombre de lignes
        lines = self.parent.findall('InvoiceLine')
        self.assertEqual(len(lines), 2)
        
        # Vérifier les numéros de ligne
        self.assertEqual(lines[0].find('LineNumber').text, '1')
        self.assertEqual(lines[1].find('LineNumber').text, '2')

def generate_sample_lines_xml():
    """Generate a sample XML with invoice lines section."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    
    # Add invoice data
    invoice = ET.SubElement(root, 'Invoice')
    
    # Add invoice lines
    lines = [
        {
            'line_number': 1,
            'item': {
                'id': 'P001',
                'name': 'Ordinateur portable'
            },
            'quantity': 2,
            'unit_price': 1500.0,
            'line_total': 3000.0,
            'taxes': [{
                'amount': 570.0,
                'type': 'VAT',
                'scheme': 'I-1602',
                'rate': 19.0
            }]
        },
        {
            'line_number': 2,
            'item': {
                'id': 'P002',
                'name': 'Souris sans fil',
                'description': 'Souris optique sans fil'
            },
            'quantity': 3,
            'unit_price': 50.0,
            'line_total': 135.0,  # Après remise
            'discount': {
                'amount': 15.0,
                'reason': 'Remise fidélité'
            },
            'taxes': [
                {
                    'amount': 25.65,
                    'type': 'VAT',
                    'scheme': 'I-1602',
                    'rate': 19.0
                }
            ]
        }
    ]
    
    # Add lines to invoice
    add_invoice_lines(invoice, lines)
    
    # Format the XML for better readability
    return minidom.parseString(ET.tostring(root, encoding='utf-8'))\
             .toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des lignes de facture TEIF ===")
    print(generate_sample_lines_xml())
