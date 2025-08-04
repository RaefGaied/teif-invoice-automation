# Ajout des constantes de validation
AMOUNT_MIN = 0.001  # Montant minimum (1 millime)
AMOUNT_MAX = 1000000000  # Montant maximum (1 milliard)
TVA_RATES = [0, 7, 13, 19]  # Taux de TVA valides en Tunisie

def validate_amount(amount: float) -> bool:
    """Valide qu'un montant est dans une plage raisonnable."""
    return AMOUNT_MIN <= amount <= AMOUNT_MAX

def validate_tva_rate(rate: float) -> float:
    """Valide et retourne le taux de TVA le plus proche."""
    if rate <= 0:
        return 0
    return min(TVA_RATES, key=lambda x: abs(x - rate))

def calculate_tva_rate(ht: float, tva: float) -> float:
    """Calcule et valide le taux de TVA à partir du HT et du montant TVA."""
    if ht <= 0:
        return 19.0  # Taux par défaut
    rate = (tva / ht) * 100
    return validate_tva_rate(rate)

def validate_and_fix_amounts(amounts: dict) -> dict:
    """Valide et corrige les montants extraits."""
    if not validate_amount(amounts['total_amount']):
        # Si le total est invalide mais qu'on a HT et TVA
        if validate_amount(amounts['amount_ht']) and validate_amount(amounts['tva_amount']):
            amounts['total_amount'] = amounts['amount_ht'] + amounts['tva_amount']
    
    if not validate_amount(amounts['amount_ht']):
        # Si le HT est invalide mais qu'on a le total et la TVA
        if validate_amount(amounts['total_amount']) and validate_amount(amounts['tva_amount']):
            amounts['amount_ht'] = amounts['total_amount'] - amounts['tva_amount']
    
    if not validate_amount(amounts['tva_amount']):
        # Si la TVA est invalide mais qu'on a le total et le HT
        if validate_amount(amounts['total_amount']) and validate_amount(amounts['amount_ht']):
            amounts['tva_amount'] = amounts['total_amount'] - amounts['amount_ht']
    
    # Calculer le taux de TVA réel
    if validate_amount(amounts['amount_ht']) and validate_amount(amounts['tva_amount']):
        amounts['tva_rate'] = calculate_tva_rate(amounts['amount_ht'], amounts['tva_amount'])
    
    # Validation finale de cohérence
    if (validate_amount(amounts['total_amount']) and 
        validate_amount(amounts['amount_ht']) and 
        validate_amount(amounts['tva_amount'])):
        
        expected_total = amounts['amount_ht'] + amounts['tva_amount']
        if abs(amounts['total_amount'] - expected_total) > 0.01:
            # Corriger le total si l'écart est significatif
            amounts['total_amount'] = expected_total
    
    # Arrondir tous les montants à 3 décimales
    for key in amounts:
        if isinstance(amounts[key], float):
            amounts[key] = round(amounts[key], 3)
    
    return amounts
