"""GitHub database schema management and migration functionality."""

import sqlite3
import os
from typing import Optional


def get_schema_version(db_path: str) -> int:
    """
    Get the current schema version from the database.

    Args:
        db_path: Path to SQLite database

    Returns:
        Schema version number (0 if no version table exists)
    """
    if not os.path.exists(db_path):
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if schema_version table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='schema_version'
        """)

        if cursor.fetchone() is None:
            conn.close()
            return 0

        # Get current version
        cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        result = cursor.fetchone()
        version = result[0] if result else 0

    except sqlite3.Error:
        version = 0
    finally:
        conn.close()

    return version


def set_schema_version(db_path: str, version: int) -> None:
    """
    Set the schema version in the database.

    Args:
        db_path: Path to SQLite database
        version: Version number to set
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema_version table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert new version
    cursor.execute("""
        INSERT OR REPLACE INTO schema_version (version, applied_at)
        VALUES (?, datetime('now'))
    """, (version,))

    conn.commit()
    conn.close()


def create_github_schema(db_path: str) -> None:
    """
    Create the GitHub table and related indexes.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create github table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS github (
            id INTEGER PRIMARY KEY,
            md_file_id INTEGER,
            is_issue BOOLEAN NOT NULL DEFAULT 0,
            url TEXT,
            num INTEGER,
            title TEXT,
            labels TEXT, -- JSON array
            type TEXT,
            assignees TEXT, -- JSON array
            milestone TEXT,
            project_key_vals TEXT, -- JSON object for project board data
            state TEXT, -- open, closed
            created_at TEXT,
            updated_at TEXT,
            closed_at TEXT,
            body TEXT, -- issue body content
            FOREIGN KEY (md_file_id) REFERENCES files (id)
        )
    """)

    # Create indexes for efficient querying
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_github_md_file_id ON github (md_file_id)",
        "CREATE INDEX IF NOT EXISTS idx_github_is_issue ON github (is_issue)",
        "CREATE INDEX IF NOT EXISTS idx_github_url ON github (url)",
        "CREATE INDEX IF NOT EXISTS idx_github_num ON github (num)",
        "CREATE INDEX IF NOT EXISTS idx_github_state ON github (state)"
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    conn.commit()
    conn.close()

    # Update schema version
    set_schema_version(db_path, 1)


def migrate_database(db_path: str) -> None:
    """
    Run database migrations to bring schema up to date.

    Args:
        db_path: Path to SQLite database
    """
    current_version = get_schema_version(db_path)

    # Migration 1: Add GitHub table and indexes
    if current_version < 1:
        create_github_schema(db_path)


def ensure_database_schema(db_path: str) -> None:
    """
    Ensure the database has the latest schema.
    This is a convenience function that can be called to make sure
    the database is up to date.

    Args:
        db_path: Path to SQLite database
    """
    migrate_database(db_path)