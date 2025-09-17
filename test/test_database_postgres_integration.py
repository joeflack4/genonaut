"""PostgreSQL integration tests for database initialization and schema management.

Tests the full database initialization process with PostgreSQL using admin credentials
and proper test schema isolation.
"""

import pytest
import os
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from genonaut.db.init import initialize_database, DatabaseInitializer
from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob
from .utils import get_admin_database_url, get_next_test_schema_name, clear_excess_test_schemas


class TestPostgresDatabaseIntegration:
    """PostgreSQL integration test cases for database operations with proper schema isolation."""
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self):
        """Set up test environment for the entire test class."""
        # Skip tests if PostgreSQL environment not configured
        if not all([
            os.getenv('DB_PASSWORD_ADMIN'),
            os.getenv('DB_PASSWORD_RW'), 
            os.getenv('DB_PASSWORD_RO')
        ]):
            pytest.skip("PostgreSQL environment not configured - missing admin/rw/ro passwords")
        
        try:
            self.__class__.admin_db_url = get_admin_database_url()
            # Test connection to ensure database is available
            engine = create_engine(self.__class__.admin_db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
        except Exception as e:
            pytest.skip(f"PostgreSQL database not available: {e}")
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment for each test."""
        # Get next available test schema name using admin credentials
        self.test_schema = get_next_test_schema_name(self.__class__.admin_db_url)
        self.test_db_url = self.__class__.admin_db_url
        
        # Clean up any excess test schemas (keep latest 3)
        clear_excess_test_schemas(self.__class__.admin_db_url, keep_latest=3)
    
    def teardown_method(self):
        """Clean up after each test."""
        # Drop the test schema if it exists
        try:
            engine = create_engine(self.__class__.admin_db_url)
            with engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {self.test_schema} CASCADE"))
                conn.commit()
            engine.dispose()
        except Exception:
            pass  # Best effort cleanup
    
    def test_database_and_user_creation(self):
        """Test database and user creation using the SQL template."""
        initializer = DatabaseInitializer(self.test_db_url)
        
        # This should create the database and users if they don't exist
        initializer.create_database_and_users()
        
        # Verify that the database and users exist by connecting with each user type
        admin_password = os.getenv('DB_PASSWORD_ADMIN')
        rw_password = os.getenv('DB_PASSWORD_RW')
        ro_password = os.getenv('DB_PASSWORD_RO')
        
        # Test admin user connection
        admin_url = self.test_db_url.replace('genonaut_admin:' + admin_password, f'genonaut_admin:{admin_password}')
        admin_engine = create_engine(admin_url)
        with admin_engine.connect() as conn:
            result = conn.execute(text("SELECT current_user"))
            assert result.fetchone()[0] == 'genonaut_admin'
        admin_engine.dispose()
        
        # Test rw user connection
        base_url = '/'.join(self.test_db_url.split('/')[:-1]) + '/' + self.test_db_url.split('/')[-1]
        rw_url = base_url.replace('genonaut_admin:' + admin_password, f'genonaut_rw:{rw_password}')
        rw_engine = create_engine(rw_url)
        with rw_engine.connect() as conn:
            result = conn.execute(text("SELECT current_user"))
            assert result.fetchone()[0] == 'genonaut_rw'
        rw_engine.dispose()
        
        # Test ro user connection
        ro_url = base_url.replace('genonaut_admin:' + admin_password, f'genonaut_ro:{ro_password}')
        ro_engine = create_engine(ro_url)
        with ro_engine.connect() as conn:
            result = conn.execute(text("SELECT current_user"))
            assert result.fetchone()[0] == 'genonaut_ro'
        ro_engine.dispose()
    
    def test_schema_creation_and_table_setup(self):
        """Test schema creation and table setup in test schema."""
        # Initialize database with test schema
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            schema_name=self.test_schema
        )
        
        # Verify the test schema exists
        engine = create_engine(self.admin_db_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = :schema_name
            """), {"schema_name": self.test_schema})
            
            assert result.fetchone() is not None, f"Test schema {self.test_schema} should exist"
        
        # Verify tables exist in the test schema
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema_name
            """), {"schema_name": self.test_schema})
            
            tables = [row[0] for row in result]
            expected_tables = ['users', 'content_items', 'user_interactions', 'recommendations', 'generation_jobs']
            
            for expected_table in expected_tables:
                assert expected_table in tables, f"Table {expected_table} should exist in schema {self.test_schema}"
        
        engine.dispose()
    
    def test_app_and_demo_schema_creation(self):
        """Test creation of app and demo schemas with tables."""
        # Initialize database without specifying test schema (normal mode)
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False
        )
        
        # Verify both app and demo schemas exist
        engine = create_engine(self.admin_db_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('app', 'demo')
                ORDER BY schema_name
            """))
            
            schemas = [row[0] for row in result]
            assert 'app' in schemas, "App schema should exist"
            assert 'demo' in schemas, "Demo schema should exist"
        
        # Verify tables exist in both schemas
        for schema in ['app', 'demo']:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema_name
                """), {"schema_name": schema})
                
                tables = [row[0] for row in result]
                expected_tables = ['users', 'content_items', 'user_interactions', 'recommendations', 'generation_jobs']
                
                for expected_table in expected_tables:
                    assert expected_table in tables, f"Table {expected_table} should exist in schema {schema}"
        
        engine.dispose()
    
    def test_test_schema_isolation(self):
        """Test that multiple test schemas can be created and are isolated."""
        # Create first test schema
        schema1 = self.test_schema
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            schema_name=schema1
        )
        
        # Create data in first schema
        schema1_url = f"{self.test_db_url}?options=-csearch_path%3D{schema1}"
        engine1 = create_engine(schema1_url)
        Session1 = sessionmaker(bind=engine1)
        session1 = Session1()
        
        user1 = User(username="schema1_user", email="schema1@example.com")
        session1.add(user1)
        session1.commit()
        session1.close()
        
        # Get second test schema
        schema2 = get_next_test_schema_name(self.admin_db_url)
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            schema_name=schema2
        )
        
        # Create different data in second schema
        schema2_url = f"{self.test_db_url}?options=-csearch_path%3D{schema2}"
        engine2 = create_engine(schema2_url)
        Session2 = sessionmaker(bind=engine2)
        session2 = Session2()
        
        user2 = User(username="schema2_user", email="schema2@example.com")
        session2.add(user2)
        session2.commit()
        session2.close()
        
        # Verify isolation - each schema should only see its own data
        session1 = Session1()
        users_in_schema1 = session1.query(User).all()
        assert len(users_in_schema1) == 1
        assert users_in_schema1[0].username == "schema1_user"
        session1.close()
        
        session2 = Session2()
        users_in_schema2 = session2.query(User).all()
        assert len(users_in_schema2) == 1
        assert users_in_schema2[0].username == "schema2_user"
        session2.close()
        
        # Clean up second schema
        try:
            engine = create_engine(self.admin_db_url)
            with engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema2} CASCADE"))
                conn.commit()
            engine.dispose()
        except Exception:
            pass
        
        engine1.dispose()
        engine2.dispose()
    
    def test_user_permissions(self):
        """Test that different user roles have appropriate permissions."""
        # Create test schema with tables
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=False,
            schema_name=self.test_schema
        )
        
        admin_password = os.getenv('DB_PASSWORD_ADMIN')
        rw_password = os.getenv('DB_PASSWORD_RW')
        ro_password = os.getenv('DB_PASSWORD_RO')
        
        base_url = '/'.join(self.test_db_url.split('/')[:-1]) + '/' + self.test_db_url.split('/')[-1]
        
        # Test RW user can insert/update/delete
        rw_url = base_url.replace('genonaut_admin:' + admin_password, f'genonaut_rw:{rw_password}')
        rw_url += f"?options=-csearch_path%3D{self.test_schema}"
        rw_engine = create_engine(rw_url)
        RWSession = sessionmaker(bind=rw_engine)
        rw_session = RWSession()
        
        # RW user should be able to insert data
        test_user = User(username="rw_test_user", email="rw@example.com")
        rw_session.add(test_user)
        rw_session.commit()
        
        # Verify data was inserted
        users = rw_session.query(User).all()
        assert len(users) == 1
        rw_session.close()
        rw_engine.dispose()
        
        # Test RO user can only read
        ro_url = base_url.replace('genonaut_admin:' + admin_password, f'genonaut_ro:{ro_password}')
        ro_url += f"?options=-csearch_path%3D{self.test_schema}"
        ro_engine = create_engine(ro_url)
        ROSession = sessionmaker(bind=ro_engine)
        ro_session = ROSession()
        
        # RO user should be able to read data
        users = ro_session.query(User).all()
        assert len(users) == 1
        assert users[0].username == "rw_test_user"
        
        # RO user should NOT be able to insert data (this should fail)
        ro_test_user = User(username="ro_test_user", email="ro@example.com")
        ro_session.add(ro_test_user)
        
        with pytest.raises(Exception):  # Should raise a permission error
            ro_session.commit()
        
        ro_session.rollback()
        ro_session.close()
        ro_engine.dispose()


