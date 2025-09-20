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


def _normalize_environment(demo: Optional[bool], environment: Optional[str]) -> str:
    """Normalize database environment selection.

    Args:
        demo: Legacy flag indicating demo database usage.
        environment: Optional explicit environment name.

    Returns:
        Canonical environment string: ``dev``, ``demo``, or ``test``.
    """

    if environment:
        candidate = environment.strip().lower()
        if candidate in {"dev", "demo", "test"}:
            return candidate

    if demo is not None:
        return "demo" if demo else "dev"

    explicit = os.getenv("GENONAUT_DB_ENVIRONMENT") or os.getenv("API_ENVIRONMENT")
    if explicit:
        lowered = explicit.strip().lower()
        if lowered in {"dev", "demo", "test"}:
            return lowered

    if _coerce_bool(os.getenv("TEST", "0")):
        return "test"
    if _coerce_bool(os.getenv("DEMO")):
        return "demo"
    return "dev"


def resolve_database_environment(
    demo: Optional[bool] = None,
    environment: Optional[str] = None,
) -> str:
    """Public helper to resolve the active database environment."""

    return _normalize_environment(demo, environment)


def _database_name_for_environment(environment: str) -> str:
    """Resolve database name for the requested environment."""

    if environment == "demo":
        return os.getenv("DB_NAME_DEMO", "genonaut_demo")
    if environment == "test":
        return os.getenv("DB_NAME_TEST", "genonaut_test")
    return os.getenv("DB_NAME", "genonaut")


def get_database_url(demo: Optional[bool] = None, environment: Optional[str] = None) -> str:
    """Get database URL from environment variables.

    Args:
        demo: Legacy flag indicating that the demo database should be used.
        environment: Explicit environment name (``dev``, ``demo``, ``test``).

    For initialization tasks, uses admin credentials by default.

    Returns:
        Database URL string.

    Raises:
        ValueError: If required environment variables are not set.
    """

    resolved_environment = _normalize_environment(demo, environment)
    database_name = _database_name_for_environment(resolved_environment)

    # Prefer an explicit DATABASE_URL variable when provided
    env_key_map = {
        "dev": "DATABASE_URL",
        "demo": "DATABASE_URL_DEMO",
        "test": "DATABASE_URL_TEST",
    }
    url_env_key = env_key_map.get(resolved_environment, "DATABASE_URL")
    raw_url = os.getenv(url_env_key)

    if raw_url and raw_url.strip():
        return raw_url.strip()

    # If we're looking for the demo DB but only DATABASE_URL is present, reuse it.
    fallback_url = os.getenv("DATABASE_URL")
    if resolved_environment in {"demo", "test"} and fallback_url and fallback_url.strip():
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
