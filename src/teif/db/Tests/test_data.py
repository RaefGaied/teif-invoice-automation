# test_data.py
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def insert_test_data():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Désactiver temporairement les contraintes
            conn.execute(text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL'"))
            
            # 1. Insérer une entreprise fournisseur
            result = conn.execute(text("""
                INSERT INTO companies (
                    identifier, name, vat_number, tax_id, commercial_register,
                    address_street, address_city, address_postal_code, 
                    phone, email, created_at, updated_at
                ) 
                OUTPUT INSERTED.id
                VALUES (
                    '1234567AAM001', 'SOCIETE FOURNISSEUR SARL', '12345678', '1234567AAM001', 'B1234567',
                    'AVENUE HABIB BOURGUIBA', 'TUNIS', '1000', 
                    '+216 70 000 000', 'contact@fournisseur.tn', GETDATE(), GETDATE()
                )
            """))
            supplier_id = result.scalar()
            
            # 2. Insérer un client
            result = conn.execute(text("""
                INSERT INTO companies (
                    identifier, name, vat_number, tax_id, commercial_register,
                    address_street, address_city, address_postal_code, 
                    phone, email, created_at, updated_at
                ) 
                OUTPUT INSERTED.id
                VALUES (
                    '9876543BBM002', 'SOCIETE CLIENTE SARL', '87654321', '9876543BBM002', 'B9876543',
                    'AVENUE MOHAMED V', 'SOUSSE', '4000', 
                    '+216 73 000 000', 'contact@client.tn', GETDATE(), GETDATE()
                )
            """))
            customer_id = result.scalar()
            
            # 3. Créer une facture
            result = conn.execute(text("""
                INSERT INTO invoices (
                    invoice_number, issue_date, supplier_id, customer_id,
                    ttn_reference, teif_version, controlling_agency,
                    created_at, updated_at
                )
                OUTPUT INSERTED.id
                VALUES (
                    'FACT-2023-001', :issue_date, :supplier_id, :customer_id,
                    'TTN-REF-001', '1.8.8', 'TTN',
                    GETDATE(), GETDATE()
                )
            """), {
                'issue_date': datetime.now().strftime('%Y-%m-%d'),
                'supplier_id': supplier_id,
                'customer_id': customer_id
            })
            invoice_id = result.scalar()
            
            # 4. Ajouter des lignes de facture
            conn.execute(text("""
                INSERT INTO invoice_lines (
                    invoice_id, line_number, item_name, quantity, 
                    unit_price, tax_rate, tax_amount, line_total, 
                    created_at, updated_at
                )
                VALUES
                    (:invoice_id, 1, 'Produit A', 2, 100.00, 19.00, 38.00, 238.00, GETDATE(), GETDATE()),
                    (:invoice_id, 2, 'Produit B', 3, 150.00, 19.00, 85.50, 535.50, GETDATE(), GETDATE())
            """), {'invoice_id': invoice_id})
            
            # 5. Ajouter les montants totaux
            conn.execute(text("""
                INSERT INTO invoice_monetary_amounts (
                    invoice_id, line_extension_amount, tax_exclusive_amount,
                    tax_inclusive_amount, payable_amount, created_at, updated_at
                )
                VALUES (
                    :invoice_id, 650.00, 650.00, 773.50, 773.50, 
                    GETDATE(), GETDATE()
                )
            """), {'invoice_id': invoice_id})
            
            # Réactiver les contraintes
            conn.execute(text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL'"))
            
            print("✅ Données de test insérées avec succès !")
            print(f"ID Fournisseur: {supplier_id}")
            print(f"ID Client: {customer_id}")
            print(f"ID Facture: {invoice_id}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion des données : {e}")
        raise

if __name__ == "__main__":
    insert_test_data()