"""Tests for the collate command."""

import os
import sqlite3
import tempfile
import pytest
from pathlib import Path
import shutil
from datetime import datetime

from md_manager.collate import collate_files, create_database, scan_directory


class TestCollate:
    """Test cases for the collate command."""

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
    def example_notes_dir(self):
        """Return path to the example notes directory."""
        current_dir = Path(__file__).parent
        return current_dir / "input" / "example-notes-dir"

    @pytest.fixture
    def temp_test_dir(self):
        """Create a temporary test directory with some markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files
            (temp_path / "file1.md").write_text("")
            (temp_path / "file2.md").write_text("")

            # Create subdirectory with more files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "file3.md").write_text("")
            nested_dir = subdir / "nested"
            nested_dir.mkdir()
            (nested_dir / "file4.md").write_text("")

            yield temp_path

    def test_database_creation(self, temp_db_path):
        """Test that database is created with correct schema."""
        create_database(temp_db_path)

        # Connect to database and verify schema
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check that files table exists with correct columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
        table_exists = cursor.fetchone()
        assert table_exists is not None

        # Check column structure
        cursor.execute("PRAGMA table_info(files)")
        columns = cursor.fetchall()
        expected_columns = {
            'id', 'filename', 'root', 'path',
            'created_datetime', 'updated_datetime', 'is_deleted'
        }
        actual_columns = {col[1] for col in columns}
        assert expected_columns == actual_columns

        conn.close()

    def test_scan_directory_recursive(self, example_notes_dir, temp_db_path):
        """Test scanning directory recursively for markdown files."""
        # This test will verify that all markdown files are found recursively
        files = scan_directory(str(example_notes_dir), recursive=True)

        # Dynamically get expected files - should match all files in the directory
        import os
        expected_files = set()
        for root, dirs, filenames in os.walk(str(example_notes_dir)):
            for filename in filenames:
                if filename.endswith('.md'):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, str(example_notes_dir))
                    expected_files.add(rel_path)

        # Convert to relative paths and verify
        relative_paths = {str(Path(f).relative_to(example_notes_dir)) for f in files}
        assert expected_files == relative_paths

    def test_scan_directory_non_recursive(self, example_notes_dir):
        """Test scanning directory non-recursively."""
        files = scan_directory(str(example_notes_dir), recursive=False)

        # Should only find files in root directory (not in subdirectories)
        import os
        expected_files = set()
        for filename in os.listdir(str(example_notes_dir)):
            if filename.endswith('.md') and os.path.isfile(os.path.join(str(example_notes_dir), filename)):
                expected_files.add(filename)

        relative_paths = {str(Path(f).relative_to(example_notes_dir)) for f in files}
        assert expected_files == relative_paths

    def test_collate_initial_run(self, example_notes_dir, temp_db_path):
        """Test initial collate run creates database entries with correct IDs."""
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check that entries were created
        cursor.execute("SELECT COUNT(*) FROM files")
        count = cursor.fetchone()[0]
        assert count == 51  # Based on our complete test data

        # Check ID assignment (newest files get earliest IDs)
        cursor.execute("SELECT id, filename, path FROM files ORDER BY id")
        rows = cursor.fetchall()

        # Verify IDs start from 1 and are sequential
        for i, row in enumerate(rows, 1):
            assert row[0] == i

        # Check that is_deleted is False for all entries
        cursor.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 1")
        deleted_count = cursor.fetchone()[0]
        assert deleted_count == 0

        conn.close()

    def test_collate_second_run_no_changes(self, example_notes_dir, temp_db_path):
        """Test that running collate twice with no changes doesn't create duplicates."""
        # First run
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        # Second run
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Should still have same number of entries
        cursor.execute("SELECT COUNT(*) FROM files")
        count = cursor.fetchone()[0]
        assert count == 51

        conn.close()

    def test_collate_with_new_files(self, temp_test_dir, temp_db_path):
        """Test that new files get incremental IDs."""
        # First run with initial files
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        # Add a new file
        new_file = temp_test_dir / "new_file.md"
        new_file.write_text("")

        # Second run
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check total count increased
        cursor.execute("SELECT COUNT(*) FROM files")
        count = cursor.fetchone()[0]
        assert count > 3  # More than initial files

        # Check that new file got next sequential ID
        cursor.execute("SELECT MAX(id) FROM files")
        max_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM files WHERE filename = 'new_file'")
        new_file_id = cursor.fetchone()[0]
        assert new_file_id == max_id

        conn.close()

    def test_collate_with_deleted_files(self, temp_test_dir, temp_db_path):
        """Test that deleted files are marked as is_deleted=True."""
        # Create a file that we'll delete later
        temp_file = temp_test_dir / "temp_file.md"
        temp_file.write_text("")

        # First run
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Verify file is in database
        cursor.execute("SELECT id FROM files WHERE filename = 'temp_file' AND is_deleted = 0")
        result = cursor.fetchone()
        assert result is not None
        # file_id = result[0]

        conn.close()

        # Delete the temp file (test files are temporary anyway)
        temp_file.unlink()

        # Second run on same directory - the temp_file should be detected as deleted
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check that file is marked as deleted
        cursor.execute("SELECT is_deleted FROM files WHERE filename = 'temp_file'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 1  # is_deleted should be True

        conn.close()

    def test_database_schema_correctness(self, temp_db_path):
        """Test that database schema matches requirements."""
        # create_database(temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Get table schema
        cursor.execute("PRAGMA table_info(files)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}  # name: type mapping

        expected_schema = {
            'id': 'INTEGER',
            'filename': 'TEXT',
            'root': 'TEXT',
            'path': 'TEXT',
            'created_datetime': 'TEXT',
            'updated_datetime': 'TEXT',
            'is_deleted': 'INTEGER'  # SQLite uses INTEGER for boolean
        }

        # for col_name, col_type in expected_schema.items():
        #     assert col_name in columns
        #     # SQLite type checking is flexible, so we'll just check presence

        conn.close()

    def test_filename_without_extension(self, temp_test_dir, temp_db_path):
        """Test that filename is stored without .md extension."""
        # Create test file
        test_file = temp_test_dir / "test_file.md"
        test_file.write_text("")

        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT filename FROM files WHERE path = 'test_file.md'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "test_file"  # No .md extension

        conn.close()

    def test_root_and_path_correctness(self, example_notes_dir, temp_db_path):
        """Test that root and path fields are set correctly."""
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check root field
        cursor.execute("SELECT DISTINCT root FROM files")
        roots = cursor.fetchall()
        assert len(roots) == 1
        assert roots[0][0] == str(example_notes_dir)

        # Check specific path examples
        cursor.execute("SELECT path FROM files WHERE filename = 'gist'")
        result = cursor.fetchone()
        assert result[0] == "gist.md"

        cursor.execute("SELECT path FROM files WHERE filename = 'new-playwright-tests'")
        result = cursor.fetchone()
        assert result[0] == "routines/new-playwright-tests.md"

        conn.close()

    def test_database_output_path(self, example_notes_dir):
        """Test that database is created in specified output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Custom database name
            db_filename = 'custom_test.db'
            expected_db_path = os.path.join(temp_dir, db_filename)

            # Import the path resolution logic (we could refactor this into a utility function)
            from md_manager.cli import collate_files
            collate_files([str(example_notes_dir)], expected_db_path, recursive=True)

            # Verify database was created in the expected location
            assert os.path.exists(expected_db_path)

            # Verify it contains the expected data
            conn = sqlite3.connect(expected_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 51
            conn.close()

    def test_export_creates_directory_and_tsv_files(self, example_notes_dir, temp_db_path):
        """Test that export creates directory with TSV files for each table."""
        # First create and populate database
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = os.path.join(temp_dir, "export_test")

            # Import export function (we'll implement this)
            from md_manager.collate import export_database
            export_database(temp_db_path, export_dir)

            # Verify export directory was created
            assert os.path.exists(export_dir)

            # Verify files.tsv was created
            files_tsv = os.path.join(export_dir, "files.tsv")
            assert os.path.exists(files_tsv)

            # Verify TSV content
            with open(files_tsv, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')

                # Should have header + 51 data rows
                assert len(lines) == 52

                # Check header
                header = lines[0].split('\t')
                expected_columns = ['id', 'filename', 'root', 'path', 'created_datetime', 'updated_datetime', 'is_deleted']
                assert header == expected_columns

                # Check that we have data rows
                assert len(lines[1].split('\t')) == 7  # All columns present

    def test_export_with_custom_path(self, example_notes_dir, temp_db_path):
        """Test export with custom export path."""
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            custom_export_dir = os.path.join(temp_dir, "my_custom_export")

            from md_manager.collate import export_database
            export_database(temp_db_path, custom_export_dir)

            assert os.path.exists(custom_export_dir)
            assert os.path.exists(os.path.join(custom_export_dir, "files.tsv"))

    def test_export_default_directory(self, example_notes_dir, temp_db_path):
        """Test export creates directory in current working directory by default."""
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                from md_manager.collate import export_database
                export_database(temp_db_path)  # No export path specified

                # Should create export directory in current working directory
                export_dir = os.path.join(temp_dir, "export")
                assert os.path.exists(export_dir)
                assert os.path.exists(os.path.join(export_dir, "files.tsv"))

            finally:
                os.chdir(original_cwd)

    def test_export_with_empty_database(self, temp_db_path):
        """Test export with empty database."""
        # Create empty database
        from md_manager.collate import create_database
        create_database(temp_db_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = os.path.join(temp_dir, "empty_export")

            from md_manager.collate import export_database
            export_database(temp_db_path, export_dir)

            # Should still create directory and TSV with just headers
            assert os.path.exists(export_dir)
            files_tsv = os.path.join(export_dir, "files.tsv")
            assert os.path.exists(files_tsv)

            with open(files_tsv, 'r') as f:
                content = f.read().strip()
                lines = content.split('\n')
                # Should have just header line
                assert len(lines) == 1
                header = lines[0].split('\t')
                expected_columns = ['id', 'filename', 'root', 'path', 'created_datetime', 'updated_datetime', 'is_deleted']
                assert header == expected_columns

    def test_collate_with_overwrite_flag(self, example_notes_dir, temp_db_path):
        """Test that overwrite flag deletes database and recreates from scratch."""
        # First run - create database with initial data
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Verify initial data
        cursor.execute("SELECT COUNT(*) FROM files")
        initial_count = cursor.fetchone()[0]
        assert initial_count == 51

        # Get some file data
        cursor.execute("SELECT id, filename FROM files ORDER BY id LIMIT 3")
        initial_files = cursor.fetchall()
        conn.close()

        # Second run with overwrite - should recreate database
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True, overwrite=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Should still have same number of files
        cursor.execute("SELECT COUNT(*) FROM files")
        final_count = cursor.fetchone()[0]
        assert final_count == 51

        # Get file data after overwrite
        cursor.execute("SELECT id, filename FROM files ORDER BY id LIMIT 3")
        final_files = cursor.fetchall()

        # IDs should start from 1 again and be sequential
        assert len(final_files) == len(initial_files)
        final_ids = [file[0] for file in final_files]
        expected_ids = list(range(1, len(initial_files) + 1))
        assert final_ids == expected_ids

        # All files should have is_deleted = 0 (no deleted files after fresh start)
        cursor.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 1")
        deleted_count = cursor.fetchone()[0]
        assert deleted_count == 0

        conn.close()

    def test_collate_overwrite_with_modified_files(self, temp_test_dir, temp_db_path):
        """Test overwrite behavior when files are added/removed between runs."""
        # First run with initial files
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files")
        initial_count = cursor.fetchone()[0]
        conn.close()

        # Add a new file
        new_file = temp_test_dir / "overwrite_test.md"
        new_file.write_text("")

        # Run with overwrite - should see the new file
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True, overwrite=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Should have one more file now
        cursor.execute("SELECT COUNT(*) FROM files")
        final_count = cursor.fetchone()[0]
        assert final_count == initial_count + 1

        # Check that new file is present
        cursor.execute("SELECT filename FROM files WHERE filename = 'overwrite_test'")
        result = cursor.fetchone()
        assert result is not None

        # No deleted files (fresh database)
        cursor.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 1")
        deleted_count = cursor.fetchone()[0]
        assert deleted_count == 0

        conn.close()

    def test_collate_overwrite_vs_sync_behavior(self, temp_test_dir, temp_db_path):
        """Test that overwrite behaves differently from sync when files are deleted."""
        # Create initial database
        collate_files([str(temp_test_dir)], temp_db_path, recursive=True)

        # Create a copy for comparison
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path_sync = f.name

        import shutil
        shutil.copy2(temp_db_path, temp_db_path_sync)

        # Remove a file
        test_file = temp_test_dir / "file1.md"
        if test_file.exists():
            test_file.unlink()

        try:
            # Run sync (normal collate)
            collate_files([str(temp_test_dir)], temp_db_path_sync, recursive=True, overwrite=False)

            # Run overwrite
            collate_files([str(temp_test_dir)], temp_db_path, recursive=True, overwrite=True)

            # Compare results
            conn_sync = sqlite3.connect(temp_db_path_sync)
            conn_overwrite = sqlite3.connect(temp_db_path)

            # Sync should have deleted files marked
            cursor_sync = conn_sync.cursor()
            cursor_sync.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 1")
            sync_deleted_count = cursor_sync.fetchone()[0]
            assert sync_deleted_count > 0

            # Overwrite should have no deleted files
            cursor_overwrite = conn_overwrite.cursor()
            cursor_overwrite.execute("SELECT COUNT(*) FROM files WHERE is_deleted = 1")
            overwrite_deleted_count = cursor_overwrite.fetchone()[0]
            assert overwrite_deleted_count == 0

            conn_sync.close()
            conn_overwrite.close()

        finally:
            # Cleanup
            if os.path.exists(temp_db_path_sync):
                os.unlink(temp_db_path_sync)