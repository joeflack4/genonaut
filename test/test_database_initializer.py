"""Unit tests for DatabaseInitializer class.

Tests the database initialization functionality in genonaut.db.init module.

todo: consider doing this in postgres instead of sqlite, or do both.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from genonaut.db.init import DatabaseInitializer
from genonaut.db.schema import Base, User, ContentItem


class TestDatabaseInitializer:
    """Test cases for DatabaseInitializer class."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment for each test."""
        # Use in-memory SQLite for testing
        self.test_db_url = 'sqlite:///:memory:'
        self.initializer = DatabaseInitializer(self.test_db_url)
        yield
        # Teardown after each test
        if hasattr(self.initializer, 'engine') and self.initializer.engine:
            Base.metadata.drop_all(self.initializer.engine)
            self.initializer.engine.dispose()
    
    def test_init_with_provided_url(self):
        """Test DatabaseInitializer initialization with provided URL."""
        custom_url = "postgresql://user:pass@localhost:5432/testdb"
        initializer = DatabaseInitializer(custom_url)
        
        assert initializer.database_url == custom_url
        assert initializer.engine is None
        assert initializer.session_factory is None
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://env:pass@host:5432/envdb'})
    def test_get_database_url_from_env_var(self):
        """Test getting database URL from DATABASE_URL environment variable."""
        initializer = DatabaseInitializer()
        
        assert initializer.database_url == 'postgresql://env:pass@host:5432/envdb'
    
    @patch.dict(os.environ, {
        'DB_HOST': 'testhost',
        'DB_PORT': '5433', 
        'DB_NAME': 'testdb',
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass'
    }, clear=True)
    def test_get_database_url_from_components(self):
        """Test constructing database URL from individual environment variables."""
        initializer = DatabaseInitializer()
        
        expected_url = "postgresql://testuser:testpass@testhost:5433/testdb"
        assert initializer.database_url == expected_url
    
    @patch.dict(os.environ, {
        'DB_HOST': 'localhost',
        'DB_USER': 'postgres'
    }, clear=True)
    def test_get_database_url_missing_password_raises_error(self):
        """Test that missing password raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DatabaseInitializer()
        
        assert "Database password must be provided" in str(exc_info.value)
    
    @patch.dict(os.environ, {'DB_PASSWORD': 'testpass'}, clear=True) 
    def test_get_database_url_uses_defaults(self):
        """Test that default values are used when environment variables not set."""
        initializer = DatabaseInitializer()
        
        expected_url = "postgresql://postgres:testpass@localhost:5432/genonaut"
        assert initializer.database_url == expected_url
    
    def test_create_engine_and_session_success(self):
        """Test successful engine and session factory creation."""
        self.initializer.create_engine_and_session()
        
        assert self.initializer.engine is not None
        assert self.initializer.session_factory is not None
        
        # Test that we can create a session
        session = self.initializer.session_factory()
        assert session is not None
        session.close()
    
    def test_create_engine_with_invalid_url_raises_error(self):
        """Test that invalid database URL raises an exception."""
        invalid_initializer = DatabaseInitializer("invalid://bad:password@host:invalidport/db")
        
        with pytest.raises((SQLAlchemyError, ValueError)):
            invalid_initializer.create_engine_and_session()
    
    def test_create_tables_success(self):
        """Test successful table creation."""
        self.initializer.create_engine_and_session()
        
        # Should not raise an exception
        self.initializer.create_tables()
        
        # Verify tables exist by checking we can create objects
        session = self.initializer.session_factory()
        user = User(username="testuser", email="test@example.com")
        session.add(user)
        session.commit()
        
        # Query should work without error
        retrieved_user = session.query(User).filter_by(username="testuser").first()
        assert retrieved_user is not None
        session.close()
    
    def test_create_tables_without_engine_raises_error(self):
        """Test that creating tables without engine raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.initializer.create_tables()
        
        assert "Engine not initialized" in str(exc_info.value)
    
    def test_drop_tables_success(self):
        """Test successful table dropping."""
        self.initializer.create_engine_and_session()
        self.initializer.create_tables()
        
        # Verify table exists
        session = self.initializer.session_factory()
        user = User(username="testuser", email="test@example.com")
        session.add(user)
        session.commit()
        session.close()
        
        # Drop tables
        self.initializer.drop_tables()
        
        # Recreate engine/session to test that tables are gone
        self.initializer.create_engine_and_session()
        session = self.initializer.session_factory()
        
        # This should fail because tables don't exist
        with pytest.raises(Exception):  # SQLite raises OperationalError
            session.query(User).first()
        
        session.close()
    
    def test_drop_tables_without_engine_raises_error(self):
        """Test that dropping tables without engine raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.initializer.drop_tables()
        
        assert "Engine not initialized" in str(exc_info.value)

    @patch.dict(os.environ, {
        'DB_PASSWORD_ADMIN': 'admin_pass',
        'DB_PASSWORD_RW': 'rw_pass', 
        'DB_PASSWORD_RO': 'ro_pass'
    })
    @patch('genonaut.db.init.create_engine')
    @patch('builtins.open')
    def test_create_database_and_users_success(self, mock_open, mock_create_engine):
        """Test successful database and user creation using SQL template."""
        # Mock file reading
        mock_file = MagicMock()
        mock_file.read.return_value = "-- Mock SQL template content"
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock the postgres engine and connection
        mock_postgres_engine = MagicMock()
        mock_connection = MagicMock()
        
        mock_postgres_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_postgres_engine
        
        # Set up initializer with test URL
        test_url = "postgresql://user:pass@localhost:5432/testdb"
        initializer = DatabaseInitializer(test_url)
        
        # Should not raise an exception
        initializer.create_database_and_users()
        
        # Verify template was rendered and executed
        mock_open.assert_called_once()
        mock_create_engine.assert_called_with("postgresql://postgres:postgres@localhost:5432/postgres")