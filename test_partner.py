"""
Test module for TEIF partner section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.partner import (
    add_seller_party,
    add_buyer_party,
    add_delivery_party,
    create_partner_section
)

class TestPartnerSection(unittest.TestCase):
    """Test cases for the partner section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')

    def test_create_seller_party(self):
        """Test creating a seller party section."""
        seller_data = {
            'id': '12345678',
            'type': 'MF',
            'name': 'Société Vendeur SARL',
            'address': {
                'street': '123 Rue du Commerce',
                'city': 'Tunis',
                'postal_code': '1000',
                'country': 'TN'
            },
            'references': {
                'RC': 'A12345678',
                'MF': '12345678'
            },
            'contacts': {
                'Téléphone': '+216 71 123 456',
                'Email': 'contact@vendeur.tn'
            }
        }
        
        add_seller_party(self.parent, seller_data)
        
        # Vérifier l'élément vendeur
        seller = self.parent.find('SellerParty')
        self.assertIsNotNone(seller)
        
        # Vérifier l'ID du vendeur
        party_id = seller.find('.//PartyIdentifier')
        self.assertEqual(party_id.text, '12345678')
        self.assertEqual(party_id.get('type'), 'MF')
        
        # Vérifier le nom du vendeur
        self.assertEqual(seller.find('.//PartyName').text, 'Société Vendeur SARL')
        
        # Vérifier l'adresse
        self.assertEqual(seller.find('.//StreetName').text, '123 Rue du Commerce')
        self.assertEqual(seller.find('.//CityName').text, 'Tunis')
        self.assertEqual(seller.find('.//PostalZone').text, '1000')
        self.assertEqual(seller.find('.//CountryCode').text, 'TN')
        
        # Vérifier les références
        refs = {ref.find('ReferenceType').text: ref.find('ReferenceValue').text 
                for ref in seller.findall('.//Rff')}
        self.assertEqual(refs['RC'], 'A12345678')
        self.assertEqual(refs['MF'], '12345678')
        
        # Vérifier les contacts
        contacts = {cta.find('ContactType').text: cta.find('ContactValue').text
                   for cta in seller.findall('.//Cta')}
        self.assertEqual(contacts['Téléphone'], '+216 71 123 456')
        self.assertEqual(contacts['Email'], 'contact@vendeur.tn')

    def test_create_buyer_party(self):
        """Test creating a buyer party section."""
        buyer_data = {
            'id': '87654321',
            'type': 'CIN',
            'name': 'Client Particulier',
            'address': {
                'street': '456 Avenue Habib Bourguiba',
                'city': 'Sousse',
                'postal_code': '4000',
                'country': 'TN'
            }
        }
        
        add_buyer_party(self.parent, buyer_data)
        
        # Vérifier l'élément acheteur
        buyer = self.parent.find('BuyerParty')
        self.assertIsNotNone(buyer)
        self.assertEqual(buyer.find('.//PartyIdentifier').text, '87654321')
        self.assertEqual(buyer.find('.//PartyName').text, 'Client Particulier')

    def test_create_delivery_party(self):
        """Test creating a delivery party section."""
        delivery_data = {
            'name': 'Entrepôt Principal',
            'address': {
                'street': '789 Zone Industrielle',
                'city': 'Sfax',
                'postal_code': '3000',
                'country': 'TN'
            }
        }
        
        add_delivery_party(self.parent, delivery_data)
        
        # Vérifier l'élément livraison
        delivery = self.parent.find('DeliveryParty')
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.find('.//PartyName').text, 'Entrepôt Principal')
        self.assertEqual(delivery.find('.//CityName').text, 'Sfax')

    def test_create_partner_minimal(self):
        """Test creating a partner section with minimal data."""
        partner_data = {
            'name': 'Partenaire Minimal',
            'id': 'MIN123'
        }
        
        create_partner_section(self.parent, partner_data, 'Test')
        
        # Vérifier que seuls les champs fournis sont présents
        test_party = self.parent.find('TestParty')
        self.assertIsNotNone(test_party)
        self.assertIsNone(test_party.find('.//StreetName'))
        self.assertIsNone(test_party.find('.//Rff'))

def generate_sample_partner_xml():
    """Generate a sample XML with partner sections."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    header = ET.SubElement(root, 'InvoiceHeader')
    
    # Ajouter un vendeur
    seller_data = {
        'id': '12345678',
        'type': 'MF',
        'name': 'Société Vendeur SARL',
        'address': {
            'street': '123 Rue du Commerce',
            'city': 'Tunis',
            'postal_code': '1000',
            'country': 'TN'
        },
        'references': {
            'RC': 'A12345678',
            'MF': '12345678'
        },
        'contacts': {
            'Téléphone': '+216 71 123 456',
            'Email': 'contact@vendeur.tn'
        }
    }
    add_seller_party(header, seller_data)
    
    # Ajouter un acheteur
    buyer_data = {
        'id': '87654321',
        'type': 'CIN',
        'name': 'Client Particulier',
        'address': {
            'street': '456 Avenue Habib Bourguiba',
            'city': 'Sousse',
            'postal_code': '4000',
            'country': 'TN'
        }
    }
    add_buyer_party(header, buyer_data)
    
    # Formater le XML pour une meilleure lisibilité
    return minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des partenaires TEIF ===")
    print(generate_sample_partner_xml())
