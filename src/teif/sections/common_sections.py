"""
Module pour les sections communes utilisées dans différents contextes du document TEIF.
"""
from typing import Dict, Any, Optional, List
#import xml.etree.ElementTree as ET
from lxml import etree as ET

def create_nad_section(parent: ET.Element, nad_data: Dict[str, Any]) -> ET.Element:
    """
    Crée une section NAD (Name and Address) pour les informations de partie.
    
    Args:
        parent: L'élément parent XML
        nad_data: Dictionnaire contenant les données de la section NAD
            - party_id: Identifiant de la partie (obligatoire)
            - party_type: Type de partie (ex: 'BY' pour acheteur, 'SU' pour vendeur)
            - name: Nom de la partie (optionnel)
            - address: Adresse (optionnelle)
            - city: Ville (optionnelle)
            - postal_code: Code postal (optionnel)
            - country_code: Code pays (optionnel)
    
    Returns:
        L'élément NAD créé
    """
    if 'party_id' not in nad_data:
        raise ValueError("Le champ 'party_id' est obligatoire pour une section NAD")
    
    nad = ET.SubElement(parent, "NAD")
    
    # Type de partie
    if 'party_type' in nad_data:
        ET.SubElement(nad, "PartyType").text = str(nad_data['party_type'])
    
    # Identifiant de la partie
    party_id = ET.SubElement(nad, "PartyID")
    party_id.text = str(nad_data['party_id'])
    
    # Nom de la partie
    if 'name' in nad_data:
        ET.SubElement(nad, "Name").text = str(nad_data['name'])
    
    # Adresse
    if any(key in nad_data for key in ['address', 'city', 'postal_code', 'country_code']):
        address = ET.SubElement(nad, "Address")
        if 'address' in nad_data:
            ET.SubElement(address, "Street").text = str(nad_data['address'])
        if 'city' in nad_data:
            ET.SubElement(address, "City").text = str(nad_data['city'])
        if 'postal_code' in nad_data:
            ET.SubElement(address, "PostalCode").text = str(nad_data['postal_code'])
        if 'country_code' in nad_data:
            ET.SubElement(address, "CountryCode").text = str(nad_data['country_code'])
    
    return nad

def create_loc_section(parent: ET.Element, loc_data: Dict[str, Any]) -> ET.Element:
    """
    Crée une section LOC (Location) pour les informations de localisation.
    
    Args:
        parent: L'élément parent XML
        loc_data: Dictionnaire contenant les données de localisation
            - type: Type de localisation (ex: '11' pour entrepôt, '92' pour lieu de dédouanement)
            - qualifier: Qualifieur de localisation (optionnel)
            - name: Nom du lieu (optionnel)
            - address: Adresse (optionnelle)
    
    Returns:
        L'élément LOC créé
    """
    if 'type' not in loc_data:
        raise ValueError("Le champ 'type' est obligatoire pour une section LOC")
    
    loc = ET.SubElement(parent, "LOC")
    
    # Type de localisation
    loc_type = ET.SubElement(loc, "LocationType")
    loc_type.text = str(loc_data['type'])
    
    # Qualifieur de localisation
    if 'qualifier' in loc_data:
        ET.SubElement(loc, "LocationQualifier").text = str(loc_data['qualifier'])
    
    # Détails de la localisation
    if 'name' in loc_data or 'address' in loc_data:
        loc_desc = ET.SubElement(loc, "LocationDescription")
        if 'name' in loc_data:
            ET.SubElement(loc_desc, "Name").text = str(loc_data['name'])
        if 'address' in loc_data:
            ET.SubElement(loc_desc, "Address").text = str(loc_data['address'])
    
    return loc

def create_rff_section(parent: ET.Element, rff_data: Dict[str, Any]) -> ET.Element:
    """
    Crée une section RFF (Reference) pour les références.
    
    Args:
        parent: L'élément parent XML
        rff_data: Dictionnaire contenant les données de référence
            - type: Type de référence (obligatoire, ex: 'VA' pour numéro de TVA)
            - value: Valeur de la référence (obligatoire)
            - qualifier: Qualifieur de référence (optionnel)
    
    Returns:
        L'élément RFF créé
    """
    if 'type' not in rff_data or 'value' not in rff_data:
        raise ValueError("Les champs 'type' et 'value' sont obligatoires pour une section RFF")
    
    rff = ET.SubElement(parent, "RFF")
    
    # Type de référence
    ET.SubElement(rff, "ReferenceType").text = str(rff_data['type'])
    
    # Valeur de la référence
    ET.SubElement(rff, "ReferenceValue").text = str(rff_data['value'])
    
    # Qualifieur de référence
    if 'qualifier' in rff_data:
        ET.SubElement(rff, "ReferenceQualifier").text = str(rff_data['qualifier'])
    
    return rff

def create_cta_section(parent: ET.Element, cta_data: Dict[str, Any]) -> ET.Element:
    """
    Crée une section CTA (Contact) pour les informations de contact.
    
    Args:
        parent: L'élément parent XML
        cta_data: Dictionnaire contenant les informations de contact
            - type: Type de contact (ex: 'IC' pour contact interne, 'PD' pour personne désignée)
            - name: Nom du contact (optionnel)
            - department: Département (optionnel)
            - phone: Numéro de téléphone (optionnel)
            - email: Adresse email (optionnel)
    
    Returns:
        L'élément CTA créé
    """
    if 'type' not in cta_data:
        raise ValueError("Le champ 'type' est obligatoire pour une section CTA")
    
    cta = ET.SubElement(parent, "CTA")
    
    # Type de contact
    ET.SubElement(cta, "ContactType").text = str(cta_data['type'])
    
    # Détails du contact
    contact = ET.SubElement(cta, "ContactDetails")
    
    if 'name' in cta_data:
        ET.SubElement(contact, "ContactName").text = str(cta_data['name'])
    
    if 'department' in cta_data:
        ET.SubElement(contact, "Department").text = str(cta_data['department'])
    
    if 'phone' in cta_data:
        ET.SubElement(contact, "PhoneNumber").text = str(cta_data['phone'])
    
    if 'email' in cta_data:
        ET.SubElement(contact, "EmailAddress").text = str(cta_data['email'])
    
    return cta
