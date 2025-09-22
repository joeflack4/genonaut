"""Database utility functions for Genonaut.

This module provides utility functions for database operations including
URL construction, configuration management, and maintenance helpers.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

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


def _normalize_environment(environment: Optional[str]) -> str:
    """Normalize database environment selection.

    Args:
        environment: Optional explicit environment name.

    Returns:
        Canonical environment string: ``dev``, ``demo``, or ``test``.
    """

    if environment:
        candidate = environment.strip().lower()
        if candidate in {"dev", "demo", "test"}:
            return candidate

    explicit = os.getenv("GENONAUT_DB_ENVIRONMENT") or os.getenv("API_ENVIRONMENT")
    if explicit:
        lowered = explicit.strip().lower()
        if lowered in {"dev", "demo", "test"}:
            return lowered

    if _coerce_bool(os.getenv("TEST", "0")):
        return "test"
    return "dev"
    return "dev"


def resolve_database_environment(
    environment: Optional[str] = None,
) -> str:
    """Public helper to resolve the active database environment."""

    return _normalize_environment(environment)


def _database_name_for_environment(environment: str) -> str:
    """Resolve database name for the requested environment."""

    if environment == "demo":
        return os.getenv("DB_NAME_DEMO", "genonaut_demo")
    if environment == "test":
        return os.getenv("DB_NAME_TEST", "genonaut_test")
    return os.getenv("DB_NAME", "genonaut")


def get_database_url(environment: Optional[str] = None) -> str:
    """Get database URL from environment variables.

    Args:
        environment: Explicit environment name (``dev``, ``demo``, ``test``).

    For initialization tasks, uses admin credentials by default.

    Returns:
        Database URL string.

    Raises:
        ValueError: If required environment variables are not set.
    """

    resolved_environment = _normalize_environment(environment)
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


def _ensure_allowed_database(name: str, allowed_suffixes: Sequence[str]) -> None:
    """Validate that the database name matches one of the allowed suffixes."""

    if not name:
        raise ValueError("Unable to determine database name for reset operation")

    if not any(name.endswith(suffix) for suffix in allowed_suffixes):
        suffix_list = ", ".join(allowed_suffixes)
        raise ValueError(
            f"Refusing to reset database '{name}'. Allowed suffixes: {suffix_list}."
        )


def _ensure_seed_utilities_importable() -> None:
    """Make sure test database utilities are available for initialization seeding."""

    project_root = Path(__file__).resolve().parent.parent.parent
    candidate_dirs = [
        project_root / "test",
        project_root / "test" / "db",
        Path.cwd() / "test",
        Path.cwd() / "test" / "db",
    ]

    for path in candidate_dirs:
        if path.exists():
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)


def reset_db(
    environment: Optional[str] = None,
    database_url: Optional[str] = None,
) -> None:
    """Truncate all rows in the selected database and re-run initialization.

    The target database must end with ``_test`` or ``_demo``. The user is prompted for
    confirmation before any destructive action occurs.

    Args:
        environment: Optional explicit environment name (``demo`` or ``test``).
        database_url: Optional explicit database URL. Defaults to resolved configuration.

    Raises:
        ValueError: If the database cannot be safely reset based on its name.
        SQLAlchemyError: Propagated when initialization utilities encounter errors.
    """

    resolved_environment = resolve_database_environment(environment=environment)
    target_url = database_url or get_database_url(environment=resolved_environment)
    url_obj = make_url(target_url)
    database_name = url_obj.database or ""

    _ensure_allowed_database(database_name, ("_demo", "_test"))

    confirmation = input(
        "Are you sure? This will clear all rows in the database and re-initialize. (yes/no): "
    ).strip().lower()
    if confirmation != "yes":
        print("Aborted.")
        return

    # Import lazily to avoid circular dependencies at module import time
    from genonaut.db.init import (
        DatabaseInitializer,
        initialize_database,
        load_project_config,
        resolve_seed_path,
    )

    print(f"Truncating tables in database '{database_name}' ({resolved_environment}).")
    initializer = DatabaseInitializer(database_url=target_url, environment=resolved_environment)
    initializer.create_engine_and_session()
    initializer.truncate_tables()

    # Dispose connections before re-running initialization to ensure a clean slate
    if initializer.engine is not None:
        initializer.engine.dispose()

    _ensure_seed_utilities_importable()
    seed_path = resolve_seed_path(load_project_config(), resolved_environment)

    print("Re-initializing database with migrations and seed data (if configured)...")
    initialize_database(
        database_url=target_url,
        create_db=False,
        drop_existing=False,
        environment=resolved_environment,
        seed_data_path=seed_path,
    )

    print("Database reset completed successfully.")


def _build_cli_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser for database utilities."""

    parser = argparse.ArgumentParser(
        description="Utilities for managing Genonaut database environments",
    )
    subparsers = parser.add_subparsers(dest="command")

    reset_parser = subparsers.add_parser(
        "reset-db",
        help="Truncate and re-initialize the demo or test database",
    )
    reset_parser.add_argument(
        "--environment",
        "-e",
        choices=("demo", "test"),
        help="Target database environment. Defaults to configuration resolution.",
    )
    reset_parser.add_argument(
        "--database-url",
        help="Optional explicit database URL override.",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entry point for the module's CLI interface."""

    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    if args.command == "reset-db":
        reset_db(environment=getattr(args, "environment", None), database_url=getattr(args, "database_url", None))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
