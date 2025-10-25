"""Database initialization and seeding module for Genonaut.

This module provides functionality to create the PostgreSQL database schema
and seed it with initial data for development and testing purposes.
"""

import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, Session

from alembic import command
from alembic.config import Config

from genonaut.db.schema import Base, User, ContentItem, UserInteraction, Recommendation, GenerationJob, ContentItemAuto, ensure_pg_trgm_extension, ensure_trigram_indexes
from genonaut.db.schema_extensions import install_extensions


from genonaut.db.utils import get_database_url, resolve_database_environment


# Load environment variables from .env file in the env/ directory
# Path from genonaut/db/init.py -> project_root/env/.env
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env_path = PROJECT_ROOT / "env" / ".env"
load_dotenv(dotenv_path=env_path)

CONFIG_PATH = PROJECT_ROOT / "config.json"

logger = logging.getLogger(__name__)


def load_project_config() -> Dict[str, Any]:
    """Load repository-level configuration from config.json.

    Returns:
        Parsed JSON configuration dictionary. Returns an empty dictionary when
        the config file is absent or invalid.
    """

    if not CONFIG_PATH.exists():
        return {}

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load config.json: %s", exc)
        return {}


def resolve_seed_path(config: Dict[str, Any], environment: str) -> Optional[Path]:
    """Resolve the seed-data directory path for the requested database."""

    seed_section = config.get("seed_data", {}) if isinstance(config, dict) else {}

    # Backwards compatibility: older config files used "seed_data_premade"
    if not seed_section and isinstance(config, dict):
        seed_section = config.get("seed_data_premade", {})

    env_key_map = {
        "dev": "main",
        "demo": "demo",
        "test": "test",
    }
    seed_key = env_key_map.get(environment, "main")
    raw_path = seed_section.get(seed_key)

    if raw_path is None and environment == "test":
        # Fall back to demo seed data when dedicated test fixtures are absent
        raw_path = seed_section.get("demo")

    candidate: Optional[Path] = None
    if raw_path:
        candidate = (PROJECT_ROOT / raw_path).resolve()
        if not candidate.exists():
            logger.warning("Seed path %s does not exist", candidate)
            candidate = None

    if environment == "test":
        fallback_dirs = [
            (PROJECT_ROOT / "test" / "db" / "input" / "rdbms_init").resolve(),
        ]

        candidate_has_data = bool(candidate and any(candidate.glob("*.tsv")))

        for default_test_seed in fallback_dirs:
            if not default_test_seed.exists():
                continue

            default_has_data = any(default_test_seed.glob("*.tsv"))

            if candidate is None:
                if default_has_data:
                    return default_test_seed
                continue

            if candidate.resolve() == default_test_seed:
                return candidate

            if default_has_data and not candidate_has_data:
                logger.warning(
                    "Configured seed path %s has no TSV data; using fallback %s",
                    candidate,
                    default_test_seed,
                )
                return default_test_seed

    return candidate


def _is_truthy(value: Optional[str]) -> bool:
    """Lightweight helper to interpret environment flags."""

    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_alembic_upgrade(database_url: str, target: str = "head") -> None:
    """Run Alembic upgrade to head for the provided database URL."""

    alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    os.environ["ALEMBIC_SQLALCHEMY_URL"] = database_url
    command.upgrade(alembic_cfg, target)


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
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        """Initialize the database initializer.
        
        Args:
            database_url: PostgreSQL connection URL. If None, will use environment variable.
            environment: Explicit environment identifier (``dev``, ``demo``, ``test``).
        """
        self.environment = resolve_database_environment(environment=environment)
        self.is_test = self.environment == "test"
        self.database_url = database_url or get_database_url(environment=self.environment)
        try:
            self._url = make_url(self.database_url)
            self.database_name = self._url.database
        except Exception:
            self._url = None
            self.database_name = None
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

        if self.environment == "test":
            database_name = self.database_name or os.getenv('DB_NAME_TEST', 'genonaut_test')
        elif self.environment == "demo":
            database_name = self.database_name or os.getenv('DB_NAME_DEMO', 'genonaut_demo')
        else:
            database_name = self.database_name or os.getenv('DB_NAME', 'genonaut')
        if not database_name:
            raise ValueError("Database name could not be determined for initialization")
        sql_content = sql_content.replace('{{ DB_NAME }}', database_name)
        
        # Create connection URL to 'postgres' database for admin operations
        # Prefer credentials embedded in the configured URL; fall back to explicit env overrides
        postgres_url: Optional[str] = None
        psql_user: Optional[str] = None
        psql_password: Optional[str] = None
        psql_host: Optional[str] = None
        psql_port: Optional[str] = None
        if self._url and self._url.username and self._url.password:
            postgres_url = self._url.set(database='postgres').render_as_string(hide_password=False)
            psql_user = self._url.username
            psql_password = self._url.password
            psql_host = self._url.host or os.getenv('DB_HOST', 'localhost')
            psql_port = str(self._url.port or os.getenv('DB_PORT', '5432'))
        else:
            fallback_user = os.getenv('DB_USER_FOR_INIT', 'postgres')
            fallback_password = os.getenv('DB_PASSWORD_FOR_INIT')

            if fallback_password:
                host = self._url.host if self._url and self._url.host else os.getenv('DB_HOST', 'localhost')
                port = self._url.port if self._url and self._url.port else os.getenv('DB_PORT', '5432')
                postgres_url = f"postgresql://{fallback_user}:{fallback_password}@{host}:{port}/postgres"
                psql_user = fallback_user
                psql_password = fallback_password
                psql_host = host
                psql_port = str(port)
            elif self.database_url:
                postgres_url = '/'.join(self.database_url.split('/')[:-1]) + '/postgres'
                psql_user = self._url.username if self._url and self._url.username else fallback_user
                psql_password = self._url.password if self._url and self._url.password else None
                psql_host = self._url.host or os.getenv('DB_HOST', 'localhost') if self._url else os.getenv('DB_HOST', 'localhost')
                psql_port = str(self._url.port) if self._url and self._url.port else os.getenv('DB_PORT', '5432')

        try:
            if not postgres_url:
                raise ValueError("Unable to determine connection URL for postgres maintenance database")

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
                effective_user = psql_user or os.getenv('DB_USER_FOR_INIT', 'postgres')
                host = psql_host or os.getenv('DB_HOST', 'localhost')
                port = psql_port or os.getenv('DB_PORT', '5432')

                # Execute SQL using psql
                psql_cmd = [
                    'psql',
                    '-h', host,
                    '-p', port,
                    '-U', effective_user,
                    '-d', 'postgres',
                    '-f', temp_file_path
                ]

                # Set password via environment variable
                env = os.environ.copy()
                if psql_password:
                    env['PGPASSWORD'] = psql_password
                elif 'PGPASSWORD' in env:
                    env.pop('PGPASSWORD')

                result = subprocess.run(psql_cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"Database '{database_name}' and users created successfully")
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
            
            print(f"Database '{database_name}' and users created successfully")
                    
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to create database and users: {e}")
    
    def create_schemas(self, schema_names: Optional[List[str]] = None) -> None:
        """Create the specified schemas.
        
        Args:
            schema_names: List of schema names to create.
            
        Raises:
            SQLAlchemyError: If schema creation fails
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")
        
        if not schema_names:
            return
        
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

        Uses the centralized extension management system to ensure all required
        extensions are installed, including those needed for GIN and GiST indexes.

        Raises:
            SQLAlchemyError: If extension enabling fails
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")

        # Skip if not PostgreSQL
        if not self.database_url.startswith('postgresql://'):
            return

        try:
            # Use the centralized extension installation system
            success = install_extensions(self.database_url)
            if not success:
                raise SQLAlchemyError("Failed to install required PostgreSQL extensions")

            # Additional safety check for pg_trgm
            ensure_pg_trgm_extension(self.engine)

        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to enable extensions: {e}")
        except Exception as e:
            raise SQLAlchemyError(f"Unexpected error enabling extensions: {e}")
    
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
                    # Set the search path to the target schema (transaction scoped)
                    conn.execute(text(f"SET search_path TO {schema_name}, public"))

                    # Now create all tables (they will be created in the schema)
                    try:
                        Base.metadata.create_all(conn)
                        conn.commit()
                    except Exception:
                        conn.rollback()
                        raise
                    
                    # Create GIN indexes for JSONB columns (PostgreSQL only) in a separate transaction
                    try:
                        conn.execute(text(f"SET search_path TO {schema_name}, public"))
                        self._create_gin_indexes_for_schema(conn, schema_name)
                        conn.commit()
                    except Exception as e:
                        # If GIN index creation fails, rollback and continue without them
                        conn.rollback()
                        print(f"Warning: GIN index creation failed, continuing without them: {e}")

                    # Create trigram indexes for text similarity (PostgreSQL only)
                    try:
                        conn.execute(text(f"SET search_path TO {schema_name}, public"))
                        ensure_trigram_indexes(self.engine)
                        conn.commit()
                    except Exception as e:
                        # If trigram index creation fails, rollback and continue without them
                        conn.rollback()
                        print(f"Warning: Trigram index creation failed, continuing without them: {e}")
                    
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
                
                # For PostgreSQL without schemas, still create GIN indexes and trigram indexes
                if self.database_url.startswith('postgresql://'):
                    with self.engine.connect() as conn:
                        try:
                            self._create_gin_indexes_for_schema(conn)
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            print(f"Warning: GIN index creation failed, continuing without them: {e}")

                        try:
                            ensure_trigram_indexes(self.engine)
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            print(f"Warning: Trigram index creation failed, continuing without them: {e}")
                
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
            UnsafeDatabaseOperationError: If attempting to drop tables from a non-test database
        """
        if not self.engine:
            raise ValueError("Engine not initialized. Call create_engine_and_session() first.")

        # SAFETY CHECK: Only allow dropping tables in test databases
        from genonaut.db.safety import validate_test_database_url
        validate_test_database_url(self.database_url)

        try:
            if schema_name and self.database_url.startswith('postgresql://'):
                # PostgreSQL: Drop tables from specific schema
                with self.engine.connect() as conn:
                    self._drop_schema_tables(conn, schema_name)
                    print(f"Database tables dropped successfully from schema: {schema_name}")
            elif self.database_url.startswith('postgresql://'):
                # PostgreSQL: Drop tables from public schema (and legacy schemas for cleanup)
                legacy_schemas = ['app', 'demo']
                with self.engine.connect() as conn:
                    for schema in ['public'] + legacy_schemas:
                        try:
                            self._drop_schema_tables(conn, schema)
                            print(f"Dropped tables from schema: {schema}")
                        except Exception as e:
                            print(f"Warning: Could not drop tables from {schema}: {e}")
                    
                    # Reset search path (safe guard after legacy attempts)
                    try:
                        conn.execute(text("SET search_path TO public"))
                        conn.commit()
                    except Exception:
                        conn.rollback()
                    
                print("Database tables dropped successfully from public schema")
            else:
                # SQLite: Just drop all tables (no schema support)
                Base.metadata.drop_all(self.engine)
                if schema_name:
                    print(f"Database tables dropped successfully (SQLite doesn't support schemas)")
                else:
                    print("Database tables dropped successfully")
        except SQLAlchemyError as e:
            raise SQLAlchemyError(f"Failed to drop tables: {e}")

    def _drop_schema_tables(self, conn, schema: str) -> None:
        """Drop tables for the provided schema, tolerating missing tables/schemas."""

        if not schema:
            raise ValueError("Schema name must be provided")

        try:
            conn.execute(text(f"SET search_path TO {schema}, public"))
        except Exception as exc:
            conn.rollback()
            raise exc

        try:
            Base.metadata.drop_all(conn)
            conn.commit()
        except Exception:
            conn.rollback()

            inspector = inspect(conn)
            existing_tables = inspector.get_table_names(schema=schema)

            if not existing_tables:
                raise RuntimeError(f"Schema '{schema}' does not exist or contains no tables to drop")

            for table_name in existing_tables:
                qualified = f'"{schema}"."{table_name}"'
                conn.execute(text(f"DROP TABLE IF EXISTS {qualified} CASCADE"))

            conn.commit()
        finally:
            try:
                conn.execute(text("SET search_path TO public"))
                conn.commit()
            except Exception:
                conn.rollback()

    def ensure_legacy_full_text_indexes(self) -> None:
        """Ensure legacy full-text indexes exist before running migrations."""

        if not self.engine or not self.database_url.startswith('postgresql://'):
            return

        statements = [
            (
                "content_items",
                """
                CREATE INDEX IF NOT EXISTS ix_content_items_title_fts
                ON content_items
                USING GIN (to_tsvector('english', coalesce(title, '')))
                """,
            ),
            (
                "generation_jobs",
                """
                CREATE INDEX IF NOT EXISTS ix_generation_jobs_prompt_fts
                ON generation_jobs
                USING GIN (to_tsvector('english', coalesce(prompt, '')))
                """,
            ),
        ]

        with self.engine.connect() as conn:
            for table_name, statement in statements:
                exists_query = text(
                    "SELECT to_regclass(:table_name) IS NOT NULL"
                )
                table_exists = conn.execute(
                    exists_query, {"table_name": f"public.{table_name}"}
                ).scalar()
                if table_exists:
                    logger.info(
                        "Creating legacy FTS index for table %s if missing", table_name
                    )
                    conn.execute(text(statement))
            conn.commit()

    def drop_new_full_text_indexes(self) -> None:
        """Drop the newer FTS indexes so migrations can recreate them."""

        if not self.engine or not self.database_url.startswith('postgresql://'):
            return

        statements = [
            "DROP INDEX IF EXISTS ci_title_fts_idx",
            "DROP INDEX IF EXISTS gj_prompt_fts_idx",
        ]

        with self.engine.connect() as conn:
            for statement in statements:
                logger.info("Dropping FTS index with statement: %s", statement.strip())
                conn.execute(text(statement))
            conn.commit()

    def truncate_tables(self, schema_name: Optional[str] = None) -> None:
        """Truncate tables while preserving schema artifacts like indexes.

        Args:
            schema_name: Optional schema to target; defaults to the primary schema.

        Raises:
            SQLAlchemyError: When truncation fails.
            ValueError: When the session factory is uninitialized.
            UnsafeDatabaseOperationError: If attempting to truncate tables from a non-test database
        """

        if not self.session_factory:
            raise ValueError("Session factory not initialized")

        # SAFETY CHECK: Only allow truncating tables in test databases
        from genonaut.db.safety import validate_test_database_url
        validate_test_database_url(self.database_url)

        session = self.session_factory()
        try:
            model_order = [GenerationJob, Recommendation, UserInteraction, ContentItem, User]

            if self.database_url.startswith('postgresql://'):
                for model in model_order:
                    table_name = model.__tablename__
                    if schema_name:
                        table_name = f"{schema_name}.{table_name}"
                    session.execute(
                        text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
                    )
                session.commit()
            else:
                for model in reversed(model_order):
                    session.query(model).delete()
                session.commit()
        except Exception as exc:
            session.rollback()
            raise SQLAlchemyError(f"Failed to truncate tables: {exc}")
        finally:
            session.close()

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
        model_classes = [User, ContentItem, ContentItemAuto, UserInteraction, Recommendation, GenerationJob]
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
                from db import utils
            
            # Seed the database only with available files
            session = self.session_factory()
            try:
                # Only seed if we have at least one expected file
                available_files = [f for f in expected_files.keys() if (tsv_directory / f).exists()]
                if available_files:
                    utils.seed_database_from_tsv(session, str(tsv_directory), schema_name, self.database_name)
                    schema_info = f" in schema '{schema_name}'" if schema_name else ""
                    print(f"Database seeded successfully from {tsv_directory}{schema_info} (processed {len(available_files)} files)")
                else:
                    logging.warning("No expected TSV files found for seeding")

                # Fallback mechanism for tables not covered by the model-based seeding
                all_table_names = Base.metadata.tables.keys()
                table_to_model_map = {table.name: mapper.class_ for mapper in Base.registry.mappers for table in mapper.tables}

                unrecognized_and_matching_tsvs = []
                for tsv_file in unrecognized_files:
                    table_name = tsv_file.replace('.tsv', '')
                    if table_name in all_table_names:
                        unrecognized_and_matching_tsvs.append(tsv_file)

                if unrecognized_and_matching_tsvs:
                    print(f"Found additional TSV files matching table names: {unrecognized_and_matching_tsvs}")

                    # Fetch users for creator_id lookup
                    users = session.query(User).all()
                    username_to_id = {user.username: user.id for user in users}

                    for tsv_file in unrecognized_and_matching_tsvs:
                        table_name = tsv_file.replace('.tsv', '')
                        file_path = tsv_directory / tsv_file
                        # Dynamically load data into the table
                        try:
                            data = utils.load_tsv_data(str(file_path))
                            if data:
                                # Handle creator_id lookup
                                if 'creator_username' in data[0]:
                                    for row in data:
                                        username = row.pop('creator_username', None)
                                        if username in username_to_id:
                                            row['creator_id'] = username_to_id[username]
                                        else:
                                            logging.warning(f"User '{username}' not found for data in '{tsv_file}'. Skipping row.")
                                            data.remove(row)

                                model_class = table_to_model_map.get(table_name)
                                if model_class:
                                    session.bulk_insert_mappings(model_class, data)
                                    session.commit()
                                    print(f"Successfully seeded table '{table_name}' from '{tsv_file}'")
                                else:
                                    logging.error(f"Could not find model for table '{table_name}'. Skipping...")

                        except Exception as e:
                            logging.error(f"Failed to seed table '{table_name}' from '{tsv_file}': {e}")
                            session.rollback()

            finally:
                session.close()
                
        except ImportError as e:
            raise SQLAlchemyError(f"Failed to import seeding utilities: {e}")
        except Exception as e:
            raise SQLAlchemyError(f"Failed to seed database: {e}")


def reseed_demo(force: bool = False) -> None:
    """Re-seed the demo database by truncating all tables and re-running the seeding process.
    
    Args:
        force: If False, prompts user for confirmation. If True, proceeds without prompting.
        
    Raises:
        SQLAlchemyError: If re-seeding fails.
        SystemExit: If user chooses not to proceed when prompted.
    """
    if not force:
        response = input("Are you sure you want to truncate all tables and re-seed the demo database? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return
    
    print("Re-seeding demo database...")
    
    # Get demo database configuration
    initializer = DatabaseInitializer(environment="demo")
    initializer.create_engine_and_session()

    # SAFETY CHECK: Only allow truncating test databases
    # Demo databases should use init-demo to recreate from scratch instead
    from genonaut.db.safety import validate_test_database_url
    validate_test_database_url(initializer.database_url)

    # Get seed data path
    config = load_project_config()
    seed_path = resolve_seed_path(config, "demo")

    if not seed_path:
        raise ValueError("Could not resolve seed data path for demo database")

    # Truncate all tables (preserve schema)
    model_classes = [GenerationJob, Recommendation, UserInteraction, ContentItem, User]  # Order matters for FK constraints

    if not initializer.session_factory:
        raise ValueError("Session factory not initialized")

    session = initializer.session_factory()
    try:
        # Truncate tables in reverse dependency order
        for model_class in model_classes:
            table_name = model_class.__tablename__
            session.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
        session.commit()
        print("All tables truncated successfully")
        
        # Re-seed with TSV data
        initializer.seed_from_tsv_directory(seed_path)
        print("Demo database re-seeded successfully")
        
    except Exception as e:
        session.rollback()
        raise SQLAlchemyError(f"Failed to re-seed demo database: {e}")
    finally:
        session.close()


def initialize_database(
    database_url: Optional[str] = None,
    create_db: bool = True,
    drop_existing: bool = False,
    schema_name: Optional[str] = None,
    seed_data_path: Optional[Path] = None,
    environment: Optional[str] = None,
    auto_seed: bool = True,
) -> None:
    """Initialize the database with schema and optional data seeding.

    Args:
        database_url: Database connection URL. Uses environment configuration when
            omitted.
        create_db: Whether to create the database if it doesn't exist.
        drop_existing: Whether to drop existing tables before creating new ones.
        schema_name: Optional schema name for table creation (primarily for tests).
        seed_data_path: Optional directory containing TSV files for seeding data.
        environment: Explicit environment identifier (``dev``, ``demo``, ``test``).
        auto_seed: Whether to load seed TSV data when a seed path is available.

    Raises:
        SQLAlchemyError: If initialization fails.
        RuntimeError: If drop_existing is True but database is not empty.
    """

    # Only pass environment if it's explicitly set (not None)
    init_kwargs = {}
    if environment is not None:
        init_kwargs['environment'] = environment

    initializer = DatabaseInitializer(database_url, **init_kwargs)

    # SAFETY CHECK: Prevent drop_existing on non-empty databases
    # This prevents accidental data loss from running init commands on populated databases
    # Exception: Test databases are allowed to drop existing tables since they're meant to be reset frequently
    if drop_existing and not initializer.is_test:
        # Create a temporary engine to check if database has tables
        temp_engine = None
        try:
            temp_engine = create_engine(initializer.database_url, pool_pre_ping=True)
            inspector = inspect(temp_engine)
            existing_tables = inspector.get_table_names()

            if existing_tables:
                table_list = ', '.join(existing_tables[:5])
                if len(existing_tables) > 5:
                    table_list += f', ... ({len(existing_tables)} total)'

                raise RuntimeError(
                    f"Safety check failed: Cannot initialize with --drop-existing on non-empty database.\n"
                    f"Database '{initializer.database_name}' already contains {len(existing_tables)} table(s): {table_list}\n"
                    f"\n"
                    f"This safety check prevents accidental data loss.\n"
                    f"\n"
                    f"If you really want to reinitialize this database:\n"
                    f"  1. For test databases: Use 'make reset-db-*' commands instead\n"
                    f"  2. For demo/dev databases: Manually drop the database first, or use reset commands\n"
                    f"  3. Alternatively: Remove the database and recreate it from scratch\n"
                )
        except RuntimeError:
            # Re-raise our safety check error
            raise
        except Exception as e:
            # If we can't check (e.g., database doesn't exist yet), that's fine - let it proceed
            logger.debug(f"Could not check for existing tables (this is OK if database doesn't exist yet): {e}")
        finally:
            if temp_engine:
                temp_engine.dispose()

    target_url = initializer.database_url or ""
    is_postgresql = target_url.startswith('postgresql://')
    is_sqlite = target_url.startswith('sqlite://')

    if create_db:
        if is_postgresql:
            initializer.create_database_and_users()
        elif not is_sqlite:
            # Non-SQLite setups rely on admin role creation as well
            initializer.create_database_and_users()

    initializer.create_engine_and_session()
    initializer.enable_extensions()

    resolved_seed_path: Optional[Path] = None
    candidate_path: Optional[Path] = None

    if seed_data_path is not None:
        candidate_path = Path(seed_data_path)
    elif schema_name is None and not is_sqlite:
        candidate_path = resolve_seed_path(
            load_project_config(),
            initializer.environment,
        )

    if candidate_path:
        if candidate_path.exists() and candidate_path.is_dir():
            resolved_seed_path = candidate_path
        else:
            logger.warning("Seed data path %s is not a valid directory", candidate_path)

    should_auto_seed = bool(resolved_seed_path and auto_seed)

    if schema_name:
        if is_postgresql:
            initializer.create_schemas([schema_name])
        if drop_existing:
            initializer.drop_tables(schema_name)
        initializer.create_tables(schema_name)
        if should_auto_seed:
            initializer.seed_from_tsv_directory(resolved_seed_path, schema_name)
    else:
        if drop_existing:
            if is_postgresql:
                with initializer.engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    conn.commit()
            initializer.drop_tables()
        elif initializer.is_test:
            if is_postgresql:
                initializer.drop_tables()
                with initializer.engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    conn.commit()
            else:
                initializer.drop_tables()

        if is_postgresql:
            try:
                _run_alembic_upgrade(initializer.database_url)
            except ProgrammingError as exc:
                message = str(exc)
                if "ix_content_items_title_fts" in message or "ix_generation_jobs_prompt_fts" in message:
                    initializer.drop_new_full_text_indexes()
                    initializer.ensure_legacy_full_text_indexes()
                    _run_alembic_upgrade(initializer.database_url)
                elif "ci_title_fts_idx" in message or "gj_prompt_fts_idx" in message:
                    initializer.drop_new_full_text_indexes()
                    _run_alembic_upgrade(initializer.database_url)
                else:
                    raise
        else:
            initializer.create_tables()

        if initializer.is_test and should_auto_seed:
            try:
                initializer.truncate_tables()
            except SQLAlchemyError as exc:
                logger.warning("Failed to truncate tables before test seeding: %s", exc)

        if should_auto_seed:
            initializer.seed_from_tsv_directory(resolved_seed_path)

    print("Database initialization completed successfully")


if __name__ == "__main__":
    config = load_project_config()
    environment = resolve_database_environment()
    seed_path = resolve_seed_path(config, environment)

    initialize_database(
        create_db=True,
        drop_existing=False,
        seed_data_path=seed_path,
        environment=environment,
    )
