"""Database initialization and seeding module for Genonaut.

This module provides functionality to create the PostgreSQL database schema
and seed it with initial data for development and testing purposes.
"""

import os
import re
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from jinja2 import Template

from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob
from genonaut.db.utils import get_database_url


# Load environment variables from .env file in the env/ directory
# Path from genonaut/db/init.py -> project_root/env/.env
env_path = Path(__file__).parent.parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


def _class_name_to_snake_case(class_name: str) -> str:
    """Convert a class name to snake_case for TSV filename.
    
    Args:
        class_name: Class name in PascalCase (e.g., "UserInteraction")
        
    Returns:
        Snake case name (e.g., "user_interactions")
    """
    # Insert underscore before uppercase letters (except first)
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
    # Add 's' for plural (simple pluralization)
    if not snake_case.endswith('s'):
        snake_case += 's'
    return snake_case



class DatabaseInitializer:
    """Database initialization and seeding class.
    
    Handles database connection, schema creation, and initial data seeding.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the database initializer.
        
        Args:
            database_url: PostgreSQL connection URL. If None, will use environment variable.
        """
        self.database_url = database_url or get_database_url()
        self.engine = None
        self.session_factory = None

    def create_engine_and_session(self) -> None:
        """Create SQLAlchemy engine and session factory.
        
        Raises:
            SQLAlchemyError: If database connection fails
        """
        try:
            self.engine = create_engine(
                self.database_url,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                pool_pre_ping=True,
                pool_recycle=300
            )
            self.session_factory = sessionmaker(bind=self.engine)
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to create database engine: {e}")
    
    def create_database_and_users(self) -> None:
        """Create the database and users using the Jinja2 SQL template.
        
        This method reads the init.sql template, populates it with user passwords,
        and executes the resulting SQL to create the database and user roles.
        """
        # Get the path to the SQL template
        current_dir = Path(__file__).parent
        sql_template_path = current_dir / 'init.sql'
        
        if not sql_template_path.exists():
            raise FileNotFoundError(f"SQL template not found: {sql_template_path}")
        
        # Read the template
        with open(sql_template_path, 'r') as f:
            template_content = f.read()
        
        # Get passwords from environment
        admin_password = os.getenv('DB_PASSWORD_ADMIN')
        rw_password = os.getenv('DB_PASSWORD_RW')
        ro_password = os.getenv('DB_PASSWORD_RO')
        
        if not all([admin_password, rw_password, ro_password]):
            raise ValueError("All user passwords must be provided: DB_PASSWORD_ADMIN, DB_PASSWORD_RW, DB_PASSWORD_RO")
        
        # Render the template with passwords using simple string replacement
        # This avoids Jinja2 conflicts with PostgreSQL $$ syntax
        sql_content = template_content.replace('{{ DB_PASSWORD_ADMIN }}', admin_password)
        sql_content = sql_content.replace('{{ DB_PASSWORD_RW }}', rw_password)
        sql_content = sql_content.replace('{{ DB_PASSWORD_RO }}', ro_password)
        
        # Create connection URL to 'postgres' database for admin operations
        # We need to use existing superuser credentials to create the new users
        # Try to get fallback credentials for the initial setup
        fallback_user = os.getenv('DB_USER', 'postgres')
        fallback_password = os.getenv('DB_PASSWORD')
        
        if fallback_password:
            # Use fallback credentials to connect to postgres database
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            postgres_url = f"postgresql://{fallback_user}:{fallback_password}@{host}:{port}/postgres"
        else:
            # If no fallback, try to modify the current URL to use postgres database
            postgres_url = '/'.join(self.database_url.split('/')[:-1]) + '/postgres'
        
        try:
            postgres_engine = create_engine(postgres_url)
            
            # Execute the SQL using psql for better PostgreSQL compatibility
            # This avoids issues with parsing complex PostgreSQL syntax
            import subprocess
            import tempfile
            
            # Write SQL to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(sql_content)
                temp_file_path = temp_file.name
            
            try:
                # Extract connection details for psql
                fallback_user = os.getenv('DB_USER', 'postgres')
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                
                # Execute SQL using psql
                psql_cmd = [
                    'psql',
                    '-h', host,
                    '-p', port,
                    '-U', fallback_user,
                    '-d', 'postgres',
                    '-f', temp_file_path
                ]
                
                # Set password via environment variable
                env = os.environ.copy()
                env['PGPASSWORD'] = fallback_password
                
                result = subprocess.run(psql_cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("Database and users created successfully")
                else:
                    print(f"psql output: {result.stdout}")
                    print(f"psql errors: {result.stderr}")
                    raise Exception(f"psql failed with return code {result.returncode}")
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
            
            print("Database and users created successfully")
                    
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to create database and users: {e}")
    
    def create_schemas(self, schema_names: List[str] = None) -> None:
        """Create the specified schemas.
        
        Args:
            schema_names: List of schema names to create. Defaults to ['demo', 'app']
            
        Raises:
            SQLAlchemyError: If schema creation fails
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")
        
        if schema_names is None:
            schema_names = ['demo', 'app']
        
        try:
            with self.engine.connect() as conn:
                for schema_name in schema_names:
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                    conn.commit()
                    print(f"Created schema: {schema_name}")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to create schemas: {e}")
    
    def enable_extensions(self) -> None:
        """Enable required PostgreSQL extensions.
        
        Enables extensions needed for JSONB GIN indexes and other features.
        
        Raises:
            SQLAlchemyError: If extension enabling fails
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")
        
        # Skip if not PostgreSQL
        if not self.database_url.startswith('postgresql://'):
            return
        
        extensions = [
            'btree_gin',  # For GIN indexes on JSONB
        ]
        
        try:
            with self.engine.connect() as conn:
                for extension in extensions:
                    conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {extension}"))
                    conn.commit()
                    print(f"Enabled extension: {extension}")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to enable extensions: {e}")
    
    def _create_gin_indexes_for_schema(self, conn, schema_name: Optional[str] = None) -> None:
        """Create GIN indexes for JSONB columns in the specified schema (PostgreSQL only)."""
        if not self.database_url.startswith('postgresql://'):
            return
        
        try:
            # First check if the columns are actually JSONB (new schema) or JSON (old schema)
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'preferences'
                AND table_schema = CURRENT_SCHEMA()
            """))
            col_info = result.fetchone()
            
            if not col_info:
                print(f"Warning: Could not find preferences column to check type")
                return
                
            column_type = col_info[1]
            
            if column_type == 'jsonb':
                # Use jsonb_path_ops for JSONB columns
                gin_indexes = [
                    "CREATE INDEX IF NOT EXISTS ix_users_preferences_gin ON users USING gin (preferences jsonb_path_ops)",
                    "CREATE INDEX IF NOT EXISTS ix_content_items_metadata_gin ON content_items USING gin (item_metadata jsonb_path_ops)",
                    "CREATE INDEX IF NOT EXISTS ix_content_items_tags_gin ON content_items USING gin (tags jsonb_path_ops)",
                    "CREATE INDEX IF NOT EXISTS ix_user_interactions_metadata_gin ON user_interactions USING gin (interaction_metadata jsonb_path_ops)",
                    "CREATE INDEX IF NOT EXISTS ix_recommendations_metadata_gin ON recommendations USING gin (rec_metadata jsonb_path_ops)",
                    "CREATE INDEX IF NOT EXISTS ix_generation_jobs_parameters_gin ON generation_jobs USING gin (parameters jsonb_path_ops)",
                ]
            elif column_type == 'json':
                # For JSON columns, we need to use a custom operator class or skip GIN indexes
                # JSON columns don't have default GIN support, so we'll skip them
                print(f"Skipping GIN indexes for JSON columns (use JSONB for better performance)")
                return
            else:
                print(f"Warning: Unexpected column type '{column_type}' for JSON/JSONB columns")
                return
            
            for index_sql in gin_indexes:
                conn.execute(text(index_sql))
                
            print(f"GIN indexes created for schema: {schema_name or 'default'} (column type: {column_type})")
        except Exception as e:
            print(f"Warning: Could not create GIN indexes: {e}")
    
    def create_tables(self, schema_name: Optional[str] = None) -> None:
        """Create all database tables based on the schema.
        
        Args:
            schema_name: Optional schema name to create tables in. If None, uses default schema.
            
        Raises:
            SQLAlchemyError: If table creation fails
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")
        
        try:
            if schema_name and self.database_url.startswith('postgresql://'):
                # PostgreSQL: Execute raw SQL to create tables in the specific schema
                with self.engine.connect() as conn:
                    # Set the search path to the target schema
                    conn.execute(text(f"SET search_path TO {schema_name}, public"))
                    conn.commit()
                    
                    # Now create all tables (they will be created in the schema)
                    Base.metadata.create_all(conn)
                    
                    # Commit the table creation first
                    conn.commit()
                    
                    # Create GIN indexes for JSONB columns (PostgreSQL only) in a separate transaction
                    try:
                        self._create_gin_indexes_for_schema(conn, schema_name)
                        conn.commit()
                    except Exception as e:
                        # If GIN index creation fails, rollback and continue without them
                        conn.rollback()
                        print(f"Warning: GIN index creation failed, continuing without them: {e}")
                    
                    # Reset search path in a new transaction
                    try:
                        conn.execute(text("SET search_path TO public"))
                        conn.commit()
                    except Exception:
                        # If we can't reset search path, that's ok
                        pass
                    
                print(f"Database tables created successfully in schema: {schema_name}")
            else:
                # SQLite or default: Create tables in default schema
                Base.metadata.create_all(self.engine)
                
                # For PostgreSQL without schemas, still create GIN indexes
                if self.database_url.startswith('postgresql://'):
                    with self.engine.connect() as conn:
                        try:
                            self._create_gin_indexes_for_schema(conn)
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            print(f"Warning: GIN index creation failed, continuing without them: {e}")
                
                if schema_name:
                    print(f"Database tables created successfully (SQLite doesn't support schemas)")
                else:
                    print("Database tables created successfully")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to create tables: {e}")
    
    def drop_tables(self, schema_name: Optional[str] = None) -> None:
        """Drop all database tables.
        
        Warning: This will delete all data in the database.
        
        Args:
            schema_name: Optional schema name to drop tables from. If None, drops from all schemas.
        
        Raises:
            SQLAlchemyError: If table dropping fails
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")
        
        try:
            if schema_name and self.database_url.startswith('postgresql://'):
                # PostgreSQL: Drop tables from specific schema
                with self.engine.connect() as conn:
                    # Set the search path to the target schema
                    conn.execute(text(f"SET search_path TO {schema_name}, public"))
                    conn.commit()
                    
                    # Drop all tables
                    Base.metadata.drop_all(conn)
                    
                    # Reset search path
                    conn.execute(text("SET search_path TO public"))
                    conn.commit()
                    
                print(f"Database tables dropped successfully from schema: {schema_name}")
            elif self.database_url.startswith('postgresql://'):
                # PostgreSQL: Drop tables from all schemas
                with self.engine.connect() as conn:
                    for schema in ['demo', 'app', 'public']:
                        try:
                            conn.execute(text(f"SET search_path TO {schema}, public"))
                            conn.commit()
                            Base.metadata.drop_all(conn)
                            print(f"Dropped tables from schema: {schema}")
                        except Exception as e:
                            print(f"Warning: Could not drop tables from {schema}: {e}")
                    
                    # Reset search path
                    conn.execute(text("SET search_path TO public"))
                    conn.commit()
                    
                print("Database tables dropped successfully from all schemas")
            else:
                # SQLite: Just drop all tables (no schema support)
                Base.metadata.drop_all(self.engine)
                if schema_name:
                    print(f"Database tables dropped successfully (SQLite doesn't support schemas)")
                else:
                    print("Database tables dropped successfully")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to drop tables: {e}")
    
    def seed_from_tsv_directory(self, tsv_directory: Path, schema_name: Optional[str] = None) -> None:
        """Seed database with data from TSV files in the specified directory.
        
        Args:
            tsv_directory: Path to directory containing TSV files
            schema_name: Optional schema name to seed tables in
            
        The method expects TSV files named after the model classes in snake_case plural form:
        - User -> users.tsv
        - ContentItem -> content_items1.tsv
        - UserInteraction -> user_interactions.tsv
        - Recommendation -> recommendations.tsv
        - GenerationJob -> generation_jobs1.tsv
        
        Raises:
            SQLAlchemyError: If seeding fails
            ValueError: If session factory not initialized
        """
        if not self.session_factory:
            raise ValueError("Session factory not initialized. Call create_engine_and_session() first.")
        
        if not tsv_directory.exists():
            raise ValueError(f"TSV directory does not exist: {tsv_directory}")
        
        if not tsv_directory.is_dir():
            raise ValueError(f"Path is not a directory: {tsv_directory}")
        
        # Define the model classes and their expected filenames
        model_classes = [User, ContentItem, UserInteraction, Recommendation, GenerationJob]
        expected_files = {}
        missing_files = []
        
        for model_class in model_classes:
            filename = _class_name_to_snake_case(model_class.__name__) + '.tsv'
            expected_files[filename] = model_class
            
            file_path = tsv_directory / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        # Log warnings for missing files
        if missing_files:
            logging.warning(f"Missing TSV files for seeding: {', '.join(missing_files)}")
        
        # Check for unrecognized files
        tsv_files_in_dir = list(tsv_directory.glob('*.tsv'))
        unrecognized_files = []
        
        for file_path in tsv_files_in_dir:
            if file_path.name not in expected_files:
                unrecognized_files.append(file_path.name)
        
        if unrecognized_files:
            logging.warning(f"Unrecognized files in TSV directory: {', '.join(unrecognized_files)}")
        
        # Import the seeding utility (avoid circular imports)
        try:
            import sys
            
            # Try to find the test directory relative to this file
            current_file = Path(__file__).resolve()
            project_root = current_file.parents[2]  # Go up from genonaut/db/init.py
            test_utils_path = project_root / 'test'
            
            if test_utils_path.exists():
                if str(test_utils_path) not in sys.path:
                    sys.path.insert(0, str(test_utils_path))
                
                from utils import seed_database_from_tsv
            else:
                # Fallback: try to import from the current working directory
                import os
                cwd_test_path = Path(os.getcwd()) / 'test'
                if cwd_test_path.exists():
                    if str(cwd_test_path) not in sys.path:
                        sys.path.insert(0, str(cwd_test_path))
                    from utils import seed_database_from_tsv
                else:
                    raise ImportError(f"Cannot find test utilities. Tried: {test_utils_path}, {cwd_test_path}")
            
            # Seed the database only with available files
            session = self.session_factory()
            try:
                # Only seed if we have at least one expected file
                available_files = [f for f in expected_files.keys() if (tsv_directory / f).exists()]
                if available_files:
                    seed_database_from_tsv(session, str(tsv_directory), schema_name)
                    schema_info = f" in schema '{schema_name}'" if schema_name else ""
                    print(f"Database seeded successfully from {tsv_directory}{schema_info} (processed {len(available_files)} files)")
                else:
                    logging.warning("No expected TSV files found for seeding")
            finally:
                session.close()
                
        except ImportError as e:
            raise SQLAlchemyError(f"Failed to import seeding utilities: {e}")
        except Exception as e:
            raise SQLAlchemyError(f"Failed to seed database: {e}")


def initialize_database(database_url: Optional[str] = None, 
                       create_db: bool = True,
                       drop_existing: bool = False,
                       app_seed_data_path: Optional[Path] = None,
                       demo_seed_data_path: Optional[Path] = None,
                       schema_name: Optional[str] = None) -> None:
    """Initialize the database with schema and optional data seeding.
    
    Args:
        database_url: PostgreSQL connection URL
        create_db: Whether to create the database if it doesn't exist
        drop_existing: Whether to drop existing tables before creating new ones
        app_seed_data_path: Optional path to directory containing TSV files for seeding 'app' schema
        demo_seed_data_path: Optional path to directory containing TSV files for seeding 'demo' schema
        schema_name: Optional specific schema name for table creation (for testing)
        
    Raises:
        SQLAlchemyError: If initialization fails
    """
    initializer = DatabaseInitializer(database_url)
    
    if create_db:
        # Only create database and users for PostgreSQL
        if database_url and database_url.startswith('postgresql://'):
            initializer.create_database_and_users()
        elif not database_url and not os.getenv('DATABASE_URL', '').startswith('sqlite://'):
            # Environment suggests PostgreSQL setup
            initializer.create_database_and_users()
    
    initializer.create_engine_and_session()
    
    # Enable required extensions for JSONB features
    initializer.enable_extensions()
    
    # Create schemas if not in test mode and using PostgreSQL
    if not schema_name:
        # Check if using PostgreSQL (schemas supported)
        is_postgresql = (database_url and database_url.startswith('postgresql://')) or \
                       (not database_url and not os.getenv('DATABASE_URL', '').startswith('sqlite://'))
        
        if is_postgresql:
            initializer.create_schemas(['demo', 'app'])
            
            if drop_existing:
                initializer.drop_tables()
            
            # Create tables in both schemas
            initializer.create_tables('demo')
            initializer.create_tables('app')
            
            # Seed the schemas
            if app_seed_data_path:
                initializer.seed_from_tsv_directory(app_seed_data_path, 'app')
            
            if demo_seed_data_path:
                initializer.seed_from_tsv_directory(demo_seed_data_path, 'demo')
        else:
            # SQLite - just create tables without schemas
            if drop_existing:
                initializer.drop_tables()
            
            initializer.create_tables()
            
            # Seed with app_seed_data_path if provided (ignore demo for SQLite)
            if app_seed_data_path:
                initializer.seed_from_tsv_directory(app_seed_data_path)
    else:
        # Test mode - create schema and tables in specified schema (PostgreSQL only)
        is_postgresql = (database_url and database_url.startswith('postgresql://')) or \
                       (not database_url and not os.getenv('DATABASE_URL', '').startswith('sqlite://'))
        
        if is_postgresql:
            initializer.create_schemas([schema_name])
            
            if drop_existing:
                initializer.drop_tables()
            
            initializer.create_tables(schema_name)
            
            # Seed with app_seed_data_path if provided
            if app_seed_data_path:
                initializer.seed_from_tsv_directory(app_seed_data_path, schema_name)
        else:
            # SQLite test mode - just create tables
            if drop_existing:
                initializer.drop_tables()
            
            initializer.create_tables()
            
            # Seed with app_seed_data_path if provided
            if app_seed_data_path:
                initializer.seed_from_tsv_directory(app_seed_data_path)
    
    print("Database initialization completed successfully")


if __name__ == "__main__":
    # Example usage
    app_seed_path = Path("io/input/init/rdbms/")
    demo_seed_path = Path("docs/demo/demo_app/init/rdbms")
    
    initialize_database(
        create_db=True,
        drop_existing=False,
        app_seed_data_path=app_seed_path if app_seed_path.exists() else None,
        demo_seed_data_path=demo_seed_path if demo_seed_path.exists() else None
    )
