"""End-to-end tests for complete database initialization workflow.

Tests the full database initialization process using the initialize_database function
and validates the complete system works as expected.
"""

import tempfile
import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from genonaut.db.init import initialize_database, DatabaseInitializer
from genonaut.db.schema import (
    Base,
    User,
    ContentItem,
    ContentItemAuto,
    UserInteraction,
    Recommendation,
    GenerationJob,
)


class TestDatabaseEndToEnd:
    """End-to-end test cases for complete database initialization."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment for each test."""
        # Create a temporary SQLite database file for testing
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db_file.close()
        
        self.test_db_url = f'sqlite:///{self.temp_db_file.name}'
        yield
        
        # Clean up after each test
        try:
            os.unlink(self.temp_db_file.name)
        except OSError:
            pass
    
    @patch('builtins.print')  # Suppress print output during tests
    def test_complete_database_initialization_with_all_options(self, mock_print):
        """Test complete database initialization with all options enabled."""
        # Initialize database with all options
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            environment="test",
        )
        
        # Verify the initialization was successful by connecting and querying
        engine = create_engine(self.test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Test that all tables exist (data seeding is tested separately)
            
            # Verify Users table exists and is accessible
            users = session.query(User).all()
            assert len(users) == 0  # Should be empty in this test
            
            # Verify ContentItems table exists
            content_items = session.query(ContentItem).all()
            assert len(content_items) == 0  # Should be empty

            # Verify ContentItemsAuto table exists
            auto_items = session.query(ContentItemAuto).all()
            assert len(auto_items) == 0

            # Verify UserInteractions table exists
            interactions = session.query(UserInteraction).all()
            assert len(interactions) == 0  # Should be empty
            
            # Verify Recommendations table exists
            recommendations = session.query(Recommendation).all()
            assert len(recommendations) == 0  # Should be empty
            
            # Verify GenerationJobs table exists
            generation_jobs = session.query(GenerationJob).all()
            assert len(generation_jobs) == 0  # Should be empty
            
        finally:
            session.close()
            engine.dispose()
    
    @patch('builtins.print')  # Suppress print output during tests
    def test_database_initialization_without_seeding(self, mock_print):
        """Test database initialization without sample data seeding."""
        # Initialize database without seeding
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            environment="test",
        )
        
        # Verify tables exist but are empty
        engine = create_engine(self.test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # All tables should exist but be empty
            assert session.query(User).count() == 0
            assert session.query(ContentItem).count() == 0
            assert session.query(ContentItemAuto).count() == 0
            assert session.query(UserInteraction).count() == 0
            assert session.query(Recommendation).count() == 0
            assert session.query(GenerationJob).count() == 0
            
            # Verify we can still insert data manually
            test_user = User(username="test_user", email="test@example.com")
            session.add(test_user)
            session.commit()
            
            assert session.query(User).count() == 1
            
        finally:
            session.close()
            engine.dispose()
    
    @patch('builtins.print')  # Suppress print output during tests
    def test_database_initialization_with_drop_existing(self, mock_print):
        """Test database initialization with dropping existing tables."""
        # First, create some initial data
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            environment="test",
        )
        
        # Verify initial data exists
        engine = create_engine(self.test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        initial_user_count = session.query(User).count()
        session.close()
        engine.dispose()
        
        assert initial_user_count == 0  # Should be empty initially
        
        # Now initialize again with drop_existing=True
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=True
        )
        
        # Verify tables were recreated (should still be empty)
        engine = create_engine(self.test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            final_user_count = session.query(User).count()
            # Should still be empty since we don't seed data in these tests
            assert final_user_count == 0
            
        finally:
            session.close()
            engine.dispose()
    
    @patch.dict(os.environ, {'DB_PASSWORD': 'test_password'}, clear=True)
    @patch('builtins.print')  # Suppress print output during tests
    def test_database_initialization_with_environment_variables(self, mock_print):
        """Test database initialization using environment variables."""
        # Test that initialization works when no URL is provided (uses env vars)
        with patch('genonaut.db.init.DatabaseInitializer') as mock_init_class, \
             patch('genonaut.db.init._run_alembic_upgrade') as mock_upgrade:
            mock_initializer = mock_init_class.return_value
            mock_initializer.database_url = "postgresql://mock:pass@localhost:5432/mockdb"

            # Call initialize_database without explicit URL
            initialize_database(
                database_url=None,  # Should use environment variables
                create_db=True,
                drop_existing=False
            )

            # Verify DatabaseInitializer was called with None (will use env vars)
            mock_init_class.assert_called_once_with(None)

            # Verify all methods were called
            mock_initializer.create_database_and_users.assert_called_once()
            mock_initializer.create_engine_and_session.assert_called_once()
            # The initializer should proceed with table creation in the active schema
            mock_upgrade.assert_called_once_with("postgresql://mock:pass@localhost:5432/mockdb")
    
    def test_database_schema_validation(self):
        """Test that the database schema matches expectations."""
        # Initialize database
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            environment="test",
        )
        
        engine = create_engine(self.test_db_url)
        
        # Verify all expected tables exist
        inspector = engine.dialect.get_table_names(engine.connect())
        expected_tables = [
            'users',
            'content_items',
            'content_items_auto',
            'user_interactions',
            'recommendations',
            'generation_jobs',
        ]
        
        for table in expected_tables:
            assert table in inspector
        
        # Verify table structures match schema definitions
        metadata = Base.metadata
        metadata.reflect(bind=engine)
        
        # Test Users table structure
        users_table = metadata.tables['users']
        user_columns = [col.name for col in users_table.columns]
        expected_user_columns = ['id', 'username', 'email', 'created_at', 'updated_at', 'preferences', 'is_active']
        
        for col in expected_user_columns:
            assert col in user_columns
        
        # Test ContentItems table structure
        content_table = metadata.tables['content_items']
        content_columns = [col.name for col in content_table.columns]
        expected_content_columns = [
            'id',
            'title',
            'content_type',
            'content_data',
            'item_metadata',
            'creator_id',
            'created_at',
            'updated_at',
            'tags',
            'quality_score',
            'is_private',
        ]

        for col in expected_content_columns:
            assert col in content_columns

        # Test ContentItemsAuto table structure mirrors ContentItems
        auto_table = metadata.tables['content_items_auto']
        auto_columns = [col.name for col in auto_table.columns]

        for col in expected_content_columns:
            assert col in auto_columns
        
        engine.dispose()
    
    @patch('builtins.print')  # Suppress print output during tests  
    def test_database_relationships_work_end_to_end(self, mock_print):
        """Test that all database relationships work in an end-to-end scenario."""
        # Initialize complete database
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            environment="test",
        )
        
        engine = create_engine(self.test_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Note: Relationship testing with actual data is done in test_database_seeding.py
            # This test just verifies that the database structure allows relationships
            
            # Verify tables exist and are accessible for relationships
            users = session.query(User).all()
            content_items = session.query(ContentItem).all()
            interactions = session.query(UserInteraction).all()
            recommendations = session.query(Recommendation).all()
            generation_jobs = session.query(GenerationJob).all()
            
            # All should be empty in this test but accessible
            assert len(users) == 0
            assert len(content_items) == 0
            assert len(interactions) == 0
            assert len(recommendations) == 0
            assert len(generation_jobs) == 0
            
        finally:
            session.close()
            engine.dispose()
    
    def test_error_handling_in_initialization(self):
        """Test that initialization handles errors gracefully."""
        # Test with invalid database URL
        with pytest.raises(Exception):  # Should raise some form of error
            initialize_database(
                database_url="invalid://bad:url/format",
                create_db=True,
                drop_existing=False
            )
