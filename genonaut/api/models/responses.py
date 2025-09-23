"""Pydantic response models for the Genonaut API."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from genonaut.api.models.enums import ContentType, InteractionType, JobStatus, JobType


class UserResponse(BaseModel):
    """Response model for user data."""
    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    is_active: bool = Field(..., description="User active status")
    
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Response model for list of users."""

    items: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class UserStatsResponse(BaseModel):
    """Response model for user statistics."""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")


class UserActivityStatsResponse(BaseModel):
    """Response model for per-user activity statistics."""

    total_interactions: int = Field(..., description="Total interactions performed by the user")
    content_created: int = Field(..., description="Number of content items created by the user")
    avg_rating_given: float = Field(..., description="Average rating given by the user")


class ContentResponse(BaseModel):
    """Response model for content data."""
    id: int = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    content_type: ContentType = Field(..., description="Content type")
    content_data: str = Field(..., description="Content data")
    item_metadata: Dict[str, Any] = Field(..., description="Content metadata")
    creator_id: UUID = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Content creation timestamp")
    tags: List[str] = Field(..., description="Content tags")
    quality_score: float = Field(..., description="Content quality score")
    is_private: bool = Field(..., description="Private status")
    
    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    """Response model for list of content."""

    items: List[ContentResponse] = Field(..., description="List of content items")
    total: int = Field(..., description="Total number of content items")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class ContentAutoResponse(ContentResponse):
    """Response model for automatically generated content."""


class ContentAutoListResponse(BaseModel):
    """Response model for list of automatically generated content."""

    items: List[ContentAutoResponse] = Field(..., description="List of automated content items")
    total: int = Field(..., description="Total number of automated content items")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class ContentStatsResponse(BaseModel):
    """Response model for content statistics."""
    total_content: int = Field(..., description="Total number of content items")
    private_content: int = Field(..., description="Number of private content items")
    type_breakdown: Dict[str, int] = Field(..., description="Content count by type")


class InteractionResponse(BaseModel):
    """Response model for interaction data."""
    id: int = Field(..., description="Interaction ID")
    user_id: UUID = Field(..., description="User ID")
    content_item_id: int = Field(..., description="Content item ID")
    interaction_type: InteractionType = Field(..., description="Interaction type")
    rating: Optional[int] = Field(..., description="Rating (1-5 scale)")
    duration: Optional[int] = Field(..., description="Duration in seconds")
    created_at: datetime = Field(..., description="Interaction timestamp")
    interaction_metadata: Dict[str, Any] = Field(..., description="Interaction metadata")
    
    model_config = {"from_attributes": True}


class InteractionListResponse(BaseModel):
    """Response model for list of interactions."""

    items: List[InteractionResponse] = Field(..., description="List of interactions")
    total: int = Field(..., description="Total number of interactions")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class InteractionStatsResponse(BaseModel):
    """Response model for interaction statistics by content."""
    content_item_id: int = Field(..., description="Content item ID")
    stats: Dict[str, Dict[str, Any]] = Field(..., description="Statistics by interaction type")


class InteractionSummaryResponse(BaseModel):
    """Response model for user interaction summary."""
    user_id: UUID = Field(..., description="User ID")
    summary: Dict[str, Any] = Field(..., description="Interaction summary by type")


class RecommendationResponse(BaseModel):
    """Response model for recommendation data."""
    id: int = Field(..., description="Recommendation ID")
    user_id: UUID = Field(..., description="User ID")
    content_item_id: int = Field(..., description="Content item ID")
    recommendation_score: float = Field(..., description="Recommendation score")
    algorithm_version: str = Field(..., description="Algorithm version")
    created_at: datetime = Field(..., description="Recommendation creation timestamp")
    is_served: bool = Field(..., description="Whether recommendation was served")
    rec_metadata: Dict[str, Any] = Field(..., description="Recommendation metadata")
    
    model_config = {"from_attributes": True}


class RecommendationListResponse(BaseModel):
    """Response model for list of recommendations."""

    items: List[RecommendationResponse] = Field(..., description="List of recommendations")
    total: int = Field(..., description="Total number of recommendations")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class RecommendationStatsResponse(BaseModel):
    """Response model for recommendation statistics."""
    user_id: Optional[UUID] = Field(..., description="User ID (if filtered)")
    total_recommendations: int = Field(..., description="Total number of recommendations")
    served_recommendations: int = Field(..., description="Number of served recommendations")
    unserved_recommendations: int = Field(..., description="Number of unserved recommendations")
    average_score: float = Field(..., description="Average recommendation score")
    algorithm_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="Statistics by algorithm")


class RecommendationGenerationResponse(BaseModel):
    """Response model for recommendation generation."""

    algorithm_version: str = Field(..., description="Algorithm version used for generation")
    recommendations: List[RecommendationResponse] = Field(default_factory=list, description="Generated recommendations")


class RecommendationServedResponse(BaseModel):
    """Response model for marking recommendations as served."""
    marked_as_served: int = Field(..., description="Number of recommendations marked as served")


class GenerationJobResponse(BaseModel):
    """Response model for generation job data."""
    id: int = Field(..., description="Job ID")
    user_id: UUID = Field(..., description="User ID")
    job_type: JobType = Field(..., description="Job type")
    prompt: str = Field(..., description="Generation prompt")
    parameters: Dict[str, Any] = Field(..., description="Generation parameters")
    status: JobStatus = Field(..., description="Job status")
    result_content_id: Optional[int] = Field(..., description="Result content ID")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(..., description="Job start timestamp")
    completed_at: Optional[datetime] = Field(..., description="Job completion timestamp")
    error_message: Optional[str] = Field(..., description="Error message if failed")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Job last update timestamp")
    
    model_config = {"from_attributes": True}


class GenerationJobListResponse(BaseModel):
    """Response model for list of generation jobs."""

    items: List[GenerationJobResponse] = Field(..., description="List of generation jobs")
    total: int = Field(..., description="Total number of jobs")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class GenerationJobStatsResponse(BaseModel):
    """Response model for generation job statistics."""
    user_id: Optional[UUID] = Field(..., description="User ID (if filtered)")
    total_jobs: int = Field(..., description="Total number of jobs")
    status_breakdown: Dict[str, int] = Field(..., description="Job count by status")
    type_breakdown: Dict[str, int] = Field(..., description="Job count by type")
    average_processing_time_seconds: Optional[float] = Field(..., description="Average processing time")


# Common response models
class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = Field(False, description="Success status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    database: Dict[str, Any] = Field(..., description="Database connectivity details")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DatabaseInfoResponse(BaseModel):
    """Database information response."""
    available_databases: List[str] = Field(..., description="List of available databases")
    current_database: str = Field(..., description="Currently selected database")


# Pagination response wrapper
class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    data: List[Any] = Field(..., description="Response data")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    has_more: bool = Field(..., description="Whether there are more items available")


# Enhanced response models with related data
class ContentWithCreatorResponse(ContentResponse):
    """Content response with creator information."""
    creator: UserResponse = Field(..., description="Content creator information")


class InteractionWithDetailsResponse(InteractionResponse):
    """Interaction response with user and content details."""
    user: UserResponse = Field(..., description="User information")
    content: ContentResponse = Field(..., description="Content information")


class RecommendationWithDetailsResponse(RecommendationResponse):
    """Recommendation response with user and content details."""
    user: UserResponse = Field(..., description="User information")
    content: ContentResponse = Field(..., description="Content information")


class GenerationJobWithResultResponse(GenerationJobResponse):
    """Generation job response with result content."""
    result_content: Optional[ContentResponse] = Field(..., description="Generated content result")


# Statistics aggregation responses
class GlobalStatsResponse(BaseModel):
    """Flattened global system statistics for dashboards/tests."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")

    total_content: int = Field(..., description="Total number of content items")
    private_content: int = Field(..., description="Number of private content items")

    total_interactions: int = Field(..., description="Total number of recorded interactions")

    total_recommendations: int = Field(..., description="Total number of recommendations")
    served_recommendations: int = Field(..., description="Number of served recommendations")
    unserved_recommendations: int = Field(..., description="Number of pending recommendations")

    total_generation_jobs: int = Field(..., description="Total generation jobs")
    running_generation_jobs: int = Field(..., description="Generation jobs currently running")
    completed_generation_jobs: int = Field(..., description="Completed generation jobs")
    failed_generation_jobs: int = Field(..., description="Failed generation jobs")
