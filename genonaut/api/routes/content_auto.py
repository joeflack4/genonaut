"""Routes for automatically generated content."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.exceptions import DatabaseError, EntityNotFoundError, ValidationError
from genonaut.api.models.requests import (
    ContentCreateRequest,
    ContentQualityUpdateRequest,
    ContentSearchRequest,
    ContentUpdateRequest,
)
from genonaut.api.models.responses import (
    ContentAutoListResponse,
    ContentAutoResponse,
    ContentStatsResponse,
    SuccessResponse,
)
from genonaut.api.services.content_service import ContentAutoService

router = APIRouter(prefix="/api/v1/content-auto", tags=["content-auto"])


def _service(db: Session) -> ContentAutoService:
    """Helper to keep route bodies tidy."""

    return ContentAutoService(db)


@router.post("/", response_model=ContentAutoResponse, status_code=status.HTTP_201_CREATED)
async def create_auto_content(
    content_data: ContentCreateRequest,
    db: Session = Depends(get_database_session),
):
    """Create a new automated content record."""

    service = _service(db)
    try:
        content = service.create_content(
            title=content_data.title,
            content_type=content_data.content_type,
            content_data=content_data.content_data,
            creator_id=content_data.creator_id,
            item_metadata=content_data.item_metadata,
            tags=content_data.tags,
            is_public=content_data.is_public,
            is_private=content_data.is_private,
        )
        return ContentAutoResponse.model_validate(content)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{content_id}", response_model=ContentAutoResponse)
async def get_auto_content(
    content_id: int,
    db: Session = Depends(get_database_session),
):
    """Return an automated content record by ID."""

    service = _service(db)
    try:
        content = service.get_content(content_id)
        return ContentAutoResponse.model_validate(content)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{content_id}", response_model=ContentAutoResponse)
async def update_auto_content(
    content_id: int,
    content_data: ContentUpdateRequest,
    db: Session = Depends(get_database_session),
):
    """Update an automated content record."""

    service = _service(db)
    try:
        content = service.update_content(
            content_id=content_id,
            title=content_data.title,
            content_data=content_data.content_data,
            item_metadata=content_data.item_metadata,
            tags=content_data.tags,
            is_public=content_data.is_public,
            is_private=content_data.is_private,
        )
        return ContentAutoResponse.model_validate(content)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.delete("/{content_id}", response_model=SuccessResponse)
async def delete_auto_content(
    content_id: int,
    db: Session = Depends(get_database_session),
):
    """Delete an automated content record."""

    service = _service(db)
    try:
        service.delete_content(content_id)
        return SuccessResponse(message=f"Auto content {content_id} deleted successfully")
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{content_id}/quality", response_model=ContentAutoResponse)
async def update_auto_content_quality(
    content_id: int,
    quality_data: ContentQualityUpdateRequest,
    db: Session = Depends(get_database_session),
):
    """Update the quality score for an automated content record."""

    service = _service(db)
    try:
        content = service.update_content_quality(content_id, quality_data.quality_score)
        return ContentAutoResponse.model_validate(content)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/", response_model=ContentAutoListResponse)
async def list_auto_content(
    search_params: ContentSearchRequest = Depends(),
    db: Session = Depends(get_database_session),
):
    """List automated content records with optional filtering."""

    service = _service(db)
    try:
        if search_params.search_term or search_params.metadata_filter or search_params.tags:
            content_list = service.search_content(search_params.model_dump())
        else:
            content_list = service.get_content_list(
                skip=search_params.skip,
                limit=search_params.limit,
                content_type=search_params.content_type,
                creator_id=search_params.creator_id,
                public_only=search_params.public_only,
            )

        total = len(content_list)
        if not (search_params.search_term or search_params.metadata_filter or search_params.tags):
            filters = {}
            if search_params.content_type:
                filters["content_type"] = search_params.content_type
            if search_params.creator_id:
                filters["creator_id"] = search_params.creator_id
            if search_params.public_only:
                filters.update({"is_public": True, "is_private": False})
            total = service.repository.count(filters)
    except DatabaseError as exc:
        if "UndefinedTable" in str(exc):
            content_list = []
            total = 0
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=total,
        skip=search_params.skip,
        limit=search_params.limit,
    )


@router.post("/search", response_model=ContentAutoListResponse)
async def search_auto_content(
    search_request: ContentSearchRequest,
    db: Session = Depends(get_database_session),
):
    """Search automated content using a POST payload."""

    service = _service(db)
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=total,
        skip=search_request.skip,
        limit=search_request.limit,
    )


@router.get("/creator/{creator_id}", response_model=ContentAutoListResponse)
async def get_auto_content_by_creator(
    creator_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session),
):
    """Return automated content created by a specific user."""

    service = _service(db)
    content_list = service.get_content_list(creator_id=creator_id, skip=skip, limit=limit)
    total = service.repository.count({"creator_id": creator_id})

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/type/{content_type}", response_model=ContentAutoListResponse)
async def get_auto_content_by_type(
    content_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session),
):
    """Return automated content filtered by type."""

    service = _service(db)
    content_list = service.get_content_list(content_type=content_type, skip=skip, limit=limit)
    total = service.repository.count({"content_type": content_type})

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/public/all", response_model=ContentAutoListResponse)
async def get_public_auto_content(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session),
):
    """Return automated content that is publicly visible."""

    service = _service(db)
    content_list = service.get_content_list(public_only=True, skip=skip, limit=limit)
    total = service.repository.count({"is_public": True, "is_private": False})

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/top-rated/all", response_model=ContentAutoListResponse)
async def get_top_rated_auto_content(
    limit: int = 10,
    db: Session = Depends(get_database_session),
):
    """Return top-rated automated content."""

    service = _service(db)
    content_list = service.get_top_rated_content(limit=limit)

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=len(content_list),
        skip=0,
        limit=limit,
    )


@router.get("/recent/all", response_model=ContentAutoListResponse)
async def get_recent_auto_content(
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_database_session),
):
    """Return recently created automated content."""

    service = _service(db)
    content_list = service.get_recent_content(days=days, limit=limit)

    return ContentAutoListResponse(
        items=[ContentAutoResponse.model_validate(content) for content in content_list],
        total=len(content_list),
        skip=0,
        limit=limit,
    )


@router.get("/stats/overview", response_model=ContentStatsResponse)
async def get_auto_content_stats(
    db: Session = Depends(get_database_session),
):
    """Return statistics for automated content."""

    service = _service(db)
    stats = service.get_content_stats()
    return ContentStatsResponse(**stats)
