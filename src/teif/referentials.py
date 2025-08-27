"""
Référentiels des codes standardisés pour le format TEIF 1.8.8.
Contient les codes et leurs descriptions pour les différents éléments de la facture électronique.
"""

# Référentiel I-0: Type d'identifiant partenaire
PARTNER_ID_TYPES = {
    "I-01": "Matricule Fiscal Tunisien",
    "I-02": "Carte d'identité nationale",
    "I-03": "Carte de séjour",
    "I-04": "Matricule Fiscal non tunisien"
}

# Référentiel I-1: Types de documents
DOCUMENT_TYPES = {
    "I-11": "Facture",
    "I-12": "Facture d'avoir",
    "I-13": "Note d'honoraire",
    "I-14": "Décompte (marché public)",
    "I-15": "Facture Export",
    "I-16": "Bon de commande"
}

# Référentiel I-2: Codes de langue
LANGUAGE_CODES = {
    "ar": "Arabe",
    "fr": "Français",
    "en": "Anglais"
}

# Langue par défaut pour les textes
DEFAULT_LANGUAGE = "fr"

# Référentiel I-3: Fonctions de date
DATE_FUNCTIONS = {
    "I-31": "Date d'émission du document",
    "I-32": "Date limite de paiement",
    "I-33": "Date de confirmation",
    "I-34": "Date d'expiration",
    "I-35": "Date de livraison",
    "I-36": "Période de facturation",
    "I-37": "Date de la génération de la référence",
    "I-38": "Autre"
}

# Référentiel I-4: Sujet de texte libre
FREE_TEXT_SUBJECTS = {
    "I-41": "Description marchandise / service",
    "I-42": "Description acquittement",
    "I-43": "Conditions du prix",
    "I-44": "Description de l'erreur",
    "I-45": "Période de temps",
    "I-46": "Formule de calcul du prix",
    "I-47": "Code incoterme livraison",
    "I-48": "Observation"
}

# Référentiel I-5: Fonction de localisation
LOCATION_FUNCTIONS = {
    "I-51": "Adresse de livraison",
    "I-52": "Adresse de paiement",
    "I-53": "Pays de provenance",
    "I-54": "Pays d'achat",
    "I-55": "Pays",
    "I-56": "Ville",
    "I-57": "Adresse de courrier",
    "I-58": "Pays première destination",
    "I-59": "Pays destination définitive"
}

# Référentiel I-6: Fonctions des partenaires
PARTNER_FUNCTIONS = {
    "I-61": "Acheteur",
    "I-62": "Fournisseur",
    "I-63": "Vendeur",
    "I-64": "Client",
    "I-65": "Receveur de la facture",
    "I-66": "Emetteur de la facture",
    "I-67": "Exportateur",
    "I-68": "Importateur",
    "I-69": "Inspecteur"
}

# Référentiel I-7: Format du nom de la partie
PARTY_NAME_FORMATS = {
    "I-71": "Nom et prénom",
    "I-72": "Raison sociale"
}

# Référentiel I-8: Qualificateurs de référence
REFERENCE_QUALIFIERS = {
    "I-81": "Identifiant du compte client",
    "I-811": "Mode de connexion client",
    "I-812": "Rang du compte client",
    "I-813": "Profil du compte client",
    "I-814": "Code du client",
    "I-815": "Registre de commerce",
    "I-816": "Catégorie de l'entreprise",
    "I-817": "Objet de la facture",
    "I-818": "Numéro CNSS",
    "I-82": "Numéro CNSS",  # Dupliqué dans la référence
    "I-83": "Référence Banque",
    "I-84": "Numéro bon de commande",
    "I-85": "Numéro bon de livraison",
    "I-86": "Numéro de décompte",
    "I-87": "Numéro de marché public",
    "I-871": "Nom marché public",
    "I-88": "Référence TTN de la facture",
    "I-89": "Numéro de la facture référenciée",
    "I-80": "Autre"
}

# Référentiel I-9: Fonction de contact
CONTACT_FUNCTIONS = {
    "I-91": "Contact Technique",
    "I-92": "Contact juridique",
    "I-93": "Contact Commercial",
    "I-94": "Autre"
}

# Référentiel I-10: Moyens de communication
COMMUNICATION_MEANS = {
    "I-101": "Téléphone",
    "I-102": "Fax",
    "I-103": "Email",
    "I-104": "Autre"
}

# Référentiel I-11: Conditions de paiement
PAYMENT_TERMS = {
    "I-111": "Basic",
    "I-112": "A une date fixe",
    "I-113": "Avec une période de grâce",
    "I-114": "Par virement bancaire",
    "I-115": "Exclusivement aux bureaux postaux",
    "I-116": "Autre",
    "I-117": "Par facilité"
}

# Référentiel I-12: Conditions de paiement (alternative)
PAYMENT_CONDITIONS = {
    "I-121": "Paiement directe",
    "I-122": "A travers une institution financière spécifique",
    "I-123": "Quelle que soit la banque",
    "I-124": "Autre"
}

# Référentiel I-13: Moyens de paiement
PAYMENT_MEANS = {
    "I-131": "Espèce",
    "I-132": "Chèque",
    "I-133": "Chèque certifié",
    "I-134": "Prélèvement bancaire",
    "I-135": "Virement bancaire",
    "I-136": "Swift",
    "I-137": "Autre"
}

# Référentiel I-14: Institution financière
FINANCIAL_INSTITUTIONS = {
    "I-141": "Poste",
    "I-142": "Banque",
    "I-143": "Autre"
}

# Référentiel I-15: Type de remise
ALLOWANCE_TYPES = {
    "I-151": "Réduction",
    "I-152": "Ristourne",
    "I-153": "Rabais",
    "I-154": "Redevance sur les télécommunications",
    "I-155": "Autre"
}

# Référentiel I-15: Rôles de signature
SIGNATURE_ROLES = {
    "I-151": "Fournisseur",
    "I-152": "Client",
    "I-153": "Tiers de confiance",
    "I-154": "Administration fiscale",
    "I-155": "Prestataire de services de certification"
}

# Référentiel I-16: Types de taxes
TAX_TYPES = {
    "I-161": "Droit de consommation",
    "I-162": "Taxe professionnelle de compétitivité FODEC",
    "I-163": "Taxe sur les emballages métalliques",
    "I-164": "Taxe pour la protection de l'environnement TPE",
    "I-165": "Taxe au profit du fonds de développement de la compétitivité dans le secteur du tourisme (FODET)",
    "I-166": "Taxe sur les climatiseurs",
    "I-167": "Taxes sur les lampes et les tubes",
    "I-168": "Taxes sur fruit et légumes non soumis à la TVA",
    "I-169": "Taxes sur les produits de la pêche non soumis à la TVA",
    "I-160": "Taxes RB non soumis à la TVA",
    "I-1601": "Droit de timbre",
    "I-1602": "TVA",
    "I-1603": "Autre",
    "I-1604": "Retenu à la source"
}

# Référentiel I-17: Type de montant
AMOUNT_TYPES = {
    "I-171": "Montant total HT de l'article",
    "I-172": "Montant total HT des articles",
    "I-173": "Montant payé",
    "I-174": "Montant HT de la charge/Service",
    "I-175": "Montant total HT des charges/Services",
    "I-176": "Montant total HT facture",
    "I-177": "Montant base taxe",
    "I-178": "Montant Taxe",
    "I-179": "Capital de l'entreprise",
    "I-180": "Montant Total TTC facture",
    "I-181": "Montant total Taxe",
    "I-182": "Montant total base taxe",
    "I-183": "Montant HT article unitaire",
    "I-184": "Montant total TTC des charges/Services",
    "I-185": "Montant total exonéré",
    "I-186": "Montant de crédit",
    "I-187": "Montant objet de suspension de la TVA",
    "I-188": "Montant net de l'article",
    "I-189": "Montant total HT toutes charges(services) comprises"
}

# Fonctions utilitaires
def is_valid_code(referentiel: dict, code: str) -> bool:
    """Vérifie si un code existe dans le référentiel donné."""
    return code in referentiel

def get_description(referentiel: dict, code: str, default: str = "Inconnu") -> str:
    """Récupère la description d'un code depuis le référentiel."""
    return referentiel.get(code, default)

def validate_document_type(doc_type: str) -> bool:
    """Valide qu'un type de document est valide."""
    return is_valid_code(DOCUMENT_TYPES, doc_type)

def get_document_type_description(doc_type: str) -> str:
    """Récupère la description d'un type de document."""
    return get_description(DOCUMENT_TYPES, doc_type)

def validate_date_function(date_function: str) -> bool:
    """Valide qu'une fonction de date est valide."""
    return is_valid_code(DATE_FUNCTIONS, date_function)

def get_date_function_description(date_function: str) -> str:
    """Récupère la description d'une fonction de date."""
    return get_description(DATE_FUNCTIONS, date_function)

def validate_payment_terms(terms_code: str) -> bool:
    """Valide qu'un code de condition de paiement est valide."""
    return is_valid_code(PAYMENT_TERMS, terms_code) or is_valid_code(PAYMENT_CONDITIONS, terms_code)

def get_payment_terms_description(terms_code: str) -> str:
    """Récupère la description d'une condition de paiement."""
    if is_valid_code(PAYMENT_TERMS, terms_code):
        return get_description(PAYMENT_TERMS, terms_code)
    return get_description(PAYMENT_CONDITIONS, terms_code)

def validate_payment_means(means_code: str) -> bool:
    """Valide qu'un code de moyen de paiement est valide."""
    return is_valid_code(PAYMENT_MEANS, means_code)

def get_payment_means_description(means_code: str) -> str:
    """Récupère la description d'un moyen de paiement."""
    return get_description(PAYMENT_MEANS, means_code)

def validate_tax_type(tax_code: str) -> bool:
    """Valide qu'un code de type de taxe est valide."""
    return is_valid_code(TAX_TYPES, tax_code)

def get_tax_type_description(tax_code: str) -> str:
    """Récupère la description d'un type de taxe."""
    return get_description(TAX_TYPES, tax_code)

def validate_amount_type(amount_code: str) -> bool:
    """Valide qu'un code de type de montant est valide."""
    return is_valid_code(AMOUNT_TYPES, amount_code)

def get_amount_type_description(amount_code: str) -> str:
    """Récupère la description d'un type de montant."""
    return get_description(AMOUNT_TYPES, amount_code)

def validate_language_code(lang_code: str) -> bool:
    """Valide qu'un code de langue est valide.
    
    Args:
        lang_code (str): Le code de langue à valider (ex: 'fr', 'ar', 'en')
        
    Returns:
        bool: True si le code est valide, False sinon
    """
    return lang_code in LANGUAGE_CODES


def validate_signature_role(role_code: str) -> bool:
    """Valide qu'un code de rôle de signature est valide.
    
    Args:
        role_code (str): Le code de rôle à valider (ex: 'I-151' pour Fournisseur)
        
    Returns:
        bool: True si le code est valide, False sinon
    """
    return is_valid_code(SIGNATURE_ROLES, role_code)


def get_signature_role_description(role_code: str) -> str:
    """Récupère la description d'un rôle de signature.
    
    Args:
        role_code (str): Le code de rôle
        
    Returns:
        str: La description du rôle ou "Inconnu" si non trouvé
    """
    return get_description(SIGNATURE_ROLES, role_code)


def validate_reference_type(ref_type: str) -> bool:
    """Valide qu'un type de référence est valide.
    
    Args:
        ref_type (str): Le code de type de référence à valider
        
    Returns:
        bool: True si le type est valide, False sinon
    """
    return ref_type in ["TTN", "BL", "BC", "FAC", "AVOIR", "AUTRE"]

def get_reference_type_description(ref_type: str) -> str:
    """Récupère la description d'un type de référence.
    
    Args:
        ref_type (str): Le code de type de référence
        
    Returns:
        str: La description du type de référence ou "Inconnu" si non trouvé
    """
    ref_descriptions = {
        "TTN": "Numéro de référence TTN (Tunisie TradeNet)",
        "BL": "Bon de livraison",
        "BC": "Bon de commande",
        "FAC": "Facture",
        "AVOIR": "Avoir",
        "AUTRE": "Autre type de référence"
    }
    return ref_descriptions.get(ref_type, "Inconnu")