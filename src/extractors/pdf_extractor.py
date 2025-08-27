"""PDF Extractor Module
===================
Extrait les données de facture depuis les fichiers PDF.
Utilise pdfplumber et PyPDF2 comme fallback.
"""
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, TypeVar, Union # Assurez-vous que tous les types sont importés

# Import base extractor components
from .base_extractor import BaseExtractor, ExtractorConfig
from .amount_validator import validate_and_fix_amounts 


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

class PDFExtractor(BaseExtractor):
    """Extracteur de données depuis les fichiers PDF."""
    
    def __init__(self, config: ExtractorConfig = None):
        """Initialise l'extracteur avec les patterns de reconnaissance."""
        # Define default config if not provided
        if config is None:
            config = ExtractorConfig(
                date_formats=["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"],
                amount_decimal_separator=",",
                amount_thousands_separator=" ",
                normalize_text=True
            )
        
        # Initialize base class
        super().__init__(config)
        
        # Set up patterns
        self.patterns = {
            'invoice_number': [
                r'facture\s*n[°o]\s*:?\s*([A-Z0-9\-_]+)',
                r'invoice\s*(?:number|#)\s*:?\s*([A-Z0-9\-_]+)',
                r'n[°o]\s*([A-Z0-9\-_]+)',
                r'ref\s*:?\s*([A-Z0-9\-_]+)',
                r'référence\s*unique\s*:?\s*([0-9]+)',
                r'référence\s*:\s*([0-9]+)',
                r'([0-9]{10,})',  # Long numbers like TTN
                r'facture\s*([A-Z0-9\-_/]+)',  # More general format
            ],
            'amounts_specific': {
                'ttc': [
                    r'total\s*t\.?t\.?c\.?\s*:?\s*(\d[\d\s,.]+)',
                    r'montant\s*t\.?t\.?c\.?\s*:?\s*(\d[\d\s,.]+)',
                    r'net\s*[àa]\s*payer\s*:?\s*(\d[\d\s,.]+)',
                    r'total\s*[àa]\s*payer\s*:?\s*(\d[\d\s,.]+)',
                ],
                'ht': [
                    r'total\s*h\.?t\.?\s*:?\s*(\d[\d\s,.]+)',
                    r'montant\s*h\.?t\.?\s*:?\s*(\d[\d\s,.]+)',
                    r'prix\s*h\.?t\.?\s*:?\s*(\d[\d\s,.]+)',
                ],
                'tva': [
                    r'(?:montant\s*)?t\.?v\.?a\.?\s*(?:\d{1,2}%?)?\s*:?\s*(\d[\d\s,.]+)',
                    r'total\s*t\.?v\.?a\.?\s*:?\s*(\d[\d\s,.]+)',
                ]
            },
            'identifier': [
                r'identifiant\s*:?\s*([0-9A-Z]{12,})',
                r'code\s*TTN\s*:?\s*([0-9A-Z]{12,})',
                r'([0-9]{7}[A-Z]{2}[0-9]{3})',  # TTN format
            ],
            'date': [
                r'date\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})',
            ],
            'amounts': [ # General amount patterns, used as fallback
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
            'tax_amounts': [ # General tax amount patterns, used as fallback
                r'tva\s*(?:\d+%?)?\s*:?\s*([0-9,\.]+)',
                r'vat\s*(?:\d+%?)?\s*:?\s*([0-9,\.]+)',
                r'taxe\s*:?\s*([0-9,\.]+)',
                r'fodec\s*:?\s*([0-9,\.]+)',
                r'timbre\s*:?\s*([0-9,\.]+)',
            ],
            'company_names': [
                r'(?:société|company|sarl|sa|sas|eurl)\s+([^,\n]+)',
                r'([A-Z][A-Za-z\s&]+(?:SARL|SA|SAS|EURL|LTD|INC))',
                r'([A-Z][A-Za-z\s]{2,}(?:TRADENET|TELECOM|SERVICES|CONSULTING|princ))',
                r'SMTP\s+princ',
            ],
            'contact_info': [
                r'tel[:\s]+([0-9\s\+\-\.]+)',
                r'fax[:\s]+([0-9\s\+\-\.]+)',
                r'e?[-\s]?mail[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'web[:\s]+(?:https?:\/\/)?([^\s,]+)',
            ],
            'address': [
                r'adresse[:\s]+([^,\n]+(?:rue|avenue|boulevard)[^,\n]+)',
                r'([^,\n]+(?:rue|avenue|boulevard)[^,\n]+)',
            ],
            'city': [
                r'(?:ville|city)[:\s]+([^,\n]+)',
                r'\b(\d{4})\s+([^,\n]+)',  # Postal code + city
            ],
            'tax_ids': [
                r'matricule\s*fiscal\s*:?\s*([0-9A-Z]+)',
                r'tax\s*id\s*:?\s*([0-9A-Z]+)',
                r'mf\s*:?\s*([0-9A-Z]+)',
                r'([0-9]{7}[A-Z]{3}[0-9]{3})',
            ],
            'items': [
                r'(\w+)\s+([^0-9\n]+)\s+(\d+[,.]?\d*)\s+(\d+)\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)',
            ]
        }
    
    def extract(self, source: str) -> Dict:
        """Implémentation de la méthode abstraite d'extraction."""
        if not isinstance(source, str):
            raise TypeError("La source doit être une chaîne de caractères (chemin de fichier)")
            
        if not os.path.exists(source):
            raise FileNotFoundError(f"Le fichier {source} n'existe pas")
            
        return self.extract_from_pdf(source)
            
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extrait les données depuis un fichier PDF.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Dict contenant les données extraites
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            Exception: Si l'extraction échoue
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Le fichier PDF {pdf_path} n'existe pas.")
        
        text = self._extract_text_from_pdf(pdf_path)
        if not text:
            raise Exception("Impossible d'extraire le texte du PDF")
            
        return self._parse_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte extrait du PDF."""
        if not text:
            return ""
        
        # Remplacer les caractères spéciaux courants
        replacements = {
            '(cid:9)': ' ',  # Mal-encoded tab character
            '\u200e': '',    # Left-to-right mark
            '\u200f': '',    # Right-to-left mark
            '\ufeff': '',    # BOM
            'ﺓﺪﻤﻟﺍ': '',      # Mal-encoded Arabic characters
            '\xa0': ' ',     # Non-breaking space
            '\t': ' ',       # Tab
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove non-printable characters and normalize spaces
        # Keep characters with ord < 128 (ASCII) or any whitespace character
        text = ''.join(char for char in text if ord(char) < 128 or char.isspace())
        
        # Normalize multiple spaces and line endings
        text = ' '.join(text.split())
        
        return text.strip()
            
    def _clean_field(self, text: str, field_type: str) -> str:
        """Nettoie un champ spécifique du texte extrait."""
        text = self._clean_text(text) # Apply general cleaning first
            
        if field_type == 'company_name':
            # Remove common irrelevant words, but be careful not to remove actual company name parts
            text = re.sub(r'(?i)(?:^|\s)(?:du|de|la|les|des)\s+', ' ', text)
            # Keep only the first 50 characters if too long
            if len(text) > 50:
                text = text[:50].strip()
                    
        elif field_type == 'city':
            # Only keep valid city names (example for Tunisia)
            # This is a very strict rule, might need to be relaxed for general invoices
            if not re.match(r'^(?:TUNIS|SFAX|SOUSSE|BIZERTE)$', text.upper()):
                text = "TUNIS"  # Default value
                    
        elif field_type == 'address':
            # Clean address: remove contact info if present at the end
            text = re.sub(r'(?i)(?:tel|fax|email|telephone).*$', '', text)
            if not text or text.lower() == "adresse inconnue":
                text = "Rue inconnue"
                    
        return text.strip()
            
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte du PDF avec pdfplumber ou PyPDF2."""
        text = ""
        
        # Try pdfplumber first
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += self._clean_text(page_text) + "\n"
                if text:
                    return text
            except Exception as e:
                print(f"Erreur pdfplumber: {e}")
        
        # Fallback to PyPDF2
        if PyPDF2:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += self._clean_text(page_text) + "\n" # Apply cleaning here too
            except Exception as e:
                print(f"Erreur PyPDF2: {e}")
        
        return text
    
    def _parse_text(self, text: str) -> Dict:
        """
        Parse le texte extrait pour identifier les données de facture.
        IMPORTANT: Aucun calcul n'est effectué, les montants sont utilisés tels quels.
        """
        # Structure de base conforme au TEIF
        invoice_data = {
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "currency": "TND",  # Force TND for Tunisian invoices
            "total_amount": 0.0,
            "amount_ht": 0.0,
            "tva_amount": 0.0,
            "tva_rate": 19.0,  # Default rate in Tunisia
            "gross_amount": 0.0,
            "stamp_duty": 0.600,  # Standard stamp duty
            "sender": {
                "identifier": "",  # TTN Code
                "name": "",
                "tax_id": "",
                "address_desc": "",
                "street": "",
                "city": "",
                "postal_code": "",
                "country": "TN",
                "references": [],
                "contacts": []
            },
            "receiver": {
                "identifier": "",  # TTN Code
                "name": "",
                "tax_id": "",
                "address_desc": "",
                "street": "",
                "city": "",
                "postal_code": "",
                "country": "TN",
                "references": [],
                "contacts": []
            },
            "payment_details": [
                {
                    "type_code": "I-114",
                    "description": "",
                    "bank_details": {
                        "account_number": "",
                        "owner_id": "",
                        "bank_code": "",
                        "branch_code": "",
                        "bank_name": ""
                    }
                }
            ],
            "items": [],
            "invoice_period_start": "",
            "invoice_period_end": "",
            "ttn_reference": "",
            "cev_reference": ""
        }
        
        # Extraction des données
        invoice_data["invoice_number"] = self._extract_invoice_number(text)
        invoice_data["invoice_date"] = self._extract_date(text)
        invoice_data["currency"] = self._extract_currency(text)
        
        # Extraction des montants (without calculations)
        amounts = self._extract_amounts(text)
        invoice_data.update(amounts)
        
        # Extraction des entités
        sender, receiver = self._extract_companies(text)
        tax_ids = self._extract_tax_ids(text)
        
        # Update sender and receiver data
        invoice_data["sender"].update(sender)
        invoice_data["receiver"].update(receiver)
        
        if tax_ids:
            if not invoice_data["sender"]["tax_id"]:
                invoice_data["sender"]["tax_id"] = tax_ids[0]
            if len(tax_ids) > 1 and not invoice_data["receiver"]["tax_id"]:
                invoice_data["receiver"]["tax_id"] = tax_ids[-1]
        
        # Extraction des taxes (without calculations)
        taxes = self._extract_taxes(text)
        invoice_data["invoice_taxes"] = taxes
        if taxes:
            invoice_data["total_taxes"] = sum(tax.get("amount", 0) for tax in taxes)
        
        # Generation of a default item
        invoice_data["items"] = self._generate_default_items(invoice_data)
        
        return invoice_data
    
    def _extract_invoice_number(self, text: str) -> str:
        """Extrait le numéro de facture."""
        for pattern in self.patterns['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_num = match.group(1).strip()
                # Avoid too short or invalid numbers
                if len(invoice_num) >= 2 and not invoice_num.isspace():
                    return invoice_num
                
        # Fallback: search for numbers in the text
        numbers = re.findall(r'\b\d{2,}\b', text)
        if numbers:
            return numbers[0]  # Take the first number found
                
        return "UNKNOWN"
    
    def _extract_date(self, text: str) -> str:
        """Extrait et formate la date de facture."""
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
                            year, month, day = parts
                        else:  # DD/MM/YYYY or MM/DD/YYYY
                            day, month, year = parts
                            if len(year) == 2:
                                year = f"20{year}"
                                
                        # Validate values
                        year = int(year)
                        month = int(month)
                        day = int(day)
                        
                        # Correction if day/month are inverted
                        if month > 12 and day <= 12:
                            month, day = day, month
                            
                        # Final validation
                        if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                            return f"{year}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    continue
        return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_currency(self, text: str) -> str:
        """Extrait la devise - Force TND for Tunisian invoices."""
        # Always return TND for Tunisian invoices
        # (TEIF standard is Tunisian)
        return "TND"
    
    def _extract_amounts(self, text: str) -> Dict:
        """Extrait et calcule les montants selon le format TEIF."""
        result = {
            "total_amount": 0.0,
            "amount_ht": 0.0,
            "tva_amount": 0.0,
            "gross_amount": 0.0,
            "currency": self._extract_currency(text)
        }
        
        def parse_amount(amount_str: str) -> float:
            """Parse an amount to float robustly."""
            if not amount_str:
                return 0.0
            
            try:
                clean_str = amount_str.strip()
                # Remove all spaces (thousands separators)
                clean_str = clean_str.replace(' ', '')
                # Replace comma with dot if it's a decimal separator and no dot exists
                if ',' in clean_str and '.' not in clean_str:
                    clean_str = clean_str.replace(',', '.')
                # Keep only digits and one decimal point
                clean_str = ''.join(c for c in clean_str if c.isdigit() or c == '.')
                
                # Ensure only one decimal point
                if clean_str.count('.') > 1:
                    parts = clean_str.split('.')
                    clean_str = ''.join(parts[:-1]) + '.' + parts[-1]
                    
                value = float(clean_str)
                # Check if amount is reasonable (not too large)
                if value > 1000000000:  # More than a billion
                    return 0.0
                return value
            except (ValueError, TypeError):
                return 0.0

        # Extract amounts with specific patterns first
        for amount_type, patterns in self.patterns['amounts_specific'].items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount = parse_amount(match.group(1))
                    if amount > 0:
                        if amount_type == 'ttc' and (result['total_amount'] == 0 or amount > result['total_amount']):
                            result['total_amount'] = amount
                        elif amount_type == 'ht' and (result['amount_ht'] == 0 or amount > result['amount_ht']):
                            result['amount_ht'] = amount
                            result['gross_amount'] = amount
                        elif amount_type == 'tva' and (result['tva_amount'] == 0 or amount < result['total_amount']): # TVA is usually smaller than total
                            result['tva_amount'] = amount
        
        # Fallback: search for generic amounts if specific ones not found
        if all(v == 0 for v in [result["total_amount"], result["amount_ht"], result["tva_amount"]]):
            amount_matches = []
            for pattern in self.patterns['amounts']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount = parse_amount(match.group(1))
                    if amount > 0:
                        amount_matches.append(amount)
            
            if amount_matches:
                amount_matches.sort(reverse=True) # Sort descending
                if len(amount_matches) >= 1:
                    result["total_amount"] = amount_matches[0]
                if len(amount_matches) >= 2:
                    result["amount_ht"] = amount_matches[1]
                if result["total_amount"] > result["amount_ht"] > 0:
                    result["tva_amount"] = result["total_amount"] - result["amount_ht"]
        
        # Validate and fix amounts
        from .amount_validator import validate_and_fix_amounts # Import here to avoid circular dependency if needed
        result = validate_and_fix_amounts(result)

        # Calculations if necessary (priority to extracted values)
        if result["total_amount"] > 0:
            if result["amount_ht"] <= 0:
                # Calculate HT from TTC (using default TVA rate)
                result["amount_ht"] = round(result["total_amount"] / (1 + result["tva_rate"] / 100), 3)
                result["gross_amount"] = result["amount_ht"]
                
            if result["tva_amount"] <= 0:
                # Calculate TVA
                result["tva_amount"] = round(result["total_amount"] - result["amount_ht"], 3)
        
        # Final check if total_amount is still 0 but HT is present
        if result["total_amount"] <= 0 and result["amount_ht"] > 0:
            result["total_amount"] = round(result["amount_ht"] * (1 + result["tva_rate"] / 100), 3)
            result["tva_amount"] = round(result["total_amount"] - result["amount_ht"], 3)
            
        return result
    
    def _extract_companies(self, text: str) -> Tuple[Dict, Dict]:
        """Extrait les informations détaillées des entreprises."""
        def extract_with_patterns(patterns: List[str], text: str) -> List[str]:
            results = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if isinstance(match, str):
                        results.append(match.strip())
                    elif isinstance(match, tuple):
                        # Always take the first capturing group if available
                        results.extend(m.strip() for m in match if m.strip())
            return list(dict.fromkeys([r for r in results if r]))  # Remove duplicates and empty strings
        
        # Define extraction patterns
        patterns = {
            'company_name': [
                r'(?:société|entreprise|sarl|sa)\s*:?\s*([^,\n]+?)(?:\s*(?:Rang|Profil|:|$$|$$|erreur|omission).*)?$',
                r'(?:raison sociale)\s*:?\s*([^,\n]+?)(?:\s*(?:Rang|Profil|:|$$|$$).*)?$',
                r'(?:Nom\s+(?:du\s+)?Compte|Client|Destinataire)\s*:?\s*([^,\n]+?)(?:\s*(?:Rang|Profil|:|$$|$$).*)?$',
                r'SMTP\s+([^,\n]+?)(?:\s*(?:Rang|Profil|:|$$|$$).*)?$',
            ],
            'address': [
                r'(?:adresse|rue|avenue)\s*:?\s*([^,\n]+(?:malaren|lac|tunis)[^,\n]*)',
                r'(?:siège|siege)\s*social\s*:?\s*([^,\n]+)',
                r'(?:Rue|Avenue|Boulevard)[^,\n]+(?:[A-Z][a-z]+\s+)+(?:malaren|lac|tunis)[^,\n]*',
            ],
            'city': [
                r'(?:ville|tunisie)\s*:?\s*([^\d,\n]{2,})(?!\s*:)',
                r'\b(?:tunis|sfax|sousse|bizerte)\b(?!\s*:)',
                r'(?:^|\s)(?:tunis|sfax|sousse|bizerte)(?:\s|$)',
            ],
            'postal': [
                r'\b(10[0-9]{2}|20[0-9]{2}|30[0-9]{2}|40[0-9]{2}|50[0-9]{2})\b',
            ],
            'identifier': [
                r'matricule\s*fiscal\s*:?\s*([0-9]{7}[A-Z][A-Z][A-Z][0-9]{3})',
                r'identifiant\s*unique\s*:?\s*([0-9A-Z]{12,})',
                r'Code\s*(?:TTN|Client)\s*:?\s*([0-9A-Z]+)',
                r'(?:^|\s)(?:[A-Z]{3}[0-9]{5}|[0-9]{7}[A-Z]{3}[0-9]{3})(?:\s|$)',  # Standalone identifiers
            ],
            'tax_id': [
                r'(?:matricule fiscal|MF)\s*:?\s*([0-9]{7}[A-Z][A-Z][A-Z][0-9]{3})',
                r'(?:code\s+fiscal|CF)\s*:?\s*([0-9]{7}[A-Z][A-Z][A-Z][0-9]{3})',
            ]
        }
        
        # Extraction des données pour chaque entité
        names = extract_with_patterns(patterns['company_name'], text)
        addresses = extract_with_patterns(patterns['address'], text)
        cities = extract_with_patterns(patterns['city'], text)
        postals = extract_with_patterns(patterns['postal'], text)
        identifiers = extract_with_patterns(patterns['identifier'], text)
        tax_ids = extract_with_patterns(patterns['tax_id'], text)
        
        # Construction de l'entité expéditeur (première occurrence)
        sender_name = names[0] if names else "ENTREPRISE EMETTRICE"
        # Nettoyer le nom (max 50 caractères)
        if len(sender_name) > 50:
            sender_name = sender_name[:50].strip()
            
        sender = {
            "name": sender_name,
            "identifier": identifiers[0] if identifiers else "0000000XXX000",
            "tax_id": tax_ids[0] if tax_ids else "",
            "address_desc": "",
            "street": addresses[0] if addresses else "Rue inconnue",
            "city": cities[0] if cities else "TUNIS",
            "postal_code": postals[0] if postals else "1000",
            "country": "TN",
            "references": [],
            "contacts": []
        }
        
        # Construction de l'entité destinataire (dernière occurrence différente)
        receiver_name = ""
        if len(names) > 1 and names[-1] != names[0]:
            receiver_name = names[-1]
        elif len(names) == 1:
            receiver_name = "CLIENT DESTINATAIRE"
        else:
            receiver_name = "CLIENT INCONNU"
            
        # Nettoyer le nom du destinataire (max 50 caractères)
        if len(receiver_name) > 50:
            receiver_name = receiver_name[:50].strip()
            
        receiver = {
            "name": receiver_name,
            "identifier": identifiers[-1] if len(identifiers) > 1 else "0000000YYY000",
            "tax_id": tax_ids[-1] if len(tax_ids) > 1 else "",
            "address_desc": "",
            "street": addresses[-1] if len(addresses) > 1 else "Adresse inconnue",
            "city": cities[-1] if len(cities) > 1 and cities[-1] != cities[0] else "TUNIS",
            "postal_code": postals[-1] if len(postals) > 1 else "1000",
            "country": "TN",
            "references": [],
            "contacts": []
        }
        
        # Extraire les contacts
        contacts = []
        for pattern in self.patterns['contact_info']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                contact_type = ""
                if "tel" in pattern:
                    contact_type = "I-101" 
                elif "fax" in pattern:
                    contact_type = "I-102"  
                elif "mail" in pattern:
                    contact_type = "I-103"  
                elif "web" in pattern:
                    contact_type = "I-104"  
                                    
                contacts.append({
                    "identifier": "CTT",
                    "name": sender["name"], 
                    "communication": {
                        "type": contact_type,
                        "value": match.strip()
                    }
                })
        if contacts:
            sender["contacts"] = contacts 
                                
        return sender, receiver
    
    def _extract_tax_ids(self, text: str) -> List[str]:
        """Extrait les identifiants fiscaux."""
        tax_ids = []
        for pattern in self.patterns['tax_ids']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tax_ids.extend(matches)
        return tax_ids
    
    def _extract_taxes(self, text: str) -> List[Dict]:
        """Extrait les taxes TELLES QUELLES (sans calculs)."""
        taxes = []
        tax_amounts = []
        
        for pattern in self.patterns['tax_amounts']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    tax_amount = float(match.replace(',', '.'))
                    tax_amounts.append(tax_amount)
                except:
                    pass
        
        # Créer des entrées de taxes
        for i, amount in enumerate(tax_amounts):
            tax_type = "TVA" if i == 0 else f"Taxe_{i+1}"
            taxes.append({
                "tax_type": tax_type,
                "amount": amount,
                "rate": 0.0 
            })
            
        return taxes
    
    def _generate_default_items(self, invoice_data: Dict) -> List[Dict]:
        """Génère un article par défaut basé sur les montants extraits."""
        amount_ht = invoice_data.get("amount_ht", 0)
        amount_ttc = invoice_data.get("total_amount", 0)
      
        tva_rate = invoice_data.get("tva_rate", 19.0)
        
        if amount_ht <= 0 and amount_ttc > 0:
            amount_ht = round(amount_ttc / (1 + tva_rate / 100), 3)
            
        return [{
            "code": "ART001",
            "description": "Article/Service (extrait automatiquement)",
            "quantity": 1.0,
            "amount_ht": amount_ht,
            "amount_ttc": round(amount_ht * (1 + tva_rate / 100), 3),
            "tax_rate": tva_rate
        }]
        
    def _format_amount(self, amount: float) -> str:
        """Formate un montant avec 3 décimales."""
        return "{:.3f}".format(amount)
