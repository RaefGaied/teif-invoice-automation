"""
Module de validation pour le format TEIF.

Ce module contient des fonctions utilitaires pour valider les données
selon les spécifications TEIF 1.8.8.
"""
from typing import Any, List, Dict, Optional
from datetime import datetime


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Vérifie que tous les champs obligatoires sont présents dans le dictionnaire.
    
    Args:
        data: Dictionnaire contenant les données à valider
        required_fields: Liste des clés obligatoires
        
    Raises:
        ValueError: Si un champ obligatoire est manquant
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValueError(f"Champs obligatoires manquants : {', '.join(missing_fields)}")


def validate_date_format(date_str: str, date_format: str) -> None:
    """
    Vérifie qu'une chaîne de caractères correspond au format de date spécifié.
    
    Args:
        date_str: Chaîne de caractères représentant une date
        date_format: Format de date attendu (ex: '%Y%m%d' pour YYYYMMDD)
        
    Raises:
        ValueError: Si la date n'est pas au format attendu
    """
    try:
        datetime.strptime(date_str, date_format)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de date invalide. Attendu: {date_format}. Reçu: {date_str}") from e


def validate_code_list(field_name: str, code: str, allowed_codes: List[str]) -> None:
    """
    Vérifie qu'un code fait partie de la liste des codes autorisés.
    
    Args:
        field_name: Nom du champ pour le message d'erreur
        code: Code à valider
        allowed_codes: Liste des codes autorisés
        
    Raises:
        ValueError: Si le code n'est pas dans la liste des codes autorisés
    """
    if code not in allowed_codes:
        raise ValueError(
            f"Valeur invalide pour {field_name}. Valeurs autorisées : {', '.join(allowed_codes)}. Reçu : {code}"
        )


def validate_currency_code(currency_code: str) -> None:
    """
    Vérifie qu'un code devise est valide selon la norme ISO 4217.
    
    Args:
        currency_code: Code devise à valider (ex: 'TND', 'EUR', 'USD')
        
    Raises:
        ValueError: Si le code devise n'est pas valide
    """
    # Liste non exhaustive des codes de devise courants
    valid_currencies = {
        'TND', 'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR',
        'BRL', 'MXN', 'RUB', 'ZAR', 'SEK', 'NOK', 'DKK', 'PLN', 'TRY', 'THB'
    }
    
    if not isinstance(currency_code, str) or len(currency_code) != 3 or currency_code.upper() not in valid_currencies:
        raise ValueError(f"Code devise invalide : {currency_code}")


def validate_amount(amount: Any) -> None:
    """
    Vérifie qu'un montant est valide (nombre positif).
    
    Args:
        amount: Montant à valider
        
    Raises:
        ValueError: Si le montant n'est pas un nombre positif
    """
    if not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError(f"Le montant doit être un nombre positif. Reçu : {amount}")


def validate_quantity(quantity: Any) -> None:
    """
    Vérifie qu'une quantité est valide (nombre strictement positif).
    
    Args:
        quantity: Quantité à valider
        
    Raises:
        ValueError: Si la quantité n'est pas un nombre strictement positif
    """
    if not isinstance(quantity, (int, float)) or quantity <= 0:
        raise ValueError(f"La quantité doit être un nombre strictement positif. Reçu : {quantity}")


def validate_country_code(country_code: str) -> None:
    """
    Vérifie qu'un code pays est valide selon la norme ISO 3166-1 alpha-2.
    
    Args:
        country_code: Code pays à valider (ex: 'TN', 'FR', 'US')
        
    Raises:
        ValueError: Si le code pays n'est pas valide
    """
    # Liste des codes pays ISO 3166-1 alpha-2
    valid_countries = {
        'AF', 'AX', 'AL', 'DZ', 'AS', 'AD', 'AO', 'AI', 'AQ', 'AG', 'AR', 'AM', 'AW', 'AU', 'AT', 'AZ',
        'BS', 'BH', 'BD', 'BB', 'BY', 'BE', 'BZ', 'BJ', 'BM', 'BT', 'BO', 'BQ', 'BA', 'BW', 'BV', 'BR',
        'IO', 'BN', 'BG', 'BF', 'BI', 'CV', 'KH', 'CM', 'CA', 'KY', 'CF', 'TD', 'CL', 'CN', 'CX', 'CC',
        'CO', 'KM', 'CG', 'CD', 'CK', 'CR', 'CI', 'HR', 'CU', 'CW', 'CY', 'CZ', 'DK', 'DJ', 'DM', 'DO',
        'EC', 'EG', 'SV', 'GQ', 'ER', 'EE', 'SZ', 'ET', 'FK', 'FO', 'FJ', 'FI', 'FR', 'GF', 'PF', 'TF',
        'GA', 'GM', 'GE', 'DE', 'GH', 'GI', 'GR', 'GL', 'GD', 'GP', 'GU', 'GT', 'GG', 'GN', 'GW', 'GY',
        'HT', 'HM', 'VA', 'HN', 'HK', 'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IM', 'IL', 'IT', 'JM',
        'JP', 'JE', 'JO', 'KZ', 'KE', 'KI', 'KP', 'KR', 'KW', 'KG', 'LA', 'LV', 'LB', 'LS', 'LR', 'LY',
        'LI', 'LT', 'LU', 'MO', 'MG', 'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MQ', 'MR', 'MU', 'YT', 'MX',
        'FM', 'MD', 'MC', 'MN', 'ME', 'MS', 'MA', 'MZ', 'MM', 'NA', 'NR', 'NP', 'NL', 'NC', 'NZ', 'NI',
        'NE', 'NG', 'NU', 'NF', 'MK', 'MP', 'NO', 'OM', 'PK', 'PW', 'PS', 'PA', 'PG', 'PY', 'PE', 'PH',
        'PN', 'PL', 'PT', 'PR', 'QA', 'RE', 'RO', 'RU', 'RW', 'BL', 'SH', 'KN', 'LC', 'MF', 'PM', 'VC',
        'WS', 'SM', 'ST', 'SA', 'SN', 'RS', 'SC', 'SL', 'SG', 'SX', 'SK', 'SI', 'SB', 'SO', 'ZA', 'GS',
        'SS', 'ES', 'LK', 'SD', 'SR', 'SJ', 'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ', 'TH', 'TL', 'TG', 'TK',
        'TO', 'TT', 'TN', 'TR', 'TM', 'TC', 'TV', 'UG', 'UA', 'AE', 'GB', 'US', 'UM', 'UY', 'UZ', 'VU',
        'VE', 'VN', 'VG', 'VI', 'WF', 'EH', 'YE', 'ZM', 'ZW'
    }
    
    if not isinstance(country_code, str) or len(country_code) != 2 or country_code.upper() not in valid_countries:
        raise ValueError(f"Code pays invalide : {country_code}. Doit être un code ISO 3166-1 alpha-2 valide.")


def validate_email(email: str) -> None:
    """
    Vérifie qu'une adresse email est valide.
    
    Args:
        email: Adresse email à valider
        
    Raises:
        ValueError: Si l'adresse email n'est pas valide
    """
    import re
    
    if not isinstance(email, str):
        raise ValueError("L'adresse email doit être une chaîne de caractères.")
    
    # Expression régulière pour valider une adresse email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValueError(f"Format d'email invalide : {email}")


def validate_phone_number(phone: str) -> None:
    """
    Vérifie qu'un numéro de téléphone est valide.
    
    Args:
        phone: Numéro de téléphone à valider
        
    Raises:
        ValueError: Si le numéro de téléphone n'est pas valide
    """
    import re
    
    if not isinstance(phone, str):
        raise ValueError("Le numéro de téléphone doit être une chaîne de caractères.")
    
    # Expression régulière pour valider un numéro de téléphone international
    # Accepte les formats :
    # - +216 12 345 678
    # - 0021612345678
    # - 12345678 (format local)
    # - (216) 12 345 678
    pattern = r'^(\+\d{1,4}[\s-]?)?(\(\d{1,4}\)[\s-]?)?[\d\s-]{8,}$'
    
    # Nettoyage des espaces et des caractères spéciaux pour la validation
    cleaned_phone = re.sub(r'[\s-()]', '', phone)
    
    # Vérification de la longueur minimale (au moins 8 chiffres)
    if len(re.sub(r'\D', '', cleaned_phone)) < 8:
        raise ValueError("Le numéro de téléphone doit contenir au moins 8 chiffres.")
    
    # Vérification du format général
    if not re.match(pattern, phone):
        raise ValueError(f"Format de numéro de téléphone invalide : {phone}")


def validate_date(date_str: str, date_format: str = '%Y-%m-%d') -> None:
    """
    Vérifie qu'une chaîne de date est valide selon le format spécifié.
    
    Args:
        date_str: Chaîne de caractères représentant une date
        date_format: Format de date attendu (par défaut: 'YYYY-MM-DD')
        
    Raises:
        ValueError: Si la date n'est pas valide ou ne correspond pas au format
    """
    try:
        from datetime import datetime
        datetime.strptime(date_str, date_format)
    except ValueError as e:
        raise ValueError(f"Format de date invalide. Attendu: {date_format}. Reçu: {date_str}") from e
    except TypeError as e:
        raise ValueError("La date doit être une chaîne de caractères.") from e
