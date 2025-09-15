"""
Database package for TEIF application.

This package contains all database-related code including models, repositories,
schemas, and session management.
"""

# Import session and Base for easier access
from .session import Base, get_db, SessionLocal

# Import models to ensure they are registered with SQLAlchemy
from . import models  # noqa: F401

__all__ = [
    'Base',
    'get_db',
    'SessionLocal'
]