"""API routes for user search history."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.user_search_history_service import UserSearchHistoryService
from genonaut.api.exceptions import ValidationError


router = APIRouter(prefix="/api/v1/users/{user_id}/search-history", tags=["search-history"])


# Request/Response Models
class AddSearchRequest(BaseModel):
    """Request model for adding search to history."""
    search_query: str = Field(..., min_length=1, max_length=500)


class SearchHistoryItem(BaseModel):
    """Response model for a single search history item."""
    id: int
    user_id: str
    search_query: str
    created_at: str

    class Config:
        from_attributes = True


class SearchHistoryListResponse(BaseModel):
    """Response model for list of search history items."""
    items: List[SearchHistoryItem]


class PaginationMetadata(BaseModel):
    """Pagination metadata."""
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SearchHistoryPaginatedResponse(BaseModel):
    """Response model for paginated search history."""
    items: List[SearchHistoryItem]
    pagination: PaginationMetadata


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    success: bool
    message: str


class ClearHistoryResponse(BaseModel):
    """Response model for clear all history operation."""
    success: bool
    deleted_count: int
    message: str


# Endpoints
@router.post("", response_model=SearchHistoryItem, status_code=201)
def add_search_to_history(
    user_id: UUID,
    request: AddSearchRequest,
    db: Session = Depends(get_database_session)
):
    """Add a search query to user's history.

    Args:
        user_id: UUID of the user
        request: Request containing search_query
        db: Database session

    Returns:
        Created search history item

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        service = UserSearchHistoryService(db)
        history_item = service.add_search(user_id, request.search_query)

        return SearchHistoryItem(
            id=history_item.id,
            user_id=str(history_item.user_id),
            search_query=history_item.search_query,
            created_at=history_item.created_at.isoformat()
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recent", response_model=SearchHistoryListResponse)
def get_recent_searches(
    user_id: UUID,
    limit: int = Query(default=3, ge=1, le=100),
    db: Session = Depends(get_database_session)
):
    """Get user's most recent search queries.

    Args:
        user_id: UUID of the user
        limit: Maximum number of recent searches (default 3, max 100)
        db: Database session

    Returns:
        List of recent search history items

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        service = UserSearchHistoryService(db)
        items = service.get_recent_searches(user_id, limit)

        return SearchHistoryListResponse(
            items=[
                SearchHistoryItem(
                    id=item.id,
                    user_id=str(item.user_id),
                    search_query=item.search_query,
                    created_at=item.created_at.isoformat()
                )
                for item in items
            ]
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=SearchHistoryPaginatedResponse)
def get_search_history(
    user_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_database_session)
):
    """Get user's search history with pagination.

    Args:
        user_id: UUID of the user
        page: Page number (1-indexed, default 1)
        page_size: Items per page (default 20, max 100)
        db: Database session

    Returns:
        Paginated search history

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        service = UserSearchHistoryService(db)
        result = service.get_search_history_paginated(user_id, page, page_size)

        return SearchHistoryPaginatedResponse(
            items=[
                SearchHistoryItem(
                    id=item.id,
                    user_id=str(item.user_id),
                    search_query=item.search_query,
                    created_at=item.created_at.isoformat()
                )
                for item in result["items"]
            ],
            pagination=PaginationMetadata(**result["pagination"])
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{history_id}", response_model=DeleteResponse)
def delete_search_history_item(
    user_id: UUID,
    history_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete a specific search history entry.

    Args:
        user_id: UUID of the user
        history_id: ID of the history entry to delete
        db: Database session

    Returns:
        Delete result

    Raises:
        HTTPException: 404 if not found or unauthorized
    """
    service = UserSearchHistoryService(db)
    success = service.delete_search(user_id, history_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Search history item not found or unauthorized"
        )

    return DeleteResponse(
        success=True,
        message="Search history item deleted successfully"
    )


@router.delete("", response_model=ClearHistoryResponse)
def clear_all_search_history(
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Clear all search history for a user.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        Clear result with count of deleted items
    """
    service = UserSearchHistoryService(db)
    deleted_count = service.clear_all_history(user_id)

    return ClearHistoryResponse(
        success=True,
        deleted_count=deleted_count,
        message=f"Cleared {deleted_count} search history item(s)"
    )
