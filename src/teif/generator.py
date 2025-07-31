"""
TEIF XML Generator
=================

Génère des fichiers XML conformes au standard TEIF (Tunisian Electronic Invoice Format).
Respecte tous les éléments obligatoires (M) et conditionnels (C) du standard TTN.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, List


class TEIFGenerator:
    """Générateur de XML TEIF conforme au standard TTN."""
    
    def __init__(self):
        """Initialise le générateur TEIF."""
        self.namespace = "http://www.tradenet.com.tn/teif/invoice/1.0"
        self.schema_location = "http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd"
        self.version = "1.8.8"  # Version actuelle du format TEIF
    
    def generate_xml(self, invoice_data: Dict, signature_data: Dict = None) -> str:
        """
        Génère le XML TEIF à partir des données de facture.
        
        Args:
            invoice_data: Dictionnaire contenant les données de facture
            signature_data: Données de signature électronique (optionnel)
            
        Returns:
            String contenant le XML TEIF formaté
        """
        # Ensure using TND currency by default and validate mandatory fields
        invoice_data['currency'] = 'TND'
        if 'amount' in invoice_data and not invoice_data.get('currency_code'):
            invoice_data['currency_code'] = 'TND'
            
        root = self._create_root_element()
        
        # Éléments obligatoires (M) selon le standard TEIF
        self._add_invoice_header(root, invoice_data)      # Rang 1 (M)
        self._add_bgm(root, invoice_data)                 # Rang 2 (M)
        self._add_dtm(root, invoice_data)                 # Rang 3 (M)
        self._add_partner_sections(root, invoice_data)    # Rang 4-5 (M)
        
        # Éléments conditionnels (C)
        self._add_payment_section(root, invoice_data)     # Rang 15-16 (C)
        
        # Lignes d'articles (M)
        self._add_line_sections(root, invoice_data)       # Rang 24-37 (M)
        
        # Montants et taxes (M)
        self._add_invoice_amounts(root, invoice_data)     # Rang 41-42 (M)
        self._add_invoice_taxes(root, invoice_data)       # Rang 46-48 (M)
        
        # Éléments de validation et signature (M)
        self._add_ttn_validation(root, invoice_data)      # Rang 55-57 (M)
        self._add_signature(root, signature_data)         # Rang 58 (M)
        
        return self._prettify_xml(root)
    
    def _create_root_element(self) -> ET.Element:
        """Crée l'élément racine avec les namespaces."""
        return ET.Element("TEIF", attrib={
            "controlingAgency": "TTN",
            "version": self.version
        })
    
    def _add_invoice_header(self, root: ET.Element, data: Dict):
        """Ajoute l'en-tête de facture (Rang 1 - M)."""
        header = ET.SubElement(root, "InvoiceHeader")
        
        # Message Sender & Receiver Identifiers
        ET.SubElement(header, "MessageSenderIdentifier", type="I-01").text = data.get("sender", {}).get("identifier", "")
        ET.SubElement(header, "MessageRecieverIdentifier", type="I-01").text = data.get("receiver", {}).get("identifier", "")
    
    def _add_bgm(self, root: ET.Element, data: Dict):
        """Ajoute le début du message (Rang 2 - M)."""
        invoice_body = self._get_or_create_invoice_body(root)
        bgm = ET.SubElement(invoice_body, "Bgm")
        ET.SubElement(bgm, "DocumentIdentifier").text = data.get("invoice_number", "")
        doc_type = ET.SubElement(bgm, "DocumentType", code="I-11")
        doc_type.text = "Facture"
    
    def _get_or_create_invoice_body(self, root: ET.Element) -> ET.Element:
        """Récupère ou crée la section InvoiceBody."""
        invoice_body = root.find("InvoiceBody")
        if invoice_body is None:
            invoice_body = ET.SubElement(root, "InvoiceBody")
        return invoice_body

    def _add_dtm(self, root: ET.Element, data: Dict):
        """Ajoute la date/période (Rang 3 - M)."""
        invoice_body = self._get_or_create_invoice_body(root)
        dtm = ET.SubElement(invoice_body, "Dtm")
        
        # Date de facturation
        date_text = ET.SubElement(dtm, "DateText", format="ddMMyy", functionCode="I-31")
        date_text.text = datetime.strptime(data.get("invoice_date", ""), "%Y-%m-%d").strftime("%d%m%y")
        
        # Période de facturation (si disponible)
        if data.get("invoice_period_start") and data.get("invoice_period_end"):
            period_text = ET.SubElement(dtm, "DateText", format="ddMMyy-ddMMyy", functionCode="I-36")
            start_date = datetime.strptime(data["invoice_period_start"], "%Y-%m-%d").strftime("%d%m%y")
            end_date = datetime.strptime(data["invoice_period_end"], "%Y-%m-%d").strftime("%d%m%y")
            period_text.text = f"{start_date}-{end_date}"
        
        # Date d'échéance
        if data.get("due_date"):
            due_date_text = ET.SubElement(dtm, "DateText", format="ddMMyy", functionCode="I-32")
            due_date_text.text = datetime.strptime(data["due_date"], "%Y-%m-%d").strftime("%d%m%y")
    
    def _add_partner_sections(self, root: ET.Element, data: Dict):
        """Ajoute les sections partenaires (Rang 4-5 - M)."""
        invoice_body = self._get_or_create_invoice_body(root)
        partner_section = ET.SubElement(invoice_body, "PartnerSection")
        
        # Fournisseur (Supplier)
        supplier_details = ET.SubElement(partner_section, "PartnerDetails", functionCode="I-62")
        supplier_nad = ET.SubElement(supplier_details, "Nad")
        ET.SubElement(supplier_nad, "PartnerIdentifier", type="I-01").text = data["sender"].get("identifier", "")
        ET.SubElement(supplier_nad, "PartnerName", nameType="Qualification").text = data["sender"].get("name", "")
        
        # Adresse du fournisseur
        addr = ET.SubElement(supplier_nad, "PartnerAdresses", lang="fr")
        ET.SubElement(addr, "AdressDescription").text = data["sender"].get("address_desc", "")
        ET.SubElement(addr, "Street").text = data["sender"].get("street", "")
        ET.SubElement(addr, "CityName").text = data["sender"].get("city", "")
        ET.SubElement(addr, "PostalCode").text = data["sender"].get("postal_code", "")
        ET.SubElement(addr, "Country", codeList="ISO_3166-1").text = data["sender"].get("country", "TN")
        
        # Références fournisseur
        self._add_partner_references(supplier_details, data["sender"].get("references", []))
        
        # Contacts fournisseur
        self._add_partner_contacts(supplier_details, data["sender"].get("contacts", []))
        
        # Acheteur (Buyer)
        buyer_details = ET.SubElement(partner_section, "PartnerDetails", functionCode="I-64")
        buyer_nad = ET.SubElement(buyer_details, "Nad")
        ET.SubElement(buyer_nad, "PartnerIdentifier", type="I-01").text = data["receiver"].get("identifier", "")
        ET.SubElement(buyer_nad, "PartnerName", nameType="Qualification").text = data["receiver"].get("name", "")
        
        # Adresse de l'acheteur
        addr = ET.SubElement(buyer_nad, "PartnerAdresses", lang="fr")
        ET.SubElement(addr, "AdressDescription").text = data["receiver"].get("address_desc", "")
        ET.SubElement(addr, "Street").text = data["receiver"].get("street", "")
        ET.SubElement(addr, "CityName").text = data["receiver"].get("city", "")
        ET.SubElement(addr, "PostalCode").text = data["receiver"].get("postal_code", "")
        ET.SubElement(addr, "Country", codeList="ISO_3166-1").text = data["receiver"].get("country", "TN")
        
        # Références acheteur
        self._add_partner_references(buyer_details, data["receiver"].get("references", []))

    def _add_partner_references(self, parent: ET.Element, references: List[Dict]):
        """Ajoute les références d'un partenaire."""
        for ref in references:
            ref_section = ET.SubElement(parent, "RffSection")
            reference = ET.SubElement(ref_section, "Reference", refID=ref.get("type", ""))
            reference.text = ref.get("value", "")

    def _add_partner_contacts(self, parent: ET.Element, contacts: List[Dict]):
        """Ajoute les contacts d'un partenaire."""
        for contact in contacts:
            cta_section = ET.SubElement(parent, "CtaSection")
            contact_elem = ET.SubElement(cta_section, "Contact", functionCode="I-94")
            ET.SubElement(contact_elem, "ContactIdentifier").text = contact.get("identifier", "")
            ET.SubElement(contact_elem, "ContactName").text = contact.get("name", "")
            
            if contact.get("communication"):
                comm = ET.SubElement(cta_section, "Communication")
                ET.SubElement(comm, "ComMeansType").text = contact["communication"].get("type", "")
                ET.SubElement(comm, "ComAdress").text = contact["communication"].get("value", "")
    
    def _add_payment_section(self, root: ET.Element, data: Dict):
        """Ajoute la section paiement si disponible (Rang 15-16 - C)."""
        if not data.get("payment_details"):
            return
            
        invoice_body = self._get_or_create_invoice_body(root)
        pyt_section = ET.SubElement(invoice_body, "PytSection")
        
        for payment in data["payment_details"]:
            pyt_details = ET.SubElement(pyt_section, "PytSectionDetails")
            pyt = ET.SubElement(pyt_details, "Pyt")
            
            ET.SubElement(pyt, "PaymentTearmsTypeCode").text = payment.get("type_code", "")
            ET.SubElement(pyt, "PaymentTearmsDescription").text = payment.get("description", "")
            
            # Informations bancaires si disponibles
            if payment.get("bank_details"):
                bank = payment["bank_details"]
                pyt_fii = ET.SubElement(pyt_details, "PytFii", functionCode="I-141")
                
                account = ET.SubElement(pyt_fii, "AccountHolder")
                ET.SubElement(account, "AccountNumber").text = bank.get("account_number", "")
                ET.SubElement(account, "OwnerIdentifier").text = bank.get("owner_id", "")
                
                institution = ET.SubElement(pyt_fii, "InstitutionIdentification", nameCode=bank.get("bank_code", ""))
                ET.SubElement(institution, "BranchIdentifier").text = bank.get("branch_code", "")
                ET.SubElement(institution, "InstitutionName").text = bank.get("bank_name", "")
    
    def _add_line_sections(self, root: ET.Element, data: Dict):
        """Ajoute les lignes d'articles (Rang 24-37 - M)."""
        invoice_body = self._get_or_create_invoice_body(root)
        
        for line_index, item in enumerate(data.get("items", []), 1):
            lin_section = ET.SubElement(invoice_body, "LinSection")
            lin = ET.SubElement(lin_section, "Lin")
            
            # Identifiant de ligne
            ET.SubElement(lin, "ItemIdentifier").text = str(line_index)
            
            # Description de l'article
            lin_imd = ET.SubElement(lin, "LinImd", lang="fr")
            ET.SubElement(lin_imd, "ItemCode").text = item.get("code", "")
            ET.SubElement(lin_imd, "ItemDescription").text = item.get("description", "")
            
            # Quantité
            lin_qty = ET.SubElement(lin, "LinQty")
            quantity = ET.SubElement(lin_qty, "Quantity", measurementUnit="UNIT")
            quantity.text = str(item.get("quantity", 1))
            
            # Taxes de ligne
            for tax in item.get("taxes", []):
                lin_tax = ET.SubElement(lin, "LinTax")
                tax_type = tax.get("tax_type", "").lower()
                if tax_type == "tva" or tax_type == "vat":
                    tax_code = "I-1602"
                    tax_name = "TVA"
                else:
                    tax_code = f"I-16{len(tax_type):02d}"
                    tax_name = tax_type
                ET.SubElement(lin_tax, "TaxTypeName", code=tax_code).text = tax_name
                tax_details = ET.SubElement(lin_tax, "TaxDetails")
                ET.SubElement(tax_details, "TaxRate").text = f"{tax.get('rate', 0.0):.1f}"
            
            # Montants de ligne
            lin_moa = ET.SubElement(lin, "LinMoa")
            
            # Montant HT (prix unitaire * quantité)
            unit_price = item.get("unit_price", 0.0)
            quantity = item.get("quantity", 1.0)
            line_total = unit_price * quantity
            
            moa_ht = ET.SubElement(lin_moa, "MoaDetails")
            moa_ht_elem = ET.SubElement(moa_ht, "Moa", amountTypeCode="I-183", currencyCodeList="ISO_4217")
            amount_ht = ET.SubElement(moa_ht_elem, "Amount", currencyIdentifier=data.get("currency", "TND"))
            amount_ht.text = f"{line_total:.3f}"
            
            # Montant TTC (ajouter les taxes)
            tax_total = sum(tax.get("amount", 0.0) for tax in item.get("taxes", []))
            line_total_ttc = line_total + tax_total
            
            moa_ttc = ET.SubElement(lin_moa, "MoaDetails")
            moa_ttc_elem = ET.SubElement(moa_ttc, "Moa", amountTypeCode="I-171", currencyCodeList="ISO_4217")
            amount_ttc = ET.SubElement(moa_ttc_elem, "Amount", currencyIdentifier=data.get("currency", "TND"))
            amount_ttc.text = f"{line_total_ttc:.3f}"
    
    def _add_invoice_amounts(self, root: ET.Element, data: Dict):
        """Ajoute les montants de facture (Rang 41-42 - M)."""
        invoice_body = self._get_or_create_invoice_body(root)
        invoice_moa = ET.SubElement(invoice_body, "InvoiceMoa")

        # Ensure using TND currency for all amounts
        currency = data.get("currency", "TND")  # Default to TND if not specified
        data["currency"] = currency  # Update the currency in the data dictionary
        
        currency = data.get("currency", "TND")
        
        # Montant brut (total HT)
        items = data.get("items", [])
        gross_amount = sum(
            item.get("unit_price", 0.0) * item.get("quantity", 1.0)
            for item in items
        )
        
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-179", currencyCodeList="ISO_4217")
        amount = ET.SubElement(moa, "Amount", currencyIdentifier=currency)
        amount.text = f"{gross_amount:.3f}"
        
        # Calcul du total avec taxes
        tax_amount = sum(
            sum(tax.get("amount", 0.0) for tax in item.get("taxes", []))
            for item in items
        )
        total_amount = gross_amount + tax_amount
        
        # Montant total avec description en texte
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-180", currencyCodeList="ISO_4217")
        amount = ET.SubElement(moa, "Amount", currencyIdentifier=currency)
        amount.text = f"{total_amount:.3f}"
        if data.get("amount_in_words"):
            ET.SubElement(moa, "AmountDescription", lang="fr").text = data["amount_in_words"]
        
        # Montant HT (même que brut)
        amount_details = ET.SubElement(invoice_moa, "AmountDetails")
        moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-176", currencyCodeList="ISO_4217")
        amount = ET.SubElement(moa, "Amount", currencyIdentifier=currency)
        amount.text = f"{gross_amount:.3f}"
        
        # On itère sur chaque type de taxe pour les montants de TVA et autres taxes
        for tax_type in set(tax["tax_type"].lower() for item in items for tax in item.get("taxes", [])):
            tax_base = sum(
                item.get("unit_price", 0.0) * item.get("quantity", 1.0)
                for item in items
                if any(t["tax_type"].lower() == tax_type for t in item.get("taxes", []))
            )
            
            tax_amount = sum(
                tax["amount"]
                for item in items
                for tax in item.get("taxes", [])
                if tax["tax_type"].lower() == tax_type
            )
            
            # Base taxable
            amount_details = ET.SubElement(invoice_moa, "AmountDetails")
            moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-182", currencyCodeList="ISO_4217")
            amount = ET.SubElement(moa, "Amount", currencyIdentifier=currency)
            amount.text = f"{tax_base:.3f}"
            
            # Montant de la taxe
            amount_details = ET.SubElement(invoice_moa, "AmountDetails")
            moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-181", currencyCodeList="ISO_4217")
            amount = ET.SubElement(moa, "Amount", currencyIdentifier=currency)
            amount.text = f"{tax_amount:.3f}"
    
    def _add_invoice_taxes(self, root: ET.Element, data: Dict):
        """Ajoute les taxes de facture (Rang 46-48 - M)."""
        invoice_body = self._get_or_create_invoice_body(root)
        invoice_tax = ET.SubElement(invoice_body, "InvoiceTax")
        
        # Ajouter toutes les taxes depuis invoice_taxes
        for tax_entry in data.get("invoice_taxes", []):
            tax_details = ET.SubElement(invoice_tax, "InvoiceTaxDetails")
            tax = ET.SubElement(tax_details, "Tax")
            
            # Mapper les types de taxes aux codes TEIF
            tax_type = tax_entry.get("tax_type", "").lower()
            if tax_type == "droit_timbre" or tax_type == "droit de timbre":
                tax_code = "I-1601"
                tax_name = "droit de timbre"
            elif tax_type == "tva" or tax_type == "vat":
                tax_code = "I-1602"
                tax_name = "TVA"
            else:
                tax_code = f"I-16{len(tax_type):02d}"  # Code générique pour autres taxes
                tax_name = tax_type
                
            ET.SubElement(tax, "TaxTypeName", code=tax_code).text = tax_name
            tax_details_elem = ET.SubElement(tax, "TaxDetails")
            ET.SubElement(tax_details_elem, "TaxRate").text = f"{tax_entry.get('rate', 0.0):.1f}"
            
            amount_details = ET.SubElement(tax_details, "AmountDetails")
            moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-178", currencyCodeList="ISO_4217")
            amount = ET.SubElement(moa, "Amount", currencyIdentifier=data.get("currency", "TND"))
            amount.text = f"{tax_entry.get('amount', 0.0):.3f}"
        
        # Add base amounts for each tax if available
        for tax_entry in data.get("invoice_taxes", []):
            if tax_entry.get("base_amount"):
                tax_details = ET.SubElement(invoice_tax, "InvoiceTaxDetails")
                amount_details = ET.SubElement(tax_details, "AmountDetails")
                moa = ET.SubElement(amount_details, "Moa", amountTypeCode="I-177", currencyCodeList="ISO_4217")
                amount = ET.SubElement(moa, "Amount", currencyIdentifier=data.get("currency", "TND"))
                amount.text = f"{tax_entry.get('base_amount', 0.0):.3f}"
    
    def _add_ttn_validation(self, root: ET.Element, data: Dict):
        """Ajoute la référence de validation TTN (Rang 55-57 - M)."""
        ref_ttn_val = ET.SubElement(root, "RefTtnVal")
        
        # TTN Reference
        reference_ttn = ET.SubElement(ref_ttn_val, "ReferenceTTN", refID="I-88")
        reference_ttn.text = data.get("ttn_reference", "")
        
        # Reference Date
        ref_date = ET.SubElement(ref_ttn_val, "ReferenceDate")
        date_text = ET.SubElement(ref_date, "DateText", format="ddMMyyHHmm", functionCode="I-37")
        date_text.text = datetime.now().strftime("%d%m%y%H%M")
        
        # CEV Reference
        if data.get("cev_reference"):
            ET.SubElement(ref_ttn_val, "ReferenceCEV").text = data["cev_reference"]
    
    def _add_signature(self, root: ET.Element, signature_data: Dict = None):
        """Ajoute la signature électronique XAdES."""
        # Signature fournisseur
        sig_frs = ET.SubElement(root, "ds:Signature", {
            "xmlns:ds": "http://www.w3.org/2000/09/xmldsig#",
            "Id": "SigFrs"
        })
        
        # SignedInfo
        signed_info = ET.SubElement(sig_frs, "ds:SignedInfo")
        ET.SubElement(signed_info, "ds:CanonicalizationMethod", 
                     Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
        ET.SubElement(signed_info, "ds:SignatureMethod", 
                     Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")
        
        # Reference
        reference = ET.SubElement(signed_info, "ds:Reference", Id="r-id-frs", Type="", URI="")
        transforms = ET.SubElement(reference, "ds:Transforms")
        
        transform1 = ET.SubElement(transforms, "ds:Transform", 
                                 Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116")
        ET.SubElement(transform1, "ds:XPath").text = "not(ancestor-or-self::ds:Signature)"
        
        transform2 = ET.SubElement(transforms, "ds:Transform",
                                 Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116")
        ET.SubElement(transform2, "ds:XPath").text = "not(ancestor-or-self::RefTtnVal)"
        
        ET.SubElement(transforms, "ds:Transform",
                     Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
        
        ET.SubElement(reference, "ds:DigestMethod",
                     Algorithm="http://www.w3.org/2001/04/xmlenc#sha256")
        ET.SubElement(reference, "ds:DigestValue").text = signature_data.get("digest_value", "")
        
        # SignatureValue
        signature_value = ET.SubElement(sig_frs, "ds:SignatureValue", Id="value-SigFrs")
        signature_value.text = signature_data.get("signature_value", "")
        
        # KeyInfo with X509 certificates
        key_info = ET.SubElement(sig_frs, "ds:KeyInfo")
        x509_data = ET.SubElement(key_info, "ds:X509Data")
        
        for cert in signature_data.get("certificates", []):
            ET.SubElement(x509_data, "ds:X509Certificate").text = cert
            
        # XAdES Qualifying Properties
        self._add_xades_properties(sig_frs, signature_data)
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Formate joliment le XML."""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")
    
    def _add_xades_properties(self, signature_element: ET.Element, signature_data: Dict):
        """Ajoute les propriétés XAdES à la signature."""
        ds_object = ET.SubElement(signature_element, "ds:Object")
        qualifying_props = ET.SubElement(ds_object, "xades:QualifyingProperties",
            {"xmlns:xades": "http://uri.etsi.org/01903/v1.3.2#",
             "Target": "#SigFrs"})
        
        signed_props = ET.SubElement(qualifying_props, "xades:SignedProperties",
                                   Id="xades-SigFrs")
        
        # SignedSignatureProperties
        sig_props = ET.SubElement(signed_props, "xades:SignedSignatureProperties")
        
        # SigningTime
        ET.SubElement(sig_props, "xades:SigningTime").text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # SigningCertificate
        if signature_data.get("signing_certificate"):
            cert_v2 = ET.SubElement(sig_props, "xades:SigningCertificateV2")
            cert = ET.SubElement(cert_v2, "xades:Cert")
            
            cert_digest = ET.SubElement(cert, "xades:CertDigest")
            ET.SubElement(cert_digest, "ds:DigestMethod",
                         Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
            ET.SubElement(cert_digest, "ds:DigestValue").text = signature_data["signing_certificate"].get("digest", "")
            
            ET.SubElement(cert, "xades:IssuerSerialV2").text = signature_data["signing_certificate"].get("issuer_serial", "")
        
        # SignaturePolicyIdentifier
        policy = ET.SubElement(sig_props, "xades:SignaturePolicyIdentifier")
        policy_id = ET.SubElement(policy, "xades:SignaturePolicyId")
        
        sig_policy_id = ET.SubElement(policy_id, "xades:SigPolicyId")
        ET.SubElement(sig_policy_id, "xades:Identifier", Qualifier="OIDasURN").text = "urn:2.16.788.1.2.1"
        ET.SubElement(sig_policy_id, "xades:Description").text = "Politique de signature de la facture electronique"
        
        # SignerRole
        signer_role = ET.SubElement(sig_props, "xades:SignerRoleV2")
        claimed_roles = ET.SubElement(signer_role, "xades:ClaimedRoles")
        ET.SubElement(claimed_roles, "xades:ClaimedRole").text = signature_data.get("signer_role", "CEO")
        
        # SignedDataObjectProperties
        data_props = ET.SubElement(signed_props, "xades:SignedDataObjectProperties")
        data_format = ET.SubElement(data_props, "xades:DataObjectFormat", ObjectReference="#r-id-frs")
        ET.SubElement(data_format, "xades:MimeType").text = "application/octet-stream"

    def validate_data(self, invoice_data: Dict) -> List[str]:
        """
        Valide les données avant génération XML.
        
        Returns:
            Liste des erreurs de validation (vide si OK)
        """
        errors = []
        
        # Vérifications obligatoires
        required_fields = {
            "invoice_number": "Numéro de facture",
            "invoice_date": "Date de facture",
            "sender.identifier": "Identifiant du fournisseur",
            "sender.name": "Nom du fournisseur",
            "receiver.identifier": "Identifiant du client",
            "receiver.name": "Nom du client",
            "items": "Articles",
            "total_amount": "Montant total",
            "amount_ht": "Montant HT",
            "tva_amount": "Montant TVA"
        }
        
        for field, label in required_fields.items():
            parts = field.split('.')
            value = invoice_data
            for part in parts:
                value = value.get(part, {}) if part != parts[-1] else value.get(part)
            
            if not value:
                errors.append(f"{label} manquant")
            elif field == "total_amount" and float(value) <= 0:
                errors.append(f"{label} invalide")
                
        # Vérification des articles
        if invoice_data.get("items"):
            for i, item in enumerate(invoice_data["items"], 1):
                if not item.get("code"):
                    errors.append(f"Code article manquant - ligne {i}")
                if not item.get("description"):
                    errors.append(f"Description article manquante - ligne {i}")
                if not item.get("quantity"):
                    errors.append(f"Quantité manquante - ligne {i}")
                if item.get("amount_ht", 0) <= 0:
                    errors.append(f"Montant HT invalide - ligne {i}")
        
        return errors
