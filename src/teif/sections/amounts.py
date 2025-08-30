"""
Module pour la gestion des montants et des sections monétaires dans les documents TEIF.
"""
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET


def add_invoice_moa(parent: ET.Element, moa_data: Dict[str, Any]) -> None:
    """
    Ajoute la section InvoiceMoa au document TEIF.
    
    Args:
        parent: L'élément parent XML (InvoiceBody)
        moa_data: Dictionnaire contenant les montants à ajouter
            - amounts: Liste de dictionnaires, chaque dictionnaire contient:
                - amount_type_code: Code du type de montant (obligatoire, 6 caractères max)
                - amount: Montant numérique (obligatoire, max 15 chiffres avant la virgule)
                - currency: Code devise (TND, EUR, USD) - défaut: TND
                - description: Description textuelle du montant (optionnel, 500 caractères max)
                - lang: Langue de la description (AR, FR, EN) - défaut: FR
    """
    if not moa_data or 'amounts' not in moa_data or not moa_data['amounts']:
        return
    
    # Création de l'élément InvoiceMoa
    invoice_moa = ET.SubElement(parent, "InvoiceMoa")
    amount_details = ET.SubElement(invoice_moa, "AmountDetails")
    
    # Ajout de chaque montant
    for amount_info in moa_data['amounts']:
        _add_moa_detail(amount_details, amount_info)


def _add_moa_detail(parent: ET.Element, amount_info: Dict[str, Any]) -> None:
    """
    Ajoute un élément Moa avec ses détails.
    
    Args:
        parent: L'élément parent (AmountDetails)
        amount_info: Dictionnaire contenant les informations du montant
    """
    # Validation des champs obligatoires
    if 'amount_type_code' not in amount_info or 'amount' not in amount_info:
        raise ValueError("Les champs 'amount_type_code' et 'amount' sont obligatoires")
    
    # Préparation des attributs
    moa_attrs = {
        'amountTypeCode': str(amount_info['amount_type_code'])[:6],
        'currencyCodeList': 'ISO_4217'
    }
    
    # Création de l'élément Moa
    moa = ET.SubElement(parent, "Moa", **moa_attrs)
    
    # Ajout du montant
    amount = ET.SubElement(moa, "Amount")
    amount.set('currencyIdentifier', amount_info.get('currency', 'TND'))
    
    # Formatage du montant selon le pattern: -?[0-9]{1,15}(,[0-9]{2,5})?
    formatted_amount = _format_amount(amount_info['amount'])
    amount.text = formatted_amount
    
    # Ajout de la description si fournie
    if 'description' in amount_info:
        desc_attrs = {'lang': amount_info.get('lang', 'FR')}
        desc = ET.SubElement(moa, "AmountDescription", **desc_attrs)
        desc.text = str(amount_info['description'])[:500]  # Limite à 500 caractères


def _format_amount(amount: Any) -> str:
    """
    Formate un montant selon le format attendu par TEIF.
    
    Args:
        amount: Le montant à formater (nombre ou chaîne)
        
    Returns:
        str: Le montant formaté selon le pattern -?[0-9]{1,15}(,[0-9]{2,5})?
    """
    try:
        # Conversion en float pour gérer différents formats d'entrée
        num = float(str(amount).replace(',', '.'))
        
        # Formatage avec 3 décimales maximum
        formatted = f"{num:.3f}"
        
        # Suppression des zéros inutiles après la virgule
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        # Remplacement du point par une virgule si nécessaire
        formatted = formatted.replace('.', ',')
        
        # Vérification du format
        if not _is_valid_amount_format(formatted):
            raise ValueError(f"Format de montant invalide: {formatted}")
            
        return formatted
    except (ValueError, TypeError) as e:
        raise ValueError(f"Impossible de formater le montant: {amount}") from e


def _is_valid_amount_format(amount_str: str) -> bool:
    """
    Vérifie si le format du montant est valide selon le pattern TEIF.
    
    Args:
        amount_str: Le montant sous forme de chaîne
        
    Returns:
        bool: True si le format est valide, False sinon
    """
    import re
    pattern = r'^-?\d{1,15}(,\d{1,5})?$'
    return bool(re.match(pattern, amount_str))


# Export des fonctions publiques
__all__ = ['add_invoice_moa']
