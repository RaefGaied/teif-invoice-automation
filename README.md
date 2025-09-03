<div align="center">
  <h1>🔄 TEIF Invoice Converter</h1>
  <h3>Conversion Automatique de Factures PDF vers le Format TEIF 1.8.8</h3>
  <img src="https://img.shields.io/badge/Version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.7+-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</div>

<div align="center">
  <img src="https://via.placeholder.com/800x200/2a2a72/ffffff?text=TEIF+Converter" alt="TEIF Converter Logo" width="100%">
  <p><em>Solution professionnelle de conversion de factures électroniques conforme aux normes tunisiennes</em></p>
</div>


## Table of Contents

- [Description](#description)
  - [Fonctionnalités principales](#fonctionnalités-principales)
- [Structure TEIF XML](#structure-teif-xml)
  - [Structure de Base](#structure-de-base)
  - [Points Importants](#points-importants)
- [Architecture du Projet](#architecture-du-projet)
  - [Vue d'ensemble](#vue-densemble)
  - [Workflow Principal](#workflow-principal)
  - [Architecture Détaillée des Composants](#architecture-détaillée-des-composants)
  - [Processus de Génération XML TEIF](#processus-de-génération-xml-teif)
  - [Structure XML et Séquence des Étapes](#structure-xml-et-séquence-des-étapes)
  - [Processus de Génération de Signature](#processus-de-génération-de-signature)
  - [Flux de Données et Validation](#flux-de-données-et-validation)
  - [Légende des Diagrammes](#légende-des-diagrammes)
- [Fonctionnalités Clés](#fonctionnalités-clés)
  - [Signature Électronique XAdES-B](#signature-électronique-xades-b)
  - [Conformité TEIF](#conformité-teif)
  - [Architecture Modulaire](#architecture-modulaire)
- [Implémentation Technique](#implémentation-technique)
  - [Composants de la Section de Signature](#composants-de-la-section-de-signature)
  - [Architecture du Flux de Données](#architecture-du-flux-de-données)
- [Structure du Projet](#structure-du-projet)
  - [Fichiers Racine Importants](#fichiers-racine-importants)
  - [Fichiers de Configuration](#fichiers-de-configuration)
- [Description des Composants Clés](#description-des-composants-clés)
- [Installation](#installation)
  - [Prérequis](#prérequis)
  - [Installation des dépendances](#installation-des-dépendances)
  - [Dépendances principales](#dépendances-principales)
- [Utilisation](#utilisation)
  - [Conversion d'un fichier PDF](#conversion-dun-fichier-pdf)
  - [Spécifier un dossier de sortie](#spécifier-un-dossier-de-sortie)
  - [Aperçu sans sauvegarde](#aperçu-sans-sauvegarde)
  - [Tester avec des données d'exemple](#tester-avec-des-données-dexemple)
  - [Aide](#aide)
- [Signature XAdES](#signature-xades)
  - [Génération de la signature](#génération-de-la-signature)
  - [Ajout de la signature à la facture](#ajout-de-la-signature-à-la-facture)
- [Contribution](#contribution)
- [Licence](#licence)
- [Auteur](#auteur)
- [Remerciements](#remerciements)



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

Le format TEIF (Tunisian Electronic Invoice Format) suit une structure XML spécifique. Voici un aperçu des éléments principaux :

### Structure de Base

```xml
<TEIF>
  <Header>
    <DocumentType>INVOICE</DocumentType>
    <DocumentNumber>FACT-2023-001</DocumentNumber>
    <DocumentDate>2023-01-01</DocumentDate>
    <Currency>DINAR TUNISIEN</Currency>
    <CurrencyCode>TND</CurrencyCode>
  </Header>
  
  <Seller>
    <Name>NOM DU VENDEUR</Name>
    <TaxIdentifier>
      <ID>IDENTIFIANT FISCAL</ID>
      <Type>FISCAL_NUMBER</Type>
    </TaxIdentifier>
  </Seller>
  
  <Buyer>
    <Name>NOM DE L'ACHETEUR</Name>
    <TaxIdentifier>...</TaxIdentifier>
  </Buyer>
  
  <Invoice>
    <InvoiceHeader>...</InvoiceHeader>
    <InvoiceLines>
      <Line>
        <LineNumber>1</LineNumber>
        <Item>
          <Description>DESCRIPTION DE L'ARTICLE</Description>
          <Quantity>1.000</Quantity>
          <UnitPrice>100.000</UnitPrice>
        </Item>
        <Moa amountTypeCode="I-181" currencyCodeList="ISO_4217">
          <Amount currencyIdentifier="TND">100.000</Amount>
          <AmountDescription lang="FR">Montant hors taxes</AmountDescription>
        </Moa>
      </Line>
    </InvoiceLines>
    
    <InvoiceTotals>
      <Moa amountTypeCode="I-181" currencyCodeList="ISO_4217">
        <Amount currencyIdentifier="TND">100.000</Amount>
        <AmountDescription lang="FR">Total hors taxes</AmountDescription>
      </Moa>
      <Moa amountTypeCode="I-182" currencyCodeList="ISO_4217">
        <Amount currencyIdentifier="TND">19.000</Amount>
        <AmountDescription lang="FR">Total TVA</AmountDescription>
      </Moa>
      <Moa amountTypeCode="I-183" currencyCodeList="ISO_4217">
        <Amount currencyIdentifier="TND">119.000</Amount>
        <AmountDescription lang="FR">Total TTC</AmountDescription>
      </Moa>
    </InvoiceTotals>
  </Invoice>
  
  <Signature>...</Signature>
</TEIF>
```


### Points Importants

1. **En-tête (Header)**
   - Contient les informations de base du document
   - Inclut le type de document, numéro, date et devise

2. **Vendeur et Acheteur**
   - Sections dédiées pour les informations des parties
   - Inclut les identifiants fiscaux

3. **Lignes de Facture**
   - Chaque ligne contient un article ou service
   - Inclut la description, quantité, prix unitaire et montant HT

4. **Totaux**
   - Montant HT
   - Montant TVA
   - Montant TTC
   - Autres totaux spécifiques

5. **Signature**
   - Signature électronique XAdES
   - Optionnelle selon le cas d'utilisation

### Attributs Spéciaux

- `currencyCodeList="ISO_4217"` : Obligatoire pour tous les éléments MOA
- `amountTypeCode` : Code indiquant le type de montant (ex: I-181 pour HT, I-182 pour TVA, etc.)
- `currencyIdentifier` : Code devise (TND pour Dinar Tunisien)

Pour plus de détails, consultez le fichier `docs/TEIF_XML_Structure_Analysis.md`.


## Architecture du Projet

### Vue d'ensemble

L'architecture du projet est conçue pour assurer une séparation claire des responsabilités et une facilité de maintenance. Le système intègre un flux de travail complet pour la conversion et la signature électronique de documents TEIF conformes aux standards Tunisie TradeNet.

### Workflow Principal

![Workflow Principal](https://github.com/user-attachments/assets/64f109ab-fc9c-4c1c-bfd0-37f81d51b088)

### Architecture Détaillée des Composants

![Architecture Détaillée](https://github.com/user-attachments/assets/ba503358-b287-4743-8543-ec25e9bd1af8)

### Processus de Génération XML TEIF

![Processus de Génération XML](https://github.com/user-attachments/assets/0b07bdd3-41c5-4461-82f0-4c7594c2317f)

![Génération XML Détaillée](https://github.com/user-attachments/assets/a0f4b888-7210-43ae-92e3-55eea854d36c)

### Structure XML et Séquence des Étapes

![Structure XML](https://github.com/user-attachments/assets/2d1bbd60-fb42-4151-b87c-1277f4eed44b)

![Séquence des Étapes](https://github.com/user-attachments/assets/325185fa-4e5f-4d72-aa92-5deaf4522e9c)

### Processus de Génération de Signature

![Génération de Signature](https://github.com/user-attachments/assets/ac16648b-6f0d-4c25-a445-eca2c663c9e5)

### Flux de Données et Validation

![Flux de Données](https://github.com/user-attachments/assets/bf20c4d1-288a-4e6b-b2ae-18d977ed0248)

### Légende des Diagrammes

- **En rose** : Point d'entrée principal (CLI)
- **En bleu clair** : Fichiers d'entrée/sortie
- **En vert clair** : Fichiers de configuration
- **Boîtes blanches** : Composants principaux

## Fonctionnalités Clés

### Signature Électronique XAdES-B

- **SignedInfo** : Contient la méthode de canonicalisation, la méthode de signature et les références du document
- **SignatureValue** : Signature RSA-SHA256 de l'élément SignedInfo
- **KeyInfo** : Informations du certificat X.509 pour la vérification de signature
- **QualifyingProperties** : Propriétés spécifiques XAdES incluant l'heure de signature et les détails du certificat

### Conformité TEIF

- **TTN Version 1.8.8** : Conformité complète avec les spécifications Tunisie TradeNet
- **Structure XML** : Structure de document TEIF correcte avec tous les éléments requis
- **Validation** : Validation multi-niveaux pour l'intégrité des données et la conformité du format
- **Sécurité** : Signatures XAdES-B pour l'authenticité et la non-répudiation des documents

### Architecture Modulaire

- **Extracteurs** : Extraction et normalisation des données PDF
- **Générateurs** : Génération des sections XML TEIF
- **Validateurs** : Validation des données et de la structure XML
- **Interface CLI** : Outil en ligne de commande pour le traitement par lots

## Implémentation Technique

### Composants de la Section de Signature

- **Gestion des namespaces** : Gestion appropriée des namespaces XML pour les préfixes ds: et xades:
- **Gestion des certificats** : Chargement et validation des certificats X.509
- **Calcul d'empreinte** : Calcul de hash SHA-256 pour l'intégrité du document
- **Canonicalisation** : XML-EXC-C14N pour une représentation XML cohérente
- **Transformations XPath** : Filtrage et traitement des références de document

### Architecture du Flux de Données

- **Couche d'entrée** : Fichiers PDF, configuration et certificats
- **Couche de traitement** : Extraction, normalisation et validation
- **Couche de génération** : Création de la structure XML TEIF
- **Couche de sécurité** : Application de la signature XAdES-B
- **Couche de sortie** : XML TEIF signé conforme aux standards TTN


## Structure du Projet

```
TTN/
├── .github/
│   └── workflows/
│       └── main.yml
├── certs/
│   ├── ca.crt
│   ├── ca.key
│   ├── server.crt
│   └── server.key
├── docs/
│   ├── TEIF_XML_Structure_Analysis.md
│   ├── teif_xml_structure_example.xml
│   └── XADES_SIGNATURE.md
├── examples/
│   └── sign_teif_invoice.py
├── extracted_data/
├── legacy/
│   ├── README.md
│   ├── transform_invoice.py
│   └── transform_invoice_simple.py
├── output/
│   └── complete_invoice.xml
├── public/
│   └── teif-invoices/
├── scripts/
│   └── generate_test_cert.py
├── src/
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── ...
│   └── teif/
│       ├── sections/
│       │   ├── __init__.py
│       │   ├── amounts.py
│       │   ├── common.py
│       │   ├── header.py
│       │   ├── lines.py
│       │   ├── partner.py
│       │   ├── payment.py
│       │   ├── references.py
│       │   ├── signature.py
│       │   └── taxes.py
│       ├── utils/
│       │   └── __init__.py
│       ├── __init__.py
│       └── generator.py
├── tests/
│   ├── test_data/
│   ├── test_output/
│   ├── conftest.py
│   ├── test_signature.py
│   └── test_*.py
├── .gitignore
├── .pytest_cache/
├── .vscode/
├── .venv/
├── .idea/
├── main.py
├── requirements.txt
├── setup.py
├── openssl.cnf
└── debug_extraction.py
```

### Fichiers Racine Importants
- `main.py` : Point d'entrée principal de l'application
- `requirements.txt` : Dépendances du projet
- `setup.py` : Configuration du package Python
- `openssl.cnf` : Configuration OpenSSL pour la génération de certificats
- `debug_extraction.py` : Utilitaire de débogage pour l'extraction

### Fichiers de Configuration
- `.gitignore` : Fichiers ignorés par Git
- `.pytest_cache/` : Cache des tests
- `.vscode/` : Configuration VS Code
- `.venv/` : Environnement virtuel Python
- `.idea/` : Configuration PyCharm/IntelliJ

## Description des Composants Clés

1. **Générateur TEIF** (`src/teif/generator.py`)
   - Classe principale pour la génération de documents TEIF
   - Gère la création de la structure XML
   - Coordonne les différents modules de génération

2. **Modules de Sections** (`src/teif/sections/`)
   - `header.py`: Gestion de l'en-tête TEIF et des métadonnées
   - `partner.py`: Gestion des parties (vendeur, acheteur, livraison)
   - `lines.py`: Génération des lignes de facture
   - `taxes.py`: Calcul et application des taxes
   - `payment.py`: Conditions et moyens de paiement
   - `amounts.py`: Gestion des montants et devises
   - `common.py`: Fonctions utilitaires partagées

3. **Interface en Ligne de Commande** (`src/cli/`)
   - Point d'entrée pour l'utilisation en ligne de commande
   - Gestion des arguments et options
   - Gestion des erreurs et journalisation

4. **Tests** (`tests/`)
   - Tests unitaires pour chaque composant
   - Tests d'intégration
   - Données de test et résultats attendus

5. **Utilitaires** (`scripts/`)
   - Scripts pour la gestion des certificats
   - Outils de développement

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
- `ca.key` - Clé privée de l'AC
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

- **Raef Gaied**

## Remerciements

- L'équipe TTN pour la documentation du standard TEIF
- La communauté Python pour les bibliothèques utilisées
- Tous les contributeurs qui ont aidé à améliorer ce projet
