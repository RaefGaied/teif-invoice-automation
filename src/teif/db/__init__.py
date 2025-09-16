"""
Database package for TEIF application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Import models to ensure they are registered with SQLAlchemy
from .models import base  # This imports all models via base.py

# Create the SQLAlchemy engine
engine = create_engine(
    'mssql+pyodbc://localhost/TEIF_Complete_DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes&Encrypt=yes&Connection+Timeout=30',
    echo=True  # Set to False in production
)

# Create a configured "Session" class
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Create a base class for declarative models
Base = declarative_base()

def get_db():
    """
    Dependency function that will create a new SQLAlchemy SessionLocal that will be used in a single request.
    The session is closed at the end of the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = [
    'Base',
    'get_db',
    'SessionLocal'
]