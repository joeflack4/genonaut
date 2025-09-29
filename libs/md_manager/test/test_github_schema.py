"""Tests for GitHub database schema and migration functionality."""

import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

from md_manager.github_schema import create_github_schema, get_schema_version, migrate_database


class TestGitHubSchema:
    """Test cases for GitHub database schema."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def db_with_files_table(self, temp_db_path):
        """Create a database with the files table already present."""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Create the files table (existing schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                root TEXT NOT NULL,
                path TEXT NOT NULL,
                created_datetime TEXT NOT NULL,
                updated_datetime TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()
        return temp_db_path

    def test_create_github_schema(self, db_with_files_table):
        """Test that GitHub schema is created correctly."""
        create_github_schema(db_with_files_table)

        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()

        # Check that github table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github'")
        table_exists = cursor.fetchone()
        assert table_exists is not None

        # Check column structure
        cursor.execute("PRAGMA table_info(github)")
        columns = cursor.fetchall()
        column_names = {col[1] for col in columns}

        expected_columns = {
            'id', 'md_file_id', 'is_issue', 'url', 'num', 'title',
            'labels', 'type', 'assignees', 'milestone', 'project_key_vals',
            'state', 'created_at', 'updated_at', 'closed_at', 'body'
        }
        assert expected_columns == column_names

        # Check foreign key constraint exists
        cursor.execute("PRAGMA foreign_key_list(github)")
        foreign_keys = cursor.fetchall()
        assert len(foreign_keys) == 1
        assert foreign_keys[0][2] == 'files'  # References files table
        assert foreign_keys[0][3] == 'md_file_id'  # From column
        assert foreign_keys[0][4] == 'id'  # To column

        conn.close()

    def test_github_schema_indexes(self, db_with_files_table):
        """Test that proper indexes are created on github table."""
        create_github_schema(db_with_files_table)

        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()

        # Check that indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='github'")
        indexes = {row[0] for row in cursor.fetchall()}

        expected_indexes = {
            'idx_github_md_file_id',
            'idx_github_is_issue',
            'idx_github_url',
            'idx_github_num',
            'idx_github_state'
        }

        # Note: SQLite automatically creates indexes for PRIMARY KEY and UNIQUE constraints
        # so we need to check for our custom indexes
        for expected_index in expected_indexes:
            assert expected_index in indexes

        conn.close()

    def test_schema_version_tracking(self, temp_db_path):
        """Test that schema version is tracked correctly."""
        # Initially no version should exist
        version = get_schema_version(temp_db_path)
        assert version == 0

        # After creating schema, version should be 1
        create_github_schema(temp_db_path)
        version = get_schema_version(temp_db_path)
        assert version == 1

    def test_migrate_database_creates_schema(self, db_with_files_table):
        """Test that migrate_database creates GitHub schema when needed."""
        # Check initial state - no github table
        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github'")
        assert cursor.fetchone() is None
        conn.close()

        # Run migration
        migrate_database(db_with_files_table)

        # Check that github table now exists
        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_migrate_database_idempotent(self, db_with_files_table):
        """Test that migrate_database can be run multiple times safely."""
        # Run migration twice
        migrate_database(db_with_files_table)
        migrate_database(db_with_files_table)

        # Should still work and have correct schema
        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(github)")
        columns = cursor.fetchall()
        assert len(columns) == 16  # Expected number of columns

        conn.close()

    def test_github_table_data_types(self, db_with_files_table):
        """Test that columns have correct data types and constraints."""
        create_github_schema(db_with_files_table)

        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()

        # Test inserting valid data
        cursor.execute('''
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime)
            VALUES (1, 'test', '/test', 'test.md', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
        ''')

        cursor.execute('''
            INSERT INTO github (md_file_id, is_issue, url, num, title, labels, assignees, state)
            VALUES (1, 1, 'https://github.com/test/repo/issues/1', 1, 'Test Issue', '["bug"]', '["user1"]', 'open')
        ''')

        # Verify data was inserted
        cursor.execute("SELECT * FROM github WHERE md_file_id = 1")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == 1  # md_file_id
        assert row[2] == 1  # is_issue
        assert row[3] == 'https://github.com/test/repo/issues/1'  # url

        conn.close()

    def test_foreign_key_constraint(self, db_with_files_table):
        """Test that foreign key constraint is enforced."""
        create_github_schema(db_with_files_table)

        conn = sqlite3.connect(db_with_files_table)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        cursor = conn.cursor()

        # Try to insert with non-existent md_file_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO github (md_file_id, is_issue) VALUES (999, 1)
            ''')

        conn.close()

    def test_default_values(self, db_with_files_table):
        """Test that default values are set correctly."""
        create_github_schema(db_with_files_table)

        conn = sqlite3.connect(db_with_files_table)
        cursor = conn.cursor()

        # Insert files record first
        cursor.execute('''
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime)
            VALUES (1, 'test', '/test', 'test.md', '2025-01-01T00:00:00Z', '2025-01-01T00:00:00Z')
        ''')

        # Insert minimal github record
        cursor.execute('''
            INSERT INTO github (md_file_id) VALUES (1)
        ''')

        # Check default values
        cursor.execute("SELECT is_issue FROM github WHERE md_file_id = 1")
        is_issue = cursor.fetchone()[0]
        assert is_issue == 0  # Default should be 0 (False)

        conn.close()