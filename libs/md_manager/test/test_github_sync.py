"""Tests for GitHub synchronization functionality."""

import os
import sqlite3
import tempfile
import pytest
import responses
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from md_manager.github_sync import GitHubIssueSyncer, GitHubSyncError, ConfigurationError
from md_manager.config import GitHubConfig
from md_manager.collate import collate_files
from md_manager.github_schema import migrate_database


class TestGitHubIssueSyncer:
    """Test cases for GitHub issue synchronization."""

    @pytest.fixture
    def github_config(self):
        """Create a test GitHub configuration."""
        return GitHubConfig(
            token="test_token",
            repo_owner="test_owner",
            repo_name="test_repo",
            sync_enabled=True
        )

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def syncer(self, temp_db_path, github_config):
        """Create a GitHubIssueSyncer instance."""
        return GitHubIssueSyncer(temp_db_path, github_config)

    @pytest.fixture
    def sample_github_issue(self):
        """Sample GitHub issue data."""
        return {
            "number": 123,
            "title": "Fix critical bug in authentication",
            "body": "The authentication system has a critical vulnerability that needs to be addressed.",
            "html_url": "https://github.com/test_owner/test_repo/issues/123",
            "state": "open",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-16T14:30:00Z",
            "closed_at": None,
            "labels": [
                {"name": "bug"},
                {"name": "priority:high"},
                {"name": "security"}
            ],
            "assignees": [
                {"login": "developer1"},
                {"login": "developer2"}
            ],
            "milestone": {
                "title": "v2.0"
            }
        }

    def test_syncer_initialization(self, temp_db_path, github_config):
        """Test GitHubIssueSyncer initialization."""
        syncer = GitHubIssueSyncer(temp_db_path, github_config)

        assert syncer.db_path == temp_db_path
        assert syncer.github_config == github_config
        assert syncer.client.auth_provider is not None
        assert syncer.client.auth_provider.is_valid()
        assert syncer.client.repo_owner == "test_owner"
        assert syncer.client.repo_name == "test_repo"

        # Verify database schema is created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github'")
        assert cursor.fetchone() is not None
        conn.close()

    @responses.activate
    def test_fetch_issues_success(self, syncer):
        """Test successful fetching of issues from GitHub."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 1,
                    "title": "Issue 1",
                    "state": "open",
                    "html_url": "https://github.com/test_owner/test_repo/issues/1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "labels": [],
                    "assignees": []
                },
                {
                    "number": 2,
                    "title": "Issue 2",
                    "state": "closed",
                    "html_url": "https://github.com/test_owner/test_repo/issues/2",
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "closed_at": "2024-01-02T12:00:00Z",
                    "labels": [],
                    "assignees": []
                }
            ],
            status=200
        )

        issues = syncer.fetch_issues()

        assert len(issues) == 2
        assert issues[0]["number"] == 1
        assert issues[1]["number"] == 2

    @responses.activate
    def test_fetch_issues_filters_pull_requests(self, syncer):
        """Test that pull requests are filtered out from issues."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 1,
                    "title": "Issue 1",
                    "state": "open",
                    "html_url": "https://github.com/test_owner/test_repo/issues/1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "labels": [],
                    "assignees": []
                },
                {
                    "number": 2,
                    "title": "Pull Request 2",
                    "state": "open",
                    "html_url": "https://github.com/test_owner/test_repo/pull/2",
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "labels": [],
                    "assignees": [],
                    "pull_request": {"url": "https://api.github.com/repos/test_owner/test_repo/pulls/2"}
                }
            ],
            status=200
        )

        issues = syncer.fetch_issues()

        # Should only return the issue, not the pull request
        assert len(issues) == 1
        assert issues[0]["number"] == 1

    @responses.activate
    def test_fetch_issues_with_since_parameter(self, syncer):
        """Test fetching issues with since parameter."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[],
            status=200
        )

        syncer.fetch_issues(since="2024-01-15T00:00:00Z")

        # Verify the request was made with correct parameters
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "since=2024-01-15T00%3A00%3A00Z" in request.url

    @responses.activate
    def test_fetch_issues_api_error(self, syncer):
        """Test handling of GitHub API errors."""
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={"message": "Not Found"},
            status=404
        )

        with pytest.raises(ConfigurationError, match="Repository not found"):
            syncer.fetch_issues()

    def test_parse_issue_metadata(self, syncer, sample_github_issue):
        """Test parsing of GitHub issue metadata."""
        metadata = syncer.parse_issue_metadata(sample_github_issue)

        assert metadata["url"] == "https://github.com/test_owner/test_repo/issues/123"
        assert metadata["num"] == 123
        assert metadata["title"] == "Fix critical bug in authentication"
        assert metadata["labels"] == ["bug", "priority:high", "security"]
        assert metadata["type"] == "issue"
        assert metadata["assignees"] == ["developer1", "developer2"]
        assert metadata["milestone"] == "v2.0"
        assert metadata["state"] == "open"
        assert metadata["created_at"] == "2024-01-15T10:00:00Z"
        assert metadata["updated_at"] == "2024-01-16T14:30:00Z"
        assert metadata["closed_at"] is None

    def test_parse_issue_metadata_minimal(self, syncer):
        """Test parsing issue metadata with minimal data."""
        minimal_issue = {
            "number": 456,
            "title": "Simple issue",
            "html_url": "https://github.com/test_owner/test_repo/issues/456",
            "state": "closed",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": "2024-01-02T00:00:00Z"
        }

        metadata = syncer.parse_issue_metadata(minimal_issue)

        assert metadata["num"] == 456
        assert metadata["title"] == "Simple issue"
        assert metadata["labels"] == []
        assert metadata["assignees"] == []
        assert metadata["milestone"] is None
        assert metadata["body"] == ""

    def test_find_matching_file_by_number_in_path(self, syncer):
        """Test finding matching file by issue number in path."""
        # Setup database with test files
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()

        # Insert test file
        cursor.execute("""
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime, is_deleted)
            VALUES (1, '123-auth-bug', '/test', 'issues/123-auth-bug.md', '2024-01-01', '2024-01-01', 0)
        """)

        cursor.execute("""
            INSERT INTO github (md_file_id, is_issue)
            VALUES (1, 1)
        """)

        conn.commit()
        conn.close()

        file_id = syncer.find_matching_file(123, "Auth bug", "Description")

        assert file_id == 1

    def test_find_matching_file_by_number_in_filename(self, syncer):
        """Test finding matching file by issue number in filename."""
        # Setup database with test files
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime, is_deleted)
            VALUES (2, 'issue-456', '/test', 'bugs/issue-456.md', '2024-01-01', '2024-01-01', 0)
        """)

        cursor.execute("""
            INSERT INTO github (md_file_id, is_issue)
            VALUES (2, 1)
        """)

        conn.commit()
        conn.close()

        file_id = syncer.find_matching_file(456, "Some bug", "Description")

        assert file_id == 2

    def test_find_matching_file_by_existing_mapping(self, syncer):
        """Test finding matching file by existing database mapping."""
        # Setup database with existing mapping
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime, is_deleted)
            VALUES (3, 'some-file', '/test', 'issues/some-file.md', '2024-01-01', '2024-01-01', 0)
        """)

        cursor.execute("""
            INSERT INTO github (md_file_id, is_issue, num)
            VALUES (3, 1, 789)
        """)

        conn.commit()
        conn.close()

        file_id = syncer.find_matching_file(789, "Mapped issue", "Description")

        assert file_id == 3

    def test_find_matching_file_no_match(self, syncer):
        """Test when no matching file is found."""
        file_id = syncer.find_matching_file(999, "Unmapped issue", "Description")

        assert file_id is None

    def test_update_issue_metadata(self, syncer):
        """Test updating issue metadata for existing file."""
        # Setup database with test file
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime, is_deleted)
            VALUES (1, 'test-file', '/test', 'issues/test-file.md', '2024-01-01', '2024-01-01', 0)
        """)

        cursor.execute("""
            INSERT INTO github (md_file_id, is_issue)
            VALUES (1, 1)
        """)

        conn.commit()
        conn.close()

        metadata = {
            "url": "https://github.com/test/repo/issues/123",
            "num": 123,
            "title": "Test Issue",
            "labels": ["bug", "urgent"],
            "type": "issue",
            "assignees": ["user1"],
            "milestone": "v1.0",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": None,
            "body": "Test description"
        }

        syncer.update_issue_metadata(1, metadata)

        # Verify update
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, num, title, state FROM github WHERE md_file_id = 1")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == "https://github.com/test/repo/issues/123"
        assert result[1] == 123
        assert result[2] == "Test Issue"
        assert result[3] == "open"

    def test_update_issue_metadata_no_entry(self, syncer):
        """Test error when trying to update non-existent GitHub entry."""
        metadata = {
            "url": "https://github.com/test/repo/issues/123",
            "num": 123,
            "title": "Test Issue",
            "labels": [],
            "type": "issue",
            "assignees": [],
            "milestone": None,
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": None,
            "body": ""
        }

        with pytest.raises(GitHubSyncError, match="No GitHub entry found for file ID"):
            syncer.update_issue_metadata(999, metadata)

    def test_create_orphan_issue_entry(self, syncer):
        """Test creating orphaned issue entry."""
        metadata = {
            "url": "https://github.com/test/repo/issues/456",
            "num": 456,
            "title": "Orphaned Issue",
            "labels": ["enhancement"],
            "type": "issue",
            "assignees": ["user2"],
            "milestone": "v2.0",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": None,
            "body": "This issue has no local file"
        }

        syncer.create_orphan_issue_entry(metadata)

        # Verify entry was created
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT md_file_id, num, title FROM github WHERE num = 456")
        result = cursor.fetchone()
        conn.close()

        assert result[0] is None  # md_file_id should be NULL
        assert result[1] == 456
        assert result[2] == "Orphaned Issue"

    def test_get_last_sync_time_none(self, syncer):
        """Test getting last sync time when no previous sync exists."""
        sync_time = syncer.get_last_sync_time()
        assert sync_time is None

    def test_get_last_sync_time_existing(self, syncer):
        """Test getting last sync time when previous sync exists."""
        # Set a sync time
        test_time = "2024-01-15T10:30:00Z"
        syncer.update_sync_time(test_time)

        sync_time = syncer.get_last_sync_time()
        assert sync_time == test_time

    def test_update_sync_time(self, syncer):
        """Test updating sync time."""
        test_time = "2024-01-16T15:45:00Z"
        syncer.update_sync_time(test_time)

        # Verify it was stored
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_sync_time FROM sync_status WHERE sync_type = 'github_issues'")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == test_time

    def test_sync_issues_disabled(self, temp_db_path):
        """Test sync when GitHub sync is disabled."""
        config = GitHubConfig(sync_enabled=False)
        syncer = GitHubIssueSyncer(temp_db_path, config)

        with pytest.raises(GitHubSyncError, match="GitHub sync is not enabled"):
            syncer.sync_issues()

    @responses.activate
    def test_sync_issues_success(self, syncer):
        """Test successful issue synchronization."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 123,
                    "title": "Test Issue",
                    "body": "Test description",
                    "html_url": "https://github.com/test_owner/test_repo/issues/123",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "closed_at": None,
                    "labels": [],
                    "assignees": [],
                    "milestone": None
                }
            ],
            status=200
        )

        # Setup existing file to match
        conn = sqlite3.connect(syncer.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO files (id, filename, root, path, created_datetime, updated_datetime, is_deleted)
            VALUES (1, '123-test-issue', '/test', 'issues/123-test-issue.md', '2024-01-01', '2024-01-01', 0)
        """)

        cursor.execute("""
            INSERT INTO github (md_file_id, is_issue)
            VALUES (1, 1)
        """)

        conn.commit()
        conn.close()

        stats = syncer.sync_issues()

        assert stats["total_fetched"] == 1
        assert stats["matched_files"] == 1
        assert stats["updated_files"] == 1
        assert stats["orphaned_issues"] == 0
        assert stats["errors"] == 0

    @responses.activate
    def test_sync_issues_with_orphans(self, syncer):
        """Test synchronization with orphaned issues."""
        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 999,
                    "title": "Orphaned Issue",
                    "body": "No local file",
                    "html_url": "https://github.com/test_owner/test_repo/issues/999",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "closed_at": None,
                    "labels": [],
                    "assignees": [],
                    "milestone": None
                }
            ],
            status=200
        )

        stats = syncer.sync_issues()

        assert stats["total_fetched"] == 1
        assert stats["matched_files"] == 0
        assert stats["updated_files"] == 0
        assert stats["orphaned_issues"] == 1
        assert stats["errors"] == 0

    @responses.activate
    def test_sync_issues_force_full_sync(self, syncer):
        """Test force full sync ignores last sync time."""
        # Set a previous sync time
        syncer.update_sync_time("2024-01-01T00:00:00Z")

        # Mock GitHub API response
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[],
            status=200
        )

        syncer.sync_issues(force_full_sync=True)

        # Verify the request was made without since parameter
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "since=" not in request.url


class TestGitHubSyncIntegration:
    """Integration tests for GitHub synchronization with real database."""

    @pytest.fixture
    def temp_dir_with_issues(self):
        """Create temporary directory with issue files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create issue files
            issues_dir = temp_path / "issues"
            issues_dir.mkdir()

            (issues_dir / "001-login-bug.md").write_text("# Login Bug\nUsers cannot log in")
            (issues_dir / "002-performance.md").write_text("# Performance Issue\nSlow loading")
            (issues_dir / "feature-123.md").write_text("# New Feature\nAdd dark mode")

            yield temp_path

    @pytest.fixture
    def synced_database(self, temp_dir_with_issues):
        """Database with files already collated."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Collate files first
            collate_files([str(temp_dir_with_issues)], db_path, recursive=True)
            yield db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @responses.activate
    def test_end_to_end_sync_workflow(self, synced_database):
        """Test complete end-to-end synchronization workflow."""
        # Mock GitHub API responses
        responses.add(
            responses.GET,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json=[
                {
                    "number": 1,
                    "title": "Login Bug Fix",
                    "body": "Fix the login issue reported by users",
                    "html_url": "https://github.com/test_owner/test_repo/issues/1",
                    "state": "open",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z",
                    "closed_at": None,
                    "labels": [{"name": "bug"}, {"name": "priority:high"}],
                    "assignees": [{"login": "developer1"}],
                    "milestone": {"title": "v1.1"}
                },
                {
                    "number": 123,
                    "title": "Dark Mode Feature",
                    "body": "Implement dark mode for better UX",
                    "html_url": "https://github.com/test_owner/test_repo/issues/123",
                    "state": "closed",
                    "created_at": "2024-01-03T00:00:00Z",
                    "updated_at": "2024-01-05T00:00:00Z",
                    "closed_at": "2024-01-05T00:00:00Z",
                    "labels": [{"name": "enhancement"}],
                    "assignees": [],
                    "milestone": None
                }
            ],
            status=200
        )

        config = GitHubConfig(
            token="test_token",
            repo_owner="test_owner",
            repo_name="test_repo",
            sync_enabled=True
        )

        syncer = GitHubIssueSyncer(synced_database, config)
        stats = syncer.sync_issues()

        # Verify synchronization results
        assert stats["total_fetched"] == 2
        assert stats["matched_files"] == 2  # Should match 001-login-bug.md and feature-123.md
        assert stats["updated_files"] == 2
        assert stats["orphaned_issues"] == 0
        assert stats["errors"] == 0

        # Verify database content
        conn = sqlite3.connect(synced_database)
        cursor = conn.cursor()

        # Check that GitHub metadata was populated
        cursor.execute("""
            SELECT f.path, g.num, g.title, g.state, g.labels
            FROM files f
            JOIN github g ON f.id = g.md_file_id
            WHERE g.num IS NOT NULL
            ORDER BY g.num
        """)

        results = cursor.fetchall()
        assert len(results) == 2

        # Issue #1 should match 001-login-bug.md
        assert results[0][0] == "issues/001-login-bug.md"
        assert results[0][1] == 1
        assert results[0][2] == "Login Bug Fix"
        assert results[0][3] == "open"
        assert "bug" in results[0][4]

        # Issue #123 should match feature-123.md
        assert results[1][0] == "issues/feature-123.md"
        assert results[1][1] == 123
        assert results[1][2] == "Dark Mode Feature"
        assert results[1][3] == "closed"

        conn.close()