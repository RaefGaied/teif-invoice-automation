"""
Module pour la gestion des signatures électroniques TEIF.
"""
from typing import Dict, Any, Optional, List, Union, Tuple, cast
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
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import logging
from lxml import etree as ET

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
        # Les espaces de noms sont gérés via NSMAP
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
        ref = ET.SubElement(parent, f'{{{DS_NS}}}Reference')
        if uri:
            ref.set('URI', uri)
        if reference_id:
            ref.set('Id', reference_id)
        
        # Ajouter les transformations
        if transforms:
            transforms_elem = ET.SubElement(ref, f'{{{DS_NS}}}Transforms')
            for transform in transforms:
                tf = ET.SubElement(
                    transforms_elem, 
                    f'{{{DS_NS}}}Transform',
                    Algorithm=transform['algorithm']
                )
                if 'xpath' in transform:
                    xpath = ET.SubElement(tf, f'{{{DS_NS}}}XPath')
                    xpath.text = transform['xpath']
        
        # Ajouter la méthode de hachage
        ET.SubElement(
            ref, 
            f'{{{DS_NS}}}DigestMethod',
            Algorithm=DIGEST_METHOD
        )
        
        # La valeur de hachage sera calculée plus tard
        ET.SubElement(ref, f'{{{DS_NS}}}DigestValue')
        
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
        obj = ET.SubElement(parent, f'{{{DS_NS}}}Object')
        
        # Créer l'élément QualifyingProperties
        qualifying_props = ET.SubElement(
            obj,
            f'{{{XADES_NS}}}QualifyingProperties',
            {
                'Target': f'#{sig_id}'
            }
        )
        
        # Créer l'élément SignedProperties
        signed_props = ET.SubElement(
            qualifying_props,
            f'{{{XADES_NS}}}SignedProperties',
            {
                'Id': f'xades-{sig_id}'
            }
        )
        
        # Créer l'élément SignedSignatureProperties
        sig_props = ET.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedSignatureProperties'
        )
        
        # Ajouter l'horodatage de signature
        signing_time = ET.SubElement(
            sig_props,
            f'{{{XADES_NS}}}SigningTime'
        )
        signing_time.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Ajouter la politique de signature
        sig_policy = ET.SubElement(
            sig_props,
            f'{{{XADES_NS}}}SignaturePolicyIdentifier'
        )
        sig_policy_id = ET.SubElement(
            sig_policy,
            f'{{{XADES_NS}}}SignaturePolicyId'
        )
        
        # Identifier de la politique
        sig_policy_id_el = ET.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyId'
        )
        ET.SubElement(
            sig_policy_id_el,
            f'{{{XADES_NS}}}Identifier'
        ).text = 'urn:oid:1.3.6.1.4.1.311.10.1.1'
        
        # Hachage de la politique
        sig_policy_hash = ET.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyHash'
        )
        ET.SubElement(
            sig_policy_hash,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm='http://www.w3.org/2001/04/xmlenc#sha256'
        )
        ET.SubElement(
            sig_policy_hash,
            f'{{{DS_NS}}}DigestValue'
        ).text = '3J1oMkha+OAlm9hBNCcAS+/nbKokG8Gf9N3XPipP7yg='
        
        # Qualifieurs de la politique
        sig_policy_qualifiers = ET.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyQualifiers'
        )
        sig_policy_qualifier = ET.SubElement(
            sig_policy_qualifiers,
            f'{{{XADES_NS}}}SigPolicyQualifier'
        )
        ET.SubElement(
            sig_policy_qualifier,
            f'{{{XADES_NS}}}SPURI'
        ).text = 'http://www.tradenet.com.tn/portal/telechargerTelechargement?lien=Politique_de_Signature_de_la_facture_electronique.pdf'
        
        # Rôle du signataire
        if role or name:
            signer_role = ET.SubElement(
                sig_props,
                f'{{{XADES_NS}}}SignerRole'
            )
            claimed_roles = ET.SubElement(
                signer_role,
                f'{{{XADES_NS}}}ClaimedRoles'
            )
            if role:
                ET.SubElement(
                    claimed_roles,
                    f'{{{XADES_NS}}}ClaimedRole'
                ).text = role
            if name:
                ET.SubElement(
                    claimed_roles,
                    f'{{{XADES_NS}}}ClaimedRole'
                ).text = name
        
        # SignedDataObjectProperties
        data_obj_props = ET.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedDataObjectProperties'
        )
        
        # DataObjectFormat pour la signature
        data_obj_format = ET.SubElement(
            data_obj_props,
            f'{{{XADES_NS}}}DataObjectFormat',
            ObjectReference=f'#r-id-{sig_id}'
        )
        ET.SubElement(
            data_obj_format,
            f'{{{XADES_NS}}}MimeType'
        ).text = 'text/xml'
        ET.SubElement(
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
        canonicalized = ET.tostring(
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
            node_str = ET.tostring(node, encoding='utf-8', method='xml')
            
            # For XAdES, we need to use exclusive XML canonicalization
            parser = ET.XMLParser(remove_blank_text=True)
            doc = ET.fromstring(node_str, parser=parser)
            
            # Apply exclusive canonicalization using lxml's c14n method
            c14n = ET.tostring(
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
            signed_info_str = ET.tostring(signed_info, encoding='utf-8')
            signed_info_parsed = ET.fromstring(signed_info_str)
            signed_info_c14n = ET.tostring(
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
        
        # Créer l'élément Signature avec les bons préfixes d'espace de noms
        signature = ET.Element(
            f'{{{DS_NS}}}Signature',
            {
                'Id': sig_id
            },
            nsmap={
                'ds': DS_NS,
                'xades': XADES_NS
            }
        )
        
        # Créer l'élément SignedInfo
        signed_info = ET.SubElement(signature, f'{{{DS_NS}}}SignedInfo')
        
        # Ajouter la méthode de canonisation
        ET.SubElement(
            signed_info,
            f'{{{DS_NS}}}CanonicalizationMethod',
            Algorithm='http://www.w3.org/2001/10/xml-exc-c14n#'
        )
        
        # Ajouter la méthode de signature
        ET.SubElement(
            signed_info,
            f'{{{DS_NS}}}SignatureMethod',
            Algorithm='http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
        )
        
        # Référence au contenu signé (r-id-frs)
        ref1 = self._create_reference(
            signed_info,
            uri='',
            reference_id=f'r-id-{sig_id}',
            transforms=[{
                'algorithm': 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
            }, {
                'algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#'
            }]
        )
        
        # Add reference to the SignedProperties
        ref2 = self._create_reference(
            signed_info,
            uri=f'#xades-{sig_id}',
            reference_id=f'xades-{sig_id}-ref',
            transforms=[{
                'algorithm': 'http://www.w3.org/2001/10/xml-exc-c14n#',
                'xpath': 'not(ancestor-or-self::ds:Signature)'
            }]
        )
        ref2.set('Type', 'http://uri.etsi.org/01903#SignedProperties')

        # Add the KeyInfo element with X509Data
        key_info = ET.SubElement(signature, f'{{{DS_NS}}}KeyInfo')
        x509_data = ET.SubElement(key_info, f'{{{DS_NS}}}X509Data')
        
        # Add the X509Certificate
        x509_cert = ET.SubElement(x509_data, f'{{{DS_NS}}}X509Certificate')
        if 'cert_data' in sig_data and sig_data['cert_data']:
            # Clean up the certificate data by removing headers/footers and whitespace
            cert_data = sig_data['cert_data']
            if isinstance(cert_data, str):
                cert_data = cert_data.encode('utf-8')
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
            cert_der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
            x509_cert.text = base64.b64encode(cert_der).decode('ascii')
        
        # Create the SignatureValue element (will be filled in later)
        ET.SubElement(signature, f'{{{DS_NS}}}SignatureValue')
        
        # Create the Object element for XAdES properties
        obj = ET.SubElement(signature, f'{{{DS_NS}}}Object')
        
        # Create the QualifyingProperties element with xades namespace
        qualifying_props = ET.SubElement(
            obj,
            f'{{{XADES_NS}}}QualifyingProperties',
            {
                'Target': f'#{sig_id}'
            }
        )
        
        # Create the SignedProperties element
        signed_props = ET.SubElement(
            qualifying_props,
            f'{{{XADES_NS}}}SignedProperties',
            {
                'Id': f'xades-{sig_id}'
            }
        )
        
        # Create SignedSignatureProperties
        signed_sig_props = ET.SubElement(
            signed_props,
            f'{{{XADES_NS}}}SignedSignatureProperties'
        )
        
        # Add SigningTime
        signing_time = ET.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SigningTime'
        )
        signing_time.text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Add SigningCertificate
        signing_cert = ET.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SigningCertificate'
        )
        
        cert_digest = ET.SubElement(
            signing_cert,
            f'{{{XADES_NS}}}Cert'
        )
        
        cert_digest_algo = ET.SubElement(
            cert_digest,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm='http://www.w3.org/2001/04/xmlenc#sha256'
        )
        
        cert_digest_value = ET.SubElement(
            cert_digest,
            f'{{{DS_NS}}}DigestValue'
        )
        
        # Calculate and set the certificate digest
        if 'cert_data' in sig_data and sig_data['cert_data']:
            cert_data = sig_data['cert_data']
            if isinstance(cert_data, str):
                cert_data = cert_data.encode('utf-8')
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
            cert_der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
            digest = hashlib.sha256(cert_der).digest()
            cert_digest_value.text = base64.b64encode(digest).decode('ascii')
        
        # Add SignaturePolicyIdentifier
        sig_policy = ET.SubElement(
            signed_sig_props,
            f'{{{XADES_NS}}}SignaturePolicyIdentifier'
        )
        
        sig_policy_id = ET.SubElement(
            sig_policy,
            f'{{{XADES_NS}}}SignaturePolicyId'
        )
        
        sig_policy_identifier = ET.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyId'
        )
        
        ET.SubElement(
            sig_policy_identifier,
            f'{{{XADES_NS}}}Identifier'
        ).text = 'urn:oid:1.3.6.1.4.1.311.10.1.1'
        
        sig_policy_hash = ET.SubElement(
            sig_policy_id,
            f'{{{XADES_NS}}}SigPolicyHash'
        )
        
        ET.SubElement(
            sig_policy_hash,
            f'{{{DS_NS}}}DigestMethod',
            Algorithm='http://www.w3.org/2001/04/xmlenc#sha256'
        )
        
        ET.SubElement(
            sig_policy_hash,
            f'{{{DS_NS}}}DigestValue'
        ).text = '3J1oMkha+OAlm9hBNCcAS+/nbKokG8Gf9N3XPipP7yg='
        
        # Add SignerRole if provided
        if 'role' in sig_data and sig_data['role']:
            signer_role = ET.SubElement(
                signed_sig_props,
                f'{{{XADES_NS}}}SignerRole'
            )
            
            claimed_roles = ET.SubElement(
                signer_role,
                f'{{{XADES_NS}}}ClaimedRoles'
            )
            
            claimed_role = ET.SubElement(
                claimed_roles,
                f'{{{XADES_NS}}}ClaimedRole'
            )
            claimed_role.text = sig_data['role']
        
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
            # Initialiser cert_content à None
            cert_content = None
            
            # Convertir cert_data en bytes si c'est une chaîne
            if isinstance(cert_data, str):
                if os.path.isfile(cert_data):
                    with open(cert_data, 'rb') as f:
                        cert_content = f.read()
                else:
                    cert_content = cert_data.encode('utf-8')
            elif isinstance(cert_data, bytes):
                cert_content = cert_data
            
            # Vérifier que le contenu du certificat a bien été chargé
            if cert_content is None:
                raise SignatureError("Aucune donnée de certificat valide fournie")
                
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
            
    def to_xml(self, parent: Optional[ET._Element] = None) -> ET._Element:
        """
        Generate the XML representation of the signature section following XAdES-B standard.

        Args:
            parent: Parent element. If provided, the signature will be appended to this element.
                  If None, a new root element will be created.
            
        Returns:
            The generated XML element (lxml.etree._Element)
        """
        if not self.signatures:
            raise ValueError("No signatures to include in the XML")
            
        # We'll only use the first signature as per XAdES spec
        sig_data = self.signatures[0]
        sig_id = sig_data.get('id', 'SigFrs')
        
        signature = self._create_signature_element(sig_data)
        
        # If parent is provided, append to it and return
        if parent is not None:
            if not hasattr(parent, 'tag') or not hasattr(parent, 'append'):
                raise TypeError("Parent must be an lxml.etree._Element")
            parent.append(signature)
            return signature
        
        return signature

def create_signature(cert_data: Union[str, bytes], 
                   key_data: Optional[Union[str, bytes]] = None,
                   key_password: Optional[str] = None,
                   signature_id: str = 'SigFrs',
                   role: Optional[str] = None,
                   name: Optional[str] = None,
                   date: Optional[Union[str, datetime]] = None) -> Dict[str, Any]:
    """
    Create a signature data dictionary for use with the SignatureSection.
    
    Args:
        cert_data: X.509 certificate in PEM format or path to certificate file
        key_data: Private key in PEM format or path to key file (optional)
        key_password: Password for the private key (if encrypted)
        signature_id: Unique identifier for the signature
        role: Role of the signer
        name: Name of the signataire
        date: Signature date (default: current time)
        
    Returns:
        Dictionary containing signature data
    """
    # If cert_data is a file path, read its contents
    if isinstance(cert_data, str) and os.path.isfile(cert_data):
        with open(cert_data, 'rb') as f:
            cert_data = f.read()
    
    # If key_data is a file path, read its contents
    if key_data is not None and isinstance(key_data, str) and os.path.isfile(key_data):
        with open(key_data, 'rb') as f:
            key_data = f.read()
    
    return {
        'x509_cert': cert_data,
        'private_key': key_data,
        'key_password': key_password,
        'signature_id': signature_id,
        'signer_role': role,
        'signer_name': name,
        'date': date or datetime.now(timezone.utc)
    }


def add_signature(signature_section: 'SignatureSection',
                 cert_data: Union[str, bytes],
                 key_data: Optional[Union[str, bytes]] = None,
                 key_password: Optional[str] = None,
                 signature_id: str = 'SigFrs',
                 role: Optional[str] = None,
                 name: Optional[str] = None,
                 date: Optional[Union[str, datetime]] = None) -> None:
    """
    Add a signature to a SignatureSection.
    
    This is a convenience function that creates and adds a signature in one step.
    
    Args:
        signature_section: The SignatureSection to add the signature to
        cert_data: X.509 certificate in PEM format or path to certificate file
        key_data: Private key in PEM format or path to key file (optional)
        key_password: Password for the private key (if encrypted)
        signature_id: Unique identifier for the signature
        role: Role of the signer
        name: Name of the signataire
        date: Signature date (default: current time)
    """
    signature_data = create_signature(
        cert_data=cert_data,
        key_data=key_data,
        key_password=key_password,
        signature_id=signature_id,
        role=role,
        name=name,
        date=date
    )
    
    signature_section.add_signature(**signature_data)


class SignatureError(Exception):
    """Erreur lors de la signature."""
    pass
