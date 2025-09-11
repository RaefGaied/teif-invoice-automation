# insert_test_invoice_fixed.py
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def insert_test_invoice():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Commencer une transaction
            with conn.begin():
                # Données de la facture
                invoice_data = {
                    'teif_version': '1.0',
                    'controlling_agency': 'TUN',
                    'sender_identifier': '1234567AAM001',
                    'receiver_identifier': '9876543BBM002',
                    'message_identifier': f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'message_datetime': datetime.now(),
                    'document_number': f"FAC-{datetime.now().strftime('%Y%m%d')}-001",
                    'document_type': '388',
                    'document_type_label': 'Facture',
                    'invoice_date': datetime.now().date(),
                    'due_date': (datetime.now() + timedelta(days=30)).date(),
                    'period_start_date': datetime.now().date(),
                    'period_end_date': (datetime.now() + timedelta(days=30)).date(),
                    'supplier_id': 1,
                    'customer_id': 2,
                    'currency': 'TND',
                    'currency_code_list': 'TND',
                    'total_without_tax': 0,
                    'tax_amount': 0,
                    'total_with_tax': 0,
                    'tax_base_amount': 0,
                    'capital_amount': 0,
                    'status': 'draft',
                    'pdf_path': '/chemin/vers/facture.pdf',
                    'xml_path': '/chemin/vers/facture.xml',
                    'ttn_validation_ref': f"TTN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }

                # Insérer la facture et récupérer l'ID
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
                    ) OUTPUT inserted.id
                    VALUES (
                        :teif_version, :controlling_agency, :sender_identifier,
                        :receiver_identifier, :message_identifier, :message_datetime,
                        :document_number, :document_type, :document_type_label,
                        :invoice_date, :due_date, :period_start_date, :period_end_date,
                        :supplier_id, :customer_id, :currency, :currency_code_list,
                        :total_without_tax, :tax_amount, :total_with_tax,
                        :tax_base_amount, :capital_amount, :status, :pdf_path, :xml_path, :ttn_validation_ref,
                        GETDATE(), GETDATE()
                    )
                """), invoice_data)
                
                invoice_id = result.scalar()
                print(f"✅ Facture créée avec l'ID: {invoice_id}")

                # Données des lignes de facture
                items = [
                    {'description': 'Ordinateur portable', 'quantity': 2, 'unit_price': 1500.00, 'tax_rate': 0.19},
                    {'description': 'Souris sans fil', 'quantity': 3, 'unit_price': 50.00, 'tax_rate': 0.07},
                    {'description': 'Clavier mécanique', 'quantity': 2, 'unit_price': 200.00, 'tax_rate': 0.19}
                ]

                # Insérer les lignes de facture
                for i, item in enumerate(items, 1):
                    line_total_ht = item['unit_price'] * item['quantity']
                    tax_amount = line_total_ht * item['tax_rate']
                    
                    conn.execute(text("""
                        INSERT INTO invoice_lines (
                            invoice_id, line_number, description,
                            quantity, unit_price, line_total_ht,
                            currency, currency_code_list, created_at
                        ) VALUES (
                            :invoice_id, :line_number, :description,
                            :quantity, :unit_price, :line_total_ht,
                            :currency, :currency_code_list, GETDATE()
                        )
                    """), {
                        'invoice_id': invoice_id,
                        'line_number': i,
                        'description': item['description'],
                        'quantity': item['quantity'],
                        'unit_price': item['unit_price'],
                        'line_total_ht': line_total_ht,
                        'currency': 'TND',
                        'currency_code_list': 'TND'
                    })

                # Calculer les totaux
                totals = conn.execute(text("""
                    SELECT 
                        SUM(line_total_ht) as total_without_tax,
                        SUM(CASE 
                            WHEN line_number = 2 THEN line_total_ht * 0.07
                            ELSE line_total_ht * 0.19
                        END) as tax_amount,
                        SUM(line_total_ht * (1 + 
                            CASE 
                                WHEN line_number = 2 THEN 0.07
                                ELSE 0.19
                            END
                        )) as total_with_tax
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
        raise

if __name__ == "__main__":
    insert_test_invoice()