"""Database tests for API services."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob
from genonaut.api.services.user_service import UserService
from genonaut.api.services.content_service import ContentService
from genonaut.api.services.interaction_service import InteractionService
from genonaut.api.services.recommendation_service import RecommendationService
from genonaut.api.services.generation_service import GenerationService
from genonaut.api.exceptions import EntityNotFoundError, ValidationError


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


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
    content = ContentItem(
        title="Test Content",
        content_type="text",
        content_data="This is test content",
        creator_id=sample_user.id,
        item_metadata={"category": "test"},
        tags=["test", "sample"]
    )
    test_db_session.add(content)
    test_db_session.commit()
    test_db_session.refresh(content)
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
        service = ContentService(test_db_session)
        content_data = {
            "title": "New Content",
            "content_type": "text",
            "content_data": "New content data",
            "creator_id": sample_user.id,
            "item_metadata": {"category": "new"},
            "tags": ["new", "content"]
        }
        
        content = service.create_content(content_data)
        assert content.id is not None
        assert content.title == "New Content"
        assert content.creator_id == sample_user.id
        assert content.quality_score == 0.5  # Default quality score
    
    def test_create_content_invalid_creator(self, test_db_session):
        """Test creating content with invalid creator ID."""
        service = ContentService(test_db_session)
        content_data = {
            "title": "New Content",
            "content_type": "text",
            "content_data": "New content data",
            "creator_id": 999,  # Non-existent user
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
        service = InteractionService(test_db_session)
        interaction_data = {
            "user_id": 999,  # Non-existent
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
            creator_id=sample_user.id
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
            "parameters": {"max_length": 1000}
        }
        
        job = service.create_generation_job(job_data)
        assert job.id is not None
        assert job.user_id == sample_user.id
        assert job.job_type == "text_generation"
        assert job.status == "pending"
        assert job.created_at is not None
    
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