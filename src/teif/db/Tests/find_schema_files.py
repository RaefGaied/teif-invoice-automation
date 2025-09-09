# find_schema_files.py
from pathlib import Path

def find_schema_files():
    root_dir = Path.cwd()
    print(f"🔍 Recherche de fichiers de schéma dans {root_dir}...")
    
    for file_path in root_dir.rglob('*.sql'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'CREATE TABLE' in content and 'invoice_lines' in content:
                print(f"\n📄 Fichier trouvé: {file_path}")
                # Afficher la partie pertinente du fichier
                lines = content.split('\n')
                start = max(0, next((i for i, line in enumerate(lines) if 'CREATE TABLE' in line and 'invoice_lines' in line), 0) - 5)
                end = min(len(lines), start + 30)
                print('\n'.join(lines[start:end]))
                print("...")

if __name__ == "__main__":
    find_schema_files()