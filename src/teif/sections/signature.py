"""
Module pour la gestion des signatures électroniques TEIF.
"""
from typing import Dict, Any, Optional, List, Union, Tuple
import xml.etree.ElementTree as ET
from datetime import datetime
import base64
from lxml import etree
from OpenSSL import crypto


class SignatureSection:
    """
    A class to handle electronic signatures in TEIF documents.
    
    This class provides methods to create and manage digital signatures
    according to the TEIF 1.8.8 standard.
    """
    
    def __init__(self):
        """Initialize a new SignatureSection instance."""
        self.signatures = []
    
    def add_signature(self,
                     cert_data: Union[str, bytes],
                     key_data: Optional[Union[str, bytes]] = None,
                     key_password: Optional[str] = None,
                     signature_id: Optional[str] = None,
                     role: Optional[str] = None,
                     name: Optional[str] = None,
                     date: Optional[Union[str, datetime]] = None) -> None:
        """
        Add a signature to the section.
        
        Args:
            cert_data: Path to certificate file or certificate data
            key_data: Path to private key file or key data (optional)
            key_password: Password for the private key (optional)
            signature_id: Unique identifier for the signature (optional)
            role: Role of the signer (optional)
            name: Name of the signer (optional)
            date: Signature date (optional, default: now)
        """
        self.signatures.append({
            'cert_data': cert_data,
            'key_data': key_data,
            'key_password': key_password,
            'signature_id': signature_id,
            'role': role,
            'name': name,
            'date': date or datetime.now()
        })
    
    def to_xml(self, parent: ET.Element = None) -> ET.Element:
        """
        Generate the XML representation of the signature section.
        
        Args:
            parent: The parent XML element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            signature_section = ET.Element('SignatureSection')
        else:
            signature_section = ET.SubElement(parent, 'SignatureSection')
        
        for sig in self.signatures:
            self._add_signature_element(signature_section, sig)
        
        return signature_section
    
    def _add_signature_element(self, parent: ET.Element, sig_data: Dict[str, Any]) -> None:
        """Helper method to add a signature element."""
        try:
            # Create signature element
            signature = ET.SubElement(parent, 'Signature')
            
            # Add signature ID if provided
            if 'signature_id' in sig_data and sig_data['signature_id']:
                signature.set('Id', str(sig_data['signature_id']))
            
            # Add signature type
            signature_type = ET.SubElement(signature, 'SignatureType')
            signature_type.text = 'XAdES'  # Default to XAdES
            
            # Add signature date
            date = sig_data.get('date', datetime.now())
            if isinstance(date, datetime):
                date = date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            date_elem = ET.SubElement(signature, 'SignatureDate')
            date_elem.text = str(date)
            
            # Add signer information if available
            if 'name' in sig_data and sig_data['name']:
                signer = ET.SubElement(signature, 'Signer')
                
                # Add signer name
                name_elem = ET.SubElement(signer, 'Name')
                name_elem.text = str(sig_data['name'])
                
                # Add signer role if provided
                if 'role' in sig_data and sig_data['role']:
                    role_elem = ET.SubElement(signer, 'Role')
                    role_elem.text = str(sig_data['role'])
            
            # Add certificate information
            cert_data = sig_data['cert_data']
            if isinstance(cert_data, str) and cert_data.startswith('-----BEGIN CERTIFICATE-----'):
                # Certificate is already in PEM format
                cert_pem = cert_data
            else:
                # Load certificate from file
                with open(cert_data, 'rb') as f:
                    cert_pem = f.read()
            
            # Add certificate data
            cert_elem = ET.SubElement(signature, 'Certificate')
            # Remove headers and newlines for storage
            cert_data = '\n'.join(line.strip() for line in cert_pem.split('\n')
                                 if line.strip() and not line.startswith('-----'))
            cert_elem.text = cert_data
            
            # Add signature value (placeholder, actual signing would be done here)
            sig_value = ET.SubElement(signature, 'SignatureValue')
            sig_value.text = '[SIGNATURE VALUE]'  # Placeholder
            
        except Exception as e:
            raise SignatureError(f"Failed to create signature: {str(e)}")


class SignatureError(Exception):
    """Exception levée en cas d'erreur de signature."""
    pass


def create_signature(parent: ET.Element, signature_data: Dict[str, Any]) -> ET.Element:
    """
    Crée un élément de signature avec les métadonnées fournies.
    
    Args:
        parent: L'élément parent XML
        signature_data: Dictionnaire contenant les données de signature
            - id: Identifiant unique de la signature (optionnel)
            - type: Type de signature (optionnel, défaut: 'XAdES')
            - timestamp: Horodatage de la signature (optionnel, défaut: maintenant)
            
    Returns:
        L'élément de signature créé
    """
    signature = ET.SubElement(parent, "Signature")
    
    # ID de la signature
    if 'id' in signature_data:
        signature.set('Id', str(signature_data['id']))
    
    # Type de signature
    signature_type = signature_data.get('type', 'XAdES')
    ET.SubElement(signature, "SignatureType").text = signature_type
    
    # Horodatage
    timestamp = signature_data.get('timestamp', datetime.utcnow().isoformat() + 'Z')
    ET.SubElement(signature, "SignatureTimestamp").text = str(timestamp)
    
    # Informations sur le signataire (optionnelles)
    if 'signer_info' in signature_data:
        signer_info = ET.SubElement(signature, "SignerInfo")
        for key, value in signature_data['signer_info'].items():
            ET.SubElement(signer_info, key).text = str(value)
    
    return signature


def add_signature(
    parent: ET.Element, 
    cert_data: Dict[str, Any],
    signature_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Ajoute une signature électronique à un document TEIF.
    
    Args:
        parent: L'élément parent XML
        cert_data: Dictionnaire contenant les informations du certificat
            - cert: Chemin vers le fichier de certificat ou données du certificat
            - key: Chemin vers la clé privée ou données de la clé (optionnel pour la génération)
            - password: Mot de passe de la clé privée (optionnel)
        signature_data: Données supplémentaires de signature (optionnel)
            - id: Identifiant de la signature (optionnel)
            - role: Rôle du signataire (optionnel)
            - name: Nom du signataire (optionnel)
            - date: Date de signature (optionnel, défaut: maintenant)
    
    Raises:
        SignatureError: En cas d'erreur lors de la création de la signature
    """
    if not cert_data or 'cert' not in cert_data:
        raise SignatureError("Les données du certificat sont requises")
    
    try:
        # Charger le certificat
        cert = _load_certificate(cert_data['cert'])
        
        # Créer l'élément de signature
        signature = ET.SubElement(parent, "Signature")
        
        # ID de la signature
        if signature_data and 'id' in signature_data:
            signature.set("Id", str(signature_data['id']))
        
        # Informations sur le signataire
        signer_info = ET.SubElement(signature, "SignerInformation")
        
        # Rôle du signataire
        if signature_data and 'role' in signature_data:
            ET.SubElement(
                signer_info,
                "SignerRole",
                code=signature_data['role']
            )
        
        # Nom du signataire
        if signature_data and 'name' in signature_data:
            ET.SubElement(signer_info, "SignerName").text = str(signature_data['name'])
        
        # Date de signature
        sign_date = datetime.now()
        if signature_data and 'date' in signature_data:
            sign_date = signature_data['date']
        
        ET.SubElement(
            signature,
            "SigningTime"
        ).text = sign_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Données du certificat
        cert_info = ET.SubElement(signature, "SigningCertificate")
        
        # Empreinte numérique du certificat
        cert_digest = ET.SubElement(cert_info, "CertDigest")
        cert_digest.text = cert.digest('sha1').decode('ascii')
        
        # Données brutes du certificat (encodées en base64)
        cert_value = ET.SubElement(cert_info, "CertValue")
        cert_value.text = base64.b64encode(
            crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
        ).decode('ascii')
        
        # Si une clé privée est fournie, on peut signer le document
        if 'key' in cert_data:
            private_key = _load_private_key(
                cert_data['key'],
                cert_data.get('password')
            )
            
            # Créer la signature
            signed_info = _create_signed_info(parent)
            signature_value = _sign_data(signed_info, private_key)
            
            # Ajouter la valeur de la signature
            sig_value = ET.SubElement(signature, "SignatureValue")
            sig_value.text = base64.b64encode(signature_value).decode('ascii')
    
    except Exception as e:
        raise SignatureError(f"Erreur lors de la création de la signature: {str(e)}")


def _load_certificate(cert_data: str) -> crypto.X509:
    """Charge un certificat à partir d'un fichier ou de données brutes."""
    try:
        if '-----BEGIN CERTIFICATE-----' in cert_data:
            # Données PEM
            return crypto.load_certificate(crypto.FILETYPE_PEM, cert_data.encode())
        else:
            # Fichier
            with open(cert_data, 'rb') as f:
                return crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
    except Exception as e:
        raise SignatureError(f"Impossible de charger le certificat: {str(e)}")


def _load_private_key(key_data: str, password: Optional[str] = None) -> crypto.PKey:
    """Charge une clé privée à partir d'un fichier ou de données brutes."""
    try:
        if '-----BEGIN PRIVATE KEY-----' in key_data:
            # Données PEM
            return crypto.load_privatekey(
                crypto.FILETYPE_PEM,
                key_data.encode(),
                password.encode() if password else None
            )
        else:
            # Fichier
            with open(key_data, 'rb') as f:
                return crypto.load_privatekey(
                    crypto.FILETYPE_PEM,
                    f.read(),
                    password.encode() if password else None
                )
    except Exception as e:
        raise SignatureError(f"Impossible de charger la clé privée: {str(e)}")


def _create_signed_info(element: ET.Element) -> bytes:
    """Crée l'élément SignedInfo pour la signature."""
    # Convertir l'élément en chaîne XML canonique
    xml_str = ET.tostring(element, encoding='utf-8', method='xml')
    
    # Parser avec lxml pour la canonisation
    parser = etree.XMLParser(remove_blank_text=True)
    doc = etree.fromstring(xml_str, parser)
    
    # Canonisation exclusive XML 1.0
    signed_info = etree.tostring(
        doc,
        method='c14n',
        exclusive=True,
        with_comments=False,
        inclusive_ns_prefixes=None
    )
    
    return signed_info


def _sign_data(data: bytes, private_key: crypto.PKey) -> bytes:
    """Signe des données avec une clé privée."""
    try:
        # Créer un objet de signature
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        
        # Convertir la clé OpenSSL en clé cryptography
        pem_key = crypto.dump_privatekey(
            crypto.FILETYPE_PEM,
            private_key
        )
        
        key = serialization.load_pem_private_key(
            pem_key,
            password=None,
            backend=default_backend()
        )
        
        # Signer les données
        signature = key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return signature
    except Exception as e:
        raise SignatureError(f"Erreur lors de la signature des données: {str(e)}")


__all__ = [
    'create_signature',
    'add_signature',
    'SignatureError',
    'SignatureSection'
]
