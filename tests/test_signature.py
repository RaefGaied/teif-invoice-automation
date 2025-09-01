"""
Test module for TEIF digital signature functionality.
"""
import os
import unittest
import sys
import pytest
from pathlib import Path
from lxml import etree as ET

# Add the parent directory to the path to import the module
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.teif.sections.signature import SignatureSection, SignatureError
    CRYPTO_AVAILABLE = True
except ImportError as e:
    CRYPTO_AVAILABLE = False
    print(f"Warning: Could not import required modules: {e}")
    print("Some tests will be skipped.")

# Skip tests if cryptography is not available
pytestmark = pytest.mark.skipif(
    not CRYPTO_AVAILABLE,
    reason="Cryptography library not available"
)

class TestSignatureSection(unittest.TestCase):
    """Test cases for SignatureSection class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Create test directory if it doesn't exist
        cls.test_dir = Path(__file__).parent / 'test_data'
        cls.test_dir.mkdir(exist_ok=True)
        
        # Paths for test certificate and key
        cls.cert_path = cls.test_dir / 'test_cert.pem'
        cls.key_path = cls.test_dir / 'test_key.pem'
        
        # Create test certificate and key if they don't exist
        cls._create_test_certificate()
        
        # Create a minimal XML document for testing (without XML declaration)
        cls.test_xml = """
        <TEIF xmlns="http://www.tradenet.tn/teif">
            <Header>
                <InvoiceNumber>INV-2023-001</InvoiceNumber>
                <IssueDate>2023-01-01</IssueDate>
            </Header>
            <Body>
                <TotalAmount>1000.00</TotalAmount>
            </Body>
        </TEIF>"""
    
    @classmethod
    def _create_test_certificate(cls):
        """Create a test certificate and private key if they don't exist."""
        # Create test directory if it doesn't exist
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        
        if cls.cert_path.exists() and cls.key_path.exists():
            return
            
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from datetime import datetime, timedelta
            
            # Generate private key
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Generate self-signed certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, u"TN"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Test Organization"),
                x509.NameAttribute(NameOID.COMMON_NAME, u"test.example.com"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).sign(key, hashes.SHA256())
            
            # Write certificate
            with open(cls.cert_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write private key
            with open(cls.key_path, 'wb') as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
                
        except ImportError as e:
            print(f"Warning: Could not create test certificate: {e}")
            raise unittest.SkipTest("Cryptography library not available")
        except Exception as e:
            print(f"Error creating test certificate: {e}")
            raise
    
    def setUp(self):
        """Set up test case."""
        self.section = SignatureSection()
        
    def test_add_signature(self):
        """Test adding a signature to the section."""
        with open(self.cert_path, 'rb') as f:
            cert_data = f.read()
        
        # Add signature
        self.section.add_signature(
            cert_data=cert_data,
            signature_id='SigFrs',
            role='Fournisseur',
            name='Test Provider',
            date='2023-01-01T12:00:00Z'
        )
        
        # Verify signature was added
        self.assertEqual(len(self.section.signatures), 1)
        self.assertEqual(self.section.signatures[0].get('signature_id'), 'SigFrs')
        self.assertEqual(self.section.signatures[0].get('role'), 'Fournisseur')
        self.assertEqual(self.section.signatures[0].get('name'), 'Test Provider')
    
    def test_to_xml(self):
        """Test XML generation."""
        with open(self.cert_path, 'rb') as f:
            cert_data = f.read()
        
        # Add signature
        self.section.add_signature(
            cert_data=cert_data,
            signature_id='SigFrs',
            name='Test Signer',
            role='Fournisseur',
            date='2023-01-01T12:00:00Z'
        )
        
        # Generate XML
        root = ET.Element('TEIF', {
            'xmlns': 'http://www.tradenet.tn/teif'
        })
        self.section.to_xml(root)
        
        # Verify XML structure
        signature = root.find(
            './/ds:Signature', 
            namespaces={'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        )
        self.assertIsNotNone(signature)
        self.assertEqual(signature.get('Id'), 'SigFrs')
        
        # Verify XAdES structure
        qualifying_properties = signature.find(
            './/xades:QualifyingProperties',
            namespaces={'xades': 'http://uri.etsi.org/01903/v1.3.2#'}
        )
        self.assertIsNotNone(qualifying_properties)
    
    def test_invalid_certificate(self):
        """Test with invalid certificate data."""
        # Test with completely invalid certificate data
        with self.assertRaises(SignatureError):
            self.section.add_signature(
                cert_data=b'invalid certificate data',
                signature_id='SigFrs'
            )
        
        # Test with malformed PEM data (missing BEGIN/END CERTIFICATE)
        with self.assertRaises(SignatureError):
            self.section.add_signature(
                cert_data=b'NOT A VALID CERTIFICATE',
                signature_id='SigFrs'
            )
    
    @unittest.skipIf(not os.path.exists('tests/test_data/test_cert.pem'), "Test certificate not found")
    def test_sign_document(self):
        """Test document signing."""
        # Parse test XML
        parser = ET.XMLParser(remove_blank_text=True)
        doc = ET.fromstring(self.test_xml.strip(), parser=parser)
        
        # Remove existing SignatureSection if any
        for elem in doc.findall('SignatureSection'):
            doc.remove(elem)
        
        # Load test certificate and key
        with open(self.cert_path, 'rb') as cert_file, \
             open(self.key_path, 'rb') as key_file:
            cert_data = cert_file.read()
            key_data = key_file.read()
            
            # Add signature with key
            self.section.add_signature(
                cert_data=cert_data,
                key_data=key_data,
                signature_id='SigFrs',
                name='Test Signer',
                role='Fournisseur',
                date='2023-01-01T12:00:00Z'
            )
            
            # Add signature to document
            self.section.to_xml(doc)
            
            # Verify the signature was added
            signature = doc.find(
                './/ds:Signature', 
                namespaces={'ds': 'http://www.w3.org/2000/09/xmldsig#'}
            )
            self.assertIsNotNone(signature)


if __name__ == '__main__':
    unittest.main()
