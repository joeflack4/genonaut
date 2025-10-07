"""Checkpoint model service for business logic operations."""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.db.schema import CheckpointModel
from genonaut.api.repositories.checkpoint_model_repository import CheckpointModelRepository
from genonaut.api.exceptions import EntityNotFoundError


class CheckpointModelService:
    """Service class for checkpoint model business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.repository = CheckpointModelRepository(db)

    def get_all(self) -> List[CheckpointModel]:
        """Get all checkpoint models sorted by rating descending.

        Returns:
            List of all checkpoint models sorted by rating (highest first)
        """
        return self.repository.get_all()

    def get_by_id(self, id: UUID) -> CheckpointModel:
        """Get checkpoint model by ID.

        Args:
            id: Checkpoint model UUID

        Returns:
            CheckpointModel instance

        Raises:
            EntityNotFoundError: If checkpoint model not found
        """
        model = self.repository.get_by_id(id)
        if model is None:
            raise EntityNotFoundError("CheckpointModel", id)
        return model

    def get_by_architecture(self, architecture: str) -> List[CheckpointModel]:
        """Get checkpoint models by architecture.

        Args:
            architecture: Model architecture (e.g., 'sd1', 'sdxl')

        Returns:
            List of checkpoint models with matching architecture sorted by rating
        """
        return self.repository.get_by_architecture(architecture)
