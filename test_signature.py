"""
Test module for TEIF signature section.
"""
import sys
import os
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.dom import minidom

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from teif.sections.signature import (
    create_signature,
    add_signature,
    SignatureError
)

class TestSignatureSection(unittest.TestCase):
    """Test cases for the signature section of TEIF documents."""

    def setUp(self):
        """Set up test fixtures."""
        self.parent = ET.Element('TestRoot')
        self.sample_date = datetime(2023, 1, 1, 12, 0, 0)

    def test_create_signature_basic(self):
        """Test creating a basic signature element."""
        sig_data = {
            'id': 'SIG-001',
            'type': 'XAdES',
            'timestamp': self.sample_date.isoformat() + 'Z',
            'signer_info': {
                'Name': 'Test Signer',
                'Role': 'Signer'
            }
        }
        
        sig_elem = create_signature(self.parent, sig_data)
        
        # Verify basic structure
        self.assertEqual(sig_elem.tag, 'Signature')
        self.assertEqual(sig_elem.get('Id'), 'SIG-001')
        
        # Verify signature type
        self.assertEqual(sig_elem.find('SignatureType').text, 'XAdES')
        
        # Verify signer info
        signer_info = sig_elem.find('SignerInfo')
        self.assertIsNotNone(signer_info)
        self.assertEqual(signer_info.find('Name').text, 'Test Signer')
        self.assertEqual(signer_info.find('Role').text, 'Signer')

    def test_add_signature_minimal(self):
        """Test adding a minimal signature."""
        cert_data = {
            'cert': 'dummy_cert_data',
            'key': 'dummy_key_data'
        }
        
        # This will fail because of dummy data
        with self.assertRaises(SignatureError):
            add_signature(self.parent, cert_data)
            
        # Since we can't properly test add_signature without real certs,
        # we'll just verify that the function can be called without syntax errors
        # and that it raises the expected exception with dummy data
        self.assertTrue(True)  # Just to have an assertion

def generate_sample_signature_xml():
    """Generate a sample XML with signature section."""
    root = ET.Element('TEIF', version='1.8.8', controllingAgency='TTN')
    
    # Add a sample signature
    signature = ET.SubElement(root, 'Signature', Id='SIG-001')
    
    # Add signature type
    ET.SubElement(signature, 'SignatureType').text = 'XAdES'
    
    # Add timestamp
    ET.SubElement(signature, 'SignatureTimestamp').text = '2023-01-01T12:00:00Z'
    
    # Add signer information
    signer_info = ET.SubElement(signature, 'SignerInformation')
    ET.SubElement(signer_info, 'SignerRole', code='SIGNER').text = 'Signataire'
    ET.SubElement(signer_info, 'SignerName').text = 'Société Test'
    
    # Add signing time
    ET.SubElement(signature, 'SigningTime').text = '2023-01-01T12:00:00Z'
    
    # Add certificate info
    cert_info = ET.SubElement(signature, 'SigningCertificate')
    ET.SubElement(cert_info, 'CertDigest').text = 'A1B2C3D4E5F6...'
    ET.SubElement(cert_info, 'CertValue').text = 'MIIE...'  # Truncated for brevity
    
    # Format the XML for better readability
    return minidom.parseString(ET.tostring(root, encoding='utf-8'))\
             .toprettyxml(indent="    ")

if __name__ == '__main__':
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Show sample XML
    print("\n=== Exemple de sortie XML des signatures TEIF ===")
    print(generate_sample_signature_xml())
