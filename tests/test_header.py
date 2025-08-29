"""
Test module for TEIF 1.8.8 Header Section

This module contains tests for the header section of TEIF documents.
"""
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from teif.sections.header import (
    create_header_element, 
    create_bgm_element,
    create_dtm_element,
    validate_tax_identifier
)

class TestTaxIDValidation(unittest.TestCase):
    """Test cases for tax identifier validation."""
    
    def test_valid_tax_ids(self):
        """Test valid tax identifiers."""
        valid_ids = [
            '1234567AAM001',  # Company
            '9876543PPC002',  # Professional
            '1111111BBN000'   # Non-profit
        ]
        for tax_id in valid_ids:
            with self.subTest(tax_id=tax_id):
                validate_tax_identifier(tax_id)
    
    def test_invalid_tax_ids(self):
        """Test invalid tax identifiers."""
        invalid_cases = [
            ('123456', "Trop court"),
            ('1234567890123456', "Trop long"),
            ('1234567IIN001', "Caractère de contrôle invalide (I)"),
            ('1234567OON001', "Caractère de contrôle invalide (O)"),
            ('1234567UUN001', "Caractère de contrôle invalide (U)"),
            ('1234567XXN001', "Code TVA invalide"),
            ('1234567AAX001', "Code catégorie invalide"),
            ('1234567AAMABC', "Numéro d'établissement invalide"),
            ('1234567AAE000', "Établissement secondaire avec numéro 000")
        ]
        for tax_id, reason in invalid_cases:
            with self.subTest(tax_id=tax_id, reason=reason):
                with self.assertRaises(ValueError):
                    validate_tax_identifier(tax_id)

class TestHeaderSection(unittest.TestCase):
    """Test cases for the InvoiceHeader section."""
    
    def test_create_minimal_header(self):
        """Test creating header with required fields only."""
        header_data = {'sender_identifier': '1234567AAM001'}
        header = create_header_element(header_data)
        
        self.assertEqual(header.tag, 'InvoiceHeader')
        sender = header.find('MessageSenderIdentifier')
        self.assertEqual(sender.get('type'), 'I-01')
        self.assertEqual(sender.text, '1234567AAM001')
        self.assertIsNone(header.find('MessageRecieverIdentifier'))
    
    def test_create_header_with_receiver(self):
        """Test creating header with receiver information."""
        header_data = {
            'sender_identifier': '1234567AAM001',
            'receiver_identifier': '9876543PPC002',
            'receiver_identifier_type': 'I-01'
        }
        header = create_header_element(header_data)
        
        receiver = header.find('MessageRecieverIdentifier')
        self.assertEqual(receiver.get('type'), 'I-01')
        self.assertEqual(receiver.text, '9876543PPC002')
    
    def test_header_validation(self):
        """Test header validation."""
        with self.assertRaises(ValueError):
            create_header_element({})  # Missing sender_identifier
            
        with self.assertRaises(ValueError):
            create_header_element({'sender_identifier': 'INVALID'})  # Invalid tax ID

class TestBGMSection(unittest.TestCase):
    """Test cases for the BGM (Document Identification) section."""
    
    def test_create_minimal_bgm(self):
        """Test creating BGM with required fields only."""
        root = ET.Element('TestRoot')
        bgm_data = {
            'document_number': 'FAC-2023-001',
            'document_type': 'I-11'
        }
        bgm = create_bgm_element(root, bgm_data)
        
        self.assertEqual(bgm.tag, 'Bgm')
        self.assertEqual(bgm.find('DocumentIdentifier').text, 'FAC-2023-001')
        doc_type = bgm.find('DocumentType')
        self.assertEqual(doc_type.get('code'), 'I-11')
        self.assertIsNone(bgm.find('DocumentReferences'))
    
    def test_create_bgm_with_references(self):
        """Test creating BGM with document references."""
        root = ET.Element('TestRoot')
        bgm_data = {
            'document_number': 'FAC-2023-001',
            'document_type': 'I-11',
            'document_type_label': 'Facture',
            'references': [
                {
                    'reference': 'CMD-2023-123',
                    'reference_type': 'ON',
                    'reference_date': '20230815'
                },
                {
                    'reference': 'CT-2023-456',
                    'reference_type': 'CT'
                }
            ]
        }
        bgm = create_bgm_element(root, bgm_data)
        
        refs = bgm.find('DocumentReferences')
        self.assertEqual(len(refs.findall('DocumentReference')), 2)
        
        # Verify first reference
        ref1 = refs.findall('DocumentReference')[0]
        self.assertEqual(ref1.find('Reference').text, 'CMD-2023-123')
        self.assertEqual(ref1.find('Reference').get('type'), 'ON')
        self.assertEqual(ref1.find('ReferenceDate').text, '20230815')
        
        # Verify second reference
        ref2 = refs.findall('DocumentReference')[1]
        self.assertEqual(ref2.find('Reference').text, 'CT-2023-456')
        self.assertEqual(ref2.find('Reference').get('type'), 'CT')
        self.assertIsNone(ref2.find('ReferenceDate'))
    
    def test_bgm_validation(self):
        """Test BGM validation."""
        root = ET.Element('TestRoot')
        
        with self.assertRaises(ValueError):
            create_bgm_element(root, {})  # Missing required fields
            
        with self.assertRaises(ValueError):
            create_bgm_element(root, {
                'document_number': 'X' * 71,  # Too long
                'document_type': 'I-11'
            })

class TestDTMSection(unittest.TestCase):
    """Test cases for the DTM (Date/Time/Period) section."""
    
    def test_create_dtm(self):
        """Test creating DTM element."""
        root = ET.Element('TestRoot')
        dtm_data = {
            'date_text': '150823',
            'function_code': 'I-31',
            'format': 'ddMMyy'
        }
        dtm = create_dtm_element(root, dtm_data)
        
        self.assertEqual(dtm.tag, 'Dtm')
        date_text = dtm.find('DateText')
        self.assertEqual(date_text.text, '150823')
        self.assertEqual(date_text.get('functionCode'), 'I-31')
        self.assertEqual(date_text.get('format'), 'ddmmyy')
    
    def test_dtm_validation(self):
        """Test DTM validation."""
        root = ET.Element('TestRoot')
        
        with self.assertRaises(ValueError):
            create_dtm_element(root, {})  # Missing required fields
            
        with self.assertRaises(ValueError):
            create_dtm_element(root, {
                'date_text': '150823',
                'function_code': 'INVALID',
                'format': 'ddMMyy'
            })

class TestFullDocumentGeneration(unittest.TestCase):
    """Test full TEIF document generation."""
    
    def test_generate_teif_document(self):
        """Test generating a complete TEIF document."""
        # Create root element
        teif = ET.Element('TEIF', {
            'version': '1.8.8',
            'controllingAgency': 'TTN'
        })
        
        # Add header
        header = create_header_element({
            'sender_identifier': '1234567AAM001',
            'receiver_identifier': '9876543PPC002'
        })
        teif.append(header)
        
        # Add invoice body
        invoice_body = ET.SubElement(teif, 'InvoiceBody')
        
        # Add BGM
        bgm = create_bgm_element(ET.Element('Temp'), {
            'document_number': 'FAC-2023-001',
            'document_type': 'I-11',
            'document_type_label': 'Facture',
            'references': [{'reference': 'CMD-2023-123', 'reference_type': 'ON'}]
        })
        invoice_body.append(bgm)
        
        # Add DTM
        dtm = create_dtm_element(ET.Element('Temp'), {
            'date_text': '150823',
            'function_code': 'I-31',
            'format': 'ddMMyy'
        })
        invoice_body.append(dtm)
        
        # Convert to string for assertions
        xml_str = ET.tostring(teif, encoding='unicode')
        
        # Verify structure
        self.assertIn('<TEIF version="1.8.8" controllingAgency="TTN">', xml_str)
        self.assertIn('<MessageSenderIdentifier type="I-01">1234567AAM001</MessageSenderIdentifier>', xml_str)
        self.assertIn('<DocumentIdentifier>FAC-2023-001</DocumentIdentifier>', xml_str)
        self.assertIn('<DateText functionCode="I-31" format="ddmmyy">150823</DateText>', xml_str)

if __name__ == '__main__':
    unittest.main()
