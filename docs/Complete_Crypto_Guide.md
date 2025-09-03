# Guide Complet de Cryptographie pour TEIF

## 🎯 Vue d'Ensemble

Ce guide explique en détail tous les concepts cryptographiques utilisés dans les signatures électroniques TEIF :

1. **Certificats X.509** - Infrastructure de clés publiques
2. **Signature RSA** - Algorithme de signature numérique  
3. **Standard XAdES** - Signatures électroniques avancées

---

## 📜 1. CERTIFICATS X.509

### Qu'est-ce qu'un Certificat X.509 ?

Un **certificat X.509** est un document numérique qui :
- ✅ **Lie une clé publique à une identité** (personne, organisation, serveur)
- ✅ **Est signé par une Autorité de Certification** (CA) de confiance
- ✅ **Contient des métadonnées** sur le propriétaire
- ✅ **A une période de validité** définie

### Structure d'un Certificat X.509

\`\`\`
📋 CERTIFICAT X.509 v3
├── 🔢 Version (v3)
├── 🆔 Numéro de série (unique)
├── 🔐 Algorithme de signature (RSA-SHA256)
├── 👤 Émetteur (CA)
│   ├── CN = Autorité de Certification Tunisienne
│   ├── O = Direction Générale des Impôts
│   └── C = TN
├── ⏰ Période de validité
│   ├── Valide à partir de: 2024-01-01
│   └── Valide jusqu'à: 2025-01-01
├── 👥 Sujet (propriétaire)
│   ├── CN = Société Exemple SARL
│   ├── O = Société Exemple SARL
│   ├── C = TN
│   └── emailAddress = admin@exemple.tn
├── 🔑 Clé publique RSA (2048 bits)
└── 📋 Extensions
    ├── Key Usage (signature numérique)
    ├── Extended Key Usage (signature de code)
    └── Subject Alternative Name (DNS, email)
\`\`\`

### Processus de Création

\`\`\`python
# 1. Générer une paire de clés RSA
private_key = rsa.generate_private_key(
    public_exponent=65537,  # Standard
    key_size=2048          # Sécurisé
)

# 2. Définir l'identité (Subject)
subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "TN"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Mon Entreprise"),
    x509.NameAttribute(NameOID.COMMON_NAME, "facture.monentreprise.tn")
])

# 3. Construire le certificat
certificate = x509.CertificateBuilder().subject_name(subject)
    .issuer_name(ca_subject)  # Signé par la CA
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .sign(ca_private_key, hashes.SHA256())
\`\`\`

---

## 🔐 2. SIGNATURE RSA

### Principe de la Signature RSA

La **signature RSA** utilise la cryptographie asymétrique :

\`\`\`
🔑 PAIRE DE CLÉS RSA
├── 🔓 Clé Publique (n, e)
│   └── Pour VÉRIFIER les signatures
└── 🔒 Clé Privée (n, d)  
    └── Pour CRÉER les signatures
\`\`\`

### Algorithme RSA Détaillé

#### Génération des Clés
1. **Choisir deux nombres premiers** p et q (très grands)
2. **Calculer le module** n = p × q
3. **Calculer φ(n)** = (p-1) × (q-1)
4. **Choisir l'exposant public** e (généralement 65537)
5. **Calculer l'exposant privé** d tel que e × d ≡ 1 (mod φ(n))

#### Processus de Signature
\`\`\`python
# 1. Calculer le hachage du message
message = "Facture TEIF à signer"
hash_sha256 = hashlib.sha256(message.encode()).digest()

# 2. Signer le hachage avec la clé privée
signature = private_key.sign(
    hash_sha256,
    padding.PKCS1v15(),  # Schéma de padding
    hashes.SHA256()      # Algorithme de hachage
)

# 3. La signature est : signature = hash^d mod n
\`\`\`

#### Vérification de Signature
\`\`\`python
# 1. Déchiffrer la signature avec la clé publique
# decrypted_hash = signature^e mod n

# 2. Calculer le hachage du message reçu
received_hash = hashlib.sha256(received_message.encode()).digest()

# 3. Comparer les hachages
public_key.verify(signature, received_message, padding.PKCS1v15(), hashes.SHA256())
# ✅ Si identiques → signature valide
# ❌ Si différents → signature invalide
\`\`\`

### Schémas de Padding

#### PKCS#1 v1.5 (Classique)
\`\`\`
Format: 00 01 FF...FF 00 ASN.1 HASH
├── 00 01        : Indicateur de signature
├── FF...FF      : Padding avec 0xFF
├── 00           : Séparateur
├── ASN.1        : Identifiant d'algorithme
└── HASH         : Hachage du message
\`\`\`

#### PSS (Moderne - Recommandé)
\`\`\`
Format: Padding probabiliste avec sel aléatoire
├── 🎲 Sel aléatoire pour chaque signature
├── 🔒 Sécurité cryptographique renforcée
└── 📋 Résistance aux attaques avancées
\`\`\`

---

## ⭐ 3. STANDARD XAdES

### Qu'est-ce que XAdES ?

**XAdES** (XML Advanced Electronic Signatures) étend XML-DSig pour créer des signatures électroniques **juridiquement valides** :

- 🏛️ **Conforme aux réglementations européennes**
- 📋 **Propriétés de signature avancées**
- ⏰ **Support de la validation à long terme**
- 🔒 **Non-répudiation garantie**

### Niveaux XAdES

\`\`\`
📊 NIVEAUX XAdES (du plus simple au plus complexe)

🔹 XAdES-BES (Basic Electronic Signature)
├── Signature XML-DSig standard
├── Certificat du signataire
├── Horodatage de signature
└── Propriétés du signataire
└── 👉 UTILISÉ POUR TEIF

🔹 XAdES-EPES (Explicit Policy Electronic Signature)
├── Tout de XAdES-BES
└── + Politique de signature explicite

🔹 XAdES-T (with Timestamp)
├── Tout de XAdES-BES/EPES
└── + Horodatage d'une autorité externe

🔹 XAdES-LT (Long Term)
├── Tout de XAdES-T
└── + Informations de révocation (CRL/OCSP)

🔹 XAdES-LTA (Long Term with Archive)
├── Tout de XAdES-LT
└── + Horodatages d'archive périodiques
\`\`\`

### Structure XAdES Complète

\`\`\`xml
<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" 
              xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
  
  <!-- 1. INFORMATIONS SIGNÉES -->
  <ds:SignedInfo>
    <ds:CanonicalizationMethod Algorithm="..."/>
    <ds:SignatureMethod Algorithm="rsa-sha256"/>
    
    <!-- Référence au document -->
    <ds:Reference URI="">
      <ds:Transforms>
        <ds:Transform Algorithm="enveloped-signature"/>
      </ds:Transforms>
      <ds:DigestMethod Algorithm="sha256"/>
      <ds:DigestValue>ABC123...</ds:DigestValue>
    </ds:Reference>
    
    <!-- Référence aux propriétés XAdES -->
    <ds:Reference Type="SignedProperties" URI="#SIG-001-SignedProperties">
      <ds:DigestMethod Algorithm="sha256"/>
      <ds:DigestValue>XYZ789...</ds:DigestValue>
    </ds:Reference>
  </ds:SignedInfo>
  
  <!-- 2. VALEUR DE SIGNATURE -->
  <ds:SignatureValue>SIGNATURE_RSA_BASE64...</ds:SignatureValue>
  
  <!-- 3. INFORMATIONS DE CLÉ -->
  <ds:KeyInfo>
    <ds:X509Data>
      <ds:X509Certificate>CERTIFICAT_BASE64...</ds:X509Certificate>
      <ds:X509SubjectName>CN=Société,O=Org,C=TN</ds:X509SubjectName>
    </ds:X509Data>
  </ds:KeyInfo>
  
  <!-- 4. PROPRIÉTÉS XAdES -->
  <ds:Object>
    <xades:QualifyingProperties Target="#SIG-001">
      <xades:SignedProperties Id="SIG-001-SignedProperties">
        
        <!-- Propriétés de signature -->
        <xades:SignedSignatureProperties>
          <xades:SigningTime>2024-09-01T15:30:00Z</xades:SigningTime>
          <xades:SigningCertificate>
            <xades:Cert>
              <xades:CertDigest>
                <ds:DigestMethod Algorithm="sha256"/>
                <ds:DigestValue>CERT_HASH...</ds:DigestValue>
              </xades:CertDigest>
            </xades:Cert>
          </xades:SigningCertificate>
        </xades:SignedSignatureProperties>
        
        <!-- Propriétés des données -->
        <xades:SignedDataObjectProperties>
          <xades:CommitmentTypeIndication>
            <xades:CommitmentTypeId>
              <xades:Identifier>ProofOfApproval</xades:Identifier>
              <xades:Description>Signature d'approbation TEIF</xades:Description>
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
\`\`\`

### Processus de Validation XAdES

\`\`\`
🔍 VALIDATION XAdES COMPLÈTE

1️⃣ Validation XML-DSig
├── ✅ Intégrité du document (hachage SHA-256)
├── ✅ Signature cryptographique RSA
└── ✅ Correspondance certificat/clé publique

2️⃣ Validation du Certificat
├── ✅ Période de validité
├── ✅ Chaîne de certification
├── ✅ Statut de révocation (CRL/OCSP)
└── ✅ Contraintes d'utilisation

3️⃣ Validation XAdES
├── ✅ Cohérence des propriétés signées
├── ✅ Validité de l'horodatage
├── ✅ Conformité à la politique
└── ✅ Intégrité des références

4️⃣ Validation Contextuelle
├── ✅ Autorisation du signataire
├── ✅ Conformité réglementaire TEIF
├── ✅ Cohérence des données métier
└── ✅ Respect des procédures fiscales
\`\`\`

---

## 🚀 Utilisation Pratique

### Exemple Complet pour TEIF

\`\`\`python
from src.teif.signature.xades_complete_implementation import XAdESCompleteImplementation
from src.teif.signature.certificate_manager import CertificateManager

# 1. Créer les certificats
cert_manager = CertificateManager()
ca_cert, ca_key = cert_manager.create_ca_certificate()
certificate, private_key = cert_manager.create_end_entity_certificate(
    subject_name="Mon Entreprise SARL",
    organization="Mon Entreprise SARL", 
    email="facture@monentreprise.tn"
)

# 2. Créer le document TEIF
teif_root = ET.Element("TEIF")
# ... ajouter le contenu de la facture ...

# 3. Signer avec XAdES
xades_impl = XAdESCompleteImplementation()
signature = xades_impl.create_complete_xades_signature(
    teif_document=teif_root,
    certificate=certificate,
    private_key=private_key,
    signer_role="supplier"
)

# 4. Ajouter la signature au document
teif_root.append(signature)

# 5. Valider la signature
signed_xml = ET.tostring(teif_root, encoding='unicode')
validation = xades_impl.validate_xades_signature(signed_xml)

if validation['valid']:
    print("✅ Signature TEIF valide et conforme")
else:
    print("❌ Problèmes détectés:", validation['errors'])
\`\`\`

---

## 🔒 Sécurité et Bonnes Pratiques

### Protection des Clés Privées
- 🏦 **Stockage sécurisé** (HSM, coffre-fort numérique)
- 🔐 **Chiffrement avec mot de passe** fort
- 👥 **Accès restreint et audité**
- 🔄 **Rotation régulière** des certificats

### Validation Stricte
- 🔗 **Vérification de la chaîne** de certificats
- 📋 **Contrôle des listes de révocation** (CRL/OCSP)
- ⏰ **Validation des contraintes temporelles**
- 📊 **Audit complet** des signatures

### Conformité Réglementaire TEIF
- ⚖️ **Respect du cadre légal** tunisien
- 📁 **Archivage sécurisé** des signatures
- 📝 **Traçabilité complète** des opérations
- 📚 **Documentation** des processus

---

## 🎯 Résumé Exécutif

| Composant | Rôle | Sécurité | Usage TEIF |
|-----------|------|----------|------------|
| **Certificat X.509** | Identité numérique | Chaîne de confiance CA | Identification du signataire |
| **Signature RSA** | Preuve cryptographique | RSA-2048 + SHA-256 | Intégrité de la facture |
| **Standard XAdES** | Cadre juridique | Conformité européenne | Valeur légale en Tunisie |

### Avantages pour TEIF
- ✅ **Sécurité cryptographique** maximale
- ✅ **Conformité réglementaire** garantie  
- ✅ **Non-répudiation** juridique
- ✅ **Intégrité** des données fiscales
- ✅ **Authentification** des émetteurs

---

*Ce guide technique couvre tous les aspects cryptographiques nécessaires pour implémenter des signatures électroniques conformes TEIF. Pour des questions spécifiques, consultez la documentation technique ou l'équipe de développement.*
