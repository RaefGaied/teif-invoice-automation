# XAdES Signature Implementation

This document describes the XAdES (XML Advanced Electronic Signatures) implementation for the TEIF (Tunisian Electronic Invoice Format) project.

## Overview

The XAdES implementation provides digital signature capabilities for TEIF documents, ensuring:
- Data integrity
- Non-repudiation
- Compliance with Tunisian e-invoicing standards (TTN 1.8.8)
- Support for XAdES-BES (Basic Electronic Signature) and XAdES-T (Timestamp)

## Features

- XAdES-BES signature generation and validation
- Support for RSA keys (2048-bit and 4096-bit)
- SHA-256 digest algorithm
- XML-DSIG Exclusive Canonicalization
- Tunisian signature policy OID integration
- Support for multiple signer roles

## Usage

### Adding a Signature

```python
from src.teif.sections.signature import SignatureSection

# Create a signature section
signature_section = SignatureSection()

# Add a signature with certificate and private key
with open('certificate.pem', 'rb') as f:
    cert_data = f.read()

with open('private_key.pem', 'rb') as f:
    key_data = f.read()

signature_section.add_signature(
    cert_data=cert_data,
    key_data=key_data,
    key_password='your_password',  # Optional
    signature_id='SIG-001',
    role='supplier',
    name='ACME Corp',
    date='2023-01-01T12:00:00Z'  # Optional, defaults to current time
)

# Sign an XML document
import xml.etree.ElementTree as ET
root = ET.Element('Invoice')
# ... add invoice data ...
signature_section.sign_document(root)

# Get the signed XML as string
signed_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
```

### Validating a Signature

```python
from lxml import etree
from signxml import XMLVerifier

# Load the signed XML
with open('signed_invoice.xml', 'rb') as f:
    xml_data = f.read()

# Verify the signature
verified_data = XMLVerifier().verify(
    xml_data,
    x509_cert='certificate.pem',
    expect_config=True,
    expect_repeated_attributes=False,
    ignore_ambiguous_time_not_z=True
)

print("Signature is valid:", verified_data.signed_xml is not None)
```

## Signature Format

The generated signature follows the XAdES-BES standard with the following structure:

```xml
<ds:Signature Id="SIG-001" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <ds:SignedInfo>
    <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
    <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
    <!-- References and transforms -->
  </ds:SignedInfo>
  <ds:SignatureValue>...</ds:SignatureValue>
  <ds:KeyInfo>
    <ds:X509Data>
      <ds:X509Certificate>...</ds:X509Certificate>
    </ds:X509Data>
  </ds:KeyInfo>
  <ds:Object>
    <xades:QualifyingProperties Target="#SIG-001" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
      <xades:SignedProperties Id="xades-SIG-001">
        <xades:SignedSignatureProperties>
          <xades:SigningTime>2023-01-01T12:00:00Z</xades:SigningTime>
          <xades:SigningCertificate>
            <xades:Cert>
              <xades:CertDigest>
                <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                <ds:DigestValue>...</ds:DigestValue>
              </xades:CertDigest>
              <xades:IssuerSerial>
                <ds:X509IssuerName>CN=Test CA,O=Test Org,C=TN</ds:X509IssuerName>
                <ds:X509SerialNumber>1234567890</ds:X509SerialNumber>
              </xades:IssuerSerial>
            </xades:Cert>
          </xades:SigningCertificate>
          <xades:SignaturePolicyIdentifier>
            <xades:SignaturePolicyId>
              <xades:SigPolicyId>
                <xades:Identifier Qualifier="OID">urn:oid:1.3.6.1.4.1.15021.1.2.1</xades:Identifier>
              </xades:SigPolicyId>
            </xades:SignaturePolicyId>
          </xades:SignaturePolicyIdentifier>
          <xades:SignerRole>
            <xades:ClaimedRoles>
              <xades:ClaimedRole>supplier</xades:ClaimedRole>
            </xades:ClaimedRoles>
          </xades:SignerRole>
        </xades:SignedSignatureProperties>
      </xades:SignedProperties>
    </xades:QualifyingProperties>
  </ds:Object>
</ds:Signature>
```

## Error Handling

The following exceptions may be raised during signature operations:

- `SignatureError`: Base exception for all signature-related errors
- `CertificateError`: Certificate validation or loading failed
- `KeyError`: Invalid or missing key material
- `XMLSyntaxError`: Invalid XML structure or syntax

## Dependencies

- Python 3.8+
- cryptography
- lxml
- pyOpenSSL
- signxml
- xmlsec
- python-xades

## References

- [ETSI TS 101 903 - XAdES](https://www.etsi.org/deliver/etsi_ts/101900_101999/101903/01.04.02_60/ts_101903v010402p.pdf)
- [W3C XML Signature Syntax and Processing](https://www.w3.org/TR/xmldsig-core1/)
- [Tunisian E-Invoicing Standard (TTN 1.8.8)](https://www.tunisiacommerce.gov.tn/)
