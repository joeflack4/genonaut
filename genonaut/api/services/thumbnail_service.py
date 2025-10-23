"""Thumbnail generation and image processing service."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageOps
from PIL.Image import Resampling

from genonaut.api.config import get_settings, get_cached_settings

logger = logging.getLogger(__name__)


class ThumbnailSize:
    """Predefined thumbnail sizes."""
    SMALL = (150, 150)    # Small thumbnails for lists
    MEDIUM = (300, 300)   # Medium thumbnails for grids
    LARGE = (600, 600)    # Large thumbnails for previews


class ThumbnailService:
    """Service for generating and managing image thumbnails."""

    def __init__(self):
        """Initialize thumbnail service."""
        self.settings = get_cached_settings() or get_settings()
        self.thumbnail_dir = Path(self.settings.comfyui_output_dir) / "thumbnails"
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnails(
        self,
        source_image_path: str,
        sizes: Optional[List[Tuple[int, int]]] = None,
        formats: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Generate thumbnails in multiple sizes and formats.

        Args:
            source_image_path: Path to the source image
            sizes: List of (width, height) tuples for thumbnail sizes
            formats: List of image formats ('webp', 'png', 'jpeg')

        Returns:
            Dictionary mapping format to list of thumbnail paths
        """
        if sizes is None:
            sizes = [ThumbnailSize.SMALL, ThumbnailSize.MEDIUM, ThumbnailSize.LARGE]

        if formats is None:
            formats = ['webp', 'png']  # WebP first for efficiency, PNG as fallback

        if not os.path.exists(source_image_path):
            raise FileNotFoundError(f"Source image not found: {source_image_path}")

        source_path = Path(source_image_path)
        source_stem = source_path.stem

        results = {fmt: [] for fmt in formats}

        try:
            with Image.open(source_image_path) as img:
                # Auto-orient the image based on EXIF data
                img = ImageOps.exif_transpose(img)

                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                for size in sizes:
                    for fmt in formats:
                        thumbnail_path = self._generate_single_thumbnail(
                            img, source_stem, size, fmt
                        )
                        results[fmt].append(thumbnail_path)

        except Exception as e:
            logger.error(f"Failed to generate thumbnails for {source_image_path}: {e}")
            raise

        return results

    def _generate_single_thumbnail(
        self,
        img: Image.Image,
        source_stem: str,
        size: Tuple[int, int],
        fmt: str
    ) -> str:
        """Generate a single thumbnail file.

        Args:
            img: PIL Image object
            source_stem: Filename stem without extension
            size: (width, height) tuple
            fmt: Output format ('webp', 'png', 'jpeg')

        Returns:
            Path to generated thumbnail
        """
        width, height = size
        size_suffix = f"{width}x{height}"

        filename = f"{source_stem}_{size_suffix}.{fmt}"
        thumbnail_path = self.thumbnail_dir / filename

        # Create thumbnail maintaining aspect ratio
        thumbnail = img.copy()
        thumbnail.thumbnail(size, Resampling.LANCZOS)

        # Save with format-specific optimization
        save_kwargs = self._get_save_kwargs(fmt)

        try:
            thumbnail.save(thumbnail_path, format=fmt.upper(), **save_kwargs)
            logger.debug(f"Generated thumbnail: {thumbnail_path}")
            return str(thumbnail_path)

        except Exception as e:
            logger.error(f"Failed to save thumbnail {thumbnail_path}: {e}")
            raise

    def _get_save_kwargs(self, fmt: str) -> Dict:
        """Get format-specific save parameters for optimization.

        Args:
            fmt: Image format

        Returns:
            Dictionary of save parameters
        """
        if fmt == 'webp':
            return {
                'quality': 85,
                'method': 6,  # Best compression
                'optimize': True
            }
        elif fmt == 'jpeg':
            return {
                'quality': 85,
                'optimize': True,
                'progressive': True
            }
        elif fmt == 'png':
            return {
                'optimize': True,
                'compress_level': 6
            }
        else:
            return {}

    def generate_thumbnail_for_generation(
        self,
        image_paths: List[str],
        generation_id: int
    ) -> Dict[str, Dict[str, List[str]]]:
        """Generate thumbnails for a ComfyUI generation.

        Args:
            image_paths: List of generated image file paths
            generation_id: Generation request ID

        Returns:
            Dictionary mapping image filename to thumbnail results
        """
        results = {}

        for image_path in image_paths:
            try:
                image_filename = Path(image_path).name
                thumbnails = self.generate_thumbnails(image_path)
                results[image_filename] = thumbnails

                logger.info(f"Generated thumbnails for generation {generation_id}: {image_filename}")

            except Exception as e:
                logger.error(f"Failed to generate thumbnails for {image_path} in generation {generation_id}: {e}")
                # Continue processing other images even if one fails
                results[Path(image_path).name] = {'webp': [], 'png': []}

        return results

    def cleanup_thumbnails(self, thumbnail_paths: List[str]) -> int:
        """Clean up thumbnail files.

        Args:
            thumbnail_paths: List of thumbnail file paths to delete

        Returns:
            Number of files successfully deleted
        """
        deleted_count = 0

        for thumbnail_path in thumbnail_paths:
            try:
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                    deleted_count += 1
                    logger.debug(f"Deleted thumbnail: {thumbnail_path}")

            except Exception as e:
                logger.error(f"Failed to delete thumbnail {thumbnail_path}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} thumbnail files")

        return deleted_count

    def get_thumbnail_url(self, thumbnail_path: str, size: str = 'medium') -> Optional[str]:
        """Get URL for serving a thumbnail.

        Args:
            thumbnail_path: Path to thumbnail file
            size: Thumbnail size ('small', 'medium', 'large')

        Returns:
            URL path for serving the thumbnail
        """
        if not os.path.exists(thumbnail_path):
            return None

        # Convert absolute path to relative URL path
        relative_path = Path(thumbnail_path).relative_to(self.settings.comfyui_output_dir)
        return f"/api/v1/images/{relative_path}"

    def validate_image(self, image_path: str) -> bool:
        """Validate that a file is a valid image.

        Args:
            image_path: Path to image file

        Returns:
            True if valid image, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()  # Verify it's a valid image
            return True
        except Exception:
            return False

    def get_image_info(self, image_path: str) -> Optional[Dict]:
        """Get basic information about an image.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image information or None if invalid
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'file_size': os.path.getsize(image_path)
                }
        except Exception as e:
            logger.error(f"Failed to get image info for {image_path}: {e}")
            return None
