"""Bookmark API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.bookmark_service import BookmarkService
from genonaut.api.services.bookmark_category_member_service import BookmarkCategoryMemberService
from genonaut.api.models.requests import (
    BookmarkCreateRequest,
    BookmarkUpdateRequest,
    BookmarkListRequest,
    CategoryMembershipAddRequest,
    CategoryMembershipUpdateRequest
)
from genonaut.api.models.responses import (
    BookmarkResponse,
    BookmarkListResponse,
    CategoryMembershipResponse,
    CategoryMembershipListResponse,
    SuccessResponse,
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError

router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])


@router.post("/", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark_data: BookmarkCreateRequest,
    user_id: UUID = Query(..., description="User ID creating the bookmark"),
    db: Session = Depends(get_database_session)
):
    """Create a new bookmark for a user."""
    service = BookmarkService(db)
    try:
        bookmark = service.create_bookmark(
            user_id=user_id,
            content_id=bookmark_data.content_id,
            content_source_type=bookmark_data.content_source_type,
            note=bookmark_data.note,
            pinned=bookmark_data.pinned,
            is_public=bookmark_data.is_public
        )
        return BookmarkResponse.model_validate(bookmark)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=BookmarkListResponse)
async def list_bookmarks(
    user_id: UUID = Query(..., description="User ID to list bookmarks for"),
    pinned: bool = Query(None, description="Filter by pinned status"),
    is_public: bool = Query(None, description="Filter by public status"),
    category_id: UUID = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_database_session)
):
    """Get list of bookmarks for a user with optional filtering."""
    service = BookmarkService(db)
    try:
        bookmarks = service.get_user_bookmarks(
            user_id=user_id,
            skip=skip,
            limit=limit,
            pinned=pinned,
            is_public=is_public,
            category_id=category_id
        )
        total = service.count_user_bookmarks(
            user_id=user_id,
            pinned=pinned,
            is_public=is_public,
            category_id=category_id
        )
        return BookmarkListResponse(
            items=[BookmarkResponse.model_validate(bookmark) for bookmark in bookmarks],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get bookmark by ID."""
    service = BookmarkService(db)
    try:
        bookmark = service.get_bookmark(bookmark_id)
        return BookmarkResponse.model_validate(bookmark)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: UUID,
    bookmark_data: BookmarkUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update a bookmark."""
    service = BookmarkService(db)
    try:
        bookmark = service.update_bookmark(
            bookmark_id=bookmark_id,
            note=bookmark_data.note,
            pinned=bookmark_data.pinned,
            is_public=bookmark_data.is_public
        )
        return BookmarkResponse.model_validate(bookmark)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{bookmark_id}", response_model=SuccessResponse)
async def delete_bookmark(
    bookmark_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Delete a bookmark (soft delete)."""
    service = BookmarkService(db)
    try:
        service.delete_bookmark(bookmark_id)
        return SuccessResponse(message=f"Bookmark {bookmark_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Category membership endpoints
@router.post("/{bookmark_id}/categories", response_model=CategoryMembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_bookmark_to_category(
    bookmark_id: UUID,
    membership_data: CategoryMembershipAddRequest,
    db: Session = Depends(get_database_session)
):
    """Add a bookmark to a category."""
    service = BookmarkCategoryMemberService(db)
    try:
        membership = service.add_bookmark_to_category(
            bookmark_id=bookmark_id,
            category_id=membership_data.category_id,
            position=membership_data.position
        )
        return CategoryMembershipResponse.model_validate(membership)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{bookmark_id}/categories", response_model=CategoryMembershipListResponse)
async def get_bookmark_categories(
    bookmark_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get all categories that a bookmark belongs to."""
    service = BookmarkCategoryMemberService(db)
    try:
        memberships = service.get_bookmark_categories(bookmark_id)
        return CategoryMembershipListResponse(
            items=[CategoryMembershipResponse.model_validate(membership) for membership in memberships],
            total=len(memberships)
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{bookmark_id}/categories/{category_id}", response_model=SuccessResponse)
async def remove_bookmark_from_category(
    bookmark_id: UUID,
    category_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Remove a bookmark from a category."""
    service = BookmarkCategoryMemberService(db)
    try:
        removed = service.remove_bookmark_from_category(bookmark_id, category_id)
        if removed:
            return SuccessResponse(message=f"Bookmark {bookmark_id} removed from category {category_id}")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark is not in this category"
            )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{bookmark_id}/categories/{category_id}/position", response_model=CategoryMembershipResponse)
async def update_bookmark_position(
    bookmark_id: UUID,
    category_id: UUID,
    position_data: CategoryMembershipUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update bookmark position in a category."""
    service = BookmarkCategoryMemberService(db)
    try:
        membership = service.update_bookmark_position(
            bookmark_id=bookmark_id,
            category_id=category_id,
            position=position_data.position
        )
        return CategoryMembershipResponse.model_validate(membership)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
