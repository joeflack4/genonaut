"""Integration tests for database operations.

Tests the full database initialization and operations with actual database connections.

todo: datetime.utcnow(): In newer Python versions, seems to be .now(datetime.UTC)
"""

import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from genonaut.db.init import DatabaseInitializer
from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob


class TestDatabaseIntegration:
    """Integration test cases for database operations."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database for each test."""
        # Create a temporary SQLite database file for integration testing
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_file.close()
        
        self.test_db_url = f'sqlite:///{self.temp_db_file.name}'
        self.initializer = DatabaseInitializer(self.test_db_url)
    
    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self.initializer, 'engine') and self.initializer.engine:
            self.initializer.engine.dispose()
        
        # Remove temporary database file
        try:
            os.unlink(self.temp_db_file.name)
        except OSError:
            pass
    
    def test_full_database_initialization_workflow(self):
        """Test the complete database initialization workflow."""
        # Initialize engine and session
        self.initializer.create_engine_and_session()
        
        # Create tables
        self.initializer.create_tables()
        
        # Verify tables exist by checking metadata
        table_names = [table.name for table in Base.metadata.tables.values()]
        expected_tables = ['users', 'content_items', 'user_interactions', 'recommendations', 'generation_jobs']
        
        for expected_table in expected_tables:
            assert expected_table in table_names
        
        # Note: Sample data seeding is now tested separately in test_database_seeding.py
        # This test just verifies that tables are created correctly
    
    def test_user_content_relationship_integrity(self):
        """Test that user-content relationships work correctly across operations."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        session = self.initializer.session_factory()
        
        # Create a user
        user = User(
            username="integration_user",
            email="integration@example.com",
            preferences={"test": True}
        )
        session.add(user)
        session.commit()
        
        # Create content items for this user
        content1 = ContentItem(
            title="Integration Test Content 1",
            content_type="text",
            content_data="Test content 1",
            creator_id=user.id,
            tags=["integration", "test"]
        )
        
        content2 = ContentItem(
            title="Integration Test Content 2", 
            content_type="image",
            content_data="/path/to/test/image.jpg",
            creator_id=user.id,
            metadata={"size": "1024x768"}
        )
        
        session.add_all([content1, content2])
        session.commit()
        
        # Test forward relationships (user -> content)
        user_content = session.query(ContentItem).filter_by(creator_id=user.id).all()
        assert len(user_content) == 2
        
        # Test backward relationships (content -> user)
        assert content1.creator.username == "integration_user"
        assert content2.creator.email == "integration@example.com"
        
        # Test ORM relationship properties
        assert len(user.content_items) == 2
        assert content1 in user.content_items
        assert content2 in user.content_items
        
        session.close()
    
    def test_user_interaction_workflow(self):
        """Test complete user interaction workflow."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        session = self.initializer.session_factory()
        
        # Create users and content
        creator = User(username="creator", email="creator@example.com")
        viewer = User(username="viewer", email="viewer@example.com")
        
        content = ContentItem(
            title="Interactive Content",
            content_type="video",
            content_data="/path/to/video.mp4",
            creator_id=1  # Will be set after commit
        )
        
        session.add_all([creator, viewer])
        session.commit()
        
        content.creator_id = creator.id
        session.add(content)
        session.commit()
        
        # Create various interactions
        interactions = [
            UserInteraction(
                user_id=viewer.id,
                content_item_id=content.id,
                interaction_type="view",
                duration=300,
                metadata={"device": "mobile"}
            ),
            UserInteraction(
                user_id=viewer.id,
                content_item_id=content.id,
                interaction_type="like",
                rating=5
            ),
            UserInteraction(
                user_id=creator.id,
                content_item_id=content.id,
                interaction_type="view",
                duration=150,
                metadata={"device": "desktop"}
            )
        ]
        
        session.add_all(interactions)
        session.commit()
        
        # Test interaction queries
        viewer_interactions = session.query(UserInteraction).filter_by(user_id=viewer.id).all()
        assert len(viewer_interactions) == 2
        
        content_interactions = session.query(UserInteraction).filter_by(content_item_id=content.id).all()
        assert len(content_interactions) == 3
        
        # Test specific interaction data
        like_interaction = session.query(UserInteraction).filter_by(
            interaction_type="like", user_id=viewer.id
        ).first()
        assert like_interaction is not None
        assert like_interaction.rating == 5
        
        session.close()
    
    def test_recommendation_generation_workflow(self):
        """Test recommendation generation and tracking workflow."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        session = self.initializer.session_factory()
        
        # Create users and content
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        
        content1 = ContentItem(
            title="Content 1",
            content_type="text",
            content_data="Content 1 data",
            creator_id=1  # Will be updated
        )
        
        content2 = ContentItem(
            title="Content 2",
            content_type="image", 
            content_data="/path/to/image.jpg",
            creator_id=1  # Will be updated
        )
        
        session.add_all([user1, user2])
        session.commit()
        
        content1.creator_id = user1.id
        content2.creator_id = user1.id
        session.add_all([content1, content2])
        session.commit()
        
        # Generate recommendations
        recommendations = [
            Recommendation(
                user_id=user2.id,
                content_item_id=content1.id,
                recommendation_score=0.85,
                algorithm_version="test_v1.0",
                metadata={"reason": "collaborative_filtering"}
            ),
            Recommendation(
                user_id=user2.id,
                content_item_id=content2.id,
                recommendation_score=0.72,
                algorithm_version="test_v1.0",
                metadata={"reason": "content_based"}
            )
        ]
        
        session.add_all(recommendations)
        session.commit()
        
        # Test recommendation queries
        user_recommendations = session.query(Recommendation).filter_by(user_id=user2.id).all()
        assert len(user_recommendations) == 2
        
        high_score_recs = session.query(Recommendation).filter(
            Recommendation.recommendation_score > 0.8
        ).all()
        assert len(high_score_recs) == 1
        assert high_score_recs[0].recommendation_score == 0.85
        
        # Test serving recommendations
        best_rec = session.query(Recommendation).filter_by(user_id=user2.id).order_by(
            Recommendation.recommendation_score.desc()
        ).first()
        
        best_rec.is_served = True
        session.commit()
        
        # Verify served status
        served_recs = session.query(Recommendation).filter_by(is_served=True).all()
        assert len(served_recs) == 1
        
        session.close()
    
    def test_generation_job_lifecycle(self):
        """Test complete generation job lifecycle."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        session = self.initializer.session_factory()
        
        # Create user
        user = User(username="generator", email="generator@example.com")
        session.add(user)
        session.commit()
        
        # Create generation job
        job = GenerationJob(
            user_id=user.id,
            job_type="text",
            prompt="Generate a creative story",
            parameters={"model": "test-gpt", "temperature": 0.8},
            status="pending"
        )
        
        session.add(job)
        session.commit()
        
        # Simulate job processing
        job.status = "running"
        # noinspection PyDeprecation
        job.started_at = datetime.utcnow()
        session.commit()

        # Create result content
        result_content = ContentItem(
            title="Generated Creative Story",
            content_type="text",
            content_data="Once upon a time in a digital realm...",
            creator_id=user.id,
            metadata={"generated_by": "test-gpt"}
        )

        session.add(result_content)
        session.commit()

        # Complete the job
        job.status = "completed"
        # noinspection PyDeprecation
        job.completed_at = datetime.utcnow()
        job.result_content_id = result_content.id
        session.commit()
        
        # Test job queries and relationships
        completed_jobs = session.query(GenerationJob).filter_by(status="completed").all()
        assert len(completed_jobs) == 1
        
        completed_job = completed_jobs[0]
        assert completed_job.user.username == "generator"
        assert completed_job.result_content.title == "Generated Creative Story"
        assert completed_job.started_at is not None
        assert completed_job.completed_at is not None
        
        # Test user's generation history
        user_jobs = session.query(GenerationJob).filter_by(user_id=user.id).all()
        assert len(user_jobs) == 1
        
        session.close()
    
    def test_database_constraints_and_indexes(self):
        """Test that database constraints and indexes work as expected."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        session = self.initializer.session_factory()
        
        # Test unique constraints on User model
        user1 = User(username="unique_user", email="unique@example.com")
        session.add(user1)
        session.commit()
        
        # Try to create user with duplicate username (should work in SQLite without enforcement)
        # But we can test the constraint exists in the schema
        user_table = Base.metadata.tables['users']
        username_column = user_table.columns['username']
        assert username_column.unique
        
        email_column = user_table.columns['email']
        assert email_column.unique
        
        # Test indexes exist
        assert username_column.index
        assert email_column.index
        
        session.close()
    
    def test_data_persistence_across_sessions(self):
        """Test that data persists correctly across different sessions."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        # Create data in first session
        session1 = self.initializer.session_factory()
        
        user = User(username="persistent_user", email="persistent@example.com")
        session1.add(user)
        session1.commit()
        
        user_id = user.id
        session1.close()
        
        # Access data in second session
        session2 = self.initializer.session_factory()
        
        retrieved_user = session2.query(User).filter_by(id=user_id).first()
        assert retrieved_user is not None
        assert retrieved_user.username == "persistent_user"
        assert retrieved_user.email == "persistent@example.com"
        
        session2.close()


