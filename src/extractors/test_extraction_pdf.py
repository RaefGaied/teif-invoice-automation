# test_extraction_pdf.py
import os
import sys
import glob
from pathlib import Path

from src.extractors.base_extractor import ExtractorConfig
from src.extractors.pdf_extractor import PDFExtractor


def get_pdf_paths(directory="."):
    """Retourne la liste des fichiers PDF dans le répertoire spécifié."""
    return list(Path(directory).glob("**/*.pdf"))

def select_pdf_file(pdf_files):
    """Permet à l'utilisateur de sélectionner un fichier PDF."""
    if not pdf_files:
        print("Aucun fichier PDF trouvé dans le répertoire courant et ses sous-répertoires.")
        return None
    
    print("\nFichiers PDF trouvés :")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"{i}. {pdf_file}")
    
    while True:
        try:
            choice = input("\nEntrez le numéro du fichier à traiter (ou 'q' pour quitter) : ")
            if choice.lower() == 'q':
                return None
            choice = int(choice) - 1
            if 0 <= choice < len(pdf_files):
                return str(pdf_files[choice])
            print("Numéro invalide. Veuillez réessayer.")
        except ValueError:
            print("Veuillez entrer un numéro valide.")

def main():
    # Configuration de base
    config = ExtractorConfig(
        date_formats=["%d/%m/%Y"],
        amount_decimal_separator=",",
        amount_thousand_separator=" ",
        debug_mode=True
    )
    
    # Initialisation de l'extracteur
    extractor = PDFExtractor(config)
    
    # Recherche des fichiers PDF
    pdf_files = get_pdf_paths()
    if not pdf_files:
        print("Aucun fichier PDF trouvé dans le répertoire courant et ses sous-répertoires.")
        return
    
    # Sélection du fichier PDF
    pdf_path = select_pdf_file(pdf_files)
    if not pdf_path:
        return
    
    # Vérification de l'existence du fichier
    if not os.path.exists(pdf_path):
        print(f"Erreur: Le fichier {pdf_path} n'existe pas.")
        return
    
    # Création du répertoire de sortie s'il n'existe pas
    output_dir = "extracted_data"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Extraction des données
        print(f"\nExtraction des données depuis {os.path.basename(pdf_path)}...")
        data = extractor.extract(pdf_path)
        
        # Enregistrement en format texte
        print("\nEnregistrement des données extraites...")
        base_name = Path(pdf_path).stem
        output_path = os.path.join(output_dir, base_name)
        
        # Enregistrement en format texte
        txt_file = extractor.save_extracted_data(
            data,
            output_path=output_path,
            format="txt"
        )
        print(f"Données enregistrées dans : {txt_file}")
        
        # Enregistrement en format JSON
        json_file = extractor.save_extracted_data(
            data,
            output_path=output_path,
            format="json"
        )
        print(f"Données JSON enregistrées dans : {json_file}")
        
        # Affichage d'un aperçu des données extraites
        print("\nAperçu des données extraites :")
        print("=" * 50)
        print(f"Numéro de facture: {data.get('facture', {}).get('numero', 'Non trouvé')}")
        print(f"Date: {data.get('facture', {}).get('date', 'Non trouvée')}")
        print(f"Fournisseur: {data.get('fournisseur', {}).get('nom', 'Non trouvé')}")
        print(f"Total TTC: {data.get('totaux', {}).get('total_ttc', 0)} TND")
        
    except Exception as e:
        print(f"Une erreur s'est produite lors de l'extraction : {str(e)}")
        if config.debug_mode:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()



