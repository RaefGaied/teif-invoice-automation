# check_companies.py
from sqlalchemy import create_engine, text

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def check_companies():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Vérifier les entreprises
            print("📋 Entreprises existantes :")
            companies = conn.execute(text("""
                SELECT id, identifier, name, vat_number 
                FROM companies
                ORDER BY id
            """))
            
            for company in companies:
                print(f"ID: {company.id}, Identifiant: {company.identifier}")
                print(f"  Nom: {company.name}")
                print(f"  TVA: {company.vat_number}")
                print("-" * 50)
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_companies()