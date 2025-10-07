"""LoRA model service for business logic operations."""

from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.db.schema import LoraModel, CheckpointModel
from genonaut.api.repositories.lora_model_repository import LoraModelRepository
from genonaut.api.repositories.checkpoint_model_repository import CheckpointModelRepository
from genonaut.api.exceptions import EntityNotFoundError


class LoraModelService:
    """Service class for LoRA model business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.repository = LoraModelRepository(db)
        self.checkpoint_repository = CheckpointModelRepository(db)
        self.db = db

    def get_all(self) -> List[LoraModel]:
        """Get all LoRA models sorted by rating descending.

        Returns:
            List of all LoRA models sorted by rating (highest first)
        """
        return self.repository.get_all()

    def get_by_id(self, id: UUID) -> LoraModel:
        """Get LoRA model by ID.

        Args:
            id: LoRA model UUID

        Returns:
            LoraModel instance

        Raises:
            EntityNotFoundError: If LoRA model not found
        """
        model = self.repository.get_by_id(id)
        if model is None:
            raise EntityNotFoundError("LoraModel", id)
        return model

    def get_by_compatible_architecture(self, architecture: str) -> List[LoraModel]:
        """Get LoRA models by compatible architecture.

        Args:
            architecture: Compatible architecture (e.g., 'sd1', 'sdxl')

        Returns:
            List of LoRA models compatible with the architecture sorted by rating
        """
        return self.repository.get_by_compatible_architecture(architecture)

    def get_paginated_with_compatibility(
        self,
        page: int = 1,
        page_size: int = 10,
        checkpoint_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Get paginated LoRA models with compatibility and optimality flags.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            checkpoint_id: UUID of checkpoint to check compatibility against

        Returns:
            Tuple of (list of enriched LoRA model dicts, total count, total pages)
        """
        checkpoint = None
        if checkpoint_id:
            checkpoint = self.checkpoint_repository.get_by_id(UUID(checkpoint_id))

        # Get paginated models
        models, total = self.repository.get_paginated(
            page=page,
            page_size=page_size
        )

        # Enrich with compatibility/optimality flags
        enriched_models = []
        for model in models:
            enriched = {
                'model': model,
                'is_compatible': self._check_compatibility(model, checkpoint) if checkpoint else None,
                'is_optimal': self._check_optimality(model, checkpoint) if checkpoint else None,
            }
            enriched_models.append(enriched)

        total_pages = (total + page_size - 1) // page_size

        return enriched_models, total, total_pages

    def _check_compatibility(self, lora: LoraModel, checkpoint: Optional[CheckpointModel]) -> bool:
        """Check if LoRA is compatible with checkpoint.

        Args:
            lora: LoRA model to check
            checkpoint: Checkpoint model to check against

        Returns:
            True if compatible, False otherwise
        """
        if not checkpoint or not checkpoint.architecture:
            return False

        if not lora.compatible_architectures:
            return False

        # Case-insensitive partial match
        checkpoint_arch = checkpoint.architecture.lower()
        lora_archs = lora.compatible_architectures.lower()

        return checkpoint_arch in lora_archs

    def _check_optimality(self, lora: LoraModel, checkpoint: Optional[CheckpointModel]) -> bool:
        """Check if LoRA is optimal for checkpoint.

        Args:
            lora: LoRA model to check
            checkpoint: Checkpoint model to check against

        Returns:
            True if optimal, False otherwise
        """
        if not checkpoint or not checkpoint.family:
            return False

        if not lora.optimal_checkpoints or len(lora.optimal_checkpoints) == 0:
            return False

        # Case-insensitive check if family is in optimal_checkpoints list
        checkpoint_family = checkpoint.family.lower()
        optimal_checkpoints = [cp.lower() for cp in lora.optimal_checkpoints]

        return checkpoint_family in optimal_checkpoints
