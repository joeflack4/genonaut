"""Unit tests for Pydantic API models."""

import pytest
from uuid import uuid4, UUID
from pydantic import ValidationError

from genonaut.api.models.requests import (
    UserCreateRequest, UserUpdateRequest, UserPreferencesUpdateRequest,
    ContentCreateRequest, ContentUpdateRequest, ContentQualityUpdateRequest,
    InteractionCreateRequest, InteractionUpdateRequest,
    RecommendationCreateRequest, RecommendationBulkCreateRequest,
    GenerationJobCreateRequest, GenerationJobStatusUpdateRequest,
    ContentSearchRequest, UserSearchRequest
)
from genonaut.api.models.responses import (
    UserResponse, ContentResponse, InteractionResponse,
    RecommendationResponse, GenerationJobResponse,
    ErrorResponse, PaginatedResponse
)
from genonaut.api.models.enums import ContentType, InteractionType, JobType

# Test UUIDs for consistent use across tests
TEST_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_CREATOR_ID = UUID("550e8400-e29b-41d4-a716-446655440001")
TEST_CONTENT_ID = UUID("550e8400-e29b-41d4-a716-446655440002")


class TestUserModels:
    """Test user-related request/response models."""
    
    def test_user_create_request_valid(self):
        """Test valid user creation request."""
        data = {
            "username": "test_user",
            "email": "test@example.com",
            "preferences": {"theme": "dark", "notifications": True}
        }
        user = UserCreateRequest(**data)
        assert user.username == "test_user"
        assert user.email == "test@example.com"
        assert user.preferences == {"theme": "dark", "notifications": True}
    
    def test_user_create_request_invalid_username(self):
        """Test user creation with invalid username."""
        data = {
            "username": "invalid username with spaces",
            "email": "test@example.com"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreateRequest(**data)
        assert "Username can only contain letters, numbers, hyphens, and underscores" in str(exc_info.value)
    
    def test_user_create_request_invalid_email(self):
        """Test user creation with invalid email."""
        data = {
            "username": "test_user",
            "email": "invalid-email"
        }
        with pytest.raises(ValidationError):
            UserCreateRequest(**data)
    
    def test_user_create_request_short_username(self):
        """Test user creation with too short username."""
        data = {
            "username": "ab",
            "email": "test@example.com"
        }
        with pytest.raises(ValidationError):
            UserCreateRequest(**data)
    
    def test_user_update_request_valid(self):
        """Test valid user update request."""
        data = {
            "username": "new_username",
            "email": "new@example.com",
            "is_active": False
        }
        user = UserUpdateRequest(**data)
        assert user.username == "new_username"
        assert user.email == "new@example.com"
        assert user.is_active is False
    
    def test_user_update_request_empty(self):
        """Test user update request with no fields."""
        user = UserUpdateRequest()
        assert user.username is None
        assert user.email is None
        assert user.is_active is None
    
    def test_user_preferences_update_request(self):
        """Test user preferences update request."""
        data = {
            "preferences": {"new_setting": "value", "count": 42}
        }
        prefs = UserPreferencesUpdateRequest(**data)
        assert prefs.preferences == {"new_setting": "value", "count": 42}


class TestContentModels:
    """Test content-related request/response models."""
    
    def test_content_create_request_valid(self):
        """Test valid content creation request."""
        data = {
            "title": "Test Content",
            "content_type": ContentType.TEXT,
            "content_data": "This is test content",
            "prompt": "Test prompt",
            "creator_id": TEST_CREATOR_ID,
            "item_metadata": {"category": "test"},
            "tags": ["tag1", "tag2"],
            "is_public": True,
            "is_private": False
        }
        content = ContentCreateRequest(**data)
        assert content.title == "Test Content"
        assert content.content_type == ContentType.TEXT
        assert content.creator_id == TEST_CREATOR_ID
        assert set(content.tags) == {"tag1", "tag2"}
    
    def test_content_create_request_invalid_creator_id(self):
        """Test content creation with invalid creator ID."""
        data = {
            "title": "Test Content",
            "content_type": ContentType.TEXT,
            "content_data": "This is test content",
            "prompt": "Test prompt",
            "creator_id": "invalid-uuid"  # Invalid UUID format
        }
        with pytest.raises(ValidationError):
            ContentCreateRequest(**data)

    def test_content_create_request_valid_private(self):
        """Test content creation with private setting."""
        data = {
            "title": "Test Content",
            "content_type": ContentType.TEXT,
            "content_data": "This is test content",
            "prompt": "Test prompt",
            "creator_id": TEST_CREATOR_ID,
            "is_private": True
        }
        content = ContentCreateRequest(**data)
        assert content.is_private is True

    def test_content_create_request_too_many_tags(self):
        """Test content creation with too many tags."""
        data = {
            "title": "Test Content",
            "content_type": ContentType.TEXT,
            "content_data": "This is test content",
            "prompt": "Test prompt",
            "creator_id": TEST_CREATOR_ID,
            "tags": [f"tag{i}" for i in range(25)]  # Too many tags
        }
        with pytest.raises(ValidationError) as exc_info:
            ContentCreateRequest(**data)
        assert "Cannot have more than 20 tags" in str(exc_info.value)

    def test_content_create_request_duplicate_tags(self):
        """Test content creation removes duplicate tags."""
        data = {
            "title": "Test Content",
            "content_type": ContentType.TEXT,
            "content_data": "This is test content",
            "prompt": "Test prompt",
            "creator_id": TEST_CREATOR_ID,
            "tags": ["tag1", "tag2", "tag1", "tag3", "tag2"]  # Duplicates
        }
        content = ContentCreateRequest(**data)
        assert len(content.tags) == 3
        assert set(content.tags) == {"tag1", "tag2", "tag3"}
    
    def test_content_quality_update_request_valid(self):
        """Test valid quality score update."""
        data = {"quality_score": 0.75}
        quality = ContentQualityUpdateRequest(**data)
        assert quality.quality_score == 0.75
    
    def test_content_quality_update_request_invalid_score(self):
        """Test quality score outside valid range."""
        with pytest.raises(ValidationError):
            ContentQualityUpdateRequest(quality_score=1.5)  # > 1.0
        
        with pytest.raises(ValidationError):
            ContentQualityUpdateRequest(quality_score=-0.1)  # < 0.0


class TestInteractionModels:
    """Test interaction-related request/response models."""
    
    def test_interaction_create_request_valid(self):
        """Test valid interaction creation request."""
        data = {
            "user_id": TEST_USER_ID,
            "content_item_id": 2,
            "interaction_type": InteractionType.LIKE,
            "rating": 5,
            "duration": 120,
            "metadata": {"source": "web"}
        }
        interaction = InteractionCreateRequest(**data)
        assert interaction.user_id == TEST_USER_ID
        assert interaction.content_item_id == 2
        assert interaction.interaction_type == InteractionType.LIKE
        assert interaction.rating == 5
        assert interaction.duration == 120
    
    def test_interaction_create_request_invalid_rating(self):
        """Test interaction creation with invalid rating."""
        data = {
            "user_id": TEST_USER_ID,
            "content_item_id": 2,
            "interaction_type": InteractionType.LIKE,
            "rating": 6  # Invalid - must be 1-5
        }
        with pytest.raises(ValidationError):
            InteractionCreateRequest(**data)
    
    def test_interaction_create_request_invalid_user_id(self):
        """Test interaction creation with invalid user ID."""
        data = {
            "user_id": "invalid-uuid",  # Invalid UUID format
            "content_item_id": 2,
            "interaction_type": InteractionType.LIKE
        }
        with pytest.raises(ValidationError):
            InteractionCreateRequest(**data)


class TestRecommendationModels:
    """Test recommendation-related request/response models."""
    
    def test_recommendation_create_request_valid(self):
        """Test valid recommendation creation request."""
        data = {
            "user_id": TEST_USER_ID,
            "content_item_id": 2,
            "recommendation_score": 0.85,
            "algorithm_version": "v1.2",
            "metadata": {"reason": "content_similarity"}
        }
        rec = RecommendationCreateRequest(**data)
        assert rec.user_id == TEST_USER_ID
        assert rec.content_item_id == 2
        assert rec.recommendation_score == 0.85
        assert rec.algorithm_version == "v1.2"
    
    def test_recommendation_create_request_invalid_score(self):
        """Test recommendation creation with invalid score."""
        data = {
            "user_id": TEST_USER_ID,
            "content_item_id": 2,
            "recommendation_score": 1.5,  # Invalid - must be 0-1
            "algorithm_version": "v1.2"
        }
        with pytest.raises(ValidationError):
            RecommendationCreateRequest(**data)
    
    def test_recommendation_bulk_create_request_valid(self):
        """Test valid bulk recommendation creation request."""
        rec_data = {
            "user_id": TEST_USER_ID,
            "content_item_id": 2,
            "recommendation_score": 0.85,
            "algorithm_version": "v1.2"
        }
        data = {
            "recommendations": [rec_data, rec_data]
        }
        bulk_rec = RecommendationBulkCreateRequest(**data)
        assert len(bulk_rec.recommendations) == 2
    
    def test_recommendation_bulk_create_request_empty(self):
        """Test bulk recommendation creation with empty list."""
        data = {"recommendations": []}
        with pytest.raises(ValidationError):
            RecommendationBulkCreateRequest(**data)
    
    def test_recommendation_bulk_create_request_too_many(self):
        """Test bulk recommendation creation with too many recommendations."""
        rec_data = {
            "user_id": TEST_USER_ID,
            "content_item_id": 2,
            "recommendation_score": 0.85,
            "algorithm_version": "v1.2"
        }
        data = {
            "recommendations": [rec_data] * 1001  # Too many
        }
        with pytest.raises(ValidationError):
            RecommendationBulkCreateRequest(**data)


class TestGenerationJobModels:
    """Test generation job-related request/response models."""
    
    def test_generation_job_create_request_valid(self):
        """Test valid generation job creation request."""
        data = {
            "user_id": TEST_USER_ID,
            "job_type": JobType.TEXT,
            "prompt": "Generate a story about space exploration",
            "parameters": {"max_length": 1000, "temperature": 0.7}
        }
        job = GenerationJobCreateRequest(**data)
        assert job.user_id == TEST_USER_ID
        assert job.job_type == JobType.TEXT
        assert job.prompt == "Generate a story about space exploration"
        assert job.parameters == {"max_length": 1000, "temperature": 0.7}
    
    def test_generation_job_create_request_long_prompt(self):
        """Test generation job creation with too long prompt."""
        data = {
            "user_id": TEST_USER_ID,
            "job_type": JobType.TEXT,
            "prompt": "x" * 10001  # Too long
        }
        with pytest.raises(ValidationError):
            GenerationJobCreateRequest(**data)
    
    def test_generation_job_status_update_request_valid(self):
        """Test valid job status update request."""
        data = {
            "status": "completed",
            "error_message": None
        }
        status = GenerationJobStatusUpdateRequest(**data)
        assert status.status == "completed"
        assert status.error_message is None
    
    def test_generation_job_status_update_request_invalid_status(self):
        """Test job status update with invalid status."""
        data = {"status": "invalid_status"}
        with pytest.raises(ValidationError):
            GenerationJobStatusUpdateRequest(**data)


class TestSearchModels:
    """Test search and filter request models."""
    
    def test_content_search_request_valid(self):
        """Test valid content search request."""
        data = {
            "search_term": "test",
            "content_type": ContentType.TEXT,
            "creator_id": TEST_CREATOR_ID,
            "metadata_filter": {"category": "tech"},
            "tags": ["python", "api"],
            "public_only": True,
            "skip": 10,
            "limit": 50
        }
        search = ContentSearchRequest(**data)
        assert search.search_term == "test"
        assert search.content_type == ContentType.TEXT
        assert search.creator_id == TEST_CREATOR_ID
        assert search.skip == 10
        assert search.limit == 50
    
    def test_content_search_request_invalid_limit(self):
        """Test content search with invalid limit."""
        data = {"limit": 1001}  # Too high
        with pytest.raises(ValidationError):
            ContentSearchRequest(**data)
        
        data = {"limit": 0}  # Too low
        with pytest.raises(ValidationError):
            ContentSearchRequest(**data)
    
    def test_user_search_request_defaults(self):
        """Test user search request with default values."""
        search = UserSearchRequest()
        assert search.active_only is False
        assert search.preferences_filter is None
        assert search.skip == 0
        assert search.limit == 100


class TestResponseModels:
    """Test response models."""
    
    def test_error_response_valid(self):
        """Test error response model."""
        data = {
            "error": "ValidationError",
            "detail": "Invalid input data"
        }
        error = ErrorResponse(**data)
        assert error.success is False
        assert error.error == "ValidationError"
        assert error.detail == "Invalid input data"
    
    def test_paginated_response_valid(self):
        """Test paginated response model."""
        data = {
            "items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total_count": 100,
                "has_next": True,
                "has_previous": False
            }
        }
        paginated = PaginatedResponse(**data)
        assert len(paginated.items) == 2
        assert paginated.pagination.total_count == 100
        assert paginated.pagination.has_next is True
        assert paginated.pagination.has_previous is False


class TestEnums:
    """Test enum values."""
    
    def test_content_type_enum(self):
        """Test ContentType enum values."""
        assert ContentType.TEXT == "text"
        assert ContentType.IMAGE == "image"
        assert ContentType.VIDEO == "video"
        assert ContentType.AUDIO == "audio"
    
    def test_interaction_type_enum(self):
        """Test InteractionType enum values."""
        assert InteractionType.VIEW == "view"
        assert InteractionType.LIKE == "like"
        assert InteractionType.SHARE == "share"
        assert InteractionType.COMMENT == "comment"
        assert InteractionType.DOWNLOAD == "download"
    
    def test_job_type_enum(self):
        """Test JobType enum values."""
        assert JobType.TEXT == "text_generation"
        assert JobType.IMAGE == "image_generation"
        assert JobType.VIDEO == "video_generation"
        assert JobType.AUDIO == "audio_generation"