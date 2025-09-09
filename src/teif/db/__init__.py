"""
TEIF Database Module

This module provides database connectivity and model definitions for the TEIF system.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Import all models to ensure they are registered with SQLAlchemy
from .models import *

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'mssql+pyodbc://@localhost/TEIF_Complete_DB?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session factory
Session = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()

# Import all models to ensure they are registered with SQLAlchemy's metadata
from .models.base import BaseModel
from .models.company import Company, CompanyReference, CompanyContact, ContactCommunication
from .models.invoice import Invoice, InvoiceLine, InvoiceDate, InvoiceReference, AdditionalDocument, SpecialCondition
from .models.payment import PaymentTerm, PaymentMean
from .models.signature import InvoiceSignature, GeneratedXmlFile
from .models.tax import LineTax, InvoiceTax, InvoiceMonetaryAmount

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency function to get DB session.
    Use in FastAPI dependencies with Depends(get_db).
    """
    db = Session()
    try:
        yield db
    finally:
        db.close()