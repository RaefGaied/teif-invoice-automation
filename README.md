# PDF to TEIF Converter

Convertisseur automatique de factures PDF vers le format TEIF (Tunisian Electronic Invoice Format) conforme aux standards TTN (Tunisie TradeNet) version 1.8.8.

## Description

Ce projet Python extrait automatiquement les données de factures depuis des fichiers PDF et les convertit en format XML TEIF conforme au standard tunisien d'échange électronique de factures (version 1.8.8).

### Fonctionnalités principales

- **Extraction intelligente** : Analyse avancée du contenu des PDFs pour extraire les données de facture
- **Conformité TEIF 1.8.8** : Génère du XML strictement conforme au standard TTN
- **Préservation des données** : Utilise les montants et taxes exactement comme trouvés dans le PDF, sans recalcul
- **Support multi-format** : Fonctionne avec différents formats de factures PDF
- **Architecture modulaire** : Code organisé en modules clairs et maintenables
- **Validation intégrée** : Vérification de la conformité du XML généré
- **Génération de signatures** : Support pour les signatures XAdES (optionnel)

## Structure TEIF XML

Le générateur produit des fichiers XML conformes à la structure TEIF 1.8.8 avec les éléments suivants :

```xml
<TEIF xmlns="http://www.tradenet.com.tn/teif/invoice/1.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd"
      version="1.8.8"
      controlingAgency="TTN">
  
  <!-- En-tête de la facture -->
  <DocumentIdentifier>FACT-12345</DocumentIdentifier>
  <DocumentType code="I-11">Facture</DocumentType>
  
  <!-- Section des partenaires -->
  <PartnerSection>
    <!-- Fournisseur -->
    <Partner functionCode="I-62">
      <Name nameType="Qualification">Nom du fournisseur</Name>
      <TaxId>12345678A</TaxId>
      <!-- Autres informations du fournisseur -->
    </Partner>
    
    <!-- Client -->
    <Partner functionCode="I-64">
      <Name nameType="Qualification">Nom du client</Name>
      <TaxId>87654321B</TaxId>
      <!-- Autres informations du client -->
    </Partner>
  </PartnerSection>
  
  <!-- Corps de la facture -->
  <InvoiceBody>
    <!-- Lignes de facture -->
    <Line>
      <LineNumber>1</LineNumber>
      <Item>
        <Description>Description de l'article</Description>
      </Item>
      <Quantity unit="PCE">1.0</Quantity>
      <Price>
        <Amount amountTypeCode="I-183" currencyIdentifier="TND">100.000</Amount>
      </Price>
      <LineTotal>
        <Amount amountTypeCode="I-171" currencyIdentifier="TND">100.000</Amount>
      </LineTotal>
    </Line>
    
    <!-- Totaux -->
    <InvoiceMoa>
      <Amount amountTypeCode="I-180" currencyIdentifier="TND">119.000</Amount>
      <Amount amountTypeCode="I-176" currencyIdentifier="TND">100.000</Amount>
      <Amount amountTypeCode="I-181" currencyIdentifier="TND">19.000</Amount>
    </InvoiceMoa>
    
    <!-- Taxes -->
    <InvoiceTax>
      <TaxTypeName code="I-1602">TVA</TaxTypeName>
      <TaxRate>19.0</TaxRate>
      <TaxableAmount>100.000</TaxableAmount>
      <TaxAmount>19.000</TaxAmount>
    </InvoiceTax>
  </InvoiceBody>
  
  <!-- Signature électronique -->
  <Signature>...</Signature>
  
</TEIF>
```

## Installation

### Prérequis

- Python 3.7 ou plus récent
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Dépendances principales

- `pdfplumber` : Extraction de texte depuis les PDFs
- `PyPDF2` : Fallback pour l'extraction PDF
- `lxml` : Génération et validation XML
- `signxml` : Signature XAdES (optionnel)

## Utilisation

### Conversion d'un fichier PDF

```bash
python main.py facture.pdf
```

### Spécifier un dossier de sortie

```bash
python main.py facture.pdf -o ./output
```

### Aperçu sans sauvegarde

```bash
python main.py facture.pdf --preview
```

### Tester avec des données d'exemple

```bash
python test_teif_generator.py tests/sample_invoice.pdf
```

### Aide

```bash
python main.py --help
```

## Structure du projet

```
TTN/
├── main.py                        # Point d'entrée principal
├── test_teif_generator.py         # Script de test du générateur
├── requirements.txt               # Dépendances
├── README.md                      # Documentation
├── docs/                          # Documentation technique
│   └── TEIF_XML_Structure_Analysis.md  # Analyse de la structure TEIF
├── src/                           # Code source
│   ├── __init__.py
│   ├── extractors/                # Modules d'extraction
│   │   ├── __init__.py
│   │   ├── base_extractor.py      # Classe de base pour l'extraction
│   │   ├── pdf_extractor.py       # Extraction depuis PDF
│   │   └── amount_validator.py    # Validation des montants
│   ├── teif/                      # Génération TEIF
│   │   ├── __init__.py
│   │   └── generator.py           # Générateur XML TEIF
│   └── cli/                       # Interface ligne de commande
│       ├── __init__.py
│       └── main.py                # Gestion des arguments CLI
├── public/                        # Fichiers de sortie
│   └── teif-invoices/             # XMLs TEIF générés
└── tests/                         # Tests
    └── sample_invoice.pdf         # Exemple de facture pour les tests
```

## Architecture technique

### Extraction des données

Le module `extractors` est responsable de l'extraction des données depuis les fichiers PDF. Il utilise une approche hybride :

1. Extraction du texte brut avec `pdfplumber`
2. Analyse syntaxique pour identifier les champs clés
3. Validation et normalisation des données extraites

### Génération TEIF

Le module `teif` gère la génération du XML conforme au standard TEIF 1.8.8 :

- Structure XML validée par schéma XSD
- Support des éléments obligatoires et conditionnels
- Gestion des formats de données spécifiques (dates, montants, etc.)

## Signature XAdES

Le projet prend en charge les signatures XAdES-BES pour les factures TEIF. La signature est générée à l'aide de la bibliothèque `signxml`.

### Génération de la signature

Pour générer une signature XAdES, vous devez fournir un certificat et une clé privée. Vous pouvez utiliser les outils de génération de certificats pour créer un certificat et une clé privée.

```bash
python scripts/generate_test_cert.py
```

Cela créera les fichiers suivants dans le répertoire `certs` :

- `ca.crt` - Certificat de l'autorité de certification
- `ca.key` - Clé privée de l'autorité de certification
- `server.crt` - Certificat du serveur
- `server.key` - Clé privée du serveur

### Ajout de la signature à la facture

Pour ajouter la signature à la facture, vous devez utiliser la classe `SignatureSection` du module `teif`.

```python
from src.teif.sections.signature import SignatureSection

# Créez une section de signature
signature = SignatureSection()

# Ajoutez la signature avec le certificat et la clé privée
with open('certs/server.crt', 'rb') as f:
    cert_data = f.read()

with open('certs/server.key', 'rb') as f:
    key_data = f.read()

signature.add_signature(
    cert_data=cert_data,
    key_data=key_data,
    key_password=None,  # Ajoutez un mot de passe si la clé est chiffrée
    signature_id='SIG-001',
    role='supplier',
    name='Votre nom d\'entreprise'
)

# Signez le document XML
signature.sign_document(votre_facture_xml_root)
```

## Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout d\'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/ma-nouvelle-fonctionnalite`)
5. Créez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Auteur

- **Votre Nom** - [@votrepseudo](https://github.com/votrepseudo)

## Remerciements

- L'équipe TTN pour la documentation du standard TEIF
- La communauté Python pour les bibliothèques utilisées
- Tous les contributeurs qui ont aidé à améliorer ce projet
