"""
Module pour la gestion des références TTN et autres références de documents.
"""
from typing import Dict, Any, List, Optional, Union
#import xml.etree.ElementTree as ET
from lxml import etree as ET
import base64


class ReferencesSection:
    """
    A class to handle various types of references in TEIF documents.
    
    This class provides methods to create and manage document references,
    TTN references, and other types of references according to the TEIF 1.8.8 standard.
    """
    
    def __init__(self):
        """Initialize a new ReferencesSection instance."""
        self.references = []
    
    def add_reference(self, 
                     ref_type: str, 
                     value: str, 
                     ref_format: Optional[str] = None) -> None:
        """
        Add a generic reference to the section.
        
        Args:
            ref_type: Type of reference (e.g., 'ON', 'VN', 'FC', 'BC')
            value: The reference value
            ref_format: Optional format of the reference
        """
        self.references.append({
            'type': ref_type,
            'value': value,
            'format': ref_format
        })
    
    def add_ttn_reference(self,
                         number: str,
                         ref_type: str = 'TTNREF',
                         date: Optional[str] = None,
                         qr_code: Optional[str] = None) -> None:
        """
        Add a TTN reference with optional QR code.
        
        Args:
            number: Reference number
            ref_type: Type of reference (default: 'TTNREF')
            date: Reference date in DDMMYY format (optional)
            qr_code: Base64 encoded QR code (optional)
        """
        self.references.append({
            'type': ref_type,
            'value': number,
            'date': date,
            'qr_code': qr_code,
            'is_ttn': True
        })
    
    def add_document_reference(self,
                             doc_id: str,
                             doc_type: Optional[str] = None,
                             doc_date: Optional[str] = None,
                             description: Optional[str] = None) -> None:
        """
        Add a document reference.
        
        Args:
            doc_id: Document identifier
            doc_type: Type of document (optional)
            doc_date: Document date (optional)
            description: Document description (optional)
        """
        self.references.append({
            'type': 'DOCREF',
            'value': doc_id,
            'doc_type': doc_type,
            'date': doc_date,
            'description': description,
            'is_document': True
        })
    
    def to_xml(self, parent: ET.Element = None) -> ET.Element:
        """
        Generate the XML representation of the references section.
        
        Args:
            parent: The parent XML element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            ref_section = ET.Element('ReferencesSection')
        else:
            ref_section = ET.SubElement(parent, 'ReferencesSection')
        
        for ref in self.references:
            if ref.get('is_ttn'):
                self._add_ttn_reference_element(ref_section, ref)
            elif ref.get('is_document'):
                self._add_document_reference_element(ref_section, ref)
            else:
                self._add_generic_reference_element(ref_section, ref)
        
        return ref_section
    
    def _add_generic_reference_element(self, parent: ET.Element, ref: Dict[str, Any]) -> None:
        """Helper method to add a generic reference element."""
        ref_elem = ET.SubElement(parent, 'Reference')
        ET.SubElement(ref_elem, 'ReferenceType').text = str(ref['type'])
        ET.SubElement(ref_elem, 'ReferenceValue').text = str(ref['value'])
        
        if 'format' in ref and ref['format']:
            ET.SubElement(ref_elem, 'ReferenceFormat').text = str(ref['format'])
    
    def _add_ttn_reference_element(self, parent: ET.Element, ref: Dict[str, Any]) -> None:
        """Helper method to add a TTN reference element."""
        ref_elem = ET.SubElement(parent, 'TTNReference')
        
        # Add reference type and value
        ET.SubElement(ref_elem, 'ReferenceType').text = str(ref['type'])
        ET.SubElement(ref_elem, 'ReferenceValue').text = str(ref['value'])
        
        # Add date if provided
        if 'date' in ref and ref['date']:
            ET.SubElement(ref_elem, 'ReferenceDate').text = str(ref['date'])
        
        # Add QR code if provided
        if 'qr_code' in ref and ref['qr_code']:
            qr_elem = ET.SubElement(ref_elem, 'QRCode')
            qr_elem.text = str(ref['qr_code'])
    
    def _add_document_reference_element(self, parent: ET.Element, ref: Dict[str, Any]) -> None:
        """Helper method to add a document reference element."""
        doc_ref = ET.SubElement(parent, 'DocumentReference')
        
        # Add document ID
        ET.SubElement(doc_ref, 'DocumentID').text = str(ref['value'])
        
        # Add document type if provided
        if 'doc_type' in ref and ref['doc_type']:
            ET.SubElement(doc_ref, 'DocumentType').text = str(ref['doc_type'])
        
        # Add document date if provided
        if 'date' in ref and ref['date']:
            ET.SubElement(doc_ref, 'DocumentDate').text = str(ref['date'])
        
        # Add description if provided
        if 'description' in ref and ref['description']:
            ET.SubElement(doc_ref, 'DocumentDescription').text = str(ref['description'])

def create_reference(parent: ET.Element, ref_data: Dict[str, Any]) -> ET.Element:
    """
    Crée un élément de référence générique.
    
    Args:
        parent: L'élément parent XML
        ref_data: Dictionnaire contenant les données de référence
            - type: Type de référence (obligatoire)
            - value: Valeur de la référence (obligatoire)
            - format: Format de la référence (optionnel)
            
    Returns:
        L'élément de référence créé
        
    Raises:
        ValueError: Si les champs obligatoires sont manquants
    """
    if not all(key in ref_data for key in ['type', 'value']):
        raise ValueError("Les champs 'type' et 'value' sont obligatoires pour une référence")
    
    ref_elem = ET.SubElement(parent, "Reference")
    ET.SubElement(ref_elem, "ReferenceType").text = str(ref_data['type'])
    ET.SubElement(ref_elem, "ReferenceValue").text = str(ref_data['value'])
    
    if 'format' in ref_data:
        ref_elem.set('format', str(ref_data['format']))
        
    return ref_elem

def add_ttn_reference(parent: ET.Element, ref_data: Dict[str, Any]) -> None:
    """
    Ajoute une référence TTN avec QR code.
    
    Args:
        parent: L'élément parent XML
        ref_data: Dictionnaire contenant les données de référence
            - number: Numéro de référence (obligatoire)
            - type: Type de référence (optionnel, défaut: 'TTNREF')
            - date: Date de référence au format DDMMYY (optionnel)
            - qr_code: Code QR encodé en base64 (optionnel)
    
    Raises:
        ValueError: Si le numéro de référence est manquant
    """
    if 'number' not in ref_data:
        raise ValueError("Le champ 'number' est obligatoire pour une référence TTN")
    
    ref_elem = ET.SubElement(parent, "TTNReference")
    
    # Type de référence
    ref_type = ref_data.get('type', 'TTNREF')
    ET.SubElement(ref_elem, "ReferenceType").text = ref_type
    
    # Numéro de référence
    ET.SubElement(ref_elem, "ReferenceNumber").text = str(ref_data['number'])
    
    # Date de référence
    if 'date' in ref_data:
        ET.SubElement(ref_elem, "ReferenceDate").text = str(ref_data['date'])
    
    # Code QR (optionnel)
    if 'qr_code' in ref_data:
        try:
            # Décoder pour vérifier que c'est un QR code valide
            qr_data = ref_data['qr_code']
            if isinstance(qr_data, str):
                # Supprimer le préfixe si présent (ex: 'data:image/png;base64,')
                if ';base64,' in qr_data:
                    qr_data = qr_data.split(';base64,', 1)[1]
                # Décoder pour vérifier
                base64.b64decode(qr_data)
                
                qr_elem = ET.SubElement(ref_elem, "QRCode")
                qr_elem.text = qr_data
                qr_elem.set("mimeCode", "image/png")  # Format par défaut
                
                # Ajouter l'encodage si ce n'est pas déjà fait
                if not qr_data.startswith('data:image/'):
                    qr_elem.text = f"data:image/png;base64,{qr_data}"
                    
        except Exception as e:
            # En cas d'erreur, on ignore simplement le QR code
            pass

def add_document_reference(parent: ET.Element, doc_data: Dict[str, Any]) -> None:
    """
    Ajoute une référence à un document.
    
    Args:
        parent: L'élément parent XML
        doc_data: Dictionnaire contenant les données du document
            - id: Identifiant du document (obligatoire)
            - type: Type de document (optionnel)
            - date: Date du document (optionnel)
            - description: Description du document (optionnel)
    """
    if 'id' not in doc_data:
        return
    
    doc_elem = ET.SubElement(parent, "DocumentReference")
    
    # Type de document
    if 'type' in doc_data:
        ET.SubElement(
            doc_elem,
            "DocumentTypeCode",
            listID="I-200"  # Référentiel des types de documents
        ).text = str(doc_data['type'])
    
    # Identifiant du document
    ET.SubElement(doc_elem, "ID").text = str(doc_data['id'])
    
    # Date du document
    if 'date' in doc_data:
        date = doc_data['date']
        if hasattr(date, 'strftime'):
            date = date.strftime('%Y-%m-%d')
        ET.SubElement(doc_elem, "IssueDate").text = str(date)
    
    # Description du document
    if 'description' in doc_data:
        ET.SubElement(doc_elem, "DocumentDescription").text = str(doc_data['description'])

# Add to __all__ to make it available for import
__all__ = [
    'create_reference',
    'add_ttn_reference',
    'add_document_reference',
    'ReferencesSection'
]
