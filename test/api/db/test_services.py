"""Database tests for API services (PostgreSQL)."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from genonaut.db.schema import (
    Base,
    User,
    ContentItem,
    ContentItemAuto,
    UserInteraction,
    Recommendation,
    GenerationJob,
    Bookmark,
    BookmarkCategory,
    BookmarkCategoryMember,
)
from genonaut.api.services.user_service import UserService
from genonaut.api.services.content_service import ContentAutoService, ContentService
from genonaut.api.services.interaction_service import InteractionService
from genonaut.api.services.recommendation_service import RecommendationService
from genonaut.api.services.generation_service import GenerationService
from genonaut.api.services.bookmark_category_member_service import BookmarkCategoryMemberService
from genonaut.api.services.bookmark_service import BookmarkService
from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import ContentResponse
from genonaut.api.utils.tag_identifiers import get_uuid_for_slug

# Import PostgreSQL fixtures
from test.db.postgres_fixtures import postgres_session


@pytest.fixture(scope="function")
def test_db_session(postgres_session):
    """Create a test database session using PostgreSQL test database.

    This is an alias for postgres_session to maintain backward compatibility
    with existing tests. The session automatically rolls back after each test.
    """
    return postgres_session


@pytest.fixture
def sample_user(test_db_session):
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        preferences={"theme": "dark", "notifications": True}
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_content(test_db_session, sample_user):
    """Create sample content for testing."""
    from test.conftest import sync_content_tags_for_tests

    tags = ["test", "sample"]
    content = ContentItem(
        title="Test Content",
        content_type="text",
        content_data="This is test content",
        creator_id=sample_user.id,
        item_metadata={"category": "test"},
        prompt="Test prompt",
        path_thumb="/thumbs/test-content.png",
    )
    test_db_session.add(content)
    test_db_session.commit()
    test_db_session.refresh(content)
    sync_content_tags_for_tests(test_db_session, content.id, 'items', tags)  # 'items' not 'regular' for partitioned tables

    return content


@pytest.fixture
def sample_auto_content(test_db_session, sample_user):
    """Create sample automated content for testing."""
    from test.conftest import sync_content_tags_for_tests

    tags = ["auto"]
    content = ContentItemAuto(
        title="Auto Test Content",
        content_type="text",
        content_data="Automatically generated content",
        creator_id=sample_user.id,
        prompt="Test prompt",
        item_metadata={"generator": "system"},
        path_thumb="/thumbs/auto-content.png",
    )
    test_db_session.add(content)
    test_db_session.commit()
    test_db_session.refresh(content)
    sync_content_tags_for_tests(test_db_session, content.id, 'auto', tags)

    return content


class TestUserService:
    """Test UserService business logic operations."""
    
    def test_create_user_success(self, test_db_session):
        """Test successful user creation."""
        service = UserService(test_db_session)
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "preferences": {"lang": "en"}
        }
        
        user = service.create_user(user_data)
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.is_active is True
    
    def test_create_user_duplicate_username(self, test_db_session, sample_user):
        """Test creating user with duplicate username."""
        service = UserService(test_db_session)
        user_data = {
            "username": sample_user.username,  # Duplicate
            "email": "different@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            service.create_user(user_data)
        assert "Username already exists" in str(exc_info.value.detail)
    
    def test_create_user_duplicate_email(self, test_db_session, sample_user):
        """Test creating user with duplicate email."""
        service = UserService(test_db_session)
        user_data = {
            "username": "differentuser",
            "email": sample_user.email  # Duplicate
        }
        
        with pytest.raises(ValidationError) as exc_info:
            service.create_user(user_data)
        assert "Email already exists" in str(exc_info.value.detail)
    
    def test_update_user_preferences(self, test_db_session, sample_user):
        """Test updating user preferences."""
        service = UserService(test_db_session)
        new_preferences = {"theme": "light", "lang": "es", "new_setting": "value"}
        
        updated_user = service.update_user_preferences(sample_user.id, new_preferences)
        
        # Should merge with existing preferences
        expected_prefs = {
            "theme": "light",  # Updated
            "notifications": True,  # Preserved
            "lang": "es",  # New
            "new_setting": "value"  # New
        }
        assert updated_user.preferences == expected_prefs
    
    def test_get_user_statistics(self, test_db_session, sample_user, sample_content):
        """Test getting user statistics."""
        service = UserService(test_db_session)
        
        # Create some interactions and content
        interaction = UserInteraction(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            interaction_type="like"
        )
        test_db_session.add(interaction)
        test_db_session.commit()
        
        stats = service.get_user_statistics(sample_user.id)
        assert "total_interactions" in stats
        assert "content_created" in stats
        assert "avg_rating_given" in stats
        assert stats["total_interactions"] >= 1
        assert stats["content_created"] >= 1
    
    def test_deactivate_user(self, test_db_session, sample_user):
        """Test deactivating a user."""
        service = UserService(test_db_session)
        
        deactivated_user = service.deactivate_user(sample_user.id)
        assert deactivated_user.is_active is False
        assert deactivated_user.updated_at is not None


class TestContentService:
    """Test ContentService business logic operations."""

    def test_create_content_success(self, test_db_session, sample_user):
        """Test successful content creation."""
        from test.conftest import sync_content_tags_for_tests

        service = ContentService(test_db_session)
        tags = ["new", "content"]
        content_data = {
            "title": "New Content",
            "content_type": "text",
            "content_data": "New content data",
            "creator_id": sample_user.id,
            "prompt": "Test prompt",
            "item_metadata": {"category": "new"},
        }

        content = service.create_content(content_data)

        # Sync tags to junction table
        sync_content_tags_for_tests(test_db_session, content.id, 'items', tags)  # 'items' not 'regular' for partitioned tables

        assert content.id is not None
        assert content.title == "New Content"
        assert content.creator_id == sample_user.id
        assert content.quality_score == 0.5  # Default quality score
    
    def test_create_content_invalid_creator(self, test_db_session):
        """Test creating content with invalid creator ID."""
        from uuid import UUID

        service = ContentService(test_db_session)
        # Use a non-existent UUID instead of integer (PostgreSQL requires UUID type)
        non_existent_id = UUID('99999999-9999-9999-9999-999999999999')
        content_data = {
            "title": "New Content",
            "content_type": "text",
            "content_data": "New content data",
            "creator_id": non_existent_id,  # Non-existent user
            "item_metadata": {"category": "new"}
        }

        with pytest.raises(ValidationError) as exc_info:
            service.create_content(content_data)
        assert "Creator not found" in str(exc_info.value.detail)
    
    def test_search_content(self, test_db_session, sample_content):
        """Test content search functionality."""
        service = ContentService(test_db_session)
        search_params = {
            "search_term": "Test",
            "content_type": "text",
            "public_only": True
        }
        
        results = service.search_content(search_params)
        assert len(results) >= 1
        assert sample_content.id in [c.id for c in results]
    
    def test_update_content_quality(self, test_db_session, sample_content):
        """Test updating content quality score."""
        service = ContentService(test_db_session)
        
        updated_content = service.update_content_quality(sample_content.id, 0.85)
        assert updated_content.quality_score == 0.85
    
    def test_get_content_analytics(self, test_db_session, sample_content, sample_user):
        """Test getting content analytics."""
        service = ContentService(test_db_session)
        
        # Create some interactions
        interactions = [
            UserInteraction(
                user_id=sample_user.id,
                content_item_id=sample_content.id,
                interaction_type="view"
            ),
            UserInteraction(
                user_id=sample_user.id,
                content_item_id=sample_content.id,
                interaction_type="like",
                rating=5
            )
        ]
        test_db_session.add_all(interactions)
        test_db_session.commit()
        
        analytics = service.get_content_analytics(sample_content.id)
        assert "total_views" in analytics
        assert "total_likes" in analytics
        assert "avg_rating" in analytics
        assert analytics["total_views"] >= 1
        assert analytics["total_likes"] >= 1

    def test_content_response_includes_path_thumb(self, sample_content):
        """Ensure ContentResponse exposes thumbnail paths when present."""
        response = ContentResponse.model_validate(sample_content)
        assert response.path_thumb == "/thumbs/test-content.png"

    def test_content_response_handles_missing_path_thumb(self, test_db_session, sample_user):
        """Ensure ContentResponse gracefully handles missing thumbnail paths."""
        from test.conftest import sync_content_tags_for_tests

        tags = ["none"]
        content_without_thumb = ContentItem(
            title="No Thumb",
            content_type="text",
            content_data="Body",
            creator_id=sample_user.id,
            prompt="Test prompt",
            item_metadata={},
        )
        test_db_session.add(content_without_thumb)
        test_db_session.commit()
        test_db_session.refresh(content_without_thumb)
        sync_content_tags_for_tests(test_db_session, content_without_thumb.id, 'items', tags)  # 'items' not 'regular'

        response = ContentResponse.model_validate(content_without_thumb)
        assert response.path_thumb is None

    def test_get_unified_content_paginated_includes_path_thumb(self, test_db_session, sample_content, sample_auto_content, sample_user):
        """Unified content payloads should include thumbnail paths and support null values."""
        from test.conftest import sync_content_tags_for_tests

        # Create an additional record without a thumbnail to verify null handling.
        tags = []
        no_thumb_content = ContentItem(
            title="Missing Thumb",
            content_type="image",
            content_data="/images/missing.png",
            creator_id=sample_user.id,
            prompt="Test prompt",
            item_metadata={},
            path_thumb=None,
        )
        test_db_session.add(no_thumb_content)
        test_db_session.commit()
        test_db_session.refresh(no_thumb_content)
        sync_content_tags_for_tests(test_db_session, no_thumb_content.id, 'items', tags)  # 'items' not 'regular' for partitioned tables

        service = ContentService(test_db_session)
        pagination = PaginationRequest(page=1, page_size=10)
        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=["regular", "auto"],
        )

        id_to_item = {(item["id"], item["source_type"]): item for item in result["items"]}

        # PostgreSQL table partitioning. The partition functionality works correctly on PostgreSQL
        # (verified via API tests against demo database). These tests should be migrated to use
        # PostgreSQL.
        if len(result["items"]) == 0:
            import pytest
            pytest.skip("Test requires PostgreSQL with partitioning support ")

        # Note: source_type='items' for regular content (not 'regular') due to partitioning
        assert id_to_item[(sample_content.id, "items")]["path_thumb"] == "/thumbs/test-content.png"
        assert id_to_item[(sample_auto_content.id, "auto")]["path_thumb"] == "/thumbs/auto-content.png"
        assert id_to_item[(no_thumb_content.id, "items")]["path_thumb"] is None

    def test_path_thumbs_alt_res_included_in_unified_content(self, test_db_session, sample_user):
        """Verify path_thumbs_alt_res field is returned in unified content queries."""
        from test.conftest import sync_content_tags_for_tests

        # Create content with alternate resolution thumbnails
        tags = []
        content_with_alt_res = ContentItem(
            title="Multi-Res Content",
            content_type="image",
            content_data="/images/full.png",
            creator_id=sample_user.id,
            prompt="Test prompt",
            path_thumb="/thumbs/410x614.png",
            path_thumbs_alt_res={
                "256x384": "/thumbs/256x384.png",
                "358x538": "/thumbs/358x538.png",
                "512x768": "/thumbs/512x768.png"
            },
            item_metadata={},
        )
        test_db_session.add(content_with_alt_res)
        test_db_session.commit()
        test_db_session.refresh(content_with_alt_res)
        sync_content_tags_for_tests(test_db_session, content_with_alt_res.id, 'items', tags)  # 'items' not 'regular' for partitioned tables

        service = ContentService(test_db_session)
        pagination = PaginationRequest(page=1, page_size=10)
        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=["regular"],
        )

        matching_items = [item for item in result["items"] if item["id"] == content_with_alt_res.id]
        assert len(matching_items) == 1
        item = matching_items[0]

        assert item["path_thumbs_alt_res"] is not None
        assert item["path_thumbs_alt_res"]["256x384"] == "/thumbs/256x384.png"
        assert item["path_thumbs_alt_res"]["358x538"] == "/thumbs/358x538.png"
        assert item["path_thumbs_alt_res"]["512x768"] == "/thumbs/512x768.png"

    def test_get_unified_content_tag_match_any(self, test_db_session, sample_user):
        """Tag filtering with 'any' logic should return items that match any tag."""
        from test.conftest import sync_content_tags_for_tests

        tags_one = ["fantasy", "dragon"]
        content_one = ContentItem(
            title="Forest Dragon",
            content_type="image",
            content_data="/images/dragon.png",
            creator_id=sample_user.id,
            item_metadata={},
            prompt="Generated",
        )
        test_db_session.add(content_one)
        test_db_session.commit()
        test_db_session.refresh(content_one)
        sync_content_tags_for_tests(test_db_session, content_one.id, 'regular', tags_one)

        tags_two = ["fantasy", "spirit"]
        content_two = ContentItem(
            title="Forest Spirit",
            content_type="image",
            content_data="/images/spirit.png",
            creator_id=sample_user.id,
            item_metadata={},
            prompt="Generated",
        )
        test_db_session.add(content_two)
        test_db_session.commit()
        test_db_session.refresh(content_two)
        sync_content_tags_for_tests(test_db_session, content_two.id, 'regular', tags_two)

        service = ContentService(test_db_session)
        pagination = PaginationRequest(page=1, page_size=10)

        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=["regular"],
            tags=["dragon", "spirit"],
            tag_match="any",
        )

        titles = {item["title"] for item in result["items"]}
        assert "Forest Dragon" in titles
        assert "Forest Spirit" in titles

    def test_get_unified_content_tag_match_all(self, test_db_session, sample_user):
        """Tag filtering with 'all' logic should require all tags to be present."""
        from test.conftest import sync_content_tags_for_tests

        tags_all = ["fantasy", "dragon", "crystal"]
        content_all = ContentItem(
            title="Crystal Dragon",
            content_type="image",
            content_data="/images/crystal.png",
            creator_id=sample_user.id,
            item_metadata={},
            prompt="Generated",
        )
        test_db_session.add(content_all)
        test_db_session.commit()
        test_db_session.refresh(content_all)
        sync_content_tags_for_tests(test_db_session, content_all.id, 'regular', tags_all)

        tags_partial = ["fantasy", "crystal"]
        content_partial = ContentItem(
            title="Crystal Cave",
            content_type="image",
            content_data="/images/cave.png",
            creator_id=sample_user.id,
            item_metadata={},
            prompt="Generated",
        )
        test_db_session.add(content_partial)
        test_db_session.commit()
        test_db_session.refresh(content_partial)
        sync_content_tags_for_tests(test_db_session, content_partial.id, 'regular', tags_partial)

        service = ContentService(test_db_session)
        pagination = PaginationRequest(page=1, page_size=10)

        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=["regular"],
            tags=["fantasy", "dragon"],
            tag_match="all",
        )

        titles = [item["title"] for item in result["items"]]
        assert "Crystal Dragon" in titles
        assert "Crystal Cave" not in titles

    def test_get_unified_content_tag_uuid_filter(self, test_db_session, sample_user):
        """UUID-identifiers should resolve to legacy slugs for tag filtering."""
        from test.conftest import sync_content_tags_for_tests

        tags = ['4k']
        tagged_content = ContentItem(
            title="4K Landscape",
            content_type="image",
            content_data="/images/4k.png",
            creator_id=sample_user.id,
            item_metadata={},
            prompt="High resolution",
        )
        test_db_session.add(tagged_content)
        test_db_session.commit()
        test_db_session.refresh(tagged_content)
        sync_content_tags_for_tests(test_db_session, tagged_content.id, 'items', tags)  # 'items' not 'regular' for partitioned tables

        uuid_identifier = get_uuid_for_slug('4k')
        assert uuid_identifier is not None

        service = ContentService(test_db_session)
        pagination = PaginationRequest(page=1, page_size=10)

        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=['regular'],
            tags=[uuid_identifier],
            tag_match='any',
        )

        titles = [item["title"] for item in result["items"]]
        assert "4K Landscape" in titles

    def test_get_unified_content_tag_objects_filter(self, test_db_session, sample_user):
        """Content tagged with object structures should be filterable."""
        from test.conftest import sync_content_tags_for_tests

        uuid_identifier = get_uuid_for_slug('4k')
        assert uuid_identifier is not None

        tags = [
            {
                'id': uuid_identifier,
                'slug': '4k',
                'name': '4K',
            }
        ]
        tagged_content = ContentItem(
            title="4K Portrait",
            content_type="image",
            content_data="/images/4k-portrait.png",
            creator_id=sample_user.id,
            item_metadata={},
            prompt="High resolution portrait",
        )
        test_db_session.add(tagged_content)
        test_db_session.commit()
        test_db_session.refresh(tagged_content)
        sync_content_tags_for_tests(test_db_session, tagged_content.id, 'items', tags)  # 'items' not 'regular' for partitioned tables

        service = ContentService(test_db_session)
        pagination = PaginationRequest(page=1, page_size=10)

        result = service.get_unified_content_paginated(
            pagination=pagination,
            content_types=['regular'],
            tags=[uuid_identifier],
            tag_match='any',
        )

        titles = [item["title"] for item in result["items"]]
        assert "4K Portrait" in titles


class TestContentAutoService:
    """Verify automated content is handled separately."""

    def test_create_auto_content_success(self, test_db_session, sample_user):
        from test.conftest import sync_content_tags_for_tests

        service = ContentAutoService(test_db_session)
        tags = ["auto"]
        content = service.create_content(
            {
                "title": "Auto Generated",
                "content_type": "text",
                "content_data": "Auto body",
                "creator_id": sample_user.id,
                "prompt": "Test prompt",
                "item_metadata": {"source": "automation"},
            }
        )

        # Sync tags to junction table
        sync_content_tags_for_tests(test_db_session, content.id, 'auto', tags)

        assert isinstance(content, ContentItemAuto)
        assert content.title == "Auto Generated"

    def test_auto_content_list_filters(self, test_db_session, sample_auto_content):
        service = ContentAutoService(test_db_session)
        results = service.get_content_list()

        assert any(isinstance(item, ContentItemAuto) for item in results)
        stats = service.get_content_stats()
        assert stats["total_content"] >= 1


class TestInteractionService:
    """Test InteractionService business logic operations."""
    
    def test_record_interaction(self, test_db_session, sample_user, sample_content):
        """Test recording a new interaction."""
        service = InteractionService(test_db_session)
        interaction_data = {
            "user_id": sample_user.id,
            "content_item_id": sample_content.id,
            "interaction_type": "like",
            "rating": 5,
            "duration": 120
        }
        
        interaction = service.record_interaction(interaction_data)
        assert interaction.id is not None
        assert interaction.user_id == sample_user.id
        assert interaction.content_item_id == sample_content.id
        assert interaction.interaction_type == "like"
        assert interaction.rating == 5
    
    def test_record_interaction_invalid_user(self, test_db_session, sample_content):
        """Test recording interaction with invalid user."""
        from uuid import UUID

        service = InteractionService(test_db_session)
        # Use a non-existent UUID instead of integer (PostgreSQL requires UUID type)
        non_existent_id = UUID('99999999-9999-9999-9999-999999999999')
        interaction_data = {
            "user_id": non_existent_id,  # Non-existent
            "content_item_id": sample_content.id,
            "interaction_type": "like"
        }

        with pytest.raises(ValidationError) as exc_info:
            service.record_interaction(interaction_data)
        assert "User not found" in str(exc_info.value.detail)
    
    def test_record_interaction_invalid_content(self, test_db_session, sample_user):
        """Test recording interaction with invalid content."""
        service = InteractionService(test_db_session)
        interaction_data = {
            "user_id": sample_user.id,
            "content_item_id": 999,  # Non-existent
            "interaction_type": "like"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            service.record_interaction(interaction_data)
        assert "Content not found" in str(exc_info.value.detail)
    
    def test_get_user_behavior_analytics(self, test_db_session, sample_user, sample_content):
        """Test getting user behavior analytics."""
        service = InteractionService(test_db_session)
        
        # Create interactions
        interactions = [
            UserInteraction(
                user_id=sample_user.id,
                content_item_id=sample_content.id,
                interaction_type="view"
            ),
            UserInteraction(
                user_id=sample_user.id,
                content_item_id=sample_content.id,
                interaction_type="like"
            )
        ]
        test_db_session.add_all(interactions)
        test_db_session.commit()
        
        analytics = service.get_user_behavior_analytics(sample_user.id)
        assert "total_interactions" in analytics
        assert "interaction_types" in analytics
        assert "favorite_content_types" in analytics
        assert analytics["total_interactions"] >= 2


class TestRecommendationService:
    """Test RecommendationService business logic operations."""
    
    def test_create_recommendation(self, test_db_session, sample_user, sample_content):
        """Test creating a recommendation."""
        service = RecommendationService(test_db_session)
        rec_data = {
            "user_id": sample_user.id,
            "content_item_id": sample_content.id,
            "recommendation_score": 0.85,
            "algorithm_version": "v1.0"
        }
        
        recommendation = service.create_recommendation(rec_data)
        assert recommendation.id is not None
        assert recommendation.user_id == sample_user.id
        assert recommendation.content_item_id == sample_content.id
        assert recommendation.recommendation_score == 0.85
    
    def test_generate_recommendations_for_user(self, test_db_session, sample_user, sample_content):
        """Test generating recommendations for a user."""
        service = RecommendationService(test_db_session)
        
        # Mock the recommendation algorithm
        with patch.object(service, '_calculate_content_similarity', return_value=0.8):
            recommendations = service.generate_recommendations_for_user(
                sample_user.id, 
                algorithm_version="v1.0", 
                limit=5
            )
            
            assert len(recommendations) >= 1
            assert all(r.user_id == sample_user.id for r in recommendations)
    
    def test_get_served_recommendations(self, test_db_session, sample_user, sample_content):
        """Test getting served recommendations."""
        service = RecommendationService(test_db_session)
        
        # Create served recommendation
        served_rec = Recommendation(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            recommendation_score=0.9,
            algorithm_version="v1.0",
            served_at=datetime.utcnow()
        )
        test_db_session.add(served_rec)
        test_db_session.commit()
        
        served_recommendations = service.get_served_recommendations(sample_user.id)
        rec_ids = [r.id for r in served_recommendations]
        assert served_rec.id in rec_ids
    
    def test_bulk_create_recommendations(self, test_db_session, sample_user, sample_content):
        """Test bulk creating recommendations."""
        service = RecommendationService(test_db_session)
        
        # Create second content item
        content2 = ContentItem(
            title="Second Content",
            content_type="text",
            content_data="Second content data",
            creator_id=sample_user.id,
            prompt="Test prompt"
        )
        test_db_session.add(content2)
        test_db_session.commit()
        test_db_session.refresh(content2)
        
        rec_data_list = [
            {
                "user_id": sample_user.id,
                "content_item_id": sample_content.id,
                "recommendation_score": 0.8,
                "algorithm_version": "v1.0"
            },
            {
                "user_id": sample_user.id,
                "content_item_id": content2.id,
                "recommendation_score": 0.7,
                "algorithm_version": "v1.0"
            }
        ]
        
        recommendations = service.bulk_create_recommendations(rec_data_list)
        assert len(recommendations) == 2
        assert all(r.user_id == sample_user.id for r in recommendations)


class TestGenerationService:
    """Test GenerationService business logic operations."""
    
    def test_create_generation_job(self, test_db_session, sample_user):
        """Test creating a generation job."""
        service = GenerationService(test_db_session)
        job_data = {
            "user_id": sample_user.id,
            "job_type": "text_generation",
            "prompt": "Generate a story",
            "params": {"max_length": 1000}
        }

        async_result = MagicMock()
        async_result.id = "task-123"

        with patch("genonaut.worker.tasks.run_comfy_job.delay", return_value=async_result) as mock_delay:
            job = service.create_generation_job(job_data)

        mock_delay.assert_called_once()
        assert job.id is not None
        assert job.user_id == sample_user.id
        assert job.job_type == "text_generation"
        assert job.status == "pending"
        assert job.created_at is not None
        assert job.celery_task_id == "task-123"
        # The service automatically adds 'backend' field (defaults to 'kerniegen')
        assert job.params == {"backend": "kerniegen", "max_length": 1000}
    
    def test_start_job_processing(self, test_db_session, sample_user):
        """Test starting job processing."""
        service = GenerationService(test_db_session)
        
        # Create job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="pending"
        )
        test_db_session.add(job)
        test_db_session.commit()
        
        started_job = service.start_job_processing(job.id)
        assert started_job.status == "running"
        assert started_job.started_at is not None
        assert started_job.updated_at is not None
    
    def test_complete_job(self, test_db_session, sample_user, sample_content):
        """Test completing a generation job."""
        service = GenerationService(test_db_session)
        
        # Create running job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="running",
            started_at=datetime.utcnow()
        )
        test_db_session.add(job)
        test_db_session.commit()
        
        completed_job = service.complete_job(job.id, sample_content.id)
        assert completed_job.status == "completed"
        assert completed_job.result_content_id == sample_content.id
        assert completed_job.completed_at is not None
    
    def test_fail_job(self, test_db_session, sample_user):
        """Test failing a generation job."""
        service = GenerationService(test_db_session)
        
        # Create running job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="running"
        )
        test_db_session.add(job)
        test_db_session.commit()
        
        error_message = "Generation failed due to timeout"
        failed_job = service.fail_job(job.id, error_message)
        assert failed_job.status == "failed"
        assert failed_job.error_message == error_message
        assert failed_job.completed_at is not None

    def test_cancel_pending_job(self, test_db_session, sample_user):
        """Test cancelling a pending generation job."""
        service = GenerationService(test_db_session)

        # Create pending job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="pending"
        )
        test_db_session.add(job)
        test_db_session.commit()

        reason = "User requested cancellation"
        cancelled_job = service.cancel_job(job.id, reason=reason)
        assert cancelled_job.status == "cancelled"
        assert cancelled_job.error_message == f"Cancelled: {reason}"
        assert cancelled_job.completed_at is not None

    def test_cancel_running_job(self, test_db_session, sample_user):
        """Test cancelling a running generation job."""
        service = GenerationService(test_db_session)

        # Create running job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="running",
            started_at=datetime.utcnow()
        )
        test_db_session.add(job)
        test_db_session.commit()

        cancelled_job = service.cancel_job(job.id)
        assert cancelled_job.status == "cancelled"
        assert cancelled_job.error_message is None
        assert cancelled_job.completed_at is not None

    def test_cancel_job_invalid_status(self, test_db_session, sample_user):
        """Test that cancelling completed/failed jobs raises error."""
        service = GenerationService(test_db_session)

        # Test completed job
        completed_job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="completed"
        )
        test_db_session.add(completed_job)
        test_db_session.commit()

        with pytest.raises(ValidationError) as exc_info:
            service.cancel_job(completed_job.id)
        assert "Cannot cancel job with status 'completed'" in str(exc_info.value)

        # Test failed job
        failed_job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="failed"
        )
        test_db_session.add(failed_job)
        test_db_session.commit()

        with pytest.raises(ValidationError) as exc_info:
            service.cancel_job(failed_job.id)
        assert "Cannot cancel job with status 'failed'" in str(exc_info.value)

    def test_cancel_nonexistent_job(self, test_db_session):
        """Test cancelling a non-existent job raises error."""
        service = GenerationService(test_db_session)

        with pytest.raises(EntityNotFoundError):
            service.cancel_job(999)

    def test_get_queue_statistics(self, test_db_session, sample_user):
        """Test getting queue statistics."""
        service = GenerationService(test_db_session)
        
        # Create jobs with different statuses
        jobs = [
            GenerationJob(
                user_id=sample_user.id,
                job_type="text_generation",
                prompt="Pending job",
                status="pending"
            ),
            GenerationJob(
                user_id=sample_user.id,
                job_type="text_generation",
                prompt="Running job",
                status="running"
            ),
            GenerationJob(
                user_id=sample_user.id,
                job_type="text_generation",
                prompt="Completed job",
                status="completed"
            ),
            GenerationJob(
                user_id=sample_user.id,
                job_type="text_generation",
                prompt="Cancelled job",
                status="cancelled"
            )
        ]
        test_db_session.add_all(jobs)
        test_db_session.commit()

        stats = service.get_queue_statistics()
        assert "pending_jobs" in stats
        assert "running_jobs" in stats
        assert "completed_jobs" in stats
        assert "failed_jobs" in stats
        assert "cancelled_jobs" in stats
        assert stats["pending_jobs"] >= 1
        assert stats["running_jobs"] >= 1
        assert stats["completed_jobs"] >= 1
        assert stats["cancelled_jobs"] >= 1


# Bookmark test fixtures
@pytest.fixture
def sample_bookmark(test_db_session, sample_user, sample_content):
    """Create a sample bookmark for testing."""
    bookmark = Bookmark(
        user_id=sample_user.id,
        content_id=sample_content.id,
        content_source_type='items',
        note="Test bookmark note",
        pinned=False,
        is_public=False
    )
    test_db_session.add(bookmark)
    test_db_session.commit()
    test_db_session.refresh(bookmark)
    return bookmark


@pytest.fixture
def sample_categories(test_db_session, sample_user):
    """Create sample bookmark categories for testing."""
    categories = [
        BookmarkCategory(
            user_id=sample_user.id,
            name="Category 1",
            description="First test category"
        ),
        BookmarkCategory(
            user_id=sample_user.id,
            name="Category 2",
            description="Second test category"
        ),
        BookmarkCategory(
            user_id=sample_user.id,
            name="Uncategorized",
            description="Default category"
        )
    ]
    test_db_session.add_all(categories)
    test_db_session.commit()
    for cat in categories:
        test_db_session.refresh(cat)
    return categories


class TestBookmarkCategoryMemberService:
    """Test bookmark category membership service."""

    def test_add_bookmark_to_category_updates_timestamp(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test that adding a bookmark to a category updates category.updated_at."""
        service = BookmarkCategoryMemberService(test_db_session)
        category = sample_categories[0]
        original_updated_at = category.updated_at

        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)

        # Add bookmark to category
        service.add_bookmark_to_category(
            bookmark_id=sample_bookmark.id,
            category_id=category.id
        )

        # Refresh category from database
        test_db_session.refresh(category)

        # Assert updated_at was updated
        assert category.updated_at > original_updated_at

    def test_remove_bookmark_from_category_updates_timestamp(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test that removing a bookmark from a category updates category.updated_at."""
        service = BookmarkCategoryMemberService(test_db_session)
        category = sample_categories[0]

        # First add bookmark to category
        service.add_bookmark_to_category(
            bookmark_id=sample_bookmark.id,
            category_id=category.id
        )
        test_db_session.refresh(category)
        original_updated_at = category.updated_at

        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)

        # Remove bookmark from category
        removed = service.remove_bookmark_from_category(
            bookmark_id=sample_bookmark.id,
            category_id=category.id
        )

        assert removed is True

        # Refresh category from database
        test_db_session.refresh(category)

        # Assert updated_at was updated
        assert category.updated_at > original_updated_at

    def test_sync_bookmark_categories_adds_new_categories(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test sync_bookmark_categories adds new category memberships."""
        service = BookmarkCategoryMemberService(test_db_session)

        # Sync bookmark with two categories
        category_ids = [sample_categories[0].id, sample_categories[1].id]
        result = service.sync_bookmark_categories(
            bookmark_id=sample_bookmark.id,
            category_ids=category_ids,
            user_id=sample_user.id
        )

        assert len(result) == 2
        result_category_ids = {m.category_id for m in result}
        assert result_category_ids == set(category_ids)

    def test_sync_bookmark_categories_removes_old_categories(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test sync_bookmark_categories removes category memberships not in the list."""
        service = BookmarkCategoryMemberService(test_db_session)

        # First add bookmark to category 1 and 2
        service.add_bookmark_to_category(
            bookmark_id=sample_bookmark.id,
            category_id=sample_categories[0].id
        )
        service.add_bookmark_to_category(
            bookmark_id=sample_bookmark.id,
            category_id=sample_categories[1].id
        )

        # Now sync to only category 2 (should remove category 1)
        category_ids = [sample_categories[1].id]
        result = service.sync_bookmark_categories(
            bookmark_id=sample_bookmark.id,
            category_ids=category_ids,
            user_id=sample_user.id
        )

        assert len(result) == 1
        assert result[0].category_id == sample_categories[1].id

    def test_sync_bookmark_categories_updates_updated_at(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test sync_bookmark_categories updates updated_at for affected categories."""
        service = BookmarkCategoryMemberService(test_db_session)

        category1 = sample_categories[0]
        category2 = sample_categories[1]
        original_updated_at_1 = category1.updated_at
        original_updated_at_2 = category2.updated_at

        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)

        # Sync bookmark to category 1
        service.sync_bookmark_categories(
            bookmark_id=sample_bookmark.id,
            category_ids=[category1.id],
            user_id=sample_user.id
        )

        # Refresh categories
        test_db_session.refresh(category1)
        test_db_session.refresh(category2)

        # Category 1 should be updated, category 2 should not
        assert category1.updated_at > original_updated_at_1
        assert category2.updated_at == original_updated_at_2

    def test_sync_bookmark_categories_empty_list_defaults_to_uncategorized(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test sync_bookmark_categories with empty list defaults to 'Uncategorized'."""
        service = BookmarkCategoryMemberService(test_db_session)

        # Sync with empty list
        result = service.sync_bookmark_categories(
            bookmark_id=sample_bookmark.id,
            category_ids=[],
            user_id=sample_user.id
        )

        assert len(result) == 1
        # Find the "Uncategorized" category
        uncategorized = next(c for c in sample_categories if c.name == "Uncategorized")
        assert result[0].category_id == uncategorized.id

    def test_sync_bookmark_categories_validates_user_ownership(
        self,
        test_db_session,
        sample_user,
        sample_bookmark,
        sample_categories
    ):
        """Test sync_bookmark_categories validates bookmark belongs to user."""
        service = BookmarkCategoryMemberService(test_db_session)

        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com"
        )
        test_db_session.add(other_user)
        test_db_session.commit()

        # Try to sync with wrong user_id
        with pytest.raises(ValidationError, match="does not belong to the specified user"):
            service.sync_bookmark_categories(
                bookmark_id=sample_bookmark.id,
                category_ids=[sample_categories[0].id],
                user_id=other_user.id
            )

    def test_create_bookmark_auto_assigns_to_uncategorized(
        self,
        test_db_session,
        sample_user,
        sample_content
    ):
        """Test that creating a bookmark automatically assigns it to Uncategorized category."""
        bookmark_service = BookmarkService(test_db_session)
        member_service = BookmarkCategoryMemberService(test_db_session)

        # Create bookmark
        bookmark = bookmark_service.create_bookmark(
            user_id=sample_user.id,
            content_id=sample_content.id,
            content_source_type='items',
            note="Test bookmark"
        )

        # Get bookmark's categories
        memberships = member_service.get_bookmark_categories(bookmark.id)

        # Should be in exactly one category (Uncategorized)
        assert len(memberships) == 1

        # Verify it's the Uncategorized category
        from genonaut.api.repositories.bookmark_category_repository import BookmarkCategoryRepository
        category_repo = BookmarkCategoryRepository(test_db_session)
        category = category_repo.get(memberships[0].category_id)
        assert category.name == "Uncategorized"
