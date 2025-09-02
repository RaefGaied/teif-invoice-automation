# Anciennes Versions et Scripts de Transition

Ce répertoire contient les anciennes versions du code et des scripts de transition qui ne font plus partie de la version actuelle du projet mais qui sont conservés à des fins de référence et de compatibilité.

## Contenu du Répertoire

### `transform_invoice.py`
Ancienne implémentation de la transformation des factures. Cette version a été remplacée par une architecture plus modulaire dans le dossier `src/`.

**Caractéristiques principales :**
- Conversion basique de factures au format TEIF
- Moins de fonctionnalités que la version actuelle
- Structure de code moins modulaire

### `transform_invoice_simple.py`
Version simplifiée du transformateur de factures, principalement utilisée pour les tests et le prototypage.

## Migration vers la Nouvelle Version

### Changements Majeurs
1. **Nouvelle Architecture Modulaire**
   - Séparation claire des préoccupations
   - Meilleure maintenabilité
   - Plus facile à étendre

2. **Nouvelles Fonctionnalités**
   - Support complet TEIF 1.8.8
   - Gestion avancée des taxes
   - Signature électronique XAdES
   - Meilleure gestion des erreurs

### Guide de Migration

Pour migrer depuis l'ancienne version :

1. **Mise à jour des Imports**
   ```python
   # Ancien
   from transform_invoice import generate_teif
   
   # Nouveau
   from src.teif.generator import TEIFGenerator
   ```

2. **Génération de Facture**
   ```python
   # Ancienne méthode
   xml_data = generate_teif(invoice_data)
   
   # Nouvelle méthode
   generator = TEIFGenerator()
   xml_data = generator.generate_teif_xml(invoice_data)
   ```

3. **Gestion des Erreurs**
   - La nouvelle version utilise des exceptions plus spécifiques
   - Meilleure journalisation des erreurs

## Compatibilité

Les fichiers dans ce répertoire sont fournis uniquement à des fins de référence. Il est fortement recommandé de migrer vers la nouvelle version pour bénéficier des dernières fonctionnalités et corrections de bogues.

## Aide Supplémentaire

Pour toute question sur la migration ou l'utilisation des anciennes versions, veuillez consulter la documentation principale ou ouvrir une issue sur le dépôt du projet.
