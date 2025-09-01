"""
Tests for XAdES-B signature generation and validation.
"""
import os
import unittest
import tempfile
from datetime import datetime
from lxml import etree
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes

from src.teif.sections.signature import SignatureSection, SignatureError

class TestXAdESSignature(unittest.TestCase):    
    @classmethod
    def setUpClass(cls):
        """Create test certificate and key pair."""
        # Generate a test private key
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create a self-signed certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "TN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tunis"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Tunis"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
        ])
        
        cls.cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            cls.private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + datetime.timedelta(days=365)
        ).sign(
            cls.private_key, 
            hashes.SHA256()
        )
        
        # Convert to PEM format
        cls.private_key_pem = cls.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        cls.cert_pem = cls.cert.public_bytes(
            encoding=serialization.Encoding.PEM
        )
    
    def test_xades_signature_creation(self):
        """Test creating a XAdES-B signature."""
        # Create a test XML document
        root = etree.Element("TestDocument")
        etree.SubElement(root, "Data").text = "Test content"
        
        # Create signature section
        sig_section = SignatureSection()
        
        # Add a signature
        sig_section.add_signature(
            cert_data=self.cert_pem,
            key_data=self.private_key_pem,
            signature_id="TestSig1",
            role="supplier",
            name="Test Signer"
        )
        
        # Generate the signature XML
        signature = sig_section.to_xml()
        
        # Verify the signature structure
        self.assertIsNotNone(signature)
        self.assertEqual(signature.tag, f'{{http://www.w3.org/2000/09/xmldsig#}}Signature')
        
        # Check for required elements
        self.assertIsNotNone(signature.find(f'.//{{http://www.w3.org/2000/09/xmldsig#}}SignedInfo'))
        self.assertIsNotNone(signature.find(f'.//{{http://www.w3.org/2000/09/xmldsig#}}SignatureValue'))
        self.assertIsNotNone(signature.find(f'.//{{http://uri.etsi.org/01903/v1.3.2#}}SignedProperties'))
        
        # Check the signature policy identifier
        sig_policy_id = signature.find(
            './/{http://uri.etsi.org/01903/v1.3.2#}SignaturePolicyIdentifier/' +
            '{http://uri.etsi.org/01903/v1.3.2#}SignaturePolicyId/' +
            '{http://uri.etsi.org/01903/v1.3.2#}SigPolicyId/' +
            '{http://uri.etsi.org/01903/v1.3.2#}Identifier'
        )
        self.assertIsNotNone(sig_policy_id)
        self.assertEqual(sig_policy_id.text, "urn:oid:1.3.6.1.4.1.15021.1.2.1")
    
    def test_xades_sign_document(self):
        """Test signing a complete XML document."""
        # Create a test XML document
        root = etree.Element("TestDocument")
        etree.SubElement(root, "Data").text = "Test content"
        
        # Create signature section
        sig_section = SignatureSection()
        
        # Add a signature
        sig_section.add_signature(
            cert_data=self.cert_pem,
            key_data=self.private_key_pem,
            signature_id="TestSig2",
            role="supplier",
            name="Test Signer"
        )
        
        # Sign the document
        sig_section.sign_document(root)
        
        # Verify the signature was added
        signature = root.find(f'.//{{http://www.w3.org/2000/09/xmldsig#}}Signature')
        self.assertIsNotNone(signature)
        
        # Verify the signature value was set
        sig_value = signature.find(f'.//{{http://www.w3.org/2000/09/xmldsig#}}SignatureValue')
        self.assertIsNotNone(sig_value)
        self.assertNotEqual(sig_value.text, '')
    
    def test_invalid_certificate(self):
        """Test with an invalid certificate."""
        sig_section = SignatureSection()
        
        with self.assertRaises(SignatureError):
            sig_section.add_signature(
                cert_data=b"INVALID CERTIFICATE DATA",
                key_data=self.private_key_pem,
                signature_id="TestSig3"
            )
    
    def test_missing_key_data(self):
        """Test signing without providing key data."""
        sig_section = SignatureSection()
        
        # Should be able to create signature without key data
        sig_section.add_signature(
            cert_data=self.cert_pem,
            signature_id="TestSig4"
        )
        
        # But signing should fail
        with self.assertRaises(ValueError):
            sig_section.sign_document(etree.Element("Test"))

if __name__ == "__main__":
    unittest.main()
