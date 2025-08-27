"""
Module pour la gestion des sections partenaires (vendeur, acheteur, livraison) dans les documents TEIF.

Ce module implémente les sections liées aux parties impliquées dans la transaction selon le standard TEIF 1.8.8.
"""
from typing import Dict, Any, List, Optional, Union
import xml.etree.ElementTree as ET

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
    Ajoute une adresse complète selon le standard TEIF 1.8.8.
    """
    address = ET.SubElement(parent, "Address")
    
    # Description de l'adresse (optionnel)
    if 'description' in address_data:
        desc = ET.SubElement(address, "AdressDescription")
        desc.text = str(address_data['description'])
    
    # Rue (optionnel)
    if 'street' in address_data:
        street = ET.SubElement(address, "Street")
        street.text = str(address_data['street'])
    
    # Ville (optionnel mais recommandé)
    if 'city' in address_data:
        city = ET.SubElement(address, "CityName")
        city.text = str(address_data['city'])
    
    # Code postal (optionnel mais recommandé)
    if 'postal_code' in address_data:
        postal_code = ET.SubElement(address, "PostalCode")
        postal_code.text = str(address_data['postal_code'])
    
    # Pays (optionnel mais recommandé)
    if 'country_code' in address_data:
        country = ET.SubElement(address, "Country", codeList="ISO_3166-1")
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
    Ajoute une section de contact (CTA) au partenaire.
    """
    cta = ET.SubElement(parent, "CtaSection")
    
    # Détails du contact
    contact = ET.SubElement(cta, "Contact", functionCode=contact_data.get('function_code', 'I-94'))
    
    # Identifiant du contact (optionnel)
    if 'id' in contact_data:
        contact_id = ET.SubElement(contact, "ContactIdentifier")
        contact_id.text = str(contact_data['id'])
    
    # Nom du contact (optionnel mais recommandé)
    if 'name' in contact_data:
        contact_name = ET.SubElement(contact, "ContactName")
        contact_name.text = str(contact_data['name'])
    
    # Moyens de communication (optionnels)
    if 'communications' in contact_data and isinstance(contact_data['communications'], list):
        for comm in contact_data['communications']:
            _add_communication(cta, comm)

def _add_communication(parent: ET.Element, comm_data: Dict[str, str]) -> None:
    """
    Ajoute un moyen de communication à une section de contact.
    """
    comm = ET.SubElement(parent, "Communication")
    
    # Type de moyen de communication (obligatoire)
    means_type = ET.SubElement(comm, "ComMeansType")
    means_type.text = str(comm_data.get('type', ''))
    
    # Valeur du moyen de communication (obligatoire)
    address = ET.SubElement(comm, "ComAdress")
    address.text = str(comm_data.get('value', ''))

def add_seller_party(parent: ET.Element, seller_data: Dict[str, Any]) -> ET.Element:
    """
    Ajoute les informations du vendeur (SU - Supplier) à la facture TEIF.
    
    Structure TEIF 1.8.8:
    - RANG 4: PartnerSection (obligatoire)
      - RANG 5: NAD (obligatoire)
        - RANG 6: LOC (optionnel, répétable)
        - RANG 7-12: RFF, DTM, CTA (optionnels)
    
    Args:
        parent: L'élément parent XML
        seller_data: Dictionnaire contenant les données du vendeur avec les clés:
            - id: Identifiant du vendeur (obligatoire)
            - type: Type d'identification (ex: 'I-01' pour Matricule Fiscal)
            - name: Nom du vendeur (obligatoire)
            - legal_form: Forme juridique (optionnel)
            - vat_number: Numéro de TVA (obligatoire pour facture de TVA)
            - tax_identifier: Identifiant fiscal (optionnel)
            - address: Dictionnaire d'adresse (obligatoire)
            - contacts: Liste de contacts (optionnel)
            - references: Dictionnaire de références (optionnel)
            - location: Dictionnaire de localisation (optionnel)
            - registration: Dictionnaire d'immatriculation (optionnel)
            
    Returns:
        ET.Element: L'élément PartnerSection du vendeur
        
    Raises:
        ValueError: Si les champs obligatoires sont manquants ou invalides
    """
    # Vérification des champs obligatoires
    validate_required_fields(seller_data, ['id', 'name', 'address'])
    
    # Création de la section partenaire (RANG 4)
    partner_section = create_partner_section(parent, seller_data, 'I-62')
    
    # Informations spécifiques au vendeur
    if 'vat_number' in seller_data:
        vat = ET.SubElement(partner_section.find("PartnerDetails"), "VATIdentifier")
        vat.text = str(seller_data['vat_number'])
    
    # Compte bancaire (optionnel)
    if 'financial_account' in seller_data:
        _add_financial_account(partner_section.find("PartnerDetails"), seller_data['financial_account'])
    
    # Immatriculation (optionnel)
    if 'registration' in seller_data:
        _add_registration_details(partner_section.find("PartnerDetails"), seller_data['registration'])
    
    return partner_section

def add_buyer_party(parent: ET.Element, buyer_data: Dict[str, Any]) -> ET.Element:
    """
    Ajoute les informations de l'acheteur (BY - Buyer) à la facture TEIF.
    
    Structure TEIF 1.8.8:
    - RANG 4: PartnerSection (obligatoire)
      - RANG 5: NAD (obligatoire)
        - RANG 6: LOC (optionnel, répétable)
        - RANG 7-12: RFF, DTM, CTA (optionnels)
    
    Args:
        parent: L'élément parent XML
        buyer_data: Dictionnaire contenant les données de l'acheteur avec les clés:
            - id: Identifiant de l'acheteur (obligatoire)
            - type: Type d'identification (ex: 'I-01' pour Matricule Fiscal)
            - name: Nom de l'acheteur (obligatoire)
            - legal_form: Forme juridique (optionnel)
            - vat_number: Numéro de TVA (obligatoire pour facture de TVA)
            - tax_identifier: Identifiant fiscal (optionnel)
            - address: Dictionnaire d'adresse (obligatoire pour facture)
            - contacts: Liste de contacts (optionnel)
            - references: Dictionnaire de références (optionnel)
            - location: Dictionnaire de localisation (optionnel)
            - registration: Dictionnaire d'immatriculation (optionnel)
            
    Returns:
        ET.Element: L'élément PartnerSection de l'acheteur
        
    Raises:
        ValueError: Si les champs obligatoires sont manquants ou invalides
    """
    # Vérification des champs obligatoires
    validate_required_fields(buyer_data, ['id', 'name'])
    
    # Création de la section partenaire (RANG 4)
    partner_section = create_partner_section(parent, buyer_data, 'I-64')
    
    # Informations spécifiques à l'acheteur
    if 'vat_number' in buyer_data:
        vat = ET.SubElement(partner_section.find("PartnerDetails"), "VATIdentifier")
        vat.text = str(buyer_data['vat_number'])
    
    # Immatriculation (optionnel)
    if 'registration' in buyer_data:
        _add_registration_details(partner_section.find("PartnerDetails"), buyer_data['registration'])
    
    return partner_section

def add_delivery_party(parent: ET.Element, delivery_data: Dict[str, Any]) -> ET.Element:
    """
    Ajoute les informations du point de livraison (DP - Delivery Point) à la facture TEIF.
    
    Structure TEIF 1.8.8:
    - RANG 4: PartnerSection (obligatoire)
      - RANG 5: NAD (obligatoire)
        - RANG 6: LOC (optionnel, répétable)
        - RANG 7-12: RFF, DTM, CTA (optionnels)
    
    Args:
        parent: L'élément parent XML
        delivery_data: Dictionnaire contenant les données du point de livraison avec les clés:
            - id: Identifiant du point de livraison (obligatoire)
            - name: Nom du point de livraison (obligatoire)
            - address: Dictionnaire d'adresse (obligatoire)
            - contacts: Liste de contacts (optionnel)
            - references: Dictionnaire de références (optionnel)
            - location: Dictionnaire de localisation (optionnel)
            - registration: Dictionnaire d'immatriculation (optionnel)
            
    Returns:
        ET.Element: L'élément PartnerSection du point de livraison
        
    Raises:
        ValueError: Si les champs obligatoires sont manquants ou invalides
    """
    # Vérification des champs obligatoires
    required_fields = ['id', 'name', 'address']
    validate_required_fields(delivery_data, required_fields)
    
    # Vérification de l'adresse
    if 'address' in delivery_data:
        required_address_fields = ['street', 'city', 'postal_code', 'country']
        validate_required_fields(delivery_data['address'], required_address_fields)
        
        # Validation du code pays
        if 'country' in delivery_data['address']:
            validate_country_code(delivery_data['address']['country'])
    
    # Création de la section partenaire
    partner_section = create_partner_section(parent, delivery_data, 'I-63')
    
    # Ajout de l'adresse
    if 'address' in delivery_data:
        _add_address(partner_section.find("PartnerDetails").find("Nad"), delivery_data['address'])
    
    # Ajout des références si présentes
    if 'references' in delivery_data and delivery_data['references']:
        _add_references_section(partner_section.find("PartnerDetails"), delivery_data['references'])
    
    # Ajout des contacts si présents
    if 'contacts' in delivery_data and delivery_data['contacts']:
        for contact in delivery_data['contacts']:
            _add_contact_section(partner_section.find("PartnerDetails"), contact)
    
    # Ajout de la localisation si présente
    if 'location' in delivery_data and delivery_data['location']:
        _add_location_section(partner_section.find("PartnerDetails"), delivery_data['location'])
    
    # Ajout des détails d'immatriculation si présents
    if 'registration' in delivery_data and delivery_data['registration']:
        _add_registration_details(partner_section.find("PartnerDetails"), delivery_data['registration'])
    
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

def _add_address(parent: ET.Element, address_data: Dict[str, Any]) -> None:
    """
    Add address information to a partner section.
    
    Args:
        parent: The parent XML element
        address_data: Dictionary containing address information
    """
    address = ET.SubElement(parent, "Address")
    
    # Add street address (required)
    if 'street' in address_data:
        street = ET.SubElement(address, "Street")
        street.text = address_data['street']
    
    # Add city (required)
    if 'city' in address_data:
        city = ET.SubElement(address, "City")
        city.text = address_data['city']
    
    # Add postal code (required)
    if 'postal_code' in address_data:
        postal_code = ET.SubElement(address, "PostalCode")
        postal_code.text = str(address_data['postal_code'])
    
    # Add country code (required, 2-letter ISO code)
    if 'country' in address_data:
        country = ET.SubElement(address, "CountryCode")
        country.text = address_data['country']
    
    # Add additional address lines if provided
    if 'additional_lines' in address_data and isinstance(address_data['additional_lines'], list):
        for line in address_data['additional_lines']:
            if line:
                additional_line = ET.SubElement(address, "AdditionalAddressLine")
                additional_line.text = str(line)

def _add_contact_section(parent: ET.Element, contact_data: Dict[str, Any]) -> None:
    """
    Add contact information to a partner section.
    
    Args:
        parent: The parent XML element
        contact_data: Dictionary containing contact information
    """
    contact = ET.SubElement(parent, "Contact")
    
    # Add contact person name
    if 'name' in contact_data:
        person = ET.SubElement(contact, "PersonName")
        person.text = contact_data['name']
    
    # Add department if provided
    if 'department' in contact_data and contact_data['department']:
        dept = ET.SubElement(contact, "Department")
        dept.text = contact_data['department']
    
    # Add communication channels
    if 'phone' in contact_data and contact_data['phone']:
        phone = ET.SubElement(contact, "Communication")
        phone.set("type", "TE")  # TE = Telephone
        phone.text = contact_data['phone']
    
    if 'email' in contact_data and contact_data['email']:
        email = ET.SubElement(contact, "Communication")
        email.set("type", "EM")  # EM = Email
        email.text = contact_data['email']

def _add_location_section(parent: ET.Element, location_data: Dict[str, Any]) -> None:
    """
    Add location information to a partner section.
    
    Args:
        parent: The parent XML element
        location_data: Dictionary containing location information
    """
    location = ET.SubElement(parent, "Location")
    
    # Add location type if provided
    if 'type' in location_data:
        location.set("type", location_data['type'])
    
    # Add location identifier if provided
    if 'id' in location_data:
        loc_id = ET.SubElement(location, "LocationIdentifier")
        if 'id_type' in location_data:
            loc_id.set("type", location_data['id_type'])
        loc_id.text = str(location_data['id'])
    
    # Add location name if provided
    if 'name' in location_data:
        name = ET.SubElement(location, "LocationName")
        name.text = location_data['name']
    
    # Add address if provided
    if 'address' in location_data and isinstance(location_data['address'], dict):
        _add_address(location, location_data['address'])

def _add_references_section(parent: ET.Element, references: List[Dict[str, str]]) -> None:
    """
    Add reference information to a partner section.
    
    Args:
        parent: The parent XML element
        references: List of reference dictionaries, each with 'type' and 'value' keys
    """
    for ref in references:
        if 'type' in ref and 'value' in ref:
            reference = ET.SubElement(parent, "Reference")
            reference.set("type", ref['type'])
            reference.text = str(ref['value'])

class PartnerSection:
    def __init__(self, parent: ET.Element, partner_data: Dict[str, Any], function_code: str):
        self.parent = parent
        self.partner_data = partner_data
        self.function_code = function_code
        self.partner_section = create_partner_section(parent, partner_data, function_code)
