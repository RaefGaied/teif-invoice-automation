#!/usr/bin/env python3
"""
Utility script to generate test certificates and keys for XAdES signature testing.

This script generates:
- A self-signed CA certificate
- A server certificate signed by the CA
- Private keys for both certificates
- All files are saved in PEM format
"""
import os
import argparse
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def generate_private_key(key_size=2048, output_file=None):
    """Generate a private key.
    
    Args:
        key_size: Key size in bits (default: 2048)
        output_file: Path to save the private key (optional)
        
    Returns:
        The generated private key
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    if output_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        with open(output_file, 'wb') as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )
        print(f"Private key saved to: {output_file}")
    
    return private_key

def create_ca_certificate(subject_name, private_key, days_valid=3650, output_file=None):
    """Create a self-signed CA certificate.
    
    Args:
        subject_name: Dictionary of subject name attributes
        private_key: The private key to sign the certificate with
        days_valid: Number of days the certificate is valid for
        output_file: Path to save the certificate (optional)
        
    Returns:
        The generated certificate
    """
    subject = issuer = x509.Name([
        x509.NameAttribute(getattr(NameOID, k.upper()), v)
        for k, v in subject_name.items()
    ])
    
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=days_valid))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )
    
    if output_file:
        with open(output_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"CA certificate saved to: {output_file}")
    
    return cert

def create_server_certificate(subject_name, private_key, ca_private_key, ca_cert, 
                            days_valid=365, dns_names=None, output_file=None):
    """Create a server certificate signed by a CA.
    
    Args:
        subject_name: Dictionary of subject name attributes
        private_key: The private key for the server
        ca_private_key: The private key of the CA
        ca_cert: The CA certificate
        days_valid: Number of days the certificate is valid for
        dns_names: List of DNS names for the Subject Alternative Name extension
        output_file: Path to save the certificate (optional)
        
    Returns:
        The generated certificate
    """
    subject = x509.Name([
        x509.NameAttribute(getattr(NameOID, k.upper()), v)
        for k, v in subject_name.items()
    ])
    
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=days_valid))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.CODE_SIGNING,
            ]),
            critical=False
        )
    )
    
    # Add Subject Alternative Name extension if DNS names are provided
    if dns_names:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(name) for name in dns_names]),
            critical=False
        )
    
    cert = builder.sign(ca_private_key, hashes.SHA256(), default_backend())
    
    if output_file:
        with open(output_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"Server certificate saved to: {output_file}")
    
    return cert

def main():
    parser = argparse.ArgumentParser(description='Generate test certificates for XAdES signing')
    parser.add_argument('--output-dir', default='certs', help='Output directory for generated files')
    parser.add_argument('--key-size', type=int, default=2048, help='Key size in bits (default: 2048)')
    parser.add_argument('--ca-common-name', default='Test CA', help='CA common name')
    parser.add_argument('--server-common-name', default='test.example.com', help='Server common name')
    parser.add_argument('--organization', default='Test Organization', help='Organization name')
    parser.add_argument('--country', default='TN', help='2-letter country code')
    parser.add_argument('--state', default='Tunis', help='State or province')
    parser.add_argument('--locality', default='Tunis', help='Locality or city')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate CA private key
    print("Generating CA private key...")
    ca_key_file = os.path.join(args.output_dir, 'ca.key')
    ca_private_key = generate_private_key(args.key_size, ca_key_file)
    
    # Generate CA certificate
    print("Generating CA certificate...")
    ca_cert_file = os.path.join(args.output_dir, 'ca.crt')
    ca_cert = create_ca_certificate(
        subject_name={
            'country_name': args.country,
            'state_or_province_name': args.state,
            'locality_name': args.locality,
            'organization_name': args.organization,
            'common_name': args.ca_common_name
        },
        private_key=ca_private_key,
        output_file=ca_cert_file
    )
    
    # Generate server private key
    print("Generating server private key...")
    server_key_file = os.path.join(args.output_dir, 'server.key')
    server_private_key = generate_private_key(args.key_size, server_key_file)
    
    # Generate server certificate
    print("Generating server certificate...")
    server_cert_file = os.path.join(args.output_dir, 'server.crt')
    create_server_certificate(
        subject_name={
            'country_name': args.country,
            'state_or_province_name': args.state,
            'locality_name': args.locality,
            'organization_name': args.organization,
            'common_name': args.server_common_name
        },
        private_key=server_private_key,
        ca_private_key=ca_private_key,
        ca_cert=ca_cert,
        dns_names=[args.server_common_name, 'localhost'],
        output_file=server_cert_file
    )
    
    print("\nCertificate generation complete!")
    print(f"Files saved to: {os.path.abspath(args.output_dir)}")
    print("\nTo use these certificates for testing:")
    print(f"- Use {server_key_file} as your private key")
    print(f"- Use {server_cert_file} as your certificate")
    print(f"- Use {ca_cert_file} as the CA certificate for verification")

if __name__ == '__main__':
    main()
