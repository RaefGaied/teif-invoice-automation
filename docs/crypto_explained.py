"""
Explication complète des concepts cryptographiques pour TEIF
- Certificats X.509
- Signature RSA
- Standard XAdES
"""

import hashlib
import base64
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID, ExtensionOID
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

class X509CertificateExplainer:
    """
    Explication détaillée des certificats X.509
    
    Un certificat X.509 est un document numérique qui :
    1. Lie une clé publique à une identité (personne, organisation, serveur)
    2. Est signé par une Autorité de Certification (CA)
    3. Contient des métadonnées sur le propriétaire
    4. A une période de validité définie
    """
    
    def __init__(self):
        self.examples = {}
    
    def explain_certificate_structure(self):
        """
        Structure d'un certificat X.509 v3
        
        Un certificat X.509 contient plusieurs champs obligatoires :
        """
        structure = {
            "Version": "Version du certificat (généralement v3)",
            "Serial Number": "Numéro de série unique attribué par la CA",
            "Signature Algorithm": "Algorithme utilisé pour signer le certificat",
            "Issuer": "Nom distingué (DN) de l'autorité de certification",
            "Validity": {
                "Not Before": "Date de début de validité",
                "Not After": "Date de fin de validité"
            },
            "Subject": "Nom distingué du propriétaire du certificat",
            "Subject Public Key Info": {
                "Algorithm": "Algorithme de la clé publique (RSA, ECDSA, etc.)",
                "Public Key": "La clé publique elle-même"
            },
            "Extensions": "Extensions optionnelles (v3 uniquement)"
        }
        
        print("=== STRUCTURE D'UN CERTIFICAT X.509 ===")
        self._print_structure(structure)
        
        return structure
    
    def _print_structure(self, obj, indent=0):
        """Affiche la structure de manière hiérarchique"""
        for key, value in obj.items():
            print("  " * indent + f"• {key}:")
            if isinstance(value, dict):
                self._print_structure(value, indent + 1)
            else:
                print("  " * (indent + 1) + f"→ {value}")
    
    def create_example_certificate(self):
        """
        Crée un certificat d'exemple pour démonstration
        """
        print("\n=== CRÉATION D'UN CERTIFICAT D'EXEMPLE ===")
        
        # 1. Générer une paire de clés RSA
        print("1. Génération de la paire de clés RSA...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,  # Exposant public standard
            key_size=2048          # Taille de clé (2048 bits = sécurisé)
        )
        public_key = private_key.public_key()
        
        # 2. Créer les informations du sujet
        print("2. Définition du sujet (Subject)...")
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "TN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tunis"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Tunis"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Société Exemple SARL"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Département IT"),
            x509.NameAttribute(NameOID.COMMON_NAME, "facture.exemple.tn"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "admin@exemple.tn")
        ])
        
        # 3. Créer les informations de l'émetteur (auto-signé)
        print("3. Définition de l'émetteur (Issuer)...")
        issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "TN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Autorité de Certification Tunisienne"),
            x509.NameAttribute(NameOID.COMMON_NAME, "CA Racine Tunisie")
        ])
        
        # 4. Construire le certificat
        print("4. Construction du certificat...")
        cert_builder = x509.CertificateBuilder()
        
        # Informations de base
        cert_builder = cert_builder.subject_name(subject)
        cert_builder = cert_builder.issuer_name(issuer)
        cert_builder = cert_builder.public_key(public_key)
        cert_builder = cert_builder.serial_number(x509.random_serial_number())
        
        # Période de validité
        now = datetime.utcnow()
        cert_builder = cert_builder.not_valid_before(now)
        cert_builder = cert_builder.not_valid_after(now + timedelta(days=365))
        
        # 5. Ajouter des extensions
        print("5. Ajout des extensions...")
        
        # Extension Key Usage (utilisation de la clé)
        cert_builder = cert_builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,    # Pour signer des documents
                key_encipherment=True,     # Pour chiffrer des clés
                key_agreement=False,
                key_cert_sign=False,       # Pas une CA
                crl_sign=False,
                content_commitment=True,   # Non-répudiation
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        
        # Extension Extended Key Usage
        cert_builder = cert_builder.add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.EMAIL_PROTECTION,
                x509.oid.ExtendedKeyUsageOID.CODE_SIGNING
            ]),
            critical=False
        )
        
        # Subject Alternative Name
        cert_builder = cert_builder.add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("facture.exemple.tn"),
                x509.DNSName("www.exemple.tn"),
                x509.RFC822Name("admin@exemple.tn")
            ]),
            critical=False
        )
        
        # 6. Signer le certificat
        print("6. Signature du certificat...")
        certificate = cert_builder.sign(private_key, hashes.SHA256())
        
        # 7. Analyser le certificat créé
        self.analyze_certificate(certificate)
        
        # Sauvegarder pour utilisation
        self.examples['certificate'] = certificate
        self.examples['private_key'] = private_key
        
        return certificate, private_key
    
    def analyze_certificate(self, certificate):
        """Analyse détaillée d'un certificat"""
        print("\n=== ANALYSE DU CERTIFICAT ===")
        
        print(f"Version: {certificate.version.name}")
        print(f"Numéro de série: {certificate.serial_number}")
        print(f"Algorithme de signature: {certificate.signature_algorithm_oid._name}")
        
        print(f"\nÉmetteur (Issuer):")
        for attribute in certificate.issuer:
            print(f"  {attribute.oid._name}: {attribute.value}")
        
        print(f"\nSujet (Subject):")
        for attribute in certificate.subject:
            print(f"  {attribute.oid._name}: {attribute.value}")
        
        print(f"\nValidité:")
        print(f"  Valide à partir de: {certificate.not_valid_before}")
        print(f"  Valide jusqu'à: {certificate.not_valid_after}")
        
        print(f"\nClé publique:")
        public_key = certificate.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            print(f"  Type: RSA")
            print(f"  Taille: {public_key.key_size} bits")
            print(f"  Exposant public: {public_key.public_numbers().e}")
        
        print(f"\nExtensions:")
        for extension in certificate.extensions:
            print(f"  {extension.oid._name}: {'Critique' if extension.critical else 'Non-critique'}")


class RSASignatureExplainer:
    """
    Explication détaillée de la signature RSA
    
    La signature RSA est un processus cryptographique qui :
    1. Prouve l'authenticité d'un message
    2. Garantit l'intégrité des données
    3. Assure la non-répudiation
    """
    
    def __init__(self):
        self.examples = {}
    
    def explain_rsa_algorithm(self):
        """
        Explication de l'algorithme RSA
        """
        print("=== ALGORITHME RSA EXPLIQUÉ ===")
        
        explanation = """
        RSA (Rivest-Shamir-Adleman) est un algorithme de cryptographie asymétrique basé sur :
        
        1. GÉNÉRATION DES CLÉS :
           • Choisir deux nombres premiers p et q
           • Calculer n = p × q (module)
           • Calculer φ(n) = (p-1) × (q-1)
           • Choisir e tel que 1 < e < φ(n) et pgcd(e, φ(n)) = 1
           • Calculer d tel que e × d ≡ 1 (mod φ(n))
           • Clé publique : (n, e)
           • Clé privée : (n, d)
        
        2. SIGNATURE :
           • Calculer le hachage H du message
           • Signature S = H^d mod n (avec la clé privée)
        
        3. VÉRIFICATION :
           • Calculer H' = S^e mod n (avec la clé publique)
           • Vérifier que H' = H (hachage original)
        """
        
        print(explanation)
    
    def demonstrate_signature_process(self, message="Facture TEIF à signer"):
        """
        Démonstration complète du processus de signature
        """
        print(f"\n=== DÉMONSTRATION DE SIGNATURE RSA ===")
        print(f"Message à signer: '{message}'")
        
        # 1. Générer une paire de clés
        print("\n1. Génération de la paire de clés RSA...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Afficher les paramètres de la clé
        private_numbers = private_key.private_numbers()
        public_numbers = public_key.public_numbers()
        
        print(f"   Taille de clé: 2048 bits")
        print(f"   Exposant public (e): {public_numbers.e}")
        print(f"   Module (n): {hex(public_numbers.n)[:50]}...")
        
        # 2. Calculer le hachage du message
        print(f"\n2. Calcul du hachage SHA-256...")
        message_bytes = message.encode('utf-8')
        hash_object = hashlib.sha256(message_bytes)
        message_hash = hash_object.digest()
        
        print(f"   Message original: {message}")
        print(f"   Message en bytes: {message_bytes}")
        print(f"   Hachage SHA-256: {message_hash.hex()}")
        print(f"   Taille du hachage: {len(message_hash)} bytes")
        
        # 3. Signer le hachage
        print(f"\n3. Signature RSA du hachage...")
        signature = private_key.sign(
            message_hash,
            padding.PKCS1v15(),  # Padding PKCS#1 v1.5
            hashes.SHA256()      # Algorithme de hachage
        )
        
        print(f"   Signature générée: {signature.hex()[:100]}...")
        print(f"   Taille de signature: {len(signature)} bytes")
        
        # 4. Vérifier la signature
        print(f"\n4. Vérification de la signature...")
        try:
            public_key.verify(
                signature,
                message_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            print("   ✅ Signature VALIDE")
        except Exception as e:
            print(f"   ❌ Signature INVALIDE: {e}")
        
        # 5. Démonstration de l'invalidité avec message modifié
        print(f"\n5. Test avec message modifié...")
        modified_message = message + " [MODIFIÉ]"
        modified_hash = hashlib.sha256(modified_message.encode()).digest()
        
        try:
            public_key.verify(
                signature,
                modified_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            print("   ❌ ERREUR: Signature valide pour message modifié!")
        except Exception:
            print("   ✅ Signature correctement REJETÉE pour message modifié")
        
        # Sauvegarder pour utilisation
        self.examples['private_key'] = private_key
        self.examples['public_key'] = public_key
        self.examples['signature'] = signature
        self.examples['message_hash'] = message_hash
        
        return signature, message_hash
    
    def explain_padding_schemes(self):
        """
        Explication des schémas de padding RSA
        """
        print("\n=== SCHÉMAS DE PADDING RSA ===")
        
        padding_info = {
            "PKCS#1 v1.5": {
                "Description": "Schéma de padding classique",
                "Sécurité": "Acceptable mais obsolescent",
                "Usage": "Compatibilité avec anciens systèmes",
                "Format": "00 01 FF...FF 00 ASN.1 HASH"
            },
            "PSS (Probabilistic Signature Scheme)": {
                "Description": "Schéma de padding moderne",
                "Sécurité": "Très sécurisé, recommandé",
                "Usage": "Nouvelles implémentations",
                "Format": "Padding aléatoire avec sel"
            }
        }
        
        for scheme, info in padding_info.items():
            print(f"\n{scheme}:")
            for key, value in info.items():
                print(f"  {key}: {value}")


class XAdESExplainer:
    """
    Explication complète du standard XAdES
    
    XAdES (XML Advanced Electronic Signatures) étend XML-DSig pour :
    1. Ajouter des propriétés de signature avancées
    2. Supporter la validation à long terme
    3. Respecter les réglementations européennes
    """
    
    def __init__(self):
        self.namespaces = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }
    
    def explain_xades_levels(self):
        """
        Explication des différents niveaux XAdES
        """
        print("=== NIVEAUX DE SIGNATURE XAdES ===")
        
        levels = {
            "XAdES-BES": {
                "Nom complet": "Basic Electronic Signature",
                "Description": "Signature de base avec certificat",
                "Composants": [
                    "Signature XML-DSig standard",
                    "Certificat du signataire",
                    "Horodatage de signature",
                    "Propriétés du signataire"
                ],
                "Usage": "Signatures simples, TEIF"
            },
            "XAdES-EPES": {
                "Nom complet": "Explicit Policy Electronic Signature", 
                "Description": "XAdES-BES + politique de signature",
                "Composants": [
                    "Tout de XAdES-BES",
                    "Référence à une politique de signature",
                    "Règles de validation explicites"
                ],
                "Usage": "Environnements réglementés"
            },
            "XAdES-T": {
                "Nom complet": "with Timestamp",
                "Description": "XAdES-BES/EPES + horodatage externe",
                "Composants": [
                    "Tout de XAdES-BES/EPES",
                    "Horodatage d'une autorité de confiance",
                    "Protection contre révocation"
                ],
                "Usage": "Signatures à moyen terme"
            },
            "XAdES-LT": {
                "Nom complet": "Long Term",
                "Description": "XAdES-T + informations de révocation",
                "Composants": [
                    "Tout de XAdES-T",
                    "Informations de révocation (CRL/OCSP)",
                    "Chaîne de certificats complète"
                ],
                "Usage": "Archivage long terme"
            },
            "XAdES-LTA": {
                "Nom complet": "Long Term with Archive timestamp",
                "Description": "XAdES-LT + horodatage d'archive",
                "Composants": [
                    "Tout de XAdES-LT",
                    "Horodatages d'archive périodiques",
                    "Protection contre obsolescence crypto"
                ],
                "Usage": "Archivage très long terme"
            }
        }
        
        for level, info in levels.items():
            print(f"\n🔹 {level} - {info['Nom complet']}")
            print(f"   Description: {info['Description']}")
            print(f"   Usage: {info['Usage']}")
            print(f"   Composants:")
            for component in info['Composants']:
                print(f"     • {component}")
    
    def create_xades_structure_example(self):
        """
        Crée un exemple de structure XAdES complète
        """
        print("\n=== STRUCTURE XAdES DÉTAILLÉE ===")
        
        # Créer la structure XML
        signature = ET.Element(f"{{{self.namespaces['ds']}}}Signature")
        signature.set("Id", "SIG-EXAMPLE-001")
        
        # 1. SignedInfo
        signed_info = ET.SubElement(signature, f"{{{self.namespaces['ds']}}}SignedInfo")
        
        # Canonicalization Method
        canon_method = ET.SubElement(signed_info, f"{{{self.namespaces['ds']}}}CanonicalizationMethod")
        canon_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        
        # Signature Method
        sig_method = ET.SubElement(signed_info, f"{{{self.namespaces['ds']}}}SignatureMethod")
        sig_method.set("Algorithm", "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")
        
        # Reference to document
        reference = ET.SubElement(signed_info, f"{{{self.namespaces['ds']}}}Reference")
        reference.set("URI", "")
        
        transforms = ET.SubElement(reference, f"{{{self.namespaces['ds']}}}Transforms")
        transform = ET.SubElement(transforms, f"{{{self.namespaces['ds']}}}Transform")
        transform.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        
        digest_method = ET.SubElement(reference, f"{{{self.namespaces['ds']}}}DigestMethod")
        digest_method.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")
        
        digest_value = ET.SubElement(reference, f"{{{self.namespaces['ds']}}}DigestValue")
        digest_value.text = "ABC123...DEF789"  # Exemple
        
        # Reference to XAdES properties
        xades_ref = ET.SubElement(signed_info, f"{{{self.namespaces['ds']}}}Reference")
        xades_ref.set("Type", "http://uri.etsi.org/01903#SignedProperties")
        xades_ref.set("URI", "#SIG-EXAMPLE-001-SignedProperties")
        
        xades_digest_method = ET.SubElement(xades_ref, f"{{{self.namespaces['ds']}}}DigestMethod")
        xades_digest_method.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")
        
        xades_digest_value = ET.SubElement(xades_ref, f"{{{self.namespaces['ds']}}}DigestValue")
        xades_digest_value.text = "XYZ456...UVW123"  # Exemple
        
        # 2. SignatureValue
        sig_value = ET.SubElement(signature, f"{{{self.namespaces['ds']}}}SignatureValue")
        sig_value.text = "SIGNATURE_BASE64_ENCODED_VALUE_HERE"
        
        # 3. KeyInfo
        key_info = ET.SubElement(signature, f"{{{self.namespaces['ds']}}}KeyInfo")
        x509_data = ET.SubElement(key_info, f"{{{self.namespaces['ds']}}}X509Data")
        
        x509_cert = ET.SubElement(x509_data, f"{{{self.namespaces['ds']}}}X509Certificate")
        x509_cert.text = "CERTIFICATE_BASE64_ENCODED_HERE"
        
        x509_subject = ET.SubElement(x509_data, f"{{{self.namespaces['ds']}}}X509SubjectName")
        x509_subject.text = "CN=Test Certificate,O=Test Org,C=TN"
        
        # 4. Object with XAdES properties
        obj = ET.SubElement(signature, f"{{{self.namespaces['ds']}}}Object")
        
        qualifying_props = ET.SubElement(obj, f"{{{self.namespaces['xades']}}}QualifyingProperties")
        qualifying_props.set("Target", "#SIG-EXAMPLE-001")
        
        signed_props = ET.SubElement(qualifying_props, f"{{{self.namespaces['xades']}}}SignedProperties")
        signed_props.set("Id", "SIG-EXAMPLE-001-SignedProperties")
        
        # SignedSignatureProperties
        signed_sig_props = ET.SubElement(signed_props, f"{{{self.namespaces['xades']}}}SignedSignatureProperties")
        
        signing_time = ET.SubElement(signed_sig_props, f"{{{self.namespaces['xades']}}}SigningTime")
        signing_time.text = "2024-09-01T15:30:00Z"
        
        signing_cert = ET.SubElement(signed_sig_props, f"{{{self.namespaces['xades']}}}SigningCertificate")
        cert = ET.SubElement(signing_cert, f"{{{self.namespaces['xades']}}}Cert")
        
        cert_digest = ET.SubElement(cert, f"{{{self.namespaces['xades']}}}CertDigest")
        cert_digest_method = ET.SubElement(cert_digest, f"{{{self.namespaces['ds']}}}DigestMethod")
        cert_digest_method.set("Algorithm", "http://www.w3.org/2001/04/xmlenc#sha256")
        
        cert_digest_value = ET.SubElement(cert_digest, f"{{{self.namespaces['ds']}}}DigestValue")
        cert_digest_value.text = "CERT_DIGEST_VALUE_HERE"
        
        # SignedDataObjectProperties
        signed_data_props = ET.SubElement(signed_props, f"{{{self.namespaces['xades']}}}SignedDataObjectProperties")
        
        commitment = ET.SubElement(signed_data_props, f"{{{self.namespaces['xades']}}}CommitmentTypeIndication")
        commitment_id = ET.SubElement(commitment, f"{{{self.namespaces['xades']}}}CommitmentTypeId")
        
        identifier = ET.SubElement(commitment_id, f"{{{self.namespaces['xades']}}}Identifier")
        identifier.set("Qualifier", "OIDAsURI")
        identifier.text = "http://uri.etsi.org/01903/v1.2.2#ProofOfApproval"
        
        # Afficher la structure créée
        self._print_xml_structure(signature)
        
        return signature
    
    def _print_xml_structure(self, element, indent=0):
        """Affiche la structure XML de manière lisible"""
        tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        attrs = ' '.join([f'{k}="{v}"' for k, v in element.attrib.items()])
        attrs_str = f" {attrs}" if attrs else ""
        
        print("  " * indent + f"<{tag_name}{attrs_str}>")
        
        if element.text and element.text.strip():
            print("  " * (indent + 1) + f"'{element.text.strip()}'")
        
        for child in element:
            self._print_xml_structure(child, indent + 1)
    
    def explain_xades_validation_process(self):
        """
        Explication du processus de validation XAdES
        """
        print("\n=== PROCESSUS DE VALIDATION XAdES ===")
        
        validation_steps = [
            {
                "Étape": "1. Validation XML-DSig",
                "Description": "Vérification de la signature XML de base",
                "Contrôles": [
                    "Intégrité du document (hachage)",
                    "Validité de la signature cryptographique",
                    "Correspondance certificat/clé publique"
                ]
            },
            {
                "Étape": "2. Validation du certificat",
                "Description": "Vérification du certificat X.509",
                "Contrôles": [
                    "Période de validité",
                    "Chaîne de certification",
                    "Statut de révocation (CRL/OCSP)",
                    "Contraintes d'utilisation"
                ]
            },
            {
                "Étape": "3. Validation XAdES",
                "Description": "Vérification des propriétés XAdES",
                "Contrôles": [
                    "Cohérence des propriétés signées",
                    "Validité de l'horodatage",
                    "Conformité à la politique de signature",
                    "Intégrité des références"
                ]
            },
            {
                "Étape": "4. Validation contextuelle",
                "Description": "Vérification du contexte métier",
                "Contrôles": [
                    "Autorisation du signataire",
                    "Conformité réglementaire",
                    "Cohérence des données métier",
                    "Respect des procédures"
                ]
            }
        ]
        
        for step in validation_steps:
            print(f"\n{step['Étape']}: {step['Description']}")
            for control in step['Contrôles']:
                print(f"  ✓ {control}")


# Démonstration complète
def main_demonstration():
    """
    Démonstration complète des concepts cryptographiques
    """
    print("🔐 DÉMONSTRATION COMPLÈTE DES CONCEPTS CRYPTOGRAPHIQUES POUR TEIF")
    print("=" * 80)
    
    # 1. Certificats X.509
    print("\n" + "="*50)
    print("PARTIE 1: CERTIFICATS X.509")
    print("="*50)
    
    x509_explainer = X509CertificateExplainer()
    x509_explainer.explain_certificate_structure()
    certificate, private_key = x509_explainer.create_example_certificate()
    
    # 2. Signature RSA
    print("\n" + "="*50)
    print("PARTIE 2: SIGNATURE RSA")
    print("="*50)
    
    rsa_explainer = RSASignatureExplainer()
    rsa_explainer.explain_rsa_algorithm()
    rsa_explainer.demonstrate_signature_process()
    rsa_explainer.explain_padding_schemes()
    
    # 3. XAdES
    print("\n" + "="*50)
    print("PARTIE 3: STANDARD XAdES")
    print("="*50)
    
    xades_explainer = XAdESExplainer()
    xades_explainer.explain_xades_levels()
    xades_explainer.create_xades_structure_example()
    xades_explainer.explain_xades_validation_process()
    
    print("\n" + "="*80)
    print("🎉 DÉMONSTRATION TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    main_demonstration()
