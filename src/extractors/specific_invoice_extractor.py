"""
Specific Invoice Extractor
========================

Extracteur spécialisé pour un format de facture particulier.
"""

from typing import Dict, Any, List
import re
from .base_extractor import BaseExtractor, ExtractorConfig

class SpecificInvoiceExtractor(BaseExtractor):
    """Extracteur spécialisé pour un format de facture spécifique."""
    
    def __init__(self, config: ExtractorConfig = None):
        """Initialise l'extracteur avec une configuration spécifique."""
        super().__init__(config or ExtractorConfig(
            date_formats=["%d/%m/%Y", "%Y-%m-%d"],
            amount_decimal_separator=".",
            amount_thousands_separator=",",
            normalize_text=True
        ))
       
        self.patterns = {
            'invoice_number': [
                r'Facture[:\s]+([A-Z0-9-]+)',
                r'N°[:\s]*([A-Z0-9-]+)',
                r'Reference[:\s]+([A-Z0-9-]+)'
            ],
            'date': [
                r'Date[:\s]+(\d{2}[/.]\d{2}[/.]\d{4})',
                r'Émise le[:\s]+(\d{2}[/.]\d{2}[/.]\d{4})'
            ],
            'total_amount': [
                r'Total TTC[:\s]+(\d[\d\s,\.]+)',
                r'Montant à payer[:\s]+(\d[\d\s,\.]+)'
            ]
        }
        
       
        self.sections = {
            'header': (0, 0.2),    
            'items': (0.2, 0.7),   
            'totals': (0.7, 1.0)   
        }
    
    def extract(self, source: Any) -> Dict[str, Any]:
        """
        Extrait les données d'une facture selon un format spécifique.
        
        Args:
            source: Le contenu de la facture (PDF, texte, etc.)
            
        Returns:
            Dict contenant les données extraites
        """
        # Initialiser le dictionnaire de résultats
        extracted_data = {
            'invoice_number': '',
            'invoice_date': None,
            'sender': {},
            'receiver': {},
            'items': [],
            'total_amount': 0.0,
            'currency': self.config.default_currency
        }
        
        try:
            # Extraction selon le format spécifique
            text_content = self._get_text_content(source)
            
            # Extraire les informations de base
            extracted_data.update(self._extract_basic_info(text_content))
            
            # Extraire les informations des partenaires
            extracted_data.update(self._extract_partner_info(text_content))
            
            # Extraire les articles
            extracted_data['items'] = self._extract_items(text_content)
            
            # Extraire les montants
            extracted_data.update(self._extract_amounts(text_content))
            
            # Nettoyer les données extraites
            extracted_data = self.clean_extracted_data(extracted_data)
            
            # Valider les données
            errors = self.validate_extracted_data(extracted_data)
            if errors:
                print("Warnings during extraction:", errors)
                
        except Exception as e:
            print(f"Error during extraction: {str(e)}")
            
        return extracted_data
    
    def _get_text_content(self, source: Any) -> str:
        """Extrait le texte du document source."""
        # À implémenter selon le type de source
        return ""
    
    def _extract_basic_info(self, text: str) -> Dict[str, Any]:
        """Extrait les informations de base (numéro, date, etc.)."""
        info = {}
        
        # Numéro de facture
        for pattern in self.patterns['invoice_number']:
            match = re.search(pattern, text)
            if match:
                info['invoice_number'] = match.group(1)
                break
                
        # Date de facture
        for pattern in self.patterns['date']:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                info['invoice_date'] = self.field_extractor.clean_date(date_str)
                break
        
        return info
    
    def _extract_partner_info(self, text: str) -> Dict[str, Dict[str, str]]:
        """Extrait les informations des partenaires."""
        return {
            'sender': self._extract_partner_block(text, is_sender=True),
            'receiver': self._extract_partner_block(text, is_sender=False)
        }
    
    def _extract_partner_block(self, text: str, is_sender: bool) -> Dict[str, str]:
        """Extrait les informations d'un bloc partenaire."""
        # À personnaliser selon le format spécifique
        return {}
    
    def _extract_items(self, text: str) -> List[Dict[str, Any]]:
        """Extrait les lignes d'articles."""
        items = []
        # À personnaliser selon le format spécifique
        return items
    
    def _extract_amounts(self, text: str) -> Dict[str, float]:
        """Extrait les montants de la facture."""
        amounts = {
            'total_amount': 0.0,
            'amount_ht': 0.0,
            'amount_ttc': 0.0
        }
        
        # Total TTC
        for pattern in self.patterns['total_amount']:
            match = re.search(pattern, text)
            if match:
                amounts['total_amount'] = self.field_extractor.clean_amount(match.group(1))
                break
        
        return amounts
