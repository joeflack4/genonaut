"""Model discovery and management service for ComfyUI models."""

import os
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from genonaut.api.config import get_settings
from genonaut.api.repositories.available_model_repository import AvailableModelRepository
from genonaut.api.services.cache_service import ComfyUICacheService
from genonaut.db.schema import AvailableModel

logger = logging.getLogger(__name__)


class ModelDiscoveryService:
    """Service for discovering and managing ComfyUI models."""

    # Common model file extensions
    MODEL_EXTENSIONS = {
        '.safetensors',
        '.ckpt',
        '.pt',
        '.pth',
        '.bin'
    }

    # Model type mappings based on directory structure
    MODEL_TYPE_MAPPINGS = {
        'checkpoints': 'checkpoint',
        'checkpoint': 'checkpoint',
        'loras': 'lora',
        'lora': 'lora',
        'embeddings': 'embedding',
        'textual_inversion': 'embedding',
        'vae': 'vae',
        'vaes': 'vae',
        'controlnet': 'controlnet',
        'upscale_models': 'upscaler',
        'upscaler': 'upscaler',
        'clip': 'clip',
        'clip_vision': 'clip_vision',
        'style_models': 'style',
        'hypernetworks': 'hypernetwork',
        'diffusers': 'diffuser'
    }

    def __init__(self, db: Session):
        """Initialize model discovery service.

        Args:
            db: Database session
        """
        self.db = db
        self.settings = get_settings()
        self.repository = AvailableModelRepository(db)
        self.cache_service = ComfyUICacheService()

        # Common ComfyUI model directory paths
        self.model_base_paths = [
            # Standard ComfyUI installation paths
            os.path.expanduser("~/ComfyUI/models"),
            "/opt/ComfyUI/models",
            "./ComfyUI/models",
            # Additional common paths
            os.path.expanduser("~/.cache/huggingface/diffusers"),
            os.path.expanduser("~/.cache/huggingface/transformers"),
        ]

        # Add custom paths from settings if available
        if hasattr(self.settings, 'comfyui_model_paths') and self.settings.comfyui_model_paths:
            if isinstance(self.settings.comfyui_model_paths, str):
                self.model_base_paths.extend(self.settings.comfyui_model_paths.split(':'))
            elif isinstance(self.settings.comfyui_model_paths, list):
                self.model_base_paths.extend(self.settings.comfyui_model_paths)

    def discover_models(self, base_paths: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Discover all available models in ComfyUI directories.

        Args:
            base_paths: Optional list of base paths to search. Uses defaults if None.

        Returns:
            Dictionary mapping model types to lists of discovered models
        """
        if base_paths is None:
            base_paths = self.model_base_paths

        discovered_models = {}
        total_found = 0

        for base_path in base_paths:
            path = Path(base_path)
            if not path.exists():
                logger.debug(f"Model path does not exist: {base_path}")
                continue

            logger.info(f"Scanning model directory: {base_path}")
            models_in_path = self._scan_directory(path)

            for model_type, models in models_in_path.items():
                if model_type not in discovered_models:
                    discovered_models[model_type] = []
                discovered_models[model_type].extend(models)
                total_found += len(models)

        logger.info(f"Discovery complete. Found {total_found} models across {len(discovered_models)} types")
        return discovered_models

    def _scan_directory(self, base_path: Path) -> Dict[str, List[Dict]]:
        """Scan a directory for model files.

        Args:
            base_path: Base directory to scan

        Returns:
            Dictionary mapping model types to discovered models
        """
        models = {}

        try:
            for item in base_path.iterdir():
                if item.is_dir():
                    # Check if this directory name maps to a known model type
                    dir_name = item.name.lower()
                    model_type = self.MODEL_TYPE_MAPPINGS.get(dir_name)

                    if model_type:
                        # Scan this directory for model files
                        model_files = self._scan_model_files(item, model_type)
                        if model_files:
                            if model_type not in models:
                                models[model_type] = []
                            models[model_type].extend(model_files)
                    else:
                        # Recursively scan subdirectories
                        subdirectory_models = self._scan_directory(item)
                        for sub_type, sub_models in subdirectory_models.items():
                            if sub_type not in models:
                                models[sub_type] = []
                            models[sub_type].extend(sub_models)

        except PermissionError as e:
            logger.warning(f"Permission denied scanning directory {base_path}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {base_path}: {e}")

        return models

    def _scan_model_files(self, directory: Path, model_type: str) -> List[Dict]:
        """Scan for model files in a specific directory.

        Args:
            directory: Directory to scan
            model_type: Type of models expected in this directory

        Returns:
            List of model information dictionaries
        """
        model_files = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.MODEL_EXTENSIONS:
                    model_info = self._extract_model_info(file_path, model_type)
                    if model_info:
                        model_files.append(model_info)

        except Exception as e:
            logger.error(f"Error scanning model files in {directory}: {e}")

        return model_files

    def _extract_model_info(self, file_path: Path, model_type: str) -> Optional[Dict]:
        """Extract information about a model file.

        Args:
            file_path: Path to the model file
            model_type: Type of the model

        Returns:
            Model information dictionary or None if extraction fails
        """
        try:
            stat = file_path.stat()

            # Calculate file hash for uniqueness
            file_hash = self._calculate_file_hash(file_path)

            # Extract model name (filename without extension)
            model_name = file_path.stem

            # Build relative path from the models directory
            try:
                # Find the models directory in the path
                path_parts = file_path.parts
                models_index = -1
                for i, part in enumerate(path_parts):
                    if part.lower() == 'models':
                        models_index = i
                        break

                if models_index >= 0:
                    relative_path = '/'.join(path_parts[models_index + 1:])
                else:
                    relative_path = str(file_path.relative_to(file_path.parents[2]))
            except (ValueError, IndexError):
                relative_path = file_path.name

            return {
                'name': model_name,
                'model_type': model_type,
                'file_path': str(file_path),
                'relative_path': relative_path,
                'file_size': stat.st_size,
                'file_hash': file_hash,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'is_active': True,
                'format': file_path.suffix.lower().lstrip('.')
            }

        except Exception as e:
            logger.error(f"Failed to extract model info for {file_path}: {e}")
            return None

    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read at a time

        Returns:
            Hexadecimal string of the file hash
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Only hash the first 1MB for large files to improve performance
                bytes_read = 0
                max_bytes = 1024 * 1024  # 1MB

                for chunk in iter(lambda: f.read(chunk_size), b""):
                    if bytes_read >= max_bytes:
                        break
                    hash_sha256.update(chunk)
                    bytes_read += len(chunk)

            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return f"error_{file_path.name}_{file_path.stat().st_size}"

    def update_model_database(self, discovered_models: Optional[Dict[str, List[Dict]]] = None) -> Dict[str, int]:
        """Update the database with discovered models.

        Args:
            discovered_models: Optional pre-discovered models. Will run discovery if None.

        Returns:
            Statistics about the update operation
        """
        if discovered_models is None:
            discovered_models = self.discover_models()

        stats = {
            'added': 0,
            'updated': 0,
            'deactivated': 0,
            'errors': 0
        }

        # Get existing models from database
        existing_models = self.repository.get_all_models()
        existing_by_hash = {model.file_hash: model for model in existing_models}
        discovered_hashes = set()

        try:
            for model_type, models in discovered_models.items():
                for model_info in models:
                    try:
                        file_hash = model_info['file_hash']
                        discovered_hashes.add(file_hash)

                        if file_hash in existing_by_hash:
                            # Update existing model
                            existing_model = existing_by_hash[file_hash]
                            updated = self._update_existing_model(existing_model, model_info)
                            if updated:
                                stats['updated'] += 1
                        else:
                            # Add new model
                            self._add_new_model(model_info)
                            stats['added'] += 1

                    except Exception as e:
                        logger.error(f"Error processing model {model_info.get('name', 'unknown')}: {e}")
                        stats['errors'] += 1

            # Deactivate models that are no longer found
            for existing_model in existing_models:
                if existing_model.file_hash not in discovered_hashes and existing_model.is_active:
                    existing_model.is_active = False
                    stats['deactivated'] += 1

            self.db.commit()

            # Invalidate model-related caches after successful update
            self.cache_service.invalidate_models_cache()
            logger.info(f"Model database update completed: {stats}")

        except Exception as e:
            logger.error(f"Failed to update model database: {e}")
            self.db.rollback()
            raise

        return stats

    def _update_existing_model(self, existing_model: AvailableModel, model_info: Dict) -> bool:
        """Update an existing model in the database.

        Args:
            existing_model: Existing model record
            model_info: New model information

        Returns:
            True if the model was updated
        """
        updated = False

        # Check if file path has changed
        if existing_model.file_path != model_info['file_path']:
            existing_model.file_path = model_info['file_path']
            updated = True

        # Check if relative path has changed
        if existing_model.relative_path != model_info['relative_path']:
            existing_model.relative_path = model_info['relative_path']
            updated = True

        # Update file size if different
        if existing_model.file_size != model_info['file_size']:
            existing_model.file_size = model_info['file_size']
            updated = True

        # Reactivate if it was deactivated
        if not existing_model.is_active:
            existing_model.is_active = True
            updated = True

        # Update modified time
        if existing_model.modified_at != model_info['modified_at']:
            existing_model.modified_at = model_info['modified_at']
            updated = True

        return updated

    def _add_new_model(self, model_info: Dict):
        """Add a new model to the database.

        Args:
            model_info: Model information dictionary
        """
        self.repository.create_model(
            name=model_info['name'],
            model_type=model_info['model_type'],
            file_path=model_info['file_path'],
            relative_path=model_info['relative_path'],
            file_size=model_info['file_size'],
            file_hash=model_info['file_hash'],
            format=model_info['format'],
            is_active=model_info['is_active']
        )

    def validate_model_availability(self, model_names: List[str]) -> Dict[str, bool]:
        """Validate that models are available and accessible.

        Args:
            model_names: List of model names to validate

        Returns:
            Dictionary mapping model names to availability status
        """
        availability = {}

        for model_name in model_names:
            model = self.repository.get_model_by_name(model_name)
            if model and model.is_active:
                # Check if file still exists
                availability[model_name] = os.path.exists(model.file_path)
            else:
                availability[model_name] = False

        return availability

    def get_model_statistics(self) -> Dict[str, int]:
        """Get statistics about available models.

        Returns:
            Dictionary with model statistics
        """
        # Try to get from cache first
        cached_stats = self.cache_service.get_model_stats()
        if cached_stats is not None:
            return cached_stats

        # Calculate stats from database
        models = self.repository.get_all_models()

        stats = {
            'total_models': len(models),
            'active_models': sum(1 for m in models if m.is_active),
            'inactive_models': sum(1 for m in models if not m.is_active),
        }

        # Count by type
        for model in models:
            type_key = f"{model.model_type}_models"
            stats[type_key] = stats.get(type_key, 0) + 1

        # Cache the results
        self.cache_service.set_model_stats(stats)

        return stats

    def cleanup_orphaned_models(self) -> int:
        """Remove model records for files that no longer exist.

        Returns:
            Number of orphaned models removed
        """
        models = self.repository.get_all_models()
        removed_count = 0

        for model in models:
            if not os.path.exists(model.file_path):
                try:
                    self.repository.delete_model(model.id)
                    removed_count += 1
                    logger.info(f"Removed orphaned model: {model.name} (file not found: {model.file_path})")
                except Exception as e:
                    logger.error(f"Failed to remove orphaned model {model.name}: {e}")

        if removed_count > 0:
            self.db.commit()
            logger.info(f"Cleaned up {removed_count} orphaned model records")

        return removed_count