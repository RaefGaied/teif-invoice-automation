# check_invoice_lines_structure.py
from sqlalchemy import create_engine, text

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def check_invoice_lines_structure():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Vérifier la structure de la table invoice_lines
            print("🔍 Structure de la table 'invoice_lines':")
            result = conn.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'invoice_lines'
                ORDER BY ORDINAL_POSITION
            """))
            
            for row in result:
                print(f"  - {row.COLUMN_NAME}: {row.DATA_TYPE}" + 
                      (f"({row.CHARACTER_MAXIMUM_LENGTH})" if row.CHARACTER_MAXIMUM_LENGTH else "") +
                      f" (Nullable: {row.IS_NULLABLE})")
            
            # Vérifier les contraintes de clé étrangère
            print("\n🔑 Contraintes de clé étrangère pour 'invoice_lines':")
            fks = conn.execute(text("""
                SELECT 
                    fk.name AS fk_name,
                    tp.name AS parent_table,
                    cp.name AS parent_column,
                    tr.name AS referenced_table,
                    cr.name AS referenced_column
                FROM 
                    sys.foreign_keys fk
                INNER JOIN 
                    sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                INNER JOIN 
                    sys.tables tp ON fkc.parent_object_id = tp.object_id
                INNER JOIN 
                    sys.tables tr ON fkc.referenced_object_id = tr.object_id
                INNER JOIN 
                    sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
                INNER JOIN 
                    sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
                WHERE 
                    tp.name = 'invoice_lines'
            """))
            
            for fk in fks:
                print(f"  - {fk.fk_name}: {fk.parent_table}.{fk.parent_column} -> {fk.referenced_table}.{fk.referenced_column}")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_invoice_lines_structure()