from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from ..config.config import settings
import logging

# Set up logging
logging.basicConfig()
sql_logger = logging.getLogger('sqlalchemy.engine')
sql_logger.setLevel(logging.INFO)

# Create database engine
SQLALCHEMY_DATABASE_URL = settings.database_url

print("\n=== Testing Database Connection ===")
try:
    # Create a test connection
    test_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=True
    )
    
    # Test the connection
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT @@VERSION"))
        version = result.scalar()
        print(f"\n✅ Successfully connected to SQL Server")
        print(f"SQL Server Version: {version}")
        
        # Verify database exists
        result = conn.execute(
            text("SELECT name FROM sys.databases WHERE name = :dbname"),
            {"dbname": settings.database['database']}
        )
        if not result.scalar():
            print(f"⚠️ Warning: Database '{settings.database['database']}' not found!")
        else:
            print(f"✅ Database '{settings.database['database']}' exists")
    
    # Create the main engine with the same settings
    engine = test_engine
    
except Exception as e:
    print(f"\n❌ Failed to connect to database:")
    print(f"Error: {str(e)}")
    print(f"\nConnection string: {SQLALCHEMY_DATABASE_URL}")
    print("\nTroubleshooting steps:")
    print("1. Verify SQL Server is running")
    print("2. Check if the server name and port are correct")
    print("3. Ensure Windows Authentication is enabled")
    print("4. Verify the database name is correct")
    print("5. Check if the ODBC driver is properly installed")
    raise

# Create a scoped session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency function that yields database sessions.
    
    Usage in FastAPI endpoints:
    ```python
    from ..db.session import get_db
    
    @app.get("/items/")
    def read_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
    ```
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
