"""System API routes for health checks and database information."""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings
from genonaut.api.models.responses import (
    HealthResponse,
    DatabaseInfoResponse,
    GlobalStatsResponse,
)
from genonaut.api.services.user_service import UserService
from genonaut.api.services.content_service import ContentService
from genonaut.api.services.interaction_service import InteractionService
from genonaut.api.services.recommendation_service import RecommendationService
from genonaut.api.services.generation_service import GenerationService

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_database_session)):
    """Health check endpoint with database connectivity test."""
    try:
        # Simple query to test database connectivity
        db.execute(text("SELECT 1"))
        return HealthResponse(
            status="healthy",
            database={
                "status": "connected",
            },
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database={
                "status": "disconnected",
            },
            timestamp=datetime.utcnow(),
            error=str(e),
        )


@router.get("/databases", response_model=DatabaseInfoResponse)
async def get_database_info():
    """Get database information."""
    settings = get_settings()
    
    available_databases = ["dev", "demo"]
    current_database = settings.api_environment
    
    return DatabaseInfoResponse(
        available_databases=available_databases,
        current_database=current_database
    )


@router.get("/stats/global", response_model=GlobalStatsResponse)
async def get_global_stats(db: Session = Depends(get_database_session)):
    """Get global system statistics."""
    try:
        # Get stats from all services
        user_service = UserService(db)
        content_service = ContentService(db)
        interaction_service = InteractionService(db)
        recommendation_service = RecommendationService(db)
        generation_service = GenerationService(db)

        user_stats = user_service.get_user_stats()
        content_stats = content_service.get_content_stats()
        interaction_stats = interaction_service.get_interaction_stats()
        recommendation_stats = recommendation_service.get_recommendation_stats()
        generation_stats = generation_service.get_generation_stats()

        status_breakdown = generation_stats.get('status_breakdown', {})

        return GlobalStatsResponse(
            total_users=user_stats.get('total_users', 0),
            active_users=user_stats.get('active_users', 0),
            inactive_users=user_stats.get('inactive_users', 0),
            total_content=content_stats.get('total_content', 0),
            public_content=content_stats.get('public_content', 0),
            private_content=content_stats.get('private_content', 0),
            total_interactions=interaction_stats.get('total_interactions', 0),
            total_recommendations=recommendation_stats.get('total_recommendations', 0),
            served_recommendations=recommendation_stats.get('served_recommendations', 0),
            unserved_recommendations=recommendation_stats.get('unserved_recommendations', 0),
            total_generation_jobs=generation_stats.get('total_jobs', 0),
            running_generation_jobs=status_breakdown.get('running', 0),
            completed_generation_jobs=status_breakdown.get('completed', 0),
            failed_generation_jobs=status_breakdown.get('failed', 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve global statistics: {str(e)}"
        )
