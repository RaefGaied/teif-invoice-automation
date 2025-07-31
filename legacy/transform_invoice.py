import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import re
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# PDF processing libraries
try:
    import pdfplumber
    import pandas as pd # pandas est importé mais non utilisé directement dans le code fourni, peut être retiré si non nécessaire
except ImportError:
    print("Warning: pdfplumber et pandas requis. Installez avec: pip install pdfplumber pandas")
    pdfplumber = None

class TTNInvoiceExtractor:
    """Extracteur spécialisé pour les factures TTN (Tunisie TradeNet)."""
    
    def __init__(self):
        # Patterns spécifiques aux factures TTN
        self.ttn_patterns = {
            'invoice_number': [
                r'facture\s*n°?\s*:?\s*([0-9]+)',
                r'référence\s*:?\s*([0-9]+)',
                r'n°\s*([0-9]+)',
                r'invoice\s*(?:number|n°)?\s*:?\s*([0-9A-Z\-]+)'
            ],
            'invoice_date': [
                r'date\s*:?\s*(\d{2}/\d{2}/\d{4})',
                r'(\d{2}/\d{2}/\d{4})',
                r'du\s*(\d{1,2}/\d{1,2}/\d{4})'
            ],
            'client_code': [
                r'code\s*client\s*:?\s*([0-9]+)',
                r'client\s*:?\s*([0-9]+)'
            ],
            'tax_id': [
                r'matricule\s*fiscal\s*:?\s*([0-9A-Z]+)',
                r'mf\s*:?\s*([0-9A-Z]+)'
            ],
            'payment_due_date': [
                r'date\s*limite\s*de\s*paiement\s*:?\s*(\d{6})',
                r'échéance\s*:?\s*(\d{2}/\d{2}/\d{4})'
            ],
            'ttn_reference': [
                r'([0-9]{15,20})',  # Long numeric reference
                r'TTN[\-\s]*([0-9\-]+)'
            ]
        }
        
        # Patterns pour les totaux et taxes
        self.total_patterns = {
            'total_ht': r'total\s*h\.?t\.?\s*:?\s*([0-9,\.]+)',
            'tva_amount': r'(?:t\.?v\.?a\.?|tva)\s*([0-9,\.]+)%?\s*([0-9,\.]+)',
            'fodec_amount': r'fodec\s*([0-9,\.]+)%?\s*([0-9,\.]+)',
            'timbre_amount': r'(?:droit\s*de\s*)?timbre\s*([0-9,\.]+)',
            'total_ttc': r'total\s*t\.?t\.?c\.?\s*:?\s*([0-9,\.]+)'
        }

    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extrait toutes les données d'une facture TTN depuis un PDF."""
        if not pdfplumber:
            raise ImportError("pdfplumber requis pour l'extraction PDF")
            
        print(f"🔍 Analyse du PDF: {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            # Extraire le texte de toutes les pages
            full_text = ""
            tables_data = []
            
            for page_num, page in enumerate(pdf.pages):
                print(f"📄 Traitement page {page_num + 1}")
                
                # Extraire le texte
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                
                # Extraire les tableaux
                tables = page.extract_tables()
                if tables:
                    tables_data.extend(tables)
                    print(f"📊 {len(tables)} tableau(x) trouvé(s)")
        
        # Analyser les données extraites
        invoice_data = self._parse_ttn_invoice(full_text, tables_data)
        
        # Afficher un résumé de l'extraction
        self._print_extraction_summary(invoice_data)
        
        return invoice_data

    def _parse_ttn_invoice(self, text: str, tables: List) -> Dict:
        """Parse spécifiquement une facture TTN."""
        print("🔍 Analyse des données TTN...")
        
        # Structure de données complète
        invoice_data = {
            "invoice_number": "",
            "invoice_date": "",
            "currency": "TND",
            "sender": {
                "name": "TUNISIE TRADENET",
                "tax_id": "1049000T",
                "address": "Rue du Lac Malaren, Immeuble El Khalij Les Berges du Lac, 1053 Tunis, Tunisie"
            },
            "receiver": {
                "name": "",
                "tax_id": "",
                "address": "",
                "client_code": ""
            },
            "payment_terms": "À régler exclusivement au niveau des bureaux postaux sur présentation de la facture",
            "payment_due_date": "",
            "items": [],
            "subtotal_ht": 0.0,
            "invoice_taxes": [],
            "total_taxes": 0.0,
            "total_amount": 0.0,
            "ttn_validation_ref": "",
            "invoice_allowances": []
        }
        
        # 1. Extraction des informations de base
        self._extract_basic_info(text, invoice_data)
        
        # 2. Extraction des informations client
        self._extract_client_info(text, invoice_data)
        
        # 3. Extraction des lignes d'articles depuis les tableaux
        self._extract_line_items(tables, invoice_data)
        
        # 4. Extraction des totaux et taxes
        self._extract_totals_and_taxes(text, tables, invoice_data)
        
        # 5. Extraction des références TTN
        self._extract_ttn_references(text, invoice_data)
        
        return invoice_data

    def _extract_basic_info(self, text: str, invoice_data: Dict):
        """Extrait les informations de base de la facture."""
        print("📋 Extraction des informations de base...")
        
        # Numéro de facture
        for pattern in self.ttn_patterns['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data["invoice_number"] = match.group(1)
                print(f"✅ Numéro de facture: {invoice_data['invoice_number']}")
                break
        
        # Date de facture - correction du format
        for pattern in self.ttn_patterns['invoice_date']:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    # Convertir DD/MM/YYYY vers YYYY-MM-DD
                    if '/' in date_str:
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            day, month, year = parts
                            # Corriger l'année si elle est sur 2 chiffres
                            if len(year) == 2:
                                year = f"20{year}"
                            elif len(year) == 4:
                                # Année déjà complète
                                pass
                            invoice_data["invoice_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            print(f"✅ Date de facture: {invoice_data['invoice_date']}")
                            break
                except Exception as e:
                    print(f"⚠️ Erreur parsing date {date_str}: {e}")
                    continue

    def _extract_client_info(self, text: str, invoice_data: Dict):
        """Extrait les informations du client."""
        print("👤 Extraction des informations client...")
        
        # Code client
        for pattern in self.ttn_patterns['client_code']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data["receiver"]["client_code"] = match.group(1)
                print(f"✅ Code client: {invoice_data['receiver']['client_code']}")
                break
        
        # Matricule fiscal
        for pattern in self.ttn_patterns['tax_id']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data["receiver"]["tax_id"] = match.group(1).upper()
                print(f"✅ Matricule fiscal: {invoice_data['receiver']['tax_id']}")
                break
        
        # Nom du client (extraction basique)
        lines = text.split('\n')
        for line in lines:
            if 'centre informatique' in line.lower() or 'complexe hached' in line.lower():
                # Nettoyer le nom du client
                client_name = re.sub(r'code\s*client\s*:?\s*[0-9]+', '', line, flags=re.IGNORECASE).strip()
                invoice_data["receiver"]["name"] = client_name
                print(f"✅ Nom client: {invoice_data['receiver']['name']}")
                break

    def _split_multiline_cell(self, cell_content: str) -> List[str]:
        """Sépare le contenu d'une cellule multi-lignes."""
        if not cell_content:
            return []
        
        # Séparer par les retours à la ligne
        lines = str(cell_content).split('\n')
        # Nettoyer et filtrer les lignes vides
        return [line.strip() for line in lines if line.strip()]

    def _safe_float_convert(self, value_str: str) -> float:
        """Convertit une chaîne en float de manière sécurisée."""
        if not value_str:
            return 0.0
        
        try:
            # Nettoyer la chaîne
            clean_str = str(value_str).strip().replace(',', '.')
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0

    def _extract_line_items(self, tables: List, invoice_data: Dict):
        """Extrait les lignes d'articles depuis les tableaux avec gestion des cellules multi-lignes."""
        print("📊 Extraction des lignes d'articles...")
        
        items = []
        
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue
                
            print(f"🔍 Analyse du tableau {table_idx + 1} avec {len(table)} lignes")
            
            # Afficher le contenu du tableau pour debug
            for row_idx, row in enumerate(table):
                if row:  # Seulement si la ligne n'est pas vide
                    print(f"   Ligne {row_idx}: {row}")
            
            # Chercher les lignes qui contiennent des données multi-lignes
            for row_idx, row in enumerate(table):
                if not row or len(row) < 4: # Minimum 4 colonnes pour description, qty, unit_price, line_total
                    continue
                
                # Nettoyer les cellules
                clean_row = [str(cell).strip() if cell else "" for cell in row]
                
                # Vérifier si c'est une ligne avec des données multi-lignes
                has_multiline = any('\n' in cell for cell in clean_row if cell)
                
                if has_multiline:
                    print(f"🔍 Ligne multi-lignes détectée: {clean_row}")
                    
                    # Séparer chaque cellule en lignes
                    split_cells = [self._split_multiline_cell(cell) for cell in clean_row]
                    
                    # Vérifier que nous avons des données
                    if not any(split_cells):
                        continue
                    
                    # Trouver le nombre maximum de lignes
                    max_lines = max(len(cell_lines) for cell_lines in split_cells if cell_lines)
                    
                    print(f"📊 {max_lines} articles détectés dans cette ligne")
                    
                    # Extraire chaque article
                    for line_idx in range(max_lines):
                        try:
                            # Extraire les données de chaque colonne pour cette ligne
                            description = ""
                            quantity = 1.0
                            unit_price = 0.0
                            line_total = 0.0
                            
                            # Description (colonne 0)
                            if len(split_cells) > 0 and line_idx < len(split_cells[0]):
                                description = split_cells[0][line_idx].replace('C. ', '').strip()
                            
                            # Quantité (colonne 1)
                            if len(split_cells) > 1 and line_idx < len(split_cells[1]):
                                quantity = self._safe_float_convert(split_cells[1][line_idx])
                            
                            # Prix unitaire (colonne 3 généralement)
                            if len(split_cells) > 3 and line_idx < len(split_cells[3]):
                                unit_price = self._safe_float_convert(split_cells[3][line_idx])
                            
                            # Total ligne (colonne 4 généralement)
                            if len(split_cells) > 4 and line_idx < len(split_cells[4]):
                                line_total = self._safe_float_convert(split_cells[4][line_idx])
                            
                            # Vérifier que nous avons des données valides
                            if description and (line_total > 0 or unit_price > 0):
                                item = {
                                    "description": description,
                                    "quantity": quantity,
                                    "unit_price": unit_price,
                                    "line_total": line_total if line_total > 0 else quantity * unit_price,
                                    "tax_rate": 0.0  # Pas de TVA sur les services TTN généralement
                                }
                                
                                items.append(item)
                                print(f"✅ Article {line_idx + 1}: {description} - {quantity} x {unit_price} = {item['line_total']}")
                            
                        except Exception as e:
                            print(f"⚠️ Erreur parsing article {line_idx + 1}: {e}")
                            continue
                
                # Vérifier aussi les lignes simples (sans multi-lignes)
                # Assurez-vous que le code de service est dans la première colonne
                elif clean_row and any(code in clean_row[0].upper() for code in ['SMTP', 'TCPAP', 'FGE', 'FSE']):
                    try:
                        description = clean_row[0].replace('C. ', '').strip()
                        quantity = self._safe_float_convert(clean_row[1]) if len(clean_row) > 1 else 1.0
                        unit_price = self._safe_float_convert(clean_row[3]) if len(clean_row) > 3 else 0.0
                        line_total = self._safe_float_convert(clean_row[4]) if len(clean_row) > 4 else 0.0
                        
                        if description and (line_total > 0 or unit_price > 0):
                            item = {
                                "description": description,
                                "quantity": quantity,
                                "unit_price": unit_price,
                                "line_total": line_total if line_total > 0 else quantity * unit_price,
                                "tax_rate": 0.0
                            }
                            
                            items.append(item)
                            print(f"✅ Article simple: {description} - {quantity} x {unit_price} = {item['line_total']}")
                        
                    except Exception as e:
                        print(f"⚠️ Erreur parsing ligne simple: {clean_row} - {e}")
                        continue
        
        invoice_data["items"] = items
        print(f"📦 Total articles extraits: {len(items)}")

    def _extract_totals_and_taxes(self, text: str, tables: List, invoice_data: Dict):
        """Extrait les totaux et informations de taxes."""
        print("💰 Extraction des totaux et taxes...")
        
        # Calculer le sous-total HT à partir des articles
        if invoice_data["items"]:
            invoice_data["subtotal_ht"] = sum(item["line_total"] for item in invoice_data["items"])
            print(f"✅ Total HT calculé: {invoice_data['subtotal_ht']:.3f}")
        
        # Chercher les totaux dans le texte et les tableaux
        text_lower = text.lower()
        
        # Chercher aussi dans les tableaux pour les taxes
        for table in tables:
            for row in table:
                if not row:
                    continue
                
                row_text = ' '.join(str(cell) for cell in row if cell).lower()
                
                # TVA
                tva_patterns = [
                    r'(?:t\.?v\.?a\.?|tva).*?([0-9,\.]+).*?([0-9,\.]+)', # Taux puis montant
                    r'([0-9,\.]+).*?(?:t\.?v\.?a\.?|tva).*?([0-9,\.]+)' # Montant puis taux (moins courant)
                ]
                
                for pattern in tva_patterns:
                    tva_match = re.search(pattern, row_text)
                    if tva_match and not any(tax["tax_type"] == "TVA" for tax in invoice_data["invoice_taxes"]):
                        try:
                            # Essayer de déterminer quel groupe est le taux et lequel est le montant
                            val1 = self._safe_float_convert(tva_match.group(1))
                            val2 = self._safe_float_convert(tva_match.group(2))
                            
                            # Le taux est généralement plus petit que le montant et <= 25%
                            if val1 > 0 and val1 <= 25 and val2 > val1:
                                tva_rate, tva_amount = val1, val2
                            elif val2 > 0 and val2 <= 25 and val1 > val2:
                                tva_rate, tva_amount = val2, val1
                            else: # Fallback si la logique de détection taux/montant est incertaine
                                tva_rate = 18.0 # Taux standard en Tunisie
                                tva_amount = max(val1, val2) # Prendre le plus grand comme montant
                            
                            invoice_data["invoice_taxes"].append({
                                "tax_type": "TVA",
                                "rate": tva_rate,
                                "amount": tva_amount
                            })
                            print(f"✅ TVA: {tva_rate}% = {tva_amount:.3f}")
                            break # Sortir après avoir trouvé la TVA
                        except Exception as e:
                            print(f"⚠️ Erreur parsing TVA: {e}")
                            pass
                
                # FODEC
                fodec_match = re.search(r'fodec.*?([0-9,\.]+)', row_text)
                if fodec_match and not any(tax["tax_type"] == "FODEC" for tax in invoice_data["invoice_taxes"]):
                    try:
                        fodec_amount = self._safe_float_convert(fodec_match.group(1))
                        invoice_data["invoice_taxes"].append({
                            "tax_type": "FODEC",
                            "rate": 1.0, # Taux FODEC standard
                            "amount": fodec_amount
                        })
                        print(f"✅ FODEC: 1.0% = {fodec_amount:.3f}")
                    except Exception as e:
                        print(f"⚠️ Erreur parsing FODEC: {e}")
                        pass
                
                # Droit de timbre
                timbre_match = re.search(r'(?:droit.*?de\s*)?timbre\s*([0-9,\.]+)', row_text)
                if timbre_match and not any(tax["tax_type"] == "Droit_Timbre" for tax in invoice_data["invoice_taxes"]):
                    try:
                        timbre_amount = self._safe_float_convert(timbre_match.group(1))
                        invoice_data["invoice_taxes"].append({
                            "tax_type": "Droit_Timbre",
                            "rate": 0.0, # Pas de taux pour le timbre fiscal
                            "amount": timbre_amount
                        })
                        print(f"✅ Droit de timbre: {timbre_amount:.3f}")
                    except Exception as e:
                        print(f"⚠️ Erreur parsing timbre: {e}")
                        pass
                
                # Total TTC
                ttc_patterns = [
                    r'total.*?(?:t\.?t\.?c\.?|ttc).*?([0-9,\.]+)',
                    r'([0-9,\.]+).*?total.*?(?:t\.?t\.?c\.?|ttc)'
                ]
                
                for pattern in ttc_patterns:
                    ttc_match = re.search(pattern, row_text)
                    if ttc_match and invoice_data["total_amount"] == 0.0:
                        try:
                            invoice_data["total_amount"] = self._safe_float_convert(ttc_match.group(1))
                            print(f"✅ Total TTC: {invoice_data['total_amount']:.3f}")
                            break # Sortir après avoir trouvé le total TTC
                        except Exception as e:
                            print(f"⚠️ Erreur parsing TTC: {e}")
                            pass
        
        # Calculer le total des taxes si non trouvé directement
        if invoice_data["total_taxes"] == 0.0:
            invoice_data["total_taxes"] = sum(tax["amount"] for tax in invoice_data["invoice_taxes"])
            if invoice_data["total_taxes"] > 0:
                print(f"✅ Total des taxes calculé: {invoice_data['total_taxes']:.3f}")
        
        # Si pas de total TTC trouvé, le calculer à partir du HT et des taxes
        if invoice_data["total_amount"] == 0.0:
            invoice_data["total_amount"] = invoice_data["subtotal_ht"] + invoice_data["total_taxes"]
            print(f"✅ Total TTC calculé: {invoice_data['total_amount']:.3f}")

    def _extract_ttn_references(self, text: str, invoice_data: Dict):
        """Extrait les références de validation TTN."""
        print("🔗 Extraction des références TTN...")
        
        # Chercher les longues références numériques (références de validation TTN)
        for pattern in self.ttn_patterns['ttn_reference']:
            matches = re.findall(pattern, text)
            if matches:
                # Prendre la plus longue référence trouvée
                longest_ref = max(matches, key=len)
                if len(longest_ref) >= 15:  # Les références TTN sont longues
                    invoice_data["ttn_validation_ref"] = longest_ref
                    print(f"✅ Référence TTN: {longest_ref}")
                    break

    def _print_extraction_summary(self, invoice_data: Dict):
        """Affiche un résumé de l'extraction."""
        print("\n" + "="*60)
        print("📋 RÉSUMÉ DE L'EXTRACTION")
        print("="*60)
        print(f"📄 Facture N°: {invoice_data.get('invoice_number', 'Non trouvé')}")
        print(f"📅 Date: {invoice_data.get('invoice_date', 'Non trouvée')}")
        print(f"👤 Client: {invoice_data['receiver'].get('name', 'Non trouvé')}")
        print(f"🆔 Code client: {invoice_data['receiver'].get('client_code', 'Non trouvé')}")
        print(f"🏛️ Matricule fiscal: {invoice_data['receiver'].get('tax_id', 'Non trouvé')}")
        print(f"📦 Nombre d'articles: {len(invoice_data.get('items', []))}")
        
        for i, item in enumerate(invoice_data.get('items', []), 1):
            print(f"   {i}. {item['description']} - {item['quantity']} x {item['unit_price']:.3f} = {item['line_total']:.3f} TND")
        
        print(f"💰 Sous-total HT: {invoice_data.get('subtotal_ht', 0):.3f} TND")
        
        for tax in invoice_data.get('invoice_taxes', []):
            print(f"🏛️ {tax['tax_type']}: {tax.get('rate', 0)}% = {tax['amount']:.3f} TND")
        
        print(f"💸 Total TTC: {invoice_data.get('total_amount', 0):.3f} TND")
        print(f"🔗 Référence TTN: {invoice_data.get('ttn_validation_ref', 'Non trouvée')}")
        print("="*60)

def prettify_xml(elem):
    """Retourne une chaîne XML joliment formatée."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def transform_to_teif_xml(data):
    """Transforme les données complètes en XML TEIF."""
    root = ET.Element("TEIFInvoice")
    root.set("xmlns", "http://www.tradenet.com.tn/teif/invoice/1.0")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:schemaLocation", "http://www.tradenet.com.tn/teif/invoice/1.0 teif_invoice_schema.xsd")

    # InvoiceHeader
    invoice_header = ET.SubElement(root, "InvoiceHeader")
    invoice_header.set("version", "1.0")
    message_id = f"TTN-{data.get('invoice_number', 'UNKNOWN')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ET.SubElement(invoice_header, "MessageId").text = message_id
    
    # Bgm
    bgm = ET.SubElement(root, "Bgm")
    ET.SubElement(bgm, "DocumentTypeCode").text = "380"
    ET.SubElement(bgm, "DocumentNumber").text = str(data.get("invoice_number", ""))
    
    # Dtm
    dtm_invoice = ET.SubElement(root, "Dtm")
    ET.SubElement(dtm_invoice, "DateTimeQualifier").text = "137"
    ET.SubElement(dtm_invoice, "DateTime").text = data.get("invoice_date", "")

    # PartnerSection - Supplier
    supplier_section = ET.SubElement(root, "PartnerSection")
    supplier_section.set("role", "supplier")
    
    supplier_nad = ET.SubElement(supplier_section, "Nad")
    ET.SubElement(supplier_nad, "PartyQualifier").text = "SU"
    ET.SubElement(supplier_nad, "PartyId").text = data["sender"].get("tax_id", "")
    ET.SubElement(supplier_nad, "PartyName").text = data["sender"].get("name", "")
    ET.SubElement(supplier_nad, "PartyAddress").text = data["sender"].get("address", "")
    
    # PartnerSection - Buyer
    buyer_section = ET.SubElement(root, "PartnerSection")
    buyer_section.set("role", "buyer")
    
    buyer_nad = ET.SubElement(buyer_section, "Nad")
    ET.SubElement(buyer_nad, "PartyQualifier").text = "BY"
    ET.SubElement(buyer_nad, "PartyId").text = data["receiver"].get("tax_id", "")
    ET.SubElement(buyer_nad, "PartyName").text = data["receiver"].get("name", "")
    ET.SubElement(buyer_nad, "PartyAddress").text = data["receiver"].get("address", "")

    # PytSection
    if data.get("payment_terms"):
        pyt_section = ET.SubElement(root, "PytSection")
        pyt = ET.SubElement(pyt_section, "Pyt")
        ET.SubElement(pyt, "PaymentTermsTypeCode").text = "1"
        ET.SubElement(pyt, "PaymentTermsDescription").text = data.get("payment_terms", "")

    # LinSection - Articles
    for line_index, item in enumerate(data.get("items", []), 1):
        lin_section = ET.SubElement(root, "LinSection")
        lin_section.set("lineNumber", str(line_index))
        
        # LinImd
        lin_imd = ET.SubElement(lin_section, "LinImd")
        ET.SubElement(lin_imd, "ItemDescriptionType").text = "F"
        ET.SubElement(lin_imd, "ItemDescription").text = item.get("description", "")
        
        # LinQty
        lin_qty = ET.SubElement(lin_section, "LinQty")
        ET.SubElement(lin_qty, "QuantityQualifier").text = "47"
        ET.SubElement(lin_qty, "Quantity").text = str(item.get("quantity", 0))
        ET.SubElement(lin_qty, "MeasureUnitQualifier").text = "PCE"
        
        # LinDtm
        lin_dtm = ET.SubElement(lin_section, "LinDtm")
        ET.SubElement(lin_dtm, "DateTimeQualifier").text = "137"
        ET.SubElement(lin_dtm, "DateTime").text = data.get("invoice_date", "")
        
        # LinTax
        lin_tax = ET.SubElement(lin_section, "LinTax")
        ET.SubElement(lin_tax, "DutyTaxFeeTypeCode").text = "VAT"
        ET.SubElement(lin_tax, "DutyTaxFeeRate").text = f"{item.get('tax_rate', 0.0):.2f}"
        
        # TaxPaymentDate
        tax_payment_date = ET.SubElement(lin_tax, "TaxPaymentDate")
        ET.SubElement(tax_payment_date, "DateTimeQualifier").text = "140"
        ET.SubElement(tax_payment_date, "DateTime").text = data.get("invoice_date", "")
        
        # LinMoa
        lin_moa = ET.SubElement(lin_section, "LinMoa")
        ET.SubElement(lin_moa, "MonetaryAmountTypeQualifier").text = "203"
        ET.SubElement(lin_moa, "MonetaryAmount").text = f"{item.get('line_total', 0.0):.3f}"
        ET.SubElement(lin_moa, "CurrencyCode").text = data.get("currency", "TND")
        
        # Rff
        rff = ET.SubElement(lin_moa, "Rff")
        ET.SubElement(rff, "ReferenceQualifier").text = "LI"
        ET.SubElement(rff, "ReferenceNumber").text = f"LINE-{line_index}"

    # InvoiceMoa
    invoice_moa = ET.SubElement(root, "InvoiceMoa")
    moa = ET.SubElement(invoice_moa, "Moa")
    ET.SubElement(moa, "MonetaryAmountTypeQualifier").text = "86"
    ET.SubElement(moa, "MonetaryAmount").text = f"{data.get('total_amount', 0.0):.3f}"
    ET.SubElement(moa, "CurrencyCode").text = data.get("currency", "TND")

    # InvoiceTax
    invoice_tax = ET.SubElement(root, "InvoiceTax")
    
    # Ajouter chaque taxe
    for tax_info in data.get("invoice_taxes", []):
        tax_element = ET.SubElement(invoice_tax, "Tax")
        ET.SubElement(tax_element, "DutyTaxFeeTypeCode").text = tax_info.get("tax_type", "VAT")
        if tax_info.get("rate", 0) > 0:
            ET.SubElement(tax_element, "DutyTaxFeeRate").text = f"{tax_info.get('rate', 0.0):.2f}"
        
        tax_moa = ET.SubElement(tax_element, "Moa")
        ET.SubElement(tax_moa, "MonetaryAmountTypeQualifier").text = "124"
        ET.SubElement(tax_moa, "MonetaryAmount").text = f"{tax_info.get('amount', 0.0):.3f}"
        ET.SubElement(tax_moa, "CurrencyCode").text = data.get("currency", "TND")

    # RefTtnVal
    ref_ttn_val = ET.SubElement(root, "RefTtnVal")
    reference = ET.SubElement(ref_ttn_val, "Reference")
    ET.SubElement(reference, "ReferenceQualifier").text = "AAK"
    ET.SubElement(reference, "ReferenceNumber").text = data.get("ttn_validation_ref", "")
    
    ref_date = ET.SubElement(reference, "ReferenceDate")
    ET.SubElement(ref_date, "DateTimeQualifier").text = "171"
    ET.SubElement(ref_date, "DateTime").text = datetime.now().strftime("%Y-%m-%d")

    # Signature
    signature_element = ET.SubElement(root, "Signature")
    signature_element.set("xmlns:ds", "http://www.w3.org/2000/09/xmldsig#")
    
    signed_info = ET.SubElement(signature_element, "ds:SignedInfo")
    ET.SubElement(signed_info, "ds:CanonicalizationMethod", Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    ET.SubElement(signed_info, "ds:SignatureMethod", Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")
    
    signature_value = ET.SubElement(signature_element, "ds:SignatureValue")
    signature_value.text = "PLACEHOLDER_SIGNATURE_ELECTRONIQUE_XADES_BASE64"
    
    key_info = ET.SubElement(signature_element, "ds:KeyInfo")
    ET.SubElement(key_info, "ds:X509Data").text = "PLACEHOLDER_CERTIFICAT_X509_BASE64"

    return prettify_xml(root)

def process_invoice(input_source: str, output_dir: str = "public/teif-invoices") -> str:
    """Traite une facture TTN et génère le fichier XML TEIF complet."""
    
    if input_source.endswith('.pdf'):
        print(f"🚀 Traitement de la facture TTN: {input_source}")
        extractor = TTNInvoiceExtractor()
        invoice_data = extractor.extract_from_pdf(input_source)
    else:
        raise ValueError("Seuls les fichiers PDF sont supportés")
    
    # Génération du XML TEI-F
    print("\n🔄 Génération du fichier TEI-F XML...")
    xml_content = transform_to_teif_xml(invoice_data)
    
    # Création du dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Génération du nom de fichier
    invoice_number = invoice_data.get('invoice_number', 'UNKNOWN')
    file_name = f"facture_ttn_{invoice_number}.xml"
    output_path = os.path.join(output_dir, file_name)

    # Écrire le fichier XML
    with open(output_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_content)
    
    print(f"✅ Facture TEI-F générée: {output_path}")
    print(f"📊 Taille du fichier: {os.path.getsize(output_path)} octets")
    
    # Sauvegarder aussi les données JSON pour debug
    json_path = output_path.replace('.xml', '_data.json')
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(invoice_data, json_file, indent=2, ensure_ascii=False)
    print(f"🔍 Données extraites sauvées: {json_path}")
    
    return output_path

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Extracteur complet pour factures TTN vers format TEI-F XML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemples d'utilisation:
  python ttn_invoice_processor.py facture_ttn.pdf
  python ttn_invoice_processor.py facture_ttn.pdf -o output/ --preview
        """
    )
    
    parser.add_argument('input', help="Fichier PDF de facture TTN")
    parser.add_argument('-o', '--output', default='public/teif-invoices', help="Dossier de sortie")
    parser.add_argument('--preview', action='store_true', help="Affiche un aperçu du XML généré")
    parser.add_argument('-v', '--verbose', action='store_true', help="Mode verbeux")
    
    args = parser.parse_args()
    
    try:
        output_path = process_invoice(args.input, args.output)
        
        if args.preview:
            print("\n" + "="*60)
            print("📄 APERÇU DU XML GÉNÉRÉ")
            print("="*60)
            with open(output_path, 'r', encoding='utf-8') as xml_file:
                lines = xml_file.readlines()
                for i, line in enumerate(lines[:30]):
                    print(f"{i+1:2d}: {line.rstrip()}")
                if len(lines) > 30:
                    print(f"... et {len(lines) - 30} lignes supplémentaires")
        
        print(f"\n🎉 Conversion terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
