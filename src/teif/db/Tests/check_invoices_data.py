# check_invoices_data.py
from sqlalchemy import create_engine, text

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def check_tables_data():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Vérifier le nombre de factures
            count = conn.execute(text("SELECT COUNT(*) FROM invoices")).scalar()
            print(f"📊 Nombre total de factures : {count}")
            
            # Afficher les premières factures
            if count > 0:
                print("\n🔍 Détails des factures :")
                invoices = conn.execute(text("""
                    SELECT TOP 5 * 
                    FROM invoices
                    ORDER BY created_at DESC
                """))
                
                for i, invoice in enumerate(invoices, 1):
                    print(f"\nFacture {i}:")
                    for col in invoice.keys():
                        print(f"  {col}: {getattr(invoice, col)}")
            
            # Vérifier les tables liées
            print("\n📋 Vérification des tables :")
            tables = ['companies', 'invoice_lines', 'invoice_monetary_amounts']
            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  - {table}: {count} enregistrements")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_tables_data()