"""Bookmark category API routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.bookmark_category_service import BookmarkCategoryService
from genonaut.api.services.bookmark_category_member_service import BookmarkCategoryMemberService
from genonaut.api.models.requests import (
    BookmarkCategoryCreateRequest,
    BookmarkCategoryUpdateRequest,
    BookmarkCategoryListRequest
)
from genonaut.api.models.responses import (
    BookmarkCategoryResponse,
    BookmarkCategoryListResponse,
    BookmarkCategoryTreeNode,
    BookmarksInCategoryResponse,
    BookmarkResponse,
    SuccessResponse,
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError

router = APIRouter(prefix="/api/v1/bookmark-categories", tags=["bookmark-categories"])


@router.post("/", response_model=BookmarkCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: BookmarkCategoryCreateRequest,
    user_id: UUID = Query(..., description="User ID creating the category"),
    db: Session = Depends(get_database_session)
):
    """Create a new bookmark category for a user."""
    service = BookmarkCategoryService(db)
    try:
        category = service.create_category(
            user_id=user_id,
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
            icon=category_data.icon,
            cover_content_id=category_data.cover_content_id,
            cover_content_source_type=category_data.cover_content_source_type,
            parent_id=category_data.parent_id,
            sort_index=category_data.sort_index,
            is_public=category_data.is_public
        )
        return BookmarkCategoryResponse.model_validate(category)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=BookmarkCategoryListResponse)
async def list_categories(
    user_id: UUID = Query(..., description="User ID to list categories for"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    sort_field: str = Query("sort_index", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_database_session)
):
    """Get list of bookmark categories for a user with optional filtering and sorting."""
    service = BookmarkCategoryService(db)
    try:
        sort_by_index = sort_field == "sort_index"
        categories = service.get_user_categories(
            user_id=user_id,
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            is_public=is_public,
            sort_by_index=sort_by_index,
            sort_field=sort_field,
            sort_order=sort_order
        )
        total = service.count_user_categories(
            user_id=user_id,
            parent_id=parent_id,
            is_public=is_public
        )
        return BookmarkCategoryListResponse(
            items=[BookmarkCategoryResponse.model_validate(category) for category in categories],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/tree", response_model=List[BookmarkCategoryTreeNode])
async def get_category_tree(
    user_id: UUID = Query(..., description="User ID to get category tree for"),
    db: Session = Depends(get_database_session)
):
    """Get category tree structure for a user.

    Returns a flat list of all categories. Clients should build the tree structure
    using the parent_id relationships.
    """
    service = BookmarkCategoryService(db)
    try:
        categories = service.get_category_tree(user_id)
        return [BookmarkCategoryTreeNode.model_validate(cat) for cat in categories]
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{category_id}", response_model=BookmarkCategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get category by ID."""
    service = BookmarkCategoryService(db)
    try:
        category = service.get_category(category_id)
        return BookmarkCategoryResponse.model_validate(category)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{category_id}/children", response_model=BookmarkCategoryListResponse)
async def get_child_categories(
    category_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_database_session)
):
    """Get child categories of a parent category."""
    service = BookmarkCategoryService(db)
    try:
        children = service.get_child_categories(category_id, skip=skip, limit=limit)
        # Count would require a separate repo method, for now return list length
        return BookmarkCategoryListResponse(
            items=[BookmarkCategoryResponse.model_validate(child) for child in children],
            total=len(children),
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{category_id}/bookmarks", response_model=BookmarksInCategoryResponse)
async def get_bookmarks_in_category(
    category_id: UUID,
    user_id: UUID = Query(..., description="User ID (for user ratings)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    sort_field: str = Query("user_rating_then_created", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_content: bool = Query(True, description="Include content data in response"),
    db: Session = Depends(get_database_session)
):
    """Get bookmarks in a category with optional content data and sorting."""
    category_service = BookmarkCategoryService(db)
    member_service = BookmarkCategoryMemberService(db)

    try:
        category = category_service.get_category(category_id)

        if include_content:
            # Get bookmarks with content data
            bookmark_dicts = member_service.get_bookmarks_in_category_with_content(
                category_id=category_id,
                user_id=user_id,
                skip=skip,
                limit=limit,
                sort_field=sort_field,
                sort_order=sort_order
            )

            # Construct BookmarkWithContentResponse objects
            from genonaut.api.models.responses import BookmarkWithContentResponse, ContentResponse
            items = []
            for bm_dict in bookmark_dicts:
                bookmark = bm_dict['bookmark']
                content = bm_dict['content']
                user_rating = bm_dict['user_rating']

                # Create BookmarkWithContentResponse
                bookmark_response = BookmarkWithContentResponse(
                    id=bookmark.id,
                    user_id=bookmark.user_id,
                    content_id=bookmark.content_id,
                    content_source_type=bookmark.content_source_type,
                    note=bookmark.note,
                    pinned=bookmark.pinned,
                    is_public=bookmark.is_public,
                    created_at=bookmark.created_at,
                    updated_at=bookmark.updated_at,
                    content=ContentResponse.model_validate(content) if content else None,
                    user_rating=user_rating
                )
                items.append(bookmark_response)
        else:
            # Get bookmarks without content (legacy behavior)
            bookmarks = member_service.get_bookmarks_in_category(
                category_id,
                skip=skip,
                limit=limit
            )
            items = [BookmarkResponse.model_validate(bookmark) for bookmark in bookmarks]

        total = member_service.count_bookmarks_in_category(category_id)

        return BookmarksInCategoryResponse(
            category=BookmarkCategoryResponse.model_validate(category),
            bookmarks=items,
            total=total
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{category_id}", response_model=BookmarkCategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: BookmarkCategoryUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update a category."""
    service = BookmarkCategoryService(db)
    try:
        category = service.update_category(
            category_id=category_id,
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
            icon=category_data.icon,
            cover_content_id=category_data.cover_content_id,
            cover_content_source_type=category_data.cover_content_source_type,
            parent_id=category_data.parent_id,
            sort_index=category_data.sort_index,
            is_public=category_data.is_public
        )
        return BookmarkCategoryResponse.model_validate(category)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{category_id}", response_model=SuccessResponse)
async def delete_category(
    category_id: UUID,
    target_category_id: Optional[UUID] = Query(None, description="Category ID to move bookmarks to (defaults to 'Uncategorized')"),
    delete_all: bool = Query(False, description="If true, delete all bookmarks instead of moving them"),
    db: Session = Depends(get_database_session)
):
    """Delete a category with optional bookmark migration.

    By default, bookmarks will be moved to 'Uncategorized' category.
    Specify target_category_id to move bookmarks to a different category.
    Set delete_all=true to delete all bookmarks instead.

    Note: The 'Uncategorized' category cannot be deleted.
    Child categories will have their parent_id set to NULL (orphaned).
    """
    service = BookmarkCategoryService(db)
    try:
        service.delete_category(category_id, target_category_id, delete_all)
        return SuccessResponse(message=f"Category {category_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/share/{share_token}", response_model=BookmarkCategoryResponse)
async def get_category_by_share_token(
    share_token: UUID,
    db: Session = Depends(get_database_session)
):
    """Get public category by share token."""
    service = BookmarkCategoryService(db)
    try:
        category = service.get_by_share_token(share_token)
        return BookmarkCategoryResponse.model_validate(category)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
