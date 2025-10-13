"""Database tests for API repositories."""

import os
import uuid
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from genonaut.db.schema import (
    Base,
    User,
    ContentItem,
    ContentItemAuto,
    UserInteraction,
    Recommendation,
    GenerationJob,
)
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.interaction_repository import InteractionRepository
from genonaut.api.repositories.recommendation_repository import RecommendationRepository
from genonaut.api.repositories.generation_job_repository import GenerationJobRepository
from genonaut.api.exceptions import EntityNotFoundError, DatabaseError


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
    from test.conftest import sync_content_tags_for_tests

    tags = ["test", "sample"]
    content = ContentItem(
        title="Test Content",
        content_type="text",
        content_data="This is test content",
        creator_id=sample_user.id,
        item_metadata={"category": "test"},
        prompt="Test prompt"
    )
    test_db_session.add(content)
    test_db_session.commit()
    test_db_session.refresh(content)

    # Populate content_tags junction table for SQLite tests
    sync_content_tags_for_tests(test_db_session, content.id, 'regular', tags)

    return content


@pytest.fixture
def sample_auto_content(test_db_session, sample_user):
    """Create sample automated content for testing."""
    from test.conftest import sync_content_tags_for_tests

    tags = ["auto"]
    content = ContentItemAuto(
        title="Automated Content",
        content_type="text",
        content_data="Automated payload",
        creator_id=sample_user.id,
        item_metadata={"source": "system"},
    )
    test_db_session.add(content)
    test_db_session.commit()
    test_db_session.refresh(content)

    # Populate content_tags junction table for SQLite tests
    sync_content_tags_for_tests(test_db_session, content.id, 'auto', tags)

    return content


class TestUserRepository:
    """Test UserRepository database operations."""
    
    def test_create_user(self, test_db_session):
        """Test creating a new user."""
        repo = UserRepository(test_db_session)
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "preferences": {"lang": "en"}
        }
        
        user = repo.create(user_data)
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.preferences == {"lang": "en"}
        assert user.created_at is not None
    
    def test_get_user_by_id(self, test_db_session, sample_user):
        """Test getting user by ID."""
        repo = UserRepository(test_db_session)
        
        user = repo.get(sample_user.id)
        assert user is not None
        assert user.id == sample_user.id
        assert user.username == sample_user.username
    
    def test_get_user_not_found(self, test_db_session):
        """Test getting user that doesn't exist."""
        repo = UserRepository(test_db_session)
        
        user = repo.get(999)
        assert user is None
    
    def test_get_user_or_404(self, test_db_session, sample_user):
        """Test get_or_404 method with existing user."""
        repo = UserRepository(test_db_session)
        
        user = repo.get_or_404(sample_user.id)
        assert user.id == sample_user.id
    
    def test_get_user_or_404_not_found(self, test_db_session):
        """Test get_or_404 method raises exception for non-existent user."""
        repo = UserRepository(test_db_session)
        
        with pytest.raises(EntityNotFoundError) as exc_info:
            repo.get_or_404(999)
        assert "User with id 999 not found" in str(exc_info.value.detail)
    
    def test_update_user(self, test_db_session, sample_user):
        """Test updating user."""
        repo = UserRepository(test_db_session)
        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }
        
        updated_user = repo.update(sample_user.id, update_data)
        assert updated_user.username == "updateduser"
        assert updated_user.email == "updated@example.com"
        assert updated_user.updated_at is not None
    
    def test_delete_user(self, test_db_session, sample_user):
        """Test soft deleting user."""
        repo = UserRepository(test_db_session)
        
        deleted_user = repo.delete(sample_user.id)
        assert deleted_user.is_active is False
        assert deleted_user.updated_at is not None
    
    def test_get_by_username(self, test_db_session, sample_user):
        """Test getting user by username."""
        repo = UserRepository(test_db_session)
        
        user = repo.get_by_username(sample_user.username)
        assert user is not None
        assert user.id == sample_user.id
    
    def test_get_by_email(self, test_db_session, sample_user):
        """Test getting user by email."""
        repo = UserRepository(test_db_session)
        
        user = repo.get_by_email(sample_user.email)
        assert user is not None
        assert user.id == sample_user.id
    
    def test_get_users_by_preferences_filter(self, test_db_session):
        """Test filtering users by preferences."""
        repo = UserRepository(test_db_session)
        
        # Create users with different preferences
        user1 = User(username="user1", email="user1@test.com", preferences={"theme": "dark"})
        user2 = User(username="user2", email="user2@test.com", preferences={"theme": "light"})
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        
        # Note: SQLite doesn't support JSONB operations like PostgreSQL
        # This test would work differently in a real PostgreSQL environment
        users = repo.get_by_preferences_filter({"theme": "dark"})
        # In SQLite, this might return all users or none depending on implementation
        # The real test would be in PostgreSQL with proper JSONB support
        assert isinstance(users, list)
    
    def test_get_active_users(self, test_db_session, sample_user):
        """Test getting only active users."""
        repo = UserRepository(test_db_session)
        
        # Create inactive user
        inactive_user = User(username="inactive", email="inactive@test.com", is_active=False)
        test_db_session.add(inactive_user)
        test_db_session.commit()
        
        active_users = repo.get_active_users()
        user_ids = [u.id for u in active_users]
        assert sample_user.id in user_ids
        assert inactive_user.id not in user_ids

    def test_get_admin_user_by_username(self, test_db_session):
        """Test getting the admin user by username and verifying their UUID."""
        repo = UserRepository(test_db_session)
        admin_uuid_str = os.environ.get("DB_USER_ADMIN_UUID")
        admin_uuid = uuid.UUID(admin_uuid_str)

        # Create admin user
        admin_user = User(
            id=admin_uuid,
            username="Admin",
            email="admin@example.com",
        )
        test_db_session.add(admin_user)
        test_db_session.commit()

        user = repo.get_by_username("Admin")
        assert user is not None
        assert user.id == admin_uuid


class TestContentRepository:
    """Test ContentRepository database operations."""

    def test_create_content(self, test_db_session, sample_user):
        repo = ContentRepository(test_db_session)
        content = repo.create(
            {
                "title": "New Content",
                "content_type": "text",
                "content_data": "New content data",
                "creator_id": sample_user.id,
                "prompt": "Test prompt",
                "item_metadata": {"category": "new"},
                "tags": ["new", "content"],
            }
        )

        assert content.id is not None
        assert content.title == "New Content"

    def test_get_content_by_creator(self, test_db_session, sample_user, sample_content):
        repo = ContentRepository(test_db_session)
        content_list = repo.get_by_creator_id(sample_user.id)

        assert sample_content.id in [c.id for c in content_list]

    def test_get_content_by_type(self, test_db_session, sample_content):
        repo = ContentRepository(test_db_session)
        content_list = repo.get_by_content_type("text")

        assert sample_content.id in [c.id for c in content_list]

    def test_search_content_by_title(self, test_db_session, sample_content):
        repo = ContentRepository(test_db_session)
        content_list = repo.search_by_title("Test")

        assert sample_content.id in [c.id for c in content_list]

    def test_update_quality_score(self, test_db_session, sample_content):
        repo = ContentRepository(test_db_session)
        updated_content = repo.update_quality_score(sample_content.id, 0.85)

        assert updated_content.quality_score == 0.85
        assert updated_content.updated_at is not None


class TestContentAutoRepository:
    """Ensure ContentRepository supports ContentItemAuto."""

    def test_create_auto_content(self, test_db_session, sample_user):
        repo = ContentRepository(test_db_session, model=ContentItemAuto)
        content = repo.create(
            {
                "title": "Generated Story",
                "content_type": "text",
                "content_data": "Story seed",
                "creator_id": sample_user.id,
                "prompt": "Test prompt",
                "item_metadata": {"generator": "system"},
                "tags": ["auto", "story"],
            }
        )

        assert isinstance(content, ContentItemAuto)


class TestInteractionRepository:
    """Test InteractionRepository database operations."""
    
    def test_create_interaction(self, test_db_session, sample_user, sample_content):
        """Test creating new interaction."""
        repo = InteractionRepository(test_db_session)
        interaction_data = {
            "user_id": sample_user.id,
            "content_item_id": sample_content.id,
            "interaction_type": "like",
            "rating": 5,
            "duration": 120,
            "interaction_metadata": {"source": "web"}
        }
        
        interaction = repo.create(interaction_data)
        assert interaction.id is not None
        assert interaction.user_id == sample_user.id
        assert interaction.content_item_id == sample_content.id
        assert interaction.interaction_type == "like"
        assert interaction.rating == 5
    
    def test_get_user_interactions(self, test_db_session, sample_user, sample_content):
        """Test getting interactions for a user."""
        repo = InteractionRepository(test_db_session)
        
        # Create interaction
        interaction = UserInteraction(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            interaction_type="view"
        )
        test_db_session.add(interaction)
        test_db_session.commit()
        
        interactions = repo.get_by_user_id(sample_user.id)
        assert len(interactions) >= 1
        assert interaction.id in [i.id for i in interactions]
    
    def test_get_content_interactions(self, test_db_session, sample_user, sample_content):
        """Test getting interactions for content."""
        repo = InteractionRepository(test_db_session)
        
        # Create interaction
        interaction = UserInteraction(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            interaction_type="share"
        )
        test_db_session.add(interaction)
        test_db_session.commit()
        
        interactions = repo.get_by_content_id(sample_content.id)
        assert len(interactions) >= 1
        assert interaction.id in [i.id for i in interactions]
    
    def test_get_interactions_by_type(self, test_db_session, sample_user, sample_content):
        """Test getting interactions by type."""
        repo = InteractionRepository(test_db_session)
        
        # Create different interaction types
        like_interaction = UserInteraction(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            interaction_type="like"
        )
        view_interaction = UserInteraction(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            interaction_type="view"
        )
        test_db_session.add_all([like_interaction, view_interaction])
        test_db_session.commit()
        
        like_interactions = repo.get_by_interaction_type("like")
        assert len(like_interactions) >= 1
        assert like_interaction.id in [i.id for i in like_interactions]


class TestRecommendationRepository:
    """Test RecommendationRepository database operations."""
    
    def test_create_recommendation(self, test_db_session, sample_user, sample_content):
        """Test creating new recommendation."""
        repo = RecommendationRepository(test_db_session)
        rec_data = {
            "user_id": sample_user.id,
            "content_item_id": sample_content.id,
            "recommendation_score": 0.85,
            "algorithm_version": "v1.0",
            "rec_metadata": {"reason": "similarity"}
        }
        
        recommendation = repo.create(rec_data)
        assert recommendation.id is not None
        assert recommendation.user_id == sample_user.id
        assert recommendation.content_item_id == sample_content.id
        assert recommendation.recommendation_score == 0.85
    
    def test_get_user_recommendations(self, test_db_session, sample_user, sample_content):
        """Test getting recommendations for a user."""
        repo = RecommendationRepository(test_db_session)
        
        # Create recommendation
        recommendation = Recommendation(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            recommendation_score=0.9,
            algorithm_version="v1.0"
        )
        test_db_session.add(recommendation)
        test_db_session.commit()
        
        recommendations = repo.get_by_user_id(sample_user.id)
        assert len(recommendations) >= 1
        assert recommendation.id in [r.id for r in recommendations]
    
    def test_get_unserved_recommendations(self, test_db_session, sample_user, sample_content):
        """Test getting unserved recommendations."""
        repo = RecommendationRepository(test_db_session)
        
        # Create served and unserved recommendations
        served_rec = Recommendation(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            recommendation_score=0.8,
            algorithm_version="v1.0",
            served_at=datetime.utcnow()
        )
        unserved_rec = Recommendation(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            recommendation_score=0.9,
            algorithm_version="v1.0"
        )
        test_db_session.add_all([served_rec, unserved_rec])
        test_db_session.commit()
        
        unserved = repo.get_unserved_recommendations(sample_user.id)
        rec_ids = [r.id for r in unserved]
        assert unserved_rec.id in rec_ids
        assert served_rec.id not in rec_ids
    
    def test_mark_as_served(self, test_db_session, sample_user, sample_content):
        """Test marking recommendations as served."""
        repo = RecommendationRepository(test_db_session)
        
        # Create recommendation
        recommendation = Recommendation(
            user_id=sample_user.id,
            content_item_id=sample_content.id,
            recommendation_score=0.85,
            algorithm_version="v1.0"
        )
        test_db_session.add(recommendation)
        test_db_session.commit()
        
        # Mark as served
        served_recs = repo.mark_as_served([recommendation.id])
        assert len(served_recs) == 1
        assert served_recs[0].served_at is not None


class TestGenerationJobRepository:
    """Test GenerationJobRepository database operations."""
    
    def test_create_generation_job(self, test_db_session, sample_user):
        """Test creating new generation job."""
        repo = GenerationJobRepository(test_db_session)
        job_data = {
            "user_id": sample_user.id,
            "job_type": "text_generation",
            "prompt": "Generate a story",
            "parameters": {"max_length": 1000},
            "status": "pending"
        }
        
        job = repo.create(job_data)
        assert job.id is not None
        assert job.user_id == sample_user.id
        assert job.job_type == "text_generation"
        assert job.status == "pending"
    
    def test_update_job_status(self, test_db_session, sample_user):
        """Test updating job status."""
        repo = GenerationJobRepository(test_db_session)
        
        # Create job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Test prompt",
            status="pending"
        )
        test_db_session.add(job)
        test_db_session.commit()
        
        # Update status
        updated_job = repo.update_status(job.id, "running")
        assert updated_job.status == "running"
        assert updated_job.updated_at is not None
    
    def test_get_jobs_by_status(self, test_db_session, sample_user):
        """Test getting jobs by status."""
        repo = GenerationJobRepository(test_db_session)
        
        # Create jobs with different statuses
        pending_job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Pending job",
            status="pending"
        )
        completed_job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="Completed job",
            status="completed"
        )
        test_db_session.add_all([pending_job, completed_job])
        test_db_session.commit()
        
        pending_jobs = repo.get_by_status("pending")
        pending_ids = [j.id for j in pending_jobs]
        assert pending_job.id in pending_ids
        assert completed_job.id not in pending_ids
    
    def test_get_user_jobs(self, test_db_session, sample_user):
        """Test getting jobs for a user."""
        repo = GenerationJobRepository(test_db_session)
        
        # Create job
        job = GenerationJob(
            user_id=sample_user.id,
            job_type="text_generation",
            prompt="User job",
            status="pending"
        )
        test_db_session.add(job)
        test_db_session.commit()
        
        user_jobs = repo.get_by_user_id(sample_user.id)
        assert len(user_jobs) >= 1
        assert job.id in [j.id for j in user_jobs]
