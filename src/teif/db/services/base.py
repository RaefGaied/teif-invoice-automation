from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast
from uuid import UUID
import logging
from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from ..models.base import Base
from ..models.invoice import InvoiceStatus
from ..repositories.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

def handle_db_errors(func):
    """Decorator to handle database errors and provide consistent error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Database operation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise ServiceError(f"An unexpected error occurred: {str(e)}") from e
    return wrapper

class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass

class NotFoundError(ServiceError):
    """Raised when a requested resource is not found."""
    pass

class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass

class DatabaseError(ServiceError):
    """Raised when a database operation fails."""
    pass

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class with common CRUD operations and error handling."""
    
    def __init__(self, repository: BaseRepository):
        """Initialize base service with a repository instance.
        
        Args:
            repository: Repository instance for database operations
        """
        self.repository = repository
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @handle_db_errors
    def get(self, id: Union[int, str, UUID]) -> Optional[ModelType]:
        """Get a single record by ID.
        
        Args:
            id: The ID of the record to retrieve
            
        Returns:
            The requested record or None if not found
            
        Raises:
            DatabaseError: If a database error occurs
        """
        self.logger.debug(f"Getting record with ID: {id}")
        try:
            return self.repository.get(id)
        except Exception as e:
            self.logger.error(f"Error getting record with ID {id}: {str(e)}")
            raise
    
    @handle_db_errors
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[InvoiceStatus] = None, 
        company_id: Optional[int] = None
    ) -> List[ModelType]:
        """
        Get multiple items with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            company_id: Filter by company ID
            
        Returns:
            List of items
        """
        try:
            return self.repository.get_multi(
                skip=skip, 
                limit=limit, 
                status=status, 
                company_id=company_id
            )
        except Exception as e:
            logger.error(f"Error in get_multi: {str(e)}")
            raise ServiceError(f"Failed to retrieve items: {str(e)}") from e
    
    @handle_db_errors
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.
        
        Args:
            obj_in: The data for the new record
            
        Returns:
            The newly created record
            
        Raises:
            ValidationError: If input validation fails
            DatabaseError: If a database error occurs
        """
        self.logger.debug(f"Creating new record with data: {obj_in.dict()}")
        try:
            # Validate input
            if not isinstance(obj_in, BaseModel):
                raise ValidationError("Input must be a Pydantic model")
                
            # Create the record
            db_obj = self.repository.create(obj_in)
            self.logger.info(f"Created new record with ID: {getattr(db_obj, 'id', 'unknown')}")
            return db_obj
            
        except ValidationError as e:
            self.logger.warning(f"Validation error creating record: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating record: {str(e)}")
            raise
    
    @handle_db_errors
    def update(
        self, 
        *, 
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record.
        
        Args:
            db_obj: The database record to update
            obj_in: The data to update the record with
            
        Returns:
            The updated record
            
        Raises:
            ValidationError: If input validation fails
            DatabaseError: If a database error occurs
        """
        self.logger.debug(f"Updating record {getattr(db_obj, 'id', 'unknown')} with data: {obj_in}")
        try:
            # Validate input
            if not isinstance(obj_in, (BaseModel, dict)):
                raise ValidationError("Input must be a Pydantic model or dictionary")
                
            # Update the record
            updated_obj = self.repository.update(db_obj=db_obj, obj_in=obj_in)
            self.logger.info(f"Updated record with ID: {getattr(updated_obj, 'id', 'unknown')}")
            return updated_obj
            
        except ValidationError as e:
            self.logger.warning(f"Validation error updating record: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error updating record: {str(e)}")
            raise
    
    @handle_db_errors
    def remove(self, *, id: Union[int, str, UUID]) -> ModelType:
        """Remove a record by ID.
        
        Args:
            id: The ID of the record to remove
            
        Returns:
            The removed record
            
        Raises:
            NotFoundError: If the record is not found
            DatabaseError: If a database error occurs
        """
        self.logger.info(f"Removing record with ID: {id}")
        try:
            obj = self.get(id)
            if not obj:
                raise NotFoundError(f"Record with ID {id} not found")
                
            removed = self.repository.remove(id=id)
            self.logger.info(f"Removed record with ID: {id}")
            return removed
            
        except NotFoundError as e:
            self.logger.warning(f"Record not found: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error removing record with ID {id}: {str(e)}")
            raise
    
    def get_db(self) -> Session:
        """Get the database session.
        
        Returns:
            The current database session
        """
        return self.repository.db
