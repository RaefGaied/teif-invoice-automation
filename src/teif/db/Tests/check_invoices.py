# check_invoices.py
from sqlalchemy import create_engine, text

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def check_invoices():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Vérifier les factures
            print("\n📄 Factures existantes :")
            invoices = conn.execute(text("""
                SELECT 
                    i.id, 
                    i.document_number as invoice_number, 
                    i.invoice_date as issue_date,
                    s.name as supplier, 
                    c.name as customer,
                    i.total_without_tax,
                    i.tax_amount,
                    i.total_with_tax
                FROM invoices i
                JOIN companies s ON i.supplier_id = s.id
                JOIN companies c ON i.customer_id = c.id
                ORDER BY i.invoice_date DESC
            """))
            
            for inv in invoices:
                print("\n" + "="*60)
                print(f"📋 Facture: {inv.invoice_number}")
                print(f"   Date: {inv.issue_date}")
                print(f"   Fournisseur: {inv.supplier}")
                print(f"   Client: {inv.customer}")
                
                # Détails des lignes de facture
                print("\n   Lignes de facture :")
                lines = conn.execute(text("""
                    SELECT 
                        line_number, 
                        item_name, 
                        quantity, 
                        unit_price, 
                        tax_rate, 
                        tax_amount, 
                        line_total
                    FROM invoice_lines
                    WHERE invoice_id = :invoice_id
                    ORDER BY line_number
                """), {'invoice_id': inv.id})
                
                for line in lines:
                    print(f"\n   Ligne {line.line_number}: {line.quantity}x {line.item_name}")
                    print(f"     Prix unitaire: {line.unit_price} TND")
                    print(f"     Total HT: {line.unit_price * line.quantity} TND")
                    print(f"     Taux TVA: {line.tax_rate}%")
                    print(f"     Montant TVA: {line.tax_amount} TND")
                    print(f"     Total TTC: {line.line_total} TND")
                
                # Totaux
                print("\n   Récapitulatif :")
                print(f"     Total HT: {inv.total_without_tax} TND")
                print(f"     Total TVA: {inv.tax_amount} TND")
                print(f"     Total TTC: {inv.total_with_tax} TND")
                
                print("="*60)
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_invoices()