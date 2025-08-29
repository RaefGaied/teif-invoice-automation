"""
Test module for TEIF taxes section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.taxes import (
    add_tax_detail,
    add_invoice_tax_section
)

class TestTaxesSection(unittest.TestCase):
    """Test cases for the taxes section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.currency = 'TND'

    def test_add_tax_detail_basic(self):
        """Test adding a basic tax detail."""
        tax_data = {
            'code': 'I-1602',
            'name': 'TVA',
            'rate': 19.0,
            'amount': 190.0,
            'taxable_amount': 1000.0
        }
        
        add_tax_detail(self.parent, tax_data, self.currency)
        
        # Vérifier la structure de base
        tax_total = self.parent.find('TaxTotal')
        self.assertIsNotNone(tax_total)
        
        # Vérifier le montant de la taxe
        amount = tax_total.find('.//Amount[@amountTypeCode="I-160"]')
        self.assertEqual(amount.text, '190.000')
        self.assertEqual(amount.get('currencyID'), 'TND')
        
        # Vérifier le montant taxable
        taxable = tax_total.find('.//Amount[@amountTypeCode="I-162"]')
        self.assertEqual(taxable.text, '1000.000')
        
        # Vérifier le code de taxe
        tax_scheme = tax_total.find('.//TaxScheme/ID')
        self.assertEqual(tax_scheme.text, 'I-1602')
        
        # Vérifier le taux de TVA
        percent = tax_total.find('.//Percent')
        self.assertEqual(percent.text, '19.0')

    def test_add_invoice_tax_section(self):
        """Test adding a complete tax section to an invoice."""
        tax_data = {
            'amount': 228.0,  # Total des taxes
            'taxes': [
                {
                    'code': 'I-1602',  # TVA 19%
                    'name': 'TVA 19%',
                    'rate': 19.0,
                    'amount': 190.0,
                    'taxable_amount': 1000.0
                },
                {
                    'code': 'I-1603',  # Droit de timbre
                    'name': 'Droit de timbre',
                    'rate': 1.0,
                    'amount': 10.0,
                    'taxable_amount': 1000.0
                },
                {
                    'code': 'I-1604',  # Autre taxe
                    'name': 'Taxe spéciale',
                    'rate': 2.8,
                    'amount': 28.0,
                    'taxable_amount': 1000.0
                }
            ]
        }
        
        add_invoice_tax_section(self.parent, tax_data, self.currency)
        
        # Vérifier le montant total des taxes
        tax_total = self.parent.find('TaxTotal')
        self.assertIsNotNone(tax_total)
        
        # Vérifier le montant total
        total_amount = tax_total.find('.//Amount[@amountTypeCode="I-160"]')
        self.assertEqual(total_amount.text, '228.000')
        
        # Vérifier le nombre de taxes (chaque taxe est dans son propre TaxTotal)
        taxes = tax_total.findall('TaxTotal')
        self.assertEqual(len(taxes), 3)
        
        # Vérifier les codes de taxe
        tax_codes = [t.find('.//TaxScheme/ID').text for t in taxes]
        self.assertIn('I-1602', tax_codes)  # TVA
        self.assertIn('I-1603', tax_codes)  # Droit de timbre
        self.assertIn('I-1604', tax_codes)  # Autre taxe

    def test_tax_detail_missing_fields(self):
        """Test adding a tax detail with missing required fields."""
        with self.assertRaises(ValueError) as context:
            add_tax_detail(self.parent, {'code': 'I-1602'}, self.currency)
        
        self.assertIn("Champs de taxe manquants", str(context.exception))

def generate_sample_taxes_xml():
    """Generate a sample XML with taxes section."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    
    # Add invoice data
    invoice = ET.SubElement(root, 'Invoice')
    
    # Add taxes section
    taxes_data = {
        'amount': 228.0,
        'taxes': [
            {
                'code': 'I-1602',  # TVA 19%
                'name': 'TVA 19%',
                'rate': 19.0,
                'amount': 190.0,
                'taxable_amount': 1000.0
            },
            {
                'code': 'I-1603',  # Droit de timbre
                'name': 'Droit de timbre',
                'rate': 1.0,
                'amount': 10.0,
                'taxable_amount': 1000.0
            },
            {
                'code': 'I-1604',  # Autre taxe
                'name': 'Taxe spéciale',
                'rate': 2.8,
                'amount': 28.0,
                'taxable_amount': 1000.0
            }
        ]
    }
    
    # Add taxes to invoice
    add_invoice_tax_section(invoice, taxes_data)
    
    # Format the XML for better readability
    return minidom.parseString(ET.tostring(root, encoding='utf-8'))\
             .toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des taxes TEIF ===")
    print(generate_sample_taxes_xml())
