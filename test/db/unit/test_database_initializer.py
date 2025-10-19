"""Unit tests for DatabaseInitializer class.

Tests the database initialization functionality in genonaut.db.init module.

Tests database initialization functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine.url import make_url

from genonaut.db.init import (
    PROJECT_ROOT,
    DatabaseInitializer,
    initialize_database,
    resolve_seed_path,
)
from genonaut.db.schema import Base, User, ContentItem


class TestDatabaseInitializer:
    """Test cases for DatabaseInitializer class."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test environment for each test."""
        # Use PostgreSQL test database (provided by conftest.py)
        # For initializer tests, we use the test database URL from environment
        self.test_db_url = os.getenv('DATABASE_URL_TEST', 'postgresql://localhost/genonaut_test')
        self.initializer = DatabaseInitializer(self.test_db_url)
        yield
        # Teardown after each test
        if hasattr(self.initializer, 'engine') and self.initializer.engine:
            self.initializer.engine.dispose()
    
    def test_init_with_provided_url(self):
        """Test DatabaseInitializer initialization with provided URL."""
        custom_url = "postgresql://user:pass@localhost:5432/testdb"
        initializer = DatabaseInitializer(custom_url)
        
        assert initializer.database_url == custom_url
        assert initializer.engine is None
        assert initializer.session_factory is None
    
    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://env:pass@host:5432/envdb',
        'GENONAUT_DB_ENVIRONMENT': 'dev',
        'DB_NAME_TEST': 'genonaut_test'
    })
    def test_get_database_url_from_env_var(self):
        """Test getting database URL from DATABASE_URL environment variable."""
        initializer = DatabaseInitializer()
        
        assert initializer.database_url == 'postgresql://env:pass@host:5432/envdb'
    
    @patch.dict(os.environ, {
        'DB_HOST': 'testhost',
        'DB_PORT': '5433', 
        'DB_NAME': 'testdb',
        'DB_USER_FOR_INIT': 'testuser',
        'DB_PASSWORD_FOR_INIT': 'testpass'
    }, clear=True)
    def test_get_database_url_from_components(self):
        """Test constructing database URL from individual environment variables."""
        initializer = DatabaseInitializer()
        
        expected_url = "postgresql://testuser:testpass@testhost:5433/testdb"
        assert initializer.database_url == expected_url
    
    @patch.dict(os.environ, {
        'DB_HOST': 'localhost',
        'DB_USER_FOR_INIT': 'postgres'
    }, clear=True)
    def test_get_database_url_missing_password_raises_error(self):
        """Test that missing password raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            DatabaseInitializer()
        
        assert "Database password must be provided" in str(exc_info.value)
    
    @patch.dict(os.environ, {'DB_PASSWORD_FOR_INIT': 'testpass'}, clear=True) 
    def test_get_database_url_uses_defaults(self):
        """Test that default values are used when environment variables not set."""
        initializer = DatabaseInitializer()
        
        expected_url = "postgresql://postgres:testpass@localhost:5432/genonaut"
        assert initializer.database_url == expected_url

    @patch.dict(os.environ, {
        'DATABASE_URL_TEST': 'postgresql://genonaut_admin:test_admin@localhost:5432/genonaut_test_data'
    }, clear=True)
    def test_get_database_url_uses_explicit_test_url(self):
        """Ensure the test environment honours the dedicated database URL."""
        initializer = DatabaseInitializer(environment="test")

        assert initializer.database_url == 'postgresql://genonaut_admin:test_admin@localhost:5432/genonaut_test_data'
        assert initializer.environment == "test"

    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://genonaut_admin:admin@localhost:5432/genonaut_main',
        'DB_PASSWORD_ADMIN': 'admin'
    }, clear=True)
    def test_get_database_url_test_environment_falls_back(self):
        """Test URLs fall back to the main connection with a test database name."""
        initializer = DatabaseInitializer(environment="test")

        parsed_url = make_url(initializer.database_url)
        assert parsed_url.username == "genonaut_admin"
        assert parsed_url.host == "localhost"
        assert parsed_url.database == "genonaut_test"
        assert initializer.environment == "test"
    
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
        with pytest.raises(Exception):  # PostgreSQL raises OperationalError
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
    @patch('subprocess.run')
    @patch('genonaut.db.init.create_engine')
    @patch('builtins.open')
    def test_create_database_and_users_success(self, mock_open, mock_create_engine, mock_subprocess_run):
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
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        # Set up initializer with test URL
        test_url = "postgresql://user:pass@localhost:5432/testdb"
        initializer = DatabaseInitializer(test_url)
        
        # Should not raise an exception
        initializer.create_database_and_users()
        
        # Verify template was rendered and executed
        mock_open.assert_called_once()
        mock_create_engine.assert_called_with("postgresql://user:pass@localhost:5432/postgres")
        mock_subprocess_run.assert_called_once()





    def test_initialize_database_auto_seeds_for_postgres(self, tmp_path):
        """Automatic seeding should occur for Postgres when no path is provided."""
        seed_dir = tmp_path / "seed"
        seed_dir.mkdir()

        mock_initializer = MagicMock()
        mock_initializer.environment = "dev"
        mock_initializer.is_test = False
        mock_initializer.database_url = "postgresql://genonaut_admin:pass@localhost:5432/testdb"

        with patch('genonaut.db.init.DatabaseInitializer', return_value=mock_initializer) as mock_init_class, \
             patch('genonaut.db.init.load_project_config') as mock_load_config, \
             patch('genonaut.db.init.resolve_seed_path') as mock_resolve_seed_path, \
             patch('genonaut.db.init._run_alembic_upgrade') as mock_upgrade:

            mock_load_config.return_value = {'seed_data': {'main': str(seed_dir)}}
            mock_resolve_seed_path.return_value = seed_dir

            initialize_database(
                database_url="postgresql://genonaut_admin:pass@localhost:5432/testdb",
                create_db=False,
                drop_existing=False
            )

            mock_init_class.assert_called_once()
            mock_initializer.create_database_and_users.assert_not_called()
            mock_initializer.enable_extensions.assert_called_once()
            mock_initializer.drop_tables.assert_not_called()
            mock_upgrade.assert_called_once_with("postgresql://genonaut_admin:pass@localhost:5432/testdb")
            mock_initializer.seed_from_tsv_directory.assert_called_once_with(seed_dir)


    def test_initialize_database_auto_drops_for_test_environment(self, tmp_path):
        """Test databases should auto-drop existing tables before seeding."""
        seed_dir = tmp_path / "seed"
        seed_dir.mkdir()

        mock_initializer = MagicMock()
        mock_initializer.environment = "test"
        mock_initializer.is_test = True
        mock_initializer.database_url = "postgresql://genonaut_admin:pass@localhost:5432/genonaut_test"
        mock_initializer.engine = MagicMock()

        with patch('genonaut.db.init.DatabaseInitializer', return_value=mock_initializer) as mock_init_class, \
             patch('genonaut.db.init.load_project_config') as mock_load_config, \
             patch('genonaut.db.init.resolve_seed_path') as mock_resolve_seed_path, \
             patch('genonaut.db.init._run_alembic_upgrade') as mock_upgrade:

            mock_load_config.return_value = {'seed_data': {'test': str(seed_dir)}}
            mock_resolve_seed_path.return_value = seed_dir

            initialize_database(environment="test", create_db=False)

            mock_init_class.assert_called_once()
            mock_initializer.create_database_and_users.assert_not_called()
            mock_initializer.drop_tables.assert_not_called()
            mock_initializer.truncate_tables.assert_called_once()
            mock_initializer.seed_from_tsv_directory.assert_called_once_with(seed_dir)
            mock_upgrade.assert_called_once_with(mock_initializer.database_url)


def test_resolve_seed_path_prefers_builtin_test_directory(tmp_path):
    """Seed path resolution should use the bundled test fixtures when available."""

    demo_seed_dir = tmp_path / "demo_seed"
    demo_seed_dir.mkdir()

    relative_demo_path = os.path.relpath(demo_seed_dir, PROJECT_ROOT)
    config = {"seed_data": {"demo": relative_demo_path}}

    resolved_path = resolve_seed_path(config, "test")

    expected_seed_path = (PROJECT_ROOT / "test" / "db" / "input" / "rdbms_init").resolve()

    # Should always use the canonical test input directory
    assert resolved_path == expected_seed_path
