"""
Test module for TEIF header section.

This module contains tests for the header section of TEIF documents.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.header import (
    create_header_element, 
    create_bgm_element,
    create_dtm_element,
    DTM_FUNCTION_CODES
)

class TestHeaderSection(unittest.TestCase):
    """Test cases for the header section of TEIF documents."""

    def test_create_header_element_minimal(self):
        """Test creating a minimal header with required fields only."""
        # Test data with valid tax ID (9th char: A,P,B,F,N; 10th char: M,P,C,N,E)
        header_data = {
            'sender_identifier': '1234567AAM123'  # 9th char: 'A', 10th char: 'M'
        }
        
        # Create header element
        header = create_header_element(header_data)
        
        # Verify the root element
        self.assertEqual(header.tag, 'InvoiceHeader')
        
        # Verify sender identifier
        sender_elem = header.find('MessageSenderIdentifier')
        self.assertIsNotNone(sender_elem)
        self.assertEqual(sender_elem.text, '1234567AAM123')
        self.assertEqual(sender_elem.get('type'), 'I-01')

    def test_create_header_element_with_receiver(self):
        """Test creating a header with receiver information."""
        # Test data with valid tax IDs
        header_data = {
            'sender_identifier': '1234567BPP123',  # 9th char: 'P', 10th char: 'P'
            'receiver_identifier': '9876543CCN456',  # Receiver tax ID
            'receiver_identifier_type': 'I-01'  # Tax ID type
        }
        
        # Create header element
        header = create_header_element(header_data)
        
        # Verify sender and receiver elements
        self.assertEqual(header.find('MessageSenderIdentifier').text, '1234567BPP123')
        
        receiver_elem = header.find('MessageRecieverIdentifier')
        self.assertIsNotNone(receiver_elem)
        self.assertEqual(receiver_elem.text, '9876543CCN456')
        self.assertEqual(receiver_elem.get('type'), 'I-01')

    def test_create_header_element_missing_required(self):
        """Test creating a header with missing required fields."""
        with self.assertRaises(ValueError) as context:
            create_header_element({})
        self.assertIn('sender_identifier', str(context.exception))



class TestDocumentIdentification(unittest.TestCase):
    """Test cases for the document identification section (BGM)."""
    
    def test_create_bgm_element_full(self):
        """Test creating a full BGM element."""
        # Create a parent element
        parent = ET.Element('TestRoot')
        
        # Test data with valid document type and code
        bgm_data = {
            'document_number': 'INV-2023-001',
            'document_type': 'INVOICE',  # Using valid document type
            'document_type_code': '380',  # Standard invoice type code
            'references': [
                {'type': 'PO', 'value': 'PO-12345'},
                {'type': 'CT', 'value': 'CT-2023-001', 'date': '20230801'}
            ]
        }
        
        # Create BGM element
        bgm = create_bgm_element(parent, bgm_data)
        
        # Verify the root element
        self.assertEqual(bgm.tag, 'BGM')
        
        # Verify document identifier
        doc_id = bgm.find('DocumentIdentifier')
        self.assertIsNotNone(doc_id)
        self.assertEqual(doc_id.text, 'INV-2023-001')
        
        # Verify document type (should be the code, not the type name)
        doc_type = bgm.find('DocumentType')
        self.assertIsNotNone(doc_type)
        self.assertEqual(doc_type.text, '380')  # Should be the code, not 'INVOICE'
        
        # Verify references - check that references are added to the parent element
        refs = bgm.findall('DocumentReference')
        self.assertEqual(len(refs), 2)
        
        # Verify first reference (PO)
        ref1 = refs[0]
        ref1_type = ref1.find('DocumentTypeCode')
        ref1_value = ref1.find('DocumentIdentifier')
        self.assertIsNotNone(ref1_type)
        self.assertIsNotNone(ref1_value)
        self.assertEqual(ref1_type.text, 'PO')
        self.assertEqual(ref1_value.text, 'PO-12345')
        
        # Verify second reference (Contract with date)
        ref2 = refs[1]
        ref2_type = ref2.find('DocumentTypeCode')
        ref2_value = ref2.find('DocumentIdentifier')
        ref2_date = ref2.find('DocumentDate')
        
        self.assertIsNotNone(ref2_type)
        self.assertIsNotNone(ref2_value)
        self.assertIsNotNone(ref2_date)
        
        self.assertEqual(ref2_type.text, 'CT')
        self.assertEqual(ref2_value.text, 'CT-2023-001')
        self.assertEqual(ref2_date.text, '20230801')

class TestDTMSection(unittest.TestCase):
    """Test cases for the DTM (Date/Time/Period) section."""
    
    def test_create_dtm_element_full(self):
        """Test creating a complete DTM element."""
        # Create a parent element
        parent = ET.Element('TestRoot')
        
        # Test data
        dtm_data = {
            'date_text': '20230821',
            'function_code': '137',  # Invoice date
            'format': 'YYYYMMDD'
        }
        
        # Create DTM element
        dtm = create_dtm_element(parent, dtm_data)
        
        # Verify the DTM element
        self.assertEqual(dtm.tag, 'DTM')
        
        # Verify DateText element and its attributes
        date_text = dtm.find('DateText')
        self.assertIsNotNone(date_text)
        self.assertEqual(date_text.text, '20230821')
        self.assertEqual(date_text.get('functionCode'), '137')
        self.assertEqual(date_text.get('format'), 'YYYYMMDD')
    
    def test_create_dtm_element_minimal(self):
        """Test creating a DTM element with minimal required fields."""
        # Create a parent element
        parent = ET.Element('TestRoot')
        
        # Test data with only required fields
        dtm_data = {
            'date_text': '220823',
            'function_code': '137',
            'format': 'YYMMDD'
        }
        
        # Create DTM element
        dtm = create_dtm_element(parent, dtm_data)
        
        # Verify the DTM element
        date_text = dtm.find('DateText')
        self.assertEqual(date_text.text, '220823')
        self.assertEqual(date_text.get('functionCode'), '137')
        self.assertEqual(date_text.get('format'), 'YYMMDD')
    
    def test_create_dtm_element_invalid_function_code(self):
        """Test creating a DTM element with an invalid function code."""
        parent = ET.Element('TestRoot')
        dtm_data = {
            'date_text': '20230821',
            'function_code': 'INVALID',
            'format': 'YYYYMMDD'
        }
        
        with self.assertRaises(ValueError) as context:
            create_dtm_element(parent, dtm_data)
        self.assertIn('Invalid DTM function code', str(context.exception))
    
    def test_create_dtm_element_invalid_format(self):
        """Test creating a DTM element with an invalid format."""
        parent = ET.Element('TestRoot')
        dtm_data = {
            'date_text': '2023-08-21',
            'function_code': '137',
            'format': 'INVALID_FORMAT'
        }
        
        with self.assertRaises(ValueError) as context:
            create_dtm_element(parent, dtm_data)
        self.assertIn('Invalid DTM format', str(context.exception))


def generate_sample_header_xml():
    """Génère un exemple de fichier XML d'en-tête TEIF."""
    # Create root element
    teif = ET.Element('TEIF')
    teif.set('version', '1.8.8')
    teif.set('controllingAgency', 'TTN')
    
    # Create header (InvoiceHeader)
    header_data = {
        'message_id': 'MSG-2023-001',
        'sender_identifier': '1234567CBC123',  # 9th char: 'B', 10th char: 'C'
        'sender_identifier_type': 'TIN',  # Tax Identification Number
        'message_date': '2023-08-21T10:30:00Z',
        'version': '1.8.8',
        'controlling_agency': 'TTN',
        'test_indicator': '1',
        'sender_name': 'Test Company',
        'sender_country': 'TN',
        'sender_vat_number': '12345678',
        'sender_tax_system': 'VAT'
    }
    header = create_header_element(header_data)
    teif.append(header)
    
    # Add document identification (BGM)
    bgm_data = {
        'document_number': 'FAC-2023-001',
        'document_type': 'INVOICE',  # Using valid document type
        'document_type_code': '380',  # Standard invoice code
        'document_function_code': '9',  # Original document
        'references': [
            {'type': 'PO', 'value': 'PO-2023-123'},
            {'type': 'CT', 'value': 'CT-2023-456', 'date': '20230715'}
        ]
    }
    bgm = create_bgm_element(header, bgm_data)
    
    # Add invoice date (DTM)
    dtm_data = {
        'date_text': '20230821',
        'function_code': '137',  # Invoice date
        'format': 'YYYYMMDD'
    }
    create_dtm_element(header, dtm_data)
    
    # Add due date (DTM)
    due_date_data = {
        'date_text': '20230920',
        'function_code': '35',  # Payment due date
        'format': 'YYYYMMDD'
    }
    create_dtm_element(header, due_date_data)
    
    # Format and return the XML
    from xml.dom import minidom
    xml_str = minidom.parseString(ET.tostring(teif, encoding='utf-8')).toprettyxml(indent="    ")
    return xml_str


if __name__ == '__main__':
    # Exécuter les tests unitaires
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Afficher un exemple de sortie XML
    print("\n=== Exemple de sortie XML d'en-tête TEIF ===")
    print(generate_sample_header_xml())
