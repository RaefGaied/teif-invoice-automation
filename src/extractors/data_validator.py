"""
Module de validation intermédiaire des données extraites
====================================================

Permet de sauvegarder et valider les données extraites avant génération XML.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

class DataValidator:
    """Validateur de données extraites avant génération XML."""
    
    def __init__(self, output_dir: str = None):
        """Initialise le validateur avec un répertoire de sortie."""
        self.output_dir = output_dir or os.getcwd()
        
    def save_extracted_data(self, data: Dict[str, Any], source_file: str) -> str:
        """
        Sauvegarde les données extraites dans un fichier JSON.
        
        Args:
            data: Dictionnaire des données extraites
            source_file: Nom du fichier source
            
        Returns:
            Chemin du fichier JSON créé
        """
        # Créer un nom de fichier basé sur le fichier source
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        json_file = os.path.join(self.output_dir, f"{base_name}_data.json")
        
        # Ajouter des métadonnées
        data_with_meta = {
            "metadata": {
                "source_file": source_file,
                "extraction_date": datetime.now().isoformat(),
                "validation_status": self.validate_data(data)
            },
            "data": data
        }
        
        # Sauvegarder en JSON avec formatage lisible
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data_with_meta, f, indent=2, ensure_ascii=False)
            
        return json_file
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les données extraites.
        
        Returns:
            Dict avec statut et erreurs de validation
        """
        status = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validation des champs requis
        required_fields = {
            "invoice_number": "Numéro de facture",
            "invoice_date": "Date de facture",
            "total_amount": "Montant total",
            "sender": "Informations fournisseur",
            "receiver": "Informations client"
        }
        
        for field, label in required_fields.items():
            if field not in data or not data[field]:
                status["errors"].append(f"Champ obligatoire manquant: {label}")
                status["is_valid"] = False
        
        # Validation des montants
        if "total_amount" in data:
            if not isinstance(data["total_amount"], (int, float)):
                status["errors"].append("Le montant total doit être un nombre")
                status["is_valid"] = False
            elif data["total_amount"] <= 0:
                status["errors"].append("Le montant total doit être positif")
                status["is_valid"] = False
        
        # Validation des partenaires
        for partner_type in ["sender", "receiver"]:
            if partner_type in data:
                partner = data[partner_type]
                if not partner.get("name"):
                    status["warnings"].append(f"Nom du {partner_type} manquant")
                if not partner.get("identifier"):
                    status["warnings"].append(f"Identifiant du {partner_type} manquant")
        
        return status
    
    def load_json_data(self, json_file: str) -> Dict[str, Any]:
        """
        Charge les données depuis un fichier JSON.
        
        Args:
            json_file: Chemin vers le fichier JSON
            
        Returns:
            Dict contenant les données
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("data", {})  # Retourne uniquement les données, pas les métadonnées
    
    def print_validation_report(self, data: Dict[str, Any]):
        """Affiche un rapport de validation des données."""
        status = self.validate_data(data)
        
        print("\n=== RAPPORT DE VALIDATION ===")
        print(f"Statut: {'✅ Valide' if status['is_valid'] else '❌ Invalid'}")
        
        if status["errors"]:
            print("\n❌ Erreurs:")
            for error in status["errors"]:
                print(f"   - {error}")
                
        if status["warnings"]:
            print("\n⚠️ Avertissements:")
            for warning in status["warnings"]:
                print(f"   - {warning}")
                
        print("\n=== DONNÉES EXTRAITES ===")
        print(f"Numéro: {data.get('invoice_number', 'Non trouvé')}")
        print(f"Date: {data.get('invoice_date', 'Non trouvée')}")
        print(f"Montant total: {data.get('total_amount', 0.0):.3f} {data.get('currency', 'TND')}")
        print(f"Fournisseur: {data.get('sender', {}).get('name', 'Non trouvé')}")
        print(f"Client: {data.get('receiver', {}).get('name', 'Non trouvé')}")
        print("========================")
