"""
Script to generate a test certificate and private key for unit tests.
"""
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

def generate_test_certificate():
    """Generate a test certificate and private key."""
    # Create test directory if it doesn't exist
    test_dir = Path(__file__).parent / 'test_data'
    test_dir.mkdir(exist_ok=True)
    
    cert_path = test_dir / 'test_cert.pem'
    key_path = test_dir / 'test_key.pem'
    
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
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Write private key
    with open(key_path, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    
    print(f"Generated certificate: {cert_path}")
    print(f"Generated private key: {key_path}")

if __name__ == "__main__":
    generate_test_certificate()
