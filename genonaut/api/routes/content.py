"""Content management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.content_service import ContentService
from genonaut.api.models.requests import (
    ContentCreateRequest, 
    ContentUpdateRequest, 
    ContentQualityUpdateRequest,
    ContentSearchRequest
)
from genonaut.api.models.responses import (
    ContentResponse, 
    ContentListResponse, 
    ContentStatsResponse,
    SuccessResponse
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
            creator_id=content_data.creator_id,
            item_metadata=content_data.item_metadata,
            tags=content_data.tags,
            is_public=content_data.is_public,
            is_private=content_data.is_private
        )
        return ContentResponse.model_validate(content)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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
            is_public=content_data.is_public,
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
    search_params: ContentSearchRequest = Depends(),
    db: Session = Depends(get_database_session)
):
    """Get list of content with optional filtering and search."""
    service = ContentService(db)
    
    try:
        if search_params.search_term or search_params.metadata_filter or search_params.tags:
            content_list = service.search_content(search_params.model_dump())
        else:
            # Handle filtering
            content_list = service.get_content_list(
                skip=search_params.skip,
                limit=search_params.limit,
                content_type=search_params.content_type,
                creator_id=search_params.creator_id,
                public_only=search_params.public_only,
            )

        # Get total count for pagination
        total = len(content_list)
        if not (search_params.search_term or search_params.metadata_filter or search_params.tags):
            filters = {}
            if search_params.content_type:
                filters['content_type'] = search_params.content_type
            if search_params.creator_id:
                filters['creator_id'] = search_params.creator_id
            if search_params.public_only:
                filters.update({'is_public': True, 'is_private': False})

            total = service.repository.count(filters)
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            content_list = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=total,
        skip=search_params.skip,
        limit=search_params.limit
    )


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
                if getattr(content, "is_public", False) and not getattr(content, "is_private", False)
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


@router.get("/creator/{creator_id}", response_model=ContentListResponse)
async def get_content_by_creator(
    creator_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get content by creator."""
    service = ContentService(db)
    content_list = service.get_content_list(
        creator_id=creator_id,
        skip=skip,
        limit=limit
    )
    
    total = service.repository.count({'creator_id': creator_id})
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/type/{content_type}", response_model=ContentListResponse)
async def get_content_by_type(
    content_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get content by type."""
    service = ContentService(db)
    content_list = service.get_content_list(
        content_type=content_type,
        skip=skip,
        limit=limit
    )
    
    total = service.repository.count({'content_type': content_type})
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/public/all", response_model=ContentListResponse)
async def get_public_content(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get all public content."""
    service = ContentService(db)
    content_list = service.get_content_list(
        public_only=True,
        skip=skip,
        limit=limit
    )
    
    total = service.repository.count({'is_public': True, 'is_private': False})
    
    return ContentListResponse(
        items=[ContentResponse.model_validate(content) for content in content_list],
        total=total,
        skip=skip,
        limit=limit
    )


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
