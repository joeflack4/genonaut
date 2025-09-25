"""Pydantic request models for the Genonaut API."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator, EmailStr

from genonaut.api.models.enums import ContentType, InteractionType, JobType


class UserCreateRequest(BaseModel):
    """Request model for creating a user."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v


class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")
    email: Optional[EmailStr] = Field(None, description="New email address")
    is_active: Optional[bool] = Field(None, description="User active status")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v


class UserPreferencesUpdateRequest(BaseModel):
    """Request model for updating user preferences."""
    preferences: Dict[str, Any] = Field(..., description="User preferences to merge with existing ones")


class ContentCreateRequest(BaseModel):
    """Request model for creating content."""
    title: str = Field(..., min_length=1, max_length=255, description="Content title")
    content_type: ContentType = Field(..., description="Type of content")
    content_data: str = Field(..., min_length=1, description="The actual content or reference to it")
    creator_id: UUID = Field(..., description="ID of the user creating the content")
    item_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Content metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Content tags")
    is_private: bool = Field(False, description="Whether content is private")

    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Remove duplicates and empty tags
            v = list(set(tag.strip() for tag in v if tag.strip()))
            # Limit number of tags
            if len(v) > 20:
                raise ValueError('Cannot have more than 20 tags')
        return v


class ContentUpdateRequest(BaseModel):
    """Request model for updating content."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New content title")
    content_data: Optional[str] = Field(None, min_length=1, description="New content data")
    item_metadata: Optional[Dict[str, Any]] = Field(None, description="New content metadata")
    tags: Optional[List[str]] = Field(None, description="New content tags")
    is_private: Optional[bool] = Field(None, description="New private status")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            # Remove duplicates and empty tags
            v = list(set(tag.strip() for tag in v if tag.strip()))
            # Limit number of tags
            if len(v) > 20:
                raise ValueError('Cannot have more than 20 tags')
        return v


class ContentQualityUpdateRequest(BaseModel):
    """Request model for updating content quality score."""
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score between 0.0 and 1.0")


class InteractionCreateRequest(BaseModel):
    """Request model for creating an interaction."""
    user_id: UUID = Field(..., description="User ID")
    content_item_id: int = Field(..., gt=0, description="Content item ID")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5 scale)")
    duration: Optional[int] = Field(None, ge=0, description="Duration in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Interaction metadata")


class InteractionUpdateRequest(BaseModel):
    """Request model for updating an interaction."""
    rating: Optional[int] = Field(None, ge=1, le=5, description="New rating (1-5 scale)")
    duration: Optional[int] = Field(None, ge=0, description="New duration in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New interaction metadata")


class RecommendationCreateRequest(BaseModel):
    """Request model for creating a recommendation."""
    user_id: UUID = Field(..., description="User ID")
    content_item_id: int = Field(..., gt=0, description="Content item ID")
    recommendation_score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score (0-1)")
    algorithm_version: str = Field(..., min_length=1, max_length=50, description="Algorithm version")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Recommendation metadata")


class RecommendationBulkCreateRequest(BaseModel):
    """Request model for bulk creating recommendations."""
    recommendations: List[RecommendationCreateRequest] = Field(..., min_items=1, max_items=1000, description="List of recommendations to create")


class RecommendationUpdateRequest(BaseModel):
    """Request model for updating a recommendation."""
    recommendation_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="New recommendation score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New recommendation metadata")


class RecommendationServedRequest(BaseModel):
    """Request model for marking recommendations as served."""
    recommendation_ids: List[int] = Field(..., min_items=1, description="List of recommendation IDs to mark as served")


class GenerationJobCreateRequest(BaseModel):
    """Request model for creating a generation job."""
    user_id: UUID = Field(..., description="User ID")
    job_type: JobType = Field(..., description="Type of generation job")
    prompt: str = Field(..., min_length=1, max_length=10000, description="Generation prompt")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generation parameters")

    @validator('job_type', pre=True)
    def normalize_job_type(cls, value):
        if isinstance(value, JobType):
            return value
        if isinstance(value, str):
            normalized = value.lower()
            mapping = {
                'text_generation': JobType.TEXT,
                'text': JobType.TEXT,
                'image_generation': JobType.IMAGE,
                'image': JobType.IMAGE,
                'video_generation': JobType.VIDEO,
                'video': JobType.VIDEO,
                'audio_generation': JobType.AUDIO,
                'audio': JobType.AUDIO,
            }
            if normalized in mapping:
                return mapping[normalized]
            try:
                return JobType(normalized)
            except ValueError:
                raise ValueError(f"Unsupported job type: {value}")
        return value


class GenerationJobUpdateRequest(BaseModel):
    """Request model for updating a generation job."""
    parameters: Optional[Dict[str, Any]] = Field(None, description="New generation parameters")


class GenerationJobStatusUpdateRequest(BaseModel):
    """Request model for updating generation job status."""
    status: str = Field(..., pattern="^(pending|running|completed|failed|cancelled)$", description="New job status")
    error_message: Optional[str] = Field(None, description="Error message for failed jobs")


class GenerationJobResultRequest(BaseModel):
    """Request model for setting generation job result."""
    content_id: int = Field(..., gt=0, description="ID of the generated content item")


class GenerationJobCancelRequest(BaseModel):
    """Request model for cancelling a generation job."""
    reason: Optional[str] = Field(None, description="Optional reason for cancellation")


# Search and filter request models
class ContentSearchRequest(BaseModel):
    """Request model for searching content."""
    search_term: Optional[str] = Field(None, description="Search term for title")
    content_type: Optional[ContentType] = Field(None, description="Filter by content type")
    creator_id: Optional[UUID] = Field(None, description="Filter by creator ID")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    tags: Optional[List[str]] = Field(None, description="Tags to search for")
    public_only: bool = Field(False, description="Return only public content")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class UserSearchRequest(BaseModel):
    """Request model for searching users."""
    active_only: bool = Field(False, description="Return only active users")
    preferences_filter: Optional[Dict[str, Any]] = Field(None, description="Preferences filters")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class RecommendationSearchRequest(BaseModel):
    """Request model for searching recommendations."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    content_item_id: Optional[int] = Field(None, gt=0, description="Filter by content item ID")
    algorithm_version: Optional[str] = Field(None, description="Filter by algorithm version")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum recommendation score")
    unserved_only: bool = Field(False, description="Return only unserved recommendations")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class RecommendationGenerateRequest(BaseModel):
    """Request model for generating recommendations."""

    user_id: UUID = Field(..., description="Target user ID")
    algorithm_version: str = Field(..., min_length=1, description="Requested algorithm version")
    limit: int = Field(10, ge=1, le=100, description="Maximum recommendations to generate")


class InteractionSearchRequest(BaseModel):
    """Request model for searching interactions."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    content_item_id: Optional[int] = Field(None, gt=0, description="Filter by content item ID")
    interaction_type: Optional[InteractionType] = Field(None, description="Filter by interaction type")
    days: Optional[int] = Field(None, ge=1, le=365, description="Days to look back for recent interactions")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class GenerationJobSearchRequest(BaseModel):
    """Request model for searching generation jobs."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    job_type: Optional[JobType] = Field(None, description="Filter by job type")
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed|cancelled)$", description="Filter by status")
    days: Optional[int] = Field(None, ge=1, le=365, description="Days to look back")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")

    @validator('job_type', pre=True)
    def normalize_search_job_type(cls, value):
        if value is None:
            return value
        if isinstance(value, JobType):
            return value
        if isinstance(value, str):
            normalized = value.lower()
            mapping = {
                'text_generation': JobType.TEXT,
                'text': JobType.TEXT,
                'image_generation': JobType.IMAGE,
                'image': JobType.IMAGE,
                'video_generation': JobType.VIDEO,
                'video': JobType.VIDEO,
                'audio_generation': JobType.AUDIO,
                'audio': JobType.AUDIO,
            }
            if normalized in mapping:
                return mapping[normalized]
            try:
                return JobType(normalized)
            except ValueError:
                raise ValueError(f"Unsupported job type: {value}")
        return value



class PaginationRequest(BaseModel):
    """Request model for pagination parameters."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")
    cursor: Optional[str] = Field(None, description="Cursor for cursor-based pagination")
    sort_field: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

    @validator('cursor')
    def clean_cursor(cls, v):
        """Clean up cursor value - empty strings become None."""
        if v is not None and v.strip() == "":
            return None
        return v

    @property
    def skip(self) -> int:
        """Calculate skip value for offset-based pagination."""
        return (self.page - 1) * self.page_size


class ComfyUIGenerationCreateRequest(BaseModel):
    """Request model for creating a ComfyUI generation."""
    user_id: UUID = Field(..., description="User ID for the generation request")
    prompt: str = Field(..., min_length=1, max_length=2000, description="Positive prompt for generation")
    negative_prompt: Optional[str] = Field("", max_length=2000, description="Negative prompt for generation")
    checkpoint_model: str = Field(..., min_length=1, max_length=255, description="Checkpoint model name")
    lora_models: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="LoRA models with strengths")
    width: int = Field(832, ge=64, le=2048, description="Image width")
    height: int = Field(1216, ge=64, le=2048, description="Image height")
    batch_size: int = Field(1, ge=1, le=8, description="Number of images to generate")
    sampler_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="KSampler parameters")

    @validator('lora_models')
    def validate_lora_models(cls, v):
        if v is not None:
            for lora in v:
                if not isinstance(lora, dict) or 'name' not in lora:
                    raise ValueError("LoRA models must contain 'name' field")
        return v


class ComfyUIModelListRequest(BaseModel):
    """Request model for listing available ComfyUI models."""
    model_type: Optional[str] = Field(None, description="Filter by model type (checkpoint, lora)")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, max_length=255, description="Search in model names")


class ComfyUIGenerationListRequest(PaginationRequest):
    """Request model for listing ComfyUI generations."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by generation status")
    created_after: Optional[str] = Field(None, description="Filter generations created after this date")
    created_before: Optional[str] = Field(None, description="Filter generations created before this date")
