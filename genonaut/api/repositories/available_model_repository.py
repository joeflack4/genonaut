"""Repository for managing available ComfyUI models."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from genonaut.api.repositories.base import BaseRepository
from genonaut.api.services.cache_service import ComfyUICacheService, cached
from genonaut.db.schema import AvailableModel


class AvailableModelRepository(BaseRepository[AvailableModel, Dict[str, Any], Dict[str, Any]]):
    """Repository for available model operations."""

    def __init__(self, db: Session):
        """Initialize available model repository.

        Args:
            db: Database session
        """
        super().__init__(db, AvailableModel)
        self.cache_service = ComfyUICacheService()

    def create_model(
        self,
        name: str,
        model_type: str,
        file_path: str,
        relative_path: str,
        file_size: int,
        file_hash: str,
        format: str,
        is_active: bool = True,
        metadata: Optional[dict] = None
    ) -> AvailableModel:
        """Create a new available model record.

        Args:
            name: Model name
            model_type: Type of model (checkpoint, lora, etc.)
            file_path: Full path to model file
            relative_path: Relative path within models directory
            file_size: Size of model file in bytes
            file_hash: Hash of model file for uniqueness
            format: File format (safetensors, ckpt, etc.)
            is_active: Whether model is active
            metadata: Optional metadata dictionary

        Returns:
            Created model record
        """
        model = AvailableModel(
            name=name,
            model_type=model_type,
            file_path=file_path,
            relative_path=relative_path,
            file_size=file_size,
            file_hash=file_hash,
            format=format,
            is_active=is_active,
            metadata=metadata or {}
        )
        created_model = self.create(model)

        # Invalidate cache after creating new model
        self.cache_service.invalidate_models_cache()

        return created_model

    def get_model_by_name(self, name: str) -> Optional[AvailableModel]:
        """Get model by name.

        Args:
            name: Model name

        Returns:
            Model record or None if not found
        """
        return self.db.query(AvailableModel).filter(
            AvailableModel.name == name
        ).first()

    def get_model_by_hash(self, file_hash: str) -> Optional[AvailableModel]:
        """Get model by file hash.

        Args:
            file_hash: File hash

        Returns:
            Model record or None if not found
        """
        return self.db.query(AvailableModel).filter(
            AvailableModel.file_hash == file_hash
        ).first()

    @cached("models_by_type", ttl_seconds=3600)  # 1 hour cache
    def get_models_by_type(self, model_type: str, active_only: bool = True) -> List[AvailableModel]:
        """Get all models of a specific type.

        Args:
            model_type: Type of models to retrieve
            active_only: Whether to only return active models

        Returns:
            List of model records
        """
        query = self.db.query(AvailableModel).filter(
            AvailableModel.type == model_type
        )

        if active_only:
            query = query.filter(AvailableModel.is_active == True)

        return query.order_by(AvailableModel.name).all()

    @cached("all_models", ttl_seconds=3600)  # 1 hour cache
    def get_all_models(self, active_only: bool = False) -> List[AvailableModel]:
        """Get all available models.

        Args:
            active_only: Whether to only return active models

        Returns:
            List of all model records
        """
        query = self.db.query(AvailableModel)

        if active_only:
            query = query.filter(AvailableModel.is_active == True)

        return query.order_by(AvailableModel.type, AvailableModel.name).all()

    def search_models(
        self,
        search_term: str,
        model_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[AvailableModel]:
        """Search models by name or metadata.

        Args:
            search_term: Term to search for
            model_type: Optional model type filter
            active_only: Whether to only search active models

        Returns:
            List of matching model records
        """
        query = self.db.query(AvailableModel).filter(
            AvailableModel.name.ilike(f"%{search_term}%")
        )

        if model_type:
            query = query.filter(AvailableModel.type == model_type)

        if active_only:
            query = query.filter(AvailableModel.is_active == True)

        return query.order_by(AvailableModel.name).all()

    def get_model_types(self) -> List[str]:
        """Get list of all unique model types.

        Returns:
            List of model type strings
        """
        result = self.db.query(AvailableModel.type.distinct()).all()
        return [row[0] for row in result]

    def get_models_count_by_type(self, active_only: bool = True) -> dict:
        """Get count of models by type.

        Args:
            active_only: Whether to only count active models

        Returns:
            Dictionary mapping model types to counts
        """
        query = self.db.query(
            AvailableModel.type,
            func.count(AvailableModel.id).label('count')
        )

        if active_only:
            query = query.filter(AvailableModel.is_active == True)

        result = query.group_by(AvailableModel.type).all()
        return {model_type: count for model_type, count in result}

    def update_model_status(self, model_id: int, is_active: bool) -> bool:
        """Update model active status.

        Args:
            model_id: Model ID
            is_active: New active status

        Returns:
            True if update was successful
        """
        model = self.get_or_404(model_id)
        model.is_active = is_active
        self.db.commit()
        return True

    def delete_model(self, model_id: int) -> bool:
        """Delete a model record.

        Args:
            model_id: Model ID to delete

        Returns:
            True if deletion was successful
        """
        model = self.get_or_404(model_id)
        self.db.delete(model)
        self.db.commit()
        return True

    def get_models_by_format(self, format: str, active_only: bool = True) -> List[AvailableModel]:
        """Get models by file format.

        Args:
            format: File format (e.g., 'safetensors', 'ckpt')
            active_only: Whether to only return active models

        Returns:
            List of model records
        """
        query = self.db.query(AvailableModel).filter(
            AvailableModel.format == format
        )

        if active_only:
            query = query.filter(AvailableModel.is_active == True)

        return query.order_by(AvailableModel.name).all()

    def get_large_models(self, min_size_mb: int = 100, active_only: bool = True) -> List[AvailableModel]:
        """Get models larger than specified size.

        Args:
            min_size_mb: Minimum size in megabytes
            active_only: Whether to only return active models

        Returns:
            List of large model records
        """
        min_size_bytes = min_size_mb * 1024 * 1024

        query = self.db.query(AvailableModel).filter(
            AvailableModel.file_size >= min_size_bytes
        )

        if active_only:
            query = query.filter(AvailableModel.is_active == True)

        return query.order_by(AvailableModel.file_size.desc()).all()

    def bulk_update_status(self, model_ids: List[int], is_active: bool) -> int:
        """Bulk update model status.

        Args:
            model_ids: List of model IDs to update
            is_active: New active status

        Returns:
            Number of models updated
        """
        updated = self.db.query(AvailableModel).filter(
            AvailableModel.id.in_(model_ids)
        ).update(
            {AvailableModel.is_active: is_active},
            synchronize_session=False
        )
        self.db.commit()
        return updated