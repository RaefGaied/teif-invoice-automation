# TEIF Converter - Complete Architecture Documentation

## Architecture du Projet

### Vue d'ensemble

L'architecture du projet est conçue pour assurer une séparation claire des responsabilités et une facilité de maintenance. Voici les principaux composants :

#### 1. Diagramme d'Architecture Principal

![Architecture du Générateur TEIF](https://github.com/user-attachments/assets/64f109ab-fc9c-4c1c-bfd0-37f81d51b088 "Vue d'ensemble de l'architecture")

#### 2. Processus de Génération XML

![Processus de génération XML](https://github.com/user-attachments/assets/0b07bdd3-41c5-4461-82f0-4c7594c2317f "Flux de génération XML")

#### 3. Séquence des Étapes

![Séquence des étapes](https://github.com/user-attachments/assets/325185fa-4e5f-4d72-aa92-5deaf4522e9c "Séquence d'exécution")

#### 4. Structure XML

![Structure XML](https://github.com/user-attachments/assets/2d1bbd60-fb42-4151-b87c-1277f4eed44b "Structure du document XML")

### Légende des Diagrammes

- **En rose** : Point d'entrée principal (CLI)
- **En bleu clair** : Fichiers d'entrée/sortie
- **En vert clair** : Fichiers de configuration
- **Boîtes blanches** : Composants principaux

---

## Main Workflow

<img width="3840" height="2654" alt="main wokflow" src="https://github.com/user-attachments/assets/e125c0dc-6a4a-4c48-8b21-e999a6658f04" />

<img width="3840" height="2654" alt="main wokflow" src="https://github.com/user-attachments/assets/e125c0dc-6a4a-4c48-8b21-e999a6658f04" />


## Detailed Component Architecture

<img width="3840" height="1523" alt="Detailed Component Architecture" src="https://github.com/user-attachments/assets/ba503358-b287-4743-8543-ec25e9bd1af8" />

<img width="3840" height="1523" alt="Detailed Component Architecture" src="https://github.com/user-attachments/assets/ba503358-b287-4743-8543-ec25e9bd1af8" />

## TEIF XML Structure Flow

<img width="3840" height="2678" alt="TEIF XML Structure Flow" src="https://github.com/user-attachments/assets/a0f4b888-7210-43ae-92e3-55eea854d36c" />

<img width="3840" height="2678" alt="TEIF XML Structure Flow" src="https://github.com/user-attachments/assets/a0f4b888-7210-43ae-92e3-55eea854d36c" />


## Signature Generation Process

<img width="3840" height="2990" alt="Signature Generation Process" src="https://github.com/user-attachments/assets/ac16648b-6f0d-4c25-a445-eca2c663c9e5" />

<img width="3840" height="2990" alt="Signature Generation Process" src="https://github.com/user-attachments/assets/ac16648b-6f0d-4c25-a445-eca2c663c9e5" />


## Data Flow & Validation

<img width="869" height="3840" alt="Data Flow   Validation" src="https://github.com/user-attachments/assets/bf20c4d1-288a-4e6b-b2ae-18d977ed0248" />

<img width="869" height="3840" alt="Data Flow   Validation" src="https://github.com/user-attachments/assets/bf20c4d1-288a-4e6b-b2ae-18d977ed0248" />


## Key Features

### XAdES-B Electronic Signature
- **SignedInfo**: Contains canonicalization method, signature method, and document references
- **SignatureValue**: RSA-SHA256 signature of the SignedInfo element
- **KeyInfo**: X.509 certificate information for signature verification
- **QualifyingProperties**: XAdES-specific properties including signing time and certificate details

### TEIF Compliance
- **TTN Version 1.8.8**: Full compliance with Tunisie TradeNet specifications
- **XML Structure**: Proper TEIF document structure with all required elements
- **Validation**: Multi-level validation for data integrity and format compliance
- **Security**: XAdES-B signatures for document authenticity and non-repudiation

### Modular Architecture
- **Extractors**: PDF data extraction and normalization
- **Generators**: TEIF XML section generation
- **Validators**: Data and XML structure validation
- **CLI Interface**: Command-line tool for batch processing

## Technical Implementation

### Signature Section Components
- **Namespace Management**: Proper XML namespace handling for ds: and xades: prefixes
- **Certificate Handling**: X.509 certificate loading and validation
- **Digest Calculation**: SHA-256 hash computation for document integrity
- **Canonicalization**: XML-EXC-C14N for consistent XML representation
- **XPath Transformations**: Document reference filtering and processing

### Data Flow Architecture
- **Input Layer**: PDF files, configuration, and certificates
- **Processing Layer**: Extraction, normalization, and validation
- **Generation Layer**: TEIF XML structure creation
- **Security Layer**: XAdES-B signature application
- **Output Layer**: Signed TEIF XML compliant with TTN standards
