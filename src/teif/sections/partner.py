"""
Module pour la gestion des sections partenaires (vendeur, acheteur, livraison) dans les documents TEIF.

Ce module implémente les sections liées aux parties impliquées dans la transaction selon le standard TEIF 1.8.8.
"""
from typing import Dict, Any, List, Optional, Union
#import xml.etree.ElementTree as ET
from lxml import etree as ET

__all__ = [
    'create_partner_section',
    'add_seller_party',
    'add_buyer_party',
    'add_delivery_party',
    'PartnerSection'
]

def create_partner_section(parent: ET.Element, partner_data: Dict[str, Any], function_code: str) -> ET.Element:
    """
    Crée une section partenaire selon le standard TEIF 1.8.8.
    
    Args:
        parent: L'élément parent XML
        partner_data: Dictionnaire contenant les données du partenaire
        function_code: Code de fonction du partenaire (ex: 'I-62' pour vendeur, 'I-64' pour acheteur)
        
    Returns:
        ET.Element: L'élément PartnerSection créé
    """
    # Créer l'élément PartnerSection s'il n'existe pas déjà
    partner_section = parent.find("PartnerSection")
    if partner_section is None:
        partner_section = ET.SubElement(parent, "PartnerSection")
    
    # Créer l'élément PartnerDetails avec le functionCode
    partner_details = ET.SubElement(partner_section, "PartnerDetails", functionCode=function_code)
    
    # Ajouter la section NAD (Name and Address) - Obligatoire
    _add_nad_section(partner_details, partner_data)
    
    # Ajouter les sections LOC (Localisation) si disponibles
    if 'locations' in partner_data and isinstance(partner_data['locations'], list):
        for location in partner_data['locations']:
            _add_location_section(partner_details, location)
    
    # Ajouter les références si disponibles
    if 'references' in partner_data and isinstance(partner_data['references'], list):
        for ref in partner_data['references']:
            _add_reference_section(partner_details, ref)
    
    # Ajouter les contacts si disponibles
    if 'contacts' in partner_data and isinstance(partner_data['contacts'], list):
        for contact in partner_data['contacts']:
            _add_contact_section(partner_details, contact)
    
    return partner_section

def _add_nad_section(parent: ET.Element, partner_data: Dict[str, Any]) -> None:
    """
    Ajoute la section NAD (Name and Address) au partenaire.
    """
    nad = ET.SubElement(parent, "Nad")
    
    # Identifiant du partenaire (obligatoire)
    if 'identification' in partner_data:
        ident = partner_data['identification']
        partner_id = ET.SubElement(nad, "PartnerIdentifier", type=ident.get('type', 'I-01'))
        partner_id.text = str(ident.get('value', ''))
    
    # Nom du partenaire (optionnel mais recommandé)
    if 'name' in partner_data:
        name_attrs = {}
        if 'name_type' in partner_data:
            name_attrs['nameType'] = partner_data['name_type']
        name = ET.SubElement(nad, "PartnerName", **name_attrs)
        name.text = str(partner_data['name'])
    
    # Adresse (obligatoire pour certains types de partenaires)
    if 'address' in partner_data:
        _add_address(nad, partner_data['address'])

def _add_address(parent: ET.Element, address_data: Dict[str, Any]) -> None:
    """
    Add address information according to TEIF 1.8.8 specification.
    
    Args:
        parent: The parent XML element
        address_data: Dictionary containing address information with keys:
            - description: Optional address description
            - street: Street address (max 35 chars)
            - city: City name (max 35 chars)
            - postal_code: Postal code (max 17 chars)
            - country_code: ISO 3166-1 alpha-2 country code (e.g., 'TN')
            - lang: Language code ('ar', 'fr', 'en')
    """
    if not address_data:
        return
        
    address = ET.SubElement(parent, "PartnerAdresses")
    
    # Add language attribute if specified
    if 'lang' in address_data:
        lang = address_data['lang'].lower()
        if lang in ('ar', 'fr', 'en'):
            address.set('lang', lang.upper())
    
    # Add address description if provided
    if 'description' in address_data:
        desc = ET.SubElement(address, "AdressDescription")
        desc.text = str(address_data['description'])[:500]  # Max 500 chars
    
    # Add street if provided
    if 'street' in address_data:
        street = ET.SubElement(address, "Street")
        street.text = str(address_data['street'])[:35]  # Max 35 chars
    
    # Add city if provided
    if 'city' in address_data:
        city = ET.SubElement(address, "CityName")
        city.text = str(address_data['city'])[:35]  # Max 35 chars
    
    # Add postal code if provided
    if 'postal_code' in address_data:
        postal = ET.SubElement(address, "PostalCode")
        postal.text = str(address_data['postal_code'])[:17]  # Max 17 chars
    
    # Add country if provided
    if 'country_code' in address_data:
        country = ET.SubElement(address, "Country")
        country.set('codeList', 'ISO_3166-1')
        country.text = str(address_data['country_code']).upper()

def _add_location_section(parent: ET.Element, location_data: Dict[str, Any]) -> None:
    """
    Ajoute une section de localisation (LOC) au partenaire.
    """
    location = ET.SubElement(parent, "Location")
    
    # Nom de la localisation (optionnel)
    if 'name' in location_data:
        loc_name = ET.SubElement(location, "LocationName")
        loc_name.text = str(location_data['name'])
    
    # Adresse de la localisation (optionnelle)
    if 'address' in location_data:
        _add_address(location, location_data['address'])

def _add_reference_section(parent: ET.Element, ref_data: Dict[str, str]) -> None:
    """
    Ajoute une section de référence (RFF) au partenaire.
    """
    rff = ET.SubElement(parent, "RffSection")
    ref = ET.SubElement(rff, "Reference", refID=ref_data.get('type', ''))
    ref.text = str(ref_data.get('value', ''))
    
    # Date de référence (optionnelle)
    if 'date' in ref_data:
        ref_date = ET.SubElement(rff, "ReferenceDate")
        ref_date.text = str(ref_data['date'])

def _add_contact_section(parent: ET.Element, contact_data: Dict[str, Any]) -> None:
    """
    Add contact information according to TEIF 1.8.8 specification.
    
    Args:
        parent: The parent XML element
        contact_data: Dictionary containing contact information with keys:
            - function_code: Contact function code (6 chars, from I9 referential)
            - name: Contact name (max 200 chars)
            - identifier: Optional contact identifier (max 6 chars)
            - communications: List of communication methods
    """
    if not contact_data:
        return
        
    cta_section = ET.SubElement(parent, "CtaSection")
    
    # Create contact element with function code
    contact = ET.SubElement(cta_section, "Contact")
    if 'function_code' in contact_data:
        contact.set('functionCode', str(contact_data['function_code'])[:6])
    
    # Add contact identifier if provided
    if 'identifier' in contact_data:
        ident = ET.SubElement(contact, "ContactIdentifier")
        ident.text = str(contact_data['identifier'])[:6]  # Max 6 chars
    
    # Add contact name if provided
    if 'name' in contact_data:
        name = ET.SubElement(contact, "ContactName")
        name.text = str(contact_data['name'])[:200]  # Max 200 chars
    
    # Add communication methods if provided
    if 'communications' in contact_data and isinstance(contact_data['communications'], list):
        for comm in contact_data['communications']:
            _add_communication(contact, comm)

def _add_communication(parent: ET.Element, comm_data: Dict[str, str]) -> None:
    """
    Add communication method to a contact.
    
    Args:
        parent: The parent XML element
        comm_data: Dictionary containing communication details with keys:
            - type: Communication type code (from I10 referential)
            - value: Communication value (phone, email, etc.)
    """
    if not comm_data or 'type' not in comm_data or 'value' not in comm_data:
        return
        
    comm = ET.SubElement(parent, "Communication")
    
    # Add communication type
    comm_type = ET.SubElement(comm, "ComMeansType")
    comm_type.text = str(comm_data['type'])[:6]  # Max 6 chars
    
    # Add communication value
    comm_addr = ET.SubElement(comm, "ComAdress")
    comm_addr.text = str(comm_data['value'])[:200]  # Max 200 chars

def add_seller_party(parent: ET.Element, seller_data: Dict[str, Any]) -> ET.Element:
    """
    Add seller party information according to TEIF 1.8.8 specification.
    
    Args:
        parent: The parent XML element
        seller_data: Dictionary containing seller information with keys:
            - identifier: Seller's tax identification (required)
            - identifier_type: Type of identification (default: 'I-01' for Matricule Fiscal)
            - name: Legal name of the seller (required)
            - legal_form: Legal form of the seller (optional)
            - vat_number: VAT identification number (required for VAT invoices)
            - address: Dictionary with seller's address information
            - contacts: List of contact information dictionaries
            - references: List of reference dictionaries
            - locations: List of location dictionaries
    """
    # Validate required fields
    required_fields = ['identifier', 'name', 'vat_number', 'address']
    for field in required_fields:
        if field not in seller_data or not seller_data[field]:
            raise ValueError(f"Le champ obligatoire '{field}' est manquant pour le vendeur")
    
    # Préparer les données pour create_partner_section
    partner_data = {
        'identification': {
            'type': seller_data.get('identifier_type', 'I-01'),
            'value': seller_data['identifier']
        },
        'name': seller_data['name'],
        'name_type': 'I-100',  # Nom commercial
        'address': seller_data['address']
    }
    
    # Ajouter les champs optionnels s'ils existent
    if 'legal_form' in seller_data:
        partner_data['legal_form'] = seller_data['legal_form']
    if 'contacts' in seller_data:
        partner_data['contacts'] = seller_data['contacts']
    if 'references' in seller_data:
        partner_data['references'] = seller_data['references']
    if 'locations' in seller_data:
        partner_data['locations'] = seller_data['locations']
    
    # Create partner section with function code I-62 for seller
    partner_section = create_partner_section(parent, partner_data, 'I-62')
    
    # Add VAT number (pas dans la section NAD)
    vat = ET.SubElement(partner_section, "VATIdentifier")
    vat.text = str(seller_data['vat_number'])
    
    return partner_section

def add_buyer_party(parent: ET.Element, buyer_data: Dict[str, Any]) -> ET.Element:
    """
    Add buyer party information according to TEIF 1.8.8 specification.
    
    Args:
        parent: The parent XML element
        buyer_data: Dictionary containing buyer information with keys:
            - identifier: Buyer's tax identification (required)
            - identifier_type: Type of identification (default: 'I-01' for Matricule Fiscal)
            - name: Legal name of the buyer (required)
            - legal_form: Legal form of the buyer (optional)
            - vat_number: VAT identification number (required for VAT invoices)
            - address: Dictionary with buyer's address information
            - contacts: List of contact information dictionaries
            - references: List of reference dictionaries
    """
    # Validate required fields
    required_fields = ['identifier', 'name', 'address']
    for field in required_fields:
        if field not in buyer_data or not buyer_data[field]:
            raise ValueError(f"Le champ obligatoire '{field}' est manquant pour l'acheteur")
    
    # Préparer les données pour create_partner_section
    partner_data = {
        'identification': {
            'type': buyer_data.get('identifier_type', 'I-01'),
            'value': buyer_data['identifier']
        },
        'name': buyer_data['name'],
        'name_type': 'I-100',  # Nom commercial
        'address': buyer_data['address']
    }
    
    # Ajouter les champs optionnels s'ils existent
    if 'legal_form' in buyer_data:
        partner_data['legal_form'] = buyer_data['legal_form']
    if 'contacts' in buyer_data:
        partner_data['contacts'] = buyer_data['contacts']
    if 'references' in buyer_data:
        partner_data['references'] = buyer_data['references']
    if 'vat_number' in buyer_data:
        partner_data['vat_number'] = buyer_data['vat_number']
    
    # Create partner section with function code I-64 for buyer
    partner_section = create_partner_section(parent, partner_data, 'I-64')
    
    # Add VAT number if provided (pas dans la section NAD)
    if 'vat_number' in buyer_data and buyer_data['vat_number']:
        vat = ET.SubElement(partner_section, "VATIdentifier")
        vat.text = str(buyer_data['vat_number'])
    
    return partner_section

def add_delivery_party(parent: ET.Element, delivery_data: Dict[str, Any]) -> ET.Element:
    """
    Add delivery party information according to TEIF 1.8.8 specification.
    
    Args:
        parent: The parent XML element
        delivery_data: Dictionary containing delivery information with keys:
            - name: Name of the delivery location (required)
            - identifier: Delivery location identifier (optional)
            - identifier_type: Type of identification (default: 'I-01')
            - address: Dictionary with delivery address information (required)
            - contacts: List of contact information dictionaries (optional)
            - references: List of reference dictionaries (optional)
            - locations: List of location dictionaries (optional)
    
    Returns:
        ET.Element: The created PartnerSection element
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    required_fields = ['name', 'address']
    for field in required_fields:
        if field not in delivery_data or not delivery_data[field]:
            raise ValueError(f"Le champ obligatoire '{field}' est manquant pour la livraison")
    
    # Create partner section with function code I-63 for delivery
    partner_section = create_partner_section(parent, delivery_data, 'I-63')
    
    # Add NAD (Name and Address) section
    nad = ET.SubElement(partner_section, "Nad")
    
    # Add delivery location name (required)
    name = ET.SubElement(nad, "PartnerName")
    name.text = str(delivery_data['name'])[:200]  # Max 200 chars
    
    # Add delivery location identifier if provided
    if 'identifier' in delivery_data and delivery_data['identifier']:
        ident = ET.SubElement(nad, "PartnerIdentifier")
        ident.set("type", delivery_data.get('identifier_type', 'I-01'))
        ident.text = str(delivery_data['identifier'])
    
    # Add address
    _add_address(nad, delivery_data['address'])
    
    # Add references if provided
    if 'references' in delivery_data and isinstance(delivery_data['references'], list):
        for ref in delivery_data['references']:
            if 'type' in ref and 'value' in ref:
                rff_section = ET.SubElement(partner_section, "RffSection")
                reference = ET.SubElement(rff_section, "Reference")
                reference.set("refID", ref['type'])
                reference.text = str(ref['value'])
    
    # Add contacts if provided
    if 'contacts' in delivery_data and isinstance(delivery_data['contacts'], list):
        for contact in delivery_data['contacts']:
            _add_contact_section(partner_section, contact)
    
    # Add locations if provided
    if 'locations' in delivery_data and isinstance(delivery_data['locations'], list):
        for location in delivery_data['locations']:
            _add_location_section(partner_section, location)
    
    return partner_section

def _add_financial_account(parent: ET.Element, account_data: Dict[str, str]) -> None:
    """
    Ajoute les informations de compte financier.
    
    Args:
        parent: L'élément parent XML
        account_data: Données du compte financier
    """
    account = ET.SubElement(parent, "FinancialAccount")
    
    if 'iban' in account_data:
        iban = ET.SubElement(account, "IBAN")
        iban.text = str(account_data['iban'])
    
    if 'bank_name' in account_data:
        bank_name = ET.SubElement(account, "BankName")
        bank_name.text = str(account_data['bank_name'])
    
    if 'bic' in account_data:
        bic = ET.SubElement(account, "BIC")
        bic.text = str(account_data['bic'])

def _add_registration_details(parent: ET.Element, registration_data: Dict[str, str]) -> None:
    """
    Ajoute les détails d'immatriculation.
    
    Args:
        parent: L'élément parent XML
        registration_data: Données d'immatriculation
    """
    registration = ET.SubElement(parent, "Registration")
    
    if 'number' in registration_data:
        reg_num = ET.SubElement(registration, "RegistrationNumber")
        reg_num.text = str(registration_data['number'])
    
    if 'type' in registration_data:
        reg_type = ET.SubElement(registration, "RegistrationType")
        reg_type.text = str(registration_data['type'])
    
    if 'issuer' in registration_data:
        issuer = ET.SubElement(registration, "Issuer")
        issuer.text = str(registration_data['issuer'])

def _add_references_section(parent: ET.Element, references: List[Dict[str, str]]) -> None:
    """
    Ajoute une section de références (RFF) au partenaire.
    """
    for ref in references:
        rff = ET.SubElement(parent, "RffSection")
        ref_elem = ET.SubElement(rff, "Reference", refID=ref.get('type', ''))
        ref_elem.text = ref.get('value', '')

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Vérifie que les champs obligatoires sont présents dans les données.
    
    Args:
        data: Données à vérifier
        required_fields: Liste des champs obligatoires
        
    Raises:
        ValueError: Si un champ obligatoire est manquant
    """
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Le champ '{field}' est obligatoire")

def validate_country_code(country_code: str) -> None:
    """
    Vérifie que le code pays est valide.
    
    Args:
        country_code: Code pays à vérifier
        
    Raises:
        ValueError: Si le code pays est invalide
    """
    # Liste des codes pays valides (ISO 3166-1 alpha-2)
    valid_country_codes = ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW']
    
    if country_code.upper() not in valid_country_codes:
        raise ValueError(f"Le code pays '{country_code}' est invalide")

class PartnerSection:
    def __init__(self, parent: ET.Element, partner_data: Dict[str, Any], function_code: str):
        self.parent = parent
        self.partner_data = partner_data
        self.function_code = function_code
        self.partner_section = create_partner_section(parent, partner_data, function_code)

def _add_references_section(parent: ET.Element, references: List[Dict[str, str]]) -> None:
    """
    Ajoute une section de références (RFF) au partenaire.
    """
    for ref in references:
        rff = ET.SubElement(parent, "RffSection")
        ref_elem = ET.SubElement(rff, "Reference", refID=ref.get('type', ''))
        ref_elem.text = ref.get('value', '')

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Vérifie que les champs obligatoires sont présents dans les données.
    
    Args:
        data: Données à vérifier
        required_fields: Liste des champs obligatoires
        
    Raises:
        ValueError: Si un champ obligatoire est manquant
    """
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Le champ '{field}' est obligatoire")

def validate_country_code(country_code: str) -> None:
    """
    Vérifie que le code pays est valide.
    
    Args:
        country_code: Code pays à vérifier
        
    Raises:
        ValueError: Si le code pays est invalide
    """
    # Liste des codes pays valides (ISO 3166-1 alpha-2)
    valid_country_codes = ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW']
    
    if country_code.upper() not in valid_country_codes:
        raise ValueError(f"Le code pays '{country_code}' est invalide")

class PartnerSection:
    def __init__(self, parent: ET.Element, partner_data: Dict[str, Any], function_code: str):
        self.parent = parent
        self.partner_data = partner_data
        self.function_code = function_code
        self.partner_section = create_partner_section(parent, partner_data, function_code)
