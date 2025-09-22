#!/usr/bin/env python3
"""Database backup utility for Genonaut project.

This script provides functionality to backup PostgreSQL databases and migration history.
It creates organized backups with timestamps and separate folders for database dumps and migration files.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def load_config() -> dict:
    """Load configuration from config.json."""
    repo_root = Path(__file__).parent.parent.parent.parent
    config_path = repo_root / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def sanitize_datetime_string(dt: datetime) -> str:
    """Convert datetime to a filesystem-safe string."""
    # Format: YYYY-MM-DD_HH-MM-SS
    dt_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
    # Replace any remaining special characters with hyphens
    return re.sub(r'[^\w\-_]', '-', dt_str)


def extract_db_name_from_url(database_url: str) -> str:
    """Extract database name from PostgreSQL URL."""
    try:
        parsed = urlparse(database_url)

        # Check if the URL has a valid scheme
        if not parsed.scheme:
            raise ValueError("URL missing scheme (postgresql://)")

        # Check if the URL has a valid netloc (host:port)
        if not parsed.netloc:
            raise ValueError("URL missing host information")

        db_name = parsed.path.lstrip('/')
        if not db_name:
            raise ValueError("No database name found in URL")
        return db_name
    except ValueError:
        raise  # Re-raise ValueError as-is
    except Exception as e:
        raise ValueError(f"Invalid database URL format: {e}")


def create_backup_structure(backup_dir: str, db_name: str, timestamp: str) -> tuple[Path, Path]:
    """Create backup directory structure and return paths to db_dump and history dirs."""
    repo_root = Path(__file__).parent.parent.parent.parent
    base_backup_dir = repo_root / backup_dir

    # Create the main backup directory structure
    db_backup_dir = base_backup_dir / db_name / timestamp
    db_dump_dir = db_backup_dir / "db_dump"
    history_dir = db_backup_dir / "history"

    # Create all directories
    db_dump_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    return db_dump_dir, history_dir


def backup_database(database_url: str, output_dir: Path) -> bool:
    """Backup PostgreSQL database using pg_dump."""
    try:
        # Extract database name for the output file
        db_name = extract_db_name_from_url(database_url)
        output_file = output_dir / f"{db_name}_backup.sql"

        # Run pg_dump command
        cmd = [
            "pg_dump",
            database_url,
            "--verbose",
            "--no-password",
            "--format=plain",
            "--file", str(output_file)
        ]

        print(f"Running database backup: {' '.join(cmd[:2])} [URL] {' '.join(cmd[3:])}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error during database backup: {result.stderr}")
            return False

        print(f"Database backup completed: {output_file}")
        return True

    except Exception as e:
        print(f"Database backup failed: {e}")
        return False


def backup_migration_history(output_dir: Path) -> bool:
    """Backup migration history files."""
    try:
        repo_root = Path(__file__).parent.parent.parent.parent
        migrations_dir = repo_root / "genonaut" / "db" / "migrations" / "versions"

        if not migrations_dir.exists():
            print(f"Migration directory not found: {migrations_dir}")
            return False

        # Copy all .py files from versions directory
        migration_files = list(migrations_dir.glob("*.py"))

        if not migration_files:
            print("No migration files found to backup")
            return True

        print(f"Backing up {len(migration_files)} migration files...")

        for migration_file in migration_files:
            dest_file = output_dir / migration_file.name
            shutil.copy2(migration_file, dest_file)
            print(f"Copied: {migration_file.name}")

        print(f"Migration history backup completed: {output_dir}")
        return True

    except Exception as e:
        print(f"Migration history backup failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backup PostgreSQL database and migration history for Genonaut project"
    )

    parser.add_argument(
        "database_url",
        help="PostgreSQL database URL to backup"
    )

    parser.add_argument(
        "--db-dump",
        action="store_true",
        default=True,
        help="Backup database using pg_dump (default: True)"
    )

    parser.add_argument(
        "--no-db-dump",
        dest="db_dump",
        action="store_false",
        help="Skip database backup"
    )

    parser.add_argument(
        "--history",
        action="store_true",
        default=True,
        help="Backup migration history files (default: True)"
    )

    parser.add_argument(
        "--no-history",
        dest="history",
        action="store_false",
        help="Skip migration history backup"
    )

    args = parser.parse_args()

    # Validate that at least one backup type is enabled
    if not args.db_dump and not args.history:
        print("Error: At least one backup type must be enabled (--db-dump or --history)")
        sys.exit(1)

    try:
        # Load configuration
        config = load_config()
        backup_dir = config.get("backup_dir", "_archive/backups/db/")

        # Extract database name and create timestamp
        db_name = extract_db_name_from_url(args.database_url)
        timestamp = sanitize_datetime_string(datetime.now())

        print(f"Starting backup for database: {db_name}")
        print(f"Timestamp: {timestamp}")

        # Create backup directory structure
        db_dump_dir, history_dir = create_backup_structure(backup_dir, db_name, timestamp)

        success = True

        # Backup database if requested
        if args.db_dump:
            print("\n=== Database Backup ===")
            if not backup_database(args.database_url, db_dump_dir):
                success = False

        # Backup migration history if requested
        if args.history:
            print("\n=== Migration History Backup ===")
            if not backup_migration_history(history_dir):
                success = False

        if success:
            print(f"\n✅ Backup completed successfully!")
            print(f"Backup location: {db_dump_dir.parent}")
        else:
            print(f"\n❌ Backup completed with errors!")
            sys.exit(1)

    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()