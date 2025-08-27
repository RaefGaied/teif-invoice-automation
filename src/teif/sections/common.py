"""
Module pour les fonctions utilitaires communes utilisées dans les sections TEIF.
"""
from typing import Any, Dict, Optional, Union
import re
from datetime import datetime, date

def format_date(value: Optional[Union[str, date, datetime]]) -> Optional[str]:
    """
    Formate une date au format ISO 8601 (YYYY-MM-DD).
    
    Args:
        value: Valeur à formater (chaîne, date ou datetime)
    
    Returns:
        Chaîne formatée ou None si la valeur est invalide
    """
    if value is None:
        return None
    
    if isinstance(value, (date, datetime)):
        return value.strftime('%Y-%m-%d')
    
    if isinstance(value, str):
        # Essayer de parser la date si c'est une chaîne
        try:
            # Format YYYY-MM-DD
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                return value
            # Format DD/MM/YYYY
            if re.match(r'^\d{2}/\d{2}/\d{4}$', value):
                dt = datetime.strptime(value, '%d/%m/%Y')
                return dt.strftime('%Y-%m-%d')
            # Format YYYYMMDD
            if re.match(r'^\d{8}$', value):
                dt = datetime.strptime(value, '%Y%m%d')
                return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            pass
    
    return None

def format_currency(amount: Any, default_currency: str = 'TND') -> Dict[str, str]:
    """
    Formate un montant et une devise.
    
    Args:
        amount: Montant à formater (peut être un nombre ou une chaîne)
        default_currency: Code devise par défaut (défaut: 'TND')
    
    Returns:
        Dictionnaire avec les clés 'amount' et 'currency'
    """
    if amount is None:
        return {'amount': '0.000', 'currency': default_currency}
    
    # Si c'est un dictionnaire avec amount et currency
    if isinstance(amount, dict) and 'amount' in amount:
        currency = amount.get('currency', default_currency)
        return {
            'amount': _format_amount(amount['amount']),
            'currency': str(currency).upper()
        }
    
    # Sinon, on suppose que c'est juste le montant
    return {
        'amount': _format_amount(amount),
        'currency': default_currency
    }

def _format_amount(value: Any) -> str:
    """
    Formate un montant avec 3 décimales.
    
    Args:
        value: Valeur à formater
    
    Returns:
        Chaîne formatée avec 3 décimales
    """
    try:
        # Essayer de convertir en float
        num = float(str(value).strip().replace(' ', '').replace(',', '.'))
        # Formater avec 3 décimales
        return f"{num:.3f}"
    except (ValueError, TypeError, AttributeError):
        return '0.000'

def get_nested_value(data: Dict, path: str, default: Any = None) -> Any:
    """
    Récupère une valeur imbriquée dans un dictionnaire en utilisant un chemin.
    
    Args:
        data: Dictionnaire source
        path: Chemin vers la valeur (ex: 'client.address.city')
        default: Valeur par défaut si le chemin n'existe pas
    
    Returns:
        La valeur trouvée ou la valeur par défaut
    """
    if not data or not path:
        return default
    
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current if current is not None else default

def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Nettoie un texte en supprimant les espaces superflus et en normalisant les sauts de ligne.
    
    Args:
        text: Texte à nettoyer
    
    Returns:
        Texte nettoyé ou None si le texte est vide
    """
    if not text:
        return None
    
    if not isinstance(text, str):
        text = str(text)
    
    # Remplacer les espaces multiples par un seul espace
    text = ' '.join(text.split())
    
    # Supprimer les espaces en début et fin
    text = text.strip()
    
    return text if text else None
