from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TypeVar, Generic, Type
import json
import os

# Type variable for generic extractor configuration
T = TypeVar('T')

@dataclass
class ExtractorConfig:
    """Configuration de base pour les extracteurs."""
    date_formats: List[str] = field(
        default_factory=lambda: ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"]
    )
    amount_decimal_separator: str = ","
    amount_thousand_separator: str = " "
    default_currency: str = "TND"
    language: str = "fr"
    debug_mode: bool = False

class BaseExtractor(Generic[T]):
    """Classe de base pour l'extraction de données."""
    
    def __init__(self, config: Optional[ExtractorConfig] = None):
        """Initialise l'extracteur avec une configuration optionnelle."""
        self.config = config or ExtractorConfig()
        self._debug_log: List[str] = []
    
    def extract(self, source: Any) -> Dict[str, Any]:
        """Méthode principale d'extraction à implémenter par les sous-classes."""
        raise NotImplementedError("La méthode extract() doit être implémentée par les sous-classes")
    
    def save_extracted_data(self, data: Dict[str, Any], output_path: str, 
                          format: str = "txt", encoding: str = "utf-8") -> str:
        """
        Enregistre les données extraites dans un fichier.
        
        Args:
            data: Données à enregistrer
            output_path: Chemin de sortie (sans extension)
            format: Format de sortie ('txt' ou 'json')
            encoding: Encodage du fichier de sortie
            
        Returns:
            Chemin du fichier généré
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            return self._save_as_json(data, output_path, encoding)
        else:
            return self._save_as_text(data, output_path, encoding)
    
    def _save_as_text(self, data: Dict[str, Any], output_path: Path, 
                     encoding: str = "utf-8") -> str:
        """
        Enregistre les données au format texte lisible.
        
        Args:
            data: Données à enregistrer
            output_path: Chemin de sortie (sans extension)
            encoding: Encodage du fichier
            
        Returns:
            Chemin du fichier généré
        """
        text_lines = ["=== Données extraites ==="]
        text_lines.append(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        text_lines.append("=" * 50)
        
        for section, content in data.items():
            if isinstance(content, dict):
                text_lines.append(f"\n--- {section.upper()} ---")
                for key, value in content.items():
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, ensure_ascii=False, indent=2)
                    text_lines.append(f"{key}: {value}")
            else:
                text_lines.append(f"\n{section}: {content}")
        
        # Ajout des logs de débogage si en mode debug
        if self.config.debug_mode and self._debug_log:
            text_lines.append("\n=== LOGS DE DÉBOGAGE ===")
            text_lines.extend(self._debug_log)
        
        # Création du fichier
        output_file = output_path.with_suffix('.txt')
        with open(output_file, 'w', encoding=encoding) as f:
            f.write('\n'.join(text_lines))
        
        return str(output_file)
    
    def _save_as_json(self, data: Dict[str, Any], output_path: Path, 
                     encoding: str = "utf-8") -> str:
        """
        Enregistre les données au format JSON.
        
        Args:
            data: Données à enregistrer
            output_path: Chemin de sortie (sans extension)
            encoding: Encodage du fichier
            
        Returns:
            Chemin du fichier généré
        """
        output_file = output_path.with_suffix('.json')
        with open(output_file, 'w', encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2, 
                     default=self._json_serializer)
        
        return str(output_file)
    
    def _json_serializer(self, obj: Any) -> Any:
        """Sérialiseur personnalisé pour les objets non sérialisables par défaut."""
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Type {type(obj)} non sérialisable")
    
    def _log_debug(self, message: str) -> None:
        """Enregistre un message de débogage."""
        if self.config.debug_mode:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._debug_log.append(f"[{timestamp}] {message}")
    
    def _format_amount(self, amount_str: str) -> float:
        """
        Formate un montant selon la configuration de l'extracteur.
        
        Args:
            amount_str: Chaîne représentant le montant
            
        Returns:
            float: Montant formaté
        """
        if not amount_str:
            return 0.0
            
        # Nettoyage des espaces et remplacement des séparateurs
        clean_str = str(amount_str).strip()
        clean_str = clean_str.replace(self.config.amount_thousand_separator, "")
        clean_str = clean_str.replace(",", ".")
        
        try:
            return float(clean_str)
        except (ValueError, TypeError):
            self._log_debug(f"Impossible de convertir le montant: {amount_str}")
            return 0.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Tente de parser une date selon les formats configurés.
        
        Args:
            date_str: Chaîne représentant une date
            
        Returns:
            Objet datetime ou None si la date n'a pas pu être parsée
        """
        if not date_str:
            return None
            
        date_str = str(date_str).strip()
        
        for fmt in self.config.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        self._log_debug(f"Format de date non reconnu: {date_str}")
        return None