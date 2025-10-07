"""LoRA model repository for database operations."""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func

from genonaut.db.schema import LoraModel
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class LoraModelRepository(BaseRepository[LoraModel, Dict[str, Any], Dict[str, Any]]):
    """Repository for LoraModel entity operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, LoraModel)

    def get_by_id(self, id: UUID) -> Optional[LoraModel]:
        """Get LoRA model by UUID.

        Args:
            id: LoRA model UUID

        Returns:
            LoraModel instance or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(LoraModel).filter(LoraModel.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get LoRA model with id {id}: {str(e)}")

    def get_all(self) -> List[LoraModel]:
        """Get all LoRA models sorted by rating descending.

        Returns:
            List of all LoRA models sorted by rating (highest first)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(LoraModel)
                .order_by(desc(LoraModel.rating))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get all LoRA models: {str(e)}")

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        checkpoint_architecture: Optional[str] = None,
        checkpoint_family: Optional[str] = None
    ) -> Tuple[List[LoraModel], int]:
        """Get paginated LoRA models with optional filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            checkpoint_architecture: Filter by compatible architecture
            checkpoint_family: Filter by optimal checkpoint family

        Returns:
            Tuple of (list of LoRA models, total count)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(LoraModel)

            # Apply filters if provided
            if checkpoint_architecture:
                # Check if compatible_architectures contains the architecture
                query = query.filter(
                    LoraModel.compatible_architectures.ilike(f"%{checkpoint_architecture}%")
                )

            if checkpoint_family:
                # Check if optimal_checkpoints array contains the family
                # This uses PostgreSQL's array operators
                query = query.filter(
                    func.array_to_string(LoraModel.optimal_checkpoints, ',').ilike(f"%{checkpoint_family}%")
                )

            # Get total count before pagination
            total = query.count()

            # Apply sorting and pagination
            offset = (page - 1) * page_size
            models = (
                query
                .order_by(desc(LoraModel.rating))
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return models, total

        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get paginated LoRA models: {str(e)}")

    def get_by_compatible_architecture(self, architecture: str) -> List[LoraModel]:
        """Get LoRA models by compatible architecture.

        Args:
            architecture: Compatible architecture (e.g., 'sd1', 'sdxl')

        Returns:
            List of LoRA models compatible with the architecture

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(LoraModel)
                .filter(LoraModel.compatible_architectures.ilike(f"%{architecture}%"))
                .order_by(desc(LoraModel.rating))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to get LoRA models by compatible architecture {architecture}: {str(e)}"
            )
