"""Command Line Interface
======================
Interface en ligne de commande pour le convertisseur PDF vers TEIF.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict

# Ajouter le dossier parent au path pour les imports
# Assurez-vous que ce chemin est correct pour vos modules extractors, teif, utils
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importations des modules du projet
from extractors import PDFExtractor
from teif import TEIFGenerator
from utils import (
    validate_pdf_file,
    create_output_directory,
    log_extraction_summary,
    validate_teif_data,
    generate_unique_filename,
    sanitize_filename
)

class PDFToTEIFConverter:
    """Convertisseur principal PDF vers TEIF."""
    
    def __init__(self):
        """Initialise le convertisseur."""
        self.pdf_extractor = PDFExtractor()
        self.teif_generator = TEIFGenerator()
    
    def convert_pdf(self, pdf_path: str, output_dir: str = None, preview: bool = False, include_signature: bool = True, debug_json: bool = False) -> Dict:
        """
        Convertit un PDF en XML TEIF.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            output_dir: Dossier de sortie (optionnel)
            preview: Afficher un aperçu au lieu de sauvegarder
            include_signature: Ajouter les signatures XAdES
            debug_json: Sauvegarder les données extraites en JSON
            
        Returns:
            Chemin vers le fichier XML généré ou contenu XML si preview=True
        """
        # Validation du fichier PDF
        if not validate_pdf_file(pdf_path):
            raise ValueError(f"Fichier PDF invalide: {pdf_path}")
        
        print(f"📄 Traitement du fichier: {os.path.basename(pdf_path)}")
        
            # Extraction des données
        print("🔍 Extraction des données du PDF...")
        try:
            invoice_data = self.pdf_extractor.extract(pdf_path)
        except Exception as e:
            print(f"\n❌ Erreur lors de l'extraction: {str(e)}")
            raise        # Affichage du résumé d'extraction
        print(log_extraction_summary(invoice_data))
        
        # Sauvegarder les données extraites en JSON si demandé
        if debug_json:
            json_filename = sanitize_filename(f"extracted_data_{os.path.splitext(os.path.basename(pdf_path))[0]}.json")
            json_path = os.path.join(output_dir or os.getcwd(), json_filename)
            
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(invoice_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 Données extraites sauvegardées: {json_path}")
            
            # Si on ne fait que du debug, on s'arrête ici
            if preview:
                return {"status": "success", "json_file": json_path, "data": invoice_data}
        
        # Validation des données
        print("✅ Validation des données...")
        validation_errors = validate_teif_data(invoice_data)
        if validation_errors:
            print("⚠️  Avertissements de validation:")
            for error in validation_errors:
                print(f"   - {error}")
        
        # Préparation des données de signature si nécessaire
        if include_signature:
            print("🔐 Préparation des signatures électroniques...")
            signature_data = {
                "digest_value": "bCtqJZah+oGHv2z1bsUbJk2Q4/P+v0gFEvhr5I/is1E=",
                "signature_value": "DpyejsAd/4OP7uqlBvJKtBdOtWp0nuMAPf9TMi0TWBLLKM2SR61VTb49kdy37XTBVGaJTE7NaJ8J9OKbIXUH/Qm78jn7mjkvNqHliLBZ/WW1n1FU96v0IN+5mv6Pw18SvZGjLKgbwH4PMGZYSLfjtlZ8oJxHLLsVooBO0GzkjO3w05ykfeVvDJz89Fm+FbJh84pbNXp67WcBg4zu6HbCFidDXi653yaMrRDnhA3r4IxSi4bG8CkuzdDy6XUpK3/a0o69K07hg6S54NWao7Aw0TVQIc0B6BpnxytkA7cZ7AiPeHl9Xz8a5Lm5ytzxulYuFkz2pwAW6oWGzs6VzsJPoA==",
                "certificates": [
                    "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"
                ],
                "signing_certificate": {
                    "digest": "lNeILSzjoMfAGZWD/MvRYcvQ2tw=",
                    "issuer_serial": "MIGAMHSkcjBwMQswCQYDVQQGEwJUTjEOMAwGA1UEBwwFVHVuaXMxLjAsBgNVBAoMJU5hdGlvbmFsIERpZ2l0YWwgQ2VydGlmaWNhdGlvbiBBZ2VuY3kxITAfBgNVBAMMGFRuVHJ1c3QgUXVhbGlmaWVkIEdvdiBDQQIIBW0G+ewtTEA="
                },
                "signer_role": "CEO"
            }
        else:
            signature_data = None

        # Génération du XML TEIF
        print("🔧 Génération du XML TEIF...")
        try:
            teif_xml = self.teif_generator.generate_xml(invoice_data, signature_data)
        except Exception as e:
            raise Exception(f"Erreur lors de la génération XML: {e}")
        
        # Mode aperçu
        if preview:
            print("\n" + "="*50)
            print("APERÇU XML TEIF:")
            print("="*50)
            print(teif_xml)
            return teif_xml
        
        # Sauvegarde du fichier
        # MODIFICATION ICI : output_dir est maintenant garanti non-None par argparse
        # et sera un chemin absolu ou relatif valide.
        output_dir = create_output_directory(output_dir)
        
        # Génération du nom de fichier
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        xml_filename = generate_unique_filename(f"teif_{base_name}", "xml", output_dir)
        xml_path = os.path.join(output_dir, xml_filename)
        
        # Écriture du fichier
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(teif_xml)
        
        print(f"✅ Fichier TEIF généré: {xml_path}")
        return xml_path
    
    def convert_with_sample_data(self, output_dir: str = None, preview: bool = False) -> str:
        """
        Génère un XML TEIF avec des données d'exemple.
        
        Args:
            output_dir: Dossier de sortie
            preview: Mode aperçu
            
        Returns:
            Chemin vers le fichier ou contenu XML
        """
        print("📋 Génération avec données d'exemple...")
        
        # Données d'exemple basées sur une facture TTN réelle
        sample_data = {
            "invoice_number": "12016_2012",
            "invoice_date": "2024-01-15",
            "invoice_period_start": "2024-01-01",
            "invoice_period_end": "2024-01-31",
            "currency": "TND",
            "total_amount": 2.540,
            "amount_ht": 2.000,
            "tva_amount": 0.240,
            "tva_rate": 12.0,
            "gross_amount": 2.000,
            "stamp_duty": 0.300,
            "amount_in_words": "DEUX DINARS ET CINQ CENT QUARANTE MILLIMES",
            "sender": {
                "identifier": "0736202XAM000",
                "name": "Tunisie TradeNet",
                "tax_id": "B154702000",
                "address_desc": "Lotissement El Khalij Les Berges du Lac",
                "street": "Rue du Lac Malaren",
                "city": "Tunis",
                "postal_code": "1053",
                "country": "TN",
                "references": [
                    {"type": "I-815", "value": "B154702000"},
                    {"type": "I-816", "value": "SA"}
                ],
                "contacts": [
                    {
                        "identifier": "TTN",
                        "name": "Tunisie TradeNet",
                        "communication": {
                            "type": "I-101",
                            "value": "71 861 712"
                        }
                    },
                    {
                        "identifier": "TTN",
                        "name": "Tunisie TradeNet",
                        "communication": {
                            "type": "I-102",
                            "value": "71 861 141"
                        }
                    }
                ]
            },
            "receiver": {
                "identifier": "0914089JAM000",
                "name": "STE FRERE ET MOSAIQUE",
                "tax_id": "0914089J",
                "address_desc": "",
                "street": "",
                "city": "Salle publique Tunis",
                "postal_code": "1000",
                "country": "TN",
                "references": [
                    {"type": "I-81", "value": "0914089J"},
                    {"type": "I-811", "value": "SMTP"},
                    {"type": "I-813", "value": "Salle Publique"}
                ]
            },
            "payment_details": [
                {
                    "type_code": "I-114",
                    "description": "Les banques sont priees de payer au RIB suivant: 0410 5044 4047 0138 1036.",
                    "bank_details": None
                },
                {
                    "type_code": "I-115",
                    "description": "A Regler exclusivement au niveau des bureaux postaux sur presentation de la facture.",
                    "bank_details": {
                        "account_number": "0120021241115530",
                        "owner_id": "1B",
                        "bank_code": "0760",
                        "branch_code": "0760",
                        "bank_name": "La poste"
                    }
                }
            ],
            "items": [
                {
                    "code": "DDM",
                    "description": "Dossier DDM",
                    "quantity": 1.0,
                    "amount_ht": 2.000,
                    "amount_ttc": 2.000,
                    "tax_rate": 12.0
                }
            ],
            "ttn_reference": "073620200053562920196810312",
            "cev_reference": "iVBORw0KGgoAAAANSUhEUgAAASwAAAEsAQAAAABRBrPYAAAFmElEQVR42u2aQa6jSgxFjRjUjGwAqbZRM7ZENgDJBmBLzGobSGwAZgxK8T8mo6R78L9UNfp5Qq0X+kSqxvb1tWnRf/Ozyw/7YT/sh/2w/xMm4rb5XAcnjav3bm06fWqtsRXxxTDPnaHbXs4/z7VauJPup4wxjVoOa6u4zbF+dfUR27u2twV+e3Spd0UxqeLaO46nzyU1oRXXjktpTKegeyd2yDP10t7jpmdbErMoNNL24vdum2Qj7jvfcn8JVj6MfOMwf7n+SMuMGD/b5Npb9Eesd8fZAFYS4I8CzIhJtbT8268oJHHcrp+6jnw3lMPWPqTxVOWK+rSa8vNZz5TYUg7TyW3UVHXK0BHxlSRvXJIg9+iLYXKz49UHhRwT5TyIPzgbl5bDUuO2vUtDJ+Oix0KVISAU2vp5tsxY34kEvzs/R311a8W9Re7kW9RiGB83XVZT6UCO0SAQLp06uX9XfUZMxjM1/HqSZu1N/dTZzUHIhHIYktVajoXtWNL9kmjg3UJTEBs61FJfopPoI7z7EQcmIuUw2hB30hjVlFn8rOl2AqShILY9wvbqWjDCzTkt4jT9c7vCUQhrUcs7NaVcay9r3xF95FpuS0FsPFFpuu16i/Vxmlw/43rlQDlse6CQgjjXs/VfKy7islNfX1HIiSmxHtFMc1P+ULmf/kEGhnoqiPkHObZwGHM1z2UVQau3l0j1EYW8WFvR3B2nMsEk5+8WBan4KAUx0//ICfmlfkiqcMsuDaHtP6s+K4btF5sCaA1BZ3PI3jzGYqcthplP41Hs9tjXO25cWnPLgq8rh2H7PZk2Of9Wy75DLeGxGVoOOxbLLgnraFYcA0n3R8Tq6fNsWTHaKxItVPRMkivnBE6DKZiWwxgBJutENQd7OKKQbhQ49saVw+hB643jmaupX4EuTznXWI5Pic6L2bxDn0Wp4Pugl2s1s9F8FmBWjMpNFDKxZnTlr3a64UIH5CqH4Wo2C72zeec4LeKzmlMdQjnMIj4F/wqW7XTAwcwGmsnXtRhGglnxIhrjIozt8zVj9ja2+2KYNfdHsFijzHetJ7tN7n3vQ7JitDw8uTlVBkkiTsox1d5NTMphVFN7Tcoes2qriYCXY8iy8acYhlASCOZHooCYbEx5DCBN+GM1kRNjNifT9EET7MxQTRTaycPhz3IYHbDWmOi8IqswSwq2ygbMPxplRqx+mkrrcdJ8FRnBzxxKa/CfI09ebK0ijd6WTjjzp9rGoLHV05eryYv5az9gbsr2Eh1HxaUzzGJyymGWbI1DuIgCGb5xTnrfThS+hSsjxsRh09wuFxCYJb1JqG7zx2oiM4ZGYb+PiDNHnFPvbGM5BUuGYhjW1BbCGMXRFjLoZDuYiMlNy2EYVDogEs19Sjg11JdbkRQJ5TCmj3Vc2kF4GlfuLTrjVPXa75XCTP+fWKlgammuNVj6vf1VMcwskwkIviJemWDLH7QLlfbFMNuL4k4bbIzT99Qj13KvigWxV6AdeHw4z8FcjdgrlfFyyAUx9Dnabu254C7IPXudsYf6c92UF9NDrReYG3fIyDVencSd6GgxTMaIeUu9JcB6PX/GZ9X3XrEUhmLY+7ibbrak1WS7l1gTl+lr6ZcT48mn6qwfzpL8dUXhahPtUBAj2Ta10MvlncSef+CZ+MdnsLJil/9fmF7N1VSR6DP7oNvfC6Ks2HtRcLm4iGqtlW1+alsEfb+oyojZrDE4osB50njSlWwX9MLVhHKYvUeY4/borIQnJ0xY10TpP9tuXsxes9LyGieV3SMKfMR12G6tJGarCTSEJ2AOCg2JnO1rWZodY1onEPb65uC226i13n1tfvJiZozNPhHopb2ZpFBZDFxfEp0X4wnYIMAUOXQMdGsV3y+MGDPLYb//bfLDftgP+2E/7D9h/wDXxRRC2h7o9AAAAABJRU5ErkJggg=="
        }
        
        print(log_extraction_summary(sample_data))
        
        # Génération XML
        teif_xml = self.teif_generator.generate_xml(sample_data)
        
        if preview:
            print("\n" + "="*50)
            print("APERÇU XML TEIF (DONNÉES EXEMPLE):")
            print("="*50)
            print(teif_xml)
            return teif_xml
        
        # Sauvegarde
        # MODIFICATION ICI : output_dir est maintenant garanti non-None par argparse
        output_dir = create_output_directory(output_dir)
        xml_filename = generate_unique_filename("teif_sample", "xml", output_dir)
        xml_path = os.path.join(output_dir, xml_filename)
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(teif_xml)
        
        print(f"✅ Fichier TEIF exemple généré: {xml_path}")
        return xml_path

def main():
    """Point d'entrée principal du CLI."""
    parser = argparse.ArgumentParser(
        description="Convertisseur PDF vers TEIF XML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemples d'utilisation:
  %(prog)s facture.pdf                     # Conversion simple
  %(prog)s facture.pdf -o ./output         # Spécifier dossier de sortie
  %(prog)s facture.pdf --preview           # Aperçu sans sauvegarde
  %(prog)s --sample                        # Générer avec données d'exemple
  %(prog)s --sample --preview              # Aperçu des données d'exemple
        """
    )
    
    # Arguments principaux
    parser.add_argument(
        'pdf_file',
        nargs='?',
        help='Fichier PDF à convertir'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        default=os.getcwd(), # MODIFICATION ICI : Définit le répertoire courant comme défaut
        help='Dossier de sortie pour le fichier XML (défaut: répertoire courant)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Afficher un aperçu du XML au lieu de le sauvegarder'
    )
    
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Générer un XML avec des données d\'exemple'
    )
    
    parser.add_argument(
        '--no-sign',
        action='store_true',
        help='Ne pas inclure les signatures électroniques dans le XML'
    )
    
    parser.add_argument(
        '--debug-json',
        action='store_true',
        help='Sauvegarder les données extraites en JSON pour débogage'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='PDF to TEIF Converter v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validation des arguments
    if not args.sample and not args.pdf_file:
        parser.error("Vous devez spécifier un fichier PDF ou utiliser --sample")
    
    if args.sample and args.pdf_file:
        parser.error("Vous ne pouvez pas utiliser --sample avec un fichier PDF")
    
    # Initialisation du convertisseur
    converter = PDFToTEIFConverter()
    
    try:
        # MODIFICATION ICI : Assurez-vous que output_dir est un chemin absolu
        # avant de le passer aux méthodes de conversion.
        final_output_dir = os.path.abspath(args.output_dir)

        if args.sample:
            # Mode données d'exemple
            result = converter.convert_sample_data(
                output_dir=final_output_dir,
                preview=args.preview,
                include_signature=not args.no_sign,
                debug_json=args.debug_json
            )
        else:
            result = converter.convert_pdf(
                pdf_path=args.pdf_file,
                output_dir=final_output_dir,
                preview=args.preview,
                include_signature=not args.no_sign,
                debug_json=args.debug_json
            )
        
        if not args.preview:
            print(f"\n🎉 Conversion terminée avec succès!")
            print(f"📁 Fichier généré: {result}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}", file=sys.stderr)
        sys.exit(1)

# Note: Le if __name__ == "__main__": est dans le main.py racine
# et appelle cette fonction main.
