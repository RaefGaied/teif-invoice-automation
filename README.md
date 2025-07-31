# PDF to TEIF Converter

Convertisseur automatique de factures PDF vers le format TEIF (Tunisian Electronic Invoice Format) conforme aux standards TTN.

## Description

Ce projet Python extrait automatiquement les données de factures depuis des fichiers PDF et les convertit en format XML TEIF conforme au standard tunisien d'échange électronique de factures.

### Fonctionnalités principales

- **Extraction automatique** : Analyse le contenu des PDFs pour extraire les données de facture
- **Conformité TEIF** : Génère du XML strictement conforme au standard TTN
- **Pas de recalculs** : Utilise les montants et taxes exactement comme trouvés dans le PDF
- **Support multi-format** : Fonctionne avec différents formats de factures PDF
- **Architecture modulaire** : Code organisé en modules clairs et maintenables
- **Interface simple** : Ligne de commande facile à utiliser

## Installation

### Prérequis

- Python 3.7 ou plus récent
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Dépendances

- `pdfplumber` : Extraction de texte depuis les PDFs (recommandé)
- `PyPDF2` : Fallback pour l'extraction PDF

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

### Générer avec des données d'exemple

```bash
python main.py --sample
```

### Aide

```bash
python main.py --help
```

## Structure du projet

```
TTN/
├── main.py                        # Point d'entrée principal
├── requirements.txt               # Dépendances
├── README.md                      # Documentation
├── src/                           # Code source modulaire
│   ├── __init__.py
│   ├── extractors/                # Modules d'extraction
│   │   ├── __init__.py
│   │   └── pdf_extractor.py       # Extraction depuis PDF
│   ├── teif/                      # Génération TEIF
│   │   ├── __init__.py
│   │   └── generator.py           # Générateur XML TEIF
│   ├── utils/                     # Utilitaires
│   │   ├── __init__.py
│   │   └── helpers.py             # Fonctions d'aide
│   └── cli/                       # Interface ligne de commande
│       ├── __init__.py
│       └── main.py                # CLI principal
├── public/                        # Fichiers de sortie
│   └── teif-invoices/            # XMLs TEIF générés
└── legacy/                        # Anciennes versions
    ├── transform_invoice.py       # Version complète (legacy)
    └── transform_invoice_simple.py # Version simplifiée (legacy)
```

## Architecture modulaire

### Modules principaux

- **`extractors/`** : Extraction de données depuis différents formats
  - `PDFExtractor` : Extraction depuis fichiers PDF

- **`teif/`** : Génération XML conforme au standard TEIF
  - `TEIFGenerator` : Générateur XML avec tous les éléments obligatoires

- **`utils/`** : Utilitaires et fonctions d'aide
  - Validation de fichiers, formatage, helpers divers

- **`cli/`** : Interface en ligne de commande
  - `PDFToTEIFConverter` : Classe principale de conversion
  - Interface utilisateur conviviale

### Avantages de cette structure

- **Maintenabilité** : Code organisé en modules spécialisés
- **Extensibilité** : Facile d'ajouter de nouveaux extracteurs ou formats
- **Testabilité** : Chaque module peut être testé indépendamment
- **Réutilisabilité** : Les modules peuvent être utilisés dans d'autres projets

## Format de sortie

Le script génère des fichiers XML conformes au standard TEIF avec tous les éléments obligatoires :

- **InvoiceHeader** : En-tête avec ID unique TTN
- **Bgm** : Début de message avec type et numéro de facture
- **Dtm** : Date/période
- **PartnerSection** : Détails des partenaires (fournisseur/client)
- **LinSection** : Lignes d'articles avec quantités, prix, taxes
- **InvoiceMoa** : Montants de facture
- **InvoiceTax** : Taxes de facture
- **RefTtnVal** : Référence de validation TTN
- **Signature** : Signature électronique (placeholder)

## Exemples

### Conversion simple

```bash
$ python main.py facture_exemple.pdf
📄 Traitement du fichier: facture_exemple.pdf
🔍 Extraction des données du PDF...
=== RÉSUMÉ EXTRACTION ===
Numéro: 20240001234567890
Date: 2024-01-15
Montant total: 1200.00 TND
Fournisseur: TRADENET TUNISIE
Client: ENTREPRISE CLIENT SARL
Articles: 1
Taxes: 1
========================
✅ Validation des données...
🔧 Génération du XML TEIF...
✅ Fichier TEIF généré: ./teif_facture_exemple.xml

🎉 Conversion terminée avec succès!
📁 Fichier généré: ./teif_facture_exemple.xml
```

### Aperçu des données d'exemple

```bash
$ python main.py --sample --preview
📋 Génération avec données d'exemple...
=== RÉSUMÉ EXTRACTION ===
Numéro: 20240001234567890
Date: 2024-01-15
Montant total: 1200.00 TND
Fournisseur: TRADENET TUNISIE
Client: ENTREPRISE CLIENT SARL
Articles: 1
Taxes: 1
========================

==================================================
APERÇU XML TEIF (DONNÉES EXEMPLE):
==================================================
<?xml version="1.0" ?>
<TEIFInvoice xmlns="http://www.tradenet.com.tn/teif/invoice/1.0"...>
...
</TEIFInvoice>
```

## Développement

### Utilisation des modules

```python
from src.extractors import PDFExtractor
from src.teif import TEIFGenerator
from src.utils import validate_pdf_file

# Extraction
extractor = PDFExtractor()
invoice_data = extractor.extract_from_pdf("facture.pdf")

# Génération TEIF
generator = TEIFGenerator()
teif_xml = generator.generate_xml(invoice_data)
```

### Personnalisation

Pour adapter le script à de nouveaux formats :

1. **Modifier les patterns** dans `src/extractors/pdf_extractor.py`
2. **Étendre le générateur** dans `src/teif/generator.py`
3. **Ajouter des utilitaires** dans `src/utils/helpers.py`
4. **Tester** avec vos fichiers spécifiques

### Tests

```bash
# Test avec données d'exemple
python main.py --sample --preview

# Test avec vos PDFs
python main.py votre_facture.pdf --preview
```

## Limitations

- **Extraction basée sur regex** : Peut nécessiter des ajustements pour certains formats de PDF
- **Pas de signature réelle** : Les éléments de signature sont des placeholders
- **Validation XSD** : Validation contre le schéma XSD TTN recommandée
- **Formats PDF complexes** : Les PDFs avec mise en page complexe peuvent nécessiter des améliorations

## Migration depuis les versions legacy

Si vous utilisiez les anciens scripts :

- `transform_invoice_simple.py` → `python main.py`
- `transform_invoice.py` → `python main.py` (même interface)

Les anciens scripts restent disponibles dans le dossier `legacy/` pour compatibilité.

## Support

Pour des questions ou problèmes :

1. Vérifiez que vos PDFs sont lisibles et contiennent du texte extractible
2. Testez d'abord avec `--preview` pour voir les données extraites
3. Ajustez les patterns regex si nécessaire pour votre format
4. Validez le XML généré contre le schéma XSD TTN

## Licence

Projet TTN - Convertisseur PDF vers TEIF

---

*Développé pour la conformité au standard TEIF (Tunisian Electronic Invoice Format) de TTN*

```xml
<?xml version="1.0" ?>
<TEIFInvoice xmlns="http://www.tradenet.com.tn/teif/invoice/1.0" 
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
             xsi:schemaLocation="http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd">
    <InvoiceHeader>
        <InvoiceNumber>INV-2024-001</InvoiceNumber>
        <InvoiceDate>2024-07-30</InvoiceDate>
{{ ... }}
        <TotalAmount>2000.00</TotalAmount>
    </InvoiceHeader>
    <!-- ... autres éléments ... -->
</TEIFInvoice>
```

## Support

Pour toute question ou problème, veuillez consulter la documentation officielle TTN ou contacter le support technique.
