"""
Base Extractor Module
===================

Module définissant les classes de base pour l'extraction de données de factures.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExtractorConfig:
    """Configuration pour l'extraction de données."""
    date_formats: List[str] = None
    amount_decimal_separator: str = ","
    amount_thousands_separator: str = " "
    default_currency: str = "TND"
    remove_spaces: bool = True
    normalize_text: bool = True
    
class BaseFieldExtractor:
    """Classe de base pour l'extraction de champs spécifiques."""
    
    def __init__(self, config: ExtractorConfig):
        self.config = config
    
    def clean_amount(self, amount_str: str) -> float:
        """Nettoie et convertit une chaîne de montant en float."""
        if not amount_str:
            return 0.0
        
        # Supprimer les séparateurs de milliers
        cleaned = amount_str.replace(self.config.amount_thousands_separator, "")
        # Convertir le séparateur décimal
        cleaned = cleaned.replace(self.config.amount_decimal_separator, ".")
        # Supprimer tous les caractères non numériques sauf le point
        cleaned = "".join(c for c in cleaned if c.isdigit() or c == ".")
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def clean_date(self, date_str: str) -> Optional[datetime]:
        """Tente de parser une date selon les formats configurés."""
        if not date_str or not self.config.date_formats:
            return None
            
        for date_format in self.config.date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
        return None
    
    def clean_text(self, text: str) -> str:
        """Nettoie une chaîne de texte selon la configuration."""
        if not text:
            return ""
            
        cleaned = text.strip()
        if self.config.remove_spaces:
            cleaned = " ".join(cleaned.split())
        if self.config.normalize_text:
            cleaned = cleaned.upper()
        return cleaned

class BaseExtractor(ABC):
    """Classe de base abstraite pour l'extraction de données de factures."""
    
    def __init__(self, config: ExtractorConfig = None):
        self.config = config or ExtractorConfig()
        self.field_extractor = BaseFieldExtractor(self.config)
    
    @abstractmethod
    def extract(self, source: Any) -> Dict[str, Any]:
        """
        Extrait les données de la source.
        
        Args:
            source: La source des données (fichier, texte, etc.)
            
        Returns:
            Dict contenant les données extraites
        """
        pass
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Valide les données extraites.
        
        Args:
            data: Dictionnaire des données extraites
            
        Returns:
            Liste des erreurs de validation
        """
        errors = []
        required_fields = {
            "invoice_number": "Numéro de facture",
            "invoice_date": "Date de facture",
            "total_amount": "Montant total",
            "sender": "Informations fournisseur",
            "receiver": "Informations client"
        }
        
        for field, label in required_fields.items():
            if field not in data or not data[field]:
                errors.append(f"Champ obligatoire manquant: {label}")
                
        if "items" in data and not data["items"]:
            errors.append("Aucune ligne de facture trouvée")
            
        return errors
    
    def clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nettoie et normalise les données extraites.
        
        Args:
            data: Dictionnaire des données extraites
            
        Returns:
            Dictionnaire des données nettoyées
        """
        cleaned = {}
        
        # Nettoyage des champs textuels
        text_fields = ["invoice_number", "sender.name", "receiver.name", "description"]
        for field in text_fields:
            value = data
            parts = field.split(".")
            try:
                for part in parts[:-1]:
                    value = value[part]
                if parts[-1] in value:
                    value[parts[-1]] = self.field_extractor.clean_text(value[parts[-1]])
            except (KeyError, TypeError):
                continue
        
        # Nettoyage des montants
        amount_fields = ["total_amount", "amount_ht", "amount_ttc"]
        for field in amount_fields:
            if field in data:
                cleaned[field] = self.field_extractor.clean_amount(str(data[field]))
        
        # Nettoyage des dates
        date_fields = ["invoice_date", "due_date"]
        for field in date_fields:
            if field in data:
                cleaned[field] = self.field_extractor.clean_date(str(data[field]))
        
        # Nettoyage des articles
        if "items" in data and isinstance(data["items"], list):
            cleaned_items = []
            for item in data["items"]:
                cleaned_item = {
                    "description": self.field_extractor.clean_text(str(item.get("description", ""))),
                    "quantity": float(item.get("quantity", 0)),
                    "unit_price": self.field_extractor.clean_amount(str(item.get("unit_price", 0))),
                }
                if "taxes" in item:
                    cleaned_item["taxes"] = [
                        {
                            "tax_type": tax.get("tax_type", ""),
                            "rate": float(tax.get("rate", 0)),
                            "amount": self.field_extractor.clean_amount(str(tax.get("amount", 0)))
                        }
                        for tax in item["taxes"]
                    ]
                cleaned_items.append(cleaned_item)
            cleaned["items"] = cleaned_items
        
        return cleaned
