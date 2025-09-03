# PDF to TEIF Converter

Un convertisseur Python pour transformer des factures PDF en format TEIF (Tunisian Electronic Invoice Format) XML conforme aux standards TTN (Tunisie TradeNet) version 1.8.8.

## Fonctionnalités

- Extraction automatique des données depuis les factures PDF
- Génération de XML TEIF conforme aux standards tunisiens
- Support des signatures électroniques XAdES-B
- Interface en ligne de commande (CLI)
- Architecture modulaire et extensible

## Installation

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Utilisation

\`\`\`bash
python cli.py --input facture.pdf --output facture_teif.xml
\`\`\`

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

## Structure XML TEIF

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

## Contribution

Les contributions sont les bienvenues ! Veuillez consulter les guidelines de contribution avant de soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
