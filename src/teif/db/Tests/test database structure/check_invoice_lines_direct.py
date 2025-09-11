# check_invoice_lines_direct.py
from sqlalchemy import create_engine, text

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

def check_invoice_lines_direct():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Vérifier les colonnes de la table
            print("🔍 Colonnes de la table 'invoice_lines':")
            result = conn.execute(text("""
                SELECT 
                    c.name AS column_name,
                    t.name AS data_type,
                    c.max_length,
                    c.precision,
                    c.scale,
                    c.is_nullable
                FROM 
                    sys.columns c
                INNER JOIN 
                    sys.types t ON c.user_type_id = t.user_type_id
                WHERE 
                    c.object_id = OBJECT_ID('invoice_lines')
                ORDER BY 
                    c.column_id
            """))
            
            for row in result:
                print(f"  - {row.column_name}: {row.data_type}" + 
                      (f"({row.max_length})" if row.max_length > 0 and row.data_type in ('varchar', 'nvarchar', 'char', 'nchar') else "") +
                      (f"({row.precision},{row.scale})" if row.precision and row.scale else "") +
                      f" (Nullable: {'YES' if row.is_nullable else 'NO'})")
            
            # Vérifier les contraintes
            print("\n🔑 Contraintes de la table 'invoice_lines':")
            constraints = conn.execute(text("""
                SELECT 
                    name AS constraint_name,
                    type_desc AS constraint_type,
                    definition
                FROM 
                    sys.check_constraints
                WHERE 
                    parent_object_id = OBJECT_ID('invoice_lines')
            """))
            
            for constraint in constraints:
                print(f"  - {constraint.constraint_name}: {constraint.constraint_type}")
                print(f"    {constraint.definition}")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    check_invoice_lines_direct()