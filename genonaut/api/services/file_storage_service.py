"""File storage and management service."""

import os
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from genonaut.api.config import get_settings, get_cached_settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for managing file storage and organization."""

    def __init__(self):
        """Initialize file storage service."""
        self.settings = get_cached_settings() or get_settings()
        self.base_output_dir = Path(self.settings.comfyui_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.generations_dir = self.base_output_dir / "generations"
        self.thumbnails_dir = self.base_output_dir / "thumbnails"
        self.temp_dir = self.base_output_dir / "temp"

        for directory in [self.generations_dir, self.thumbnails_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def organize_generation_files(
        self,
        generation_id: int,
        user_id: UUID,
        file_paths: List[str]
    ) -> List[str]:
        """Organize generation files into user/date directory structure.

        Args:
            generation_id: Generation request ID
            user_id: User ID who created the generation
            file_paths: List of generated file paths

        Returns:
            List of new organized file paths

        Raises:
            OSError: If file operations fail
        """
        if not file_paths:
            return []

        # Create user directory structure: generations/user_id/YYYY/MM/DD/
        now = datetime.utcnow()
        user_dir = self.generations_dir / str(user_id) / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        user_dir.mkdir(parents=True, exist_ok=True)

        organized_paths = []

        for file_path in file_paths:
            source_path = Path(file_path)

            if not source_path.exists():
                logger.warning(f"Source file not found: {file_path}")
                continue

            # Create organized filename: gen_{generation_id}_{original_name}
            organized_filename = f"gen_{generation_id}_{source_path.name}"
            target_path = user_dir / organized_filename

            try:
                # Move file to organized location
                shutil.move(str(source_path), str(target_path))
                organized_paths.append(str(target_path))
                logger.info(f"Organized file: {file_path} -> {target_path}")

            except Exception as e:
                logger.error(f"Failed to organize file {file_path}: {e}")
                # If move fails, keep original path
                organized_paths.append(file_path)

        return organized_paths

    def get_user_storage_usage(self, user_id: UUID) -> Dict[str, int]:
        """Get storage usage statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with storage usage statistics
        """
        user_dir = self.generations_dir / str(user_id)

        if not user_dir.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "generations": 0,
                "thumbnails": 0
            }

        total_files = 0
        total_size = 0
        generations = 0
        thumbnails = 0

        # Count generation files
        for file_path in user_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

                if file_path.name.startswith("gen_"):
                    generations += 1

        # Count thumbnails
        user_thumbnails_pattern = f"{user_id}_*"
        for thumbnail_path in self.thumbnails_dir.glob(user_thumbnails_pattern):
            if thumbnail_path.is_file():
                thumbnails += 1

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "generations": generations,
            "thumbnails": thumbnails
        }

    def cleanup_old_files(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up files older than specified days.

        Args:
            days_old: Remove files older than this many days

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cutoff_timestamp = cutoff_date.timestamp()

        stats = {
            "generations_deleted": 0,
            "thumbnails_deleted": 0,
            "temp_files_deleted": 0,
            "bytes_freed": 0,
            "errors": 0
        }

        # Clean up generation files
        for file_path in self.generations_dir.rglob("*"):
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats["generations_deleted"] += 1
                        stats["bytes_freed"] += file_size
                        logger.debug(f"Deleted old generation file: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to delete generation file {file_path}: {e}")
                    stats["errors"] += 1

        # Clean up thumbnail files
        for file_path in self.thumbnails_dir.rglob("*"):
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats["thumbnails_deleted"] += 1
                        stats["bytes_freed"] += file_size
                        logger.debug(f"Deleted old thumbnail: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to delete thumbnail {file_path}: {e}")
                    stats["errors"] += 1

        # Clean up temp files (any age)
        for file_path in self.temp_dir.rglob("*"):
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    stats["temp_files_deleted"] += 1
                    stats["bytes_freed"] += file_size
                    logger.debug(f"Deleted temp file: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to delete temp file {file_path}: {e}")
                    stats["errors"] += 1

        # Clean up empty directories
        self._cleanup_empty_directories(self.generations_dir)
        self._cleanup_empty_directories(self.thumbnails_dir)

        logger.info(f"Cleanup completed: {stats}")
        return stats

    def _cleanup_empty_directories(self, base_path: Path):
        """Recursively remove empty directories.

        Args:
            base_path: Base path to start cleanup from
        """
        for dir_path in sorted(base_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and dir_path != base_path:
                try:
                    # Only remove if directory is empty
                    dir_path.rmdir()
                    logger.debug(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty or other error, skip
                    pass

    def validate_file_path(self, file_path: str) -> bool:
        """Validate that a file path is within allowed directories.

        Args:
            file_path: File path to validate

        Returns:
            True if path is valid and within allowed directories
        """
        try:
            full_path = Path(file_path).resolve()
            base_path = self.base_output_dir.resolve()

            # Check if path is within base output directory
            full_path.relative_to(base_path)

            # Check if file exists and is a regular file
            return full_path.exists() and full_path.is_file()

        except (ValueError, OSError):
            return False

    def get_file_security_info(self, file_path: str) -> Optional[Dict]:
        """Get security information about a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with security information or None if file invalid
        """
        if not self.validate_file_path(file_path):
            return None

        try:
            path = Path(file_path)
            stat = path.stat()

            return {
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "permissions": oct(stat.st_mode)[-3:],
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK),
                "extension": path.suffix.lower(),
                "relative_path": str(path.relative_to(self.base_output_dir))
            }

        except Exception as e:
            logger.error(f"Failed to get file security info for {file_path}: {e}")
            return None

    def cleanup_generation_files(self, generation_id: int) -> int:
        """Clean up all files associated with a generation.

        Args:
            generation_id: Generation ID to clean up

        Returns:
            Number of files deleted
        """
        deleted_count = 0

        # Find and delete generation files (pattern: gen_{generation_id}_*)
        pattern = f"gen_{generation_id}_*"

        for file_path in self.generations_dir.rglob(pattern):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted generation file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete generation file {file_path}: {e}")

        # Find and delete associated thumbnails
        for thumbnail_path in self.thumbnails_dir.glob(f"gen_{generation_id}_*"):
            if thumbnail_path.is_file():
                try:
                    thumbnail_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted generation thumbnail: {thumbnail_path}")
                except Exception as e:
                    logger.error(f"Failed to delete generation thumbnail {thumbnail_path}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} files for generation {generation_id}")

        return deleted_count

    def get_storage_statistics(self) -> Dict[str, int]:
        """Get overall storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_generations": 0,
            "total_thumbnails": 0,
            "total_temp_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "users_with_data": 0
        }

        # Count generation files
        for file_path in self.generations_dir.rglob("*"):
            if file_path.is_file():
                stats["total_generations"] += 1
                stats["total_size_bytes"] += file_path.stat().st_size

        # Count thumbnail files
        for file_path in self.thumbnails_dir.rglob("*"):
            if file_path.is_file():
                stats["total_thumbnails"] += 1
                stats["total_size_bytes"] += file_path.stat().st_size

        # Count temp files
        for file_path in self.temp_dir.rglob("*"):
            if file_path.is_file():
                stats["total_temp_files"] += 1
                stats["total_size_bytes"] += file_path.stat().st_size

        # Count users with data
        for user_dir in self.generations_dir.iterdir():
            if user_dir.is_dir():
                stats["users_with_data"] += 1

        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)

        return stats
