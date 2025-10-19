"""PostgreSQL test database fixtures and utilities.

This module provides fixtures and helper functions for tests that use the
PostgreSQL test database (genonaut_test) .

The PostgreSQL test database must be initialized before running tests:
    make init-test

Usage:
    import pytest
    from test.db.postgres_fixtures import postgres_session

    def test_something(postgres_session):
        # Use postgres_session for database operations
        user = User(username="test")
        postgres_session.add(user)
        postgres_session.commit()
"""

import os
from typing import Generator
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from genonaut.db.schema import Base
from genonaut.api.config import get_settings


def get_postgres_test_url() -> str:
    """Get the PostgreSQL test database URL.

    Returns:
        Database URL for the PostgreSQL test database (genonaut_test)

    Raises:
        RuntimeError: If database configuration is not set up for testing
    """
    # Ensure we're in test mode
    os.environ["ENV_TARGET"] = "local-test"
    os.environ["APP_CONFIG_PATH"] = "config/local-test.json"
    os.environ["GENONAUT_DB_ENVIRONMENT"] = "test"

    settings = get_settings()

    # Get password from environment
    db_password = os.getenv("DB_PASSWORD_ADMIN")
    if not db_password:
        raise RuntimeError(
            "DB_PASSWORD_ADMIN environment variable not set. "
            "Ensure env/.env.shared is loaded."
        )

    # Construct PostgreSQL URL
    db_url = (
        f"postgresql://{settings.db_user_admin}:{db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )

    return db_url


def create_postgres_test_engine(echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine for the PostgreSQL test database.

    Args:
        echo: Whether to echo SQL statements (useful for debugging)

    Returns:
        SQLAlchemy Engine configured for PostgreSQL test database
    """
    db_url = get_postgres_test_url()

    engine = create_engine(
        db_url,
        echo=echo,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
    )

    return engine


@contextmanager
def postgres_test_transaction(session: Session) -> Generator[Session, None, None]:
    """Context manager for test transactions that automatically rollback.

    This provides transaction isolation for tests - changes made within the
    context manager are rolled back when the context exits, leaving the
    database in a clean state.

    Args:
        session: SQLAlchemy session

    Yields:
        Session within a savepoint that will be rolled back

    Example:
        with postgres_test_transaction(session) as tx_session:
            user = User(username="test")
            tx_session.add(user)
            tx_session.commit()
        # Changes are rolled back here
    """
    # Begin a savepoint (nested transaction)
    session.begin_nested()

    try:
        yield session
    finally:
        # Always rollback to restore clean state
        session.rollback()


# ---------------------------------------------------------------------------
# Pytest Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def postgres_engine():
    """Session-scoped PostgreSQL engine.

    Creates a single engine that's reused across all tests in the session.
    This is more efficient than creating a new engine for each test.

    Yields:
        SQLAlchemy Engine for PostgreSQL test database
    """
    engine = create_postgres_test_engine(echo=False)

    # Verify connection works
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
    except Exception as e:
        raise RuntimeError(
            f"Failed to connect to PostgreSQL test database: {e}\n"
            "Ensure the test database is initialized with: make init-test"
        )

    yield engine

    # Clean up
    engine.dispose()


@pytest.fixture(scope="function")
def postgres_session(postgres_engine) -> Generator[Session, None, None]:
    """Function-scoped PostgreSQL session with automatic rollback.

    Each test gets a fresh session within a transaction that's automatically
    rolled back after the test completes. This provides test isolation without
    needing to truncate tables or recreate the database.

    Args:
        postgres_engine: Session-scoped engine fixture

    Yields:
        SQLAlchemy Session for test use

    Example:
        def test_user_creation(postgres_session):
            user = User(username="testuser")
            postgres_session.add(user)
            postgres_session.commit()

            # Query the user
            found = postgres_session.query(User).filter_by(username="testuser").first()
            assert found is not None
            # Changes rolled back after test
    """
    # Create a connection and begin a transaction
    connection = postgres_engine.connect()
    transaction = connection.begin()

    # Create a session bound to the connection
    # expire_on_commit=False prevents objects from expiring after commit,
    # which is important for API tests that access fixture objects after API calls
    SessionLocal = sessionmaker(bind=connection, expire_on_commit=False)
    session = SessionLocal()

    # Begin a nested transaction (savepoint) for the test
    session.begin_nested()

    # Set up event listener to recreate savepoint after each commit
    # This allows tests to call commit() without actually committing
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    # Cleanup: rollback and close everything
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def postgres_session_no_rollback(postgres_engine) -> Generator[Session, None, None]:
    """PostgreSQL session without automatic rollback.

    Use this fixture when you need to test actual database commits, or when
    you need changes to persist across multiple operations. You're responsible
    for cleaning up any data created during the test.

    Args:
        postgres_engine: Session-scoped engine fixture

    Yields:
        SQLAlchemy Session without automatic rollback

    Warning:
        This fixture does NOT automatically rollback changes. Use with caution
        and ensure you clean up test data manually.

    Example:
        def test_with_real_commit(postgres_session_no_rollback):
            user = User(username="permanent_test_user")
            postgres_session_no_rollback.add(user)
            postgres_session_no_rollback.commit()

            # Clean up
            postgres_session_no_rollback.delete(user)
            postgres_session_no_rollback.commit()
    """
    SessionLocal = sessionmaker(bind=postgres_engine)
    session = SessionLocal()

    yield session

    session.close()


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def truncate_tables(session: Session, *table_names: str) -> None:
    """Truncate specified tables in the test database.

    This is useful for cleaning up test data when using the no-rollback session.
    Uses CASCADE to handle foreign key constraints.

    Args:
        session: Database session
        *table_names: Names of tables to truncate

    Example:
        truncate_tables(session, "users", "content_items")
    """
    if not table_names:
        return

    tables_str = ", ".join(table_names)
    session.execute(text(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE"))
    session.commit()


def count_rows(session: Session, table_name: str) -> int:
    """Count rows in a table.

    Args:
        session: Database session
        table_name: Name of table to count

    Returns:
        Number of rows in the table
    """
    result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar()


def table_exists(session: Session, table_name: str) -> bool:
    """Check if a table exists in the database.

    Args:
        session: Database session
        table_name: Name of table to check

    Returns:
        True if table exists, False otherwise
    """
    result = session.execute(
        text(
            "SELECT EXISTS ("
            "  SELECT FROM information_schema.tables "
            "  WHERE table_schema = 'public' "
            "  AND table_name = :table_name"
            ")"
        ),
        {"table_name": table_name}
    )
    return result.scalar()


def get_table_columns(session: Session, table_name: str) -> list[str]:
    """Get list of column names for a table.

    Args:
        session: Database session
        table_name: Name of table

    Returns:
        List of column names
    """
    result = session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :table_name "
            "ORDER BY ordinal_position"
        ),
        {"table_name": table_name}
    )
    return [row[0] for row in result.fetchall()]


def verify_postgres_features(session: Session) -> dict[str, bool]:
    """Verify that PostgreSQL-specific features are working.

    This is useful for tests that depend on PostgreSQL features that in-memory databases
    doesn't support (JSONB, table partitioning, etc.)

    Args:
        session: Database session

    Returns:
        Dictionary of feature names and whether they're working

    Example:
        features = verify_postgres_features(session)
        assert features["jsonb"], "JSONB support required"
        assert features["partitioning"], "Table partitioning required"
    """
    features = {}

    # Check JSONB support
    try:
        session.execute(text("SELECT '{}'::jsonb"))
        features["jsonb"] = True
    except Exception:
        features["jsonb"] = False

    # Check table partitioning support
    try:
        # Check if content_items_all exists and is partitioned
        result = session.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT FROM pg_catalog.pg_class c "
                "  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
                "  WHERE n.nspname = 'public' "
                "  AND c.relname = 'content_items_all' "
                "  AND c.relkind = 'p'"  # 'p' = partitioned table
                ")"
            )
        )
        features["partitioning"] = result.scalar()
    except Exception:
        features["partitioning"] = False

    # Check table inheritance support
    try:
        result = session.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT FROM pg_catalog.pg_inherits"
                ")"
            )
        )
        features["inheritance"] = True
    except Exception:
        features["inheritance"] = False

    return features
