"""Database utility functions for Genonaut.

This module provides utility functions for database operations including
URL construction and configuration management.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url


# Load environment variables from .env file in the env/ directory
# Path from genonaut/db/init.py -> project_root/env/.env
env_path = Path(__file__).parent.parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


def _coerce_bool(value: Optional[str]) -> bool:
    """Convert an environment string to boolean.

    Args:
        value: Raw environment variable value.

    Returns:
        True when the value represents a truthy flag, False otherwise.
    """

    if value is None:
        return False

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_name_for_flag(demo: bool) -> str:
    """Resolve database name for the requested environment."""

    if demo:
        return os.getenv("DB_NAME_DEMO", "genonaut_demo")
    return os.getenv("DB_NAME", "genonaut")


def get_database_url(demo: Optional[bool] = None) -> str:
    """Get database URL from environment variables.

    Args:
        demo: Optional flag indicating that the demo database should be used.
            When omitted, the value falls back to the `DEMO` environment
            variable, defaulting to False.

    For initialization tasks, uses admin credentials by default.

    Returns:
        Database URL string.

    Raises:
        ValueError: If required environment variables are not set.
    """

    resolved_demo = demo if demo is not None else _coerce_bool(os.getenv("DEMO"))
    database_name = _database_name_for_flag(resolved_demo)

    # Prefer an explicit DATABASE_URL variable when provided
    url_env_key = "DATABASE_URL_DEMO" if resolved_demo else "DATABASE_URL"
    raw_url = os.getenv(url_env_key)

    if raw_url and raw_url.strip():
        return raw_url.strip()

    # If we're looking for the demo DB but only DATABASE_URL is present, reuse it.
    fallback_url = os.getenv("DATABASE_URL")
    if resolved_demo and fallback_url and fallback_url.strip():
        url_obj = make_url(fallback_url.strip())
        if url_obj.database != database_name:
            url_obj = url_obj.set(database=database_name)
        return str(url_obj)

    # Otherwise, construct from individual components using admin credentials by default
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")

    # Try admin credentials first (for initialization)
    admin_password = os.getenv("DB_PASSWORD_ADMIN")
    if admin_password:
        return (
            f"postgresql://genonaut_admin:{admin_password}@{host}:{port}/{database_name}"
        )

    # Fall back to legacy credentials for backward compatibility
    username = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise ValueError(
            "Database password must be provided via DB_PASSWORD_ADMIN (preferred) or "
            "DB_PASSWORD/DATABASE_URL environment variable"
        )

    return f"postgresql://{username}:{password}@{host}:{port}/{database_name}"

