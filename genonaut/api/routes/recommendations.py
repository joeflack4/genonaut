"""Recommendation API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.services.recommendation_service import RecommendationService
from genonaut.api.models.requests import (
    RecommendationCreateRequest,
    RecommendationUpdateRequest,
    RecommendationBulkCreateRequest,
    RecommendationServedRequest,
    RecommendationSearchRequest,
    RecommendationGenerateRequest,
)
from genonaut.api.models.responses import (
    RecommendationResponse,
    RecommendationListResponse,
    RecommendationStatsResponse,
    RecommendationGenerationResponse,
    RecommendationServedResponse,
    SuccessResponse,
)
from genonaut.api.exceptions import EntityNotFoundError, ValidationError

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    recommendation_data: RecommendationCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Create a new recommendation."""
    service = RecommendationService(db)
    try:
        recommendation = service.create_recommendation(
            user_id=recommendation_data.user_id,
            content_item_id=recommendation_data.content_item_id,
            recommendation_score=recommendation_data.recommendation_score,
            algorithm_version=recommendation_data.algorithm_version,
            metadata=recommendation_data.metadata
        )
        return RecommendationResponse.model_validate(recommendation)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/bulk", response_model=RecommendationListResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_recommendations(
    bulk_data: RecommendationBulkCreateRequest,
    db: Session = Depends(get_database_session)
):
    """Bulk create recommendations."""
    service = RecommendationService(db)
    try:
        # Convert Pydantic models to dictionaries
        recommendations_data = [
            {
                'user_id': rec.user_id,
                'content_item_id': rec.content_item_id,
                'recommendation_score': rec.recommendation_score,
                'algorithm_version': rec.algorithm_version,
                'rec_metadata': rec.metadata
            }
            for rec in bulk_data.recommendations
        ]
        
        recommendations = service.bulk_create_recommendations(recommendations_data)
        
        return RecommendationListResponse(
            items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
            total=len(recommendations),
            skip=0,
            limit=len(recommendations)
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_database_session)
):
    """Get recommendation by ID."""
    service = RecommendationService(db)
    try:
        recommendation = service.get_recommendation(recommendation_id)
        return RecommendationResponse.model_validate(recommendation)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: int,
    recommendation_data: RecommendationUpdateRequest,
    db: Session = Depends(get_database_session)
):
    """Update a recommendation."""
    service = RecommendationService(db)
    try:
        recommendation = service.update_recommendation(
            recommendation_id=recommendation_id,
            recommendation_score=recommendation_data.recommendation_score,
            metadata=recommendation_data.metadata
        )
        return RecommendationResponse.model_validate(recommendation)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{recommendation_id}", response_model=SuccessResponse)
async def delete_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete a recommendation."""
    service = RecommendationService(db)
    try:
        service.delete_recommendation(recommendation_id)
        return SuccessResponse(message=f"Recommendation {recommendation_id} deleted successfully")
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=RecommendationListResponse)
async def get_recommendations(
    search_params: RecommendationSearchRequest = Depends(),
    db: Session = Depends(get_database_session)
):
    """Get list of recommendations with optional filtering."""
    service = RecommendationService(db)
    
    recommendations = []
    total = 0
    
    if search_params.user_id:
        recommendations = service.get_user_recommendations(
            user_id=search_params.user_id,
            skip=search_params.skip,
            limit=search_params.limit,
            min_score=search_params.min_score,
            unserved_only=search_params.unserved_only
        )
        total = service.repository.count({'user_id': search_params.user_id})
    elif search_params.content_item_id:
        recommendations = service.get_content_recommendations(
            content_item_id=search_params.content_item_id,
            skip=search_params.skip,
            limit=search_params.limit
        )
        total = service.repository.count({'content_item_id': search_params.content_item_id})
    elif search_params.algorithm_version:
        recommendations = service.get_recommendations_by_algorithm(
            algorithm_version=search_params.algorithm_version,
            skip=search_params.skip,
            limit=search_params.limit
        )
        total = service.repository.count({'algorithm_version': search_params.algorithm_version})
    else:
        recommendations = service.repository.get_multi(
            skip=search_params.skip,
            limit=search_params.limit
        )
        total = service.repository.count()
    
    return RecommendationListResponse(
        items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
        total=total,
        skip=search_params.skip,
        limit=search_params.limit
    )


@router.get("/user/{user_id}/recommendations", response_model=RecommendationListResponse)
async def get_user_recommendations(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    min_score: float = None,
    unserved_only: bool = False,
    db: Session = Depends(get_database_session)
):
    """Get recommendations for a specific user."""
    service = RecommendationService(db)
    try:
        recommendations = service.get_user_recommendations(
            user_id=user_id,
            skip=skip,
            limit=limit,
            min_score=min_score,
            unserved_only=unserved_only
        )
        total = service.repository.count({'user_id': user_id})
        
        return RecommendationListResponse(
            items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/user/{user_id}/top", response_model=RecommendationListResponse)
async def get_top_user_recommendations(
    user_id: int,
    min_score: float = 0.5,
    limit: int = 10,
    db: Session = Depends(get_database_session)
):
    """Get top recommendations for a user."""
    service = RecommendationService(db)
    try:
        recommendations = service.repository.get_top_recommendations(
            user_id=user_id,
            min_score=min_score,
            limit=limit
        )
        
        return RecommendationListResponse(
            items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
            total=len(recommendations),
            skip=0,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/unserved", response_model=RecommendationListResponse)
async def get_unserved_user_recommendations(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_database_session)
):
    """Get unserved recommendations for a user."""
    service = RecommendationService(db)
    try:
        recommendations = service.repository.get_unserved_recommendations(
            user_id=user_id,
            limit=limit
        )
        
        return RecommendationListResponse(
            items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
            total=len(recommendations),
            skip=0,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/recent", response_model=RecommendationListResponse)
async def get_recent_user_recommendations(
    user_id: int,
    days: int = 7,
    limit: int = 50,
    db: Session = Depends(get_database_session)
):
    """Get recent recommendations for a user."""
    service = RecommendationService(db)
    try:
        recommendations = service.get_recent_recommendations(user_id, days=days, limit=limit)
        
        return RecommendationListResponse(
            items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
            total=len(recommendations),
            skip=0,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/stats", response_model=RecommendationStatsResponse)
async def get_user_recommendation_stats(
    user_id: int,
    db: Session = Depends(get_database_session)
):
    """Get recommendation statistics for a user."""
    service = RecommendationService(db)
    try:
        stats = service.get_user_recommendation_stats(user_id)
        return RecommendationStatsResponse(user_id=user_id, **stats)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/content/{content_item_id}/recommendations", response_model=RecommendationListResponse)
async def get_content_recommendations(
    content_item_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get recommendations for a specific content item."""
    service = RecommendationService(db)
    try:
        recommendations = service.get_content_recommendations(
            content_item_id=content_item_id,
            skip=skip,
            limit=limit
        )
        total = service.repository.count({'content_item_id': content_item_id})
        
        return RecommendationListResponse(
            items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
            total=total,
            skip=skip,
            limit=limit
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/algorithm/{algorithm_version}/recommendations", response_model=RecommendationListResponse)
async def get_recommendations_by_algorithm(
    algorithm_version: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_database_session)
):
    """Get recommendations by algorithm version."""
    service = RecommendationService(db)
    recommendations = service.get_recommendations_by_algorithm(
        algorithm_version=algorithm_version,
        skip=skip,
        limit=limit
    )
    total = service.repository.count({'algorithm_version': algorithm_version})
    
    return RecommendationListResponse(
        items=[RecommendationResponse.model_validate(rec) for rec in recommendations],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/served", response_model=RecommendationServedResponse)
async def mark_recommendations_as_served(
    served_data: RecommendationServedRequest,
    db: Session = Depends(get_database_session)
):
    """Mark recommendations as served."""
    service = RecommendationService(db)
    try:
        marked_count = service.mark_recommendations_as_served(served_data.recommendation_ids)
        return RecommendationServedResponse(marked_as_served=marked_count)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/generate", response_model=RecommendationGenerationResponse)
async def generate_recommendations_endpoint(
    request: RecommendationGenerateRequest,
    db: Session = Depends(get_database_session)
):
    """Generate recommendations for a user using the given algorithm."""

    service = RecommendationService(db)
    try:
        recommendations = service.generate_recommendations(
            user_id=request.user_id,
            algorithm_version=request.algorithm_version,
            limit=request.limit,
        )
        return RecommendationGenerationResponse(
            algorithm_version=request.algorithm_version,
            recommendations=[RecommendationResponse.model_validate(rec) for rec in recommendations],
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/stats/overview")
async def get_recommendation_stats(
    db: Session = Depends(get_database_session)
):
    """Get overall recommendation statistics."""
    service = RecommendationService(db)
    stats = service.get_recommendation_stats()
    return stats
