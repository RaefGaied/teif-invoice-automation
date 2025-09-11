from sqlalchemy import create_engine, text

DATABASE_URL = "mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Vérifier les tables
        result = conn.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """))
        tables = [row[0] for row in result]
        
        if tables:
            print("✅ Tables trouvées :")
            for table in tables:
                print(f"- {table}")
        else:
            print("ℹ️ Aucune table trouvée dans la base de données")
            
except Exception as e:
    print(f"❌ Erreur : {e}")