"""Local to GitHub synchronization functionality for md-manager.

This module handles pushing local markdown files and their metadata to GitHub issues.
Phase 3 focuses on the Local → GitHub direction of synchronization.

Key Features:
- Detect local file changes since last sync
- Parse markdown file metadata and content
- Create new GitHub issues from local files
- Update existing GitHub issues with local changes
- Handle bidirectional sync coordination
- Resolve conflicts between local and remote changes
"""

import sqlite3
import re
import logging
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .github_client import (
    GitHubClient, GitHubError, AuthenticationError, AuthorizationError,
    NotFoundError, ValidationError, ServerError, NetworkError
)
from .config import GitHubConfig
from .github_sync import GitHubSyncError, DatabaseError, ConfigurationError
from .auth import get_authentication_provider
from .cache import FileChangeCache, create_cache_provider


class SyncDirection(Enum):
    """Synchronization direction enum."""
    LOCAL_TO_GITHUB = "local_to_github"
    GITHUB_TO_LOCAL = "github_to_local"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    MANUAL = "manual"
    SKIP = "skip"


@dataclass
class FileChange:
    """Represents a change to a local file."""
    file_id: int
    file_path: str
    change_type: str  # "created", "modified", "deleted"
    current_hash: Optional[str]
    previous_hash: Optional[str]
    modified_time: datetime
    github_issue_num: Optional[int] = None
    sync_required: bool = True


@dataclass
class SyncConflict:
    """Represents a synchronization conflict."""
    file_id: int
    file_path: str
    issue_num: int
    conflict_type: str  # "content", "metadata", "state"
    local_value: Any
    remote_value: Any
    last_local_modified: datetime
    last_remote_modified: datetime


class LocalSyncError(GitHubSyncError):
    """Exception raised during local to GitHub synchronization operations."""
    pass


class ConflictError(LocalSyncError):
    """Exception raised when sync conflicts cannot be resolved automatically."""

    def __init__(self, message: str, conflicts: List[SyncConflict]):
        super().__init__(message)
        self.conflicts = conflicts


class LocalToGitHubSyncer:
    """
    Handles synchronization from local markdown files to GitHub issues.

    This class manages the process of detecting local file changes and pushing
    them to GitHub as new issues or updates to existing issues.
    """

    def __init__(self, db_path: str, github_config: GitHubConfig):
        """
        Initialize the local to GitHub syncer.

        Args:
            db_path: Path to the SQLite database
            github_config: GitHub configuration settings

        Raises:
            ConfigurationError: If configuration is invalid
            DatabaseError: If database setup fails
        """
        self.db_path = db_path
        self.github_config = github_config

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Initialize file change cache for optimization
        cache_provider = create_cache_provider("memory")
        self.file_cache = FileChangeCache(cache_provider)

        # Validate configuration
        self._validate_config()

        # Initialize GitHub client
        self.client = None
        if github_config.sync_enabled:
            try:
                # Get authentication provider from config
                auth_provider = get_authentication_provider(github_config.__dict__)
                if not auth_provider:
                    raise ConfigurationError("No valid authentication method configured")

                self.client = GitHubClient(
                    auth_provider=auth_provider,
                    repo_owner=github_config.repo_owner,
                    repo_name=github_config.repo_name,
                    base_url=github_config.base_url,
                    max_retries=github_config.max_retries,
                    rate_limit_threshold=github_config.rate_limit_threshold
                )
                self.logger.info(f"Initialized GitHub client for local sync: {github_config.repo_owner}/{github_config.repo_name}")
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize GitHub client: {str(e)}")

        # Validate database exists
        if not Path(db_path).exists():
            raise DatabaseError(f"Database file not found: {db_path}")

    def _validate_config(self) -> None:
        """
        Validate GitHub configuration for local sync.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.github_config.sync_enabled:
            return  # Sync is disabled, no validation needed

        required_fields = ['token', 'repo_owner', 'repo_name']
        missing_fields = [field for field in required_fields
                         if not getattr(self.github_config, field, None)]

        if missing_fields:
            raise ConfigurationError(
                f"Missing required GitHub configuration: {', '.join(missing_fields)}"
            )

        # Validate repository name format
        if not re.match(r'^[a-zA-Z0-9._-]+$', self.github_config.repo_name):
            raise ConfigurationError(f"Invalid repository name: {self.github_config.repo_name}")

        # Validate repository owner format
        if not re.match(r'^[a-zA-Z0-9._-]+$', self.github_config.repo_owner):
            raise ConfigurationError(f"Invalid repository owner: {self.github_config.repo_owner}")

    def detect_file_changes(self, since: Optional[str] = None) -> List[FileChange]:
        """
        Detect changes to local files since the last sync.

        Args:
            since: ISO 8601 timestamp to detect changes since this time

        Returns:
            List of file changes that need to be synchronized

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.info("Detecting local file changes for sync")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get files that have been modified since last sync
            if since:
                cursor.execute("""
                    SELECT f.id, f.root, f.path, f.filename, f.updated_datetime,
                           g.num as github_issue_num
                    FROM files f
                    LEFT JOIN github g ON f.id = g.md_file_id
                    WHERE f.is_deleted = 0
                    AND f.updated_datetime > ?
                    ORDER BY f.updated_datetime ASC
                """, (since,))
            else:
                # Get all active files
                cursor.execute("""
                    SELECT f.id, f.root, f.path, f.filename, f.updated_datetime,
                           g.num as github_issue_num
                    FROM files f
                    LEFT JOIN github g ON f.id = g.md_file_id
                    WHERE f.is_deleted = 0
                    ORDER BY f.updated_datetime ASC
                """)

            # Collect all file paths for batch change detection
            file_data = []
            for row in cursor.fetchall():
                file_id, root_path, relative_path, filename, modified_time, github_issue_num = row
                full_path = os.path.join(root_path, relative_path)
                file_data.append((file_id, full_path, relative_path, filename, modified_time, github_issue_num))

            # Use file cache to efficiently detect which files have actually changed
            file_paths = [data[1] for data in file_data]  # Extract full paths
            changed_file_paths = set(self.file_cache.get_changed_files(file_paths))

            changes = []
            for file_id, full_path, relative_path, filename, modified_time, github_issue_num in file_data:
                # Skip files that haven't changed (optimization)
                if full_path not in changed_file_paths:
                    self.logger.debug(f"File unchanged, skipping: {relative_path}")
                    continue

                # Calculate content hash only for changed files
                current_hash = None
                try:
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            current_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    else:
                        self.logger.warning(f"File does not exist: {full_path}")
                        continue
                except Exception as e:
                    self.logger.warning(f"Could not calculate hash for {relative_path}: {e}")
                    continue

                # Determine change type
                if github_issue_num is None:
                    change_type = "created"  # New file, no GitHub issue yet
                else:
                    # Check if content has changed by comparing with last sync hash
                    change_type = "modified"  # Assume modified for now

                change = FileChange(
                    file_id=file_id,
                    file_path=relative_path,
                    change_type=change_type,
                    current_hash=current_hash,
                    previous_hash=None,  # We'll populate this from sync history
                    modified_time=datetime.fromisoformat(modified_time.replace('Z', '+00:00')),
                    github_issue_num=github_issue_num
                )
                changes.append(change)

            self.logger.info(f"Found {len(changes)} files with potential changes")
            return changes

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to detect file changes: {str(e)}")
        finally:
            conn.close()

    def _get_full_path_for_file(self, file_id: int) -> Optional[str]:
        """
        Get the full filesystem path for a file by its ID.

        Args:
            file_id: Database ID of the file

        Returns:
            Full path to the file, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT root, path FROM files WHERE id = ?", (file_id,))
            result = cursor.fetchone()

            if result:
                root, relative_path = result
                return os.path.join(root, relative_path)
            return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get full path for file {file_id}: {e}")
            return None
        finally:
            conn.close()

    def parse_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Parse metadata from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary with parsed metadata

        Raises:
            LocalSyncError: If file parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {
                "title": None,
                "labels": [],
                "assignees": [],
                "milestone": None,
                "state": "open",
                "body": content,
                "priority": None
            }

            # Extract title from first header
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

            # Extract frontmatter if present
            frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
            if frontmatter_match:
                frontmatter_text = frontmatter_match.group(1)
                metadata["body"] = frontmatter_match.group(2).strip()

                # Parse YAML-like frontmatter
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')

                        if key in ['labels', 'assignees']:
                            # Parse comma-separated values
                            metadata[key] = [v.strip() for v in value.split(',') if v.strip()]
                        elif key in metadata:
                            metadata[key] = value

            # If no title found, use filename as fallback
            if not metadata["title"]:
                filename = Path(file_path).stem
                metadata["title"] = filename.replace('-', ' ').replace('_', ' ').title()

            return metadata

        except Exception as e:
            raise LocalSyncError(f"Failed to parse file metadata from {file_path}: {str(e)}")

    def create_github_issue(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new GitHub issue.

        Args:
            metadata: Issue metadata parsed from local file

        Returns:
            GitHub issue data from API response

        Raises:
            LocalSyncError: If issue creation fails
        """
        if not self.client:
            raise ConfigurationError("GitHub client not initialized")

        self.logger.info(f"Creating GitHub issue: {metadata['title']}")

        try:
            endpoint = f"/repos/{self.github_config.repo_owner}/{self.github_config.repo_name}/issues"

            issue_data = {
                "title": metadata["title"],
                "body": metadata["body"],
            }

            # Add optional fields if present
            if metadata.get("labels"):
                issue_data["labels"] = metadata["labels"]

            if metadata.get("assignees"):
                issue_data["assignees"] = metadata["assignees"]

            if metadata.get("milestone"):
                issue_data["milestone"] = metadata["milestone"]

            response = self.client._make_request("POST", endpoint, data=issue_data)

            # Update project board fields if present
            if metadata.get("project_key_vals"):
                success = self.client.update_issue_project_fields(
                    response['number'],
                    metadata["project_key_vals"]
                )
                if success:
                    self.logger.debug(f"Updated project fields for issue #{response['number']}")
                else:
                    self.logger.warning(f"Could not update project fields for issue #{response['number']}")

            self.logger.info(f"Created GitHub issue #{response['number']}: {response['title']}")
            return response

        except GitHubError as e:
            raise LocalSyncError(f"Failed to create GitHub issue: {str(e)}")

    def update_github_issue(self, issue_num: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing GitHub issue.

        Args:
            issue_num: GitHub issue number
            metadata: Updated issue metadata

        Returns:
            GitHub issue data from API response

        Raises:
            LocalSyncError: If issue update fails
        """
        if not self.client:
            raise ConfigurationError("GitHub client not initialized")

        self.logger.info(f"Updating GitHub issue #{issue_num}: {metadata['title']}")

        try:
            endpoint = f"/repos/{self.github_config.repo_owner}/{self.github_config.repo_name}/issues/{issue_num}"

            issue_data = {
                "title": metadata["title"],
                "body": metadata["body"],
            }

            # Add optional fields if present
            if metadata.get("labels"):
                issue_data["labels"] = metadata["labels"]

            if metadata.get("assignees"):
                issue_data["assignees"] = metadata["assignees"]

            if metadata.get("milestone"):
                issue_data["milestone"] = metadata["milestone"]

            if metadata.get("state") in ["open", "closed"]:
                issue_data["state"] = metadata["state"]

            response = self.client._make_request("PATCH", endpoint, data=issue_data)

            # Update project board fields if present
            if metadata.get("project_key_vals"):
                success = self.client.update_issue_project_fields(
                    issue_num,
                    metadata["project_key_vals"]
                )
                if success:
                    self.logger.debug(f"Updated project fields for issue #{issue_num}")
                else:
                    self.logger.warning(f"Could not update project fields for issue #{issue_num}")

            self.logger.info(f"Updated GitHub issue #{response['number']}: {response['title']}")
            return response

        except NotFoundError:
            raise LocalSyncError(f"GitHub issue #{issue_num} not found")
        except GitHubError as e:
            raise LocalSyncError(f"Failed to update GitHub issue #{issue_num}: {str(e)}")

    def detect_conflicts(self, file_changes: List[FileChange]) -> List[SyncConflict]:
        """
        Detect conflicts between local changes and remote GitHub state.

        Args:
            file_changes: List of local file changes

        Returns:
            List of conflicts that need resolution

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.info("Detecting sync conflicts")
        conflicts = []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for change in file_changes:
                if change.github_issue_num is None:
                    continue  # New files can't have conflicts

                # Get current GitHub data from database
                cursor.execute("""
                    SELECT title, body, state, updated_at
                    FROM github
                    WHERE num = ?
                """, (change.github_issue_num,))

                result = cursor.fetchone()
                if not result:
                    continue  # No GitHub data available

                remote_title, remote_body, remote_state, remote_updated_at = result

                # Parse current local metadata
                try:
                    full_path = self._get_full_path_for_file(change.file_id)
                    if not full_path:
                        continue  # Skip files we can't find
                    local_metadata = self.parse_file_metadata(full_path)
                except LocalSyncError:
                    continue  # Skip files we can't parse

                # Check for conflicts
                remote_modified = datetime.fromisoformat(remote_updated_at.replace('Z', '+00:00'))

                # Title conflict
                if local_metadata["title"] != remote_title and change.modified_time > remote_modified:
                    conflicts.append(SyncConflict(
                        file_id=change.file_id,
                        file_path=change.file_path,
                        issue_num=change.github_issue_num,
                        conflict_type="title",
                        local_value=local_metadata["title"],
                        remote_value=remote_title,
                        last_local_modified=change.modified_time,
                        last_remote_modified=remote_modified
                    ))

                # Content conflict
                if local_metadata["body"] != remote_body and change.modified_time > remote_modified:
                    conflicts.append(SyncConflict(
                        file_id=change.file_id,
                        file_path=change.file_path,
                        issue_num=change.github_issue_num,
                        conflict_type="content",
                        local_value=local_metadata["body"],
                        remote_value=remote_body,
                        last_local_modified=change.modified_time,
                        last_remote_modified=remote_modified
                    ))

                # State conflict
                if local_metadata["state"] != remote_state and change.modified_time > remote_modified:
                    conflicts.append(SyncConflict(
                        file_id=change.file_id,
                        file_path=change.file_path,
                        issue_num=change.github_issue_num,
                        conflict_type="state",
                        local_value=local_metadata["state"],
                        remote_value=remote_state,
                        last_local_modified=change.modified_time,
                        last_remote_modified=remote_modified
                    ))

            self.logger.info(f"Found {len(conflicts)} potential sync conflicts")
            return conflicts

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to detect conflicts: {str(e)}")
        finally:
            conn.close()

    def resolve_conflicts(self, conflicts: List[SyncConflict], strategy: ConflictResolution) -> List[SyncConflict]:
        """
        Resolve sync conflicts using the specified strategy.

        Args:
            conflicts: List of conflicts to resolve
            strategy: Resolution strategy to apply

        Returns:
            List of unresolved conflicts (empty if all resolved)

        Raises:
            ConflictError: If manual resolution is required
        """
        self.logger.info(f"Resolving {len(conflicts)} conflicts with strategy: {strategy.value}")

        if strategy == ConflictResolution.MANUAL:
            if conflicts:
                raise ConflictError(
                    f"Manual resolution required for {len(conflicts)} conflicts",
                    conflicts
                )
            return []

        unresolved = []

        for conflict in conflicts:
            if strategy == ConflictResolution.LOCAL_WINS:
                # Local changes take precedence - continue with sync
                self.logger.debug(f"Resolving conflict in favor of local: {conflict.file_path}")
                continue

            elif strategy == ConflictResolution.REMOTE_WINS:
                # Remote changes take precedence - skip this file's sync
                self.logger.debug(f"Resolving conflict in favor of remote: {conflict.file_path}")
                # We could update local file here, but that's Phase 2 territory
                continue

            elif strategy == ConflictResolution.SKIP:
                # Skip conflicted files entirely
                self.logger.debug(f"Skipping conflicted file: {conflict.file_path}")
                unresolved.append(conflict)

        return unresolved

    def update_local_sync_record(self, file_id: int, github_issue_num: int, sync_time: str) -> None:
        """
        Update the local database with sync information.

        Args:
            file_id: Database ID of the file
            github_issue_num: GitHub issue number
            sync_time: ISO 8601 timestamp of sync

        Raises:
            DatabaseError: If database update fails
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update or insert GitHub mapping
            cursor.execute("""
                INSERT OR REPLACE INTO github (
                    md_file_id, is_issue, num, url, title, labels, type,
                    assignees, milestone, state, created_at, updated_at,
                    closed_at, body
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id, True, github_issue_num,
                f"https://github.com/{self.github_config.repo_owner}/{self.github_config.repo_name}/issues/{github_issue_num}",
                "", "", "issue", "", "", "open", sync_time, sync_time, None, ""
            ))

            # Ensure sync_status table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY,
                    last_sync_time TEXT NOT NULL,
                    sync_type TEXT NOT NULL
                )
            """)

            # Record sync event
            cursor.execute("""
                INSERT INTO sync_status (last_sync_time, sync_type)
                VALUES (?, 'local_to_github')
            """, (sync_time,))

            conn.commit()

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update sync record: {str(e)}")
        finally:
            conn.close()

    def sync_to_github(
        self,
        conflict_resolution: ConflictResolution = ConflictResolution.LOCAL_WINS,
        dry_run: bool = False,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronize local files to GitHub issues.

        Args:
            conflict_resolution: Strategy for resolving conflicts
            dry_run: If True, show what would be synced without making changes
            since: ISO 8601 timestamp to sync changes since this time

        Returns:
            Dictionary with sync statistics

        Raises:
            LocalSyncError: If synchronization fails
            ConflictError: If conflicts cannot be resolved
        """
        if not self.github_config.sync_enabled:
            raise LocalSyncError("GitHub sync is not enabled")

        sync_type = "dry-run" if dry_run else "local-to-github"
        self.logger.info(f"Starting {sync_type} synchronization")

        sync_start_time = datetime.now(timezone.utc).isoformat()

        # Detect local file changes
        file_changes = self.detect_file_changes(since=since)

        # Detect conflicts
        conflicts = self.detect_conflicts(file_changes)

        # Resolve conflicts
        unresolved_conflicts = self.resolve_conflicts(conflicts, conflict_resolution)

        if unresolved_conflicts:
            raise ConflictError(
                f"Cannot proceed with {len(unresolved_conflicts)} unresolved conflicts",
                unresolved_conflicts
            )

        # Track statistics
        stats = {
            "total_files": len(file_changes),
            "new_issues": 0,
            "updated_issues": 0,
            "skipped_files": 0,
            "conflicts_resolved": len(conflicts) - len(unresolved_conflicts),
            "errors": 0
        }

        if dry_run:
            self.logger.info(f"DRY RUN: Would process {len(file_changes)} files")
            for change in file_changes:
                if change.change_type == "created":
                    self.logger.info(f"  Would create issue for: {change.file_path}")
                else:
                    self.logger.info(f"  Would update issue #{change.github_issue_num} for: {change.file_path}")
            return stats

        # Process each file change
        failed_files = []
        for change in file_changes:
            try:
                # Get full path for the file
                full_path = self._get_full_path_for_file(change.file_id)
                if not full_path:
                    self.logger.warning(f"Could not find full path for file {change.file_path}")
                    continue

                # Parse file metadata
                metadata = self.parse_file_metadata(full_path)

                if change.change_type == "created":
                    # Create new GitHub issue
                    issue_response = self.create_github_issue(metadata)
                    self.update_local_sync_record(
                        change.file_id,
                        issue_response["number"],
                        sync_start_time
                    )
                    stats["new_issues"] += 1

                elif change.change_type == "modified" and change.github_issue_num:
                    # Update existing GitHub issue
                    self.update_github_issue(change.github_issue_num, metadata)
                    stats["updated_issues"] += 1

                else:
                    stats["skipped_files"] += 1

            except Exception as e:
                stats["errors"] += 1
                failed_files.append({
                    "file_path": change.file_path,
                    "error": str(e)
                })
                self.logger.error(f"Failed to sync {change.file_path}: {str(e)}")

        # Log final statistics
        self.logger.info(f"Local to GitHub sync completed: {stats['new_issues']} created, "
                        f"{stats['updated_issues']} updated, {stats['skipped_files']} skipped, "
                        f"{stats['errors']} errors")

        # Log rate limit summary if available
        if self.client:
            self.client.log_rate_limit_summary()
            rate_stats = self.client.get_rate_limit_stats()
            stats.update({
                "api_requests_made": rate_stats["requests_made"],
                "rate_limit_hits": rate_stats["rate_limit_hits"],
                "total_delay_time": rate_stats["total_delay_time"]
            })

        return stats