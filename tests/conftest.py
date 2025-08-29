"""
Test configuration and fixtures for TEIF signature tests.
"""
import pytest
from pathlib import Path

# Sample test data
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEIF xmlns="urn:tunisie:teif:1.0.0">
    <Header>
        <DocumentID>INV-2023-001</DocumentID>
        <IssueDate>2023-11-01</IssueDate>
        <DocumentType>INV</DocumentType>
    </Header>
    <Body>
        <Invoice>
            <InvoiceNumber>INV-2023-001</InvoiceNumber>
            <InvoiceDate>2023-11-01</InvoiceDate>
            <TotalAmount>1000.00</TotalAmount>
        </Invoice>
    </Body>
</TEIF>
"""

# Test certificate and key (for testing only)
TEST_CERT = """-----BEGIN CERTIFICATE-----
MIIFwTCCBCmgAwIBAgIIRZLo6uoLbQ4wDQYJKoZIhvcNAQELBQAwcDELMAkGA1UE
BhMCVE4xDjAMBgNVBAcMBVR1bmlzMS4wLAYDVQQKDCVOYXRpb25hbCBEaWdpdGFs
IENlcnRpZmljYXRpb24gQWdlbmN5MSEwHwYDVQQDDBhUblRydXN0IFF1YWxpZmll
ZCBHb3YgQ0EwHhcNMTcxMDE4MTQzMDQ4WhcNMTkxMDE4MTQzMDQ4WjBkMQswCQYD
VQQGEwJUTjEZMBcGA1UECgwQVFVOSVNJRSBUUkFETkVUMRAwDgYDVQQDDAdCT1Va
SURJMQ8wDQYDVQQKDAZIQVJJQkExFzAVBgNVBAMMDkhBQklCQSBDT01NRVJDQzCC
ASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMV7EUmFMqHZm+iB1iOXKBbK
u0C41X/IqyxalRyX+9sVDmFekXepGcjnsIST5ZQcq+vhl/HUW7aevub15wm66QAw
LF35X55w305yZNK3Vx1EmCF040/22UyXKxJRxXKWmYYfZzli6UKk0mFiRKULvFt/
2pYehF1q121uvvb+/9Wk1sDt2Vrp67MYvMowoKSs/reDs83rvARGk+H3ydAs9++F
INvIott0gryYyLtPxOZ75Ur4Gk15PePZTGDnzzGCgZM8VhZo8zeN+6FgK8QNlyE
YfD7bbeKVu4wMl1xZfld4MyMGOtsw16KUqi23cpQ+BjnTNR4fxRUIpEGjqkgliPM
CAwEAAaOCAekwggHlMDYGCCsGAQUFBwEBBCowKDAmBggrBgEFBQcwAYYaaHR0cD
ovL3ZhLmNlcnRpZmljYXRpb24udG4wHQYDVR0OBBYEFP3zo4J4TSsNDURUM7pl
RXGyiGkbMAwGA1UdEwEB/wQCMAAwHwYDVR0jBBgwFoAUcyQoJfoi9pKpFYOkLLPN
xsu0A1YwLAYDVR0gBCUwIzAJBgcEAIvsQAECMAwGCmCGFAECBgEKAQEwCAYGBACP
egECMEYGA1UdHwQ/MD0wO6A5oDeGNWh0dHA6Ly9jcmwuY2VydGlmaWNhdGlvbi50
bi90bnRydXN0cXVhbGlmaWVkZ292Y2EuY3JsMA4GA1UdDwEB/wQEAwIGwDApBgNV
HSUEIjAgBggrBgEFBQcDAgYIKwYBBQUHAwQGCisGAQQBgjcUAgIwKQYDVR0RBCIw
IIEeaGFyaWJhLmJvdXppZGlAdHJhZGVuZXQuY29tLnRuMIGABggrBgEFBQcBAwR0
MHIwCAYGBACORgEBMAgGBgQAjkYBBDATBgYEAI5GAQYwCQYHBACORgEGATBHBgYE
AI5GAQUwPTA7FjVodHRwOi8vd3d3LmNlcnRpZmljYXRpb24udG4vcHViL3Bkcy10
dW50cnVzdGdvdmNhLnBkZhMCZW4wDQYJKoZIhvcNAQELBQADggGBALcTGocPDIp7
DBQ6pGFNVhw9a1F0U3agYngyPRGkXf8lSHqxA8oZw8vrxEIkTpDG/EKVhmf2VOA/
aKaKlSyaBIzKiEvLKncrQRbTJ71SXnC1DW5Szr94EQRSzXbtQwGtB5ENWWliGcDV
OaUN8rnZO00orkDJMZy7t9vMFi3ZosKNybCSNceemySBKZiSqUXqzB1+bYEPRQHV
2rXoLXjPIzUdgY1UnmQZ2R2t0itxaDNPcQVIb4zgQwWfLwAhkJyuG9bT+l4pXH+
V0Fy5ti3GrVs0b7xF4VfQP3tj9LxIhAJ2eVeSUAA7tEWMCVbwp6Ob2E9F3hQPVQ
Hj6BGc6HyWsA8k/ON60ZjnE0kaddnMRp8P5E+Ruj9VhFgSmAK6WbxuUclFEZGzDG
oDbxiF7M/W7wNaXouazGe65KdJ45YnFpsQvvj2Zi7RusFLNQ0aCH8YWsUH1NK4Cf
yPwn+hnMhaWO1ipCKJJEEhKrB7UjymFO6DobULnPw/qKQcEMJDx1wZ3A==
-----END CERTIFICATE-----
"""

TEST_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDFexFJhTKh2Zvo
gdYjlygWyrtAuNV/yKssWpUcl/vbFQ5hXpF3qRnI57CEk+WUHKvr4Zfx1Fu2nr7m
9ecJuukAMCxd+V+ecN9OcmTSt1cdRJghdONP9tlMlysSUcVylpmGH2c5YulCpNJh
YkSlC7xbf9qWHoRdatdtbr72/v/VpNbA7dla6euzGLzKMKCkrP63g7PN67wERpPh
98nQLPfvhSDbyKLbdIK8mMi7T8Tme+VK+BpNeT3j2Uxg588xgoGTPFYWaPM3jfuh
YCvEDZchGHw+223ilbuMDJdcWX5XeDMjBjrbMNeilKott3KUPgY50zUeH8UVCKRB
o6pIJYjzAgMBAAECggEBAJwR5ZxXwqJx7QY5V8Kz8Q==
-----END PRIVATE KEY-----
"""

@pytest.fixture
def sample_xml():
    """Return a sample TEIF XML document for testing."""
    return SAMPLE_XML

@pytest.fixture
def test_cert():
    """Return a test certificate (for testing only)."""
    return TEST_CERT

@pytest.fixture
def test_key():
    """Return a test private key (for testing only)."""
    return TEST_KEY

@pytest.fixture
def teif_signer(test_cert, test_key):
    """Create and return a TEIFSigner instance for testing."""
    from src.teif.signature import TEIFSigner
    return TEIFSigner(test_cert, test_key)

@pytest.fixture
def signed_xml(teif_signer, sample_xml):
    """Return a signed XML document for testing."""
    return teif_signer.sign_xml(sample_xml.encode('utf-8'))
