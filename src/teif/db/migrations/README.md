# Gestion des Migrations de Base de Données

Ce dossier contient les migrations de base de données pour l'application TEIF, gérées par Alembic.

## Structure

- `versions/` : Contient les scripts de migration générés par Alembic
- `alembic.ini` : Fichier de configuration principal d'Alembic
- `env.py` : Configuration de l'environnement d'exécution des migrations
- `script.py.mako` : Modèle pour la génération des scripts de migration

## Commandes Utiles

### Créer une nouvelle migration
```bash
alembic revision --autogenerate -m "Description des modifications"
```

### Appliquer les migrations
```bash
alembic upgrade head
```

### Revenir à une version spécifique
```bash
alembic downgrade <revision>
```

### Voir l'état actuel
```bash
alembic current
```

### Voir l'historique des migrations
```bash
alembic history
```

## Bonnes Pratiques

1. **Toujours** créer une nouvelle migration pour les changements de schéma
2. Tester les migrations dans un environnement de développement avant la production
3. Sauvegarder la base de données avant d'appliquer des migrations
4. Documenter les migrations complexes dans les messages de commit

## Configuration

La configuration de la base de données peut être modifiée dans `alembic.ini` ou via la variable d'environnement `DATABASE_URL`.
