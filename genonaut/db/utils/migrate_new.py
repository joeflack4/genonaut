#!/usr/bin/env python3
"""New migration history initialization utility for Genonaut project.

This script automates the process of starting a fresh alembic migration history
after a database reset with history cleanup.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from .utils import resolve_database_environment, get_database_url


def _run_command(cmd: list[str], env_vars: Optional[dict] = None) -> tuple[bool, str, str]:
    """Run a command and return success status with output.

    Args:
        cmd: Command and arguments to run
        env_vars: Optional environment variables to set

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        # Merge environment variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent.parent  # Project root
        )

        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def _drop_alembic_version_table(database_url: str) -> None:
    """Drop the alembic_version table to start fresh."""
    print("Ensuring alembic_version table is removed...")

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if table exists first
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version');"
            ))
            table_exists = result.scalar()

            if table_exists:
                # Use autocommit mode for DDL
                conn.execute(text("DROP TABLE alembic_version;"))
                conn.commit()
                print("✓ alembic_version table dropped successfully")
            else:
                print("✓ alembic_version table already removed")
        engine.dispose()
    except Exception as e:
        raise RuntimeError(f"Failed to drop alembic_version table: {e}")


def _fix_migration_imports() -> None:
    """Fix import issues in generated migration files."""
    # Find the most recent migration file
    migrations_dir = Path(__file__).parent.parent / "migrations" / "versions"
    migration_files = list(migrations_dir.glob("*.py"))

    if not migration_files:
        return

    # Get the most recent migration file
    latest_migration = max(migration_files, key=lambda p: p.stat().st_mtime)

    try:
        # Read the file content
        content = latest_migration.read_text()

        # Fix imports and references
        if "genonaut.db.schema.JSONColumn()" in content:
            # Add import if not present
            if "from genonaut.db.schema import JSONColumn" not in content:
                content = content.replace(
                    "from alembic import op\nimport sqlalchemy as sa",
                    "from alembic import op\nimport sqlalchemy as sa\nfrom genonaut.db.schema import JSONColumn"
                )

            # Replace full path with short reference
            content = content.replace("genonaut.db.schema.JSONColumn()", "JSONColumn()")

            # Write back the fixed content
            latest_migration.write_text(content)
            print("  ✓ Fixed migration imports")

    except Exception as e:
        print(f"  Warning: Could not fix migration imports: {e}")


def _generate_baseline_migration(environment: str, database_url: str) -> None:
    """Generate a new baseline migration from current schema."""
    print("Generating baseline migration from current schema...")

    # Determine which environment variables to set based on environment
    env_vars = {
        "ALEMBIC_SQLALCHEMY_URL": database_url,
        "DATABASE_URL": database_url,
    }

    if environment == "demo":
        env_vars["DATABASE_URL_DEMO"] = database_url
    elif environment == "test":
        env_vars["DATABASE_URL_TEST"] = database_url
        env_vars["GENONAUT_DB_ENVIRONMENT"] = "test"

    # Generate migration
    cmd = ["alembic", "revision", "--autogenerate", "-m", "baseline schema after history reset"]
    success, stdout, stderr = _run_command(cmd, env_vars)

    if not success:
        raise RuntimeError(f"Failed to generate baseline migration: {stderr}")

    print("✓ Baseline migration generated successfully")

    # Fix import issues in the generated migration
    _fix_migration_imports()

    if stdout.strip():
        # Extract revision ID from output if possible
        for line in stdout.split('\n'):
            if 'Generating' in line and 'revision ID' in line:
                print(f"  {line.strip()}")


def _apply_migration(database_url: str) -> None:
    """Apply the migration to actually create the tables."""
    print("Applying migration to create database tables...")

    env_vars = {
        "ALEMBIC_SQLALCHEMY_URL": database_url,
        "DATABASE_URL": database_url,
    }

    cmd = ["alembic", "upgrade", "head"]
    success, stdout, stderr = _run_command(cmd, env_vars)

    if not success:
        raise RuntimeError(f"Failed to apply migration: {stderr}")

    print("✓ Migration applied and tables created")


def _verify_migration_state(database_url: str) -> None:
    """Verify that the migration state is clean and consistent."""
    print("Verifying migration state...")

    env_vars = {
        "ALEMBIC_SQLALCHEMY_URL": database_url,
        "DATABASE_URL": database_url,
    }

    # Check heads
    cmd = ["alembic", "heads"]
    success, heads_output, stderr = _run_command(cmd, env_vars)
    if not success:
        raise RuntimeError(f"Failed to check alembic heads: {stderr}")

    # Check current
    cmd = ["alembic", "current"]
    success, current_output, stderr = _run_command(cmd, env_vars)
    if not success:
        raise RuntimeError(f"Failed to check alembic current: {stderr}")

    # Parse outputs
    heads_lines = [line.strip() for line in heads_output.strip().split('\n') if line.strip()]
    current_lines = [line.strip() for line in current_output.strip().split('\n') if line.strip()]

    # Should have exactly one head
    if len(heads_lines) != 1:
        raise RuntimeError(f"Expected exactly one head, but found {len(heads_lines)}: {heads_lines}")

    # Should have exactly one current revision
    if len(current_lines) != 1:
        raise RuntimeError(f"Expected exactly one current revision, but found {len(current_lines)}: {current_lines}")

    # Head and current should match
    head_revision = heads_lines[0].split()[0]  # Extract revision ID
    current_revision = current_lines[0].split()[0]  # Extract revision ID

    if head_revision != current_revision:
        raise RuntimeError(
            f"Head revision ({head_revision}) does not match current revision ({current_revision}). "
            "Migration state is inconsistent."
        )

    print(f"✓ Migration state verified successfully")
    print(f"  Head revision: {head_revision}")
    print(f"  Current revision: {current_revision}")


def initialize_new_migration_history(
    environment: Optional[str] = None,
    database_url: Optional[str] = None,
) -> None:
    """Initialize a new alembic migration history after database reset.

    This function automates the process of:
    1. Dropping the alembic_version table
    2. Generating a new baseline migration
    3. Stamping the database with the baseline
    4. Verifying the migration state is clean

    Args:
        environment: Database environment (demo, test, etc.)
        database_url: Optional explicit database URL

    Raises:
        RuntimeError: If any step fails or verification fails
    """
    resolved_environment = resolve_database_environment(environment)
    target_url = database_url or get_database_url(environment=resolved_environment)
    url_obj = make_url(target_url)
    database_name = url_obj.database or ""

    print(f"Initializing new migration history for: {database_name} ({resolved_environment})")

    try:
        # Step 1: Drop alembic_version table
        _drop_alembic_version_table(target_url)

        # Step 2: Generate baseline migration
        _generate_baseline_migration(resolved_environment, target_url)

        # Step 3: Apply the migration to actually create tables
        _apply_migration(target_url)

        # Step 4: Verify everything is consistent
        _verify_migration_state(target_url)

        print("✅ New migration history initialized successfully!")

    except Exception as e:
        print(f"❌ Failed to initialize migration history: {e}")
        raise


def _build_cli_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser for migration initialization utility."""
    parser = argparse.ArgumentParser(
        description="Initialize new Alembic migration history after database reset",
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

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entry point for the migration initialization CLI."""
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    try:
        initialize_new_migration_history(
            environment=getattr(args, "environment", None),
            database_url=getattr(args, "database_url", None),
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()