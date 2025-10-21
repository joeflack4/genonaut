"""Pydantic response models for the Genonaut API."""

from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, computed_field

T = TypeVar('T')

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
    """Response model for content data.

    Note:
        Tags are stored in the content_tags junction table and should be fetched
        separately when needed. They are no longer directly on the content model.
    """
    id: int = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    content_type: ContentType = Field(..., description="Content type")
    content_data: str = Field(..., description="Content data")
    path_thumb: Optional[str] = Field(None, description="Path to thumbnail image on disk")
    path_thumbs_alt_res: Optional[Dict[str, str]] = Field(
        None,
        description="Mapping of alternate thumbnail resolution identifiers to disk paths",
    )
    prompt: Optional[str] = Field(None, description="Generation prompt (only included in detail views)")
    item_metadata: Dict[str, Any] = Field(..., description="Content metadata")
    creator_id: UUID = Field(..., description="Creator user ID")
    creator_username: Optional[str] = Field(None, description="Creator username")
    created_at: datetime = Field(..., description="Content creation timestamp")
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
    """Response model for generation job data.

    This model includes both general generation job fields and ComfyUI-specific fields.
    """
    id: int = Field(..., description="Job ID")
    user_id: UUID = Field(..., description="User ID")
    job_type: JobType = Field(..., description="Job type")
    prompt: str = Field(..., description="Generation prompt")
    params: Dict[str, Any] = Field(..., description="Generation parameters")
    status: JobStatus = Field(..., description="Job status")
    content_id: Optional[int] = Field(..., description="Result content ID")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(..., description="Job start timestamp")
    completed_at: Optional[datetime] = Field(..., description="Job completion timestamp")
    error_message: Optional[str] = Field(..., description="Error message if failed")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Job last update timestamp")

    # Celery integration fields
    celery_task_id: Optional[str] = Field(None, description="Celery task ID for async processing")

    # ComfyUI-specific fields
    negative_prompt: Optional[str] = Field(None, description="Negative prompt for ComfyUI generation")
    checkpoint_model: Optional[str] = Field(None, description="Checkpoint model name for ComfyUI")
    lora_models: Optional[List[Dict[str, Any]]] = Field(None, description="LoRA models with strengths for ComfyUI")
    width: Optional[int] = Field(None, description="Image width for ComfyUI")
    height: Optional[int] = Field(None, description="Image height for ComfyUI")
    batch_size: Optional[int] = Field(None, description="Number of images to generate for ComfyUI")
    comfyui_prompt_id: Optional[str] = Field(None, description="ComfyUI workflow prompt ID")

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


class NotificationResponse(BaseModel):
    """Response model for notification data."""
    id: int = Field(..., description="Notification ID")
    user_id: UUID = Field(..., description="User ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: str = Field(..., description="Notification type")
    read_status: bool = Field(..., description="Read status")
    related_job_id: Optional[int] = Field(None, description="Related generation job ID")
    related_content_id: Optional[int] = Field(None, description="Related content item ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Response model for list of notifications."""
    items: List[NotificationResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total number of notifications")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    """Response model for unread notification count."""
    unread_count: int = Field(..., description="Number of unread notifications")


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


# Pagination response wrapper (DEPRECATED - use new PaginatedResponse below)
class PaginatedResponseOld(BaseModel):
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



class PaginationMeta(BaseModel):
    """Pagination metadata for responses."""
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=1000, description="Items per page")
    total_count: int = Field(..., ge=0, description="Total number of items")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    prev_cursor: Optional[str] = Field(None, description="Cursor for previous page")

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.total_count == 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    model_config = {"from_attributes": True}


class AvailableModelResponse(BaseModel):
    """Response model for available ComfyUI models."""
    id: int = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    type: str = Field(..., description="Model type (checkpoint, lora)")
    file_path: str = Field(..., description="Path to model file")
    description: Optional[str] = Field(None, description="Model description")
    is_active: bool = Field(..., description="Whether model is active")
    created_at: datetime = Field(..., description="Model creation timestamp")
    updated_at: datetime = Field(..., description="Model last update timestamp")

    model_config = {"from_attributes": True}


class ComfyUIGenerationResponse(BaseModel):
    """Response model for ComfyUI generation requests."""
    id: int = Field(..., description="Generation request ID")
    user_id: UUID = Field(..., description="User ID")
    prompt: str = Field(..., description="Positive prompt")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt")
    checkpoint_model: str = Field(..., description="Checkpoint model name")
    lora_models: List[Dict[str, Any]] = Field(..., description="LoRA models with strengths")
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    batch_size: int = Field(..., description="Number of images to generate")
    sampler_params: Dict[str, Any] = Field(..., description="KSampler parameters")
    status: str = Field(..., description="Generation status")
    comfyui_prompt_id: Optional[str] = Field(None, description="ComfyUI workflow prompt ID")
    output_paths: List[str] = Field(..., description="Generated image file paths")
    thumbnail_paths: List[str] = Field(..., description="Thumbnail file paths")
    created_at: datetime = Field(..., description="Request creation timestamp")
    updated_at: datetime = Field(..., description="Request last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Generation start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Generation completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = {"from_attributes": True}


class ComfyUIGenerationListResponse(PaginatedResponse):
    """Response model for ComfyUI generation list."""
    items: List[ComfyUIGenerationResponse] = Field(..., description="List of generation requests")


class AvailableModelListResponse(BaseModel):
    """Response model for available model list."""
    items: List[AvailableModelResponse] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")

    model_config = {"from_attributes": True}


class TagSummaryResponse(BaseModel):
    """Compact representation of a tag."""

    id: UUID = Field(..., description="Tag identifier")
    name: str = Field(..., description="Human-readable tag name")

    model_config = {"from_attributes": True}


class TagRelationResponse(TagSummaryResponse):
    """Tag summary including traversal depth for ancestor/descendant routes."""

    depth: int = Field(..., ge=0, description="Depth relative to the requested tag")


class PopularTagResponse(TagSummaryResponse):
    """Tag summary with content cardinality (popularity count)."""

    cardinality: int = Field(..., ge=0, description="Number of content items associated with this tag")


class TagResponse(TagSummaryResponse):
    """Detailed representation of a tag including metadata and ratings."""

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary tag metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    average_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Average rating across users (null if no ratings)",
    )
    rating_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of ratings contributing to the average",
    )
    is_favorite: Optional[bool] = Field(
        None,
        description="Whether the requesting user has favorited this tag",
    )


class TagHierarchyNode(BaseModel):
    """Response model for a single tag hierarchy node."""

    id: str = Field(..., description="Tag identifier (legacy name slug)")
    name: str = Field(..., description="Human-readable tag name")
    parent: Optional[str] = Field(None, description="Parent tag ID, null for root nodes")
    average_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Average rating for the tag when requested",
    )
    rating_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of ratings included in the average",
    )


class TagHierarchyMetadata(BaseModel):
    """Metadata for tag hierarchy response."""

    totalNodes: int = Field(..., description="Total number of nodes in hierarchy")
    totalRelationships: int = Field(..., description="Total number of parent-child relationships")
    rootCategories: int = Field(..., description="Number of root categories")
    lastUpdated: datetime = Field(..., description="Last update timestamp")
    format: str = Field(..., description="Data format identifier")
    version: str = Field(..., description="Schema version")


class TagHierarchyResponse(BaseModel):
    """Response model for tag hierarchy data."""

    nodes: List[TagHierarchyNode] = Field(..., description="List of all nodes in flat array format")
    metadata: TagHierarchyMetadata = Field(..., description="Hierarchy metadata and statistics")

    model_config = {"from_attributes": True}


class TagDetailResponse(BaseModel):
    """Complete detail view of a tag including relationships and ratings."""

    tag: TagResponse = Field(..., description="Primary tag information")
    parents: List[TagSummaryResponse] = Field(..., description="Direct parent tags")
    children: List[TagSummaryResponse] = Field(..., description="Direct child tags")
    ancestors: Optional[List[TagRelationResponse]] = Field(
        None,
        description="Optional list of ancestor tags with depth metadata",
    )
    descendants: Optional[List[TagRelationResponse]] = Field(
        None,
        description="Optional list of descendant tags with depth metadata",
    )
    average_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Average rating for the tag",
    )
    rating_count: int = Field(0, ge=0, description="Number of ratings recorded for the tag")
    user_rating: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Rating supplied by the requesting user, if any",
    )
    is_favorite: Optional[bool] = Field(
        None,
        description="Whether the requesting user has favorited the tag",
    )


class TagRatingResponse(BaseModel):
    """Response model representing a single tag rating."""

    id: int = Field(..., description="Database identifier for the rating")
    user_id: UUID = Field(..., description="User who supplied the rating")
    tag_id: UUID = Field(..., description="Tag that was rated")
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating value")
    created_at: datetime = Field(..., description="Rating creation timestamp")
    updated_at: datetime = Field(..., description="Rating last update timestamp")

    model_config = {"from_attributes": True}


class TagRatingValueResponse(BaseModel):
    """Response model representing a user's rating value for a tag."""

    rating: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Rating value if present; null when user has not rated the tag",
    )


class TagStatisticsResponse(BaseModel):
    """Response model for global tag statistics."""

    totalNodes: int = Field(..., description="Total number of tags")
    totalRelationships: int = Field(..., description="Total parent-child relationships")
    rootCategories: int = Field(..., description="Number of root-level categories")


class TagListResponse(PaginatedResponse[TagResponse]):
    """Paginated list response for tags."""

    model_config = {"from_attributes": True}


class TagUserRatingsResponse(BaseModel):
    """Mapping of tag IDs to the requesting user's ratings."""

    ratings: Dict[UUID, float] = Field(default_factory=dict, description="Mapping of tag IDs to rating values")


class CheckpointModelResponse(BaseModel):
    """Response model for checkpoint model data."""
    id: UUID = Field(..., description="Checkpoint model ID")
    path: str = Field(..., description="File path to checkpoint model")
    filename: Optional[str] = Field(None, description="Filename of checkpoint model")
    name: Optional[str] = Field(None, description="Display name of checkpoint model")
    version: Optional[str] = Field(None, description="Version of checkpoint model")
    architecture: Optional[str] = Field(None, description="Model architecture (e.g., sd1, sdxl)")
    family: Optional[str] = Field(None, description="Model family")
    description: Optional[str] = Field(None, description="Description of checkpoint model")
    rating: Optional[float] = Field(None, description="Quality rating (0-1)")
    tags: List[str] = Field(..., description="Tags associated with checkpoint model")
    model_metadata: Dict[str, Any] = Field(..., description="Additional model metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class CheckpointModelListResponse(BaseModel):
    """Response model for list of checkpoint models."""
    items: List[CheckpointModelResponse] = Field(..., description="List of checkpoint models")
    total: int = Field(..., description="Total number of checkpoint models")

    model_config = {"from_attributes": True}


class LoraModelResponse(BaseModel):
    """Response model for LoRA model data."""
    id: UUID = Field(..., description="LoRA model ID")
    path: str = Field(..., description="File path to LoRA model")
    filename: Optional[str] = Field(None, description="Filename of LoRA model")
    name: Optional[str] = Field(None, description="Display name of LoRA model")
    version: Optional[str] = Field(None, description="Version of LoRA model")
    compatible_architectures: Optional[str] = Field(None, description="Compatible architectures")
    family: Optional[str] = Field(None, description="Model family")
    description: Optional[str] = Field(None, description="Description of LoRA model")
    rating: Optional[float] = Field(None, description="Quality rating (0-1)")
    tags: List[str] = Field(..., description="Tags associated with LoRA model")
    trigger_words: List[str] = Field(..., description="Trigger words for LoRA model")
    optimal_checkpoints: List[str] = Field(..., description="Optimal checkpoint models to use with this LoRA")
    model_metadata: Dict[str, Any] = Field(..., description="Additional model metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_compatible: Optional[bool] = Field(None, description="Whether LoRA is compatible with selected checkpoint")
    is_optimal: Optional[bool] = Field(None, description="Whether LoRA is optimal for selected checkpoint")

    model_config = {"from_attributes": True}


class LoraModelPaginationMeta(BaseModel):
    """Pagination metadata for LoRA model list."""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = {"from_attributes": True}


class LoraModelListResponse(BaseModel):
    """Response model for list of LoRA models."""
    items: List[LoraModelResponse] = Field(..., description="List of LoRA models")
    total: int = Field(..., description="Total number of LoRA models")
    pagination: Optional[LoraModelPaginationMeta] = Field(None, description="Pagination metadata")

    model_config = {"from_attributes": True}
