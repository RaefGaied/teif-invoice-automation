# populate_test_data.py
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def create_test_data():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Vérifier les entreprises existantes
            companies = conn.execute(text("SELECT id, name FROM companies")).fetchall()
            if len(companies) < 2:
                print("❌ Erreur : Il faut au moins 2 entreprises (fournisseur et client)")
                return

            supplier = companies[0]
            customer = companies[1]
            print(f"✅ Utilisation des entreprises :")
            print(f"  - Fournisseur: {supplier.name} (ID: {supplier.id})")
            print(f"  - Client: {customer.name} (ID: {customer.id})")

            # Créer une facture
            invoice_data = {
                'document_number': 'FAC-2023-001',
                'invoice_date': datetime.now().date(),
                'due_date': (datetime.now() + timedelta(days=30)).date(),
                'supplier_id': supplier.id,
                'customer_id': customer.id,
                'currency': 'TND',
                'status': 'draft',
                'notes': 'Facture de test générée automatiquement'
            }

            # Insérer la facture
            result = conn.execute(text("""
                INSERT INTO invoices (
                    document_number, invoice_date, due_date, 
                    supplier_id, customer_id, currency, 
                    status, notes, created_at, updated_at
                ) VALUES (
                    :document_number, :invoice_date, :due_date,
                    :supplier_id, :customer_id, :currency,
                    :status, :notes, GETDATE(), GETDATE()
                )
                SELECT SCOPE_IDENTITY() AS id
            """), invoice_data)
            
            invoice_id = result.scalar()
            print(f"\n✅ Facture créée avec l'ID: {invoice_id}")

            # Ajouter des lignes de facture
            items = [
                {'name': 'Ordinateur portable', 'quantity': 2, 'unit_price': 1500.00, 'tax_rate': 19.00},
                {'name': 'Souris sans fil', 'quantity': 3, 'unit_price': 50.00, 'tax_rate': 7.00},
                {'name': 'Clavier mécanique', 'quantity': 2, 'unit_price': 200.00, 'tax_rate': 19.00}
            ]

            for i, item in enumerate(items, 1):
                tax_amount = (item['unit_price'] * item['quantity']) * (item['tax_rate'] / 100)
                line_total = (item['unit_price'] * item['quantity']) + tax_amount
                
                conn.execute(text("""
                    INSERT INTO invoice_lines (
                        invoice_id, line_number, item_name, 
                        quantity, unit_price, tax_rate, 
                        tax_amount, line_total, created_at
                    ) VALUES (
                        :invoice_id, :line_number, :item_name,
                        :quantity, :unit_price, :tax_rate,
                        :tax_amount, :line_total, GETDATE()
                    )
                """), {
                    'invoice_id': invoice_id,
                    'line_number': i,
                    'item_name': item['name'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'tax_rate': item['tax_rate'],
                    'tax_amount': tax_amount,
                    'line_total': line_total
                })

            # Calculer les totaux
            totals = conn.execute(text("""
                SELECT 
                    SUM(unit_price * quantity) as total_without_tax,
                    SUM(tax_amount) as tax_amount,
                    SUM(line_total) as total_with_tax
                FROM invoice_lines
                WHERE invoice_id = :invoice_id
            """), {'invoice_id': invoice_id}).fetchone()

            # Mettre à jour les totaux de la facture
            conn.execute(text("""
                UPDATE invoices
                SET 
                    total_without_tax = :total_without_tax,
                    tax_amount = :tax_amount,
                    total_with_tax = :total_with_tax,
                    updated_at = GETDATE()
                WHERE id = :invoice_id
            """), {
                'invoice_id': invoice_id,
                'total_without_tax': totals.total_without_tax,
                'tax_amount': totals.tax_amount,
                'total_with_tax': totals.total_with_tax
            })

            print("\n✅ Données de test insérées avec succès !")
            print("   Vous pouvez maintenant exécuter check_invoices.py pour voir les factures.")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    create_test_data()