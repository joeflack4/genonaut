"""Integration tests for database backup functionality."""

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from genonaut.db.utils.backup import (
    create_backup_structure,
    backup_migration_history,
    extract_db_name_from_url,
    sanitize_datetime_string
)


class TestBackupIntegration(unittest.TestCase):
    """Integration tests for backup functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test backups
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(self.cleanup_temp_dir)

    def cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_full_backup_structure_creation(self):
        """Test complete backup directory structure creation."""
        # Use a test database URL
        test_db_url = "postgresql://user:pass@localhost:5432/genonaut_test"
        db_name = extract_db_name_from_url(test_db_url)
        timestamp = sanitize_datetime_string(datetime.now())

        # Mock the backup directory to use our temp directory
        with unittest.mock.patch('genonaut.db.utils.backup.Path') as mock_path:
            mock_path.return_value.parent.parent.parent.parent = Path(self.temp_dir)

            backup_dir = "_archive/backups/db/"
            db_dump_dir, history_dir = create_backup_structure(backup_dir, db_name, timestamp)

            # Verify the complete structure was created
            self.assertTrue(db_dump_dir.exists())
            self.assertTrue(history_dir.exists())

            # Verify the path structure
            expected_base = Path(self.temp_dir) / "_archive" / "backups" / "db" / db_name / timestamp
            self.assertEqual(db_dump_dir.parent, expected_base)
            self.assertEqual(db_dump_dir.name, "db_dump")
            self.assertEqual(history_dir.name, "history")

            # Verify directories are writable
            test_file = db_dump_dir / "test.txt"
            test_file.write_text("test content")
            self.assertTrue(test_file.exists())

    def test_migration_history_backup_with_real_structure(self):
        """Test migration history backup with actual file operations."""
        # Create a realistic migration structure
        repo_root = Path(self.temp_dir)
        migrations_dir = repo_root / "genonaut" / "db" / "migrations" / "versions"
        migrations_dir.mkdir(parents=True)

        # Create realistic migration files
        migration_contents = [
            ('001_baseline.py', '''"""Baseline migration.

Revision ID: 001
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('users')
'''),
            ('002_add_content.py', '''"""Add content table.

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'

def upgrade():
    op.create_table('content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('content_items')
''')
        ]

        # Write migration files
        for filename, content in migration_contents:
            migration_file = migrations_dir / filename
            migration_file.write_text(content)

        # Create backup output directory
        output_dir = Path(self.temp_dir) / "backup_test"
        output_dir.mkdir()

        # Mock the path resolution
        with unittest.mock.patch('genonaut.db.utils.backup.Path') as mock_path:
            mock_path.return_value.parent.parent.parent.parent = repo_root

            # Perform backup
            result = backup_migration_history(output_dir)

            # Verify backup succeeded
            self.assertTrue(result)

            # Verify all files were copied
            for filename, original_content in migration_contents:
                backup_file = output_dir / filename
                self.assertTrue(backup_file.exists(), f"Backup file {filename} should exist")

                # Verify content matches
                backed_up_content = backup_file.read_text()
                self.assertEqual(backed_up_content, original_content)

    def test_backup_cleanup_on_failure(self):
        """Test that partial backups can be cleaned up."""
        # This test verifies that even if backup fails, we can clean up
        test_backup_dir = Path(self.temp_dir) / "failed_backup"
        test_backup_dir.mkdir()

        # Create some test files
        (test_backup_dir / "partial_file.sql").write_text("partial backup")
        (test_backup_dir / "incomplete").mkdir()

        # Verify cleanup works
        shutil.rmtree(test_backup_dir)
        self.assertFalse(test_backup_dir.exists())

    def test_concurrent_backup_structure(self):
        """Test that multiple backup operations don't interfere."""
        # Simulate multiple backups happening at different times
        timestamps = [
            "2024-01-15_14-30-45",
            "2024-01-15_14-31-00",
            "2024-01-15_14-31-15"
        ]

        db_name = "genonaut_test"
        backup_dirs = []

        with unittest.mock.patch('genonaut.db.utils.backup.Path') as mock_path:
            mock_path.return_value.parent.parent.parent.parent = Path(self.temp_dir)

            # Create multiple backup structures
            for timestamp in timestamps:
                db_dump_dir, history_dir = create_backup_structure(
                    "_archive/backups/db/", db_name, timestamp
                )
                backup_dirs.append((db_dump_dir, history_dir))

                # Add some content to distinguish them
                (db_dump_dir / f"backup_{timestamp}.sql").write_text(f"backup at {timestamp}")
                (history_dir / f"migration_{timestamp}.py").write_text(f"migration at {timestamp}")

            # Verify all backups exist and are separate
            for i, (db_dump_dir, history_dir) in enumerate(backup_dirs):
                timestamp = timestamps[i]

                self.assertTrue(db_dump_dir.exists())
                self.assertTrue(history_dir.exists())

                # Verify content is correct for each backup
                backup_file = db_dump_dir / f"backup_{timestamp}.sql"
                self.assertTrue(backup_file.exists())
                self.assertEqual(backup_file.read_text(), f"backup at {timestamp}")

    def test_backup_with_special_database_names(self):
        """Test backup with database names containing special characters."""
        special_db_names = [
            "genonaut-test",
            "genonaut_test_2024",
            "genonaut.test"
        ]

        for db_name in special_db_names:
            with self.subTest(db_name=db_name):
                test_url = f"postgresql://user:pass@localhost:5432/{db_name}"
                extracted_name = extract_db_name_from_url(test_url)
                timestamp = "2024-01-15_14-30-45"

                with unittest.mock.patch('genonaut.db.utils.backup.Path') as mock_path:
                    mock_path.return_value.parent.parent.parent.parent = Path(self.temp_dir)

                    db_dump_dir, history_dir = create_backup_structure(
                        "_archive/backups/db/", extracted_name, timestamp
                    )

                    # Should create structure successfully
                    self.assertTrue(db_dump_dir.exists())
                    self.assertTrue(history_dir.exists())

                    # Verify path contains the database name
                    self.assertIn(extracted_name, str(db_dump_dir))


if __name__ == '__main__':
    unittest.main()