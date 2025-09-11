# check_table_structure.py
from sqlalchemy import create_engine, text, inspect

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def check_table_structure():
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        print("🔍 Structure de la table 'invoices':")
        columns = inspector.get_columns('invoices')
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_table_structure()