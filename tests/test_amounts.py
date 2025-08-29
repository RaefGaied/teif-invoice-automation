"""
Test module for TEIF amounts section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.amounts import create_amount_element, create_tax_amount, create_line_amount

class TestAmountsSection(unittest.TestCase):
    """Test cases for the amounts section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.currency = 'TND'

    def test_create_amount_element(self):
        """Test creating a basic amount element."""
        amount_data = {
            'amount': 1000.50,
            'currency': self.currency,
            'amount_type': 'I-170',
            'amount_type_name': 'Montant HT'
        }
        
        moa = create_amount_element(self.parent, amount_data)
        amount_elem = moa.find('Amount')
        
        self.assertEqual(moa.tag, 'Moa')
        self.assertEqual(amount_elem.get('currencyID'), self.currency)
        self.assertEqual(amount_elem.get('amountTypeCode'), 'I-170')
        self.assertEqual(amount_elem.text, '1000.500')

    def test_create_tax_amount(self):
        """Test creating a tax amount element."""
        tax_data = {
            'code': 'I-1602',
            'type': 'TVA',
            'rate': 19.0,
            'amount': 190.0,
            'taxable_amount': 1000.0,
            'currency': self.currency
        }
        
        invoice_tax = create_tax_amount(self.parent, tax_data)
        tax_type = invoice_tax.find('Tax/TaxTypeName')
        
        self.assertEqual(tax_type.get('code'), 'I-1602')
        self.assertEqual(tax_type.text, 'TVA')
        self.assertEqual(invoice_tax.find('Tax/TaxRate').text, '19.0')

    def test_create_line_amount(self):
        """Test creating a line amount element."""
        line_data = {
            'unit_price': 10.5,
            'quantity': 2,
            'line_total': 21.0,
            'currency': self.currency
        }
        
        line_elem = ET.Element('InvoiceLine')
        create_line_amount(line_elem, line_data)
        
        # Vérifier le prix unitaire
        price_amount = line_elem.find('Price/Moa/Amount')
        self.assertIsNotNone(price_amount)
        self.assertEqual(price_amount.text, '10.5000')
        
        # Vérifier le montant total de la ligne
        # Parcourir tous les éléments Moa/Amount et vérifier celui avec le bon amountTypeCode
        found = False
        for moa in line_elem.findall('Moa'):
            amount = moa.find('Amount')
            if amount is not None and amount.get('amountTypeCode') == 'I-179':
                self.assertEqual(amount.text, '21.000')
                found = True
                break
        self.assertTrue(found, "Aucun montant total trouvé avec amountTypeCode='I-179'")

def generate_sample_amounts_xml():
    """Generate a sample XML with amounts."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    body = ET.SubElement(root, 'InvoiceBody')
    
    # Add amounts
    amounts = ET.SubElement(body, 'InvoiceAmounts')
    
    # Add line amounts
    line = ET.SubElement(amounts, 'InvoiceLine')
    create_line_amount(line, {
        'unit_price': 10.5,
        'quantity': 2,
        'line_total': 21.0,
        'currency': 'TND'
    })
    
    # Add tax
    tax = ET.SubElement(amounts, 'InvoiceTax')
    create_tax_amount(tax, {
        'code': 'I-1602',
        'type': 'TVA',
        'rate': 19.0,
        'amount': 3.99,
        'taxable_amount': 21.0,
        'currency': 'TND'
    })
    
    # Format XML
    from xml.dom import minidom
    return minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des montants TEIF ===")
    print(generate_sample_amounts_xml())
