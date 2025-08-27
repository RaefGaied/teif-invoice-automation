"""
Module pour la gestion des montants dans les documents TEIF.

Ce module contient les fonctions nécessaires pour créer et manipuler
les montants dans un document TEIF, y compris les totaux, les taxes,
et les montants de ligne.
"""
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
import datetime

class AmountsSection:
    """
    A class to handle all amount-related operations in TEIF documents.
    
    This class provides methods to create and manage amounts, taxes, and totals
    according to the TEIF 1.8.8 standard.
    """
    
    def __init__(self, 
                 currency: str = 'TND',
                 decimal_places: int = 3):
        """
        Initialize a new AmountsSection instance.
        
        Args:
            currency: Currency code (default: 'TND' for Tunisian Dinar)
            decimal_places: Number of decimal places for rounding (default: 3)
        """
        self.currency = currency
        self.decimal_places = decimal_places
        self.totals = {}
        self.taxes = []
        self.payments = []
        self.adjustments = []
    
    def add_total(self, 
                 amount_type: str, 
                 amount: float, 
                 amount_type_name: Optional[str] = None) -> None:
        """
        Add a total amount.
        
        Args:
            amount_type: Type of amount according to TEIF standard (e.g., 'I-170' for total without tax)
            amount: The amount value
            amount_type_name: Optional name/description of the amount type
        """
        self.totals[amount_type] = {
            'amount': amount,
            'amount_type': amount_type,
            'amount_type_name': amount_type_name or amount_type,
            'currency': self.currency,
            'format': self.decimal_places
        }
    
    def add_tax(self,
               tax_code: str,
               tax_type: str,
               rate: float,
               amount: float,
               taxable_amount: float) -> None:
        """
        Add a tax amount.
        
        Args:
            tax_code: Tax code according to TEIF standard (e.g., 'I-1602' for VAT)
            tax_type: Type of tax (e.g., 'TVA', 'Droit de timbre')
            rate: Tax rate as a percentage
            amount: Tax amount
            taxable_amount: Taxable amount
        """
        self.taxes.append({
            'code': tax_code,
            'type': tax_type,
            'rate': rate,
            'amount': amount,
            'taxable_amount': taxable_amount,
            'currency': self.currency,
            'format': self.decimal_places
        })
    
    def add_payment(self,
                   amount: float,
                   payment_date: str,
                   payment_means_code: str,
                   payment_means_name: Optional[str] = None,
                   payment_id: Optional[str] = None,
                   payment_reference: Optional[str] = None,
                   due_date: Optional[str] = None,
                   paid: bool = True) -> None:
        """
        Add a payment.
        
        Args:
            amount: Payment amount
            payment_date: Payment date in YYYY-MM-DD format
            payment_means_code: Payment means code (e.g., '30' for bank transfer)
            payment_means_name: Optional payment means description
            payment_id: Optional payment ID
            payment_reference: Optional payment reference
            due_date: Optional due date in YYYY-MM-DD format
            paid: Whether the payment has been made (default: True)
        """
        self.payments.append({
            'amount': amount,
            'payment_date': payment_date,
            'payment_means_code': payment_means_code,
            'payment_means_name': payment_means_name or f"Payment {len(self.payments) + 1}",
            'payment_id': payment_id,
            'payment_reference': payment_reference,
            'due_date': due_date,
            'paid': paid,
            'currency': self.currency,
            'format': self.decimal_places
        })
    
    def to_xml(self, parent: ET.Element = None) -> ET.Element:
        """
        Generate the XML representation of the amounts section.
        
        Args:
            parent: The parent XML element. If None, creates a new root element.
            
        Returns:
            ET.Element: The generated XML element
        """
        if parent is None:
            amounts_section = ET.Element('AmountsSection')
        else:
            amounts_section = ET.SubElement(parent, 'AmountsSection')
        
        # Add totals
        for total in self.totals.values():
            create_amount_element(amounts_section, total)
        
        # Add taxes
        for tax in self.taxes:
            create_tax_amount(amounts_section, tax)
        
        # Add payments
        for payment in self.payments:
            create_payment(amounts_section, payment)
        
        # Add adjustments (if any)
        for adjustment in self.adjustments:
            create_adjustment(amounts_section, adjustment)
        
        return amounts_section

def create_amount_element(parent: ET.Element, amount_data: Dict[str, Any]) -> ET.Element:
    """
    Crée un élément de montant avec la devise, le type et le montant spécifié.
    
    Args:
        parent: L'élément parent XML
        amount_data: Dictionnaire contenant les données du montant
            - amount (obligatoire): Le montant numérique
            - currency: Code devise ISO 4217 (par défaut: 'TND')
            - format: Nombre de décimales pour l'arrondi (par défaut: 3)
            - amount_type: Type de montant selon la norme TEIF (ex: 'I-170', 'I-172')
            - amount_type_name: Libellé du type de montant (optionnel)
            
    Returns:
        ET.Element: L'élément Moa créé
        
    Raises:
        ValueError: Si les données obligatoires sont manquantes ou invalides
    """
    # Validation des entrées
    if not isinstance(parent, ET.Element):
        raise ValueError("L'élément parent doit être de type xml.etree.ElementTree.Element")
        
    if 'amount' not in amount_data:
        raise ValueError("Le montant est obligatoire (clé 'amount')")
    
    try:
        # Conversion et formatage du montant
        amount = float(amount_data['amount'])
        decimals = int(amount_data.get('format', 3))
        formatted_amount = f"{amount:.{decimals}f}"
        
        # Création de l'élément Moa
        moa = ET.SubElement(parent, "Moa")
        
        # Création de l'élément Amount avec les attributs
        amount_attrs = {
            'currencyID': amount_data.get('currency', 'TND')
        }
        
        # Ajout du type de montant s'il est spécifié
        if 'amount_type' in amount_data:
            amount_attrs['amountTypeCode'] = str(amount_data['amount_type'])
            
        amount_elem = ET.SubElement(moa, "Amount", **amount_attrs)
        amount_elem.text = formatted_amount
        
        # Ajout du libellé du type de montant si spécifié
        if 'amount_type_name' in amount_data:
            ET.SubElement(moa, "AmountTypeName").text = str(amount_data['amount_type_name'])
        
        return moa
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de montant invalide: {str(e)}")

def create_tax_amount(parent: ET.Element, tax_data: Dict[str, Any]) -> ET.Element:
    """
    Crée un élément de taxe avec son montant et ses détails.
    
    Args:
        parent: L'élément parent XML
        tax_data: Dictionnaire contenant les données de la taxe
            - code (obligatoire): Code de la taxe selon la norme TEIF (ex: 'I-1602' pour TVA)
            - type: Type de taxe (ex: 'TVA', 'Droit de timbre')
            - rate (obligatoire): Taux de taxe en pourcentage
            - amount (obligatoire): Montant de la taxe
            - taxable_amount (obligatoire): Montant taxable
            - currency: Code devise ISO 4217 (par défaut: 'TND')
            - format: Nombre de décimales pour l'arrondi (par défaut: 3)
            
    Returns:
        ET.Element: L'élément InvoiceTax créé
        
    Raises:
        ValueError: Si les données obligatoires sont manquantes ou invalides
    """
    # Validation des entrées obligatoires
    required_fields = ['code', 'rate', 'amount', 'taxable_amount']
    missing_fields = [field for field in required_fields if field not in tax_data]
    if missing_fields:
        raise ValueError(
            f"Champs de taxe manquants: {', '.join(missing_fields)}. "
            "Les champs 'code', 'rate', 'amount' et 'taxable_amount' sont obligatoires."
        )
    
    try:
        # Conversion des valeurs numériques
        rate = float(tax_data['rate'])
        amount = float(tax_data['amount'])
        taxable_amount = float(tax_data['taxable_amount'])
        
        if rate < 0 or amount < 0 or taxable_amount < 0:
            raise ValueError("Les montants et taux de taxe ne peuvent pas être négatifs")
        
        # Création de l'élément InvoiceTax
        invoice_tax = ET.SubElement(parent, "InvoiceTax")
        
        # Section Tax avec le type et le taux
        tax = ET.SubElement(invoice_tax, "Tax")
        
        # Type de taxe
        tax_type = ET.SubElement(tax, "TaxTypeName", code=str(tax_data['code']))
        tax_type.text = str(tax_data.get('type', ''))
        
        # Taux de taxe
        ET.SubElement(tax, "TaxRate").text = f"{rate:.1f}"
        
        # Montant taxable
        create_amount_element(
            invoice_tax,
            {
                'amount': taxable_amount,
                'currency': tax_data.get('currency', 'TND'),
                'format': tax_data.get('format', 3),
                'amount_type': 'I-172',  # Montant HT des articles
                'amount_type_name': 'Montant hors taxes'
            }
        )
        
        # Montant de la taxe
        create_amount_element(
            invoice_tax,
            {
                'amount': amount,
                'currency': tax_data.get('currency', 'TND'),
                'format': tax_data.get('format', 3),
                'amount_type': 'I-178',  # Montant total des taxes
                'amount_type_name': 'Montant de la taxe'
            }
        )
        
        return invoice_tax
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de données de taxe invalide: {str(e)}")

def create_line_amount(parent: ET.Element, line_data: Dict[str, Any]) -> ET.Element:
    """
    Crée les éléments de montant pour une ligne de facture.
    
    Args:
        parent: L'élément parent XML
        line_data: Dictionnaire contenant les données de la ligne
            - unit_price (obligatoire): Prix unitaire hors taxes
            - quantity (obligatoire): Quantité
            - line_total (obligatoire): Montant total de la ligne
            - currency: Code devise ISO 4217 (par défaut: 'TND')
            - format: Nombre de décimales pour l'arrondi (par défaut: 3)
            - tax_included: Indique si le prix unitaire est TTC (par défaut: False)
            - discount_amount: Montant de la remise (optionnel)
            - discount_rate: Taux de remise en pourcentage (optionnel)
            
    Returns:
        ET.Element: L'élément parent avec les montants ajoutés
        
    Raises:
        ValueError: Si les données obligatoires sont manquantes ou invalides
    """
    # Validation des entrées obligatoires
    required_fields = ['unit_price', 'quantity', 'line_total']
    missing_fields = [field for field in required_fields if field not in line_data]
    if missing_fields:
        raise ValueError(
            f"Champs de ligne manquants: {', '.join(missing_fields)}. "
            "Les champs 'unit_price', 'quantity' et 'line_total' sont obligatoires."
        )
    
    try:
        # Conversion des valeurs numériques
        unit_price = float(line_data['unit_price'])
        quantity = float(line_data['quantity'])
        line_total = float(line_data['line_total'])
        
        if unit_price < 0 or quantity <= 0 or line_total < 0:
            raise ValueError("Les montants doivent être positifs et la quantité doit être supérieure à zéro")
        
        # Création de l'élément Price pour le prix unitaire
        price = ET.SubElement(parent, "Price")
        create_amount_element(
            price,
            {
                'amount': unit_price,
                'currency': line_data.get('currency', 'TND'),
                'format': line_data.get('format', 4),  # 4 décimales pour les prix unitaires
                'amount_type': 'I-176' if line_data.get('tax_included', False) else 'I-175',
                'amount_type_name': 'Prix unitaire TTC' if line_data.get('tax_included', False) 
                                 else 'Prix unitaire HT'
            }
        )
        
        # Ajout de la quantité
        ET.SubElement(parent, "Quantity").text = f"{quantity:.3f}"
        
        # Ajout de la remise si spécifiée
        if 'discount_amount' in line_data or 'discount_rate' in line_data:
            discount_elem = ET.SubElement(parent, "Discount")
            
            # Montant de la remise
            if 'discount_amount' in line_data:
                discount_amount = float(line_data['discount_amount'])
                if discount_amount < 0:
                    raise ValueError("Le montant de la remise ne peut pas être négatif")
                    
                create_amount_element(
                    discount_elem,
                    {
                        'amount': discount_amount,
                        'currency': line_data.get('currency', 'TND'),
                        'format': line_data.get('format', 3),
                        'amount_type': 'I-172',  # Remise commerciale
                        'amount_type_name': 'Montant de la remise'
                    }
                )
            
            # Taux de remise
            if 'discount_rate' in line_data:
                discount_rate = float(line_data['discount_rate'])
                if not (0 <= discount_rate <= 100):
                    raise ValueError("Le taux de remise doit être compris entre 0 et 100%")
                ET.SubElement(discount_elem, "Rate").text = f"{discount_rate:.2f}"
        
        # Montant total de la ligne
        create_amount_element(
            parent,
            {
                'amount': line_total,
                'currency': line_data.get('currency', 'TND'),
                'format': line_data.get('format', 3),
                'amount_type': 'I-180' if line_data.get('tax_included', False) else 'I-179',
                'amount_type_name': 'Montant total TTC' if line_data.get('tax_included', False)
                                 else 'Montant total HT'
            }
        )
        
        return parent
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de données de ligne invalide: {str(e)}")

def create_invoice_totals(parent: ET.Element, totals_data: Dict[str, Any]) -> ET.Element:
    """
    Crée les éléments de totaux pour une facture.
    
    Args:
        parent: L'élément parent XML
        totals_data: Dictionnaire contenant les totaux de la facture
            - total_without_tax (obligatoire): Montant total HT
            - total_tax (obligatoire): Montant total des taxes
            - total_with_tax (obligatoire): Montant total TTC
            - currency: Code devise ISO 4217 (par défaut: 'TND')
            - format: Nombre de décimales pour l'arrondi (par défaut: 3)
            - prepaid_amount: Montant déjà payé (optionnel)
            - due_amount: Montant restant dû (optionnel)
            
    Returns:
        ET.Element: L'élément parent avec les totaux ajoutés
        
    Raises:
        ValueError: Si les données obligatoires sont manquantes ou invalides
    """
    required_fields = ['total_without_tax', 'total_tax', 'total_with_tax']
    missing_fields = [field for field in required_fields if field not in totals_data]
    if missing_fields:
        raise ValueError(
            f"Champs de totaux manquants: {', '.join(missing_fields)}. "
            "Les champs 'total_without_tax', 'total_tax' et 'total_with_tax' sont obligatoires."
        )
    
    try:
        # Conversion des valeurs numériques
        total_without_tax = float(totals_data['total_without_tax'])
        total_tax = float(totals_data['total_tax'])
        total_with_tax = float(totals_data['total_with_tax'])
        
        if total_without_tax < 0 or total_tax < 0 or total_with_tax < 0:
            raise ValueError("Les montants des totaux ne peuvent pas être négatifs")
        
        # Création des éléments de totaux
        # Montant total HT
        create_amount_element(
            parent,
            {
                'amount': total_without_tax,
                'currency': totals_data.get('currency', 'TND'),
                'format': totals_data.get('format', 3),
                'amount_type': 'I-181',  # Total HT
                'amount_type_name': 'Total hors taxes'
            }
        )
        
        # Montant total des taxes
        create_amount_element(
            parent,
            {
                'amount': total_tax,
                'currency': totals_data.get('currency', 'TND'),
                'format': totals_data.get('format', 3),
                'amount_type': 'I-182',  # Total TVA
                'amount_type_name': 'Total des taxes'
            }
        )
        
        # Montant total TTC
        create_amount_element(
            parent,
            {
                'amount': total_with_tax,
                'currency': totals_data.get('currency', 'TND'),
                'format': totals_data.get('format', 3),
                'amount_type': 'I-183',  # Total TTC
                'amount_type_name': 'Total toutes taxes comprises'
            }
        )
        
        # Montant déjà payé (optionnel)
        if 'prepaid_amount' in totals_data:
            prepaid_amount = float(totals_data['prepaid_amount'])
            if prepaid_amount < 0:
                raise ValueError("Le montant déjà payé ne peut pas être négatif")
                
            create_amount_element(
                parent,
                {
                    'amount': prepaid_amount,
                    'currency': totals_data.get('currency', 'TND'),
                    'format': totals_data.get('format', 3),
                    'amount_type': 'I-184',  # Montant déjà payé
                    'amount_type_name': 'Montant déjà payé'
                }
            )
        
        # Montant restant dû (optionnel)
        if 'due_amount' in totals_data:
            due_amount = float(totals_data['due_amount'])
            if due_amount < 0:
                raise ValueError("Le montant restant dû ne peut pas être négatif")
                
            create_amount_element(
                parent,
                {
                    'amount': due_amount,
                    'currency': totals_data.get('currency', 'TND'),
                    'format': totals_data.get('format', 3),
                    'amount_type': 'I-185',  # Montant restant dû
                    'amount_type_name': 'Montant restant dû'
                }
            )
        
        return parent
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de données de totaux invalide: {str(e)}")

def create_payment(parent: ET.Element, payment_data: Dict[str, Any]) -> ET.Element:
    """
    Crée les éléments pour un paiement.
    
    Args:
        parent: L'élément parent XML
        payment_data: Dictionnaire contenant les données du paiement
            - amount (obligatoire): Montant du paiement
            - payment_date (obligatoire): Date du paiement au format YYYY-MM-DD
            - payment_means_code (obligatoire): Code du moyen de paiement (ex: '30' pour virement)
            - payment_means_name: Libellé du moyen de paiement
            - payment_id: Identifiant du paiement (numéro de transaction)
            - payment_reference: Référence du paiement
            - currency: Code devise ISO 4217 (par défaut: 'TND')
            - format: Nombre de décimales pour l'arrondi (par défaut: 3)
            - due_date: Date d'échéance au format YYYY-MM-DD (optionnel)
            - paid: Booléen indiquant si le paiement a été effectué (par défaut: True)
            
    Returns:
        ET.Element: L'élément Payment créé
        
    Raises:
        ValueError: Si les données obligatoires sont manquantes ou invalides
    """
    required_fields = ['amount', 'payment_date', 'payment_means_code']
    missing_fields = [field for field in required_fields if field not in payment_data]
    if missing_fields:
        raise ValueError(
            f"Champs de paiement manquants: {', '.join(missing_fields)}. "
            "Les champs 'amount', 'payment_date' et 'payment_means_code' sont obligatoires."
        )
    
    try:
        # Validation des données
        amount = float(payment_data['amount'])
        if amount <= 0:
            raise ValueError("Le montant du paiement doit être supérieur à zéro")
            
        # Création de l'élément Payment
        payment_elem = ET.SubElement(parent, "Payment")
        
        # Montant du paiement
        create_amount_element(
            payment_elem,
            {
                'amount': amount,
                'currency': payment_data.get('currency', 'TND'),
                'format': payment_data.get('format', 3),
                'amount_type': 'I-186',  # Montant du paiement
                'amount_type_name': 'Montant payé'
            }
        )
        
        # Date de paiement
        payment_date_elem = ET.SubElement(payment_elem, "PaymentDate")
        ET.SubElement(payment_date_elem, "Date").text = payment_data['payment_date']
        
        # Moyen de paiement
        payment_means = ET.SubElement(payment_elem, "PaymentMeans")
        ET.SubElement(
            payment_means, 
            "PaymentMeansCode", 
            code=payment_data['payment_means_code']
        ).text = payment_data.get('payment_means_name', '')
        
        # Référence de paiement (optionnelle)
        if 'payment_id' in payment_data or 'payment_reference' in payment_data:
            payment_ref = ET.SubElement(payment_elem, "PaymentReference")
            if 'payment_id' in payment_data:
                ET.SubElement(payment_ref, "PaymentID").text = str(payment_data['payment_id'])
            if 'payment_reference' in payment_data:
                ET.SubElement(payment_ref, "PaymentReference").text = str(payment_data['payment_reference'])
        
        # Date d'échéance (optionnelle)
        if 'due_date' in payment_data:
            due_date_elem = ET.SubElement(payment_elem, "DueDate")
            ET.SubElement(due_date_elem, "Date").text = payment_data['due_date']
        
        # Statut du paiement (optionnel)
        if not payment_data.get('paid', True):
            status = ET.SubElement(payment_elem, "PaymentStatus")
            ET.SubElement(status, "PaymentStatusCode").text = "UNPAID"
        
        return payment_elem
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de données de paiement invalide: {str(e)}")

def create_adjustment(parent: ET.Element, adjustment_data: Dict[str, Any]) -> ET.Element:
    """
    Crée les éléments pour un ajustement (crédit/avoir).
    
    Args:
        parent: L'élément parent XML
        adjustment_data: Dictionnaire contenant les données de l'ajustement
            - amount (obligatoire): Montant de l'ajustement (positif pour un avoir, négatif pour une dette)
            - reason_code (obligatoire): Code de la raison de l'ajustement
            - reason: Libellé de la raison de l'ajustement
            - reference: Référence de l'ajustement
            - currency: Code devise ISO 4217 (par défaut: 'TND')
            - format: Nombre de décimales pour l'arrondi (par défaut: 3)
            - tax_included: Booléen indiquant si le montant est TTC (par défaut: False)
            - tax_rate: Taux de TVA appliqué (optionnel)
            - tax_amount: Montant de la TVA (obligatoire si tax_included est True)
            - document_reference: Référence au document lié (facture d'origine)
            - issue_date: Date d'émission au format YYYY-MM-DD (par défaut: date du jour)
            
    Returns:
        ET.Element: L'élément CreditNote créé
        
    Raises:
        ValueError: Si les données obligatoires sont manquantes ou invalides
    """
    required_fields = ['amount', 'reason_code']
    missing_fields = [field for field in required_fields if field not in adjustment_data]
    
    # Vérification des champs conditionnels
    if adjustment_data.get('tax_included', False) and 'tax_amount' not in adjustment_data:
        missing_fields.append('tax_amount')
    
    if missing_fields:
        raise ValueError(
            f"Champs d'ajustement manquants: {', '.join(missing_fields)}. "
            "Les champs 'amount' et 'reason_code' sont obligatoires. "
            "Si tax_included=True, 'tax_amount' est également requis."
        )
    
    try:
        # Conversion et validation des montants
        amount = float(adjustment_data['amount'])
        if amount == 0:
            raise ValueError("Le montant de l'ajustement ne peut pas être zéro")
            
        # Déterminer le type d'ajustement (crédit ou débit)
        is_credit = amount > 0
        
        # Création de l'élément d'ajustement
        adjustment_type = "CreditNote" if is_credit else "DebitNote"
        adjustment_elem = ET.SubElement(parent, adjustment_type)
        
        # Référence de l'ajustement
        if 'reference' in adjustment_data:
            ET.SubElement(adjustment_elem, "ID").text = str(adjustment_data['reference'])
        
        # Date d'émission
        issue_date = adjustment_data.get('issue_date', datetime.date.today().isoformat())
        issue_date_elem = ET.SubElement(adjustment_elem, "IssueDate")
        ET.SubElement(issue_date_elem, "Date").text = issue_date
        
        # Raison de l'ajustement
        reason_elem = ET.SubElement(adjustment_elem, "AdjustmentReason")
        ET.SubElement(
            reason_elem, 
            "AdjustmentReasonCode", 
            code=str(adjustment_data['reason_code'])
        ).text = adjustment_data.get('reason', '')
        
        # Montant de l'ajustement
        amount_type = 'I-190' if is_credit else 'I-191'  # Crédit ou débit
        amount_name = 'Montant du crédit' if is_credit else 'Montant du débit'
        
        create_amount_element(
            adjustment_elem,
            {
                'amount': abs(amount),  # Montant toujours positif
                'currency': adjustment_data.get('currency', 'TND'),
                'format': adjustment_data.get('format', 3),
                'amount_type': amount_type,
                'amount_type_name': amount_name
            }
        )
        
        # Montant HT si TTC
        if adjustment_data.get('tax_included', False):
            tax_amount = float(adjustment_data['tax_amount'])
            create_amount_element(
                adjustment_elem,
                {
                    'amount': abs(amount) - tax_amount,
                    'currency': adjustment_data.get('currency', 'TND'),
                    'format': adjustment_data.get('format', 3),
                    'amount_type': 'I-192',  # Montant HT de l'ajustement
                    'amount_type_name': 'Montant HT de l\'ajustement'
                }
            )
        
        # Référence au document d'origine
        if 'document_reference' in adjustment_data:
            doc_ref = ET.SubElement(adjustment_elem, "BillingReference")
            ET.SubElement(doc_ref, "InvoiceDocumentReference")\
                .text = str(adjustment_data['document_reference'])
        
        return adjustment_elem
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format de données d'ajustement invalide: {str(e)}")

# Add to __all__ to make it available for import
__all__ = [
    'create_amount_element',
    'create_tax_amount',
    'create_line_amount',
    'create_invoice_totals',
    'create_payment',
    'create_adjustment',
    'AmountsSection'
]
