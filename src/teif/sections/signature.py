"""
Module pour la gestion des signatures électroniques TEIF.
"""
from typing import Dict, Any, Optional, List, Union, Tuple, cast
import xml.etree.ElementTree as ET
from OpenSSL import crypto
from datetime import datetime, timezone
import base64
import hashlib
import uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs7, load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import copy
import os
import xml.etree.ElementTree as ET
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.x509 import load_pem_x509_certificate
import logging
from lxml import etree

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# XML Namespaces
NSMAP = {
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'xades': 'http://uri.etsi.org/01903/v1.3.2#',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xsd': 'http://www.w3.org/2001/XMLSchema',
    'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
}

# Constants for namespace URIs
DS_NS = NSMAP['ds']
XADES_NS = NSMAP['xades']
XSI_NS = NSMAP['xsi']
XSD_NS = NSMAP['xsd']
UBL_NS = NSMAP['ubl']

# Algorithmes et URLs
CANONICALIZATION_METHOD = 'http://www.w3.org/2001/10/xml-exc-c14n#'
SIGNATURE_METHOD = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
DIGEST_METHOD = 'http://www.w3.org/2001/04/xmlenc#sha256'
QUALIFYING_PROPERTIES = f"{{{XADES_NS}}}QualifyingProperties"
SIGNED_PROPERTIES = f"{{{XADES_NS}}}SignedProperties"
SIGNING_CERTIFICATE = f"{{{XADES_NS}}}SigningCertificate"
CERT = f"{{{XADES_NS}}}Cert"
CERT_DIGEST = f"{{{XADES_NS}}}CertDigest"
SIGNING_TIME = f"{{{XADES_NS}}}SigningTime"
SIGNATURE_POLICY_IDENTIFIER = f"{{{XADES_NS}}}SignaturePolicyIdentifier"
SIGNATURE_POLICY_ID = f"{{{XADES_NS}}}SignaturePolicyId"
SIG_POLICY_ID = f"{{{XADES_NS}}}SigPolicyId"
IDENTIFIER = f"{{{XADES_NS}}}Identifier"
DESCRIPTION = f"{{{XADES_NS}}}Description"
SIGNER_ROLE = f"{{{XADES_NS}}}SignerRole"
CLAIMED_ROLES = f"{{{XADES_NS}}}ClaimedRoles"
CLAIMED_ROLE = f"{{{XADES_NS}}}ClaimedRole"

class SignatureSection:
    """Classe pour gérer les signatures électroniques XAdES-B selon les spécifications d'El Fatoora."""
    
    def __init__(self):
        """Initialise une nouvelle instance de SignatureSection."""
        self.signatures = []
        self._register_namespaces()
    
    def _register_namespaces(self):
        """Enregistre les espaces de noms XML utilisés."""
        # Namespaces are handled at the root level in xml.etree
        pass
    
    def _create_reference(self, parent, uri='', transforms=None, reference_id=None):
        """
        Crée un élément Reference avec les transformations spécifiées.
        
        Args:
            parent: L'élément parent XML
            uri: URI de la référence
            transforms: Liste des transformations à appliquer
            reference_id: ID de la référence
            
        Returns:
            L'élément Reference créé
        """
        ref = etree.SubElement(parent, f'{{{DS_NS}}}Reference')
        if uri:
            ref.set('URI', uri)
        if reference_id:
            ref.set('Id', reference_id)
        
        # Ajouter les transformations
        if transforms:
            transforms_elem = etree.SubElement(ref, f'{{{DS_NS}}}Transforms')
            for transform in transforms:
                tf = etree.SubElement(
                    transforms_elem, 
                    f'{{{DS_NS}}}Transform',
                    Algorithm=transform['algorithm']
                )
                if 'xpath' in transform:
                    xpath = etree.SubElement(tf, f'{{{DS_NS}}}XPath')
                    xpath.text = transform['xpath']
        
        # Ajouter la méthode de hachage
        etree.SubElement(
            ref, 
            f'{{{DS_NS}}}DigestMethod',
            Algorithm=DIGEST_METHOD
        )
        
        # La valeur de hachage sera calculée plus tard
        etree.SubElement(ref, f'{{{DS_NS}}}DigestValue')
        
        return ref
    
    def _create_signed_properties(self, parent, sig_id, role=None, name=None):
        """
        Crée les propriétés XAdES signées.
        
        Args:
            parent: L'élément parent XML
            sig_id: ID de la signature
            role: Rôle du signataire (optionnel)
            name: Nom du signataire (optionnel)
        """
        # Créer l'élément Object pour les propriétés XAdES
        obj = etree.SubElement(parent, f'{{{DS_NS}}}Object')
        
        # Créer l'élément QualifyingProperties
        qualifying_props = etree.SubElement(
            obj,
            f'{{{XADES_NS}}}QualifyingProperties',
            {
                'Target': f'#{sig_id}'
            }
        )
        
        # Créer l'élément SignedProperties
        signed_props = etree.SubElement(
            qualifying_props,
            f'{{{XADES_NS}}}SignedProperties',
            {
                'Id': f'xades-{sig_id}'
            }
        )
        
        # Créer l'élément SignedSignatureProperties
        sig_props = etree.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedSignatureProperties'
        )
        
        # Ajouter l'horodatage de signature
        signing_time = etree.SubElement(
            sig_props,
            f'{{{XADES_NS}}}SigningTime'
        )
        signing_time.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Ajouter la politique de signature
        sig_policy = etree.SubElement(
            sig_props,
            f'{{{XADES_NS}}}SignaturePolicyIdentifier'
        )
        sig_policy_id = etree.SubElement(
            sig_policy,
            f'{{{XADES_NS}}}SignaturePolicyId'
        )
        
        # Identifier de la politique
        sig_policy_id_el = etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyId'
        )
        etree.SubElement(
            sig_policy_id_el,
            f'{{{XADES_NS}}}Identifier'
        ).text = 'urn:oid:1.3.6.1.4.1.311.10.1.1'
        
        # Hachage de la politique
        sig_policy_hash = etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyHash'
        )
        etree.SubElement(
            sig_policy_hash,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm='http://www.w3.org/2001/04/xmlenc#sha256'
        )
        etree.SubElement(
            sig_policy_hash,
            f'{{{DS_NS}}}DigestValue'
        ).text = '3J1oMkha+OAlm9hBNCcAS+/nbKokG8Gf9N3XPipP7yg='
        
        # Qualifieurs de la politique
        sig_policy_qualifiers = etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyQualifiers'
        )
        sig_policy_qualifier = etree.SubElement(
            sig_policy_qualifiers,
            f'{{{XADES_NS}}}SigPolicyQualifier'
        )
        etree.SubElement(
            sig_policy_qualifier,
            f'{{{XADES_NS}}}SPURI'
        ).text = 'http://www.tradenet.com.tn/portal/telechargerTelechargement?lien=Politique_de_Signature_de_la_facture_electronique.pdf'
        
        # Rôle du signataire
        if role or name:
            signer_role = etree.SubElement(
                sig_props,
                f'{{{XADES_NS}}}SignerRole'
            )
            claimed_roles = etree.SubElement(
                signer_role,
                f'{{{XADES_NS}}}ClaimedRoles'
            )
            if role:
                etree.SubElement(
                    claimed_roles,
                    f'{{{XADES_NS}}}ClaimedRole'
                ).text = role
            if name:
                etree.SubElement(
                    claimed_roles,
                    f'{{{XADES_NS}}}ClaimedRole'
                ).text = name
        
        # SignedDataObjectProperties
        data_obj_props = etree.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedDataObjectProperties'
        )
        
        # DataObjectFormat pour la signature
        data_obj_format = etree.SubElement(
            data_obj_props,
            f'{{{XADES_NS}}}DataObjectFormat',
            ObjectReference=f'#r-id-{sig_id}'
        )
        etree.SubElement(
            data_obj_format,
            f'{{{XADES_NS}}}MimeType'
        ).text = 'text/xml'
        etree.SubElement(
            data_obj_format,
            f'{{{XADES_NS}}}Encoding'
        ).text = 'UTF-8'
    
    def _calculate_digest(self, element, transforms=None):
        """
        Calcule le hachage d'un élément XML après application des transformations.
        
        Args:
            element: L'élément XML à hacher
            transforms: Liste des transformations à appliquer
            
        Returns:
            Tuple (données canonisées, hachage en base64)
        """
        # Faire une copie profonde pour éviter de modifier l'original
        element_copy = copy.deepcopy(element)
        
        # Appliquer les transformations dans l'ordre
        if transforms:
            for transform in transforms:
                if transform['algorithm'] == 'http://www.w3.org/TR/1999/REC-xpath-19991116':
                    # Implémenter la transformation XPath
                    xpath_expr = transform.get('xpath', '')
                    if 'not(ancestor-or-self::ds:Signature)' in xpath_expr:
                        # Exclure l'élément Signature
                        for sig in element_copy.xpath('//ds:Signature', namespaces={'ds': DS_NS}):
                            sig.getparent().remove(sig)
                    elif 'not(ancestor-or-self::RefTtnVal)' in xpath_expr:
                        # Exclure l'élément RefTtnVal
                        for ref in element_copy.xpath('//RefTtnVal'):
                            ref.getparent().remove(ref)
        
        # Canonicaliser l'élément selon XML-Exc-C14N
        canonicalized = etree.tostring(
            element_copy,
            method='c14n',
            exclusive=True,
            with_comments=False,
            inclusive_ns_prefixes=None
        )
        
        # Calculer le hachage SHA-256
        digest = hashlib.sha256(canonicalized).digest()
        return canonicalized, base64.b64encode(digest).decode('utf-8')
    
    def _sign_data(
        self,
        data: bytes,
        private_key_data: Union[bytes, str, crypto.PKey, Any],
        password: Optional[Union[str, bytes]] = None
    ) -> bytes:
        """
        Sign data with a private key.

        Args:
            data: The data to be signed
            private_key_data: Private key as bytes, string, crypto.PKey, or loaded key object
            password: Optional password if the key is encrypted

        Returns:
            The signature as bytes

        Raises:
            SignatureError: If there's an error during signing
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            
            # If it's already a loaded key object (from _load_private_key)
            if hasattr(private_key_data, 'sign'):
                key = private_key_data
            # If it's a crypto.PKey
            elif isinstance(private_key_data, crypto.PKey):
                key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key_data)
                key = load_pem_private_key(
                    key_pem,
                    password=None,
                    backend=default_backend()
                )
            # If it's a string or bytes
            elif isinstance(private_key_data, (str, bytes)):
                if isinstance(private_key_data, str):
                    if os.path.isfile(private_key_data):
                        with open(private_key_data, "rb") as f:
                            key_data = f.read()
                    else:
                        key_data = private_key_data.encode("utf-8")
                
                if isinstance(password, str):
                    password = password.encode("utf-8")

                key = load_pem_private_key(
                    key_data,
                    password=password,
                    backend=default_backend()
                )
            else:
                raise ValueError(f"Unsupported private key type: {type(private_key_data)}")

            # Sign the data
            signature = key.sign(
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            return signature

        except Exception as e:
            raise SignatureError(f"Erreur lors de la signature des données: {str(e)}")
    
    def _update_digest_values(self, signature_element: ET.Element, sig_data: Dict[str, Any]) -> None:
        """
        Met à jour les valeurs de hachage dans l'élément de signature.
        
        Args:
            signature_element: L'élément de signature à mettre à jour
            sig_data: Données de la signature
        """
        # Mettre à jour les valeurs de hachage
        signed_info = signature_element.find('.//ds:SignedInfo', namespaces={'ds': DS_NS})
        
        # Pour chaque référence dans SignedInfo
        for ref in signed_info.findall('ds:Reference', namespaces={'ds': DS_NS}):
            uri = ref.get('URI', '')
            
            # Skip if this is not a reference to signed properties
            if not uri.startswith('#'):
                continue
                
            # Find the referenced element
            ref_id = uri[1:]
            referenced_element = signature_element.find(f".//*[@Id='{ref_id}']")
            
            if referenced_element is not None:
                # Compute digest
                digest = self._compute_digest(referenced_element)
                digest_b64 = base64.b64encode(digest).decode('ascii')
                
                # Update DigestValue
                digest_value = ref.find('ds:DigestValue', namespaces={'ds': DS_NS})
                if digest_value is not None:
                    digest_value.text = digest_b64
    
    def _compute_digest(self, node: ET.Element, digest_method: str = DIGEST_METHOD) -> bytes:
        """
        Compute the digest of an XML node after canonicalization.
        
        Args:
            node: The XML element to compute digest for
            digest_method: The digest method URI
            
        Returns:
            The computed digest as bytes
        """
        try:
            # Convert node to string
            node_str = etree.tostring(node, encoding='utf-8', method='xml')
            
            # For XAdES, we need to use exclusive XML canonicalization
            parser = etree.XMLParser(remove_blank_text=True)
            doc = etree.fromstring(node_str, parser=parser)
            
            # Apply exclusive canonicalization using lxml's c14n method
            c14n = etree.tostring(
                doc,
                method='c14n',
                exclusive=True,
                with_comments=False,
                inclusive_ns_prefixes=None
            )
            
            # Compute digest
            if digest_method == DIGEST_METHOD:  # SHA-256
                digest = hashlib.sha256(c14n).digest()
            else:
                raise ValueError(f"Unsupported digest method: {digest_method}")
                
            return digest
            
        except Exception as e:
            logger.error(f"Error in _compute_digest: {str(e)}")
            raise SignatureError(f"Failed to compute digest: {str(e)}")
    
    def _sign_document(self, signature: ET.Element, key_data: bytes, key_password: Optional[str] = None) -> None:
        """
        Sign the document by computing and setting the digest values and signature.
        
        Args:
            signature: The signature element to sign
            key_data: The private key data in PEM format
            key_password: Optional password for the private key
        """
        try:
            # 1. Find all references that need digest computation
            signed_info = signature.find(f'{{{DS_NS}}}SignedInfo')
            if signed_info is None:
                raise ValueError("SignedInfo element not found in signature")
                
            # 2. Compute and set digest values for each reference
            for ref in signed_info.findall(f'{{{DS_NS}}}Reference'):
                uri = ref.get('URI', '')
                
                # Skip if this is not a reference to signed properties
                if not uri.startswith('#'):
                    continue
                    
                # Find the referenced element
                ref_id = uri[1:]
                referenced_element = signature.find(f".//*[@Id='{ref_id}']")
                
                if referenced_element is not None:
                    # Compute digest
                    digest = self._compute_digest(referenced_element)
                    digest_b64 = base64.b64encode(digest).decode('ascii')
                    
                    # Update DigestValue
                    digest_value = ref.find(f'{{{DS_NS}}}DigestValue')
                    if digest_value is not None:
                        digest_value.text = digest_b64
            
            # 3. Canonicalize SignedInfo
            signed_info_str = etree.tostring(signed_info, encoding='utf-8')
            signed_info_parsed = etree.fromstring(signed_info_str)
            signed_info_c14n = etree.tostring(
                signed_info_parsed,
                method='c14n',
                exclusive=True,
                with_comments=False,
                inclusive_ns_prefixes=None
            )
            
            # 4. Sign the canonicalized SignedInfo
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            
            # Load the private key
            if isinstance(key_data, str):
                key_data = key_data.encode('utf-8')
                
            if isinstance(key_password, str):
                key_password = key_password.encode('utf-8')
                
            private_key = load_pem_private_key(
                key_data,
                password=key_password,
                backend=default_backend()
            )
            
            # Sign using RSA-PKCS1v15 with SHA-256
            signature_bytes = private_key.sign(
                signed_info_c14n,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # 5. Set the signature value
            signature_value = signature.find(f'{{{DS_NS}}}SignatureValue')
            if signature_value is not None:
                # Ensure we're setting a string, not bytes
                signature_value.text = base64.b64encode(signature_bytes).decode('ascii')
                
        except Exception as e:
            logger.error(f"Error signing document: {str(e)}")
            raise SignatureError(f"Failed to sign document: {str(e)}")

    def sign_document(self, xml_doc: ET.Element, signature_id: str = 'SigFrs') -> None:
        """
        Sign the XML document with the specified signature.
        
        Args:
            xml_doc: The XML document to sign
            signature_id: The ID of the signature to use
        """
        if not self.signatures:
            raise ValueError("No signatures available for signing")
            
        # Find the signature element
        signature = xml_doc.find(f".//{{{DS_NS}}}Signature[@Id='{signature_id}']")
        if signature is None:
            # If signature element doesn't exist, create it
            signature = self.to_xml()
            xml_doc.append(signature)
        
        # Get the signature data
        sig_data = next((s for s in self.signatures if s.get('id') == signature_id), None)
        if not sig_data:
            raise ValueError(f"No signature found with ID: {signature_id}")
            
        # Sign the document
        self._sign_document(
            signature,
            sig_data['key_data'],
            sig_data.get('key_password')
        )
    
    def _create_signature_element(self, sig_data: Dict[str, Any]) -> ET.Element:
        """
        Crée un élément de signature complet.
        
        Args:
            sig_data: Données de la signature
            
        Returns:
            L'élément Signature créé
        """
        sig_id = sig_data.get('signature_id', 'SigFrs')
        
        # Créer l'élément Signature
        signature = etree.Element(
            f'{{{DS_NS}}}Signature',
            {
                'Id': sig_id,
                'xmlns:ds': DS_NS,
                'xmlns:xades': XADES_NS
            }
        )
        
        # Créer l'élément SignedInfo
        signed_info = etree.SubElement(signature, f'{{{DS_NS}}}SignedInfo')
        
        # Ajouter la méthode de canonisation
        etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}CanonicalizationMethod',
            Algorithm='http://www.w3.org/2001/10/xml-exc-c14n#'
        )
        
        # Ajouter la méthode de signature
        etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}SignatureMethod',
            Algorithm='http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        )
        
        # Référence au contenu signé (r-id-frs)
        ref1 = self._create_reference(
            signed_info,
            uri='',
            reference_id=f'r-id-{sig_id}',
            transforms=[
                {
                    'algorithm': 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
                },
                {
                    'algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'
                }
            ]
        )
        
        # Référence aux propriétés XAdES
        ref2 = self._create_reference(
            signed_info,
            uri=f"#xades-{sig_id}",
            transforms=[
                {'algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'}
            ]
        )
        ref2.set('Type', 'http://uri.etsi.org/01903#SignedProperties')
        
        # Ajouter SignatureValue (vide pour l'instant)
        etree.SubElement(
            signature,
            f'{{{DS_NS}}}SignatureValue',
            {'Id': f'sig-value-{sig_id}'}
        )
        
        # Ajouter KeyInfo avec le certificat
        key_info = etree.SubElement(signature, f'{{{DS_NS}}}KeyInfo')
        x509_data = etree.SubElement(key_info, f'{{{DS_NS}}}X509Data')
        
        # Ajouter le certificat X509
        cert_value = sig_data.get('cert_data', '').replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').strip()
        etree.SubElement(
            x509_data, 
            f'{{{DS_NS}}}X509Certificate'
        ).text = cert_value
        
        # Ajouter les propriétés XAdES
        self._create_signed_properties(
            signature, 
            sig_id,
            role=sig_data.get('role'),
            name=sig_data.get('name')
        )
        
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
        Ajoute une signature à la section.

        Args:
            cert_data: Données du certificat au format PEM ou chemin vers le fichier
            key_data: Données de la clé privée ou chemin vers le fichier (optionnel)
            key_password: Mot de passe de la clé privée (optionnel)
            signature_id: Identifiant unique de la signature
            role: Rôle du signataire (optionnel)
            name: Nom du signataire (optionnel)
            date: Date de signature (par défaut: maintenant)
        """
        try:
            # Convertir cert_data en bytes si c'est une chaîne
            if isinstance(cert_data, str):
                if os.path.isfile(cert_data):
                    with open(cert_data, 'rb') as f:
                        cert_content = f.read()
                else:
                    cert_content = cert_data.encode('utf-8')
            else:
                cert_content = cert_data

            # Afficher les premières lignes du certificat pour le débogage
            cert_sample = cert_content[:100] if len(cert_content) > 100 else cert_content
            logger.debug(f"Contenu du certificat (début) : {cert_sample}...")

            # Valider le format du certificat
            if not self._is_valid_certificate(cert_content):
                logger.error("Le format du certificat est invalide")
                logger.debug(f"Contenu complet du certificat : {cert_content}")
                raise SignatureError("Format de certificat invalide. Assurez-vous que le certificat est au format PEM valide.")

            # Nettoyer le contenu du certificat
            if b'-----BEGIN CERTIFICATE-----' in cert_content:
                # Extraire uniquement la partie certificat (au cas où il y aurait des en-têtes supplémentaires)
                cert_parts = cert_content.split(b'-----BEGIN CERTIFICATE-----')
                if len(cert_parts) > 1:
                    cert_content = b'-----BEGIN CERTIFICATE-----' + cert_parts[1]
                
                # Nettoyer les sauts de ligne et les espaces
                cert_lines = []
                in_cert = False
                for line in cert_content.splitlines():
                    line = line.strip()
                    if line == b'-----BEGIN CERTIFICATE-----':
                        in_cert = True
                        cert_lines.append(line)
                    elif line == b'-----END CERTIFICATE-----':
                        in_cert = False
                        cert_lines.append(line)
                    elif in_cert and line:
                        # Supprimer tout ce qui n'est pas base64 valide
                        cert_lines.append(line.split(b' ')[0].split(b'\t')[0])
                
                cert_content = b'\n'.join(cert_lines)
                
                # Vérifier que le certificat commence et se termine correctement
                if not cert_content.startswith(b'-----BEGIN CERTIFICATE-----'):
                    cert_content = b'-----BEGIN CERTIFICATE-----\n' + cert_content
                if not cert_content.endswith(b'-----END CERTIFICATE-----'):
                    cert_content = cert_content + b'\n-----END CERTIFICATE-----'

            # Traitement de la clé privée
            key_content = None
            if key_data:
                if isinstance(key_data, str):
                    if os.path.isfile(key_data):
                        with open(key_data, 'rb') as f:
                            key_content = f.read()
                    else:
                        key_content = key_data.encode('utf-8')
                else:
                    key_content = key_data
                
                # Nettoyer la clé privée si nécessaire
                if key_content and b'-----BEGIN' in key_content:
                    key_lines = []
                    in_key = False
                    for line in key_content.splitlines():
                        line = line.strip()
                        if line.startswith(b'-----BEGIN'):
                            in_key = True
                            key_lines.append(line)
                        elif line.startswith(b'-----END'):
                            in_key = False
                            key_lines.append(line)
                        elif in_key and line:
                            key_lines.append(line)
                    
                    key_content = b'\n'.join(key_lines)

            # Stocker les données de signature
            self.signatures.append({
                'id': signature_id or f'sig-{uuid.uuid4()}',
                'cert_data': cert_content,
                'key_data': key_content,
                'key_password': key_password,
                'role': role,
                'name': name or 'Signataire',
                'date': date or datetime.utcnow(),
                'signature_value': b'[SIGNATURE VALUE]',
                'digest_value': b''
            })
            
            logger.info(f"Signature ajoutée avec succès (ID: {self.signatures[-1]['id']})")

        except Exception as e:
            if isinstance(e, SignatureError):
                raise
            error_msg = f"Échec de l'ajout de la signature: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise SignatureError(error_msg) from e
    
    def _is_valid_certificate(self, cert_data: Union[str, bytes]) -> bool:
        """
        Vérifie si les données du certificat sont valides.
        
        Args:
            cert_data: Données brutes du certificat
            
        Returns:
            bool: True si le certificat est valide, False sinon
        """
        try:
            # Vérifier si les données sont vides
            if not cert_data or (isinstance(cert_data, str) and not cert_data.strip()):
                logger.error("Les données du certificat sont vides")
                return False
                
            # Convertir en bytes si c'est une chaîne
            if isinstance(cert_data, str):
                cert_data = cert_data.encode('utf-8')
                
            # Vérifier la présence des marqueurs PEM de base
            if b'-----BEGIN CERTIFICATE-----' in cert_data and b'-----END CERTIFICATE-----' in cert_data:
                return True
                
            # Si on arrive ici, le format n'est pas reconnu
            logger.error("Format de certificat non reconnu. Le certificat doit être au format PEM.")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du certificat: {str(e)}")
            return False
            
    def to_xml(self, parent: Optional[ET.Element] = None) -> ET.Element:
        """
        Generate the XML representation of the signature section following XAdES-B standard.

        Args:
            parent: Parent element. If None, creates a new root element.
            
        Returns:
            The generated XML element
        """
        if not self.signatures:
            raise ValueError("No signatures to include in the XML")
            
        # We'll only use the first signature as per XAdES spec
        sig_data = self.signatures[0]
        sig_id = sig_data.get('id', 'SigFrs')
        
        # Define namespace map
        nsmap = {
            'ds': DS_NS,
            'xades': XADES_NS,
            'xsi': XSI_NS
        }
        
        # Create the Signature element with proper namespaces
        signature = etree.Element(
            f'{{{DS_NS}}}Signature',
            nsmap=nsmap,
            attrib={
                'Id': sig_id
            }
        )
        
        # Create SignedInfo
        signed_info = etree.SubElement(signature, f'{{{DS_NS}}}SignedInfo')
        
        # Add CanonicalizationMethod
        etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}CanonicalizationMethod',
            Algorithm=CANONICALIZATION_METHOD
        )
        
        # Add SignatureMethod
        etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}SignatureMethod',
            Algorithm=SIGNATURE_METHOD
        )
        
        # Add Reference for the signed document
        ref1 = etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}Reference',
            URI=''  # Reference to the root element
        )
        
        # Add Transforms
        transforms = etree.SubElement(ref1, f'{{{DS_NS}}}Transforms')
        etree.SubElement(
            transforms,
            f'{{{DS_NS}}}Transform',
            Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature'
        )
        
        # Add DigestMethod
        etree.SubElement(
            ref1,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm=DIGEST_METHOD
        )
        
        # Add DigestValue (placeholder for now)
        digest_value = etree.SubElement(ref1, f'{{{DS_NS}}}DigestValue')
        
        # Add Reference for SignedProperties
        ref2 = etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}Reference',
            Type='http://uri.etsi.org/01903#SignedProperties',
            URI='#xades-SigFrs'
        )
        
        # Add DigestMethod for SignedProperties
        etree.SubElement(
            ref2,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm=DIGEST_METHOD
        )
        
        # Add DigestValue for SignedProperties (placeholder for now)
        sp_digest_value = etree.SubElement(ref2, f'{{{DS_NS}}}DigestValue')
        
        # Add SignatureValue (will be filled later)
        signature_value = etree.SubElement(
            signature,
            f'{{{DS_NS}}}SignatureValue',
            Id='value-SigFrs'
        )
        
        # Add KeyInfo with X509Data
        key_info = etree.SubElement(signature, f'{{{DS_NS}}}KeyInfo')
        x509_data = etree.SubElement(key_info, f'{{{DS_NS}}}X509Data')
        
        # Add certificate
        cert_pem = sig_data.get('cert_data')
        if not cert_pem:
            raise SignatureError("No certificate data found in signature")
            
        # Ensure cert_pem is bytes
        if isinstance(cert_pem, str):
            cert_pem = cert_pem.encode('utf-8')
            
        # Load the certificate
        cert = load_pem_x509_certificate(cert_pem, default_backend())
        cert_der = cert.public_bytes(Encoding.DER)
        cert_digest = hashlib.sha256(cert_der).digest()
        cert_digest_b64 = base64.b64encode(cert_digest).decode('ascii')
        
        cert_clean = '\n'.join(
            line.strip()
            for line in cert_pem.decode('utf-8').split('\n')
            if line.strip() and not line.startswith('-----')
        )
        etree.SubElement(
            x509_data,
            f'{{{DS_NS}}}X509Certificate'
        ).text = cert_clean
        
        # Add Object with QualifyingProperties
        obj = etree.SubElement(signature, f'{{{DS_NS}}}Object')
        
        # Add QualifyingProperties
        qualifying_props = etree.SubElement(
            obj,
            f'{{{XADES_NS}}}QualifyingProperties',
            Target='#SigFrs',
            nsmap={'xades': XADES_NS}
        )
        
        # Add SignedProperties
        signed_props = etree.SubElement(
            qualifying_props,
            f'{{{XADES_NS}}}SignedProperties',
            Id='xades-SigFrs'
        )
        
        # Add SignedSignatureProperties
        signed_sig_props = etree.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedSignatureProperties'
        )
        
        # Add SigningTime
        signing_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        etree.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SigningTime'
        ).text = signing_time
        
        # Add SigningCertificate
        try:
            cert = load_pem_x509_certificate(cert_pem, default_backend())
            cert_der = cert.public_bytes(Encoding.DER)
            cert_digest = hashlib.sha256(cert_der).digest()
            cert_digest_b64 = base64.b64encode(cert_digest).decode('ascii')
            
            signing_cert = etree.SubElement(
                signed_sig_props,
                f'{{{XADES_NS}}}SigningCertificate'
            )
            cert_element = etree.SubElement(signing_cert, f'{{{XADES_NS}}}Cert')
            
            # Add CertDigest
            cert_digest_elem = etree.SubElement(cert_element, f'{{{XADES_NS}}}CertDigest')
            etree.SubElement(
                cert_digest_elem,
                f'{{{DS_NS}}}DigestMethod',
                Algorithm=DIGEST_METHOD
            )
            etree.SubElement(
                cert_digest_elem,
                f'{{{DS_NS}}}DigestValue'
            ).text = cert_digest_b64
            
            # Add IssuerSerial
            issuer_serial = etree.SubElement(cert_element, f'{{{XADES_NS}}}IssuerSerial')
            etree.SubElement(
                issuer_serial,
                f'{{{DS_NS}}}X509IssuerName'
            ).text = ' '.join(
                f"{name.oid._name}={name.value}" 
                for name in cert.issuer
            )
            etree.SubElement(
                issuer_serial,
                f'{{{DS_NS}}}X509SerialNumber'
            ).text = str(cert.serial_number)
            
        except Exception as e:
            raise SignatureError(f"Failed to process certificate: {str(e)}")
        
        # Add SignaturePolicyIdentifier
        policy_identifier = etree.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SignaturePolicyIdentifier'
        )
        policy_id = etree.SubElement(
            policy_identifier,
            f'{{{XADES_NS}}}SignaturePolicyId'
        )
        sig_policy_id = etree.SubElement(
            policy_id,
            f'{{{XADES_NS}}}SigPolicyId'
        )
        etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}Identifier',
            Qualifier='OID'
        ).text = "1.3.6.1.4.1.13762.3"
        etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}Description'
        ).text = "Politique de signature électronique pour la facturation électronique en Tunisie"
        
        # Convert lxml.etree element to xml.etree.ElementTree if parent is not None
        if parent is not None:
            # Import here to avoid circular imports
            import xml.etree.ElementTree as ET
            # Convert the lxml element to a string
            signature_str = etree.tostring(signature, encoding='unicode')
            # Parse it with xml.etree
            signature_element = ET.fromstring(signature_str)
            # Append to the parent
            parent.append(signature_element)
            return signature_element
            
        return signature

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
    sig_id = signature_data.get('id', f'sig-{uuid.uuid4()}')
    sig_type = signature_data.get('type', 'XAdES')
    timestamp = signature_data.get('timestamp', datetime.now(timezone.utc).isoformat())
    
    # Créer l'élément Signature avec les espaces de noms nécessaires
    signature = etree.SubElement(parent, f'{{{DS_NS}}}Signature')
    signature.set('Id', sig_id)
    
    # Ajouter les sous-éléments de base
    signed_info = etree.SubElement(signature, f'{{{DS_NS}}}SignedInfo')
    
    # CanonicalizationMethod
    canon_method = etree.SubElement(signed_info, f'{{{DS_NS}}}CanonicalizationMethod')
    canon_method.set('Algorithm', CANONICALIZATION_METHOD)
    
    # SignatureMethod
    sig_method = etree.SubElement(signed_info, f'{{{DS_NS}}}SignatureMethod')
    sig_method.set('Algorithm', SIGNATURE_METHOD)
    
    # References
    reference = etree.SubElement(signed_info, f'{{{DS_NS}}}Reference', URI=f'#{sig_id}-ref0')
    transforms = etree.SubElement(reference, f'{{{DS_NS}}}Transforms')
    etree.SubElement(transforms, f'{{{DS_NS}}}Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
    
    digest_method = etree.SubElement(reference, f'{{{DS_NS}}}DigestMethod', Algorithm=DIGEST_METHOD)
    digest_value = etree.SubElement(reference, f'{{{DS_NS}}}DigestValue')
    
    # SignatureValue
    etree.SubElement(signature, f'{{{DS_NS}}}SignatureValue')
    
    # KeyInfo
    key_info = etree.SubElement(signature, f'{{{DS_NS}}}KeyInfo')
    x509_data = etree.SubElement(key_info, f'{{{DS_NS}}}X509Data')
    etree.SubElement(x509_data, f'{{{DS_NS}}}X509Certificate')
    
    # Object pour XAdES
    obj = etree.SubElement(signature, f'{{{DS_NS}}}Object')
    
    # QualifyingProperties
    qualifying_props = etree.SubElement(
        obj, 
        f'{{{XADES_NS}}}QualifyingProperties',
        Target=f'#{sig_id}'
    )
    
    # SignedProperties
    signed_props = etree.SubElement(
        qualifying_props, 
        f'{{{XADES_NS}}}SignedProperties',
        Id=f'{sig_id}-signed-props'
    )
    
    # SignedSignatureProperties
    signed_sig_props = etree.SubElement(
        signed_props, 
        f'{{{XADES_NS}}}SignedSignatureProperties'
    )
    
    # SigningTime
    signing_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    etree.SubElement(
        signed_sig_props,
        f'{{{XADES_NS}}}SigningTime'
    ).text = signing_time
    
    # SigningCertificate
    signing_cert = etree.SubElement(
        signed_sig_props,
        f'{{{XADES_NS}}}SigningCertificate'
    )
    cert = etree.SubElement(signing_cert, f'{{{XADES_NS}}}Cert')
    
    cert_digest = etree.SubElement(cert, f'{{{XADES_NS}}}CertDigest')
    etree.SubElement(cert_digest, f'{{{DS_NS}}}Method', Algorithm=DIGEST_METHOD)
    etree.SubElement(cert_digest, f'{{{DS_NS}}}DigestValue')
    
    # SignaturePolicyIdentifier
    sig_policy_id = etree.SubElement(
        signed_sig_props,
        f'{{{XADES_NS}}}SignaturePolicyIdentifier'
    )
    sig_policy_id_elem = etree.SubElement(
        sig_policy_id,
        f'{{{XADES_NS}}}SignaturePolicyId'
    )
    sig_policy_id_id = etree.SubElement(
        sig_policy_id_elem,
        f'{{{XADES_NS}}}SigPolicyId'
    )
    etree.SubElement(
        sig_policy_id_id,
        f'{{{XADES_NS}}}Identifier'
    )
    
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
        signature = etree.SubElement(parent, "Signature")
        
        # ID de la signature
        if signature_data and 'id' in signature_data:
            signature.set("Id", str(signature_data['id']))
        
        # Informations sur le signataire
        signer_info = etree.SubElement(signature, "SignerInformation")
        
        # Rôle du signataire
        if signature_data and 'role' in signature_data:
            etree.SubElement(
                signer_info,
                "SignerRole",
                code=signature_data['role']
            )
        
        # Nom du signataire
        if signature_data and 'name' in signature_data:
            etree.SubElement(signer_info, "SignerName").text = str(signature_data['name'])
        
        # Date de signature
        sign_date = datetime.now()
        if signature_data and 'date' in signature_data and signature_data['date'] is not None:
            if isinstance(signature_data['date'], str):
                # Parse string to datetime if needed
                try:
                    sign_date = datetime.fromisoformat(signature_data['date'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    # If parsing fails, use current time
                    sign_date = datetime.now()
            elif isinstance(signature_data['date'], datetime):
                sign_date = signature_data['date']
        
        etree.SubElement(
            signature,
            "SigningTime"
        ).text = sign_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Données du certificat
        cert_info = etree.SubElement(signature, "SigningCertificate")
        
        # Empreinte numérique du certificat
        cert_digest = etree.SubElement(cert_info, "CertDigest")
        cert_digest.text = cert.digest('sha1').decode('ascii')
        
        # Données brutes du certificat (encodées en base64)
        cert_value = etree.SubElement(cert_info, "CertValue")
        cert_value.text = base64.b64encode(
            crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
        ).decode('ascii')
        
        # Si une clé privée est fournie, on peut signer le document
        if 'key' in cert_data:
            private_key = _load_private_key(
                cert_data['key'],
                cert_data.get('password')
            )
            
            # Créer une instance de SignatureSection pour utiliser sa méthode _sign_data
            signer = SignatureSection()
            
            # Créer la signature en utilisant la méthode d'instance
            signed_info = _create_signed_info(parent)
            signature_value = signer._sign_data(
                signed_info,
                private_key,
                cert_data.get('password')
            )
            
            # Ajouter la valeur de la signature
            sig_value = etree.SubElement(signature, "SignatureValue")
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
            cert_data = '\n'.join(
                line.strip()
                for line in cert_data.split('\n')
                if line.strip() and not line.startswith('---')
            )
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


def _load_private_key(
    key_data: Union[bytes, str],
    password: Optional[Union[str, bytes]] = None
):
    """
    Load a private key from PEM data.

    Args:
        key_data: The key data as bytes or string (PEM format)
        password: Optional password if the key is encrypted

    Returns:
        The loaded private key
        
    Raises:
        ValueError: If the key cannot be loaded
    """
    try:
        # Convert string to bytes if needed
        if isinstance(key_data, str):
            if os.path.isfile(key_data):
                with open(key_data, "rb") as f:
                    key_pem = f.read()
            else:
                key_pem = key_data.encode("utf-8")
                
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password = password.encode("utf-8")

        # Try loading as PKCS#8 first
        try:
            key = load_pem_private_key(
                key_pem,
                password=password,
                backend=default_backend()
            )
            return key
        except ValueError as e:
            if "Could not deserialize key data" in str(e):
                # If PKCS#8 fails, try PKCS#1 format by adding the appropriate headers
                if isinstance(key_pem, str):
                    key_pkcs1 = key_pem.encode('utf-8')
                else:
                    key_pkcs1 = key_pem
                    
                if b'-----BEGIN RSA PRIVATE KEY-----' not in key_pkcs1:
                    key_pkcs1 = (
                        b"-----BEGIN RSA PRIVATE KEY-----\n" +
                        key_pkcs1.replace(b" ", b"").replace(b"\n", b"") +
                        b"\n-----END RSA PRIVATE KEY-----"
                    )
                try:
                    key = load_pem_private_key(
                        key_pkcs1,
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
    # Convertir l'élément en chaîne XML
    xml_str = etree.tostring(element, encoding='utf-8', method='xml')
    
    # Parser avec xml.etree.ElementTree
    parser = etree.XMLParser()
    doc = etree.fromstring(xml_str, parser=parser)
    
    # Canonisation exclusive XML 1.0
    signed_info = etree.tostring(
        doc,
        method='c14n',
        exclusive=True,
        with_comments=False
    )
    
    return signed_info


def _sign_data(
    self,
    data: bytes,
    private_key_data: Union[bytes, str],
    password: Optional[Union[str, bytes]] = None
) -> bytes:
    """
    Sign data with a private key.

    Args:
        data: The data to be signed
        private_key_data: Private key as bytes or string (PEM)
        password: Optional password if the key is encrypted

    Returns:
        The signature as bytes

    Raises:
        SignatureError: If there's an error during signing
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        
        # Convert string to bytes if needed
        if isinstance(private_key_data, str):
            if os.path.isfile(private_key_data):
                with open(private_key_data, "rb") as f:
                    key_pem = f.read()
            else:
                key_pem = private_key_data.encode("utf-8")
                
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password = password.encode("utf-8")

        # Load private key
        key = load_pem_private_key(
            private_key_data,
            password=password,
            backend=default_backend()
        )
        
        # Sign the data
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
    Sign an XML document with XAdES-B signature according to TEIF specifications.
    
    Args:
        xml_data: The XML document to sign (as string or bytes)
        cert_pem: The signer's certificate in PEM format
        key_pem: The private key in PEM format
        key_password: Password for the private key (if encrypted)
        
    Returns:
        Signed XML document as bytes with proper XAdES-B signature
        
    Raises:
        SignatureError: If there's an error during the signing process
    """
    try:
        # Parse the input XML
        if isinstance(xml_data, str):
            xml_data = xml_data.encode('utf-8')
            
        # Parse the XML and ensure we have a root element
        parser = etree.XMLParser(remove_blank_text=True)
        try:
            root = etree.fromstring(xml_data, parser=parser)
        except etree.ParseError as e:
            raise SignatureError(f"Failed to parse XML: {str(e)}")
        
        # Register namespaces for proper XML serialization
        for prefix, uri in NSMAP.items():
            etree.register_namespace(prefix, uri)
        
        # Create the main Signature element with proper namespaces
        signature = etree.Element(
            f'{{{DS_NS}}}Signature',
            {
                'Id': 'SigFrs',
                'xmlns:ds': DS_NS,
                'xmlns:xades': XADES_NS
            }
        )
        
        # 1. Create SignedInfo
        signed_info = etree.SubElement(signature, f'{{{DS_NS}}}SignedInfo')
        
        # Add CanonicalizationMethod
        etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}CanonicalizationMethod',
            Algorithm=CANONICALIZATION_METHOD
        )
        
        # Add SignatureMethod
        etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}SignatureMethod',
            Algorithm=SIGNATURE_METHOD
        )
        
        # Add Reference to the signed data
        ref1 = etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}Reference',
            URI=''  # Reference to the root element
        )
        
        # Add Transforms
        transforms = etree.SubElement(ref1, f'{{{DS_NS}}}Transforms')
        etree.SubElement(
            transforms,
            f'{{{DS_NS}}}Transform',
            Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature'
        )
        
        # Add DigestMethod
        etree.SubElement(
            ref1,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm=DIGEST_METHOD
        )
        
        # Add DigestValue (placeholder for now)
        digest_value = etree.SubElement(ref1, f'{{{DS_NS}}}DigestValue')
        
        # Add Reference for SignedProperties
        ref2 = etree.SubElement(
            signed_info,
            f'{{{DS_NS}}}Reference',
            Type='http://uri.etsi.org/01903#SignedProperties',
            URI='#xades-SigFrs'
        )
        
        # Add DigestMethod for SignedProperties
        etree.SubElement(
            ref2,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm=DIGEST_METHOD
        )
        
        # Add DigestValue for SignedProperties (placeholder for now)
        sp_digest_value = etree.SubElement(ref2, f'{{{DS_NS}}}DigestValue')
        
        # 2. Add SignatureValue (will be filled later)
        signature_value = etree.SubElement(
            signature,
            f'{{{DS_NS}}}SignatureValue',
            Id='value-SigFrs'
        )
        
        # 3. Add KeyInfo with X509Data
        key_info = etree.SubElement(signature, f'{{{DS_NS}}}KeyInfo')
        x509_data = etree.SubElement(key_info, f'{{{DS_NS}}}X509Data')
        
        # Add certificate
        cert_clean = '\n'.join(
            line.strip()
            for line in cert_pem.decode('utf-8').split('\n')
            if line.strip() and not line.startswith('-----')
        )
        etree.SubElement(
            x509_data,
            f'{{{DS_NS}}}X509Certificate'
        ).text = cert_clean
        
        # 4. Add Object with QualifyingProperties
        obj = etree.SubElement(signature, f'{{{DS_NS}}}Object')
        
        # 4.1 Create QualifyingProperties
        qualifying_props = etree.SubElement(
            obj,
            f'{{{XADES_NS}}}QualifyingProperties',
            Target='#SigFrs',
            nsmap={'xades': XADES_NS}
        )
        
        # 4.2 Create SignedProperties
        signed_props = etree.SubElement(
            qualifying_props,
            f'{{{XADES_NS}}}SignedProperties',
            Id='xades-SigFrs'
        )
        
        # 4.3 Create SignedSignatureProperties
        signed_sig_props = etree.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedSignatureProperties'
        )
        
        # Add SigningTime
        signing_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        etree.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SigningTime'
        ).text = signing_time
        
        # Add SigningCertificate
        try:
            cert = load_pem_x509_certificate(cert_pem, default_backend())
            cert_der = cert.public_bytes(Encoding.DER)
            cert_digest = hashlib.sha256(cert_der).digest()
            cert_digest_b64 = base64.b64encode(cert_digest).decode('ascii')
            
            signing_cert = etree.SubElement(
                signed_sig_props,
                f'{{{XADES_NS}}}SigningCertificate'
            )
            cert_element = etree.SubElement(signing_cert, f'{{{XADES_NS}}}Cert')
            
            # Add CertDigest
            cert_digest_elem = etree.SubElement(cert_element, f'{{{XADES_NS}}}CertDigest')
            etree.SubElement(
                cert_digest_elem,
                f'{{{DS_NS}}}DigestMethod',
                Algorithm=DIGEST_METHOD
            )
            etree.SubElement(
                cert_digest_elem,
                f'{{{DS_NS}}}DigestValue'
            ).text = cert_digest_b64
            
            # Add IssuerSerial
            issuer_serial = etree.SubElement(cert_element, f'{{{XADES_NS}}}IssuerSerial')
            etree.SubElement(
                issuer_serial,
                f'{{{DS_NS}}}X509IssuerName'
            ).text = ' '.join(
                f"{name.oid._name}={name.value}" 
                for name in cert.issuer
            )
            etree.SubElement(
                issuer_serial,
                f'{{{DS_NS}}}X509SerialNumber'
            ).text = str(cert.serial_number)
            
        except Exception as e:
            raise SignatureError(f"Failed to process certificate: {str(e)}")
        
        # Add SignaturePolicyIdentifier
        policy_identifier = etree.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SignaturePolicyIdentifier'
        )
        policy_id = etree.SubElement(
            policy_identifier,
            f'{{{XADES_NS}}}SignaturePolicyId'
        )
        sig_policy_id = etree.SubElement(
            policy_id,
            f'{{{XADES_NS}}}SigPolicyId'
        )
        etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}Identifier',
            Qualifier='OID'
        ).text = "1.3.6.1.4.1.13762.3"
        etree.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}Description'
        ).text = "Politique de signature électronique pour la facturation électronique en Tunisie"
        
        # 5. Calculate digests and signature
        # 5.1 Calculate digest of the document (excluding signature)
        root_copy = copy.deepcopy(root)
        
        # Remove existing Signature elements to prevent recursion
        for elem in root_copy.findall(f'.//{{{DS_NS}}}Signature'):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)
        
        # Canonicalize the document
        try:
            c14n_doc = etree.tostring(
                root_copy,
                method='c14n',
                exclusive=True,
                with_comments=False
            )
            doc_digest = hashlib.sha256(c14n_doc).digest()
            doc_digest_b64 = base64.b64encode(doc_digest).decode('ascii')
            
            # Update digest value for reference 1 (document)
            digest_value.text = doc_digest_b64
            
            # 5.2 Calculate digest of the SignedProperties
            signed_props_c14n = etree.tostring(
                signed_props,
                method='c14n',
                exclusive=True,
                with_comments=False
            )
            signed_props_digest = hashlib.sha256(signed_props_c14n).digest()
            signed_props_digest_b64 = base64.b64encode(signed_props_digest).decode('ascii')
            
            # Update digest value for reference 2 (signed properties)
            sp_digest_value.text = signed_props_digest_b64
            
            # 5.3 Calculate signature value
            # Canonicalize SignedInfo
            signed_info_str = etree.tostring(signed_info, encoding='utf-8')
            signed_info_parsed = etree.fromstring(signed_info_str)
            signed_info_c14n = etree.tostring(
                signed_info_parsed,
                method='c14n',
                exclusive=True,
                with_comments=False,
                inclusive_ns_prefixes=None
            )
            
            # Sign the canonicalized SignedInfo
            private_key = _load_private_key(key_pem, key_password)
            signature_bytes = private_key.sign(
                signed_info_c14n,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Update signature value
            signature_value.text = base64.b64encode(signature_bytes).decode('ascii')
            
            # Add signature to the root element
            root.append(signature)
            
            # Create the final XML with proper declaration and namespaces
            xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            # Create a new root element with all necessary namespaces
            nsmap = {
                None: root.tag.split('}')[0][1:],  # Default namespace from root element
                'ds': DS_NS,
                'xades': XADES_NS,
                'xsi': XSI_NS,
                'xsd': XSD_NS
            }
            
            # Create a new root with proper namespaces
            new_root = etree.Element(root.tag, nsmap=nsmap)
            
            # Copy all attributes from original root
            for name, value in root.attrib.items():
                if not name.startswith('xmlns'):  # Skip existing xmlns declarations
                    new_root.set(name, value)
            
            # Copy all child elements
            for child in root:
                new_root.append(child)
            
            # Generate the final XML
            from lxml import etree
            xml_str = etree.tostring(
                new_root,
                encoding='UTF-8',
                method='xml',
                xml_declaration=False,
                pretty_print=True
            ).decode('utf-8')
            
            # Add XML declaration and ensure proper indentation
            return (xml_declaration + xml_str).encode('utf-8')
            
        except Exception as e:
            raise SignatureError(f"Error during signature calculation: {str(e)}")
            
    except Exception as e:
        raise SignatureError(f"Failed to sign XML: {str(e)}") from e
