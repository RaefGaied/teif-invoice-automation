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
        self.version = "2.0"  # Latest version from documentation
        
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
        
        # Create InvoiceBody wrapper (mandatory)
        invoice_body = ET.SubElement(root, "InvoiceBody")
        
        self._add_bgm(invoice_body, invoice_data)                 # Rang 2 (M)
        self._add_dtm(invoice_body, invoice_data)                 # Rang 3 (M)
        self._add_partner_sections(invoice_body, invoice_data)    # Rang 4-5 (M)
        self._add_location_sections(invoice_body, invoice_data)   # Rang 13 (C)
        self._add_payment_section(invoice_body, invoice_data)     # Rang 15-16 (C)
        self._add_ftx_sections(invoice_body, invoice_data)        # Rang 21 (C)
        self._add_special_conditions(invoice_body, invoice_data)  # Rang 22-23 (C)
        self._add_line_sections(invoice_body, invoice_data)       # Rang 24+ (M)
        self._add_invoice_moa(invoice_body, invoice_data)         # Rang 41-42 (M)
        self._add_invoice_tax(invoice_body, invoice_data)         # Rang 46-48 (M)
        self._add_invoice_alc(invoice_body, invoice_data)         # Rang 49-52 (C)
        
        # Elements outside InvoiceBody
        self._add_additional_documents(root, invoice_data)        # Rang 53-54 (C)
        self._add_ref_ttn_val(root, invoice_data)                 # Rang 55-57 (M)
        self._add_signature(root, signature_data)                 # Rang 58 (M)
        
        return self._format_xml(root)
    
    def _create_root_element(self) -> ET.Element:
        """Crée l'élément racine avec les attributs officiels TEIF."""
        root = ET.Element("TEIF")
        root.set("xmlns", self.namespace)
        root.set("xmlns:xsi", self.xsi_namespace)
        root.set("xsi:schemaLocation", self.schema_location)
        root.set("version", self.version)
        root.set("controlingAgency", "TTN")
        return root
    
    def _add_invoice_header(self, root: ET.Element, data: dict):
        """Ajoute l'en-tête de facture (Rang 1 - M)."""
        header = ET.SubElement(root, "InvoiceHeader")
        
        # MessageSenderIdentifier with type attribute
        sender_id = ET.SubElement(header, "MessageSenderIdentifier", type="I-01")
        sender_id.text = data.get('sender', {}).get('identifier', data.get('sender', {}).get('tax_id', ''))
        
        # MessageRecieverIdentifier with type attribute
        receiver_id = ET.SubElement(header, "MessageRecieverIdentifier", type="I-01")
        receiver_id.text = data.get('receiver', {}).get('identifier', data.get('receiver', {}).get('tax_id', ''))
    
    def _add_bgm(self, invoice_body: ET.Element, data: dict):
        """Ajoute le début du message (Rang 2 - M)."""
        bgm = ET.SubElement(invoice_body, "Bgm")
        ET.SubElement(bgm, "DocumentTypeCode").text = "380"  # Commercial Invoice
        
        # Clean document number
        doc_number = data.get('invoice_number', 'UNKNOWN')
        doc_number = re.sub(r'[^a-zA-Z0-9\-_]', '', doc_number)[:35]
        ET.SubElement(bgm, "DocumentNumber").text = doc_number
    
    def _add_dtm(self, invoice_body: ET.Element, data: dict):
        """Ajoute la date/heure (Rang 3 - M)."""
        dtm = ET.SubElement(invoice_body, "Dtm")
        ET.SubElement(dtm, "DateTimeQualifier").text = "137"  # Document date
        
        # Format date as YYYY-MM-DD
        invoice_date = data.get('invoice_date', datetime.now().strftime("%Y-%m-%d"))
        try:
            # Validate date format
            datetime.strptime(invoice_date, "%Y-%m-%d")
        except ValueError:
            invoice_date = datetime.now().strftime("%Y-%m-%d")
            
        ET.SubElement(dtm, "DateTime").text = invoice_date
    
    def _add_partner_sections(self, invoice_body: ET.Element, data: dict):
        """Ajoute les sections partenaires (Rang 4-5 - M)."""
        sender = data.get('sender', {})
        receiver = data.get('receiver', {})
        
        # Supplier section
        supplier_section = ET.SubElement(invoice_body, "PartnerSection")
        self._add_partner_details(supplier_section, sender, "SU")
        
        # Buyer section
        buyer_section = ET.SubElement(invoice_body, "PartnerSection")
        self._add_partner_details(buyer_section, receiver, "BY")
    
    def _add_partner_details(self, section: ET.Element, party: dict, qualifier: str):
        """Ajoute les détails d'un partenaire avec tous les champs possibles."""
        # Nad (Rang 5 - M)
        nad = ET.SubElement(section, "Nad")
        
        # PartnerIdentifier with type attribute
        partner_id = ET.SubElement(nad, "PartnerIdentifier", type="I-01")
        partner_id.text = party.get('identifier', party.get('tax_id', 'UNKNOWN'))
        
        ET.SubElement(nad, "PartnerName").text = party.get('name', 'ENTREPRISE' if qualifier == 'SU' else 'CLIENT')
        
        # Partner addresses
        addresses = ET.SubElement(nad, "PartnerAdresses", lang="fr")
        ET.SubElement(addresses, "AdressDescription").text = party.get('address_desc', '')
        ET.SubElement(addresses, "Street").text = party.get('street', party.get('address', ''))
        ET.SubElement(addresses, "CityName").text = party.get('city', '')
        ET.SubElement(addresses, "PostalCode").text = party.get('postal_code', '')
        ET.SubElement(addresses, "Country", codeList="ISO_3166-1").text = party.get('country', 'TN')
        
        # Loc section if available (Rang 6 - C)
        if party.get('location_details'):
            self._add_loc_section(section, party['location_details'])
        
        # RffSection if references available (Rang 7-9 - C)
        if party.get('references'):
            self._add_rff_sections(section, party['references'])
        
        # CtaSection if contact available (Rang 10-12 - C)
        if party.get('contact'):
            self._add_cta_section(section, party['contact'])
    
    def _add_loc_section(self, section: ET.Element, location_details: list):
        """Ajoute les détails de localisation (Rang 6 - C)."""
        for loc_detail in location_details:
            loc = ET.SubElement(section, "Loc")
            ET.SubElement(loc, "LocationQualifier").text = loc_detail.get('qualifier', 'ZZZ')
            ET.SubElement(loc, "LocationIdentifier").text = loc_detail.get('identifier', '')
            if loc_detail.get('description'):
                ET.SubElement(loc, "LocationDescription").text = loc_detail['description']
    
    def _add_rff_sections(self, section: ET.Element, references: list):
        """Ajoute les sections de référence (Rang 7-9 - C)."""
        for ref in references:
            rff_section = ET.SubElement(section, "RffSection")
            reference = ET.SubElement(rff_section, "Reference")
            ET.SubElement(reference, "ReferenceQualifier").text = ref.get('type', 'ZZZ')
            ET.SubElement(reference, "ReferenceNumber").text = ref.get('number', '')
            
            if ref.get('date'):
                ref_date = ET.SubElement(rff_section, "ReferenceDate")
                ET.SubElement(ref_date, "DateTimeQualifier").text = "171"
                ET.SubElement(ref_date, "DateTime").text = ref['date']
    
    def _add_cta_section(self, section: ET.Element, contact: dict):
        """Ajoute la section contact (Rang 10-12 - C)."""
        cta_section = ET.SubElement(section, "CtaSection")
        contact_elem = ET.SubElement(cta_section, "Contact")
        
        ET.SubElement(contact_elem, "ContactFunctionCode").text = contact.get('function_code', 'IC')
        if contact.get('name'):
            ET.SubElement(contact_elem, "ContactName").text = contact['name']
        
        # Communication details
        if contact.get('phone') or contact.get('email') or contact.get('fax'):
            comm = ET.SubElement(cta_section, "Communication")
            ET.SubElement(comm, "CommunicationChannelQualifier").text = "TE"
            if contact.get('phone'):
                ET.SubElement(comm, "CommunicationChannelIdentifier").text = contact['phone']
            elif contact.get('email'):
                ET.SubElement(comm, "CommunicationChannelIdentifier").text = contact['email']
            elif contact.get('fax'):
                ET.SubElement(comm, "CommunicationChannelIdentifier").text = contact['fax']
    
    def _add_location_sections(self, invoice_body: ET.Element, data: dict):
        """Ajoute les sections de localisation (Rang 13-14 - C)."""
        locations = data.get('locations', [])
        if not locations:
            return
            
        for location in locations:
            loc_section = ET.SubElement(invoice_body, "LocSection")
            loc_details = ET.SubElement(loc_section, "LocDetails")
            ET.SubElement(loc_details, "LocationQualifier").text = location.get('qualifier', 'ZZZ')
            ET.SubElement(loc_details, "LocationIdentifier").text = location.get('identifier', '')
            if location.get('description'):
                ET.SubElement(loc_details, "LocationDescription").text = location['description']
    
    def _add_payment_section(self, invoice_body: ET.Element, data: dict):
        """Ajoute la section paiement (Rang 15-20 - C)."""
        payment_info = data.get('payment_info', {})
        
        if payment_info or data.get('payment_terms'):
            pyt_section = ET.SubElement(invoice_body, "PytSection")
            pyt = ET.SubElement(pyt_section, "Pyt")
            
            # Payment terms
            terms_code = payment_info.get('terms_code', '1')
            terms_desc = payment_info.get('terms_description') or data.get('payment_terms', 'Net 30 jours')
            
            ET.SubElement(pyt, "PaymentTermsTypeCode").text = terms_code
            ET.SubElement(pyt, "PaymentTermsDescription").text = terms_desc
            
            # PytDtm if due date available (Rang 17 - C)
            if payment_info.get('due_date'):
                pyt_dtm = ET.SubElement(pyt_section, "PytDtm")
                ET.SubElement(pyt_dtm, "DateTimeQualifier").text = "13"
                ET.SubElement(pyt_dtm, "DateTime").text = payment_info['due_date']
            
            # PytMoa if payment amount specified (Rang 18 - C)
            if payment_info.get('amount'):
                pyt_moa = ET.SubElement(pyt_section, "PytMoa")
                moa = ET.SubElement(pyt_moa, "Moa")
                ET.SubElement(moa, "MonetaryAmountTypeQualifier").text = "9"
                ET.SubElement(moa, "MonetaryAmount").text = f"{payment_info['amount']:.3f}"
                ET.SubElement(moa, "CurrencyCode").text = "TND"
            
            # PytPai if payment instructions available (Rang 19 - C)
            if payment_info.get('instructions'):
                pyt_pai = ET.SubElement(pyt_section, "PytPai")
                ET.SubElement(pyt_pai, "PaymentInstructionCode").text = payment_info['instructions'].get('code', '1')
                if payment_info['instructions'].get('description'):
                    ET.SubElement(pyt_pai, "PaymentInstructionDescription").text = payment_info['instructions']['description']
            
            # PytFii if financial institution available (Rang 20 - C)
            if payment_info.get('bank_details'):
                self._add_pyt_fii(pyt_section, payment_info['bank_details'])
    
    def _add_pyt_fii(self, section: ET.Element, bank_details: dict):
        """Ajoute les informations d'institution financière pour paiement (Rang 20 - C)."""
        pyt_fii = ET.SubElement(section, "PytFii")
        ET.SubElement(pyt_fii, "PartyQualifier").text = "BK"
        
        if bank_details.get('bank_code'):
            ET.SubElement(pyt_fii, "PartyIdentifier").text = bank_details['bank_code']
        if bank_details.get('bank_name'):
            ET.SubElement(pyt_fii, "PartyName").text = bank_details['bank_name']
        if bank_details.get('account_number'):
            ET.SubElement(pyt_fii, "AccountNumber").text = bank_details['account_number']
    
    def _add_ftx_sections(self, invoice_body: ET.Element, data: dict):
        """Ajoute les sections de texte libre (Rang 21 - C)."""
        free_texts = data.get('free_texts', [])
        for text in free_texts:
            ftx = ET.SubElement(invoice_body, "Ftx")
            ET.SubElement(ftx, "TextSubjectQualifier").text = text.get('subject', 'ZZZ')
            ET.SubElement(ftx, "TextFunctionCode").text = text.get('function', '1')
            if text.get('content'):
                ET.SubElement(ftx, "TextLiteral").text = text['content']
    
    def _add_special_conditions(self, invoice_body: ET.Element, data: dict):
        """Ajoute les conditions spéciales (Rang 22-23 - C)."""
        special_conditions = data.get('special_conditions', [])
        if not special_conditions:
            return
            
        conditions_section = ET.SubElement(invoice_body, "SpecialConditions")
        for condition in special_conditions:
            special_condition = ET.SubElement(conditions_section, "SpecialCondition")
            ET.SubElement(special_condition, "ConditionCode").text = condition.get('code', 'ZZZ')
            if condition.get('description'):
                ET.SubElement(special_condition, "ConditionDescription").text = condition['description']
    
    def _add_line_sections(self, invoice_body: ET.Element, data: dict):
        """Ajoute les sections lignes (Rang 24+ - M)."""
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
            self._add_line_section(invoice_body, item, i, data.get('invoice_date'))
    
    def _add_line_section(self, invoice_body: ET.Element, item: dict, line_number: int, invoice_date: str):
        """Ajoute une section ligne individuelle avec tous les éléments TEIF."""
        lin_section = ET.SubElement(invoice_body, "LinSection", lineNumber=str(line_number))
        
        # Lin (Rang 25 - M)
        lin = ET.SubElement(lin_section, "Lin")
        ET.SubElement(lin, "LineItemNumber").text = str(line_number)
        
        # LinImd (Rang 26 - M) - Item description
        lin_imd = ET.SubElement(lin_section, "LinImd")
        ET.SubElement(lin_imd, "ItemDescriptionType").text = "F"  # Free format
        ET.SubElement(lin_imd, "ItemDescription").text = item.get('description', 'Service/Produit')
        
        # Item code if available
        if item.get('code'):
            ET.SubElement(lin_imd, "ItemCode").text = item['code']
        if item.get('brand'):
            ET.SubElement(lin_imd, "ItemBrand").text = item['brand']
        if item.get('model'):
            ET.SubElement(lin_imd, "ItemModel").text = item['model']
        
        # LinApi (Rang 27 - C) - Additional product identification
        if item.get('api_details'):
            self._add_lin_api(lin_section, item['api_details'])
        
        # LinQty (Rang 28-29 - M) - Quantities
        self._add_lin_qty(lin_section, item)
        
        # LinDtm (Rang 30 - C) - Line dates
        if item.get('delivery_date') or invoice_date:
            self._add_lin_dtm(lin_section, item, invoice_date)
        
        # LinMoa (Rang 31-33 - M) - Line monetary amounts
        self._add_lin_moa(lin_section, item)
        
        # LinTax (Rang 34-36 - M) - Line tax information
        self._add_lin_tax(lin_section, item)
        
        # LinAlc (Rang 37-40 - C) - Line allowances/charges
        if item.get('allowances_charges'):
            self._add_lin_alc(lin_section, item['allowances_charges'])
        
        # SubLin (Rang 41 - C) - Sub-line details
        if item.get('sub_lines'):
            self._add_sub_lin(lin_section, item['sub_lines'])
        
        # LinRff (Rang 42 - C) - Line references
        self._add_lin_rff(lin_section, line_number, item)
        
        # LinFtx (Rang 43 - C) - Line free text
        if item.get('notes') or item.get('comments'):
            self._add_lin_ftx(lin_section, item)
    
    def _add_lin_api(self, lin_section: ET.Element, api_details: dict):
        """Ajoute les détails API de ligne (Rang 27 - C)."""
        lin_api = ET.SubElement(lin_section, "LinApi")
        ET.SubElement(lin_api, "ProductIdFunctionQualifier").text = api_details.get('function', 'SA')
        ET.SubElement(lin_api, "ProductIdentifier").text = api_details.get('identifier', '')
        if api_details.get('agency'):
            ET.SubElement(lin_api, "CodeListResponsibleAgencyCode").text = api_details['agency']
    
    def _add_lin_qty(self, lin_section: ET.Element, item: dict):
        """Ajoute les quantités de ligne (Rang 28-29 - M)."""
        # Invoiced quantity (mandatory)
        lin_qty_invoiced = ET.SubElement(lin_section, "LinQty")
        qty_invoiced = ET.SubElement(lin_qty_invoiced, "Qty")
        ET.SubElement(qty_invoiced, "QuantityQualifier").text = "47"  # Invoiced quantity
        ET.SubElement(qty_invoiced, "Quantity").text = str(item.get('quantity', 1))
        ET.SubElement(qty_invoiced, "MeasureUnitCode").text = item.get('unit', 'PCE')
        
        # Delivered quantity if different (conditional)
        delivered_qty = item.get('delivered_quantity')
        if delivered_qty and delivered_qty != item.get('quantity'):
            lin_qty_delivered = ET.SubElement(lin_section, "LinQty")
            qty_delivered = ET.SubElement(lin_qty_delivered, "Qty")
            ET.SubElement(qty_delivered, "QuantityQualifier").text = "46"  # Delivered quantity
            ET.SubElement(qty_delivered, "Quantity").text = str(delivered_qty)
            ET.SubElement(qty_delivered, "MeasureUnitCode").text = item.get('unit', 'PCE')
    
    def _add_lin_dtm(self, lin_section: ET.Element, item: dict, invoice_date: str):
        """Ajoute les dates de ligne (Rang 30 - C)."""
        # Delivery date
        delivery_date = item.get('delivery_date', invoice_date)
        if delivery_date:
            lin_dtm = ET.SubElement(lin_section, "LinDtm")
            dtm = ET.SubElement(lin_dtm, "Dtm")
            ET.SubElement(dtm, "DateTimeQualifier").text = "35"  # Delivery date
            ET.SubElement(dtm, "DateTime").text = delivery_date
    
    def _add_lin_moa(self, lin_section: ET.Element, item: dict):
        """Ajoute les montants monétaires de ligne (Rang 31-33 - M)."""
        # Unit price (mandatory)
        unit_price = item.get('unit_price', 0.0)
        lin_moa_unit = ET.SubElement(lin_section, "LinMoa")
        moa_unit = ET.SubElement(lin_moa_unit, "Moa")
        ET.SubElement(moa_unit, "MonetaryAmountTypeQualifier").text = "146"  # Unit price
        ET.SubElement(moa_unit, "MonetaryAmount").text = f"{unit_price:.3f}"
        ET.SubElement(moa_unit, "CurrencyCode").text = "TND"
        
        # Line total amount (mandatory)
        line_total = item.get('total_amount', unit_price * item.get('quantity', 1))
        lin_moa_total = ET.SubElement(lin_section, "LinMoa")
        moa_total = ET.SubElement(lin_moa_total, "Moa")
        ET.SubElement(moa_total, "MonetaryAmountTypeQualifier").text = "203"  # Line item amount
        ET.SubElement(moa_total, "MonetaryAmount").text = f"{line_total:.3f}"
        ET.SubElement(moa_total, "CurrencyCode").text = "TND"
        
        # Tax amount if specified (conditional)
        tax_amount = item.get('tax_amount')
        if tax_amount:
            lin_moa_tax = ET.SubElement(lin_section, "LinMoa")
            moa_tax = ET.SubElement(lin_moa_tax, "Moa")
            ET.SubElement(moa_tax, "MonetaryAmountTypeQualifier").text = "124"  # Tax amount
            ET.SubElement(moa_tax, "MonetaryAmount").text = f"{tax_amount:.3f}"
            ET.SubElement(moa_tax, "CurrencyCode").text = "TND"
    
    def _add_lin_tax(self, lin_section: ET.Element, item: dict):
        """Ajoute les informations de taxe de ligne (Rang 34-36 - M)."""
        lin_tax = ET.SubElement(lin_section, "LinTax")
        tax = ET.SubElement(lin_tax, "Tax")
        
        # Tax type (TVA for Tunisia)
        ET.SubElement(tax, "DutyTaxFeeTypeCode").text = "TVA"
        
        # Tax category and rate
        tax_rate = item.get('tax_rate', 19.0)  # Default 19% TVA
        tax_category = item.get('tax_category', 'S')  # Standard rate
        
        ET.SubElement(tax, "DutyTaxFeeCategoryCode").text = tax_category
        ET.SubElement(tax, "DutyTaxFeeRate").text = f"{tax_rate:.2f}"
        
        # Tax exemption reason if applicable
        if tax_category in ['E', 'Z'] and item.get('tax_exemption_reason'):
            ET.SubElement(tax, "DutyTaxFeeExemptionReasonCode").text = item['tax_exemption_reason']
        
        # Tax amount
        tax_amount = item.get('tax_amount', 0.0)
        lin_tax_moa = ET.SubElement(lin_tax, "Moa")
        ET.SubElement(lin_tax_moa, "MonetaryAmountTypeQualifier").text = "124"
        ET.SubElement(lin_tax_moa, "MonetaryAmount").text = f"{tax_amount:.3f}"
        ET.SubElement(lin_tax_moa, "CurrencyCode").text = "TND"
    
    def _add_lin_alc(self, lin_section: ET.Element, allowances_charges: list):
        """Ajoute les remises/charges de ligne (Rang 37-40 - C)."""
        for alc_data in allowances_charges:
            lin_alc = ET.SubElement(lin_section, "LinAlc")
            alc = ET.SubElement(lin_alc, "Alc")
            
            ET.SubElement(alc, "AllowanceChargeQualifier").text = alc_data.get('qualifier', 'A')
            ET.SubElement(alc, "AllowanceChargeNumber").text = alc_data.get('number', '1')
            
            # Percentage if applicable
            if alc_data.get('percentage'):
                ET.SubElement(alc, "AllowanceChargeRate").text = f"{alc_data['percentage']:.2f}"
            
            # Amount
            lin_alc_moa = ET.SubElement(lin_alc, "Moa")
            ET.SubElement(lin_alc_moa, "MonetaryAmountTypeQualifier").text = "8"
            ET.SubElement(lin_alc_moa, "MonetaryAmount").text = f"{alc_data.get('amount', 0.0):.3f}"
            ET.SubElement(lin_alc_moa, "CurrencyCode").text = "TND"
            
            # Description
            if alc_data.get('description'):
                lin_alc_ftx = ET.SubElement(lin_alc, "Ftx")
                ET.SubElement(lin_alc_ftx, "TextSubjectQualifier").text = "ZZZ"
                ET.SubElement(lin_alc_ftx, "TextLiteral").text = alc_data['description']
    
    def _add_sub_lin(self, lin_section: ET.Element, sub_lines: list):
        """Ajoute les sous-lignes (Rang 41 - C)."""
        for i, sub_line in enumerate(sub_lines, 1):
            sub_lin = ET.SubElement(lin_section, "SubLin")
            ET.SubElement(sub_lin, "SubLineItemNumber").text = str(i)
            ET.SubElement(sub_lin, "SubLineItemDescription").text = sub_line.get('description', '')
            
            if sub_line.get('quantity'):
                ET.SubElement(sub_lin, "SubLineQuantity").text = str(sub_line['quantity'])
            if sub_line.get('unit_price'):
                ET.SubElement(sub_lin, "SubLineUnitPrice").text = f"{sub_line['unit_price']:.3f}"
    
    def _add_lin_rff(self, lin_section: ET.Element, line_number: int, item: dict):
        """Ajoute les références de ligne (Rang 42 - C)."""
        lin_rff = ET.SubElement(lin_section, "LinRff")
        rff = ET.SubElement(lin_rff, "Rff")
        ET.SubElement(rff, "ReferenceQualifier").text = "LI"  # Line item reference
        ET.SubElement(rff, "ReferenceNumber").text = item.get('reference', f"LINE-{line_number}")
        
        # Additional references if available
        if item.get('purchase_order_ref'):
            po_rff = ET.SubElement(lin_section, "LinRff")
            po_ref = ET.SubElement(po_rff, "Rff")
            ET.SubElement(po_ref, "ReferenceQualifier").text = "ON"  # Purchase order
            ET.SubElement(po_ref, "ReferenceNumber").text = item['purchase_order_ref']
    
    def _add_lin_ftx(self, lin_section: ET.Element, item: dict):
        """Ajoute le texte libre de ligne (Rang 43 - C)."""
        notes = item.get('notes') or item.get('comments', '')
        if notes:
            lin_ftx = ET.SubElement(lin_section, "LinFtx")
            ftx = ET.SubElement(lin_ftx, "Ftx")
            ET.SubElement(ftx, "TextSubjectQualifier").text = "ZZZ"
            ET.SubElement(ftx, "TextFunctionCode").text = "1"
            ET.SubElement(ftx, "TextLiteral").text = notes
    
    def _add_invoice_moa(self, invoice_body: ET.Element, data: dict):
        """Ajoute les montants de facture (Rang 41-42 - M)."""
        invoice_moa = ET.SubElement(invoice_body, "InvoiceMoa")
        
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
    
    def _add_invoice_tax(self, invoice_body: ET.Element, data: dict):
        """Ajoute les informations de taxe (Rang 46-48 - M)."""
        invoice_tax = ET.SubElement(invoice_body, "InvoiceTax")
        tax = ET.SubElement(invoice_tax, "Tax")
        
        ET.SubElement(tax, "DutyTaxFeeTypeCode").text = "TVA"
        
        # Determine tax rate
        tax_rate = 19.0  # Default Tunisian VAT rate
        items = data.get('items', [])
        if items and items[0].get('tax_rate'):
            tax_rate = items[0]['tax_rate']
            
        ET.SubElement(tax, "DutyTaxFeeRate").text = f"{tax_rate:.2f}"
        
        tax_payment_date = ET.SubElement(tax, "TaxPaymentDate")
        ET.SubElement(tax_payment_date, "DateTimeQualifier").text = "140"
        ET.SubElement(tax_payment_date, "DateTime").text = data.get('invoice_date', datetime.now().strftime("%Y-%m-%d"))
        
        # Tax amount
        moa = ET.SubElement(tax, "Moa")
        ET.SubElement(moa, "MonetaryAmountTypeQualifier").text = "124"  # Tax amount
        ET.SubElement(moa, "MonetaryAmount").text = f"{data.get('tva_amount', 0.0):.3f}"
        ET.SubElement(moa, "CurrencyCode").text = "TND"
    
    def _add_invoice_alc(self, invoice_body: ET.Element, data: dict):
        """Ajoute les remises/charges de facture (Rang 49-52 - C)."""
        allowances_charges = data.get('allowances_charges', [])
        if not allowances_charges:
            return
            
        for alc_data in allowances_charges:
            invoice_alc = ET.SubElement(invoice_body, "InvoiceAlc")
            alc = ET.SubElement(invoice_alc, "Alc")
            
            ET.SubElement(alc, "AllowanceChargeQualifier").text = alc_data.get('qualifier', 'A')  # A=Allowance, C=Charge
            ET.SubElement(alc, "AllowanceChargeNumber").text = alc_data.get('number', '1')
            
            # Amount
            moa = ET.SubElement(invoice_alc, "Moa")
            ET.SubElement(moa, "MonetaryAmountTypeQualifier").text = "8"  # Allowance/charge amount
            ET.SubElement(moa, "MonetaryAmount").text = f"{alc_data.get('amount', 0.0):.3f}"
            ET.SubElement(moa, "CurrencyCode").text = "TND"
            
            # Free text if available
            if alc_data.get('description'):
                ftx = ET.SubElement(invoice_alc, "Ftx")
                ET.SubElement(ftx, "TextSubjectQualifier").text = "ZZZ"
                ET.SubElement(ftx, "TextLiteral").text = alc_data['description']
    
    def _add_additional_documents(self, root: ET.Element, data: dict):
        """Ajoute les documents additionnels (Rang 53-54 - C)."""
        additional_docs = data.get('additional_documents', [])
        if not additional_docs:
            return
            
        for doc in additional_docs:
            add_docs = ET.SubElement(root, "AdditionnalDocuments")
            ET.SubElement(add_docs, "DocumentTypeCode").text = doc.get('type', 'ZZZ')
            ET.SubElement(add_docs, "DocumentNumber").text = doc.get('number', '')
            if doc.get('description'):
                ET.SubElement(add_docs, "DocumentDescription").text = doc['description']
            
            if doc.get('date'):
                dtm = ET.SubElement(add_docs, "Dtm")
                ET.SubElement(dtm, "DateTimeQualifier").text = "137"
                ET.SubElement(dtm, "DateTime").text = doc['date']
    
    def _add_ref_ttn_val(self, root: ET.Element, data: dict):
        """Ajoute la référence TTN (Rang 55-57 - M)."""
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
