"""Integration tests for database operations.

Tests database operations with actual database connections using the migrated schema.

todo: datetime.utcnow(): In newer Python versions, seems to be .now(datetime.UTC)
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import text, inspect

from genonaut.db.schema import Base, User, ContentItem, ContentItemAuto, UserInteraction, Recommendation, GenerationJob


class TestDatabaseIntegration:
    """Integration test cases for database operations.

    These tests use the postgres_session fixture which provides:
    - Properly migrated schema (including partitioned tables)
    - Automatic rollback after each test
    - Transaction isolation
    """

    def test_full_database_initialization_workflow(self, postgres_session):
        """Test that the database schema is properly initialized via migrations."""
        # Verify tables exist by inspecting the database
        inspector = inspect(postgres_session.bind)
        table_names = inspector.get_table_names()

        expected_tables = [
            'users',
            'content_items',
            'content_items_auto',
            'content_items_all',  # Partitioned parent table from migrations
            'user_interactions',
            'recommendations',
            'generation_jobs'
        ]

        for expected_table in expected_tables:
            assert expected_table in table_names, f"Expected table '{expected_table}' not found in database"

        # Verify content_items_all is a partitioned table (from migrations)
        result = postgres_session.execute(text("""
            SELECT c.relkind
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'content_items_all'
        """))
        row = result.fetchone()
        assert row is not None, "content_items_all table not found"
        assert row[0] == 'p', "content_items_all should be partitioned table (created by migrations)"
    
    def test_user_content_relationship_integrity(self, postgres_session):
        """Test that user-content relationships work correctly across operations."""
        from test.conftest import sync_content_tags_for_tests

        # Create a user
        user = User(
            username="integration_user",
            email="integration@example.com",
            preferences={"test": True}
        )
        postgres_session.add(user)
        postgres_session.commit()

        # Create content items for this user
        tags_one = ["integration", "test"]
        content1 = ContentItem(
            title="Integration Test Content 1",
            content_type="text",
            content_data="Test content 1",
            creator_id=user.id,
            prompt="Test prompt"
        )
        postgres_session.add(content1)
        postgres_session.commit()
        postgres_session.refresh(content1)
        sync_content_tags_for_tests(postgres_session, content1.id, 'regular', tags_one)

        tags_two = []
        content2 = ContentItem(
            title="Integration Test Content 2",
            content_type="image",
            content_data="/path/to/test/image.jpg",
            creator_id=user.id,
            item_metadata={"size": "1024x768"},
            prompt="Test prompt"
        )
        postgres_session.add(content2)
        postgres_session.commit()
        postgres_session.refresh(content2)
        sync_content_tags_for_tests(postgres_session, content2.id, 'regular', tags_two)

        tags_auto = ["automation"]
        auto_item = ContentItemAuto(
            title="Automated Content",
            content_type="text",
            content_data="Automated payload",
            creator_id=user.id,
            prompt="Test prompt",
            item_metadata={"source": "auto"},
        )
        postgres_session.add(auto_item)
        postgres_session.commit()
        postgres_session.refresh(auto_item)
        sync_content_tags_for_tests(postgres_session, auto_item.id, 'auto', tags_auto)

        # Test forward relationships (user -> content)
        user_content = postgres_session.query(ContentItem).filter_by(creator_id=user.id).all()
        assert len(user_content) == 2

        # Test backward relationships (content -> user)
        assert content1.creator.username == "integration_user"
        assert content2.creator.email == "integration@example.com"

        # Test ORM relationship properties
        assert len(user.content_items) == 2
        assert len(user.auto_content_items) == 1
        assert content1 in user.content_items
        assert content2 in user.content_items
        assert auto_item in user.auto_content_items

        # Auto item should mirror fields of regular content
        assert auto_item.item_metadata["source"] == "auto"
    
    def test_user_interaction_workflow(self, postgres_session):
        """Test complete user interaction workflow."""
        # Create users and content
        creator = User(username="creator", email="creator@example.com")
        viewer = User(username="viewer", email="viewer@example.com")

        postgres_session.add_all([creator, viewer])
        postgres_session.commit()

        content = ContentItem(
            title="Interactive Content",
            content_type="video",
            content_data="/path/to/video.mp4",
            creator_id=creator.id,
            prompt="Test prompt"
        )
        postgres_session.add(content)
        postgres_session.commit()

        # Create various interactions
        interactions = [
            UserInteraction(
                user_id=viewer.id,
                content_item_id=content.id,
                interaction_type="view",
                duration=300,
                interaction_metadata={"device": "mobile"}
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
                interaction_metadata={"device": "desktop"}
            )
        ]

        postgres_session.add_all(interactions)
        postgres_session.commit()

        # Test interaction queries
        viewer_interactions = postgres_session.query(UserInteraction).filter_by(user_id=viewer.id).all()
        assert len(viewer_interactions) == 2

        content_interactions = postgres_session.query(UserInteraction).filter_by(content_item_id=content.id).all()
        assert len(content_interactions) == 3

        # Test specific interaction data
        like_interaction = postgres_session.query(UserInteraction).filter_by(
            interaction_type="like", user_id=viewer.id
        ).first()
        assert like_interaction is not None
        assert like_interaction.rating == 5
    
    def test_recommendation_generation_workflow(self, postgres_session):
        """Test recommendation generation and tracking workflow."""
        # Create users and content
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")

        postgres_session.add_all([user1, user2])
        postgres_session.commit()

        content1 = ContentItem(
            title="Content 1",
            content_type="text",
            content_data="Content 1 data",
            creator_id=user1.id,
            prompt="Test prompt"
        )

        content2 = ContentItem(
            title="Content 2",
            content_type="image",
            content_data="/path/to/image.jpg",
            creator_id=user1.id,
            prompt="Test prompt"
        )

        postgres_session.add_all([content1, content2])
        postgres_session.commit()

        # Generate recommendations
        recommendations = [
            Recommendation(
                user_id=user2.id,
                content_item_id=content1.id,
                recommendation_score=0.85,
                algorithm_version="test_v1.0",
                rec_metadata={"reason": "collaborative_filtering"}
            ),
            Recommendation(
                user_id=user2.id,
                content_item_id=content2.id,
                recommendation_score=0.72,
                algorithm_version="test_v1.0",
                rec_metadata={"reason": "content_based"}
            )
        ]

        postgres_session.add_all(recommendations)
        postgres_session.commit()

        # Test recommendation queries
        user_recommendations = postgres_session.query(Recommendation).filter_by(user_id=user2.id).all()
        assert len(user_recommendations) == 2

        high_score_recs = postgres_session.query(Recommendation).filter(
            Recommendation.recommendation_score > 0.8
        ).all()
        assert len(high_score_recs) == 1
        assert high_score_recs[0].recommendation_score == 0.85

        # Test serving recommendations
        best_rec = postgres_session.query(Recommendation).filter_by(user_id=user2.id).order_by(
            Recommendation.recommendation_score.desc()
        ).first()

        best_rec.is_served = True
        postgres_session.commit()

        # Verify served status
        served_recs = postgres_session.query(Recommendation).filter_by(is_served=True).all()
        assert len(served_recs) == 1
    
    def test_generation_job_lifecycle(self, postgres_session):
        """Test complete generation job lifecycle."""
        # Create user
        suffix = uuid.uuid4().hex[:8]
        user = User(
            username=f"generator-{suffix}",
            email=f"generator-{suffix}@example.com",
        )
        postgres_session.add(user)
        postgres_session.commit()

        # Create generation job
        job = GenerationJob(
            user_id=user.id,
            job_type="text",
            prompt="Generate a creative story",
            parameters={"model": "test-gpt", "temperature": 0.8},
            status="pending"
        )

        postgres_session.add(job)
        postgres_session.commit()

        # Simulate job processing
        job.status = "running"
        # noinspection PyDeprecation
        job.started_at = datetime.utcnow()
        postgres_session.commit()

        # Create result content
        result_content = ContentItem(
            title="Generated Creative Story",
            content_type="text",
            content_data="Once upon a time in a digital realm...",
            creator_id=user.id,
            item_metadata={"generated_by": "test-gpt"},
            prompt="Test prompt"
        )

        postgres_session.add(result_content)
        postgres_session.commit()

        # Complete the job
        job.status = "completed"
        # noinspection PyDeprecation
        job.completed_at = datetime.utcnow()
        job.result_content_id = result_content.id
        postgres_session.commit()

        # Test job queries and relationships
        completed_jobs = postgres_session.query(GenerationJob).filter_by(status="completed", user_id=user.id).all()
        assert len(completed_jobs) == 1

        completed_job = completed_jobs[0]
        assert completed_job.user.username.startswith("generator-")
        assert completed_job.result_content.title == "Generated Creative Story"
        assert completed_job.started_at is not None
        assert completed_job.completed_at is not None

        # Test user's generation history
        user_jobs = postgres_session.query(GenerationJob).filter_by(user_id=user.id).all()
        assert len(user_jobs) == 1
    
    def test_database_constraints_and_indexes(self, postgres_session):
        """Test that database constraints and indexes work as expected."""
        # Test unique constraints on User model
        user1 = User(username="unique_user", email="unique@example.com")
        postgres_session.add(user1)
        postgres_session.commit()

        # Test the constraint exists in the schema
        user_table = Base.metadata.tables['users']
        username_column = user_table.columns['username']
        assert username_column.unique

        email_column = user_table.columns['email']
        assert email_column.unique

        # Test indexes exist
        assert username_column.index
        assert email_column.index
    
    def test_data_persistence_across_sessions(self, postgres_session):
        """Test that data persists correctly within a transaction.

        Note: This test validates data persistence within the postgres_session fixture's
        transaction boundary. After the test, all changes are rolled back by the fixture.
        """
        # Create data
        user = User(username="persistent_user", email="persistent@example.com")
        postgres_session.add(user)
        postgres_session.commit()

        user_id = user.id

        # Expire the object to force a fresh query from the database
        postgres_session.expire(user)

        # Access data again (simulating a new query in the same transaction)
        retrieved_user = postgres_session.query(User).filter_by(id=user_id).first()
        assert retrieved_user is not None
        assert retrieved_user.username == "persistent_user"
        assert retrieved_user.email == "persistent@example.com"
