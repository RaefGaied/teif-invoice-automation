import lxml.etree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging
import re
import os
from decimal import Decimal

# Import local modules
from .sections.header import create_teif_root, create_bgm_element
from .sections.signature import SignatureSection
from .sections.partner import add_seller_party, add_buyer_party, add_delivery_party


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
            str: Generated XML as a string with proper formatting
        """
        try:
            # Create the root element
            root = create_teif_root(version=data.get('version', '1.8.8'))
            
            # Add header and body sections
            header = ET.SubElement(root, "InvoiceHeader")
            self._add_header(header, data)
            
            body = ET.SubElement(root, "InvoiceBody")
            
            # Add BGM section if document info is available
            if 'bgm' in data:
                self._add_bgm_section(body, data['bgm'])
                
            # Add dates if available
            if 'dates' in data and isinstance(data['dates'], list):
                self._add_dates(body, data['dates'])
            
            # Add partners if available
            if any(k in data for k in ['seller', 'buyer', 'delivery']):
                partners_data = {
                    'seller': data.get('seller'),
                    'buyer': data.get('buyer'),
                    'delivery': data.get('delivery')
                }
                self._add_partners(body, partners_data)
            elif 'partners' in data and data['partners']:
                self._add_partners(body, data['partners'])
            
            # Add payment terms if available
            if 'payment_terms' in data and data['payment_terms']:
                self._add_payment_terms(body, data['payment_terms'])
            
            # Add payment means if available
            if 'payment_means' in data and data['payment_means']:
                self._add_payment_means(body, data['payment_means'])
            
            # Add line items if available
            if 'lines' in data and data['lines']:
                self._add_line_items(body, data['lines'])
            
            # Add invoice totals if available
            if 'totals' in data:
                self._add_invoice_totals(body, data['totals'])
            
            # Add invoice tax section if available (must be after line items and before signature)
            if 'taxes' in data and data['taxes']:
                self._add_invoice_tax(body, data['taxes'])
            
            # Add signatures if available
            if 'signatures' in data and data['signatures']:
                signature_data = data['signatures'][0]
                
                # Add the signature if provided
                if signature_data:
                    self._add_signature(root, signature_data)
            
            # Backward compatibility: check for singular 'signature' key
            elif 'signature' in data and data['signature']:
                signature_data = data['signature']
                
                # Add the signature if provided
                if signature_data:
                    self._add_signature(root, signature_data)
            
            # Use our XML serialization utility
            from .utils.xml_utils import serialize_xml
            return serialize_xml(root)
            
        except Exception as e:
            self.logger.error(f"Error generating TEIF XML: {str(e)}")
            raise

    def _add_header(self, parent: ET.Element, data: Dict[str, Any]) -> None:
        """
        Add header section to the XML using TEIF 1.8.8 specification.
        
        Args:
            parent: Parent XML element (should be the root TEIF element)
            data: Dictionary containing header data
        """
        try:
            # Extract header data with fallback to root level for backward compatibility
            header_data = data.get('header', {})
            
            # Create InvoiceHeader element
            invoice_header = parent
            
            # Add MessageSenderIdentifier (required)
            sender_id = header_data.get('sender_identifier', data.get('sender_identifier', ''))
            if sender_id:
                sender_elem = ET.SubElement(invoice_header, 'MessageSenderIdentifier', type='I-01')
                sender_elem.text = str(sender_id)
            
            # Add MessageRecipientIdentifier (if available)
            receiver_id = header_data.get('receiver_identifier', data.get('receiver_identifier'))
            if receiver_id:
                receiver_elem = ET.SubElement(invoice_header, 'MessageRecipientIdentifier', 
                                           type=header_data.get('receiver_identifier_type', 'I-01'))
                receiver_elem.text = str(receiver_id)
            
            # Add CreationDateTime (current timestamp if not provided)
            creation_time = header_data.get('creation_datetime', datetime.utcnow().strftime('%Y%m%d%H%M%S'))
            ET.SubElement(invoice_header, 'CreationDateTime').text = creation_time
            
            # Add other optional header fields if provided
            if 'message_identifier' in header_data:
                ET.SubElement(invoice_header, 'MessageIdentifier').text = str(header_data['message_identifier'])
                
            if 'document_currency_code' in header_data:
                ET.SubElement(invoice_header, 'DocumentCurrencyCode').text = str(header_data['document_currency_code'])
            
        except Exception as e:
            self.logger.error(f"Error adding header section: {str(e)}")
            raise

    def _add_bgm_section(self, parent: ET.Element, bgm_data: Dict[str, Any]) -> None:
        """Add BGM (Beginning of Message) section."""
        try:
            from .sections.header import create_bgm_element
            create_bgm_element(parent, bgm_data)
        except Exception as e:
            self.logger.error(f"Error adding BGM section: {str(e)}")
            raise

    def _add_dates(self, parent: ET.Element, dates_data: List[Dict[str, Any]]) -> None:
        """Add date elements to the document under a single Dtm element."""
        try:
            if not dates_data:
                return
            
            # Create or find the Dtm element
            dtm = parent.find('Dtm')
            if dtm is None:
                dtm = ET.SubElement(parent, 'Dtm')
            
            # Add all dates to the single Dtm element
            for date_item in dates_data:
                if all(k in date_item for k in ['date_text', 'function_code', 'format']):
                    ET.SubElement(dtm, 'DateText',
                                format=date_item['format'],
                                functionCode=date_item['function_code']).text = date_item['date_text']
                            
        except Exception as e:
            self.logger.error(f"Error adding dates: {str(e)}")
            raise

    def _add_partners(self, parent: ET.Element, partners_data: Dict[str, Any]) -> None:
        """Add partner sections (seller, buyer, delivery)."""
        if not partners_data:
            self.logger.warning("No partners data provided")
            return
            
        try:
            # Add seller if exists and is not None
            if partners_data.get('seller'):
                add_seller_party(parent, partners_data['seller'])
            
            # Add buyer if exists and is not None
            if partners_data.get('buyer'):
                add_buyer_party(parent, partners_data['buyer'])
            
            # Add delivery party if exists and is not None
            if partners_data.get('delivery'):
                add_delivery_party(parent, partners_data['delivery'])
                
        except Exception as e:
            self.logger.error(f"Error adding partners: {str(e)}")
            raise

    def _add_payment_terms(self, parent: ET.Element, payment_terms_data: Dict[str, Any]) -> None:
        """
        Add payment terms section.
        
        Args:
            parent: Parent XML element
            payment_terms_data: Dictionary containing payment terms data
                - description: Payment terms description (required)
                - code: Payment type code (optional, e.g., 'I-10')
                - due_date: Due date (optional)
                - discount_percent: Discount percentage (optional)
                - discount_due_date: Discount due date (optional)
        """
        try:
            from .sections.payment import add_payment_terms
            add_payment_terms(parent, payment_terms_data)
        except Exception as e:
            self.logger.error(f"Error adding payment terms: {str(e)}")
            raise

    def _add_payment_means(self, parent: ET.Element, payment_means_data: Dict[str, Any]) -> None:
        """
        Add payment means section.
        
        Args:
            parent: Parent XML element
            payment_means_data: Dictionary containing payment means data
                - payment_means_code: Code du moyen de paiement (ex: 'I-30' pour virement)
                - payment_id: Identifiant du paiement (ex: numéro de virement)
                - due_date: Date d'échéance du paiement (format YYYY-MM-DD)
                - payee_financial_account: Dictionnaire contenant les informations du compte
                    - iban: Numéro IBAN du compte
                    - account_holder: Nom du titulaire du compte
                    - financial_institution: Nom de l'institution financière
                    - branch_code: Code de l'agence (optionnel)
        """
        try:
            # Créer la section PytSection si elle n'existe pas
            pyt_section = parent.find('PytSection')
            if pyt_section is None:
                pyt_section = ET.SubElement(parent, 'PytSection')
                pyt_section_details = ET.SubElement(pyt_section, 'PytSectionDetails')
            else:
                pyt_section_details = pyt_section.find('PytSectionDetails')
                if pyt_section_details is None:
                    pyt_section_details = ET.SubElement(pyt_section, 'PytSectionDetails')
            
            # Créer l'élément Pyt pour les moyens de paiement
            pyt = ET.SubElement(pyt_section_details, 'Pyt')
            
            # Ajouter le code du moyen de paiement
            if 'payment_means_code' in payment_means_data:
                payment_means_code = ET.SubElement(pyt, 'PaymentMeansCode')
                payment_means_code.text = str(payment_means_data['payment_means_code'])
            
            # Ajouter l'identifiant du paiement
            if 'payment_id' in payment_means_data:
                payment_id = ET.SubElement(pyt, 'PaymentID')
                payment_id.text = str(payment_means_data['payment_id'])
            
            # Ajouter la date d'échéance si fournie
            if 'due_date' in payment_means_data and payment_means_data['due_date']:
                pyt_dtm = ET.SubElement(pyt, 'PytDtm')
                date_text = ET.SubElement(pyt_dtm, 'DateText', 
                                       format="YYYY-MM-DD", 
                                       functionCode="I-32")  # I-32 = Date d'échéance
                date_text.text = str(payment_means_data['due_date'])
            
            # Ajouter les informations du compte bancaire si disponibles
            if 'payee_financial_account' in payment_means_data and payment_means_data['payee_financial_account']:
                pyt_fii = ET.SubElement(pyt, 'PytFii', functionCode="I-141")  # I-141 = Compte bancaire du bénéficiaire
                
                # Ajouter les informations du titulaire du compte
                account_holder = ET.SubElement(pyt_fii, 'AccountHolder')
                
                if 'iban' in payment_means_data['payee_financial_account']:
                    account_number = ET.SubElement(account_holder, 'AccountNumber')
                    account_number.text = str(payment_means_data['payee_financial_account']['iban'])
                
                if 'account_holder' in payment_means_data['payee_financial_account']:
                    owner_identifier = ET.SubElement(account_holder, 'OwnerIdentifier')
                    owner_identifier.text = str(payment_means_data['payee_financial_account']['account_holder'])
                
                # Ajouter les informations de l'institution financière
                if 'financial_institution' in payment_means_data['payee_financial_account']:
                    institution = ET.SubElement(pyt_fii, 'InstitutionIdentification')
                    
                    institution_name = ET.SubElement(institution, 'InstitutionName')
                    institution_name.text = str(payment_means_data['payee_financial_account']['financial_institution'])
                    
                    # Ajouter le code d'agence si fourni
                    if 'branch_code' in payment_means_data['payee_financial_account']:
                        branch_code = ET.SubElement(institution, 'BranchIdentifier')
                        branch_code.text = str(payment_means_data['payee_financial_account']['branch_code'])
                
        except Exception as e:
            self.logger.error(f"Error adding payment means: {str(e)}")
            raise

    def _add_line_items(self, parent: ET.Element, line_items: List[Dict[str, Any]]) -> None:
        """
        Add line items section.
        
        Args:
            parent: Parent XML element (InvoiceBody)
            line_items: List of line item dictionaries
        """
        try:
            if not line_items:
                return
                
            lin_section = ET.SubElement(parent, 'LinSection')
            
            for idx, item in enumerate(line_items, 1):
                line = ET.SubElement(lin_section, 'Lin')
                line.set('lineNumber', str(idx))
                
                # Add item identifier (use item_identifier from the data)
                item_id = ET.SubElement(line, 'ItemIdentifier')
                item_id.text = str(item.get('item_identifier', f'ITEM-{idx}'))
                
                # Add item description
                imd = ET.SubElement(line, 'LinImd')
                imd.set('lang', 'fr')
                
                item_code = ET.SubElement(imd, 'ItemCode')
                item_code.text = str(item.get('item_code', ''))
                
                item_desc = ET.SubElement(imd, 'ItemDescription')
                item_desc.text = str(item.get('description', '')) 
                
                # Add quantity
                qty = ET.SubElement(line, 'LinQty')
                quantity = float(item.get('quantity', 1))
                unit = str(item.get('unit', 'PCE'))
                
                quantity_elem = ET.SubElement(qty, 'Quantity')
                quantity_elem.set('measurementUnit', unit)
                quantity_elem.text = f"{quantity:.1f}"
                
                # Add unit price
                unit_price = float(item.get('unit_price', 0))
                price = ET.SubElement(line, 'LinPrice')
                price_elem = ET.SubElement(price, 'Price')
                price_elem.set('currencyIdentifier', item.get('currency', 'TND'))
                price_elem.text = f"{unit_price:.3f}"
                
                # Calculate line amount
                line_amount = quantity * unit_price
                
                # Add line amount
                moa = ET.SubElement(line, 'LinMoa')
                moa_details = ET.SubElement(moa, 'MoaDetails')
                
                amount_elem = ET.SubElement(moa_details, 'Moa', amountTypeCode='I-183', currencyCodeList='ISO_4217')
                amount = ET.SubElement(amount_elem, 'Amount')
                amount.set('currencyIdentifier', item.get('currency', 'TND'))
                amount.text = f"{line_amount:.3f}"
                
                # Add tax information if available
                if 'taxes' in item and item['taxes'] and len(item['taxes']) > 0:
                    tax_data = item['taxes'][0]  # Take first tax for simplicity
                    tax = ET.SubElement(line, 'LinTax')
                    
                    tax_type = ET.SubElement(tax, 'TaxTypeName')
                    tax_type.set('code', str(tax_data.get('code', 'I-1602')))
                    tax_type.text = str(tax_data.get('type_name', 'TVA'))
                    
                    if 'category' in tax_data:
                        tax_cat = ET.SubElement(tax, 'TaxCategory')
                        tax_cat.text = str(tax_data['category'])
                    
                    tax_details = ET.SubElement(tax, 'TaxDetails')
                    tax_detail = ET.SubElement(tax_details, 'TaxDetail')
                    
                    tax_rate = ET.SubElement(tax_detail, 'TaxRate')
                    tax_rate.text = str(tax_data.get('rate', 0))
                    
                    tax_basis = ET.SubElement(tax_detail, 'TaxRateBasis')
                    tax_basis.text = f"{line_amount:.3f}"
                    
                    tax_amount = line_amount * (float(tax_data.get('rate', 0)) / 100)
                    
                    tax_amount_details = ET.SubElement(tax, 'AmountDetails')
                    tax_moa = ET.SubElement(tax_amount_details, 'Moa', amountTypeCode='TAX_AMOUNT')
                    
                    tax_amount_elem = ET.SubElement(tax_moa, 'Amount')
                    tax_amount_elem.set('currencyIdentifier', tax_data.get('currency', 'TND'))
                    tax_amount_elem.text = f"{tax_amount:.3f}"
                    
                    tax_desc = ET.SubElement(tax_moa, 'AmountDescription', lang='FR')
                    tax_desc.text = 'Montant de la taxe'
                
        except Exception as e:
            self.logger.error(f"Error adding line items: {str(e)}")
            raise

    def _add_invoice_tax(self, parent: ET.Element, taxes_data: List[Dict[str, Any]]) -> None:
        """
        Add invoice tax section.
        
        Args:
            parent: Parent XML element (InvoiceBody)
            taxes_data: List of tax dictionaries with tax details
        """
        try:
            # Create a single InvoiceTax element
            invoice_tax = ET.SubElement(parent, 'InvoiceTax')
            invoice_tax_details = ET.SubElement(invoice_tax, 'InvoiceTaxDetails')
            
            # Add each tax to the InvoiceTaxDetails
            for tax_data in taxes_data:
                # Create Tax element for each tax
                tax = ET.SubElement(invoice_tax_details, 'Tax')
                
                # Add tax type with code
                tax_type = ET.SubElement(tax, 'TaxTypeName', code=str(tax_data.get('code', '')))
                tax_type.text = str(tax_data.get('type_name', ''))[:35]
                
                # Add tax category if provided
                if 'category' in tax_data and tax_data['category']:
                    category = ET.SubElement(tax, 'TaxCategory')
                    category.text = str(tax_data['category'])[:6]
                
                # Add tax details (rate and basis)
                tax_details = ET.SubElement(tax, 'TaxDetails')
                tax_detail = ET.SubElement(tax_details, 'TaxDetail')
                rate = ET.SubElement(tax_detail, 'TaxRate')
                rate.text = str(tax_data.get('rate', 0))
                
                if 'basis' in tax_data and tax_data['basis'] is not None:
                    basis = ET.SubElement(tax_detail, 'TaxRateBasis')
                    basis.text = str(tax_data['basis'])
                
                # Add amount details
                amount_details = ET.SubElement(tax, 'AmountDetails')
                moa = ET.SubElement(amount_details, 'Moa', amountTypeCode='TAX_AMOUNT')
                
                amount = ET.SubElement(moa, 'Amount')
                amount.set('currencyIdentifier', tax_data.get('currency', 'TND'))
                amount.text = str(tax_data.get('amount', 0))
                
                desc = ET.SubElement(moa, 'AmountDescription', lang='FR')
                desc.text = 'Montant de la taxe'
                
        except Exception as e:
            self.logger.error(f"Error adding invoice tax section: {str(e)}")
            raise

    def _add_invoice_totals(self, parent: ET.Element, totals_data: Dict[str, Any]) -> None:
        """
        Add invoice totals section.
        
        Args:
            parent: Parent XML element (InvoiceBody)
            totals_data: Dictionary containing total amounts
        """
        try:
            # Calculate totals from line items if not provided
            if 'total_without_tax' not in totals_data:
                total_ht = 0.0
                total_tva = 0.0
                
                # Find all line items
                for line in parent.findall('.//Lin'):
                    # Get amount without tax
                    amount_elem = line.find('.//Moa[amountTypeCode="I-183"]/Amount')
                    if amount_elem is not None and amount_elem.text:
                        total_ht += float(amount_elem.text)
                    
                    # Get tax amount
                    tax_amount_elem = line.find('.//Moa[amountTypeCode="TAX_AMOUNT"]/Amount')
                    if tax_amount_elem is not None and tax_amount_elem.text:
                        total_tva += float(tax_amount_elem.text)
                
                totals_data['total_without_tax'] = total_ht
                totals_data['total_tax'] = total_tva
                totals_data['total_with_tax'] = total_ht + total_tva
            
            # Add invoice totals
            invoice_moa = ET.SubElement(parent, 'InvoiceMoa')
            amount_details = ET.SubElement(invoice_moa, 'AmountDetails')
            
            # Add total without tax
            total_ht = totals_data.get('total_without_tax', 0)
            self._add_moa(amount_details, 'I-181', total_ht, 'Total hors taxes')
            
            # Add total tax
            total_tva = totals_data.get('total_tax', 0)
            self._add_moa(amount_details, 'I-182', total_tva, 'Total des taxes')
            
            # Add total with tax
            total_ttc = totals_data.get('total_with_tax', total_ht + total_tva)
            self._add_moa(amount_details, 'I-183', total_ttc, 'Total toutes taxes comprises')
            
            # Add paid amount if any
            paid_amount = totals_data.get('paid_amount', 0)
            if paid_amount > 0:
                self._add_moa(amount_details, 'I-184', paid_amount, 'Montant déjà payé')
                
                # Add remaining amount
                remaining_amount = max(0, total_ttc - paid_amount)
                self._add_moa(amount_details, 'I-185', remaining_amount, 'Montant restant dû')
            
        except Exception as e:
            self.logger.error(f"Error adding invoice totals: {str(e)}")
            raise

    def _add_invoice_amounts(self, parent: ET.Element, invoice_data: Dict[str, Any]) -> None:
        """
        Add invoice amounts section.
        
        Args:
            parent: Parent XML element (InvoiceBody)
            invoice_data: Dictionary containing invoice data
        """
        try:
            # Calculate totals from line items
            total_ht = 0.0
            total_tva = 0.0
            
            # Calculate from line items if available
            if 'line_items' in invoice_data and invoice_data['line_items']:
                for item in invoice_data['line_items']:
                    quantity = float(item.get('quantity', 1))
                    unit_price = float(item.get('unit_price', 0))
                    tax_rate = float(item.get('tax_rate', 0)) / 100  # Convert percentage to decimal
                    
                    item_total = quantity * unit_price
                    total_ht += item_total
                    total_tva += item_total * tax_rate
            
            # Apply any global adjustments from invoice data
            if 'adjustments' in invoice_data:
                for adj in invoice_data['adjustments']:
                    if adj.get('type') == 'discount':
                        discount = float(adj.get('amount', 0))
                        total_ht -= discount
                        # Recalculate tax on discounted amount if needed
                        total_tva = total_ht * (float(invoice_data.get('default_tax_rate', 0)) / 100)
            
            total_ttc = total_ht + total_tva
            
            # Add payment information if available
            paid_amount = float(invoice_data.get('paid_amount', 0))
            remaining_amount = max(0, total_ttc - paid_amount)
            
            # Create InvoiceMoa section
            invoice_moa = ET.SubElement(parent, 'InvoiceMoa')
            amount_details = ET.SubElement(invoice_moa, 'AmountDetails')
            
            # Add HT amount
            self._add_moa(amount_details, 'I-181', total_ht, 'Total hors taxes')
            
            # Add TVA amount
            self._add_moa(amount_details, 'I-182', total_tva, 'Total des taxes')
            
            # Add TTC amount
            self._add_moa(amount_details, 'I-183', total_ttc, 'Total toutes taxes comprises')
            
            # Add paid amount if any
            if paid_amount > 0:
                self._add_moa(amount_details, 'I-184', paid_amount, 'Montant déjà payé')
                
                # Add remaining amount
                self._add_moa(amount_details, 'I-185', remaining_amount, 'Montant restant dû')
            
        except Exception as e:
            self.logger.error(f"Error adding invoice amounts: {str(e)}")
            raise

    def _add_signature(self, parent: ET.Element, signature_data: Dict[str, Any]) -> None:
        """
        Add signature section to the XML document.
        
        Args:
            parent: Parent XML element (root TEIF element)
            signature_data: Dictionary containing signature data
                - id: Unique identifier for the signature (optional)
                - signer_role: Role of the signer (optional)
                - signer_name: Name of the signer (optional)
                - x509_cert: X.509 certificate in PEM format (required)
                - private_key: Private key in PEM format (optional, required for signing)
                - key_password: Password for the private key (optional)
                - date: Signature date (optional, default: now)
        """
        try:
            if not signature_data or 'x509_cert' not in signature_data:
                self.logger.warning("No certificate provided for signature. Skipping signature section.")
                return

            # Create signature section
            signature_section = SignatureSection()
            
            # Add the signature with certificate and optional private key
            signature_section.add_signature(
                cert_data=signature_data['x509_cert'],
                key_data=signature_data.get('private_key'),
                key_password=signature_data.get('key_password'),
                signature_id=signature_data.get('id', 'SigFrs'),
                role=signature_data.get('signer_role'),
                name=signature_data.get('signer_name', 'Signataire'),
                date=signature_data.get('date')
            )
            
            # Generate the signature XML and add it to the root
            signature_element = signature_section.to_xml(parent)
            parent.append(signature_element)
            
        except Exception as e:
            self.logger.error(f"Error adding signature: {str(e)}")
            raise

    def _add_moa(self, parent: ET.Element, code: str, amount: float, description: str, currency: str = 'TND') -> None:
        """
        Add a monetary amount element to the parent element.
        
        Args:
            parent: Parent XML element
            code: MOA code (e.g., 'I-181' for total without tax)
            amount: Amount value
            description: Description of the amount
            currency: Currency code (default: 'TND')
        """
        try:
            moa = ET.SubElement(parent, 'Moa')
            moa.set('amountTypeCode', code)
            
            # Add amount element
            amount_elem = ET.SubElement(moa, 'Amount')
            amount_elem.set('currencyIdentifier', currency)
            amount_elem.text = f"{amount:.3f}"
            
            # Add description
            desc_elem = ET.SubElement(moa, 'AmountDescription')
            desc_elem.set('lang', 'FR')
            desc_elem.text = description
            
        except Exception as e:
            self.logger.error(f"Error adding MOA element: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
   
    invoice_data = {
       
    }
    
    # Generate the TEIF XML
    generator = TEIFGenerator()
    try:
        xml_output = generator.generate_teif_xml(invoice_data)
        print(xml_output)
    except Exception as e:
        print(f"Error generating TEIF XML: {str(e)}")