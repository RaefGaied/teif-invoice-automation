"""
Utilities and Helpers
=====================

Fonctions utilitaires pour le projet PDF to TEIF.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional


def validate_pdf_file(file_path: str) -> bool:
    """
    Valide qu'un fichier PDF existe et est accessible.
    
    Args:
        file_path: Chemin vers le fichier PDF
        
    Returns:
        True si le fichier est valide, False sinon
    """
    if not file_path.endswith('.pdf'):
        return False
    
    if not os.path.exists(file_path):
        return False
    
    if not os.path.isfile(file_path):
        return False
    
    # Vérifier que le fichier n'est pas vide
    if os.path.getsize(file_path) == 0:
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour qu'il soit valide sur le système de fichiers.
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    # Supprimer les caractères non autorisés
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limiter la longueur
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    # Éviter les noms réservés Windows
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    if sanitized.upper() in reserved_names:
        sanitized = f"_{sanitized}"
    
    return sanitized


def format_currency(amount: float, currency: str = "TND") -> str:
    """
    Formate un montant avec la devise.
    
    Args:
        amount: Montant à formater
        currency: Code devise (TND, EUR, USD, etc.)
        
    Returns:
        Montant formaté avec devise
    """
    return f"{amount:.2f} {currency}"


def normalize_currency_code(currency_input: str) -> str:
    """
    Normalise un code devise.
    
    Args:
        currency_input: Code devise en entrée
        
    Returns:
        Code devise normalisé
    """
    currency_map = {
        'DINAR': 'TND',
        'DINARS': 'TND',
        'EURO': 'EUR',
        'EUROS': 'EUR',
        '€': 'EUR',
        '$': 'USD',
        'DOLLAR': 'USD',
        'DOLLARS': 'USD'
    }
    
    currency_upper = currency_input.upper().strip()
    return currency_map.get(currency_upper, currency_upper)


def parse_amount_string(amount_str: str) -> Optional[float]:
    """
    Parse une chaîne de montant en float.
    
    Args:
        amount_str: Chaîne contenant un montant
        
    Returns:
        Montant en float ou None si parsing impossible
    """
    if not amount_str:
        return None
    
    # Nettoyer la chaîne
    cleaned = re.sub(r'[^\d,.-]', '', amount_str)
    
    # Remplacer virgule par point
    cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def create_output_directory(base_dir: str, subdir: str = None) -> str:
    """
    Crée un dossier de sortie s'il n'existe pas.
    
    Args:
        base_dir: Dossier de base
        subdir: Sous-dossier optionnel
        
    Returns:
        Chemin complet du dossier créé
    """
    if subdir:
        full_path = os.path.join(base_dir, subdir)
    else:
        full_path = base_dir
    
    os.makedirs(full_path, exist_ok=True)
    return full_path


def get_file_info(file_path: str) -> Dict:
    """
    Récupère les informations sur un fichier.
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        Dictionnaire avec les infos du fichier
    """
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    
    return {
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'extension': os.path.splitext(file_path)[1].lower()
    }


def log_extraction_summary(invoice_data: Dict) -> str:
    """
    Crée un résumé des données extraites pour logging.
    
    Args:
        invoice_data: Données de facture extraites
        
    Returns:
        Résumé formaté
    """
    summary_lines = [
        "=== RÉSUMÉ EXTRACTION ===",
        f"Numéro: {invoice_data.get('invoice_number', 'N/A')}",
        f"Date: {invoice_data.get('invoice_date', 'N/A')}",
        f"Montant total: {format_currency(invoice_data.get('total_amount', 0), invoice_data.get('currency', 'TND'))}",
        f"Fournisseur: {invoice_data.get('sender', {}).get('name', 'N/A')}",
        f"Client: {invoice_data.get('receiver', {}).get('name', 'N/A')}",
        f"Articles: {len(invoice_data.get('items', []))}",
        f"Taxes: {len(invoice_data.get('invoice_taxes', []))}",
        "========================"
    ]
    
    return "\n".join(summary_lines)


def validate_teif_data(invoice_data: Dict) -> List[str]:
    """
    Valide les données avant génération TEIF.
    
    Args:
        invoice_data: Données de facture
        
    Returns:
        Liste des erreurs de validation
    """
    errors = []
    
    # Champs obligatoires
    required_fields = [
        ('invoice_number', 'Numéro de facture'),
        ('invoice_date', 'Date de facture'),
        ('currency', 'Devise'),
        ('total_amount', 'Montant total')
    ]
    
    for field, description in required_fields:
        if not invoice_data.get(field):
            errors.append(f"{description} manquant")
    
    # Validation du fournisseur
    sender = invoice_data.get('sender', {})
    if not sender.get('name'):
        errors.append("Nom du fournisseur manquant")
    
    # Validation du client
    receiver = invoice_data.get('receiver', {})
    if not receiver.get('name'):
        errors.append("Nom du client manquant")
    
    # Validation des articles
    items = invoice_data.get('items', [])
    if not items:
        errors.append("Aucun article trouvé")
    
    # Validation des montants
    total_amount = invoice_data.get('total_amount', 0)
    if total_amount <= 0:
        errors.append("Montant total doit être positif")
    
    return errors


def generate_unique_filename(base_name: str, extension: str, directory: str) -> str:
    """
    Génère un nom de fichier unique dans un dossier.
    
    Args:
        base_name: Nom de base
        extension: Extension (avec ou sans point)
        directory: Dossier de destination
        
    Returns:
        Nom de fichier unique
    """
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    base_name = sanitize_filename(base_name)
    filename = f"{base_name}{extension}"
    full_path = os.path.join(directory, filename)
    
    counter = 1
    while os.path.exists(full_path):
        filename = f"{base_name}_{counter}{extension}"
        full_path = os.path.join(directory, filename)
        counter += 1
    
    return filename
