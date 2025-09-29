"""Tests for Local → GitHub synchronization functionality."""

import os
import tempfile
import pytest
import responses
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from md_manager.local_sync import (
    LocalToGitHubSyncer, LocalSyncError, ConflictError,
    FileChange, SyncConflict, ConflictResolution
)
from md_manager.config import GitHubConfig
from md_manager.collate import collate_files
from md_manager.github_schema import migrate_database


class TestLocalToGitHubSyncer:
    """Test cases for LocalToGitHubSyncer class."""

    @pytest.fixture
    def temp_dir_with_files(self):
        """Create temporary directory with markdown files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create markdown files with different content
            (temp_path / "001-bug-report.md").write_text("""# Bug Report

## Description
Login form is not working properly.

## Steps to Reproduce
1. Go to login page
2. Enter credentials
3. Click submit

## Expected Result
User should be logged in.

## Actual Result
Error message appears.
""")

            (temp_path / "feature-123.md").write_text("""---
title: Dark Mode Feature
labels: enhancement, ui
assignees: developer1
state: open
---

# Dark Mode Feature

Implement dark mode toggle for better user experience.

## Requirements
- Toggle button in settings
- Persist user preference
- Apply to all pages
""")

            (temp_path / "simple-issue.md").write_text("""# Simple Issue

This is a simple issue without frontmatter.
""")

            yield temp_path

    @pytest.fixture
    def synced_database(self, temp_dir_with_files):
        """Database with files already collated."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Collate files first
            collate_files([str(temp_dir_with_files)], db_path, recursive=True)
            migrate_database(db_path)
            yield db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.fixture
    def github_config(self):
        """GitHub configuration for testing."""
        return GitHubConfig(
            token="test_token",
            repo_owner="test_owner",
            repo_name="test_repo",
            sync_enabled=True
        )

    @pytest.fixture
    def syncer(self, synced_database, github_config):
        """LocalToGitHubSyncer instance for testing."""
        return LocalToGitHubSyncer(synced_database, github_config)

    def test_syncer_initialization(self, synced_database, github_config):
        """Test syncer initialization."""
        syncer = LocalToGitHubSyncer(synced_database, github_config)

        assert syncer.db_path == synced_database
        assert syncer.github_config == github_config
        assert syncer.client is not None
        assert syncer.logger is not None

    def test_syncer_initialization_sync_disabled(self, synced_database):
        """Test syncer initialization with sync disabled."""
        config = GitHubConfig(sync_enabled=False)
        syncer = LocalToGitHubSyncer(synced_database, config)

        assert syncer.client is None

    def test_detect_file_changes(self, syncer):
        """Test detection of local file changes."""
        changes = syncer.detect_file_changes()

        assert len(changes) == 3
        assert all(isinstance(change, FileChange) for change in changes)
        assert all(change.change_type == "created" for change in changes)  # New files
        assert all(change.github_issue_num is None for change in changes)  # No GitHub issues yet

    def test_detect_file_changes_with_since(self, syncer):
        """Test file change detection with since parameter."""
        # Test with future timestamp - should return no changes
        future_time = datetime.now(timezone.utc).isoformat()
        changes = syncer.detect_file_changes(since=future_time)

        assert len(changes) == 0

    def test_parse_file_metadata_with_frontmatter(self, syncer, temp_dir_with_files):
        """Test parsing file metadata with YAML frontmatter."""
        file_path = temp_dir_with_files / "feature-123.md"
        metadata = syncer.parse_file_metadata(str(file_path))

        assert metadata["title"] == "Dark Mode Feature"
        assert "enhancement" in metadata["labels"]
        assert "ui" in metadata["labels"]
        assert "developer1" in metadata["assignees"]
        assert metadata["state"] == "open"
        assert "Implement dark mode toggle" in metadata["body"]

    def test_parse_file_metadata_without_frontmatter(self, syncer, temp_dir_with_files):
        """Test parsing file metadata without frontmatter."""
        file_path = temp_dir_with_files / "001-bug-report.md"
        metadata = syncer.parse_file_metadata(str(file_path))

        assert metadata["title"] == "Bug Report"
        assert metadata["labels"] == []
        assert metadata["assignees"] == []
        assert metadata["state"] == "open"
        assert "Login form is not working" in metadata["body"]

    def test_parse_file_metadata_simple_file(self, syncer, temp_dir_with_files):
        """Test parsing simple file without headers."""
        file_path = temp_dir_with_files / "simple-issue.md"
        metadata = syncer.parse_file_metadata(str(file_path))

        assert metadata["title"] == "Simple Issue"
        assert "This is a simple issue" in metadata["body"]

    def test_parse_file_metadata_fallback_title(self, syncer, temp_dir_with_files):
        """Test title fallback to filename when no header found."""
        # Create file without header
        test_file = temp_dir_with_files / "test-feature-request.md"
        test_file.write_text("Just some content without a header.")

        metadata = syncer.parse_file_metadata(str(test_file))

        assert metadata["title"] == "Test Feature Request"  # Filename converted to title

    @responses.activate
    def test_create_github_issue_success(self, syncer):
        """Test successful GitHub issue creation."""
        # Mock GitHub API response
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={
                "number": 42,
                "title": "Test Issue",
                "html_url": "https://github.com/test_owner/test_repo/issues/42",
                "state": "open"
            },
            status=201
        )

        metadata = {
            "title": "Test Issue",
            "body": "Test description",
            "labels": ["bug"],
            "assignees": ["user1"]
        }

        response = syncer.create_github_issue(metadata)

        assert response["number"] == 42
        assert response["title"] == "Test Issue"
        assert len(responses.calls) == 1

        # Verify request data
        request_data = responses.calls[0].request.body
        if isinstance(request_data, bytes):
            assert b"Test Issue" in request_data
            assert b"bug" in request_data
        else:
            assert "Test Issue" in request_data
            assert "bug" in request_data

    @responses.activate
    def test_create_github_issue_api_error(self, syncer):
        """Test GitHub issue creation with API error."""
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={"message": "Validation Failed"},
            status=422
        )

        metadata = {
            "title": "Test Issue",
            "body": "Test description"
        }

        with pytest.raises(LocalSyncError, match="Failed to create GitHub issue"):
            syncer.create_github_issue(metadata)

    @responses.activate
    def test_update_github_issue_success(self, syncer):
        """Test successful GitHub issue update."""
        responses.add(
            responses.PATCH,
            "https://api.github.com/repos/test_owner/test_repo/issues/42",
            json={
                "number": 42,
                "title": "Updated Issue",
                "html_url": "https://github.com/test_owner/test_repo/issues/42",
                "state": "open"
            },
            status=200
        )

        metadata = {
            "title": "Updated Issue",
            "body": "Updated description",
            "labels": ["enhancement"]
        }

        response = syncer.update_github_issue(42, metadata)

        assert response["number"] == 42
        assert response["title"] == "Updated Issue"

    @responses.activate
    def test_update_github_issue_not_found(self, syncer):
        """Test GitHub issue update with non-existent issue."""
        responses.add(
            responses.PATCH,
            "https://api.github.com/repos/test_owner/test_repo/issues/999",
            json={"message": "Not Found"},
            status=404
        )

        metadata = {
            "title": "Updated Issue",
            "body": "Updated description"
        }

        with pytest.raises(LocalSyncError, match="GitHub issue #999 not found"):
            syncer.update_github_issue(999, metadata)

    def test_detect_conflicts_no_github_data(self, syncer):
        """Test conflict detection with no GitHub data."""
        changes = syncer.detect_file_changes()
        conflicts = syncer.detect_conflicts(changes)

        # No conflicts since no GitHub data exists yet
        assert len(conflicts) == 0

    def test_resolve_conflicts_local_wins(self, syncer):
        """Test conflict resolution with local wins strategy."""
        conflicts = [
            SyncConflict(
                file_id=1,
                file_path="/test/file.md",
                issue_num=42,
                conflict_type="title",
                local_value="Local Title",
                remote_value="Remote Title",
                last_local_modified=datetime.now(timezone.utc),
                last_remote_modified=datetime.now(timezone.utc)
            )
        ]

        unresolved = syncer.resolve_conflicts(conflicts, ConflictResolution.LOCAL_WINS)

        assert len(unresolved) == 0  # All conflicts resolved in favor of local

    def test_resolve_conflicts_manual(self, syncer):
        """Test conflict resolution with manual strategy."""
        conflicts = [
            SyncConflict(
                file_id=1,
                file_path="/test/file.md",
                issue_num=42,
                conflict_type="title",
                local_value="Local Title",
                remote_value="Remote Title",
                last_local_modified=datetime.now(timezone.utc),
                last_remote_modified=datetime.now(timezone.utc)
            )
        ]

        with pytest.raises(ConflictError, match="Manual resolution required"):
            syncer.resolve_conflicts(conflicts, ConflictResolution.MANUAL)

    def test_resolve_conflicts_skip(self, syncer):
        """Test conflict resolution with skip strategy."""
        conflicts = [
            SyncConflict(
                file_id=1,
                file_path="/test/file.md",
                issue_num=42,
                conflict_type="title",
                local_value="Local Title",
                remote_value="Remote Title",
                last_local_modified=datetime.now(timezone.utc),
                last_remote_modified=datetime.now(timezone.utc)
            )
        ]

        unresolved = syncer.resolve_conflicts(conflicts, ConflictResolution.SKIP)

        assert len(unresolved) == 1  # Conflicts remain unresolved

    @responses.activate
    def test_sync_to_github_dry_run(self, syncer):
        """Test dry run sync to GitHub."""
        stats = syncer.sync_to_github(dry_run=True)

        assert stats["total_files"] == 3  # 3 files detected
        assert stats["new_issues"] == 0   # No actual creation in dry run
        assert stats["errors"] == 0

        # No API calls should be made
        assert len(responses.calls) == 0

    @responses.activate
    def test_sync_to_github_create_new_issues(self, syncer):
        """Test sync to GitHub creating new issues."""
        # Mock successful issue creation
        for i in range(1, 4):  # 3 issues
            responses.add(
                responses.POST,
                "https://api.github.com/repos/test_owner/test_repo/issues",
                json={
                    "number": i,
                    "title": f"Issue {i}",
                    "html_url": f"https://github.com/test_owner/test_repo/issues/{i}",
                    "state": "open"
                },
                status=201
            )

        stats = syncer.sync_to_github()

        assert stats["total_files"] == 3
        assert stats["new_issues"] == 3
        assert stats["updated_issues"] == 0
        assert stats["errors"] == 0

        # Should have made 3 API calls
        assert len(responses.calls) == 3

    @responses.activate
    def test_sync_to_github_with_api_error(self, syncer):
        """Test sync to GitHub with API errors."""
        # First issue succeeds
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={
                "number": 1,
                "title": "Issue 1",
                "html_url": "https://github.com/test_owner/test_repo/issues/1",
                "state": "open"
            },
            status=201
        )

        # Second issue fails
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={"message": "Validation Failed"},
            status=422
        )

        # Third issue succeeds
        responses.add(
            responses.POST,
            "https://api.github.com/repos/test_owner/test_repo/issues",
            json={
                "number": 3,
                "title": "Issue 3",
                "html_url": "https://github.com/test_owner/test_repo/issues/3",
                "state": "open"
            },
            status=201
        )

        stats = syncer.sync_to_github()

        assert stats["total_files"] == 3
        assert stats["new_issues"] == 2  # 2 succeeded
        assert stats["errors"] == 1     # 1 failed

    def test_sync_to_github_config_disabled(self, synced_database):
        """Test sync when GitHub sync is disabled."""
        config = GitHubConfig(sync_enabled=False)
        syncer = LocalToGitHubSyncer(synced_database, config)

        with pytest.raises(LocalSyncError, match="GitHub sync is not enabled"):
            syncer.sync_to_github()


class TestFileChange:
    """Test cases for FileChange dataclass."""

    def test_file_change_creation(self):
        """Test FileChange object creation."""
        change = FileChange(
            file_id=1,
            file_path="/test/file.md",
            change_type="created",
            current_hash="abc123",
            previous_hash=None,
            modified_time=datetime.now(timezone.utc)
        )

        assert change.file_id == 1
        assert change.file_path == "/test/file.md"
        assert change.change_type == "created"
        assert change.sync_required is True


class TestSyncConflict:
    """Test cases for SyncConflict dataclass."""

    def test_sync_conflict_creation(self):
        """Test SyncConflict object creation."""
        now = datetime.now(timezone.utc)
        conflict = SyncConflict(
            file_id=1,
            file_path="/test/file.md",
            issue_num=42,
            conflict_type="title",
            local_value="Local Title",
            remote_value="Remote Title",
            last_local_modified=now,
            last_remote_modified=now
        )

        assert conflict.file_id == 1
        assert conflict.issue_num == 42
        assert conflict.conflict_type == "title"
        assert conflict.local_value == "Local Title"
        assert conflict.remote_value == "Remote Title"


class TestConflictResolution:
    """Test cases for ConflictResolution enum."""

    def test_conflict_resolution_values(self):
        """Test ConflictResolution enum values."""
        assert ConflictResolution.LOCAL_WINS.value == "local_wins"
        assert ConflictResolution.REMOTE_WINS.value == "remote_wins"
        assert ConflictResolution.MANUAL.value == "manual"
        assert ConflictResolution.SKIP.value == "skip"