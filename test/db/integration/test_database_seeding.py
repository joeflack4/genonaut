"""Tests for database seeding functionality with TSV data.

Tests the database initialization and seeding using TSV files for test data.
"""

import pytest
import tempfile
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add test directory and project root to Python path for imports
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, test_dir)

from genonaut.db.init import DatabaseInitializer
from genonaut.db.schema import (
    Base,
    User,
    ContentItem,
    ContentItemAuto,
    UserInteraction,
    Recommendation,
    GenerationJob,
)
from ..utils import seed_database_from_tsv, get_next_test_schema_name, create_test_database_url


class TestDatabaseSeeding:
    """Test cases for database seeding with TSV data."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database for each test."""
        # Create a temporary SQLite database file for testing
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_file.close()
        
        # Use incremental test schema naming for real databases
        base_url = f'sqlite:///{self.temp_db_file.name}'
        test_schema_name = get_next_test_schema_name(base_url)
        self.test_db_url = create_test_database_url(base_url, test_schema_name)
        
        # Initialize database
        self.initializer = DatabaseInitializer(self.test_db_url)
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        self.session = self.initializer.session_factory()
    
    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'session'):
            self.session.close()
        
        if hasattr(self.initializer, 'engine') and self.initializer.engine:
            self.initializer.engine.dispose()
        
        # Remove temporary database file
        try:
            os.unlink(self.temp_db_file.name)
        except OSError:
            pass
    
    def test_seed_database_from_tsv_files(self):
        """Test seeding database with data from TSV files."""
        # Seed the database
        seed_database_from_tsv(self.session)
        
        # Verify users were created
        users = self.session.query(User).all()
        assert len(users) >= 3
        
        usernames = [user.username for user in users]
        assert "Admin" in usernames
        assert "bob_artist" in usernames
        assert "carol_reader" in usernames
        
        # Verify user preferences were loaded correctly
        alice = self.session.query(User).filter_by(username="Admin").first()
        assert alice is not None
        assert "sci-fi" in alice.preferences.get("favorite_genres", [])
        assert "text" in alice.preferences.get("content_types", [])
        
        # Verify content items were created
        content_items = self.session.query(ContentItem).all()
        assert len(content_items) >= 3
        
        content_titles = [item.title for item in content_items]
        assert "AI-Generated Sci-Fi Story" in content_titles
        assert "Fantasy Landscape" in content_titles
        assert "Mystery Audio Drama" in content_titles
        
        # Verify content item relationships
        sci_fi_story = self.session.query(ContentItem).filter_by(
            title="AI-Generated Sci-Fi Story"
        ).first()
        assert sci_fi_story is not None
        assert sci_fi_story.creator.username == "Admin"
        assert "sci-fi" in sci_fi_story.tags
        assert sci_fi_story.quality_score == 0.85

        # Verify auto-generated content table exists but remains empty
        auto_items = self.session.query(ContentItemAuto).all()
        assert auto_items == []

        # Verify user interactions were created
        interactions = self.session.query(UserInteraction).all()
        assert len(interactions) >= 3
        
        # Verify specific interaction
        view_interaction = self.session.query(UserInteraction).filter_by(
            interaction_type="view"
        ).first()
        assert view_interaction is not None
        assert view_interaction.user.username == "Admin"
        assert view_interaction.content_item.title == "Fantasy Landscape"
        assert view_interaction.rating == 5
        assert view_interaction.duration == 120
        
        # Verify recommendations were created
        recommendations = self.session.query(Recommendation).all()
        assert len(recommendations) >= 2
        
        # Verify specific recommendation
        alice_rec = self.session.query(Recommendation).join(User).filter(
            User.username == "Admin"
        ).first()
        assert alice_rec is not None
        assert alice_rec.content_item.title == "Mystery Audio Drama"
        assert alice_rec.recommendation_score == 0.87
        assert alice_rec.algorithm_version == "v1.0"
        assert not alice_rec.is_served
        
        # Verify generation jobs were created
        generation_jobs = self.session.query(GenerationJob).all()
        assert len(generation_jobs) >= 2
        
        # Verify completed job
        completed_job = self.session.query(GenerationJob).filter_by(
            status="completed"
        ).first()
        assert completed_job is not None
        assert completed_job.user.username == "Admin"
        assert completed_job.job_type == "text"
        assert completed_job.result_content.title == "AI-Generated Sci-Fi Story"
        assert completed_job.started_at is not None
        assert completed_job.completed_at is not None
        
        # Verify pending job
        pending_job = self.session.query(GenerationJob).filter_by(
            status="pending"
        ).first()
        assert pending_job is not None
        assert pending_job.user.username == "bob_artist"
        assert pending_job.job_type == "image"
        assert pending_job.result_content_id is None
    
    def test_seed_database_with_custom_input_dir(self):
        """Test seeding database with custom input directory."""
        # Get the test input directory
        test_input_dir = os.path.join(os.path.dirname(__file__), '..', 'input', 'rdbms_init')
        
        # Seed with explicit directory
        seed_database_from_tsv(self.session, test_input_dir)
        
        # Verify data was loaded
        users = self.session.query(User).all()
        assert len(users) > 0
        
        content_items = self.session.query(ContentItem).all()
        assert len(content_items) > 0
    
    def test_database_relationships_after_seeding(self):
        """Test that all database relationships work correctly after seeding."""
        # Seed the database
        seed_database_from_tsv(self.session)
        
        # Test User -> ContentItem relationship
        alice = self.session.query(User).filter_by(username="Admin").first()
        assert len(alice.content_items) > 0
        
        # Test ContentItem -> User relationship
        content = alice.content_items[0]
        assert content.creator.username == "Admin"
        
        # Test User -> UserInteraction relationship
        if len(alice.interactions) > 0:
            interaction = alice.interactions[0]
            assert interaction.user.username == "Admin"
        
        # Test ContentItem -> UserInteraction relationship
        content_with_interactions = self.session.query(ContentItem).join(UserInteraction).first()
        if content_with_interactions:
            interaction = content_with_interactions.interactions[0]
            assert interaction.content_item.id == content_with_interactions.id
        
        # Test User -> Recommendation relationship
        user_with_recs = self.session.query(User).join(Recommendation).first()
        if user_with_recs:
            rec = user_with_recs.recommendations[0]
            assert rec.user.id == user_with_recs.id
    
    def test_json_field_parsing(self):
        """Test that JSON fields in TSV files are parsed correctly."""
        # Seed the database
        seed_database_from_tsv(self.session)
        
        # Test user preferences (JSON field)
        alice = self.session.query(User).filter_by(username="Admin").first()
        preferences = alice.preferences
        assert isinstance(preferences, dict)
        assert "favorite_genres" in preferences
        assert isinstance(preferences["favorite_genres"], list)
        
        # Test content metadata (JSON field)
        sci_fi_story = self.session.query(ContentItem).filter_by(
            title="AI-Generated Sci-Fi Story"
        ).first()
        item_metadata = sci_fi_story.item_metadata
        assert isinstance(item_metadata, dict)
        assert item_metadata["word_count"] == 1500
        assert item_metadata["genre"] == "sci-fi"
        
        # Test content tags (JSON array)
        tags = sci_fi_story.tags
        assert isinstance(tags, list)
        assert "sci-fi" in tags
        
        # Test interaction metadata
        interaction = self.session.query(UserInteraction).filter_by(
            interaction_type="view"
        ).first()
        if interaction.interaction_metadata:
            assert isinstance(interaction.interaction_metadata, dict)
    
    def test_boolean_field_parsing(self):
        """Test that boolean fields in TSV files are parsed correctly."""
        # Seed the database
        seed_database_from_tsv(self.session)
        
        # Test user is_active field
        users = self.session.query(User).all()
        for user in users:
            assert isinstance(user.is_active, bool)
            assert user.is_active  # All test users should be active
        
        # Test content is_private field
        content_items = self.session.query(ContentItem).all()
        for content in content_items:
            assert isinstance(content.is_private, bool)
            # is_private can be either True or False, so no assertion on specific value
        
        # Test recommendation is_served field
        recommendations = self.session.query(Recommendation).all()
        for rec in recommendations:
            assert isinstance(rec.is_served, bool)
            assert not rec.is_served  # All test recommendations should not be served
    
    def test_numeric_field_parsing(self):
        """Test that numeric fields in TSV files are parsed correctly."""
        # Seed the database
        seed_database_from_tsv(self.session)
        
        # Test content quality_score (float)
        content_items = self.session.query(ContentItem).all()
        for content in content_items:
            assert isinstance(content.quality_score, float)
            assert content.quality_score >= 0.0
            assert content.quality_score <= 1.0
        
        # Test interaction rating (int)
        interactions = self.session.query(UserInteraction).all()
        for interaction in interactions:
            if interaction.rating is not None:
                assert isinstance(interaction.rating, int)
                assert interaction.rating >= 1
                assert interaction.rating <= 5
        
        # Test recommendation score (float)
        recommendations = self.session.query(Recommendation).all()
        for rec in recommendations:
            assert isinstance(rec.recommendation_score, float)
            assert rec.recommendation_score >= 0.0
            assert rec.recommendation_score <= 1.0
