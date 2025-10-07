"""Checkpoint model repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from genonaut.db.schema import CheckpointModel
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class CheckpointModelRepository(BaseRepository[CheckpointModel, Dict[str, Any], Dict[str, Any]]):
    """Repository for CheckpointModel entity operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, CheckpointModel)

    def get_by_id(self, id: UUID) -> Optional[CheckpointModel]:
        """Get checkpoint model by UUID.

        Args:
            id: Checkpoint model UUID

        Returns:
            CheckpointModel instance or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(CheckpointModel).filter(CheckpointModel.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get checkpoint model with id {id}: {str(e)}")

    def get_all(self) -> List[CheckpointModel]:
        """Get all checkpoint models sorted by rating descending.

        Returns:
            List of all checkpoint models sorted by rating (highest first)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(CheckpointModel)
                .order_by(desc(CheckpointModel.rating))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get all checkpoint models: {str(e)}")

    def get_by_architecture(self, architecture: str) -> List[CheckpointModel]:
        """Get checkpoint models by architecture.

        Args:
            architecture: Model architecture (e.g., 'sd1', 'sdxl')

        Returns:
            List of checkpoint models with matching architecture

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(CheckpointModel)
                .filter(CheckpointModel.architecture == architecture)
                .order_by(desc(CheckpointModel.rating))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get checkpoint models by architecture {architecture}: {str(e)}")
