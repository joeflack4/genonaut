"""Tests for database backup utility."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

from genonaut.db.utils.backup import (
    load_config,
    sanitize_datetime_string,
    extract_db_name_from_url,
    create_backup_structure,
    backup_migration_history
)


class TestBackupUtility(unittest.TestCase):
    """Test backup utility functions."""

    def test_sanitize_datetime_string(self):
        """Test datetime string sanitization."""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        result = sanitize_datetime_string(dt)
        expected = "2024-01-15_14-30-45"
        self.assertEqual(result, expected)

        # Test with special characters that might appear
        dt_with_microseconds = datetime(2024, 1, 15, 14, 30, 45, 123456)
        result = sanitize_datetime_string(dt_with_microseconds)
        self.assertEqual(result, "2024-01-15_14-30-45")

    def test_extract_db_name_from_url(self):
        """Test database name extraction from URLs."""
        # PostgreSQL URL
        url = "postgresql://user:pass@localhost:5432/testdb"
        result = extract_db_name_from_url(url)
        self.assertEqual(result, "testdb")

        # URL with schema
        url = "postgresql://user:pass@localhost:5432/testdb?schema=public"
        result = extract_db_name_from_url(url)
        self.assertEqual(result, "testdb")

        # URL without database name should raise error
        with self.assertRaises(ValueError):
            extract_db_name_from_url("postgresql://user:pass@localhost:5432/")

        # Invalid URL should raise error
        with self.assertRaises(ValueError):
            extract_db_name_from_url("invalid-url")

    @patch('genonaut.db.utils.backup.Path')
    def test_load_config(self, mock_path_class):
        """Test configuration loading."""
        # Mock config file content
        config_content = {
            "backup_dir": "_archive/backups/db/",
            "seed_data": {"test": "data"}
        }

        # Mock the Path chain properly
        mock_file = MagicMock()
        mock_file.__str__ = lambda x: "mocked_path"
        mock_file.exists.return_value = True

        # Setup the path chain: Path(__file__).parent.parent.parent.parent / 'config' / 'base.json'
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent.parent.parent.__truediv__.return_value.__truediv__.return_value = mock_file
        mock_path_class.return_value = mock_path_instance

        with patch('builtins.open', mock_open(read_data=json.dumps(config_content))):
            result = load_config()
            self.assertEqual(result, config_content)

        # Test missing config file
        mock_file.exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            load_config()

    def test_create_backup_structure(self):
        """Test backup directory structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the repo root to point to our temp directory
            with patch('genonaut.db.utils.backup.Path') as mock_path:
                mock_path.return_value.parent.parent.parent.parent = Path(temp_dir)

                backup_dir = "_archive/backups/db/"
                db_name = "testdb"
                timestamp = "2024-01-15_14-30-45"

                db_dump_dir, history_dir = create_backup_structure(backup_dir, db_name, timestamp)

                # Check that directories were created
                self.assertTrue(db_dump_dir.exists())
                self.assertTrue(history_dir.exists())

                # Check directory structure
                expected_base = Path(temp_dir) / "_archive" / "backups" / "db" / "testdb" / "2024-01-15_14-30-45"
                self.assertEqual(db_dump_dir, expected_base / "db_dump")
                self.assertEqual(history_dir, expected_base / "history")

    def test_backup_migration_history(self):
        """Test migration history backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock migration files
            migrations_dir = Path(temp_dir) / "genonaut" / "db" / "migrations" / "versions"
            migrations_dir.mkdir(parents=True)

            # Create some fake migration files
            migration_files = [
                "001_initial_migration.py",
                "002_add_users_table.py",
                "003_add_content_table.py"
            ]

            for filename in migration_files:
                migration_file = migrations_dir / filename
                migration_file.write_text(f"# Migration file: {filename}\npass\n")

            # Create output directory
            output_dir = Path(temp_dir) / "backup_output"
            output_dir.mkdir()

            # Mock the repo root
            with patch('genonaut.db.utils.backup.Path') as mock_path:
                mock_path.return_value.parent.parent.parent.parent = Path(temp_dir)

                # Run backup
                result = backup_migration_history(output_dir)

                # Check result
                self.assertTrue(result)

                # Check that files were copied
                for filename in migration_files:
                    backup_file = output_dir / filename
                    self.assertTrue(backup_file.exists())
                    self.assertIn(f"Migration file: {filename}", backup_file.read_text())

    def test_backup_migration_history_no_files(self):
        """Test migration history backup with no migration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty migrations directory
            migrations_dir = Path(temp_dir) / "genonaut" / "db" / "migrations" / "versions"
            migrations_dir.mkdir(parents=True)

            output_dir = Path(temp_dir) / "backup_output"
            output_dir.mkdir()

            # Mock the repo root
            with patch('genonaut.db.utils.backup.Path') as mock_path:
                mock_path.return_value.parent.parent.parent.parent = Path(temp_dir)

                # Run backup
                result = backup_migration_history(output_dir)

                # Should succeed even with no files
                self.assertTrue(result)

    def test_backup_migration_history_missing_directory(self):
        """Test migration history backup with missing migrations directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "backup_output"
            output_dir.mkdir()

            # Mock the repo root (migrations directory doesn't exist)
            with patch('genonaut.db.utils.backup.Path') as mock_path:
                mock_path.return_value.parent.parent.parent.parent = Path(temp_dir)

                # Run backup
                result = backup_migration_history(output_dir)

                # Should fail when migrations directory doesn't exist
                self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()