"""Image serving API routes."""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.thumbnail_service import ThumbnailService
from genonaut.api.config import get_settings
from genonaut.db.schema import ContentItem, ContentItemAuto

router = APIRouter(prefix="/api/v1/images", tags=["images"])


@router.get("/{file_path:path}")
async def serve_image(
    file_path: str,
    thumbnail: Optional[str] = None,
    db: Session = Depends(get_database_session)
):
    """Serve images and thumbnails with proper caching headers.

    Args:
        file_path: Can be either:
            - A content_id (numeric) to look up the image path from the database
            - A relative path to the image file within the ComfyUI output directory
        thumbnail: Optional thumbnail size ('small', 'medium', 'large')
        db: Database session

    Returns:
        FileResponse with the image file

    Raises:
        HTTPException: If file not found or access denied
    """
    settings = get_settings()
    thumbnail_service = ThumbnailService()

    # Check if file_path is a content_id (numeric)
    use_db_lookup = file_path.isdigit()
    if use_db_lookup:
        content_id = int(file_path)

        # Try to find content in both tables
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            content = db.query(ContentItemAuto).filter(ContentItemAuto.id == content_id).first()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Get the content_data field which contains the file path
        image_path = content.content_data

        # Check if it's an absolute path
        if Path(image_path).is_absolute():
            # Use the path as-is (trust database content)
            full_path = Path(image_path)
            base_path = Path(settings.comfyui_output_dir)  # For thumbnail operations
        else:
            # Relative path - prepend comfyui_output_dir
            base_path = Path(settings.comfyui_output_dir)
            full_path = base_path / image_path
    else:
        # Build absolute path to the image (legacy behavior)
        base_path = Path(settings.comfyui_output_dir)
        full_path = base_path / file_path

    # Security check: ensure path is within the allowed directory (only for non-DB lookups)
    if not use_db_lookup:
        try:
            full_path.resolve().relative_to(base_path.resolve())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Invalid file path"
            )

    # Check if this is a thumbnail request
    if thumbnail:
        # Extract the base filename without extension
        source_stem = full_path.stem

        # Map thumbnail size to dimensions
        size_map = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (600, 600)
        }

        if thumbnail not in size_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid thumbnail size. Use: {', '.join(size_map.keys())}"
            )

        # Generate thumbnail path
        size = size_map[thumbnail]
        size_suffix = f"{size[0]}x{size[1]}"
        thumbnail_filename = f"{source_stem}_{size_suffix}.webp"
        thumbnail_path = base_path / "thumbnails" / thumbnail_filename

        # Generate thumbnail if it doesn't exist
        if not thumbnail_path.exists():
            if not full_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source image not found"
                )

            try:
                # Generate thumbnail
                thumbnail_service.generate_thumbnails(
                    str(full_path),
                    sizes=[size],
                    formats=['webp']
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate thumbnail: {str(e)}"
                )

        target_path = thumbnail_path
    else:
        target_path = full_path

    # Check if file exists
    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    # Validate it's actually an image file
    if not thumbnail_service.validate_image(str(target_path)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )

    # Determine content type
    suffix = target_path.suffix.lower()
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp'
    }

    content_type = content_type_map.get(suffix, 'application/octet-stream')

    # Return file with proper caching headers
    return FileResponse(
        path=str(target_path),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "ETag": f'"{target_path.stat().st_mtime}"',  # Use modification time as ETag
        }
    )


@router.get("/{file_path:path}/info")
async def get_image_info(
    file_path: str,
    db: Session = Depends(get_database_session)
):
    """Get information about an image file.

    Args:
        file_path: Can be either:
            - A content_id (numeric) to look up the image path from the database
            - A relative path to the image file within the ComfyUI output directory
        db: Database session

    Returns:
        Dictionary with image information

    Raises:
        HTTPException: If file not found or access denied
    """
    settings = get_settings()
    thumbnail_service = ThumbnailService()

    # Check if file_path is a content_id (numeric)
    use_db_lookup = file_path.isdigit()
    if use_db_lookup:
        content_id = int(file_path)

        # Try to find content in both tables
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            content = db.query(ContentItemAuto).filter(ContentItemAuto.id == content_id).first()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Get the content_data field which contains the file path
        image_path = content.content_data

        # Check if it's an absolute path
        if Path(image_path).is_absolute():
            # Use the path as-is (trust database content)
            full_path = Path(image_path)
            base_path = Path(settings.comfyui_output_dir)
        else:
            # Relative path - prepend comfyui_output_dir
            base_path = Path(settings.comfyui_output_dir)
            full_path = base_path / image_path
    else:
        # Build absolute path to the image (legacy behavior)
        base_path = Path(settings.comfyui_output_dir)
        full_path = base_path / file_path

    # Security check: ensure path is within the allowed directory (only for non-DB lookups)
    if not use_db_lookup:
        try:
            full_path.resolve().relative_to(base_path.resolve())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Invalid file path"
            )

    # Check if file exists
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    # Get image information
    image_info = thumbnail_service.get_image_info(str(full_path))

    if image_info is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )

    return image_info


@router.delete("/thumbnails/{file_path:path}")
async def delete_thumbnails(
    file_path: str,
    db: Session = Depends(get_database_session)
):
    """Delete all thumbnails for a specific image.

    Args:
        file_path: Can be either:
            - A content_id (numeric) to look up the image path from the database
            - A relative path to the source image file
        db: Database session

    Returns:
        Success response with count of deleted thumbnails

    Raises:
        HTTPException: If operation fails
    """
    settings = get_settings()
    thumbnail_service = ThumbnailService()

    # Check if file_path is a content_id (numeric)
    use_db_lookup = file_path.isdigit()
    if use_db_lookup:
        content_id = int(file_path)

        # Try to find content in both tables
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            content = db.query(ContentItemAuto).filter(ContentItemAuto.id == content_id).first()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Get the content_data field which contains the file path
        image_path = content.content_data

        # Check if it's an absolute path
        if Path(image_path).is_absolute():
            # Use the path as-is (trust database content)
            full_path = Path(image_path)
            base_path = Path(settings.comfyui_output_dir)
        else:
            # Relative path - prepend comfyui_output_dir
            base_path = Path(settings.comfyui_output_dir)
            full_path = base_path / image_path
    else:
        # Build absolute path to the image (legacy behavior)
        base_path = Path(settings.comfyui_output_dir)
        full_path = base_path / file_path

    # Security check: ensure path is within the allowed directory (only for non-DB lookups)
    if not use_db_lookup:
        try:
            full_path.resolve().relative_to(base_path.resolve())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Invalid file path"
            )

    # Find all thumbnails for this image
    source_stem = full_path.stem
    thumbnail_dir = base_path / "thumbnails"

    thumbnail_paths = []
    if thumbnail_dir.exists():
        # Look for thumbnails with this stem
        for thumbnail_file in thumbnail_dir.glob(f"{source_stem}_*"):
            thumbnail_paths.append(str(thumbnail_file))

    # Delete thumbnails
    deleted_count = 0
    if thumbnail_paths:
        deleted_count = thumbnail_service.cleanup_thumbnails(thumbnail_paths)

    return {
        "success": True,
        "message": f"Deleted {deleted_count} thumbnails for {file_path}"
    }