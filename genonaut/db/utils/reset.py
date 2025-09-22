#!/usr/bin/env python3
"""Database reset utility for Genonaut project.

This script provides functionality to reset databases with optional backup and
migration history management.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy.engine.url import make_url
from sqlalchemy import text

from .utils import (
    resolve_database_environment,
    get_database_url,
    _ensure_allowed_database,
    _ensure_seed_utilities_importable
)
from .backup import extract_db_name_from_url


def backup_database_if_requested(database_url: str, exclude_backup: bool, with_history: bool, exclude_backup_history: bool) -> None:
    """Backup database and/or migration history if requested."""
    if exclude_backup:
        print("Skipping database backup (--exclude-backup specified)")
        return

    print("Creating backup before reset...")

    # Import backup functionality
    from .backup import backup_database, backup_migration_history, create_backup_structure, sanitize_datetime_string
    from datetime import datetime
    import json

    # Load config for backup directory
    repo_root = Path(__file__).parent.parent.parent.parent
    config_path = repo_root / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    backup_dir = config.get("backup_dir", "_archive/backups/db/")

    # Extract database name and create timestamp
    db_name = extract_db_name_from_url(database_url)
    timestamp = sanitize_datetime_string(datetime.now())

    print(f"Backing up database: {db_name}")
    print(f"Timestamp: {timestamp}")

    # Create backup directory structure
    db_dump_dir, history_dir = create_backup_structure(backup_dir, db_name, timestamp)

    # Always backup database (unless --exclude-backup)
    print("=== Database Backup ===")
    if not backup_database(database_url, db_dump_dir):
        raise RuntimeError("Database backup failed")

    # Backup migration history if requested
    if with_history and not exclude_backup_history:
        print("=== Migration History Backup ===")
        if not backup_migration_history(history_dir):
            raise RuntimeError("Migration history backup failed")

    print(f"✅ Backup completed successfully!")
    print(f"Backup location: {db_dump_dir.parent}")


def verify_and_remove_migration_history(with_history: bool) -> None:
    """Verify migration files exist and remove them if requested."""
    if not with_history:
        return

    repo_root = Path(__file__).parent.parent.parent.parent
    migrations_dir = repo_root / "genonaut" / "db" / "migrations" / "versions"

    if not migrations_dir.exists():
        raise RuntimeError(f"Migration directory not found: {migrations_dir}")

    # Get all .py files
    migration_files = list(migrations_dir.glob("*.py"))

    if not migration_files:
        print("No migration files found to remove")
    else:
        print(f"Removing {len(migration_files)} migration files...")

        for migration_file in migration_files:
            print(f"Removing: {migration_file.name}")
            migration_file.unlink()

    # Remove __pycache__ directory if it exists
    pycache_dir = migrations_dir / "__pycache__"
    if pycache_dir.exists():
        print("Removing __pycache__ directory...")
        import shutil
        shutil.rmtree(pycache_dir)
        print("✓ __pycache__ directory removed")

    print("✅ Migration history removed successfully")


def reset_db(
    environment: Optional[str] = None,
    database_url: Optional[str] = None,
    exclude_backup: bool = False,
    with_history: bool = False,
    exclude_backup_history: bool = False,
) -> None:
    """Reset database with optional backup and migration history management.

    Args:
        environment: Optional explicit environment name (``demo`` or ``test``).
        database_url: Optional explicit database URL. Defaults to resolved configuration.
        exclude_backup: Skip database backup before reset.
        with_history: Also manage migration history (backup and remove).
        exclude_backup_history: Skip migration history backup when with_history is True.

    Raises:
        ValueError: If the database cannot be safely reset based on its name.
        RuntimeError: If backup fails or migration files cannot be verified.
    """
    resolved_environment = resolve_database_environment(environment=environment)
    target_url = database_url or get_database_url(environment=resolved_environment)
    url_obj = make_url(target_url)
    database_name = url_obj.database or ""

    _ensure_allowed_database(database_name, ("_demo", "_test"))

    print(f"Database reset requested for: {database_name} ({resolved_environment})")
    if with_history:
        print("Migration history will be cleared after backup")
    if exclude_backup:
        print("Database backup will be skipped")
    if exclude_backup_history and with_history:
        print("Migration history backup will be skipped")

    confirmation = input(
        "Are you sure? This will clear all rows in the database and re-initialize. (yes/no): "
    ).strip().lower()
    if confirmation != "yes":
        print("Aborted.")
        return

    # Backup database if requested
    backup_database_if_requested(target_url, exclude_backup, with_history, exclude_backup_history)

    # Remove migration history if requested (after backup)
    verify_and_remove_migration_history(with_history)

    # Import lazily to avoid circular dependencies at module import time
    from genonaut.db.init import (
        DatabaseInitializer,
        initialize_database,
        load_project_config,
        resolve_seed_path,
    )

    # Initialize database components
    initializer = DatabaseInitializer(database_url=target_url, environment=resolved_environment)
    initializer.create_engine_and_session()

    if with_history:
        # When resetting history, drop all tables (including alembic_version)
        print("Dropping all tables for fresh migration history...")
        try:
            initializer.drop_tables()
            print("✓ All tables dropped successfully")
        except Exception as e:
            print(f"Warning: Failed to drop tables: {e}")
    else:
        # When not resetting history, just truncate tables
        print(f"Truncating tables in database '{database_name}' ({resolved_environment}).")
        initializer.truncate_tables()

    # Dispose connections before re-running initialization to ensure a clean slate
    if initializer.engine is not None:
        initializer.engine.dispose()

    # Initialize new migration history if requested (BEFORE re-initialization)
    if with_history:
        print("\nInitializing new migration history...")
        from .migrate_new import initialize_new_migration_history
        try:
            initialize_new_migration_history(
                environment=resolved_environment,
                database_url=target_url,
            )
        except Exception as e:
            print(f"❌ Failed to initialize migration history: {e}")
            print("Database reset completed, but migration history setup failed.")
            print("You may need to manually initialize the migration history.")
            raise

    _ensure_seed_utilities_importable()
    seed_path = resolve_seed_path(load_project_config(), resolved_environment)

    print("Re-initializing database with migrations and seed data (if configured)...")
    initialize_database(
        database_url=target_url,
        create_db=False,
        drop_existing=False,  # Don't drop again since migration already created tables
        environment=resolved_environment,
        seed_data_path=seed_path,
    )

    print("✅ Database reset completed successfully.")


def _build_cli_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser for database reset utility."""
    parser = argparse.ArgumentParser(
        description="Reset Genonaut database environments with optional backup and history management",
    )

    parser.add_argument(
        "--environment",
        "-e",
        choices=("demo", "test"),
        help="Target database environment. Defaults to configuration resolution.",
    )
    parser.add_argument(
        "--database-url",
        help="Optional explicit database URL override.",
    )
    parser.add_argument(
        "--exclude-backup",
        action="store_true",
        help="Skip database backup before reset",
    )
    parser.add_argument(
        "--with-history",
        action="store_true",
        help="Also backup and remove migration history files",
    )
    parser.add_argument(
        "--exclude-backup-history",
        action="store_true",
        help="Skip migration history backup when --with-history is used",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entry point for the database reset CLI."""
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    try:
        reset_db(
            environment=getattr(args, "environment", None),
            database_url=getattr(args, "database_url", None),
            exclude_backup=getattr(args, "exclude_backup", False),
            with_history=getattr(args, "with_history", False),
            exclude_backup_history=getattr(args, "exclude_backup_history", False),
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()