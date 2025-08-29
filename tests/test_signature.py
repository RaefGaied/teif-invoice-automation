"""
Test module for TEIF digital signature functionality.
"""
import os
import unittest
from pathlib import Path
import base64
from lxml import etree

# Add the parent directory to the path to import the module
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.teif.sections.signature import sign_xml, SignatureError

class TestTEIFSigner(unittest.TestCase):
    """Test cases for TEIF signature functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Read test certificate and key from files
        test_dir = Path(__file__).parent
        with open(test_dir / 'test_cert.pem', 'rb') as f:
            cls.test_cert = f.read()
            
        with open(test_dir / 'test_key.pem', 'rb') as f:
            cls.test_key = f.read()
            
        # Create output directory for test files
        cls.test_output_dir = Path(__file__).parent / "test_output"
        cls.test_output_dir.mkdir(exist_ok=True)
    
    def test_sign_xml_complete(self):
        """Test the complete XML signing process."""
        try:
            # Define namespaces
            ns = {
                'ds': 'http://www.w3.org/2000/09/xmldsig#',
                'xades': 'http://uri.etsi.org/01903/v1.3.2#'
            }
            
            # Create a minimal valid XML document with XAdES signature placeholder
            xml_template = """<?xml version="1.0" encoding="UTF-8"?>
            <TEIF xmlns="urn:tunisie:teif:1.0.0">
                <Header>
                    <DocumentID>INV-2023-001</DocumentID>
                    <IssueDate>2023-11-01</IssueDate>
                </Header>
                <Body>
                    <Invoice>
                        <InvoiceNumber>INV-2023-001</InvoiceNumber>
                        <TotalAmount>1000.00</TotalAmount>
                    </Invoice>
                </Body>
                <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" 
                           xmlns:xades="http://uri.etsi.org/01903/v1.3.2#"
                           Id="Signature">
                    <ds:SignedInfo>
                        <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
                        <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
                        <ds:Reference Id="r-id-frs" URI="">
                            <ds:Transforms>
                                <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
                            </ds:Transforms>
                            <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                            <ds:DigestValue></ds:DigestValue>
                        </ds:Reference>
                        <ds:Reference Type="http://uri.etsi.org/01903#SignedProperties" URI="#xades-SigFrs">
                            <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                            <ds:DigestValue></ds:DigestValue>
                        </ds:Reference>
                    </ds:SignedInfo>
                    <ds:SignatureValue></ds:SignatureValue>
                    <ds:KeyInfo>
                        <ds:X509Data>
                            <ds:X509Certificate></ds:X509Certificate>
                        </ds:X509Data>
                    </ds:KeyInfo>
                    <ds:Object>
                        <xades:QualifyingProperties Target="#Signature">
                            <xades:SignedProperties Id="xades-SigFrs">
                                <xades:SignedSignatureProperties>
                                    <xades:SigningTime>2023-01-01T00:00:00Z</xades:SigningTime>
                                    <xades:SigningCertificate>
                                        <xades:Cert>
                                            <xades:CertDigest>
                                                <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                                                <ds:DigestValue></ds:DigestValue>
                                            </xades:CertDigest>
                                            <xades:IssuerSerial>
                                                <ds:X509IssuerName>CN=Test CA</ds:X509IssuerName>
                                                <ds:X509SerialNumber>1</ds:X509SerialNumber>
                                            </xades:IssuerSerial>
                                        </xades:Cert>
                                    </xades:SigningCertificate>
                                </xades:SignedSignatureProperties>
                            </xades:SignedProperties>
                        </xades:QualifyingProperties>
                    </ds:Object>
                </ds:Signature>
            </TEIF>
            """
            
            # Sign the XML
            signed_xml = sign_xml(
                xml_template,
                self.test_cert,
                self.test_key
            )
            
            # Parse the signed XML
            root = etree.fromstring(signed_xml if isinstance(signed_xml, bytes) else signed_xml.encode('utf-8'))
            
            # Check that the signature is valid
            signature = root.find('.//ds:Signature', namespaces=ns)
            self.assertIsNotNone(signature, "Signature element not found")
            
            # Check for required elements
            signed_info = signature.find('.//ds:SignedInfo', namespaces=ns)
            self.assertIsNotNone(signed_info, "SignedInfo element not found")
            
            # Check digest values
            digest = signed_info.find('.//ds:DigestValue', namespaces=ns)
            self.assertIsNotNone(digest, "DigestValue not found")
            self.assertTrue(digest.text and len(digest.text) > 0, "DigestValue is empty")
            
            # Check signature value
            sig_value = signature.find('.//ds:SignatureValue', namespaces=ns)
            self.assertIsNotNone(sig_value, "SignatureValue element not found")
            self.assertTrue(sig_value.text and len(sig_value.text) > 0, 
                          "SignatureValue is empty")
            
            # Check certificate
            cert = signature.find('.//ds:X509Certificate', namespaces=ns)
            self.assertIsNotNone(cert, "X509Certificate element not found")
            self.assertTrue(cert.text and len(cert.text) > 0, 
                          "X509Certificate is empty")
            
            # Save the signed XML for inspection
            output_path = self.test_output_dir / "signed_invoice.xml"
            with open(output_path, 'wb') as f:
                f.write(signed_xml if isinstance(signed_xml, bytes) else signed_xml.encode('utf-8'))
                
        except Exception as e:
            self.fail(f"Error during XML signing: {str(e)}")
            raise  # Re-raise to see the full traceback in test output


if __name__ == '__main__':
    unittest.main()
