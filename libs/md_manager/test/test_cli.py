"""Tests for CLI commands."""

import os
import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from md_manager.cli import cli
from md_manager.collate import collate_files


class TestExportCLI:
    """Test cases for the export CLI command."""

    @pytest.fixture
    def example_notes_dir(self):
        """Return path to the example notes directory."""
        current_dir = Path(__file__).parent
        return current_dir / "input" / "example-notes-dir"

    @pytest.fixture
    def temp_db_with_data(self, example_notes_dir):
        """Create a temporary database with test data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name

        # Populate database with test data
        collate_files([str(example_notes_dir)], temp_db_path, recursive=True)

        yield temp_db_path

        # Cleanup
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

    def test_export_with_db_path(self, temp_db_with_data):
        """Test export command with explicit database path."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export")

            result = runner.invoke(cli, [
                'export',
                '--db-path', temp_db_with_data,
                '--export-path', export_path
            ])

            assert result.exit_code == 0
            assert "Successfully exported database" in result.output

            # Verify export directory and files were created
            assert os.path.exists(export_path)
            files_tsv = os.path.join(export_path, "files.tsv")
            assert os.path.exists(files_tsv)

            # Verify TSV content
            with open(files_tsv, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 2  # Header + at least one data row

    def test_export_without_db_path_finds_database(self, temp_db_with_data):
        """Test export command finds database automatically."""
        runner = CliRunner()

        # Copy database to working directory with expected name
        with tempfile.TemporaryDirectory() as temp_dir:
            target_db = os.path.join(temp_dir, "md_manager.db")

            # Copy the database file
            import shutil
            shutil.copy2(temp_db_with_data, target_db)

            # Change to temp directory and run export
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = runner.invoke(cli, ['export'])

                assert result.exit_code == 0
                assert "Successfully exported database" in result.output

                # Should create export directory in current working directory
                export_dir = os.path.join(temp_dir, "export")
                assert os.path.exists(export_dir)
                assert os.path.exists(os.path.join(export_dir, "files.tsv"))

            finally:
                os.chdir(original_cwd)

    def test_export_no_database_found(self):
        """Test export command when no database is found."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = runner.invoke(cli, ['export'])

                assert result.exit_code != 0
                assert "No database found" in result.output

            finally:
                os.chdir(original_cwd)

    def test_export_nonexistent_database(self):
        """Test export command with nonexistent database path."""
        runner = CliRunner()

        result = runner.invoke(cli, [
            'export',
            '--db-path', '/nonexistent/database.db'
        ])

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_export_shows_file_summary(self, temp_db_with_data):
        """Test that export command shows summary of created files."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "summary_test")

            result = runner.invoke(cli, [
                'export',
                '--db-path', temp_db_with_data,
                '--export-path', export_path
            ])

            assert result.exit_code == 0
            assert "Created" in result.output
            assert "TSV file" in result.output
            assert "files.tsv" in result.output
            assert "rows)" in result.output  # Should show row count