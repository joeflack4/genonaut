"""Database safety utilities to prevent accidental data loss.

This module provides validation functions to ensure destructive database operations
(DROP, TRUNCATE) are only performed on test databases, not on production or demo databases.
"""

import re
from typing import Optional
from urllib.parse import urlparse


class UnsafeDatabaseOperationError(Exception):
    """Raised when attempting a destructive operation on a non-test database."""
    pass


def validate_test_database_name(db_name: str) -> None:
    """Validate that a database name is safe for destructive operations.

    Only databases containing '_test' (e.g., 'genonaut_test', 'genonaut_test_pg',
    'genonaut_test_init') are considered safe for DROP or TRUNCATE operations.
    This prevents accidental data loss in production, demo, or development databases.

    Args:
        db_name: The database name to validate

    Raises:
        UnsafeDatabaseOperationError: If the database name is not a test database

    Examples:
        >>> validate_test_database_name("genonaut_test")  # OK
        >>> validate_test_database_name("genonaut_test_init")  # OK
        >>> validate_test_database_name("genonaut_test_pg")  # OK
        >>> validate_test_database_name("genonaut")  # Raises error
        >>> validate_test_database_name("genonaut_demo")  # Raises error
    """
    if not db_name:
        raise UnsafeDatabaseOperationError(
            "Database name is empty or None. Cannot perform destructive operations."
        )

    # Only allow databases containing '_test' somewhere in the name
    if "_test" not in db_name:
        raise UnsafeDatabaseOperationError(
            f"Refusing to perform destructive operation on database '{db_name}'. "
            f"Only databases containing '_test' in their name are allowed. "
            f"This prevents accidental data loss in production, demo, or development databases."
        )


def validate_test_database_url(db_url: str) -> None:
    """Validate that a database URL points to a safe test database.

    Extracts the database name from the URL and validates it using
    validate_test_database_name().

    Args:
        db_url: The database URL to validate (e.g., postgresql://user:pass@host:port/dbname)

    Raises:
        UnsafeDatabaseOperationError: If the database in the URL is not a test database
        ValueError: If the URL cannot be parsed or doesn't contain a database name

    Examples:
        >>> validate_test_database_url("postgresql://user:pass@localhost/genonaut_test")  # OK
        >>> validate_test_database_url("postgresql://user:pass@localhost/genonaut")  # Raises error
    """
    if not db_url:
        raise ValueError("Database URL is empty or None")

    try:
        # Parse the URL to extract the database name
        parsed = urlparse(db_url)

        # The database name is the path without the leading '/'
        db_name = parsed.path.lstrip('/')

        if not db_name:
            raise ValueError(
                f"Could not extract database name from URL: {db_url}. "
                f"URL path is empty."
            )

        # Validate the extracted database name
        validate_test_database_name(db_name)

    except UnsafeDatabaseOperationError:
        # Re-raise with context about the URL
        raise
    except Exception as e:
        raise ValueError(
            f"Failed to parse database URL '{db_url}': {e}"
        )


def extract_db_name_from_url(db_url: str) -> Optional[str]:
    """Extract database name from a database URL.

    Args:
        db_url: The database URL (e.g., postgresql://user:pass@host:port/dbname)

    Returns:
        The database name, or None if it couldn't be extracted

    Examples:
        >>> extract_db_name_from_url("postgresql://user@localhost/mydb")
        'mydb'
        >>> extract_db_name_from_url("postgresql://user@localhost/")
        None
    """
    if not db_url:
        return None

    try:
        parsed = urlparse(db_url)
        db_name = parsed.path.lstrip('/')
        return db_name if db_name else None
    except Exception:
        return None


def validate_test_database_from_session(session) -> None:
    """Validate that a SQLAlchemy session is connected to a test database.

    Extracts the database name from the session's connection URL and validates it.

    Args:
        session: SQLAlchemy Session object

    Raises:
        UnsafeDatabaseOperationError: If the database is not a test database
        ValueError: If the database name cannot be extracted from the session
    """
    try:
        # Get the database URL from the session's engine
        engine = session.get_bind()
        db_url = str(engine.url)

        # Validate using the URL validation function
        validate_test_database_url(db_url)

    except UnsafeDatabaseOperationError:
        # Re-raise as-is
        raise
    except Exception as e:
        raise ValueError(
            f"Failed to extract database name from session: {e}"
        )
