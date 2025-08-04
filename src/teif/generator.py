"""
TEIF XML Generator - Official Structure Compliant
================================================

Génère des fichiers XML conformes au standard TEIF (Tunisian Electronic Invoice Format).
Respecte la structure officielle TTN avec tous les éléments obligatoires (M) et conditionnels (C).
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List, Optional
import re


class TEIFGenerator:
    """Générateur de XML TEIF conforme au standard TTN officiel."""
    
    def __init__(self):
        """Initialise le générateur TEIF."""
        self.namespace = "http://www.tradenet.com.tn/teif/invoice/1.0"
        self.xsi_namespace = "http://www.w3.org/2001/XMLSchema-instance"
        self.schema_location = "http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd"
        self.ds_namespace = "http://www.w3.org/2000/09/xmldsig#"
        
    def generate_xml(self, invoice_data: dict, signature_data: dict = None) -> str:
        """
        Génère le XML TEIF à partir des données de facture.
        
        Args:
            invoice_data: Dictionnaire contenant les données de facture
            signature_data: Données de signature électronique (optionnel)
            
        Returns:
            String contenant le XML TEIF formaté
        """
        # Validation et nettoyage des données
        invoice_data = self._validate_and_clean_data(invoice_data)
        
        # Création de l'élément racine
        root = self._create_root_element()
        
        # Construction du XML selon l'ordre officiel TEIF
        self._add_invoice_header(root, invoice_data)      # Rang 1 (M)
        self._add_bgm(root, invoice_data)                 # Rang 2 (M)
        self._add_dtm(root, invoice_data)                 # Rang 3 (M)
        self._add_partner_sections(root, invoice_data)    # Rang 4-5 (M)
        self._add_payment_section(root, invoice_data)     # Rang 6 (C)
        self._add_line_sections(root, invoice_data)       # Rang 7+ (M)
        self._add_invoice_moa(root, invoice_data)         # Rang N-2 (M)
        self._add_invoice_tax(root, invoice_data)         # Rang N-1 (M)
        self._add_ref_ttn_val(root, invoice_data)         # Rang N (M)
        self._add_signature(root, signature_data)         # Signature (M)
        
        return self._format_xml(root)
    
    def _validate_and_clean_data(self, data: dict) -> dict:
        """Valide et nettoie les données d'entrée."""
        cleaned_data = data.copy()
        
        # Force currency to TND
        cleaned_data['currency'] = 'TND'
        
        # Validate invoice number
        invoice_num = cleaned_data.get('invoice_number', 'UNKNOWN')
        if len(invoice_num) < 3 or invoice_num in ['tre', 'UNKNOWN']:
            cleaned_data['invoice_number'] = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Clean and validate company names
        sender = cleaned_data.get('sender', {})
        receiver = cleaned_data.get('receiver', {})
        
        if not sender.get('name') or sender['name'] in ['Rue du Lac Malaren', 'ENTREPRISE EMETTRICE']:
            sender['name'] = 'ENTREPRISE EMETTRICE'
        
        if not receiver.get('name') or receiver['name'] in ['ENTREPRISE RECEPTRICE']:
            receiver['name'] = 'CLIENT DESTINATAIRE'
            
        cleaned_data['sender'] = sender
        cleaned_data['receiver'] = receiver
        
        # Ensure amounts are numeric
        for field in ['total_amount', 'amount_ht', 'tva_amount', 'gross_amount']:
            if field in cleaned_data:
                try:
                    cleaned_data[field] = float(cleaned_data[field])
                except (ValueError, TypeError):
                    cleaned_data[field] = 0.0
        
        return cleaned_data
    
    def _create_root_element(self) -> ET.Element:
        """Crée l'élément racine avec les namespaces corrects."""
        root = ET.Element("TEIFInvoice")
        root.set("xmlns", self.namespace)
        root.set("xmlns:xsi", self.xsi_namespace)
        root.set("xsi:schemaLocation", self.schema_location)
        return root
    
    def _add_invoice_header(self, root: ET.Element, data: dict):
        """Ajoute l'en-tête de facture (Rang 1 - M)."""
        header = ET.SubElement(root, "InvoiceHeader", version="1.0")
        
        # MessageId format: TTN-{InvoiceNumber}-{YYYYMMDDHHmmss}
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        invoice_num = data.get('invoice_number', 'UNKNOWN')
        message_id = f"TTN-{invoice_num}-{timestamp}"
        
        # Ensure MessageId doesn't exceed 50 characters
        if len(message_id) > 50:
            message_id = message_id[:50]
            
        ET.SubElement(header, "MessageId").text = message_id
    
    def _add_bgm(self, root: ET.Element, data: dict):
        """Ajoute le début du message (Rang 2 - M)."""
        bgm = ET.SubElement(root, "Bgm")
        ET.SubElement(bgm, "DocumentTypeCode").text = "380"  # Commercial Invoice
        
        # Clean document number
        doc_number = data.get('invoice_number', 'UNKNOWN')
        doc_number = re.sub(r'[^a-zA-Z0-9\-_]', '', doc_number)[:35]
        ET.SubElement(bgm, "DocumentNumber").text = doc_number
    
    def _add_dtm(self, root: ET.Element, data: dict):
        """Ajoute la date/heure (Rang 3 - M)."""
        dtm = ET.SubElement(root, "Dtm")
        ET.SubElement(dtm, "DateTimeQualifier").text = "137"  # Document date
        
        # Format date as YYYY-MM-DD
        invoice_date = data.get('invoice_date', datetime.now().strftime("%Y-%m-%d"))
        try:
            # Validate date format
            datetime.strptime(invoice_date, "%Y-%m-%d")
        except ValueError:
            invoice_date = datetime.now().strftime("%Y-%m-%d")
            
        ET.SubElement(dtm, "DateTime").text = invoice_date
    
    def _add_partner_sections(self, root: ET.Element, data: dict):
        """Ajoute les sections partenaires (Rang 4-5 - M)."""
        sender = data.get('sender', {})
        receiver = data.get('receiver', {})
        
        # Supplier section
        supplier_section = ET.SubElement(root, "PartnerSection", role="supplier")
        supplier_nad = ET.SubElement(supplier_section, "Nad")
        ET.SubElement(supplier_nad, "PartyQualifier").text = "SU"
        ET.SubElement(supplier_nad, "PartyId").text = sender.get('identifier', sender.get('tax_id', 'UNKNOWN'))
        ET.SubElement(supplier_nad, "PartyName").text = sender.get('name', 'ENTREPRISE EMETTRICE')
        ET.SubElement(supplier_nad, "PartyAddress").text = self._format_address(sender)
        
        # Buyer section
        buyer_section = ET.SubElement(root, "PartnerSection", role="buyer")
        buyer_nad = ET.SubElement(buyer_section, "Nad")
        ET.SubElement(buyer_nad, "PartyQualifier").text = "BY"
        ET.SubElement(buyer_nad, "PartyId").text = receiver.get('identifier', receiver.get('tax_id', 'UNKNOWN'))
        ET.SubElement(buyer_nad, "PartyName").text = receiver.get('name', 'CLIENT DESTINATAIRE')
        ET.SubElement(buyer_nad, "PartyAddress").text = self._format_address(receiver)
    
    def _format_address(self, party: dict) -> str:
        """Formate l'adresse d'une partie."""
        address_parts = []
        
        if party.get('address'):
            address_parts.append(party['address'])
        if party.get('city'):
            address_parts.append(party['city'])
        if party.get('postal_code'):
            address_parts.append(party['postal_code'])
            
        return ', '.join(address_parts) if address_parts else 'Adresse non spécifiée'
    
    def _add_payment_section(self, root: ET.Element, data: dict):
        """Ajoute la section paiement (Rang 6 - C)."""
        # Only add if payment terms are specified
        payment_terms = data.get('payment_terms')
        if payment_terms:
            pyt_section = ET.SubElement(root, "PytSection")
            pyt = ET.SubElement(pyt_section, "Pyt")
            ET.SubElement(pyt, "PaymentTermsTypeCode").text = "1"  # Net payment
            ET.SubElement(pyt, "PaymentTermsDescription").text = payment_terms
    
    def _add_line_sections(self, root: ET.Element, data: dict):
        """Ajoute les sections lignes (Rang 7+ - M)."""
        items = data.get('items', [])
        
        # If no items, create a default line
        if not items:
            items = [{
                'description': 'Service/Produit',
                'quantity': 1.0,
                'unit_price': data.get('amount_ht', 0.0),
                'total_price': data.get('amount_ht', 0.0),
                'tax_rate': 19.0
            }]
        
        for i, item in enumerate(items, 1):
            self._add_line_section(root, item, i, data.get('invoice_date'))
    
    def _add_line_section(self, root: ET.Element, item: dict, line_number: int, invoice_date: str):
        """Ajoute une section ligne individuelle."""
        lin_section = ET.SubElement(root, "LinSection", lineNumber=str(line_number))
        
        # Item description
        lin_imd = ET.SubElement(lin_section, "LinImd")
        ET.SubElement(lin_imd, "ItemDescriptionType").text = "F"  # Free text
        ET.SubElement(lin_imd, "ItemDescription").text = item.get('description', 'Service/Produit')
        
        # Quantity
        lin_qty = ET.SubElement(lin_section, "LinQty")
        ET.SubElement(lin_qty, "QuantityQualifier").text = "47"  # Invoiced quantity
        ET.SubElement(lin_qty, "Quantity").text = str(item.get('quantity', 1.0))
        ET.SubElement(lin_qty, "MeasureUnitQualifier").text = item.get('unit', 'PCE')
        
        # Date
        lin_dtm = ET.SubElement(lin_section, "LinDtm")
        ET.SubElement(lin_dtm, "DateTimeQualifier").text = "137"
        ET.SubElement(lin_dtm, "DateTime").text = invoice_date or datetime.now().strftime("%Y-%m-%d")
        
        # Tax
        lin_tax = ET.SubElement(lin_section, "LinTax")
        ET.SubElement(lin_tax, "DutyTaxFeeTypeCode").text = "VAT"
        
        tax_rate = item.get('tax_rate', 19.0)
        ET.SubElement(lin_tax, "DutyTaxFeeRate").text = f"{tax_rate:.2f}"
        
        tax_payment_date = ET.SubElement(lin_tax, "TaxPaymentDate")
        ET.SubElement(tax_payment_date, "DateTimeQualifier").text = "140"
        ET.SubElement(tax_payment_date, "DateTime").text = invoice_date or datetime.now().strftime("%Y-%m-%d")
        
        # Monetary amount
        lin_moa = ET.SubElement(lin_section, "LinMoa")
        ET.SubElement(lin_moa, "MonetaryAmountTypeQualifier").text = "203"  # Line amount
        ET.SubElement(lin_moa, "MonetaryAmount").text = f"{item.get('total_price', 0.0):.3f}"
        ET.SubElement(lin_moa, "CurrencyCode").text = "TND"
        
        # Reference
        rff = ET.SubElement(lin_moa, "Rff")
        ET.SubElement(rff, "ReferenceQualifier").text = "LI"
        ET.SubElement(rff, "ReferenceNumber").text = f"LINE-{line_number}"
    
    def _add_invoice_moa(self, root: ET.Element, data: dict):
        """Ajoute les montants de facture (Rang N-2 - M)."""
        invoice_moa = ET.SubElement(root, "InvoiceMoa")
        
        # Amount excluding VAT
        moa_ht = ET.SubElement(invoice_moa, "Moa")
        ET.SubElement(moa_ht, "MonetaryAmountTypeQualifier").text = "86"  # Total excluding VAT
        ET.SubElement(moa_ht, "MonetaryAmount").text = f"{data.get('amount_ht', 0.0):.3f}"
        ET.SubElement(moa_ht, "CurrencyCode").text = "TND"
        
        # Total amount including VAT (if different)
        total_amount = data.get('total_amount', data.get('gross_amount', 0.0))
        if total_amount != data.get('amount_ht', 0.0):
            moa_ttc = ET.SubElement(invoice_moa, "Moa")
            ET.SubElement(moa_ttc, "MonetaryAmountTypeQualifier").text = "125"  # Total including VAT
            ET.SubElement(moa_ttc, "MonetaryAmount").text = f"{total_amount:.3f}"
            ET.SubElement(moa_ttc, "CurrencyCode").text = "TND"
    
    def _add_invoice_tax(self, root: ET.Element, data: dict):
        """Ajoute les informations de taxe (Rang N-1 - M)."""
        invoice_tax = ET.SubElement(root, "InvoiceTax")
        tax = ET.SubElement(invoice_tax, "Tax")
        
        ET.SubElement(tax, "DutyTaxFeeTypeCode").text = "TVA"
        
        # Determine tax rate
        tax_rate = 19.0  # Default Tunisian VAT rate
        items = data.get('items', [])
        if items and items[0].get('tax_rate'):
            tax_rate = items[0]['tax_rate']
            
        ET.SubElement(tax, "DutyTaxFeeRate").text = f"{tax_rate:.2f}"
        
        # Tax amount
        moa = ET.SubElement(tax, "Moa")
        ET.SubElement(moa, "MonetaryAmountTypeQualifier").text = "124"  # Tax amount
        ET.SubElement(moa, "MonetaryAmount").text = f"{data.get('tva_amount', 0.0):.3f}"
        ET.SubElement(moa, "CurrencyCode").text = "TND"
    
    def _add_ref_ttn_val(self, root: ET.Element, data: dict):
        """Ajoute la référence TTN (Rang N - M)."""
        ref_ttn_val = ET.SubElement(root, "RefTtnVal")
        reference = ET.SubElement(ref_ttn_val, "Reference")
        
        ET.SubElement(reference, "ReferenceQualifier").text = "AAK"
        
        # Generate unique reference
        invoice_num = data.get('invoice_number', 'UNKNOWN')
        ref_number = f"{invoice_num}-REF-{datetime.now().strftime('%Y%m%d')}"
        ET.SubElement(reference, "ReferenceNumber").text = ref_number
        
        # Reference date
        ref_date = ET.SubElement(reference, "ReferenceDate")
        ET.SubElement(ref_date, "DateTimeQualifier").text = "171"
        ET.SubElement(ref_date, "DateTime").text = data.get('invoice_date', datetime.now().strftime("%Y-%m-%d"))
    
    def _add_signature(self, root: ET.Element, signature_data: dict = None):
        """Ajoute la section signature (M)."""
        signature = ET.SubElement(root, "Signature")
        signature.set("xmlns:ds", self.ds_namespace)
        
        # Signed info
        signed_info = ET.SubElement(signature, "ds:SignedInfo")
        
        # Canonicalization method
        canon_method = ET.SubElement(signed_info, "ds:CanonicalizationMethod")
        canon_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        
        # Signature method
        sig_method = ET.SubElement(signed_info, "ds:SignatureMethod")
        sig_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        
        # Placeholder for actual signature implementation
        if signature_data:
            # Add actual signature data if provided
            pass
    
    def _format_xml(self, root: ET.Element) -> str:
        """Formate le XML avec indentation."""
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ", encoding=None)
    
    def validate_xml_structure(self, xml_string: str) -> tuple[bool, list]:
        """
        Valide la structure XML TEIF.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            return False, [f"XML Parse Error: {e}"]
        
        # Check mandatory elements
        mandatory_elements = [
            "InvoiceHeader", "Bgm", "Dtm", 
            "PartnerSection", "LinSection", 
            "InvoiceMoa", "InvoiceTax", "RefTtnVal", "Signature"
        ]
        
        for element in mandatory_elements:
            if root.find(f".//{element}") is None:
                errors.append(f"Missing mandatory element: {element}")
        
        # Check partner sections
        supplier_section = root.find(".//PartnerSection[@role='supplier']")
        buyer_section = root.find(".//PartnerSection[@role='buyer']")
        
        if supplier_section is None:
            errors.append("Missing supplier PartnerSection")
        if buyer_section is None:
            errors.append("Missing buyer PartnerSection")
        
        return len(errors) == 0, errors
