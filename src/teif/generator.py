import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
from xml.dom import minidom
import re

# Import des modules de section
from .sections import (
    # En-tête et identification
    create_header_element,
    create_bgm_element,
    create_dtm_element,
    HeaderSection,
    
    # Partenaires
    create_partner_section,
    add_seller_party,
    add_buyer_party,
    PartnerSection,
    
    # Montants et taxes
    create_amount_element,
    create_tax_amount,
    create_adjustment,
    create_invoice_totals,
    
    # Paiements
    add_payment_terms,
    
    # Références
    create_reference,
    add_ttn_reference,
    add_document_reference,
    
    # Signature
    create_signature,
    add_signature,
    SignatureError,
    
    # Lignes de facture
    LinSection,
    LinItem,
    ItemDescription,
    Quantity,
    
    # Taxes
    add_tax_detail,
    add_invoice_tax_section
)
class TEIFGenerator:
    """Générateur de documents XML conformes à la norme TEIF 1.8.8."""
    
    def __init__(self, logging_level=logging.INFO):
        """Initialise le générateur TEIF avec les paramètres par défaut."""
       
        self.ns = {
            '': 'http://www.tn.gov/teif',
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        self.schema_location = "http://www.tn.gov/teif TEIF.xsd"
        self.version = "1.8.8"
        self.controlling_agency = "TTN"

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)
        
        # Create console handler and set level
        ch = logging.StreamHandler()
        ch.setLevel(logging_level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add handler to logger
        if not self.logger.handlers:
            self.logger.addHandler(ch)
   

    def generate_teif_xml(self, data: Dict[str, Any]) -> str:
        """
        Generate TEIF XML from the provided data.
        
        Args:
            data: Dictionary containing invoice data
            
        Returns:
            str: Generated XML as a string
        """
        try:
            # Create the root element with proper namespaces
            ns_map = {
                None: "http://www.tn.gov/teif",
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'schemaLocation': 'http://www.tn.gov/teif TEIF_1.8.8.xsd'
            }
            
            root = ET.Element("TEIF", nsmap=ns_map)
            root.set("version", data.get('version', '1.8.8'))
            
            # Create the header section
            header = ET.SubElement(root, "Header")
            self._add_header(header, data)
            
            # Create the body section
            body = ET.SubElement(root, "Body")
            
            # Add BGM (Beginning of Message)
            if 'bgm' in data:
                self._add_bgm_section(body, data['bgm'])
            
            # Add dates
            if 'dates' in data and data['dates']:
                self._add_dates(body, data['dates'])
            
            # Add partners
            if 'partners' in data and data['partners']:
                self._add_partners(body, data['partners'])
            
            # Add payment terms
            if 'payment_terms' in data and data['payment_terms']:
                self._add_payment_terms(body, data['payment_terms'])
            
            # Add line items
            if 'lines' in data and data['lines']:
                self._add_line_items(body, data)
            
            # Add invoice totals
            if 'totals' in data:
                self._add_invoice_totals(body, data['totals'])
            
            # Add tax totals
            if 'tax_totals' in data:
                self._add_tax_totals(body, data['tax_totals'])
            
            # Add legal monetary totals
            if 'monetary_totals' in data:
                self._add_legal_monetary_totals(body, data['monetary_totals'])
            
            # Add signature if present
            if 'signature' in data:
                self._add_signature(body, data['signature'])
            
            # Generate the XML string
            rough_string = ET.tostring(root, encoding='utf-8')
            
            # Pretty print the XML
            try:
                # Parse the XML and pretty print it
                reparsed = minidom.parseString(rough_string)
                pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
                
                # Remove the XML declaration added by toprettyxml
                pretty_xml = pretty_xml[pretty_xml.find('?>') + 2:].lstrip()
                
                # Return with our own XML declaration
                return '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml
                
            except Exception as e:
                # In case of formatting error, return unformatted XML with a warning
                self.logger.warning(f"Error formatting XML: {str(e)}")
                return '<?xml version="1.0" encoding="UTF-8"?>\n' + rough_string.decode('utf-8')
                
        except Exception as e:
            raise ET.ParseError(f"Error generating XML: {str(e)}")

    def _add_invoice_header(self, parent: ET.Element, data: Dict[str, Any]):
        """
        Ajoute l'en-tête de la facture avec les identifiants de l'émetteur et du destinataire.
        """
        header = ET.SubElement(parent, "InvoiceHeader")
        
        # Ajouter l'identifiant de l'émetteur
        if 'sender_identifier' in data.get('header', {}):
            sender = ET.SubElement(header, "MessageSenderIdentifier", {"type": "I-01"})
            sender.text = data['header']['sender_identifier']
            
        # Ajouter l'identifiant du destinataire
        if 'receiver_identifier' in data.get('header', {}):
            receiver = ET.SubElement(header, "MessageReceiverIdentifier", {"type": "I-01"})
            receiver.text = data['header']['receiver_identifier']

    def _add_invoice_moa_section(self, parent: ET.Element, moa_data: Dict[str, Any]) -> None:
        """
        Ajoute la section InvoiceMoa pour les montants de la facture.
        
        Args:
            parent: L'élément parent XML
            moa_data: Dictionnaire contenant les montants de la facture
        """
        # Utilisation directe de create_amount_element importé au niveau du module
        invoice_moa = ET.SubElement(parent, "InvoiceMoa")
        
        # Montant principal de la facture
        if 'amount' in moa_data:
            create_amount_element(invoice_moa, {
                'amount': moa_data['amount'],
                'currency': moa_data.get('currency', 'TND'),
                'format': 3
            })
        
        # Références et dates associées
        if 'references' in moa_data:
            for ref in moa_data['references']:
                rff = ET.SubElement(invoice_moa, "RffDtm")
                ET.SubElement(rff, "Reference").text = ref.get('reference', '')
                if 'date' in ref:
                    ET.SubElement(rff, "ReferenceDate").text = ref['date']

    def _add_invoice_alc_section(self, parent: ET.Element, alc_data: Dict[str, Any]) -> None:
        """
        Ajoute la section InvoiceAlc pour les allocations et suppléments de facture.
        
        Args:
            parent: L'élément parent XML
            alc_data: Dictionnaire contenant les informations d'allocation/supplément avec les clés:
                - type: Type d'allocation ('I-130' pour allocation, 'I-140' pour supplément)
                - description: Description de l'allocation/supplément
                - amount: Montant de l'allocation/supplément (obligatoire)
                - currency: Code devise (optionnel, défaut: 'TND')
                - rate: Taux de l'allocation en pourcentage (optionnel)
                - tax_included: Booléen indiquant si le montant est TTC (optionnel)
                - tax_amount: Montant de la taxe si tax_included est True (optionnel)
                - tax_rate: Taux de TVA (optionnel)
                - reason_code: Code de raison (optionnel)
                - reason: Description de la raison (optionnel)
                - references: Liste de références (optionnel)
        
        Raises:
            ValueError: Si les données requises sont manquantes ou invalides
        """
        # Validation des données requises
        if 'amount' not in alc_data:
            raise ValueError("Le montant de l'allocation/supplément est requis")
        # Convertir le montant en float si nécessaire
        try:
            amount = float(alc_data['amount'])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Format de montant d'allocation/supplément invalide: {str(e)}")
        
        # Créer l'élément InvoiceAlc
        invoice_alc = ET.SubElement(parent, "InvoiceAlc")
        
        # Préparer les données pour create_adjustment
        adjustment_data = {
            'type': alc_data.get('type', 'I-130'),
            'description': alc_data.get('description', ''),
            'amount': amount,
            'currency': alc_data.get('currency', 'TND'),
            'format': 3
        }
        
        # Ajouter le taux si spécifié
        if 'rate' in alc_data:
            try:
                adjustment_data['rate'] = float(alc_data['rate'])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Format de taux d'allocation/supplément invalide: {str(e)}")
        
        # Ajouter les informations de taxe si nécessaire
        if alc_data.get('tax_included', False) and 'tax_amount' in alc_data:
            try:
                tax_amount = float(alc_data['tax_amount'])
                amount_ht = amount - tax_amount
                
                adjustment_data.update({
                    'tax_included': True,
                    'tax_amount': tax_amount,
                    'amount_ht': amount_ht
                })
            except (ValueError, TypeError) as e:
                raise ValueError(f"Format de montant de taxe invalide: {str(e)}")
        
        # Utilisation de la fonction create_adjustment du module amounts
        create_adjustment(parent=invoice_alc, adjustment_data=adjustment_data)
        
        # Ajouter la raison si elle est spécifiée
        if 'reason_code' in alc_data or 'reason' in alc_data:
            reason_elem = ET.SubElement(invoice_alc, "AllowanceOrChargeReason")
            if 'reason_code' in alc_data:
                ET.SubElement(
                    reason_elem,
                    "AllowanceOrChargeReasonCode",
                    code=str(alc_data['reason_code'])
                )
            if 'reason' in alc_data:
                ET.SubElement(reason_elem, "AllowanceOrChargeReason").text = str(alc_data['reason'])
        
        # Taux de TVA (optionnel)
        if 'tax_rate' in alc_data:
            try:
                tax_elem = ET.SubElement(invoice_alc, "Tax")
                ET.SubElement(tax_elem, "TaxRate").text = str(float(alc_data['tax_rate']))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Format de taux de TVA invalide: {str(e)}")
            
        # Références de l'allocation
        if 'references' in alc_data and isinstance(alc_data['references'], list):
            for ref in alc_data['references']:
                if not isinstance(ref, dict):
                    continue
                rff = ET.SubElement(invoice_alc, "Rff")
                if 'reference' in ref:
                    ET.SubElement(rff, "Reference").text = str(ref['reference'])
                if 'type' in ref:
                    ET.SubElement(rff, "ReferenceType").text = str(ref['type'])

    def _add_invoice_tax_section(self, parent: ET.Element, tax_data: Dict[str, Any]) -> None:
        """
        Ajoute la section InvoiceTax pour les taxes de la facture.
        
        Args:
            parent: L'élément parent XML
            tax_data: Dictionnaire contenant les informations de taxe
        """
        from .sections.amounts import create_tax_amount
        
        # Utilisation de la fonction du module amounts pour gérer la création de la taxe
        create_tax_amount(parent, {
            'code': tax_data.get('code', 'I-1602'),
            'type': tax_data.get('name', 'TVA'),
            'rate': tax_data.get('rate', 0),
            'amount': tax_data.get('amount'),
            'currency': tax_data.get('currency', 'TND')
        })

    # La méthode _add_partner_section a été remplacée par un appel direct à create_partner_section

    def _add_nad_section(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """Ajoute une section NAD (Name and Address)."""
        nad = ET.SubElement(parent, "Nad")
        ET.SubElement(nad, "PartyIdentifier").text = data.get('id', '')
        ET.SubElement(nad, "PartyName").text = data.get('name', '')
        
        if 'address' in data:
            addr = data['address']
            address = ET.SubElement(nad, "Address")
            ET.SubElement(address, "StreetName").text = addr.get('street', '')
            ET.SubElement(address, "CityName").text = addr.get('city', '')
            ET.SubElement(address, "PostalZone").text = addr.get('postal_code', '')
            ET.SubElement(address, "Country").text = addr.get('country', 'TN')

    def _add_loc_section(self, parent: ET.Element, loc_data: Dict[str, Any]) -> None:
        """Ajoute une section LOC (Location)."""
        loc = ET.SubElement(parent, "Loc")
        ET.SubElement(loc, "LocationIdentifier").text = loc_data.get('id', '')
        ET.SubElement(loc, "LocationName").text = loc_data.get('name', '')

    def _add_rff_section(self, parent: ET.Element, ref_data: Dict[str, Any]) -> None:
        """Ajoute une section RFF (Reference)."""
        rff = ET.SubElement(parent, "Rff")
        ET.SubElement(rff, "Reference").text = ref_data.get('reference', '')
        if 'date' in ref_data:
            ET.SubElement(rff, "ReferenceDate").text = ref_data['date']

    def _add_cta_section(self, parent: ET.Element, contact_data: Dict[str, Any]) -> None:
        """Ajoute une section CTA (Contact)."""
        cta = ET.SubElement(parent, "Cta")
        contact = ET.SubElement(cta, "Contact")
        ET.SubElement(contact, "Name").text = contact_data.get('name', '')
        
        if 'communications' in contact_data:
            for comm in contact_data['communications']:
                comm_elem = ET.SubElement(contact, "Communication")
                ET.SubElement(comm_elem, "Type").text = comm.get('type', '')
                ET.SubElement(comm_elem, "Value").text = comm.get('value', '')

    def _add_bgm_section(self, parent: ET.Element, data: Dict[str, Any]):
        """
        Ajoute la section BGM (Beginning of message).
        
        Args:
            parent: L'élément parent XML
            data: Dictionnaire contenant les données BGM
                - document_number: Numéro du document (obligatoire)
                - document_type: Code du type de document (optionnel, défaut: 'I-11')
                - document_type_label: Libellé du type de document (optionnel, défaut: 'Facture')
        """
        if not isinstance(data, dict):
            data = {}
            
        # Créer l'élément BGM
        bgm = ET.SubElement(parent, "Bgm")
        
        # Ajouter le numéro de document (obligatoire)
        doc_number = data.get('document_number')
        if not doc_number:
            doc_number = f"FACT-{datetime.now().strftime('%Y%m%d%H%M')}"
            
        doc_id = ET.SubElement(bgm, "DocumentIdentifier")
        doc_id.text = doc_number
        
        # Ajouter le type de document avec code et libellé
        doc_type = ET.SubElement(bgm, "DocumentType", {
            'code': data.get('document_type', 'I-11')  # I-11 = Facture
        })
        doc_type.text = data.get('document_type_label', 'Facture')
        
        # Ajouter les références si présentes
        if 'references' in data and data['references']:
            self._add_references(bgm, data['references'])

    def _add_date_section(self, parent: ET.Element, dates_data: List[Dict[str, Any]]):
        """Ajoute la section des dates avec le format spécifié et validation.
        
        Args:
            parent: L'élément parent XML
            dates_data: Liste de dictionnaires contenant:
                - date_text: La valeur de la date (obligatoire)
                - function_code: Code de fonction de la date (obligatoire, ex: 'I-31' pour date d'émission)
                - format: Format de la date (obligatoire, ex: 'ddMMyy')
        """
        # Créer l'élément Dtm
        dtm = ET.SubElement(parent, "Dtm")
        
        # Ajouter chaque date
        for date_info in dates_data:
            # Valider les champs obligatoires
            if not all(k in date_info for k in ['date_text', 'function_code', 'format']):
                continue
                
            # Créer l'élément DateText avec les attributs
            date_elem = ET.SubElement(dtm, "DateText", {
                'functionCode': str(date_info['function_code']),
                'format': str(date_info['format'])
            })
            date_elem.text = str(date_info['date_text'])

    def _format_date_range(self, date_range: str) -> str:
        """Formate une plage de dates au format ddMMyy-ddMMyy."""
        if not date_range or '-' not in date_range:
            return str(date_range)
            
        start, end = date_range.split('-', 1)
        return f"{self._format_single_date(start)}-{self._format_single_date(end)}"

    def _add_payment_terms(self, parent: ET.Element, payment_terms_data: Dict[str, Any]) -> None:
        """
        Add payment terms section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            payment_terms_data: Dictionary containing payment terms information with keys:
                - type: Type of payment terms (e.g., 'I-10' for payment on receipt)
                - description: Description of payment terms (optional)
                - due_date: Payment due date (optional)
                - discount_percent: Discount percentage for early payment (optional)
                - discount_due_date: Due date to qualify for discount (optional)
        """
        if not payment_terms_data:
            return
            
        payment_terms = ET.SubElement(parent, "PaymentTerms")
        
        # Add payment terms type if provided
        if 'type' in payment_terms_data:
            ET.SubElement(payment_terms, "Type").text = str(payment_terms_data['type'])
        
        # Add description if provided
        if 'description' in payment_terms_data:
            ET.SubElement(payment_terms, "Description").text = str(payment_terms_data['description'])
        
        # Add due date if provided
        if 'due_date' in payment_terms_data:
            due_date = payment_terms_data['due_date']
            due_date_elem = ET.SubElement(payment_terms, "DueDate")
            due_date_elem.text = str(due_date['date'])
            
            # Add date format if provided
            if 'format' in due_date:
                due_date_elem.set("format", due_date['format'])
        
        # Add discount information if provided
        if 'discount_percent' in payment_terms_data or 'discount_due_date' in payment_terms_data:
            discount_elem = ET.SubElement(payment_terms, "Discount")
            
            if 'discount_percent' in payment_terms_data:
                ET.SubElement(discount_elem, "Percentage").text = str(payment_terms_data['discount_percent'])
            
            if 'discount_due_date' in payment_terms_data:
                discount_due = payment_terms_data['discount_due_date']
                discount_due_elem = ET.SubElement(discount_elem, "DueDate")
                discount_due_elem.text = str(discount_due['date'])
                
                # Add date format if provided
                if 'format' in discount_due:
                    discount_due_elem.set("format", discount_due['format'])

    def _add_pyt_section(self, parent: ET.Element, term_data: Dict[str, Any]):
        """Ajoute une section Pyt avec les termes de paiement."""
        pyt = ET.SubElement(parent, "Pyt")
        
        # Code du type de conditions de paiement (obligatoire)
        if 'code' in term_data:
            code_elem = ET.SubElement(pyt, "PaymentTearmsTypeCode")
            code_elem.text = str(term_data['code'])
        
        # Description des conditions de paiement (obligatoire)
        if 'description' in term_data:
            desc_elem = ET.SubElement(pyt, "PaymentTearmsDescription")
            desc_elem.text = str(term_data['description'])
    
    def _add_pyt_fii_section(self, parent: ET.Element, fi_data: Dict[str, Any]):
        """Ajoute une section PytFii avec les informations de l'institution financière."""
        # Créer l'élément PytFii avec l'attribut functionCode
        pyt_fii = ET.SubElement(parent, "PytFii")
        if 'function_code' in fi_data:
            pyt_fii.set("functionCode", str(fi_data['function_code']))
        
        # Ajouter les informations de compte si disponibles
        if 'account' in fi_data and fi_data['account']:
            account = ET.SubElement(pyt_fii, "AccountHolder")
            
            if 'number' in fi_data['account']:
                acc_num = ET.SubElement(account, "AccountNumber")
                acc_num.text = str(fi_data['account']['number'])
            
            if 'holder' in fi_data['account']:
                owner = ET.SubElement(account, "OwnerIdentifier")
                owner.text = str(fi_data['account']['holder'])
        
        # Ajouter les informations de l'institution financière
        if 'institution' in fi_data and fi_data['institution']:
            inst = fi_data['institution']
            inst_elem = ET.SubElement(pyt_fii, "InstitutionIdentification")
            
            if 'branch_code' in inst:
                inst_elem.set("nameCode", str(inst['branch_code']))
                branch = ET.SubElement(inst_elem, "BranchIdentifier")
                branch.text = str(inst['branch_code'])
            
            if 'name' in inst:
                name = ET.SubElement(inst_elem, "InstitutionName")
                name.text = str(inst['name'])
    
    def _add_invoice_tax_section(self, parent: ET.Element, tax_data: Dict[str, Any], currency: str) -> None:
        """
        Ajoute la section des taxes de la facture selon le standard TEIF 1.8.8.
        
        Args:
            parent: L'élément parent XML (InvoiceTax)
            tax_data: Dictionnaire contenant les informations de taxe:
                - code: Code de la taxe (ex: 'I-1602' pour TVA)
                - name: Nom de la taxe (optionnel, défaut: 'TVA')
                - rate: Taux de taxe en pourcentage (obligatoire)
                - taxable_amount: Montant taxable (obligatoire)
                - amount: Montant de la taxe (obligatoire)
                - currency: Code devise (optionnel, défaut: 'TND')
                - tax_scheme: Schéma de taxe (optionnel, défaut: 'TVA')
                - tax_category: Catégorie de taxe (optionnel)
            currency: Code devise (ex: 'TND')
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        def format_amount(value):
            """Formate un montant avec 3 décimales."""
            if value is None:
                return None
            return Decimal(str(value)).quantize(
                Decimal('0.001'), 
                rounding=ROUND_HALF_UP
            )
        
        # Créer l'élément TaxTotal
        tax_total = ET.SubElement(parent, "TaxTotal")
        
        # Montant total des taxes
        tax_amount = ET.SubElement(tax_total, "TaxAmount")
        tax_amount.text = str(format_amount(tax_data.get('amount', 0)))
        tax_amount.set('currencyID', currency)
        
        # Détails de la taxe
        tax_subtotal = ET.SubElement(tax_total, "TaxSubtotal")
        
        # Montant taxable
        taxable_amount = ET.SubElement(tax_subtotal, "TaxableAmount")
        taxable_amount.text = str(format_amount(tax_data.get('taxable_amount', 0)))
        taxable_amount.set('currencyID', currency)
        
        # Montant de la taxe
        tax_amount = ET.SubElement(tax_subtotal, "TaxAmount")
        tax_amount.text = str(format_amount(tax_data.get('amount', 0)))
        tax_amount.set('currencyID', currency)
        
        # Catégorie de taxe
        tax_category = ET.SubElement(tax_subtotal, "TaxCategory")
        
        # Taux de taxe
        tax_percent = ET.SubElement(tax_category, "Percent")
        tax_percent.text = str(tax_data.get('rate', 19.0))
        
        # Schéma de taxe
        tax_scheme = ET.SubElement(tax_category, "TaxScheme")
        
        # ID du schéma de taxe
        scheme_id = ET.SubElement(tax_scheme, "ID")
        scheme_id.text = tax_data.get('tax_scheme', 'TVA')
        
        # Nom du schéma de taxe
        scheme_name = ET.SubElement(tax_scheme, "Name")
        scheme_name.text = tax_data.get('name', 'TVA')
        
        # Catégorie de taxe (optionnel)
        if 'tax_category' in tax_data:
            category_id = ET.SubElement(tax_category, "ID")
            category_id.text = tax_data['tax_category']
        
        # Type de taxe (optionnel)
        if 'type' in tax_data:
            tax_type = ET.SubElement(tax_category, "TaxType")
            tax_type.text = tax_data['type']

    def _add_tax_detail(self, parent: ET.Element, tax_data: Dict[str, Any], currency: str):
        """
        Ajoute les détails de taxe avec validation des référentiels.
        
        Args:
            parent: L'élément parent XML
            tax_data: Dictionnaire contenant les données de taxe
                - code: Code du type de taxe (ex: 'I-1602' pour TVA)
                - type: Type de taxe (optionnel, défaut: 'TVA')
                - rate: Taux de taxe (obligatoire, ex: 19.0)
                - taxable_amount: Montant taxable (obligatoire)
                - amount: Montant de la taxe (obligatoire)
            currency: Code devise (ex: 'TND')
        """
        from .sections.amounts import create_tax_amount
        from .referentials import validate_tax_type, get_tax_type_description
        
        # Préparer les données pour create_tax_amount
        tax_info = {
            'code': tax_data.get('type', 'I-1602'),
            'type': tax_data.get('name', 'TVA'),
            'rate': float(tax_data.get('rate', 19.0)),
            'amount': float(tax_data.get('amount', 0)),
            'currency': currency,
            'taxable_amount': float(tax_data.get('taxable_amount', 0))
        }
        
        # Utiliser la fonction du module amounts pour créer la taxe
        create_tax_amount(parent, tax_info)

    def _add_additional_documents(self, parent: ET.Element, docs: List[Dict[str, Any]]):
        """
        Ajoute des documents annexes avec validation des types.
        
        Args:
            parent: L'élément parent XML
            docs: Liste de dictionnaires contenant les informations des documents
                - id: Identifiant du document (obligatoire)
                - name: Nom du document
                - type: Type de document (optionnel, ex: 'I-201' pour Facture)
                - date: Date du document au format DDMMYY
                - description: Description supplémentaire (optionnelle)
        """
        from .referentials import validate_document_type, get_document_type_description
        
        if not docs:
            return
            
        docs_section = ET.SubElement(parent, "AdditionnalDocuments")
        
        for doc in docs:
            if not doc or 'id' not in doc:
                continue
                
            doc_elem = ET.SubElement(docs_section, "AdditionnalDocument")
            
            # Identifiant du document (M)
            ET.SubElement(doc_elem, "AdditionnalDocumentIdentifier").text = str(doc['id'])
            
            # Nom du document (C)
            if 'name' in doc:
                ET.SubElement(doc_elem, "AdditionnalDocumentName").text = str(doc['name'])
            
            # Type de document (C) avec validation
            if 'type' in doc:
                doc_type = str(doc['type'])
                type_elem = ET.SubElement(doc_elem, "AdditionnalDocumentTypeCode")
                type_elem.text = doc_type
                
                # Ajouter la description si le type est valide
                if validate_document_type(doc_type):
                    type_elem.set('description', get_document_type_description(doc_type))
            
            # Date du document (C)
            if 'date' in doc:
                date_elem = ET.SubElement(doc_elem, "AdditionnalDocumentDate")
                ET.SubElement(date_elem, "DateText", format="DDMMYY").text = str(doc['date'])
                
            # Description supplémentaire (C)
            if 'description' in doc:
                ET.SubElement(doc_elem, "AdditionnalDocumentDescription").text = str(doc['description'])

    def _add_ttn_reference(self, parent: ET.Element, ref_data: Dict[str, str]):
        """
        Ajoute la référence TTN avec QR code et validation des types de référence.
        
        Args:
            parent: L'élément parent XML
            ref_data: Dictionnaire contenant les données de référence
                - number: Numéro de référence (obligatoire)
                - type: Type de référence (optionnel, défaut: 'TTNREF')
                - date: Date de référence au format DDMMYY (optionnel)
                - qr_code: Code QR encodé en base64 (optionnel)
        """
        from .referentials import validate_reference_type, get_reference_type_description
        
        if not ref_data or 'number' not in ref_data:
            return
            
        ref = ET.SubElement(parent, "RefTtnVal")
        
        # Type de référence (M) avec validation
        ref_type = ref_data.get('type', 'TTNREF')
        ref_elem = ET.SubElement(ref, "Reference", refID=ref_type)
        
        # Ajouter la description si le type est valide
        if validate_reference_type(ref_type):
            ref_elem.set('description', get_reference_type_description(ref_type))
            
        # Numéro de référence (M)
        ref_elem.text = str(ref_data['number'])
        
        # Date de référence (C)
        if 'date' in ref_data:
            date_elem = ET.SubElement(ref, "ReferenceDate")
            ET.SubElement(date_elem, "DateText", format="DDMMYY").text = str(ref_data['date'])
        
        # QR Code (C) - doit être encodé en base64
        if 'qr_code' in ref_data:
            qr_elem = ET.SubElement(ref, "ReferenceCev", format="QR-CODE")
            qr_elem.text = str(ref_data['qr_code'])
            
        # Version du standard (C)
        ET.SubElement(ref, "StandardVersion").text = "1.8.8"

    def _add_special_conditions(self, parent: ET.Element, conditions: Union[str, List[Union[str, Dict[str, str]]]]):
        """
        Ajoute les conditions spéciales à la facture avec validation des codes de langue.
        
        Args:
            parent: L'élément parent XML
            conditions: Peut être:
                - Une chaîne de caractères (condition unique en français)
                - Une liste de chaînes (plusieurs conditions en français)
                - Une liste de dictionnaires avec 'text' et 'language'
        """
        from .referentials import validate_language_code, DEFAULT_LANGUAGE
        
        if not conditions:
            return
            
        # Créer la section des conditions spéciales
        cond_section = ET.SubElement(parent, "SpecialConditions")
        
        # Gérer le cas d'une chaîne unique
        if isinstance(conditions, str):
            ET.SubElement(cond_section, "SpecialCondition", 
                         lang=DEFAULT_LANGUAGE).text = conditions.strip()
            return
            
        # Vérifier que c'est une liste
        if not isinstance(conditions, list):
            return
            
        # Traiter chaque condition
        for cond in conditions:
            if not cond:
                continue
                
            # Cas d'une chaîne simple
            if isinstance(cond, str):
                ET.SubElement(cond_section, "SpecialCondition", 
                             lang=DEFAULT_LANGUAGE).text = cond.strip()
                
            # Cas d'un dictionnaire avec langue et texte
            elif isinstance(cond, dict) and 'text' in cond:
                lang = str(cond.get('language', DEFAULT_LANGUAGE))
                # Valider le code de langue
                if not validate_language_code(lang):
                    lang = DEFAULT_LANGUAGE
                    
                ET.SubElement(cond_section, "SpecialCondition", 
                             lang=lang).text = str(cond['text']).strip()

            
    def _add_signature(self, parent: ET.Element, sig_data: Dict[str, Any]) -> None:
        """
        Ajoute une signature électronique XAdES-B conforme au standard TTN 1.8.8.
        
        Args:
            parent: L'élément parent où ajouter la signature
            sig_data: Dictionnaire contenant les données de signature
                - id: Identifiant de la signature (SigFrs, SigCEv, SigTTN)
                - x509_cert: Certificat X509 en base64 (obligatoire)
                - signing_time: Date de signature au format ISO 8601 (optionnel, par défaut maintenant)
                - signature_value: Valeur de la signature en base64 (optionnel pour génération)
                - digest_value: Valeur de hachage en base64 (optionnel pour génération)
                - signer_role: Rôle du signataire (optionnel, défaut: 'Fournisseur')
                - signature_policy: Dictionnaire de configuration de la politique de signature (optionnel)
        
        Raises:
            ValueError: Si les données de signature requises sont manquantes ou invalides
        """
        from .referentials import validate_signature_role, get_signature_role_description
        from datetime import datetime, timezone
        import base64
        import re
        
        # Validation des entrées
        if not sig_data or 'x509_cert' not in sig_data:
            raise ValueError("Les données de signature sont incomplètes. Un certificat X509 est requis.")
            
        # Nettoyer et valider l'ID de signature
        sig_id = str(sig_data.get('id', 'SigFrs')).strip()
        if not sig_id:
            sig_id = 'SigFrs'
            
        # Valider le certificat (format base64)
        cert_pem = sig_data['x509_cert'].strip()
        try:
            # Vérifier que c'est un certificat valide en base64
            base64.b64decode(cert_pem, validate=True)
        except Exception as e:
            raise ValueError(f"Le certificat fourni n'est pas un certificat X509 valide en base64: {str(e)}")
        
        # Créer l'élément Signature avec l'ID approprié
        sig = ET.SubElement(parent, f"{{{self.ns['ds']}}}Signature", Id=sig_id)
        
        # 1. SignedInfo
        signed_info = ET.SubElement(sig, f"{{{self.ns['ds']}}}SignedInfo")
        
        # 1.1 Méthode de canonicalisation (M)
        ET.SubElement(
            signed_info,
            f"{{{self.ns['ds']}}}CanonicalizationMethod",
            Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"
        )
        
        # 1.2 SignatureMethod (M)
        ET.SubElement(
            signed_info,
            f"{{{self.ns['ds']}}}SignatureMethod",
            Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
        )
        
        # 1.3 Reference pour le document (M)
        ref = ET.SubElement(
            signed_info,
            f"{{{self.ns['ds']}}}Reference",
            URI=f"#{sig_id}"
        )
        
        # 1.3.1 Transforms (M)
        transforms = ET.SubElement(ref, f"{{{self.ns['ds']}}}Transforms")
        ET.SubElement(
            transforms,
            f"{{{self.ns['ds']}}}Transform",
            Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"
        )
        
        # 1.3.2 DigestMethod (M)
        ET.SubElement(
            ref,
            f"{{{self.ns['ds']}}}DigestMethod",
            Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"
        )
        
        # 1.3.3 DigestValue (M) - Laissé vide pour le moment, sera calculé après
        digest_value = sig_data.get('digest_value', '')  # À calculer plus tard
        ET.SubElement(
            ref,
            f"{{{self.ns['ds']}}}DigestValue"
        ).text = digest_value
        
        # 1.4 Reference pour les propriétés signées (M)
        ref = ET.SubElement(
            signed_info,
            f"{{{self.ns['ds']}}}Reference",
            Type="http://uri.etsi.org/01903#SignedProperties",
            URI=f"#xades-{sig_id}"
        )
        
        # 1.4.1 Transform pour les propriétés signées (M)
        transforms = ET.SubElement(ref, f"{{{self.ns['ds']}}}Transforms")
        ET.SubElement(
            transforms,
            f"{{{self.ns['ds']}}}Transform",
            Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"
        )
        
        # 1.4.2 DigestMethod pour les propriétés signées (M)
        ET.SubElement(
            ref,
            f"{{{self.ns['ds']}}}DigestMethod",
            Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"
        )
        
        # 1.4.3 DigestValue pour les propriétés signées (M) - Laissé vide pour le moment
        ET.SubElement(
            ref,
            f"{{{self.ns['ds']}}}DigestValue"
        ).text = ""  # À calculer plus tard
        
        # 2. SignatureValue (M) - Laissé vide pour le moment, sera calculé après
        signature_value = sig_data.get('signature_value', '')  # À calculer plus tard
        ET.SubElement(
            sig,
            f"{{{self.ns['ds']}}}SignatureValue",
            Id=f"value-{sig_id}"
        ).text = signature_value
        
        # 3. KeyInfo (M)
        key_info = ET.SubElement(sig, f"{{{self.ns['ds']}}}KeyInfo")
        x509_data = ET.SubElement(key_info, f"{{{self.ns['ds']}}}X509Data")
        ET.SubElement(
            x509_data,
            f"{{{self.ns['ds']}}}X509Certificate"
        ).text = sig_data.get('x509_cert', '')
        
        # 4. Object pour les propriétés qualifiées
        obj = ET.SubElement(sig, f"{{{self.ns['ds']}}}Object")
        qual_props = ET.SubElement(
            obj,
            f"{{{self.ns['xades']}}}QualifyingProperties",
            Target=f"#{sig_id}"
        )
        
        signed_props = ET.SubElement(
            qual_props,
            f"{{{self.ns['xades']}}}SignedProperties",
            Id=f"xades-{sig_id}"
        )
        
        # 4.1 Propriétés de signature
        signed_signature_props = ET.SubElement(
            signed_props,
            f"{{{self.ns['xades']}}}SignedSignatureProperties"
        )
        
        # 4.1.1 Heure de signature
        signing_time = sig_data.get('signing_time', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
        ET.SubElement(
            signed_signature_props,
            f"{{{self.ns['xades']}}}SigningTime"
        ).text = signing_time
        
        # 4.1.2 Certificat de signature
        signing_cert = ET.SubElement(
            signed_signature_props,
            f"{{{self.ns['xades']}}}SigningCertificateV2"
        )
        cert = ET.SubElement(signing_cert, f"{{{self.ns['xades']}}}Cert")
        
        # Empreinte du certificat
        cert_digest = ET.SubElement(cert, f"{{{self.ns['xades']}}}CertDigest")
        ET.SubElement(
            cert_digest,
            f"{{{self.ns['ds']}}}DigestMethod",
            Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"
        )
        ET.SubElement(
            cert_digest,
            f"{{{self.ns['ds']}}}DigestValue"
        ).text = "Fi3/GHSQt+Xo6xqgSkTzVn96AIM="  # Valeur factice
        
        # Émetteur et numéro de série
        ET.SubElement(
            cert,
            f"{{{self.ns['xades']}}}IssuerSerialV2"
        ).text = "..."  # Valeur factice
        
        # 4.1.3 Politique de signature
        policy = ET.SubElement(
            signed_signature_props,
            f"{{{self.ns['xades']}}}SignaturePolicyIdentifier"
        )
        policy_id = ET.SubElement(policy, f"{{{self.ns['xades']}}}SigPolicyId")
        
        # Identifiant de la politique
        sig_policy_id = ET.SubElement(policy_id, f"{{{self.ns['xades']}}}Identifier",
                                      Qualifier="OIDasURN")
        sig_policy_id.text = "urn:2.16.788.1.2.1"
        
        # Hachage de la politique
        sig_policy_hash = ET.SubElement(
            policy_id,
            f"{{{self.ns['xades']}}}SigPolicyHash"
        )
        ET.SubElement(
            sig_policy_hash,
            f"{{{self.ns['ds']}}}DigestMethod",
            Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"
        )
        ET.SubElement(
            sig_policy_hash,
            f"{{{self.ns['ds']}}}DigestValue"
        ).text = "dJfuvjtlkeBfLBKUf142staW57x6LpSKGIfzWvohY3E="  # Valeur factice
        
        # 4.1.4 Rôle du signataire
        signer_role = ET.SubElement(
            signed_signature_props,
            f"{{{self.ns['xades']}}}SignerRoleV2"
        )
        claimed_roles = ET.SubElement(signer_role, f"{{{self.ns['xades']}}}ClaimedRoles")
        ET.SubElement(
            claimed_roles,
            f"{{{self.ns['xades']}}}ClaimedRole"
        ).text = sig_data.get('role', 'Fournisseur')
        
        # 4.2 Propriétés des objets de données signés
        signed_data_object_props = ET.SubElement(
            signed_props,
            f"{{{self.ns['xades']}}}SignedDataObjectProperties"
        )
        data_object_format = ET.SubElement(
            signed_data_object_props,
            f"{{{self.ns['xades']}}}DataObjectFormat",
            ObjectReference=f"#r-id-{sig_id.lower()}"
        )
        ET.SubElement(
            data_object_format,
            f"{{{self.ns['xades']}}}MimeType"
        ).text = "application/octet-stream"

    def _add_line_discount(self, parent: ET.Element, discount: Dict[str, Any], currency: str) -> None:
        """
        Ajoute une remise à une ligne de facture avec validation des données.
        
        Args:
            parent: L'élément parent (ligne de facture) auquel ajouter la remise
            discount: Dictionnaire contenant les informations de remise avec les clés:
                - amount: Montant de la remise (obligatoire)
                - type_code: Code type de remise (optionnel, défaut: 'I-172' pour Remise commerciale)
                - rate: Taux de remise en pourcentage (optionnel)
                - description: Description textuelle de la remise (optionnel)
            currency: Code devise ISO 4217 (ex: 'TND')
            
        Raises:
            ValueError: Si les données obligatoires sont manquantes ou invalides
        """
        from .sections.amounts import create_amount_element
        
        if not isinstance(discount, dict):
            raise ValueError("Le paramètre 'discount' doit être un dictionnaire")
            
        if 'amount' not in discount:
            raise ValueError("Le montant de la remise est obligatoire (clé 'amount')")
            
        if not isinstance(currency, str) or len(currency) != 3:
            raise ValueError("Le code devise doit être une chaîne de 3 caractères (ex: 'TND')")
        
        try:
            # Créer l'élément de remise
            discount_elem = ET.SubElement(parent, "Discount")
            
            # Montant de la remise (obligatoire)
            amount = float(discount['amount'])
            if amount < 0:
                raise ValueError("Le montant de la remise ne peut pas être négatif")
                
            # Utilisation de la fonction du module amounts pour créer l'élément de montant
            type_code = str(discount.get('type_code', 'I-172'))
            amount_data = {
                'amount': amount,
                'currency': currency,
                'format': 3
            }
            
            # Créer l'élément de montant avec le type de code approprié
            amount_elem = create_amount_element(discount_elem, amount_data)
            amount_elem.set('amountTypeCode', type_code)
            
            # Taux de remise (optionnel)
            if 'rate' in discount:
                rate = float(discount['rate'])
                if not (0 <= rate <= 100):
                    raise ValueError("Le taux de remise doit être compris entre 0 et 100")
                ET.SubElement(
                    discount_elem, 
                    "Rate"
                ).text = self._format_amount(rate, 2)
            
            # Description de la remise (optionnel)
            if 'description' in discount:
                description = str(discount['description']).strip()
                if description:  # Ne pas ajouter de description vide
                    ET.SubElement(
                        discount_elem, 
                        "Description"
                    ).text = description
                    
        except (ValueError, TypeError) as e:
            raise ValueError(f"Format de données de remise invalide: {str(e)}")

    def _add_line_tax(self, parent: ET.Element, tax_data: Dict[str, Any], currency: str) -> None:
        """
        Ajoute une taxe à une ligne de facture avec validation des données.
        
        Args:
            parent: L'élément parent (ligne de facture) auquel ajouter la taxe
            tax_data: Dictionnaire contenant les informations de taxe avec les clés:
                - code: Code de la taxe (optionnel, défaut: 'I-1602' pour TVA)
                - name: Nom de la taxe (optionnel, défaut: 'TVA')
                - rate: Taux de taxe en pourcentage (obligatoire)
                - taxable_amount: Montant taxable (obligatoire)
                - amount: Montant de la taxe (obligatoire)
            currency: Code devise ISO 4217 (ex: 'TND')
            
        Raises:
            ValueError: Si les données obligatoires sont manquantes ou invalides
        """
        from .sections.amounts import create_tax_amount
        from .referentials import validate_tax_type, get_tax_type_description
        
        if not isinstance(tax_data, dict):
           raise ValueError("Le paramètre 'tax_data' doit être un dictionnaire")
            
        # Vérification des champs obligatoires
        required_fields = ['rate', 'taxable_amount', 'amount']
        missing_fields = [field for field in required_fields if field not in tax_data]
        if missing_fields:
            raise ValueError(
                f"Champs de taxe manquants: {', '.join(missing_fields)}. "
                "Les champs 'rate', 'taxable_amount' et 'amount' sont obligatoires."
            )
            
        if not isinstance(currency, str) or len(currency) != 3:
            raise ValueError("Le code devise doit être une chaîne de 3 caractères (ex: 'TND')")
            
        try:
            # Validation des valeurs numériques
            rate = float(tax_data['rate'])
            taxable_amount = float(tax_data['taxable_amount'])
            amount = float(tax_data['amount'])
            
            if rate < 0 or taxable_amount < 0 or amount < 0:
                raise ValueError("Les montants et taux de taxe ne peuvent pas être négatifs")
            
            # Préparer les données pour create_tax_amount
            tax_info = {
                'code': tax_data.get('type', 'I-1602'),
                'type': tax_data.get('name', 'TVA'),
                'rate': rate,
                'amount': amount,
                'currency': currency,
                'taxable_amount': taxable_amount
            }
            
            # Vérifier si le type de taxe est valide et ajouter la description si nécessaire
            if validate_tax_type(tax_info['code']):
                tax_info['type'] = get_tax_type_description(tax_info['code'])
            
            # Utilisation de la fonction du module amounts pour créer la taxe
            create_tax_amount(parent, tax_info)
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Format de données de taxe invalide: {str(e)}")

    def _format_amount(self, value: Any, decimals: int = 3) -> str:
        """
        Formate un montant avec le nombre de décimales spécifié.
        
        Args:
            value: Valeur numérique à formater (peut être un nombre ou une chaîne)
            decimals: Nombre de décimales à afficher (par défaut: 3)
            
        Returns:
            Chaîne formatée avec le nombre de décimales spécifié
            
        Raises:
            ValueError: Si la valeur ne peut pas être convertie en nombre
            ValueError: Si le nombre de décimales est négatif
        """
        if not isinstance(decimals, int) or decimals < 0:
            raise ValueError("Le nombre de décimales doit être un entier positif ou nul")
            
        try:
            # Convertir en float et formater avec le nombre de décimales
            num_value = float(value)
            return f"{num_value:.{decimals}f}"
        except (ValueError, TypeError) as e:
            raise ValueError(f"Impossible de formater la valeur '{value}' comme montant: {str(e)}")
    
    def _format_percentage(self, value: Any) -> str:
        """
        Formate un pourcentage avec 2 décimales.
        
        Args:
            value: Valeur à formater (peut être un nombre ou une chaîne)
            
        Returns:
            Chaîne formatée avec 2 décimales
            
        Raises:
            ValueError: Si la valeur ne peut pas être convertie en nombre
        """
        try:
            # Convertir en float, multiplier par 100 pour le pourcentage et formater
            percentage = float(value) * 100
            return self._format_amount(percentage, 2)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Impossible de formater la valeur '{value}' comme pourcentage: {str(e)}")
    
    def _format_xml(self, elem: ET.Element) -> str:
        """
        Formate le XML avec une indentation correcte et des préfixes de namespace personnalisés.
        
        Args:
            elem: L'élément XML racine à formater
            
        Returns:
            str: Chaîne XML formatée avec indentation et en-tête
            
        Raises:
            ValueError: Si l'élément racine n'est pas valide
            ET.ParseError: Si une erreur survient lors du parsing du XML
        """
        if not ET.iselement(elem):
            raise ValueError("L'élément fourni n'est pas un élément XML valide")
            
        try:
            # Enregistrer les namespaces avec les préfixes souhaités
            for prefix, uri in self.ns.items():
                if prefix:  # Ne pas enregistrer le namespace par défaut avec un préfixe
                    ET.register_namespace(prefix, uri)
            
            # Ajouter l'attribut schemaLocation si nécessaire
            if 'xsi' in self.ns and hasattr(self, 'schema_location'):
                elem.set(f"{{{self.ns['xsi']}}}schemaLocation", self.schema_location)
            
            # Générer le XML brut
            rough_string = ET.tostring(elem, 'utf-8')
            
            # Parser pour le formatage
            try:
                # Parse the XML and pretty print it
                reparsed = minidom.parseString(rough_string)
                pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
                
                # Remove the XML declaration added by toprettyxml
                pretty_xml = pretty_xml[pretty_xml.find('?>') + 2:].lstrip()
                
                # Return with our own XML declaration
                return '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml
                
            except Exception as e:
                # In case of formatting error, return unformatted XML with a warning
                self.logger.warning(f"Error formatting XML: {str(e)}")
                return '<?xml version="1.0" encoding="UTF-8"?>\n' + rough_string.decode('utf-8')
                
        except Exception as e:
            raise ET.ParseError(f"Error generating XML: {str(e)}")

    def _add_line_items(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """
        Add the line items section to the TEIF XML using the new LinSection and LinItem classes.
        
        Args:
            parent: The parent XML element
            data: Dictionary containing line items data with the following structure:
                {
                    'lines': [
                        {
                            'item_identifier': str,  # Required
                            'item_code': str,        # Required
                            'description': str,      # Required
                            'quantity': float,       # Required
                            'unit': str,             # Required (e.g., 'PCE' for pieces)
                            'unit_price': float,     # Required
                            'currency': str,         # Optional, default 'TND'
                            'taxes': [              # Optional
                                {
                                    'type_name': str,   # e.g., 'TVA'
                                    'category': str,    # e.g., 'S'
                                    'details': [
                                        {
                                            'amount': float,
                                            'rate': float,
                                            'currency': str  # Optional, default 'TND'
                                        }
                                    ]
                                }
                            ],
                            'additional_info': [     # Optional
                                {
                                    'code': str,
                                    'description': str,
                                    'lang': str      # Optional, default 'fr'
                                }
                            ]
                        }
                    ]
                }
        """
        if 'lines' not in data or not data['lines']:
            return
        
        # Create a new LinSection
        lin_section = LinSection()
        
        # Add each line item
        for i, line_data in enumerate(data['lines'], 1):
            # Create a new line item
            line_item = LinItem(line_number=i)
            
            # Set basic item information
            item_identifier = line_data.get('item_identifier', f'ITEM-{i}')
            item_code = line_data.get('item_code', item_identifier)
            description = line_data.get('description', '')
            
            line_item.set_item_info(
                item_identifier=item_identifier,
                item_code=item_code,
                description=description,
                lang=line_data.get('language', 'fr')
            )
            
            # Set quantity if available
            if 'quantity' in line_data and 'unit' in line_data:
                line_item.set_quantity(
                    value=line_data['quantity'],
                    unit=line_data['unit']
                )
            
            # Add line amount
            if 'unit_price' in line_data and 'quantity' in line_data:
                line_total = line_data['unit_price'] * line_data['quantity']
                line_item.add_amount(
                    amount=line_total,
                    currency=line_data.get('currency', 'TND'),
                    type_code='I-110'  # Line item amount
                )
                
                # Add unit price as additional amount
                line_item.add_amount(
                    amount=line_data['unit_price'],
                    currency=line_data.get('currency', 'TND'),
                    type_code='I-109'  # Unit price
                )
            
            # Add taxes if available
            for tax in line_data.get('taxes', []):
                line_item.add_tax(
                    type_name=tax.get('type_name', 'TVA'),
                    category=tax.get('category', 'S'),
                    details=tax.get('details', [])
                )
            
            # Add additional product information if available
            for info in line_data.get('additional_info', []):
                line_item.add_additional_info(
                    code=info.get('code', ''),
                    description=info.get('description', ''),
                    lang=info.get('lang', 'fr')
                )
            
            # Add the line item to the section
            lin_section.add_line(line_item)
        
        # Convert the LinSection to XML and add it to the parent
        lin_section.to_xml(parent)

    def _add_header(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """
        Add the header section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            data: Dictionary containing header data
        """
        # Add message sender identifier
        if 'sender_identifier' in data.get('header', {}):
            sender = ET.SubElement(parent, "MessageSenderIdentifier")
            sender.set("type", data['header'].get('sender_type', 'I-01'))
            sender.text = str(data['header']['sender_identifier'])
        
        # Add message receiver identifier
        if 'receiver_identifier' in data.get('header', {}):
            receiver = ET.SubElement(parent, "MessageReceiverIdentifier")
            receiver.set("type", data['header'].get('receiver_type', 'I-01'))
            receiver.text = str(data['header']['receiver_identifier'])
        
        # Add document identification
        if 'document_number' in data.get('header', {}):
            doc_id = ET.SubElement(parent, "DocumentIdentification")
            ET.SubElement(doc_id, "DocumentNumber").text = str(data['header']['document_number'])
            ET.SubElement(doc_id, "DocumentType").text = data['header'].get('document_type', 'I-11')
        
        # Add dates
        if 'dates' in data.get('header', {}):
            for date_info in data['header']['dates']:
                date_elem = ET.SubElement(parent, "Date")
                ET.SubElement(date_elem, "DateText", format=date_info.get('format', 'ddMMyy')).text = date_info['date']
                ET.SubElement(date_elem, "DateType").text = date_info.get('type', 'I-31')
        
        # Add test indicator if provided
        if 'test_indicator' in data.get('header', {}):
            ET.SubElement(parent, "TestIndicator").text = str(data['header']['test_indicator'])
        
        # Add language code if provided
        if 'language' in data.get('header', {}):
            ET.SubElement(parent, "LanguageCode").text = data['header']['language']
        
        # Add currency code if provided
        if 'currency' in data.get('header', {}):
            ET.SubElement(parent, "CurrencyCode").text = data['header']['currency']
        
        # Add sender information
        if 'sender' in data:
            sender = ET.SubElement(parent, "Sender")
            if 'identifier' in data['sender']:
                ET.SubElement(sender, "Identifier").text = str(data['sender']['identifier'])
            if 'name' in data['sender']:
                ET.SubElement(sender, "Name").text = str(data['sender']['name'])
        
        # Add receiver information
        if 'receiver' in data:
            receiver = ET.SubElement(parent, "Receiver")
            if 'identifier' in data['receiver']:
                ET.SubElement(receiver, "Identifier").text = str(data['receiver']['identifier'])
            if 'name' in data['receiver']:
                ET.SubElement(receiver, "Name").text = str(data['receiver']['name'])
        
        # Add document information
        if 'document' in data:
            doc = ET.SubElement(parent, "Document")
            if 'type' in data['document']:
                ET.SubElement(doc, "Type").text = str(data['document']['type'])
            if 'number' in data['document']:
                ET.SubElement(doc, "Number").text = str(data['document']['number'])
            if 'date' in data['document']:
                ET.SubElement(doc, "Date").text = str(data['document']['date'])

    def _add_dates(self, parent: ET.Element, dates_data: List[Dict[str, Any]]) -> None:
        """
        Add dates section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            dates_data: List of date dictionaries with keys:
                - type: Type of date (e.g., 'I-31' for issue date, 'I-35' for delivery date)
                - date: The date value in the specified format
                - format: Date format (e.g., 'ddMMyy', 'yyyyMMdd')
        """
        if not dates_data:
            return
            
        dates_section = ET.SubElement(parent, "Dates")
        
        for date_info in dates_data:
            date_elem = ET.SubElement(dates_section, "Date")
            
            # Add date type (e.g., 'I-31' for issue date)
            if 'type' in date_info:
                ET.SubElement(date_elem, "Type").text = str(date_info['type'])
                
            # Add date value
            if 'date' in date_info:
                date_value = ET.SubElement(date_elem, "Value")
                date_value.text = str(date_info['date'])
                
                # Add date format if provided
                if 'format' in date_info:
                    date_value.set("format", date_info['format'])
            
            # Add time if provided
            if 'time' in date_info:
                time_elem = ET.SubElement(date_elem, "Time")
                time_elem.text = str(date_info['time'])
                
                # Add time format if provided
                if 'time_format' in date_info:
                    time_elem.set("format", date_info['time_format'])

    def _add_tax_totals(self, parent: ET.Element, tax_totals_data: List[Dict[str, Any]]) -> None:
        """
        Add tax totals section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            tax_totals_data: List of tax total dictionaries
        """
        if not tax_totals_data:
            return
            
        tax_totals = ET.SubElement(parent, "TaxTotals")
        
        for tax_data in tax_totals_data:
            tax_total = ET.SubElement(tax_totals, "TaxTotal")
            
            if 'tax_amount' in tax_data:
                ET.SubElement(tax_total, "TaxAmount", currencyID=tax_data.get('currency', 'TND')).text = str(tax_data['tax_amount'])
                
            if 'taxable_amount' in tax_data:
                ET.SubElement(tax_total, "TaxableAmount", currencyID=tax_data.get('currency', 'TND')).text = str(tax_data['taxable_amount'])
                
            if 'tax_category' in tax_data:
                tax_category = ET.SubElement(tax_total, "TaxCategory")
                if 'id' in tax_data['tax_category']:
                    ET.SubElement(tax_category, "ID").text = str(tax_data['tax_category']['id'])
                if 'percent' in tax_data['tax_category']:
                    ET.SubElement(tax_category, "Percent").text = str(tax_data['tax_category']['percent'])

    def _add_legal_monetary_totals(self, parent: ET.Element, monetary_totals: Dict[str, Any]) -> None:
        """
        Add legal monetary totals section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            monetary_totals: Dictionary containing monetary totals
        """
        legal_monetary_totals = ET.SubElement(parent, "LegalMonetaryTotals")
        
        if 'line_extension_amount' in monetary_totals:
            ET.SubElement(
                legal_monetary_totals, 
                "LineExtensionAmount",
                currencyID=monetary_totals.get('currency', 'TND')
            ).text = str(monetary_totals['line_extension_amount'])
            
        if 'tax_exclusive_amount' in monetary_totals:
            ET.SubElement(
                legal_monetary_totals,
                "TaxExclusiveAmount",
                currencyID=monetary_totals.get('currency', 'TND')
            ).text = str(monetary_totals['tax_exclusive_amount'])
            
        if 'tax_inclusive_amount' in monetary_totals:
            ET.SubElement(
                legal_monetary_totals,
                "TaxInclusiveAmount",
                currencyID=monetary_totals.get('currency', 'TND')
            ).text = str(monetary_totals['tax_inclusive_amount'])
            
        if 'allowance_total_amount' in monetary_totals:
            ET.SubElement(
                legal_monetary_totals,
                "AllowanceTotalAmount",
                currencyID=monetary_totals.get('currency', 'TND')
            ).text = str(monetary_totals['allowance_total_amount'])
            
        if 'payable_amount' in monetary_totals:
            ET.SubElement(
                legal_monetary_totals,
                "PayableAmount",
                currencyID=monetary_totals.get('currency', 'TND')
            ).text = str(monetary_totals['payable_amount'])

    def _add_partner_section(self, parent: ET.Element, partner_data: Dict[str, Any]) -> None:
        """Add partner information (buyer/seller)"""
        # Add partner type (BY = Buyer, SE = Seller, etc.)
        partner_type = ET.SubElement(parent, "PartnerType")
        partner_type.text = partner_data.get('type', 'SE')  # Default to Seller

        # Add partner identification
        if 'identifier' in partner_data:
            identifier = ET.SubElement(parent, "Identifier")
            identifier.set("type", partner_data.get('identifier_type', 'I-01'))
            identifier.text = partner_data['identifier']

        # Add name and address if available
        if 'name' in partner_data:
            ET.SubElement(parent, "Name").text = partner_data['name']
    
        if 'address' in partner_data:
            address = ET.SubElement(parent, "Address")
            addr_data = partner_data['address']
            if 'street' in addr_data:
                ET.SubElement(address, "Street").text = addr_data['street']
            if 'city' in addr_data:
                ET.SubElement(address, "City").text = addr_data['city']
            if 'postal_code' in addr_data:
                ET.SubElement(address, "PostalCode").text = addr_data['postal_code']
            if 'country' in addr_data:
                ET.SubElement(address, "Country").text = addr_data['country']

    def _add_date_section(self, parent: ET.Element, date_data: Dict[str, Any]) -> None:
        """Add date information"""
        date_type = ET.SubElement(parent, "DateType")
        date_type.text = date_data.get('type', 'I-31')  # Default to invoice date

        date_value = ET.SubElement(parent, "DateValue")
        date_value.text = date_data.get('date', '')

        if 'format' in date_data:
            date_format = ET.SubElement(parent, "DateFormat")
            date_format.text = date_data['format']

    def _add_invoice_amount(self, parent: ET.Element, amount_data: Dict[str, Any]) -> None:
        """Add invoice monetary amount"""
        amount_type = ET.SubElement(parent, "AmountType")
        amount_type.text = amount_data.get('type', 'I-146')  # Default to invoice total amount

        amount = ET.SubElement(parent, "Amount")
        amount.set("currencyID", amount_data.get('currency', 'TND'))
        amount.text = f"{float(amount_data.get('value', 0)):.3f}"

    def _add_invoice_tax(self, parent: ET.Element, tax_data: Dict[str, Any]) -> None:
        """Add invoice tax information"""
        tax_type = ET.SubElement(parent, "TaxType")
        tax_type.text = tax_data.get('type', 'I-19')  # Default to standard VAT

        tax_amount = ET.SubElement(parent, "TaxAmount")
        tax_amount.set("currencyID", tax_data.get('currency', 'TND'))
        tax_amount.text = f"{float(tax_data.get('amount', 0)):.3f}"

        if 'rate' in tax_data:
            tax_rate = ET.SubElement(parent, "TaxRate")
            tax_rate.text = f"{float(tax_data['rate']):.2f}%"

    def _add_signature(self, parent: ET.Element, signature_data: Dict[str, Any]) -> None:
        """
        Add signature section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            signature_data: Dictionary containing signature information
        """
        signature = ET.SubElement(parent, "Signature")
        
        if 'id' in signature_data:
            signature.set("ID", str(signature_data['id']))
            
        if 'signatory_party' in signature_data:
            signatory_party = ET.SubElement(signature, "SignatoryParty")
            if 'party_identification' in signature_data['signatory_party']:
                party_identification = ET.SubElement(signatory_party, "PartyIdentification")
                ET.SubElement(party_identification, "ID").text = str(
                    signature_data['signatory_party']['party_identification']
                )
                
        if 'digital_signature_attachment' in signature_data:
            attachment = ET.SubElement(signature, "DigitalSignatureAttachment")
            external_reference = ET.SubElement(attachment, "ExternalReference")
            if 'uri' in signature_data['digital_signature_attachment']:
                external_reference.set("URI", str(signature_data['digital_signature_attachment']['uri']))

    def _add_invoice_totals(self, parent: ET.Element, totals_data: Dict[str, Any]) -> None:
        """
        Add invoice totals section to the TEIF XML.
        
        Args:
            parent: The parent XML element
            totals_data: Dictionary containing invoice totals
        """
        totals = ET.SubElement(parent, "InvoiceTotals")
        
        # Add currency code if provided
        currency = totals_data.get('currency', 'TND')
        
        # Add line extension amount (total amount before tax)
        if 'line_extension_amount' in totals_data:
            ET.SubElement(
                totals,
                "LineExtensionAmount",
                currencyID=currency
            ).text = str(totals_data['line_extension_amount'])
        
        # Add tax exclusive amount
        if 'tax_exclusive_amount' in totals_data:
            ET.SubElement(
                totals,
                "TaxExclusiveAmount",
                currencyID=currency
            ).text = str(totals_data['tax_exclusive_amount'])
        
        # Add tax inclusive amount
        if 'tax_inclusive_amount' in totals_data:
            ET.SubElement(
                totals,
                "TaxInclusiveAmount",
                currencyID=currency
            ).text = str(totals_data['tax_inclusive_amount'])
        
        # Add allowance total amount if any discounts or allowances
        if 'allowance_total_amount' in totals_data:
            ET.SubElement(
                totals,
                "AllowanceTotalAmount",
                currencyID=currency
            ).text = str(totals_data['allowance_total_amount'])
        
        # Add charge total amount if any additional charges
        if 'charge_total_amount' in totals_data:
            ET.SubElement(
                totals,
                "ChargeTotalAmount",
                currencyID=currency
            ).text = str(totals_data['charge_total_amount'])
        
        # Add prepaid amount if any prepayments
        if 'prepaid_amount' in totals_data:
            ET.SubElement(
                totals,
                "PrepaidAmount",
                currencyID=currency
            ).text = str(totals_data['prepaid_amount'])
        
        # Add payable amount (final amount to be paid)
        if 'payable_amount' in totals_data:
            ET.SubElement(
                totals,
                "PayableAmount",
                currencyID=currency
            ).text = str(totals_data['payable_amount'])

    def _format_xml(self, elem: ET.Element) -> str:
        """Format XML with proper indentation and encoding"""
        # Convert to string
        rough_string = ET.tostring(elem, 'utf-8')
    
        # Parse and pretty print
        try:
            # Parse the XML and pretty print it
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        
            # Remove the XML declaration added by toprettyxml
            pretty_xml = pretty_xml[pretty_xml.find('?>') + 2:].lstrip()
        
            # Remove extra newlines and fix indentation
            pretty_xml = re.sub(r'>\s+<', '><', pretty_xml)  # Remove whitespace between tags
            pretty_xml = re.sub(r'(\S)\n\s*<', r'\1<', pretty_xml)  # Fix line breaks
            pretty_xml = re.sub(r'(\S)\n\s*', r'\1', pretty_xml)  # Remove extra newlines
        
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml
        
        except Exception as e:
            self.logger.warning(f"Error formatting XML: {str(e)}")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + rough_string.decode('utf-8')
    

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du générateur
    generator = TEIFGenerator()
    
    # Générer le XML avec les données de la facture
    # Remplacez ceci par votre propre dictionnaire de données
    invoice_data = {
        # Structure de données de la facture
    }
    
    try:
        # Génération du XML
        xml_output = generator.generate_teif_xml(invoice_data)
        
        # Sauvegarde dans un fichier
        output_file = "facture_teif.xml"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(xml_output)
        
        print(f"Facture TEIF générée avec succès : {output_file}")
        
    except Exception as e:
        print(f"Erreur lors de la génération de la facture : {str(e)}")
        raise