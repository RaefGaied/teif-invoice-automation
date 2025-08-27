"""
Test module for TEIF references section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.references import (
    create_reference,
    add_ttn_reference,
    add_document_reference
)

class TestReferencesSection(unittest.TestCase):
    """Test cases for the references section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        # Sample QR code (minimal valid base64-encoded 1x1 transparent PNG)
        self.sample_qr = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    def test_create_reference_basic(self):
        """Test creating a basic reference."""
        ref_data = {
            'type': 'PO',
            'value': 'CMD20230001',
            'format': 'string'
        }
        
        ref_elem = create_reference(self.parent, ref_data)
        
        # Vérifier la structure de base
        self.assertEqual(ref_elem.tag, 'Reference')
        self.assertEqual(ref_elem.find('ReferenceType').text, 'PO')
        self.assertEqual(ref_elem.find('ReferenceValue').text, 'CMD20230001')
        self.assertEqual(ref_elem.get('format'), 'string')

    def test_add_ttn_reference_basic(self):
        """Test adding a basic TTN reference."""
        ref_data = {
            'number': 'FAC20230001',
            'type': 'FACTURE',
            'date': '230101',
            'qr_code': self.sample_qr
        }
        
        add_ttn_reference(self.parent, ref_data)
        
        # Vérifier l'élément racine
        ttn_ref = self.parent.find('TTNReference')
        self.assertIsNotNone(ttn_ref)
        
        # Vérifier les champs de base
        self.assertEqual(ttn_ref.find('ReferenceType').text, 'FACTURE')
        self.assertEqual(ttn_ref.find('ReferenceNumber').text, 'FAC20230001')
        self.assertEqual(ttn_ref.find('ReferenceDate').text, '230101')
        
        # Vérifier le QR code
        qr_elem = ttn_ref.find('QRCode')
        self.assertIsNotNone(qr_elem)
        self.assertEqual(qr_elem.get('mimeCode'), 'image/png')
        self.assertTrue(qr_elem.text.startswith('data:image/png;base64,'))

    def test_add_document_reference(self):
        """Test adding a document reference."""
        doc_data = {
            'id': 'DOC123',
            'type': 'I-201',  # Facture d'origine
            'date': '2023-01-15',
            'description': 'Facture originale'
        }
        
        add_document_reference(self.parent, doc_data)
        
        # Vérifier l'élément racine
        doc_ref = self.parent.find('DocumentReference')
        self.assertIsNotNone(doc_ref)
        
        # Vérifier les champs
        self.assertEqual(doc_ref.find('DocumentTypeCode').text, 'I-201')
        self.assertEqual(doc_ref.find('ID').text, 'DOC123')
        self.assertEqual(doc_ref.find('IssueDate').text, '2023-01-15')
        self.assertEqual(doc_ref.find('DocumentDescription').text, 'Facture originale')

    def test_add_ttn_reference_minimal(self):
        """Test adding a TTN reference with minimal data."""
        ref_data = {'number': 'MIN123'}
        add_ttn_reference(self.parent, ref_data)
        
        ttn_ref = self.parent.find('TTNReference')
        self.assertIsNotNone(ttn_ref)
        self.assertEqual(ttn_ref.find('ReferenceType').text, 'TTNREF')
        self.assertEqual(ttn_ref.find('ReferenceNumber').text, 'MIN123')
        self.assertIsNone(ttn_ref.find('ReferenceDate'))
        self.assertIsNone(ttn_ref.find('QRCode'))

def generate_sample_references_xml():
    """Generate a sample XML with reference sections."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    header = ET.SubElement(root, 'InvoiceHeader')
    
    # Add references section
    refs = ET.SubElement(header, 'References')
    
    # Add TTN reference
    add_ttn_reference(refs, {
        'number': 'FAC20230001',
        'type': 'FACTURE',
        'date': '230101',
        'qr_code': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
    })
    
    # Add document reference
    add_document_reference(refs, {
        'id': 'CMD20230001',
        'type': 'I-202',  # Commande client
        'date': '2022-12-15',
        'description': 'Commande client n°2022-001'
    })
    
    # Add custom reference
    create_reference(refs, {
        'type': 'BL',
        'value': 'BL20230001',
        'format': 'string'
    })
    
    # Format the XML for better readability
    return minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des références TEIF ===")
    print(generate_sample_references_xml())
