"""
Base models and mixins for TEIF system.

This module provides the foundation for all SQLAlchemy models in the TEIF system,
including base classes and common mixins for database entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar, Optional, Tuple
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Type variable for generic type hints
T = TypeVar('T', bound='BaseModel')

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    This class serves as the base for all database models and provides
    common functionality and configuration.
    """
    pass

class CreatedAtMixin:
    """
    Mixin that adds created_at column to a model.
    
    Attributes:
        created_at: The timestamp when the record was created.
    """
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

class TimestampMixin(CreatedAtMixin):
    """
    Mixin that adds timestamp columns to a model.
    
    Attributes:
        created_at: The timestamp when the record was created.
        updated_at: The timestamp when the record was last updated (optional).
    """
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, onupdate=func.now(), nullable=True)

class BaseModel(Base, TimestampMixin):
    """
    Base model with common fields and methods.
    
    All database models should inherit from this class to get common functionality
    like timestamps, ID field, and utility methods.
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    def to_dict(self, exclude: Tuple[str, ...] = ()) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude: Tuple of field names to exclude from the result.
            
        Returns:
            Dictionary representation of the model instance.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary of field names and values to update.
            
        Note:
            Only updates attributes that exist on the model and don't start with '_'.
        """
        for key, value in data.items():
            if hasattr(self, key) and not key.startswith('_'):
                try:
                    setattr(self, key, value)
                except (ValueError, TypeError) as e:
                    # Log or handle conversion errors as needed
                    pass
    
    @classmethod
    def get_table_name(cls) -> str:
        """
        Get the database table name for this model.
        
        Returns:
            The name of the database table.
        """
        return cls.__tablename__
    
    def __repr__(self) -> str:
        """Return a string representation of the model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"

class CreatedAtModel(Base, CreatedAtMixin):
    """
    Base model with only created_at timestamp (no updated_at).
    
    Use this for models that don't need an updated_at field.
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    def to_dict(self, exclude: Tuple[str, ...] = ()) -> Dict[str, Any]:
        """
        Convert model to dictionary representation.
        
        Args:
            exclude: Tuple of field names to exclude from the result.
            
        Returns:
            Dictionary containing the model's fields and values.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }
