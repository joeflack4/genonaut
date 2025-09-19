"""PostgreSQL integration tests for database initialization and role management."""

import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from genonaut.db.init import initialize_database, DatabaseInitializer
from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob
from .utils import get_admin_database_url


class TestPostgresDatabaseIntegration:
    """PostgreSQL integration tests using separate databases for isolation."""
    
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
            self.__class__.admin_demo_db_url = get_admin_database_url(demo=True)
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
        # Work directly in the public schema of the admin database
        self.test_db_url = self.__class__.admin_db_url
        self.admin_demo_db_url = self.__class__.admin_demo_db_url
        # Ensure a clean slate before each test
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=True
        )
    
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
        """Tables should exist in the public schema after initialization."""
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=True
        )

        engine = create_engine(self.admin_db_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """))

            tables = {row[0] for row in result}
            expected_tables = {'users', 'content_items', 'user_interactions', 'recommendations', 'generation_jobs'}

            for expected_table in expected_tables:
                assert expected_table in tables, f"Table {expected_table} should exist in public schema"

        engine.dispose()
    
    def test_main_and_demo_databases_have_tables(self):
        """Ensure both main and demo databases expose the expected tables in public schema."""
        # Initialize primary and demo databases separately
        initialize_database(
            create_db=True,
            drop_existing=True,
            demo=False
        )

        initialize_database(
            create_db=True,
            drop_existing=True,
            demo=True
        )

        expected_tables = {
            'users',
            'content_items',
            'user_interactions',
            'recommendations',
            'generation_jobs'
        }

        targets = [
            (self.admin_db_url, 'main'),
            (self.admin_demo_db_url, 'demo')
        ]

        for url, label in targets:
            engine = create_engine(url)
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                tables = {row[0] for row in result}
                for expected_table in expected_tables:
                    assert expected_table in tables, (
                        f"Table {expected_table} should exist in public schema for the {label} database"
                    )
            engine.dispose()
    
    def test_database_isolation_between_main_and_demo(self):
        """Data inserted into main database should not appear in demo database."""
        # Initialize both databases
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=True
        )

        initialize_database(
            database_url=get_admin_database_url(demo=True),
            create_db=True,
            drop_existing=True,
            demo=True
        )

        main_engine = create_engine(self.test_db_url)
        demo_engine = create_engine(self.admin_demo_db_url)

        MainSession = sessionmaker(bind=main_engine)
        DemoSession = sessionmaker(bind=demo_engine)

        main_session = MainSession()
        demo_session = DemoSession()

        username = "integration_main_user"

        try:
            user = User(username=username, email="main@example.com")
            main_session.add(user)
            main_session.commit()

            # Main database should have the record
            assert main_session.query(User).filter_by(username=username).count() == 1

            # Demo database should remain empty
            assert demo_session.query(User).filter_by(username=username).count() == 0
        finally:
            main_session.close()
            demo_session.close()
            main_engine.dispose()
            demo_engine.dispose()
    
    def test_user_permissions(self):
        """Test that different user roles have appropriate permissions."""
        initialize_database(
            database_url=self.test_db_url,
            create_db=True,
            drop_existing=True
        )
        
        admin_password = os.getenv('DB_PASSWORD_ADMIN')
        rw_password = os.getenv('DB_PASSWORD_RW')
        ro_password = os.getenv('DB_PASSWORD_RO')
        
        base_url = '/'.join(self.test_db_url.split('/')[:-1]) + '/' + self.test_db_url.split('/')[-1]

        # Test RW user can insert/update/delete
        rw_url = base_url.replace('genonaut_admin:' + admin_password, f'genonaut_rw:{rw_password}')
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
