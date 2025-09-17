"""
Script to check the current schema of the companies table.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from src.teif.db.session import SQLALCHEMY_DATABASE_URL

def check_company_schema():
    """Check and print the current schema of the companies table."""
    # Create a new engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get the inspector
        inspector = inspect(engine)
        
        # Get all table names
        print("\n=== Database Tables ===")
        tables = inspector.get_table_names()
        for table in tables:
            print(f"- {table}")
        
        # Check if companies table exists
        if 'companies' not in tables:
            print("\n❌ Error: 'companies' table does not exist in the database.")
            return
        
        # Get columns for companies table
        print("\n=== Companies Table Columns ===")
        columns = inspector.get_columns('companies')
        for column in columns:
            print(f"- {column['name']} ({column['type']})")
            if column.get('default'):
                print(f"  Default: {column['default']}")
            if not column.get('nullable', True):
                print("  NOT NULL")
            if column.get('primary_key'):
                print("  PRIMARY KEY")
    
    except Exception as e:
        print(f"\n❌ Error checking schema: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_company_schema()
