"""
Module pour la gestion des signatures électroniques TEIF.
"""
from typing import Dict, Any, Optional, List, Union, Tuple, cast
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import base64
import hashlib
import re
from lxml import etree
from OpenSSL import crypto
from lxml.etree import _Element as Element  # type: ignore
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import copy
import os
import uuid


class SignatureSection:
    """
    Represents a signature section in a TEIF document with XAdES support.
    """
    
    def __init__(self):
        """Initialize a new SignatureSection instance."""
        self.signatures = []
        
        # Register namespaces
        ET.register_namespace('ds', 'http://www.w3.org/2000/09/xmldsig#')
        ET.register_namespace('xades', 'http://uri.etsi.org/01903/v1.3.2#')
    
    def _create_reference(self, parent, uri='', transforms=None):
        """Create a Reference element."""
        ref = ET.SubElement(parent, '{http://www.w3.org/2000/09/xmldsig#}Reference')
        if uri:
            ref.set('URI', uri)
        
        # Add transforms if provided
        if transforms:
            transforms_elem = ET.SubElement(ref, 'Transforms')
            for transform in transforms:
                tf = ET.SubElement(transforms_elem, 'Transform', 
                                 Algorithm=transform['algorithm'])
                if 'xpath' in transform:
                    ET.SubElement(tf, 'XPath').text = transform['xpath']
        
        # Default digest method
        ET.SubElement(ref, 'DigestMethod', 
                     Algorithm='http://www.w3.org/2001/04/xmlenc#sha256')
        ET.SubElement(ref, 'DigestValue').text = ''  # Will be calculated during signing
        
        return ref
    
    def _create_signed_properties(self, parent, sig_id):
        """Create XAdES SignedProperties."""
        qualifying_props = ET.SubElement(
            parent, 
            '{http://uri.etsi.org/01903/v1.3.2#}QualifyingProperties',
            {'Target': f"#{sig_id}"}
        )
        
        signed_props = ET.SubElement(
            qualifying_props,
            '{http://uri.etsi.org/01903/v1.3.2#}SignedProperties',
            {'Id': f"xades-{sig_id}"}
        )
        
        # Add basic signed signature properties
        sig_props = ET.SubElement(
            signed_props,
            '{http://uri.etsi.org/01903/v1.3.2#}SignedSignatureProperties'
        )
        
        # Signing time
        ET.SubElement(
            sig_props,
            '{http://uri.etsi.org/01903/v1.3.2#}SigningTime'
        ).text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return qualifying_props
    
    def _create_signature_element(self, sig_data: Dict[str, Any]) -> ET.Element:
        """Create a complete XAdES signature element."""
        sig_id = sig_data.get('id', f'sig-{uuid.uuid4()}')
        
        # Create Signature element
        signature = ET.Element(
            '{http://www.w3.org/2000/09/xmldsig#}Signature',
            {'Id': sig_id}
        )
        
        # Create SignedInfo
        signed_info = ET.SubElement(signature, 'SignedInfo')
        
        # Add canonicalization method
        ET.SubElement(
            signed_info,
            'CanonicalizationMethod',
            Algorithm='http://www.w3.org/2001/10/xml-exc-c14n#'
        )
        
        # Add signature method
        ET.SubElement(
            signed_info,
            'SignatureMethod',
            Algorithm='http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        )
        
        # Add reference to the signed content
        ref = self._create_reference(
            signed_info,
            transforms=[
                {
                    'algorithm': 'http://www.w3.org/TR/1999/REC-xpath-19991116',
                    'xpath': 'not(ancestor-or-self::ds:Signature)'
                },
                {
                    'algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'
                }
            ]
        )
        
        # Add reference to the XAdES signed properties
        ref = self._create_reference(
            signed_info,
            uri=f"#xades-{sig_id}",
            transforms=[
                {'algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'}
            ]
        )
        ref.set('Type', 'http://uri.etsi.org/01903#SignedProperties')
        
        # Add SignatureValue (placeholder)
        ET.SubElement(
            signature,
            'SignatureValue',
            {'Id': f'value-{sig_id}'}
        ).text = sig_data.get('signature_value', '')
        
        # Add KeyInfo with certificate
        key_info = ET.SubElement(signature, 'KeyInfo')
        x509_data = ET.SubElement(key_info, 'X509Data')
        ET.SubElement(x509_data, 'X509Certificate').text = sig_data.get('cert_data', '')
        
        # Add XAdES qualifying properties
        self._create_signed_properties(signature, sig_id)
        
        return signature
    
    def add_signature(self,
                     cert_data: Union[str, bytes],
                     key_data: Optional[Union[str, bytes]] = None,
                     key_password: Optional[str] = None,
                     signature_id: Optional[str] = None,
                     role: Optional[str] = None,
                     name: Optional[str] = None,
                     date: Optional[Union[str, datetime]] = None) -> None:
        """
        Add a signature to the section with XAdES support.
        
        Args:
            cert_data: Certificate data in PEM format or path to certificate file
            key_data: Private key data or path to key file (optional)
            key_password: Password for the private key (optional)
            signature_id: Unique identifier for the signature
            role: Role of the signer
            name: Name of the signer
            date: Signature date (default: current time)
        """
        try:
            # Load certificate data
            if isinstance(cert_data, str) and os.path.isfile(cert_data):
                with open(cert_data, 'r', encoding='utf-8') as f:
                    cert_content = f.read()
            else:
                cert_content = cert_data
            
            # Clean certificate content
            if '-----BEGIN CERTIFICATE-----' in cert_content:
                cert_content = '\n'.join(
                    line.strip()
                    for line in cert_content.split('\n')
                    if line.strip() and not line.strip().startswith('---')
                )
            
            # Store signature data
            self.signatures.append({
                'id': signature_id or f'sig-{uuid.uuid4()}',
                'cert_data': cert_content,
                'key_data': key_data,
                'key_password': key_password,
                'role': role,
                'name': name,
                'date': date or datetime.utcnow(),
                'signature_value': '[SIGNATURE VALUE]'  # Placeholder
            })
            
        except Exception as e:
            raise SignatureError(f"Failed to add signature: {str(e)}")
    
    def to_xml(self, parent: Optional[ET.Element] = None) -> ET.Element:
        """
        Generate the XML representation of the signature section.
        
        Args:
            parent: Parent element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            signature_section = ET.Element('SignatureSection')
        else:
            signature_section = ET.SubElement(parent, 'SignatureSection')
        
        # Add each signature
        for sig_data in self.signatures:
            signature = self._create_signature_element(sig_data)
            signature_section.append(signature)
        
        return signature_section


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
    """
    Charge un certificat à partir d'un fichier ou de données brutes.
    
    Args:
        cert_data: Chemin vers le fichier de certificat ou données PEM du certificat
        
    Returns:
        Un objet X509 contenant le certificat chargé
        
    Raises:
        SignatureError: Si le certificat ne peut pas être chargé
    """
    try:
        # Vérifier si les données contiennent un en-tête PEM
        if '-----BEGIN CERTIFICATE-----' in cert_data or '-----BEGIN CERTIFICATE-----' in cert_data.upper():
            # Nettoyer les données PEM (supprimer les espaces et retours à la ligne en trop)
            cert_data = '\n'.join(line.strip() for line in cert_data.split('\n') if line.strip())
            # S'assurer que l'en-tête et le pied de page sont corrects
            if not cert_data.startswith('-----BEGIN CERTIFICATE-----'):
                cert_data = '-----BEGIN CERTIFICATE-----\n' + cert_data
            if not cert_data.endswith('-----END CERTIFICATE-----'):
                cert_data = cert_data + '\n-----END CERTIFICATE-----'
            # Charger le certificat à partir des données PEM
            return crypto.load_certificate(crypto.FILETYPE_PEM, cert_data.encode('utf-8'))
        else:
            # Essayer de charger à partir d'un fichier
            try:
                with open(cert_data, 'rb') as f:
                    return crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
            except (IOError, OSError):
                # Si le chargement du fichier échoue, essayer de tracer directement comme PEM
                try:
                    return crypto.load_certificate(crypto.FILETYPE_PEM, cert_data.encode('utf-8'))
                except Exception:
                    raise SignatureError("Format de certificat non reconnu. Doit être un fichier PEM ou une chaîne PEM valide.")
    except Exception as e:
        raise SignatureError(f"Impossible de charger le certificat: {str(e)}")


def _load_private_key(key_data: bytes, password: Optional[bytes] = None):
    """
    Load a private key from PEM data, handling both PKCS#1 and PKCS#8 formats.
    
    Args:
        key_data: The private key data in PEM format
        password: Optional password if the key is encrypted
        
    Returns:
        The loaded private key
        
    Raises:
        ValueError: If the key cannot be loaded
    """
    try:
        # Try loading as PKCS#8 first
        key = load_pem_private_key(
            key_data,
            password=password,
            backend=default_backend()
        )
        return key
    except ValueError as e:
        if "Could not deserialize key data" in str(e):
            # If PKCS#8 fails, try PKCS#1 format by adding the appropriate headers
            try:
                key_data_pkcs1 = key_data
                if b'-----BEGIN RSA PRIVATE KEY-----' not in key_data:
                    key_data_pkcs1 = (
                        b"-----BEGIN RSA PRIVATE KEY-----\n" +
                        key_data.replace(b" ", b"").replace(b"\n", b"") +
                        b"\n-----END RSA PRIVATE KEY-----"
                    )
                key = load_pem_private_key(
                    key_data_pkcs1,
                    password=password,
                    backend=default_backend()
                )
                return key
            except Exception as inner_e:
                raise ValueError(f"Failed to load private key (tried PKCS#1 and PKCS#8): {str(inner_e)}")
        else:
            raise
    except Exception as e:
        raise ValueError(f"Failed to load private key: {str(e)}")


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


def sign_xml(xml_data: Union[str, bytes], cert_pem: bytes, key_pem: bytes, key_password: Optional[bytes] = None) -> bytes:
    """
    Sign an XML document with XAdES-B signature.
    
    Args:
        xml_data: The XML document to sign (as string or bytes)
        cert_pem: The signer's certificate in PEM format
        key_pem: The private key in PEM format
        key_password: Password for the private key (if encrypted)
        
    Returns:
        Signed XML document as bytes
        
    Raises:
        SignatureError: If there's an error during the signing process
    """
    try:
        # Parse the XML
        if isinstance(xml_data, str):
            xml_data = xml_data.encode('utf-8')
            
        # Parse the XML document
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_data, parser=parser)
        
        # Register namespaces
        ns = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }
        
        # Find or create the signature element
        signature = root.find('.//ds:Signature', namespaces=ns)
        if signature is None:
            raise SignatureError("No Signature element found in the XML document")
            
        # Load the private key
        try:
            private_key = _load_private_key(key_pem, key_password)
        except Exception as e:
            raise SignatureError(f"Failed to load private key: {str(e)}")
            
        # 2. Calculate digest of the document (excluding signature)
        # Create a copy of the document without the signature
        doc_without_sig = etree.Element(root.tag, root.attrib)
        for elem in root:
            if elem.tag != f"{{{ns['ds']}}}Signature":
                doc_without_sig.append(copy.deepcopy(elem))
        
        # Canonicalize the document without signature
        c14n_doc = etree.tostring(
            doc_without_sig,
            method='c14n',
            exclusive=True,
            with_comments=False
        )
        
        # Calculate digest of the document
        doc_digest = hashlib.sha256(c14n_doc).digest()
        doc_digest_b64 = base64.b64encode(doc_digest).decode('ascii')
        
        # Update the reference to the document
        ref = signature.find('.//ds:Reference[@Id="r-id-frs"]', namespaces=ns)
        if ref is not None:
            digest_value = ref.find('.//ds:DigestValue', namespaces=ns)
            if digest_value is not None:
                digest_value.text = doc_digest_b64
        
        # 3. Calculate digest of the signed properties
        signed_props = signature.find('.//xades:SignedProperties', namespaces=ns)
        if signed_props is None:
            raise SignatureError("No SignedProperties element found")
            
        # Set the Id attribute if not present
        if 'Id' not in signed_props.attrib:
            signed_props.attrib['Id'] = 'xades-SigFrs'
            
        # Get the Id for reference
        signed_props_id = signed_props.attrib['Id']
        
        # Update the reference URI in the signature
        ref = signature.find(f'.//ds:Reference[@Type="http://uri.etsi.org/01903#SignedProperties"]', namespaces=ns)
        if ref is not None:
            ref.attrib['URI'] = f"#{signed_props_id}"
            
            # Canonicalize the SignedProperties element
            c14n_signed_props = etree.tostring(
                signed_props,
                method='c14n',
                exclusive=True,
                with_comments=False
            )
            
            # Calculate digest of the SignedProperties
            signed_props_digest = hashlib.sha256(c14n_signed_props).digest()
            signed_props_digest_b64 = base64.b64encode(signed_props_digest).decode('ascii')
            
            # Update the digest value
            digest_value = ref.find('.//ds:DigestValue', namespaces=ns)
            if digest_value is not None:
                digest_value.text = signed_props_digest_b64
        
        # 4. Calculate the signature value
        signed_info = signature.find('.//ds:SignedInfo', namespaces=ns)
        if signed_info is None:
            raise SignatureError("No SignedInfo element found")
            
        # Canonicalize the SignedInfo element
        c14n_signed_info = etree.tostring(
            signed_info,
            method='c14n',
            exclusive=True,
            with_comments=False
        )
        
        # Sign the canonicalized SignedInfo
        signature_value = private_key.sign(
            c14n_signed_info,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_value_b64 = base64.b64encode(signature_value).decode('ascii')
        
        # Update the SignatureValue element
        sig_value_elem = signature.find('.//ds:SignatureValue', namespaces=ns)
        if sig_value_elem is not None:
            sig_value_elem.text = signature_value_b64
        
        # 5. Add the certificate to the KeyInfo
        x509_data = signature.find('.//ds:X509Data', namespaces=ns)
        if x509_data is not None:
            # Remove any existing X509Certificate elements
            for elem in x509_data.findall('.//ds:X509Certificate', namespaces=ns):
                x509_data.remove(elem)
                
            # Add the certificate (remove PEM headers/footers and newlines)
            cert_pem_str = cert_pem.decode('utf-8')
            cert_clean = '\n'.join(line.strip() 
                                 for line in cert_pem_str.split('\n') 
                                 if line.strip() and 
                                 not line.startswith('-----') and 
                                 not line.endswith('-----'))
            
            cert_elem = etree.SubElement(x509_data, f"{{{ns['ds']}}}X509Certificate")
            cert_elem.text = cert_clean
        
        # Return the signed XML
        return etree.tostring(
            root,
            xml_declaration=True,
            encoding='UTF-8',
            pretty_print=True
        )
        
    except Exception as e:
        raise SignatureError(f"Error signing XML: {str(e)}")


__all__ = [
    'create_signature',
    'add_signature',
    'sign_xml',
    'SignatureError',
    'SignatureSection'
]
