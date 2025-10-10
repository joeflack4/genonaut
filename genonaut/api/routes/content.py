"""Content management API routes."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.content_service import ContentService
from genonaut.api.models.requests import (
    ContentCreateRequest,
    ContentUpdateRequest,
    ContentQualityUpdateRequest,
    ContentSearchRequest,
    PaginationRequest
)
from genonaut.api.models.responses import (
    ContentResponse,
    ContentListResponse,
    ContentStatsResponse,
    SuccessResponse,
    PaginatedResponse
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError, DatabaseError

router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Create new content."""
    service = ContentService(db)
    try:
        content = service.create_content(
            title=content_data.title,
            content_type=content_data.content_type,
            content_data=content_data.content_data,
            prompt=content_data.prompt,
            creator_id=content_data.creator_id,
            item_metadata=content_data.item_metadata,
            tags=content_data.tags,
            is_private=content_data.is_private
        )
        return ContentResponse.model_validate(content)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/unified")
async def get_unified_content(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=1000, description="Items per page"),
    content_types: Optional[str] = Query(None, description="Comma-separated content types (regular, auto). Defaults to 'regular,auto' if not provided. Send empty string to get no results."),
    creator_filter: str = Query("all", description="Creator filter (all, user, community)"),
    content_source_types: Optional[List[str]] = Query(None, description="Specific content-source combinations (user-regular, user-auto, community-regular, community-auto). When provided, overrides content_types and creator_filter."),
    user_id: Optional[UUID] = Query(None, description="User ID for filtering"),
    search_term: Optional[str] = Query(None, description="Search term for title"),
    sort_field: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    tag: Optional[List[str]] = Query(None, description="Filter by tags (can specify multiple)"),
    db: Session = Depends(get_database_session)
):
    """Get unified content from both regular and auto tables with pagination."""
    service = ContentService(db)

    # NEW: Handle content_source_types parameter (preferred method)
    if content_source_types is not None:
        # Handle sentinel value for "explicitly empty" (HTTP doesn't send empty arrays)
        # If the list contains only an empty string, treat it as an explicit empty selection
        if content_source_types == [""]:
            content_source_types = []

        # Validate content_source_types
        valid_source_types = {"user-regular", "user-auto", "community-regular", "community-auto"}
        for cst in content_source_types:
            if cst and cst not in valid_source_types:  # Skip empty strings in validation
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content_source_type: {cst}. Must be one of: {', '.join(valid_source_types)}"
                )

        # Parse content_source_types into content_types and creator_filter
        # This will be passed to the service layer for processing
        content_type_list = []
        creator_filter_derived = "all"  # We'll use a special flag to indicate source-based filtering

        # The service layer will handle the actual filtering based on content_source_types
        # For now, we just validate and pass through

    else:
        # LEGACY: Parse content types (backward compatibility)
        # If not provided (None), default to both regular and auto
        # If provided but empty, return empty list (will result in no content)
        if content_types is None:
            content_type_list = ["regular", "auto"]
        else:
            content_type_list = [ct.strip() for ct in content_types.split(",") if ct.strip()]

        # Validate content types
        valid_types = {"regular", "auto"}
        for ct in content_type_list:
            if ct not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid content type: {ct}. Must be one of: {', '.join(valid_types)}"
                )

        # Validate creator filter
        if creator_filter not in {"all", "user", "community"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="creator_filter must be one of: all, user, community"
            )

    # Create pagination request
    pagination = PaginationRequest(
        page=page,
        page_size=page_size
    )

    try:
        # Get unified content
        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=content_type_list if content_source_types is None else None,
            creator_filter=creator_filter if content_source_types is None else None,
            content_source_types=content_source_types,
            user_id=user_id,
            search_term=search_term,
            sort_field=sort_field,
            sort_order=sort_order,
            tags=tag
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving unified content: {str(exc)}"
        )


@router.get("/stats/unified")
async def get_unified_content_stats(
    user_id: Optional[UUID] = Query(None, description="User ID for user-specific stats"),
    db: Session = Depends(get_database_session)
):
    """Get unified content statistics across both regular and auto tables."""
    service = ContentService(db)

    try:
        stats = service.get_unified_content_stats(user_id=user_id)
        return stats
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving unified stats: {str(exc)}"
        )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    db: Session = Depends(get_database_session)
):
    """Get content by ID."""
    service = ContentService(db)
    try:
        content = service.get_content(content_id)
        return ContentResponse.model_validate(content)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update content."""
    service = ContentService(db)
    try:
        content = service.update_content(
            content_id=content_id,
            title=content_data.title,
            content_data=content_data.content_data,
            item_metadata=content_data.item_metadata,
            tags=content_data.tags,
            is_private=content_data.is_private
        )
        return ContentResponse.model_validate(content)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{content_id}", response_model=SuccessResponse)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete content."""
    service = ContentService(db)
    try:
        service.delete_content(content_id)
        return SuccessResponse(message=f"Content {content_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{content_id}/quality", response_model=ContentResponse)
async def update_content_quality(
    content_id: int,
    quality_data: ContentQualityUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update content quality score."""
    service = ContentService(db)
    try:
        content = service.update_quality_score(content_id, quality_data.quality_score)
        return ContentResponse.model_validate(content)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/", response_model=ContentListResponse)
async def get_content_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    content_type: str = Query(None, description="Filter by content type"),
    creator_id: UUID = Query(None, description="Filter by creator ID"),
    public_only: bool = Query(False, description="Return only public content"),
    search_term: str = Query(None, description="Search term for title"),
    db: Session = Depends(get_database_session)
):
    """Get list of content (backward compatible endpoint)."""
    service = ContentService(db)

    try:
        # Build filters
        filters = {}
        if content_type:
            filters['content_type'] = content_type
        if creator_id:
            filters['creator_id'] = creator_id
        if public_only:
            filters['is_private'] = False

        # Get content using the service method
        content_items = service.get_content_list(
            skip=skip,
            limit=limit,
            content_type=content_type,
            creator_id=creator_id,
            public_only=public_only
        )

        # Calculate total count based on filters
        count_filters = {}
        if public_only:
            count_filters['is_private'] = False
        if creator_id:
            count_filters['creator_id'] = creator_id
        if content_type:
            count_filters['content_type'] = content_type

        total = service.repository.count(count_filters if count_filters else None)

    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            content_items = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return ContentListResponse(
        items=[ContentResponse.model_validate(item) for item in content_items],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/enhanced", response_model=PaginatedResponse)
async def get_content_list_enhanced(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    cursor: str = Query(None, description="Cursor for cursor-based pagination"),
    sort_field: str = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    content_type: str = Query(None, description="Filter by content type"),
    creator_id: UUID = Query(None, description="Filter by creator ID"),
    public_only: bool = Query(False, description="Return only public content"),
    search_term: str = Query(None, description="Search term for title"),
    db: Session = Depends(get_database_session)
):
    """Get list of content with enhanced pagination support."""
    service = ContentService(db)

    try:
        # Create pagination request
        pagination = PaginationRequest(
            page=page,
            page_size=page_size,
            cursor=cursor,
            sort_field=sort_field,
            sort_order=sort_order
        )

        # Build filters
        filters = {}
        if content_type:
            filters["content_type"] = content_type
        if creator_id:
            filters["creator_id"] = creator_id
        if public_only:
            filters["is_private"] = False

        # Get paginated result
        if filters:
            result = service.repository.get_paginated(pagination, filters=filters)
        else:
            result = service.get_content_list_paginated(pagination)

    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            # Return empty paginated response for missing tables
            from genonaut.api.models.responses import PaginationMeta
            pagination_meta = PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=0,
                has_next=False,
                has_previous=False
            )
            result = PaginatedResponse(items=[], pagination=pagination_meta)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return result


@router.post("/search", response_model=ContentListResponse)
async def search_content_endpoint(
    search_request: ContentSearchRequest,
    db: Session = Depends(get_database_session)
):
    """Search content via POST payload."""
    service = ContentService(db)
    try:
        content_list = service.search_content(search_request.model_dump())

        if search_request.content_type:
            content_list = [
                content
                for content in content_list
                if getattr(content, "content_type", None) == search_request.content_type
            ]

        if search_request.creator_id:
            content_list = [
                content
                for content in content_list
                if getattr(content, "creator_id", None) == search_request.creator_id
            ]

        if search_request.public_only:
            content_list = [
                content
                for content in content_list
                if not getattr(content, "is_private", False)
            ]

        total = len(content_list)
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            content_list = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=total,
        skip=search_request.skip,
        limit=search_request.limit,
    )


@router.get("/creator/{creator_id}", response_model=PaginatedResponse)
async def get_content_by_creator(
    creator_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    cursor: str = Query(None, description="Cursor for cursor-based pagination"),
    sort_field: str = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_database_session)
):
    """Get content by creator with enhanced pagination."""
    service = ContentService(db)

    pagination = PaginationRequest(
        page=page,
        page_size=page_size,
        cursor=cursor,
        sort_field=sort_field,
        sort_order=sort_order
    )

    try:
        result = service.get_content_by_creator_paginated(creator_id, pagination)
        return result
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/type/{content_type}", response_model=PaginatedResponse)
async def get_content_by_type(
    content_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    cursor: str = Query(None, description="Cursor for cursor-based pagination"),
    sort_field: str = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_database_session)
):
    """Get content by type with enhanced pagination."""
    service = ContentService(db)

    pagination = PaginationRequest(
        page=page,
        page_size=page_size,
        cursor=cursor,
        sort_field=sort_field,
        sort_order=sort_order
    )

    try:
        result = service.get_content_by_type_paginated(content_type, pagination)
        return result
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/public/all", response_model=PaginatedResponse)
async def get_public_content(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    cursor: str = Query(None, description="Cursor for cursor-based pagination"),
    sort_field: str = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_database_session)
):
    """Get all public content with enhanced pagination."""
    service = ContentService(db)

    pagination = PaginationRequest(
        page=page,
        page_size=page_size,
        cursor=cursor,
        sort_field=sort_field,
        sort_order=sort_order
    )

    try:
        result = service.get_public_content_paginated(pagination)
        return result
    except DatabaseError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/top-rated/all", response_model=ContentListResponse)
async def get_top_rated_content(
    limit: int = 10,
    db: Session = Depends(get_database_session)
):
    """Get top-rated content."""
    service = ContentService(db)
    content_list = service.get_top_rated_content(limit=limit)
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=len(content_list),
        skip=0,
        limit=limit
    )


@router.get("/recent/all", response_model=ContentListResponse)
async def get_recent_content(
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get recent content."""
    service = ContentService(db)
    content_list = service.get_recent_content(days=days, limit=limit)
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=len(content_list),
        skip=0,
        limit=limit
    )


@router.get("/stats/overview", response_model=ContentStatsResponse)
async def get_content_stats(
    db: Session = Depends(get_database_session)
):
    """Get content statistics."""
    service = ContentService(db)
    stats = service.get_content_stats()
    return ContentStatsResponse(**stats)


