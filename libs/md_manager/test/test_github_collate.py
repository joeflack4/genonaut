"""Tests for GitHub integration in collate functionality."""

import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

from md_manager.collate import collate_files
from md_manager.github_schema import migrate_database


class TestGitHubCollate:
    """Test cases for GitHub integration in collate functionality."""

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
    def test_directory_with_issues(self):
        """Create a temporary directory with issues and non-issues files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create regular files (not issues)
            (temp_path / "README.md").write_text("# README")
            (temp_path / "notes.md").write_text("# Notes")

            # Create issues directory structure
            issues_dir = temp_path / "issues"
            issues_dir.mkdir()
            (issues_dir / "bug-report.md").write_text("# Bug Report")
            (issues_dir / "feature-request.md").write_text("# Feature Request")

            # Create nested issues directories
            nested_issues = issues_dir / "priority" / "high"
            nested_issues.mkdir(parents=True)
            (nested_issues / "critical-bug.md").write_text("# Critical Bug")

            # Create subdirectory that contains issues in path
            sub_issues = temp_path / "project" / "issues" / "open"
            sub_issues.mkdir(parents=True)
            (sub_issues / "enhancement.md").write_text("# Enhancement")

            # Non-issue file in same directory as issues
            (temp_path / "project" / "documentation.md").write_text("# Documentation")

            yield temp_path

    def test_collate_detects_issue_files(self, test_directory_with_issues, temp_db_path):
        """Test that collate correctly identifies issue files based on path."""
        # Run migration first to create github table
        migrate_database(temp_db_path)

        # Run collate
        collate_files([str(test_directory_with_issues)], temp_db_path, recursive=True)

        # Check database contents
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check files table
        cursor.execute("SELECT path FROM files ORDER BY path")
        files = [row[0] for row in cursor.fetchall()]

        expected_files = {
            "README.md",
            "notes.md",
            "issues/bug-report.md",
            "issues/feature-request.md",
            "issues/priority/high/critical-bug.md",
            "project/issues/open/enhancement.md",
            "project/documentation.md"
        }
        assert set(files) == expected_files

        # Check github table - should have entries for all files
        cursor.execute("SELECT COUNT(*) FROM github")
        github_count = cursor.fetchone()[0]
        assert github_count == len(expected_files)

        # Check is_issue detection
        cursor.execute("""
            SELECT f.path, g.is_issue
            FROM files f
            JOIN github g ON f.id = g.md_file_id
            ORDER BY f.path
        """)
        results = cursor.fetchall()

        issue_files = {path for path, is_issue in results if is_issue}
        non_issue_files = {path for path, is_issue in results if not is_issue}

        expected_issue_files = {
            "issues/bug-report.md",
            "issues/feature-request.md",
            "issues/priority/high/critical-bug.md",
            "project/issues/open/enhancement.md"
        }

        expected_non_issue_files = {
            "README.md",
            "notes.md",
            "project/documentation.md"
        }

        assert issue_files == expected_issue_files
        assert non_issue_files == expected_non_issue_files

        conn.close()

    def test_collate_updates_existing_github_entries(self, test_directory_with_issues, temp_db_path):
        """Test that running collate multiple times updates github entries correctly."""
        migrate_database(temp_db_path)

        # First run
        collate_files([str(test_directory_with_issues)], temp_db_path, recursive=True)

        # Second run - should update existing entries, not create duplicates
        collate_files([str(test_directory_with_issues)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Should still have same number of entries
        cursor.execute("SELECT COUNT(*) FROM github")
        github_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM files")
        files_count = cursor.fetchone()[0]

        assert github_count == files_count  # One github entry per file

        conn.close()

    def test_is_issue_detection_edge_cases(self):
        """Test edge cases for is_issue detection."""
        from md_manager.collate import is_issue_file

        # Test various paths
        test_cases = [
            # (path, expected_is_issue)
            ("issues/bug.md", True),
            ("Issues/Bug.md", True),  # Case insensitive
            ("ISSUES/BUG.MD", True),
            ("project/issues/open/bug.md", True),
            ("deep/nested/issues/closed/old-bug.md", True),
            ("my-issues/bug.md", False),  # Should be exact word match
            ("issues-log/notes.md", False),
            ("README.md", False),
            ("src/main.py", False),
            ("docs/issues.md", False),  # File named issues, not in issues dir
            ("issues", False),  # Not a file
            ("", False),  # Empty path
        ]

        for path, expected in test_cases:
            result = is_issue_file(path)
            assert result == expected, f"Path '{path}' should be {expected}, got {result}"

    def test_collate_with_overwrite_preserves_github_data(self, test_directory_with_issues, temp_db_path):
        """Test that overwrite mode preserves GitHub-related data structure."""
        migrate_database(temp_db_path)

        # First run
        collate_files([str(test_directory_with_issues)], temp_db_path, recursive=True)

        # Verify github table exists and has data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM github")
        initial_count = cursor.fetchone()[0]
        assert initial_count > 0
        conn.close()

        # Run with overwrite
        collate_files([str(test_directory_with_issues)], temp_db_path, recursive=True, overwrite=True)

        # Verify github table still exists and has data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM github")
        final_count = cursor.fetchone()[0]

        # Should have same number of entries
        assert final_count == initial_count

        # Verify is_issue is still correctly detected
        cursor.execute("""
            SELECT f.path, g.is_issue
            FROM files f
            JOIN github g ON f.id = g.md_file_id
            WHERE g.is_issue = 1
        """)
        issue_files = cursor.fetchall()
        assert len(issue_files) > 0  # Should have some issue files

        conn.close()

    def test_github_table_foreign_key_relationship(self, test_directory_with_issues, temp_db_path):
        """Test that foreign key relationship works correctly."""
        migrate_database(temp_db_path)
        collate_files([str(test_directory_with_issues)], temp_db_path, recursive=True)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Test that every github entry has a valid file reference
        cursor.execute("""
            SELECT g.md_file_id, f.id
            FROM github g
            LEFT JOIN files f ON g.md_file_id = f.id
            WHERE f.id IS NULL
        """)
        orphaned_entries = cursor.fetchall()
        assert len(orphaned_entries) == 0, "All github entries should reference valid files"

        # Test that every file has a corresponding github entry
        cursor.execute("""
            SELECT f.id, g.md_file_id
            FROM files f
            LEFT JOIN github g ON f.id = g.md_file_id
            WHERE g.md_file_id IS NULL
        """)
        missing_github_entries = cursor.fetchall()
        assert len(missing_github_entries) == 0, "All files should have github entries"

        conn.close()