from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Initialize with database session and model class.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID.
        
        Args:
            id: Primary key of the record
            
        Returns:
            The model instance if found, else None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, *, skip: int = 0, limit: int = 100, status: Optional[str] = None, company_id: Optional[int] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            company_id: Optional company ID filter
            
        Returns:
            List of model instances
        """
        query = self.db.query(self.model)
        
        # Apply filters if provided
        if status is not None:
            query = query.filter(self.model.status == status)
        if company_id is not None:
            query = query.filter(
                (self.model.supplier_id == company_id) | 
                (self.model.customer_id == company_id)
            )
            
        return query.offset(skip).limit(limit).all()

    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.
        
        Args:
            obj_in: Pydantic model with data to create
            
        Returns:
            The created model instance
        """
        db_obj = self.model(**obj_in.dict())  # type: ignore
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record.
        
        Args:
            db_obj: Model instance to update
            obj_in: Pydantic model or dict with data to update
            
        Returns:
            The updated model instance
        """
        obj_data = obj_in.dict(exclude_unset=True) if not isinstance(obj_in, dict) else obj_in
        
        for field in obj_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_data[field])
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, *, id: int) -> ModelType:
        """Delete a record.
        
        Args:
            id: Primary key of the record to delete
            
        Returns:
            The deleted model instance
        """
        obj = self.db.query(self.model).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj