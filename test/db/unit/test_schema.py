"""Unit tests for database schema models.

Tests the SQLAlchemy models in genonaut.init.rdbms.schema module.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from genonaut.db.schema import (
    Base,
    User,
    ContentItem,
    ContentItemAuto,
    UserInteraction,
    Recommendation,
    GenerationJob,
)


class TestSchemaModels:
    """Test cases for SQLAlchemy schema models."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database and session for each test."""
        # Use in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Create test users for use in other model tests
        self.test_user1 = User(
            username="testuser1",
            email="test1@example.com",
            preferences={"genre": "sci-fi"}
        )
        self.test_user2 = User(
            username="testuser2", 
            email="test2@example.com",
            preferences={"content_type": "image"}
        )
        
        self.session.add_all([self.test_user1, self.test_user2])
        self.session.commit()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.session.close()
        Base.metadata.drop_all(self.engine)
    
    def test_user_creation(self):
        """Test User model creation and basic attributes."""
        user = User(
            username="newuser",
            email="newuser@example.com",
            preferences={"theme": "dark"}
        )
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.preferences == {"theme": "dark"}
        assert user.id is None  # Not persisted yet
        
        # Test default value after persistence
        self.session.add(user)
        self.session.commit()
        assert user.is_active
    
    def test_user_unique_constraints(self):
        """Test that User model enforces unique constraints."""
        # Try to create user with duplicate username
        duplicate_username_user = User(
            username="testuser1",  # Duplicate
            email="different@example.com"
        )
        
        self.session.add(duplicate_username_user)
        with pytest.raises(IntegrityError):
            self.session.commit()
        
        self.session.rollback()
        
        # Try to create user with duplicate email
        duplicate_email_user = User(
            username="differentuser",
            email="test1@example.com"  # Duplicate
        )
        
        self.session.add(duplicate_email_user)
        with pytest.raises(IntegrityError):
            self.session.commit()
    
    def test_user_defaults(self):
        """Test User model default values."""
        user = User(username="defaultuser", email="default@example.com")
        self.session.add(user)
        self.session.commit()
        
        assert user.is_active
        assert user.preferences == {}
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_content_item_creation(self):
        """Test ContentItem model creation and relationships."""
        content = ContentItem(
            title="Test Content",
            content_type="text",
            content_data="This is test content",
            prompt="Test prompt for schema test",
            creator_id=self.test_user1.id,
            item_metadata={"word_count": 4},
            tags=["test", "sample"]
        )
        
        self.session.add(content)
        self.session.commit()
        
        assert content.title == "Test Content"
        assert content.content_type == "text"
        assert content.creator_id == self.test_user1.id
        assert content.item_metadata["word_count"] == 4
        assert "test" in content.tags
        assert content.quality_score == 0.0

    def test_content_item_auto_creation(self):
        """Test ContentItemAuto mirrors ContentItem defaults and columns."""
        auto_item = ContentItemAuto(
            title="Auto Content",
            content_type="text",
            content_data="Automated content payload",
            prompt="Test prompt for auto content",
            creator_id=self.test_user1.id,
            item_metadata={"generator": "system"},
            tags=["auto", "system"],
        )

        self.session.add(auto_item)
        self.session.commit()

        assert auto_item.title == "Auto Content"
        assert auto_item.content_type == "text"
        assert auto_item.creator_id == self.test_user1.id
        assert auto_item.item_metadata["generator"] == "system"
        assert "auto" in auto_item.tags
        assert auto_item.quality_score == 0.0
        assert not auto_item.is_private
        assert hasattr(auto_item, "updated_at")

    def test_content_item_creator_relationship(self):
        """Test ContentItem relationship with User."""
        content = ContentItem(
            title="Relationship Test",
            content_type="image",
            content_data="/path/to/image.jpg",
            prompt="Test prompt for schema test",
            creator_id=self.test_user1.id
        )
        
        self.session.add(content)
        self.session.commit()
        
        # Test forward relationship
        assert content.creator.username == "testuser1"
        
        # Test backward relationship
        assert content in self.test_user1.content_items

    def test_content_item_auto_creator_relationship(self):
        """Test ContentItemAuto relationship with User."""
        auto_item = ContentItemAuto(
            title="Auto Relationship",
            content_type="image",
            content_data="/auto/path.png",
            prompt="Test prompt for auto relationship",
            creator_id=self.test_user1.id,
        )

        self.session.add(auto_item)
        self.session.commit()

        assert auto_item.creator.username == "testuser1"
        assert auto_item in self.test_user1.auto_content_items
    
    def test_user_interaction_creation(self):
        """Test UserInteraction model creation and constraints."""
        # First create a content item
        content = ContentItem(
            title="Interaction Test Content",
            content_type="text",
            content_data="Test content for interaction",
            prompt="Test prompt for schema test",
            creator_id=self.test_user1.id
        )
        self.session.add(content)
        self.session.commit()
        
        # Create interaction
        interaction = UserInteraction(
            user_id=self.test_user2.id,
            content_item_id=content.id,
            interaction_type="view",
            rating=4,
            duration=120,
            interaction_metadata={"device": "mobile"}
        )
        
        self.session.add(interaction)
        self.session.commit()
        
        assert interaction.interaction_type == "view"
        assert interaction.rating == 4
        assert interaction.duration == 120
        assert interaction.interaction_metadata["device"] == "mobile"
    
    def test_user_interaction_relationships(self):
        """Test UserInteraction relationships with User and ContentItem."""
        # Create content and interaction
        content = ContentItem(
            title="Relationship Test",
            content_type="audio", 
            content_data="/path/to/audio.mp3",
            prompt="Test prompt for schema test",
            creator_id=self.test_user1.id
        )
        self.session.add(content)
        self.session.commit()
        
        interaction = UserInteraction(
            user_id=self.test_user2.id,
            content_item_id=content.id,
            interaction_type="like"
        )
        self.session.add(interaction)
        self.session.commit()
        
        # Test relationships
        assert interaction.user.username == "testuser2"
        assert interaction.content_item.title == "Relationship Test"
        assert interaction in self.test_user2.interactions
        assert interaction in content.interactions
    
    def test_recommendation_creation(self):
        """Test Recommendation model creation."""
        # Create content item first
        content = ContentItem(
            title="Recommended Content",
            content_type="video",
            content_data="/path/to/video.mp4",
            prompt="Test prompt for schema test",
            creator_id=self.test_user1.id
        )
        self.session.add(content)
        self.session.commit()
        
        recommendation = Recommendation(
            user_id=self.test_user2.id,
            content_item_id=content.id,
            recommendation_score=0.85,
            algorithm_version="v2.0",
            rec_metadata={"model": "collaborative_filtering"}
        )
        
        self.session.add(recommendation)
        self.session.commit()
        
        assert recommendation.recommendation_score == 0.85
        assert recommendation.algorithm_version == "v2.0"
        assert not recommendation.is_served
        assert recommendation.rec_metadata["model"] == "collaborative_filtering"
    
    def test_generation_job_creation(self):
        """Test GenerationJob model creation and status tracking."""
        job = GenerationJob(
            user_id=self.test_user1.id,
            job_type="text",
            prompt="Generate a story about robots",
            params={"model": "gpt-4", "temperature": 0.7},
            status="pending"
        )
        
        self.session.add(job)
        self.session.commit()
        
        assert job.job_type == "text"
        assert job.prompt == "Generate a story about robots"
        assert job.status == "pending"
        assert job.params["model"] == "gpt-4"
        assert job.content_id is None
        assert job.started_at is None
        assert job.completed_at is None
    
    def test_generation_job_with_result(self):
        """Test GenerationJob with completed result."""
        # Create result content
        result_content = ContentItem(
            title="Generated Story",
            content_type="text",
            content_data="Once upon a time, there were robots...",
            prompt="Test prompt for schema test",
            creator_id=self.test_user1.id
        )
        self.session.add(result_content)
        self.session.commit()
        
        # Create completed job
        completed_time = datetime.utcnow()
        job = GenerationJob(
            user_id=self.test_user1.id,
            job_type="text",
            prompt="Generate a story",
            status="completed",
            content_id=result_content.id,
            started_at=completed_time,
            completed_at=completed_time
        )
        
        self.session.add(job)
        self.session.commit()
        
        assert job.status == "completed"
        assert job.result_content.title == "Generated Story"
        assert job.completed_at is not None
    
    def test_model_timestamps(self):
        """Test that timestamps are automatically set on model creation."""
        user = User(username="timestampuser", email="timestamp@example.com")
        self.session.add(user)
        self.session.commit()
        
        # Check that timestamps were set
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        
        # Check that created_at and updated_at are close to now
        time_diff = datetime.utcnow() - user.created_at
        assert time_diff.total_seconds() < 5  # Within 5 seconds

    def test_generation_job_backward_compatibility_aliases(self):
        """Test backward-compatible aliases for renamed GenerationJob fields."""
        # Create a job with new field names
        job = GenerationJob(
            user_id=self.test_user1.id,
            job_type="image",
            prompt="Test prompt",
            params={"model": "test-model", "temperature": 0.7},
            status="pending"
        )
        self.session.add(job)
        self.session.commit()

        # Test that 'parameters' alias works for reading
        assert job.parameters == job.params
        assert job.parameters["model"] == "test-model"

        # Test that 'parameters' alias works for writing
        job.parameters = {"new_model": "updated", "temp": 0.9}
        assert job.params == {"new_model": "updated", "temp": 0.9}
        assert job.parameters == {"new_model": "updated", "temp": 0.9}

        # Test result_content_id alias (reading)
        assert job.result_content_id is None
        assert job.result_content_id == job.content_id

        # Create a content item
        result_content = ContentItem(
            title="Generated Image",
            content_type="image",
            content_data="/path/to/image.png",
            prompt="Test prompt for alias test",
            creator_id=self.test_user1.id
        )
        self.session.add(result_content)
        self.session.commit()

        # Test result_content_id alias (writing)
        job.result_content_id = result_content.id
        assert job.content_id == result_content.id
        assert job.result_content_id == result_content.id

        # Test result_content relationship alias
        assert job.result_content is not None
        assert job.result_content.id == result_content.id
        assert job.result_content == job.content
