import os
import sys
from pathlib import Path
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

def get_database_url():
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Try to get the database URL from environment variables
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        # If not in environment, try to get it from your application's config
        try:
            from teif.config import settings
            db_url = settings.DATABASE_URL
        except ImportError:
            # If all else fails, prompt the user
            db_url = input("Please enter your database URL (e.g., mssql+pyodbc://user:password@server/database): ")
    
    if not db_url:
        raise ValueError("No database URL provided and couldn't find one in environment variables or settings")
    
    return db_url

def run_migrations():
    # Set up paths
    project_root = Path(__file__).parent.parent.parent  # Adjust based on your project structure
    alembic_ini_path = project_root / "alembic.ini"
    migrations_dir = project_root / "migrations"
    
    # Get database URL
    db_url = get_database_url()
    
    # Initialize Alembic config
    config = Config(str(alembic_ini_path))
    config.set_main_option('script_location', str(migrations_dir))
    config.set_main_option('sqlalchemy.url', db_url)  # Set the database URL
    
    try:
        # Run the migration
        print("Running migration...")
        command.upgrade(config, "head")
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()