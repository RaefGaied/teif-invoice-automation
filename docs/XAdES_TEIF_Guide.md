# Guide Complet XAdES pour TEIF

## 🔐 Introduction aux Signatures XAdES

**XAdES** (XML Advanced Electronic Signatures) est un standard européen pour les signatures électroniques avancées dans les documents XML. Pour les factures TEIF (Tunisia Electronic Invoice Format), XAdES garantit :

- **Authenticité** : Vérification de l'identité du signataire
- **Intégrité** : Assurance que le document n'a pas été modifié
- **Non-répudiation** : Impossibilité de nier avoir signé
- **Conformité légale** : Respect des réglementations tunisiennes

## 📋 Types de Signatures XAdES

### XAdES-BES (Basic Electronic Signature)
- Signature de base avec certificat X.509
- Horodatage de signature
- Propriétés du signataire
- **Utilisé pour TEIF** ✅

### XAdES-EPES (Explicit Policy Electronic Signature)
- XAdES-BES + politique de signature explicite
- Définit les règles de validation

### XAdES-T (with Timestamp)
- XAdES-BES + horodatage externe
- Protection contre la révocation de certificat

### XAdES-LT (Long Term)
- XAdES-T + informations de révocation
- Validation à long terme

## 🏗️ Structure XAdES dans TEIF

\`\`\`xml
<TEIF xmlns="http://www.tn.gov/teif" version="1.8.8">
  <!-- Contenu de la facture -->
  <InvoiceHeader>...</InvoiceHeader>
  <Body>...</Body>
  
  <!-- Section de signature -->
  <SignatureSection lineNumber="999999">
    <SignerInfo lineNumber="999998">
      <SignerRole>supplier</SignerRole>
      <SignerName>Entreprise Émettrice</SignerName>
      <SignatureId>SIG-001</SignatureId>
    </SignerInfo>
    
    <!-- Signature XAdES -->
    <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" 
                  xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
      
      <!-- Informations signées -->
      <ds:SignedInfo>
        <ds:CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
        <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
        
        <!-- Référence au document -->
        <ds:Reference URI="">
          <ds:Transforms>
            <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
          </ds:Transforms>
          <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
          <ds:DigestValue>...</ds:DigestValue>
        </ds:Reference>
        
        <!-- Référence aux propriétés XAdES -->
        <ds:Reference Type="http://uri.etsi.org/01903#SignedProperties" URI="#SIG-001-SignedProperties">
          <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
          <ds:DigestValue>...</ds:DigestValue>
        </ds:Reference>
      </ds:SignedInfo>
      
      <!-- Valeur de signature -->
      <ds:SignatureValue>...</ds:SignatureValue>
      
      <!-- Informations de clé -->
      <ds:KeyInfo>
        <ds:X509Data>
          <ds:X509Certificate>...</ds:X509Certificate>
          <ds:X509SubjectName>...</ds:X509SubjectName>
          <ds:X509SerialNumber>...</ds:X509SerialNumber>
        </ds:X509Data>
      </ds:KeyInfo>
      
      <!-- Propriétés XAdES -->
      <ds:Object>
        <xades:QualifyingProperties Target="#SIG-001">
          <xades:SignedProperties Id="SIG-001-SignedProperties">
            
            <!-- Propriétés de signature -->
            <xades:SignedSignatureProperties>
              <xades:SigningTime>2024-09-01T15:30:00Z</xades:SigningTime>
              <xades:SigningCertificate>
                <xades:Cert>
                  <xades:CertDigest>
                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                    <ds:DigestValue>...</ds:DigestValue>
                  </xades:CertDigest>
                  <xades:IssuerSerial>
                    <ds:X509IssuerName>...</ds:X509IssuerName>
                    <ds:X509SerialNumber>...</ds:X509SerialNumber>
                  </xades:IssuerSerial>
                </xades:Cert>
              </xades:SigningCertificate>
            </xades:SignedSignatureProperties>
            
            <!-- Propriétés des données -->
            <xades:SignedDataObjectProperties>
              <xades:CommitmentTypeIndication>
                <xades:CommitmentTypeId>
                  <xades:Identifier Qualifier="OIDAsURI">http://uri.etsi.org/01903/v1.2.2#ProofOfApproval</xades:Identifier>
                  <xades:Description>Signature d'approbation de facture TEIF</xades:Description>
                </xades:CommitmentTypeId>
              </xades:CommitmentTypeIndication>
              
              <xades:SignerRole>
                <xades:ClaimedRoles>
                  <xades:ClaimedRole>Émetteur de facture</xades:ClaimedRole>
                </xades:ClaimedRoles>
              </xades:SignerRole>
            </xades:SignedDataObjectProperties>
          </xades:SignedProperties>
        </xades:QualifyingProperties>
      </ds:Object>
    </ds:Signature>
  </SignatureSection>
</TEIF>
\`\`\`

## 🔧 Processus de Signature

### 1. Préparation du Document
\`\`\`python
# Charger le document TEIF
teif_xml = load_teif_document("facture.xml")
root = ET.fromstring(teif_xml)
\`\`\`

### 2. Génération de la Signature
\`\`\`python
from src.teif.signature.xades_generator import XAdESGenerator

generator = XAdESGenerator()
signature = generator.create_signature_section(
    xml_document=root,
    certificate_path="certs/server.crt",
    private_key_path="certs/server.key",
    signature_id="SIG-001"
)
\`\`\`

### 3. Intégration dans TEIF
\`\`\`python
from src.teif.sections.signature import SignatureSection

signature_section = SignatureSection()
signature_section.add_signature_to_teif(
    teif_root=root,
    certificate_path="certs/server.crt",
    private_key_path="certs/server.key",
    role="supplier",
    name="Mon Entreprise"
)
\`\`\`

## 🔑 Gestion des Certificats

### Génération de Certificats de Test
\`\`\`bash
python scripts/generate_test_cert.py
\`\`\`

Cela génère :
- `certs/ca.crt` - Certificat d'autorité
- `certs/ca.key` - Clé privée CA
- `certs/server.crt` - Certificat serveur
- `certs/server.key` - Clé privée serveur

### Structure d'un Certificat X.509
\`\`\`
Subject: CN=TEIF Server Certificate, O=Test Company Server, C=TN
Issuer: CN=TEIF Test CA, O=Tunisia Tax Network, C=TN
Validity: 365 days
Key Usage: Digital Signature, Key Encipherment
\`\`\`

## ✅ Validation de Signature

### Vérification Automatique
\`\`\`python
from src.teif.sections.signature import SignatureSection

signature_section = SignatureSection()
is_valid = signature_section.verify_signature(signed_teif_xml)

if is_valid:
    print("✅ Signature valide")
else:
    print("❌ Signature invalide")
\`\`\`

### Points de Contrôle
1. **Intégrité du document** : Hash SHA-256 du contenu
2. **Validité du certificat** : Dates de validité, révocation
3. **Chaîne de confiance** : Vérification jusqu'à l'AC racine
4. **Conformité XAdES** : Structure et éléments requis

## 🚀 Utilisation Pratique

### Exemple Complet
\`\`\`python
from src.teif.signature.xades_generator import TEIFSignatureManager

# Créer le gestionnaire
manager = TEIFSignatureManager()

# Signer une facture
signed_xml = manager.sign_teif_invoice(
    teif_xml=original_teif,
    certificate_path="certs/company.crt",
    private_key_path="certs/company.key",
    signer_info={
        "Name": "Directeur Général",
        "Role": "Invoice Issuer",
        "Organization": "Ma Société SARL"
    }
)

# Sauvegarder
with open("facture_signee.xml", "w") as f:
    f.write(signed_xml)
\`\`\`

## 🔒 Sécurité et Bonnes Pratiques

### Protection des Clés Privées
- Stockage sécurisé (HSM, coffre-fort numérique)
- Chiffrement avec mot de passe fort
- Accès restreint et audité
- Rotation régulière des certificats

### Validation Stricte
- Vérification de la chaîne de certificats
- Contrôle des listes de révocation (CRL/OCSP)
- Validation des contraintes temporelles
- Audit des signatures

### Conformité Réglementaire
- Respect du cadre légal tunisien
- Archivage sécurisé des signatures
- Traçabilité des opérations
- Documentation des processus

## 🛠️ Dépannage

### Erreurs Courantes

#### "Certificate not found"
\`\`\`bash
# Vérifier l'existence du certificat
ls -la certs/
# Régénérer si nécessaire
python scripts/generate_test_cert.py
\`\`\`

#### "Invalid signature format"
\`\`\`python
# Vérifier la structure XAdES
signature = root.find(".//ds:Signature")
if signature is None:
    print("Signature manquante")
\`\`\`

#### "Key mismatch"
\`\`\`python
# Vérifier la correspondance certificat/clé
from cryptography import x509
cert = x509.load_pem_x509_certificate(cert_data)
# Comparer les clés publiques
\`\`\`

## 📚 Références

- **Standard XAdES** : ETSI TS 101 903
- **XML Signature** : W3C Recommendation
- **TEIF Specification** : Version 1.8.8
- **Cryptography Library** : Python cryptography
- **XML Processing** : xml.etree.ElementTree

---

*Ce guide couvre l'implémentation complète des signatures XAdES pour les factures TEIF. Pour des questions spécifiques, consultez la documentation technique ou contactez l'équipe de développement.*
