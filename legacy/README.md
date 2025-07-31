# Legacy Scripts

Ce dossier contient les anciennes versions du convertisseur PDF vers TEIF pour compatibilité.

## Scripts disponibles

- `transform_invoice.py` : Version complète originale avec toutes les fonctionnalités
- `transform_invoice_simple.py` : Version simplifiée sans recalculs

## Migration recommandée

Utilisez maintenant le nouveau script modulaire :

```bash
# Ancien
python legacy/transform_invoice_simple.py facture.pdf

# Nouveau (recommandé)
python main.py facture.pdf
```

Le nouveau script offre :
- Architecture modulaire plus maintenable
- Meilleure séparation des responsabilités
- Interface utilisateur améliorée
- Code plus facilement extensible

## Compatibilité

Les anciens scripts restent fonctionnels mais ne seront plus maintenus. Migrez vers la nouvelle version pour bénéficier des améliorations futures.
