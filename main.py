#!/usr/bin/env python3
"""
PDF to TEIF Converter - Point d'entrée principal
===============================================

Convertisseur automatique de factures PDF vers le format TEIF (Tunisian Electronic Invoice Format).

Usage:
    python main.py facture.pdf                    # Conversion simple
    python main.py facture.pdf -o ./output        # Spécifier dossier de sortie
    python main.py facture.pdf --preview          # Aperçu sans sauvegarde
    python main.py --sample                       # Générer avec données d'exemple
    python main.py --sample --preview             # Aperçu des données d'exemple

Auteur: TTN Project
Version: 1.0.0
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli.main import main

if __name__ == "__main__":
    main()
