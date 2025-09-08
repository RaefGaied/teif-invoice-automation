# insert_test_invoice.py
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def insert_test_invoice():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Données de la facture
            invoice_data = {
                'teif_version': '1.0',
                'controlling_agency': 'TUN',
                'sender_identifier': '1234567AAM001',  # Identifiant fournisseur
                'receiver_identifier': '9876543BBM002',  # Identifiant client
                'message_identifier': f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'message_datetime': datetime.now(),
                'document_number': 'FAC-2023-001',
                'document_type': '388',
                'document_type_label': 'Facture',
                'invoice_date': datetime.now().date(),
                'due_date': (datetime.now() + timedelta(days=30)).date(),
                'period_start_date': datetime.now().date(),
                'period_end_date': (datetime.now() + timedelta(days=30)).date(),
                'supplier_id': 1,  # ID du fournisseur
                'customer_id': 2,  # ID du client
                'currency': 'TND',
                'currency_code_list': 'TND',
                'total_without_tax': 0,  # Sera mis à jour
                'tax_amount': 0,  # Sera mis à jour
                'total_with_tax': 0,  # Sera mis à jour
                'tax_base_amount': 0,  # Sera mis à jour
                'capital_amount': 0,  # Sera mis à jour
                'status': 'draft',
                'pdf_path': '/chemin/vers/facture.pdf',
                'xml_path': '/chemin/vers/facture.xml',
                'ttn_validation_ref': f"TTN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            # Insérer la facture
            result = conn.execute(text("""
                INSERT INTO invoices (
                    teif_version, controlling_agency, sender_identifier,
                    receiver_identifier, message_identifier, message_datetime,
                    document_number, document_type, document_type_label,
                    invoice_date, due_date, period_start_date, period_end_date,
                    supplier_id, customer_id, currency, currency_code_list,
                    total_without_tax, tax_amount, total_with_tax,
                    tax_base_amount, capital_amount, status, pdf_path, xml_path, ttn_validation_ref,
                    created_at, updated_at
                ) VALUES (
                    :teif_version, :controlling_agency, :sender_identifier,
                    :receiver_identifier, :message_identifier, :message_datetime,
                    :document_number, :document_type, :document_type_label,
                    :invoice_date, :due_date, :period_start_date, :period_end_date,
                    :supplier_id, :customer_id, :currency, :currency_code_list,
                    :total_without_tax, :tax_amount, :total_with_tax,
                    :tax_base_amount, :capital_amount, :status, :pdf_path, :xml_path, :ttn_validation_ref,
                    GETDATE(), GETDATE()
                )
                SELECT SCOPE_IDENTITY() AS id
            """), invoice_data)
            
            invoice_id = result.scalar()
            print(f"✅ Facture créée avec l'ID: {invoice_id}")

            # Données des lignes de facture
            items = [
                {'name': 'Ordinateur portable', 'quantity': 2, 'unit_price': 1500.00, 'tax_rate': 19.00},
                {'name': 'Souris sans fil', 'quantity': 3, 'unit_price': 50.00, 'tax_rate': 7.00},
                {'name': 'Clavier mécanique', 'quantity': 2, 'unit_price': 200.00, 'tax_rate': 19.00}
            ]

            # Insérer les lignes de facture
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
                    tax_base_amount = :total_without_tax,
                    capital_amount = :total_with_tax,
                    updated_at = GETDATE()
                WHERE id = :invoice_id
            """), {
                'invoice_id': invoice_id,
                'total_without_tax': totals.total_without_tax,
                'tax_amount': totals.tax_amount,
                'total_with_tax': totals.total_with_tax
            })

            print("✅ Lignes de facture ajoutées avec succès")
            print("✅ Totaux mis à jour")
            print("\n🎉 Facture de test créée avec succès !")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    insert_test_invoice()