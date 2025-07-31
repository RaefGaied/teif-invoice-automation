import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import re
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# PDF processing libraries
try:
    import pdfplumber
except ImportError:
    print("Warning: pdfplumber not installed. Install with: pip install pdfplumber")
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    print("Warning: PyPDF2 not installed. Install with: pip install PyPDF2")
    PyPDF2 = None

class SimpleInvoiceExtractor:
    """Extracteur simple pour n'importe quelle facture - sans calculs."""
    
    def __init__(self):
        self.patterns = {
            'invoice_number': [
                r'facture\s*n[°o]\s*:?\s*([A-Z0-9\-]+)',
                r'invoice\s*(?:number|#)\s*:?\s*([A-Z0-9\-]+)',
                r'n[°o]\s*([A-Z0-9\-]+)',
                r'ref\s*:?\s*([A-Z0-9\-]+)',
                r'([0-9]{10,})',  # Numéros longs comme TTN
            ],
            'date': [
                r'date\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})',
            ],
            'amounts': [
                r'total\s*(?:ttc|ht)?\s*:?\s*([0-9,\.]+)',
                r'montant\s*(?:ttc|ht)?\s*:?\s*([0-9,\.]+)',
                r'sous[- ]total\s*:?\s*([0-9,\.]+)',
                r'([0-9,\.]+)\s*(?:dinars?|tnd|eur|€)',
            ],
            'currency': [
                r'(TND|EUR|USD|MAD|DZD)',
                r'(dinars?)',
                r'(euros?)',
                r'(€)',
            ],
            'tax_amounts': [
                r'tva\s*(?:\d+%?)?\s*:?\s*([0-9,\.]+)',
                r'vat\s*(?:\d+%?)?\s*:?\s*([0-9,\.]+)',
                r'taxe\s*:?\s*([0-9,\.]+)',
                r'fodec\s*:?\s*([0-9,\.]+)',
                r'timbre\s*:?\s*([0-9,\.]+)',
            ],
            'company_names': [
                r'(?:société|company|sarl|sa|sas|eurl)\s+([^,\n]+)',
                r'([A-Z][A-Z\s&]+(?:SARL|SA|SAS|EURL|LTD|INC))',
                r'([A-Z\s]{3,}(?:TRADENET|TELECOM|SERVICES|CONSULTING))',
            ],
            'tax_ids': [
                r'matricule\s*fiscal\s*:?\s*([0-9A-Z]+)',
                r'tax\s*id\s*:?\s*([0-9A-Z]+)',
                r'mf\s*:?\s*([0-9A-Z]+)',
                r'([0-9]{7}[A-Z]{3}[0-9]{3})',
            ]
        }
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extrait les données depuis un PDF."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Le fichier PDF {pdf_path} n'existe pas.")
        
        text = ""
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"Erreur pdfplumber: {e}")
        
        if not text and PyPDF2:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                print(f"Erreur PyPDF2: {e}")
        
        if not text:
            raise Exception("Impossible d'extraire le texte du PDF")
        
        return self._parse_text(text)
    
    def _parse_text(self, text: str) -> Dict:
        """Parse le texte extrait - SANS CALCULS."""
        
        # Structure de base
        invoice_data = {
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "currency": "TND",
            "total_amount": 0.0,
            "subtotal_ht": 0.0,
            "total_taxes": 0.0,
            "sender": {"name": "", "tax_id": "", "address": ""},
            "receiver": {"name": "", "tax_id": "", "address": ""},
            "payment_terms": "",
            "items": [],
            "invoice_taxes": [],
            "invoice_allowances": [],
            "ttn_validation_ref": "",
        }
        
        # Extraction simple - un pattern à la fois
        
        # 1. Numéro de facture
        for pattern in self.patterns['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data["invoice_number"] = match.group(1)
                break
        
        # 2. Date
        for pattern in self.patterns['date']:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    if '/' in date_str:
                        parts = date_str.split('/')
                    else:
                        parts = date_str.split('-')
                    
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            invoice_data["invoice_date"] = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                        else:  # DD/MM/YYYY
                            day, month, year = parts
                            if len(year) == 2:
                                year = f"20{year}"
                            invoice_data["invoice_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
                break
        
        # 3. Montants - EXTRAITS TELS QUELS
        amounts = []
        for pattern in self.patterns['amounts']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', '.'))
                    amounts.append(amount)
                except:
                    pass
        
        if amounts:
            # Le plus grand montant est probablement le total
            invoice_data["total_amount"] = max(amounts)
            # S'il y a plusieurs montants, le plus petit pourrait être HT
            if len(amounts) > 1:
                sorted_amounts = sorted(amounts)
                invoice_data["subtotal_ht"] = sorted_amounts[-2] if len(sorted_amounts) > 1 else sorted_amounts[0]
        
        # 4. Devise
        for pattern in self.patterns['currency']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                currency = match.group(1).upper()
                if currency in ['DINARS', 'DINAR']:
                    currency = 'TND'
                elif currency in ['EUROS', 'EURO', '€']:
                    currency = 'EUR'
                invoice_data["currency"] = currency
                break
        
        # 5. Taxes - EXTRAITES TELLES QUELLES
        tax_amounts = []
        for pattern in self.patterns['tax_amounts']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    tax_amount = float(match.replace(',', '.'))
                    tax_amounts.append(tax_amount)
                except:
                    pass
        
        if tax_amounts:
            invoice_data["total_taxes"] = sum(tax_amounts)
            # Créer des entrées de taxes
            for i, amount in enumerate(tax_amounts):
                invoice_data["invoice_taxes"].append({
                    "tax_type": "TVA" if i == 0 else f"Taxe_{i+1}",
                    "amount": amount,
                    "rate": 0.0  # On ne calcule pas le taux
                })
        
        # 6. Noms d'entreprises
        companies = []
        for pattern in self.patterns['company_names']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            companies.extend(matches)
        
        if companies:
            # Premier = fournisseur, dernier = client
            invoice_data["sender"]["name"] = companies[0].strip()
            if len(companies) > 1:
                invoice_data["receiver"]["name"] = companies[-1].strip()
        
        # 7. Identifiants fiscaux
        tax_ids = []
        for pattern in self.patterns['tax_ids']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tax_ids.extend(matches)
        
        if tax_ids:
            invoice_data["sender"]["tax_id"] = tax_ids[0]
            if len(tax_ids) > 1:
                invoice_data["receiver"]["tax_id"] = tax_ids[-1]
        
        # 8. Article par défaut
        if invoice_data["subtotal_ht"] > 0:
            unit_price = invoice_data["subtotal_ht"]
        else:
            unit_price = invoice_data["total_amount"]
        
        invoice_data["items"] = [{
            "description": "Article/Service (extrait automatiquement)",
            "quantity": 1,
            "unit_price": unit_price,
            "line_total": unit_price,
            "tax_rate": 0.0
        }]
        
        return invoice_data

def prettify_xml(elem):
    """Retourne une chaîne XML joliment formatée."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def transform_to_teif_xml(data):
    """Transforme en XML TEIF conforme - SANS RECALCULER."""
    
    root = ET.Element("TEIFInvoice",
                      attrib={"xmlns": "http://www.tradenet.com.tn/teif/invoice/1.0",
                              "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                              "xsi:schemaLocation": "http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd"})

    # 1. InvoiceHeader (M)
    invoice_header = ET.SubElement(root, "InvoiceHeader")
    invoice_header.set("version", "1.0")
    ET.SubElement(invoice_header, "MessageId").text = f"TTN-{data.get('invoice_number', 'UNKNOWN')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 2. Bgm (M)
    bgm = ET.SubElement(root, "Bgm")
    ET.SubElement(bgm, "DocumentTypeCode").text = "380"
    ET.SubElement(bgm, "DocumentNumber").text = data.get("invoice_number", "")
    
    # 3. Dtm (M)
    dtm_invoice = ET.SubElement(root, "Dtm")
    ET.SubElement(dtm_invoice, "DateTimeQualifier").text = "137"
    ET.SubElement(dtm_invoice, "DateTime").text = data.get("invoice_date", "")

    # 4. PartnerSection (M) - Vendeur
    supplier_section = ET.SubElement(root, "PartnerSection")
    supplier_section.set("role", "supplier")
    
    supplier_nad = ET.SubElement(supplier_section, "Nad")
    ET.SubElement(supplier_nad, "PartyQualifier").text = "SU"
    ET.SubElement(supplier_nad, "PartyId").text = data["sender"].get("tax_id", "")
    ET.SubElement(supplier_nad, "PartyName").text = data["sender"].get("name", "")
    ET.SubElement(supplier_nad, "PartyAddress").text = data["sender"].get("address", "")
    
    # PartnerSection (M) - Acheteur
    buyer_section = ET.SubElement(root, "PartnerSection")
    buyer_section.set("role", "buyer")
    
    buyer_nad = ET.SubElement(buyer_section, "Nad")
    ET.SubElement(buyer_nad, "PartyQualifier").text = "BY"
    ET.SubElement(buyer_nad, "PartyId").text = data["receiver"].get("tax_id", "")
    ET.SubElement(buyer_nad, "PartyName").text = data["receiver"].get("name", "")
    ET.SubElement(buyer_nad, "PartyAddress").text = data["receiver"].get("address", "")

    # 15. PytSection (C)
    if data.get("payment_terms"):
        pyt_section = ET.SubElement(root, "PytSection")
        pyt = ET.SubElement(pyt_section, "Pyt")
        ET.SubElement(pyt, "PaymentTermsTypeCode").text = "1"
        ET.SubElement(pyt, "PaymentTermsDescription").text = data.get("payment_terms", "")

    # 24. LinSection (M) - Articles
    for line_index, item in enumerate(data.get("items", []), 1):
        lin_section = ET.SubElement(root, "LinSection")
        lin_section.set("lineNumber", str(line_index))
        
        # 25. LinImd (M)
        lin_imd = ET.SubElement(lin_section, "LinImd")
        ET.SubElement(lin_imd, "ItemDescriptionType").text = "F"
        ET.SubElement(lin_imd, "ItemDescription").text = item.get("description", "")
        
        # 28. LinQty (M)
        lin_qty = ET.SubElement(lin_section, "LinQty")
        ET.SubElement(lin_qty, "QuantityQualifier").text = "47"
        ET.SubElement(lin_qty, "Quantity").text = str(item.get("quantity", 1))
        ET.SubElement(lin_qty, "MeasureUnitQualifier").text = "PCE"
        
        # 29. LinDtm (M)
        lin_dtm = ET.SubElement(lin_section, "LinDtm")
        ET.SubElement(lin_dtm, "DateTimeQualifier").text = "137"
        ET.SubElement(lin_dtm, "DateTime").text = data.get("invoice_date", "")
        
        # 30. LinTax (M)
        lin_tax = ET.SubElement(lin_section, "LinTax")
        ET.SubElement(lin_tax, "DutyTaxFeeTypeCode").text = "VAT"
        ET.SubElement(lin_tax, "DutyTaxFeeRate").text = f"{item.get('tax_rate', 0.0):.2f}"
        
        # 31. TaxPaymentDate (M)
        tax_payment_date = ET.SubElement(lin_tax, "TaxPaymentDate")
        ET.SubElement(tax_payment_date, "DateTimeQualifier").text = "140"
        ET.SubElement(tax_payment_date, "DateTime").text = data.get("invoice_date", "")
        
        # 36. LinMoa (M)
        lin_moa = ET.SubElement(lin_section, "LinMoa")
        ET.SubElement(lin_moa, "MonetaryAmountTypeQualifier").text = "203"
        ET.SubElement(lin_moa, "MonetaryAmount").text = f"{item.get('line_total', 0.0):.2f}"
        ET.SubElement(lin_moa, "CurrencyCode").text = data.get("currency", "TND")
        
        # 37. Rff (M)
        rff = ET.SubElement(lin_moa, "Rff")
        ET.SubElement(rff, "ReferenceQualifier").text = "LI"
        ET.SubElement(rff, "ReferenceNumber").text = f"LINE-{line_index}"

    # 41. InvoiceMoa (M)
    invoice_moa = ET.SubElement(root, "InvoiceMoa")
    moa = ET.SubElement(invoice_moa, "Moa")
    ET.SubElement(moa, "MonetaryAmountTypeQualifier").text = "86"
    ET.SubElement(moa, "MonetaryAmount").text = f"{data.get('total_amount', 0.0):.2f}"
    ET.SubElement(moa, "CurrencyCode").text = data.get("currency", "TND")
    
    # 46. InvoiceTax (M)
    invoice_tax = ET.SubElement(root, "InvoiceTax")
    
    # Utiliser les taxes extraites TELLES QUELLES
    for tax_info in data.get("invoice_taxes", []):
        tax_element = ET.SubElement(invoice_tax, "Tax")
        ET.SubElement(tax_element, "DutyTaxFeeTypeCode").text = tax_info.get("tax_type", "VAT")
        ET.SubElement(tax_element, "DutyTaxFeeRate").text = f"{tax_info.get('rate', 0.0):.2f}"
        
        tax_moa = ET.SubElement(tax_element, "Moa")
        ET.SubElement(tax_moa, "MonetaryAmountTypeQualifier").text = "124"
        ET.SubElement(tax_moa, "MonetaryAmount").text = f"{tax_info.get('amount', 0.0):.2f}"
        ET.SubElement(tax_moa, "CurrencyCode").text = data.get("currency", "TND")
    
    # 55. RefTtnVal (M)
    ref_ttn_val = ET.SubElement(root, "RefTtnVal")
    reference = ET.SubElement(ref_ttn_val, "Reference")
    ET.SubElement(reference, "ReferenceQualifier").text = "AAK"
    ET.SubElement(reference, "ReferenceNumber").text = data.get("ttn_validation_ref", f"TTN-PENDING-{data.get('invoice_number', 'UNKNOWN')}")
    
    ref_date = ET.SubElement(reference, "ReferenceDate")
    ET.SubElement(ref_date, "DateTimeQualifier").text = "171"
    ET.SubElement(ref_date, "DateTime").text = datetime.now().strftime("%Y-%m-%d")
    
    # 58. Signature (M)
    signature_element = ET.SubElement(root, "Signature")
    signature_element.set("xmlns:ds", "http://www.w3.org/2000/09/xmldsig#")
    
    signed_info = ET.SubElement(signature_element, "ds:SignedInfo")
    ET.SubElement(signed_info, "ds:CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    ET.SubElement(signed_info, "ds:SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
    
    signature_value = ET.SubElement(signature_element, "ds:SignatureValue")
    signature_value.text = "PLACEHOLDER_SIGNATURE_ELECTRONIQUE_XADES_BASE64"
    
    key_info = ET.SubElement(signature_element, "ds:KeyInfo")
    ET.SubElement(key_info, "ds:X509Data").text = "PLACEHOLDER_CERTIFICAT_X509_BASE64"

    return prettify_xml(root)

def process_invoice(input_source: str, output_dir: str = "public/teif-invoices") -> str:
    """Traite une facture et génère le fichier TEI-F XML."""
    
    if input_source.lower() == 'sample':
        print("Utilisation des données d'exemple...")
        # Données d'exemple simplifiées
        invoice_data = {
            "invoice_number": "SAMPLE-001",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "currency": "TND",
            "total_amount": 100.0,
            "subtotal_ht": 84.75,
            "total_taxes": 15.25,
            "sender": {"name": "Entreprise Exemple", "tax_id": "1234567ABC", "address": "Tunis"},
            "receiver": {"name": "Client Exemple", "tax_id": "9876543XYZ", "address": "Sfax"},
            "payment_terms": "Net 30 jours",
            "items": [{"description": "Service exemple", "quantity": 1, "unit_price": 84.75, "line_total": 84.75, "tax_rate": 18.0}],
            "invoice_taxes": [{"tax_type": "TVA", "amount": 15.25, "rate": 18.0}],
            "invoice_allowances": [],
            "ttn_validation_ref": "SAMPLE-REF-001",
        }
    elif input_source.endswith('.pdf'):
        print(f"Extraction des données depuis le PDF: {input_source}")
        extractor = SimpleInvoiceExtractor()
        invoice_data = extractor.extract_from_pdf(input_source)
        print(f"✅ Données extraites: Facture {invoice_data.get('invoice_number', 'N/A')}, Montant: {invoice_data.get('total_amount', 0)} {invoice_data.get('currency', 'TND')}")
    else:
        raise ValueError("Le fichier d'entrée doit être un PDF (.pdf) ou 'sample'")
    
    # Génération du XML TEI-F
    print("Génération du fichier TEI-F XML...")
    xml_content = transform_to_teif_xml(invoice_data)
    
    # Création du dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Nom de fichier
    invoice_number = invoice_data.get('invoice_number', 'UNKNOWN')
    file_name = f"facture_{invoice_number}.xml"
    output_path = os.path.join(output_dir, file_name)
    
    # Écriture du fichier
    with open(output_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_content)
    
    print(f"✅ Facture TEI-F générée: {output_path}")
    print(f"📊 Taille: {os.path.getsize(output_path)} octets")
    
    return output_path

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Convertit une facture PDF en format TEI-F XML (version simplifiée)",
        epilog="""Exemples:
  python transform_invoice_simple.py sample
  python transform_invoice_simple.py facture.pdf
  python transform_invoice_simple.py facture.pdf -o sortie/ --preview
        """
    )
    
    parser.add_argument('input', help="Fichier PDF ou 'sample'")
    parser.add_argument('-o', '--output', default='public/teif-invoices', help="Dossier de sortie")
    parser.add_argument('--preview', action='store_true', help="Aperçu du XML")
    parser.add_argument('-v', '--verbose', action='store_true', help="Mode verbeux")
    
    args = parser.parse_args()
    
    try:
        output_path = process_invoice(args.input, args.output)
        
        if args.preview:
            print("\n--- Aperçu du XML généré ---")
            with open(output_path, 'r', encoding='utf-8') as xml_file:
                lines = xml_file.readlines()
                for i, line in enumerate(lines[:25]):
                    print(f"{i+1:2d}: {line.rstrip()}")
                if len(lines) > 25:
                    print(f"... et {len(lines) - 25} lignes supplémentaires")
        
        if args.verbose:
            print(f"\n✅ Conversion terminée!")
            print(f"📁 Entrée: {args.input}")
            print(f"📁 Sortie: {output_path}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
