"""User interaction API routes."""

from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.interaction_service import InteractionService
from genonaut.api.models.requests import (
    InteractionCreateRequest, 
    InteractionUpdateRequest,
    InteractionSearchRequest
)
from genonaut.api.models.responses import (
    InteractionResponse,
    InteractionListResponse,
    InteractionStatsResponse,
    InteractionSummaryResponse,
    SuccessResponse,
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.db.schema import ContentItem, UserInteraction

router = APIRouter(prefix="/api/v1/interactions", tags=["interactions"])


@router.post("/", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def record_interaction(
    interaction_data: InteractionCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Record a new user interaction."""
    service = InteractionService(db)
    try:
        interaction = service.record_interaction(
            user_id=interaction_data.user_id,
            content_item_id=interaction_data.content_item_id,
            interaction_type=interaction_data.interaction_type,
            rating=interaction_data.rating,
            duration=interaction_data.duration,
            metadata=interaction_data.metadata
        )
        return InteractionResponse.model_validate(interaction)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: int,
    db: Session = Depends(get_database_session)
):
    """Get interaction by ID."""
    service = InteractionService(db)
    try:
        interaction = service.get_interaction(interaction_id)
        return InteractionResponse.model_validate(interaction)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(
    interaction_id: int,
    interaction_data: InteractionUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update an interaction."""
    service = InteractionService(db)
    try:
        interaction = service.update_interaction(
            interaction_id=interaction_id,
            rating=interaction_data.rating,
            duration=interaction_data.duration,
            metadata=interaction_data.metadata
        )
        return InteractionResponse.model_validate(interaction)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{interaction_id}", response_model=SuccessResponse)
async def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete an interaction."""
    service = InteractionService(db)
    try:
        service.delete_interaction(interaction_id)
        return SuccessResponse(message=f"Interaction {interaction_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=InteractionListResponse)
async def get_interactions(
    search_params: InteractionSearchRequest = Depends(),
    db: Session = Depends(get_database_session)
):
    """Get list of interactions with optional filtering."""
    service = InteractionService(db)
    
    interactions = []
    total = 0
    
    if search_params.user_id:
        if search_params.days:
            interactions = service.get_recent_user_interactions(
                user_id=search_params.user_id,
                days=search_params.days,
                limit=search_params.limit
            )
        else:
            interactions = service.get_user_interactions(
                user_id=search_params.user_id,
                skip=search_params.skip,
                limit=search_params.limit
            )
        total = service.repository.count({'user_id': search_params.user_id})
    elif search_params.content_item_id:
        interactions = service.get_content_interactions(
            content_item_id=search_params.content_item_id,
            skip=search_params.skip,
            limit=search_params.limit
        )
        total = service.repository.count({'content_item_id': search_params.content_item_id})
    elif search_params.interaction_type:
        interactions = service.get_interactions_by_type(
            interaction_type=search_params.interaction_type,
            skip=search_params.skip,
            limit=search_params.limit
        )
        total = service.repository.count({'interaction_type': search_params.interaction_type})
    else:
        interactions = service.repository.get_multi(
            skip=search_params.skip,
            limit=search_params.limit
        )
        total = service.repository.count()
    
    return InteractionListResponse(
        items=[InteractionResponse.model_validate(interaction) for interaction in interactions],
        total=total,
        skip=search_params.skip,
        limit=search_params.limit
    )


@router.get("/user/{user_id}/interactions", response_model=InteractionListResponse)
async def get_user_interactions(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get interactions for a specific user."""
    service = InteractionService(db)
    try:
        interactions = service.get_user_interactions(user_id, skip=skip, limit=limit)
        total = service.repository.count({'user_id': user_id})
        
        return InteractionListResponse(
            items=[InteractionResponse.model_validate(interaction) for interaction in interactions],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/recent", response_model=InteractionListResponse)
async def get_user_recent_interactions(
    user_id: UUID,
    days: int = 30,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get recent interactions for a user."""
    service = InteractionService(db)
    try:
        interactions = service.get_recent_user_interactions(user_id, days=days, limit=limit)
        
        return InteractionListResponse(
            items=[InteractionResponse.model_validate(interaction) for interaction in interactions],
            total=len(interactions),
            skip=0,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/summary", response_model=InteractionSummaryResponse)
async def get_user_interaction_summary(
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Get interaction summary for a user."""
    service = InteractionService(db)
    try:
        summary = service.get_user_interaction_summary(user_id)
        return InteractionSummaryResponse(user_id=user_id, summary=summary)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/content/{content_item_id}/interactions", response_model=InteractionListResponse)
async def get_content_interactions(
    content_item_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get interactions for a specific content item."""
    service = InteractionService(db)
    try:
        interactions = service.get_content_interactions(content_item_id, skip=skip, limit=limit)
        total = service.repository.count({'content_item_id': content_item_id})
        
        return InteractionListResponse(
            items=[InteractionResponse.model_validate(interaction) for interaction in interactions],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/content/{content_item_id}/stats", response_model=InteractionStatsResponse)
async def get_content_interaction_stats(
    content_item_id: int,
    db: Session = Depends(get_database_session)
):
    """Get interaction statistics for a content item."""
    service = InteractionService(db)
    try:
        stats = service.get_content_interaction_stats(content_item_id)
        return InteractionStatsResponse(content_item_id=content_item_id, stats=stats)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/type/{interaction_type}/interactions", response_model=InteractionListResponse)
async def get_interactions_by_type(
    interaction_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get interactions by type."""
    service = InteractionService(db)
    interactions = service.get_interactions_by_type(interaction_type, skip=skip, limit=limit)
    total = service.repository.count({'interaction_type': interaction_type})
    
    return InteractionListResponse(
        items=[InteractionResponse.model_validate(interaction) for interaction in interactions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/user/{user_id}/content/{content_item_id}/{interaction_type}", response_model=InteractionResponse)
async def get_user_content_interaction(
    user_id: UUID,
    content_item_id: int,
    interaction_type: str,
    db: Session = Depends(get_database_session)
):
    """Get specific user-content interaction."""
    service = InteractionService(db)
    try:
        interaction = service.get_user_content_interaction(user_id, content_item_id, interaction_type)
        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {interaction_type} interaction found between user {user_id} and content {content_item_id}"
            )
        return InteractionResponse.model_validate(interaction)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/analytics/user-behavior/{user_id}")
async def get_user_behavior_analytics(
    user_id: UUID,
    db: Session = Depends(get_database_session)
):
    """Provide high-level analytics for a user's interaction history."""

    service = InteractionService(db)
    try:
        summary = service.get_user_interaction_summary(user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    total_interactions = summary.pop('total_interactions', 0)

    favorite_content_types_query = (
        db.query(ContentItem.content_type, func.count(UserInteraction.id).label('count'))
        .join(ContentItem, ContentItem.id == UserInteraction.content_item_id)
        .filter(UserInteraction.user_id == user_id)
        .group_by(ContentItem.content_type)
        .order_by(func.count(UserInteraction.id).desc())
        .limit(5)
        .all()
    )

    favorite_content_types = [row.content_type for row in favorite_content_types_query]

    return {
        "total_interactions": total_interactions,
        "interaction_types": summary,
        "favorite_content_types": favorite_content_types,
    }


@router.get("/stats/overview")
async def get_interaction_stats(
    db: Session = Depends(get_database_session)
):
    """Get overall interaction statistics."""
    service = InteractionService(db)
    stats = service.get_interaction_stats()
    return stats
