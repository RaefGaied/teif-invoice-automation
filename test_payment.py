"""
Test module for TEIF payment section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.dom import minidom

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.payment import add_payment_terms

class TestPaymentSection(unittest.TestCase):
    """Test cases for the payment section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.today = datetime.now()
        self.due_date = self.today + timedelta(days=30)

    def test_add_basic_payment_terms(self):
        """Test adding basic payment terms."""
        payment_data = {
            'code': 'I-101',  # Paiement comptant
            'description': 'Paiement à 30 jours',
            'due_date': self.due_date,
            'means_of_payment': 'I-111'  # Virement bancaire
        }
        
        add_payment_terms(self.parent, payment_data)
        
        # Vérifier la structure de base
        terms = self.parent.find('PaymentTerms')
        self.assertIsNotNone(terms)
        
        # Vérifier le code de paiement
        code = terms.find("PaymentTermsTypeCode[@listID='I-100']")
        self.assertEqual(code.text, 'I-101')
        
        # Vérifier la description
        self.assertEqual(terms.find('Note').text, 'Paiement à 30 jours')
        
        # Vérifier la date d'échéance
        due_date = terms.find('Settlement/PaymentDueDate')
        self.assertEqual(due_date.text, self.due_date.strftime('%Y-%m-%d'))
        
        # Vérifier le moyen de paiement
        means = terms.find("PaymentMeans/PaymentMeansCode[@listID='I-110']")
        self.assertEqual(means.text, 'I-111')

    def test_add_payment_with_discount(self):
        """Test adding payment terms with discount."""
        discount_date = self.today + timedelta(days=10)
        
        payment_data = {
            'code': 'I-102',  # Paiement à terme
            'due_date': self.due_date,
            'means_of_payment': 'I-111',
            'discount_terms': {
                'amount': 50.0,
                'rate': 2.0,  # 2%
                'currency': 'TND',
                'period': {
                    'end_date': discount_date,
                    'base_date': self.today
                }
            }
        }
        
        add_payment_terms(self.parent, payment_data)
        
        # Vérifier la remise
        discount = self.parent.find('.//Discount')
        self.assertIsNotNone(discount)
        
        # Vérifier le montant de la remise
        amount = discount.find('Amount')
        self.assertEqual(amount.text, '50.0')
        self.assertEqual(amount.get('currencyID'), 'TND')
        
        # Vérifier le taux de remise
        self.assertEqual(discount.find('Rate').text, '2.0')
        
        # Vérifier la période de remise
        period = discount.find('DiscountPeriod')
        self.assertEqual(period.find('EndDate').text, discount_date.strftime('%Y-%m-%d'))
        self.assertEqual(period.find('BaseDate').text, self.today.strftime('%Y-%m-%d'))

    def test_add_payment_with_period(self):
        """Test adding payment terms with period."""
        start_date = self.today
        end_date = self.today + timedelta(days=30)
        
        payment_data = {
            'code': 'I-103',  # Paiement échelonné
            'terms': {
                'start_date': start_date,
                'end_date': end_date,
                'duration': 30  # jours
            },
            'means_of_payment': 'I-112'  # Chèque
        }
        
        add_payment_terms(self.parent, payment_data)
        
        # Vérifier la période de paiement
        period = self.parent.find('.//PaymentPeriod')
        self.assertIsNotNone(period)
        
        # Vérifier les dates
        self.assertEqual(period.find('StartDate').text, start_date.strftime('%Y-%m-%d'))
        self.assertEqual(period.find('EndDate').text, end_date.strftime('%Y-%m-%d'))
        
        # Vérifier la durée
        duration = period.find("DurationMeasure[@unitCode='DAY']")
        self.assertEqual(duration.text, '30')

def generate_sample_payment_xml():
    """Generate a sample XML with payment terms section."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    
    # Add invoice data
    invoice = ET.SubElement(root, 'Invoice')
    
    # Add payment terms
    today = datetime.now()
    due_date = today + timedelta(days=30)
    discount_date = today + timedelta(days=10)
    
    payment_data = {
        'code': 'I-102',  # Paiement à terme
        'description': 'Paiement à 30 jours avec escompte de 2% pour paiement sous 10 jours',
        'due_date': due_date,
        'means_of_payment': 'I-111',  # Virement bancaire
        'discount_terms': {
            'amount': 200.0,
            'rate': 2.0,  # 2%
            'currency': 'TND',
            'period': {
                'end_date': discount_date,
                'base_date': today
            }
        }
    }
    
    # Add payment terms to invoice
    add_payment_terms(invoice, payment_data)
    
    # Format the XML for better readability
    return minidom.parseString(ET.tostring(root, encoding='utf-8'))\
             .toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des conditions de paiement TEIF ===")
    print(generate_sample_payment_xml())
