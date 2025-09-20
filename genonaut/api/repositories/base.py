"""Base repository pattern for data access operations."""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from genonaut.api.exceptions import DatabaseError, EntityNotFoundError

# Type variables for generic repository
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, db: Session, model: Type[ModelType]):
        """Initialize repository with database session and model class.
        
        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Model instance or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get {self.model.__name__} with id {id}: {str(e)}")
    
    def get_or_404(self, id: int) -> ModelType:
        """Get entity by ID or raise 404 error.
        
        Args:
            id: Entity ID
            
        Returns:
            Model instance
            
        Raises:
            EntityNotFoundError: If entity not found
            DatabaseError: If database operation fails
        """
        entity = self.get(id)
        if entity is None:
            raise EntityNotFoundError(self.model.__name__, id)
        return entity
    
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple entities with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field filters
            
        Returns:
            List of model instances
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(self.model)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.filter(getattr(self.model, field) == value)
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get {self.model.__name__} records: {str(e)}")
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new entity.
        
        Args:
            obj_in: Pydantic schema with creation data
            
        Returns:
            Created model instance
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Convert Pydantic model to dict
            if hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict()
            elif hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump()
            else:
                obj_data = obj_in
            
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create {self.model.__name__}: {str(e)}")
    
    def update(self, id: int, obj_in: UpdateSchemaType) -> ModelType:
        """Update existing entity.
        
        Args:
            id: Entity ID
            obj_in: Pydantic schema with update data
            
        Returns:
            Updated model instance
            
        Raises:
            EntityNotFoundError: If entity not found
            DatabaseError: If database operation fails
        """
        try:
            db_obj = self.get_or_404(id)
            
            # Convert Pydantic model to dict, excluding unset values
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            elif hasattr(obj_in, 'model_dump'):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update {self.model.__name__} with id {id}: {str(e)}")
    
    def delete(self, id: int) -> bool:
        """Delete entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            EntityNotFoundError: If entity not found
            DatabaseError: If database operation fails
        """
        try:
            db_obj = self.get_or_404(id)
            self.db.delete(db_obj)
            self.db.commit()
            return True
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete {self.model.__name__} with id {id}: {str(e)}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering.
        
        Args:
            filters: Dictionary of field filters
            
        Returns:
            Number of matching entities
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(self.model)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.filter(getattr(self.model, field) == value)
            
            return query.count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to count {self.model.__name__} records: {str(e)}")
    
    def exists(self, id: int) -> bool:
        """Check if entity exists by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity exists
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(self.model.id).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check existence of {self.model.__name__} with id {id}: {str(e)}")