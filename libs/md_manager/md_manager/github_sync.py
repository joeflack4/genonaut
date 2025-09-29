"""GitHub synchronization functionality for md-manager.

This module handles reading GitHub issues and synchronizing them with the local database.
Phase 2 focuses on the GitHub → Local direction of synchronization.
"""

import sqlite3
import re
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse

from .github_client import (
    GitHubClient, GitHubError, AuthenticationError, AuthorizationError,
    NotFoundError, ValidationError, ServerError, NetworkError, RateLimitError
)
from .config import GitHubConfig
from .github_schema import migrate_database
from .collate import create_database
from .auth import get_authentication_provider
from .sync_state import SyncStateManager, SyncOperation, SyncStatus


class GitHubSyncError(Exception):
    """Base exception for GitHub synchronization operations."""
    pass


class DatabaseError(GitHubSyncError):
    """Exception raised for database operation errors."""
    pass


class ConfigurationError(GitHubSyncError):
    """Exception raised for configuration issues."""
    pass


class SyncValidationError(GitHubSyncError):
    """Exception raised for sync validation failures."""
    pass


class PartialSyncError(GitHubSyncError):
    """Exception raised when sync completes with some errors."""

    def __init__(self, message: str, stats: Dict[str, int]):
        super().__init__(message)
        self.stats = stats


class GitHubIssueSyncer:
    """
    Handles synchronization of GitHub issues with local markdown files.

    This class manages the process of fetching issues from GitHub and updating
    the local database with their metadata.
    """

    def __init__(self, db_path: str, github_config: GitHubConfig):
        """
        Initialize the GitHub issue syncer.

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

        # Validate configuration
        self._validate_config()

        # Only initialize GitHub client if sync is enabled and we have valid auth
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
                self.logger.info(f"Initialized GitHub client for {github_config.repo_owner}/{github_config.repo_name}")
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize GitHub client: {str(e)}")

        # Ensure database schema is up to date
        try:
            create_database(db_path)  # Creates files table
            migrate_database(db_path)  # Creates github table and other GitHub-related tables
            self.logger.info(f"Database schema validated: {db_path}")
        except Exception as e:
            raise DatabaseError(f"Failed to setup database schema: {str(e)}")

        # Initialize sync state manager for resumable operations
        self.sync_state = SyncStateManager(db_path)

    def _validate_config(self) -> None:
        """
        Validate GitHub configuration.

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

        # Validate repository name format (allow alphanumeric, dots, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9._-]+$', self.github_config.repo_name):
            raise ConfigurationError(f"Invalid repository name: {self.github_config.repo_name}")

        # Validate repository owner format (allow alphanumeric, dots, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9._-]+$', self.github_config.repo_owner):
            raise ConfigurationError(f"Invalid repository owner: {self.github_config.repo_owner}")

    def fetch_issues(self, since: Optional[str] = None, state: str = "all") -> List[Dict[str, Any]]:
        """
        Fetch issues from GitHub repository.

        Args:
            since: ISO 8601 timestamp to fetch issues updated since this time
            state: Issue state filter ('open', 'closed', 'all')

        Returns:
            List of issue dictionaries from GitHub API

        Raises:
            GitHubSyncError: If fetching issues fails
            ConfigurationError: If client is not initialized
        """
        if not self.client:
            raise ConfigurationError("GitHub client not initialized - check configuration and sync settings")

        # Validate inputs
        valid_states = {'open', 'closed', 'all'}
        if state not in valid_states:
            raise SyncValidationError(f"Invalid state '{state}'. Must be one of: {', '.join(valid_states)}")

        self.logger.info(f"Fetching issues with state='{state}'" + (f", since='{since}'" if since else ""))

        try:
            endpoint = f"/repos/{self.github_config.repo_owner}/{self.github_config.repo_name}/issues"
            params = {
                "state": state,
                "sort": "updated",
                "direction": "asc"
            }

            if since:
                params["since"] = since

            issues = []
            issue_count = 0
            for issue in self.client._paginate_request("GET", endpoint, params):
                # Filter out pull requests (GitHub API includes them in issues endpoint)
                if "pull_request" not in issue:
                    issues.append(issue)
                    issue_count += 1

            self.logger.info(f"Successfully fetched {issue_count} issues from GitHub")
            return issues

        except AuthenticationError as e:
            raise ConfigurationError(f"GitHub authentication failed: {e}")
        except AuthorizationError as e:
            raise ConfigurationError(f"GitHub access denied: {e}")
        except NotFoundError as e:
            raise ConfigurationError(f"Repository not found: {self.github_config.repo_owner}/{self.github_config.repo_name}")
        except RateLimitError as e:
            raise GitHubSyncError(f"GitHub rate limit exceeded: {e}")
        except NetworkError as e:
            raise GitHubSyncError(f"Network error while fetching issues: {e}")
        except ServerError as e:
            raise GitHubSyncError(f"GitHub server error: {e}")
        except GitHubError as e:
            raise GitHubSyncError(f"Failed to fetch issues from GitHub: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching issues: {str(e)}")
            raise GitHubSyncError(f"Unexpected error fetching issues: {str(e)}")

    def parse_issue_metadata(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GitHub issue data into our database schema format.

        Args:
            issue: Raw issue data from GitHub API

        Returns:
            Dictionary with parsed metadata matching our database schema
        """
        # Extract labels
        labels = [label["name"] for label in issue.get("labels", [])]

        # Extract assignees
        assignees = [assignee["login"] for assignee in issue.get("assignees", [])]

        # Extract milestone
        milestone = None
        if issue.get("milestone"):
            milestone = issue["milestone"]["title"]

        # Extract project board data
        project_key_vals = {}
        try:
            # Fetch project data for this issue
            project_data = self.client.get_issue_project_items(issue["number"])
            if project_data:
                project_key_vals = project_data
        except Exception as e:
            self.logger.debug(f"Could not fetch project data for issue #{issue['number']}: {e}")

        return {
            "url": issue["html_url"],
            "num": issue["number"],
            "title": issue["title"],
            "labels": labels,
            "type": "issue",  # Could be enhanced to detect issue types from labels
            "assignees": assignees,
            "milestone": milestone,
            "project_key_vals": project_key_vals,
            "state": issue["state"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "closed_at": issue.get("closed_at"),
            "body": issue.get("body", "")
        }

    def find_matching_file(self, issue_num: int, issue_title: str, issue_body: str) -> Optional[int]:
        """
        Find local markdown file that matches a GitHub issue.

        Args:
            issue_num: GitHub issue number
            issue_title: Issue title
            issue_body: Issue body content

        Returns:
            File ID from database if match found, None otherwise

        Raises:
            DatabaseError: If database operation fails
            SyncValidationError: If inputs are invalid
        """
        # Validate inputs
        if not isinstance(issue_num, int) or issue_num <= 0:
            raise SyncValidationError(f"Invalid issue number: {issue_num}")

        self.logger.debug(f"Finding matching file for issue #{issue_num}: {issue_title}")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                # Strategy 1: Look for issue number in filename or path
                # Pattern: issues/123-something.md or issues/issue-123.md etc.
                cursor.execute("""
                    SELECT f.id, f.path, f.filename
                    FROM files f
                    JOIN github g ON f.id = g.md_file_id
                    WHERE g.is_issue = 1
                """)

                for file_id, path, filename in cursor.fetchall():
                    # Check for issue number in path or filename
                    # Use multiple patterns to handle different formats:
                    # 1. Zero-padded numbers: 001, 002, etc.
                    # 2. Regular word boundaries: issue-123, feature-456

                    zero_padded_pattern = rf'0*{issue_num}\b'  # Matches 001, 0001, etc.
                    word_boundary_pattern = rf'\b{issue_num}\b'  # Matches 123 in feature-123

                    path_match = (re.search(zero_padded_pattern, path) or
                                 re.search(word_boundary_pattern, path))
                    filename_match = (re.search(zero_padded_pattern, filename) or
                                     re.search(word_boundary_pattern, filename))

                    if path_match or filename_match:
                        self.logger.debug(f"Found matching file: {path} (ID: {file_id})")
                        return file_id

                # Strategy 2: Look for GitHub URL in file content
                # This would require reading file contents - implement if needed

                # Strategy 3: Look for existing mapping in database
                cursor.execute("SELECT md_file_id FROM github WHERE num = ?", (issue_num,))
                result = cursor.fetchone()
                if result:
                    self.logger.debug(f"Found existing mapping for issue #{issue_num} to file ID: {result[0]}")
                    return result[0]

                # No match found
                self.logger.debug(f"No matching file found for issue #{issue_num}")
                return None

            except sqlite3.Error as e:
                raise DatabaseError(f"Database query failed while finding matching file: {str(e)}")
            finally:
                conn.close()

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error finding matching file for issue #{issue_num}: {str(e)}")
            raise DatabaseError(f"Unexpected error finding matching file: {str(e)}")

    def update_issue_metadata(self, file_id: int, metadata: Dict[str, Any]) -> None:
        """
        Update GitHub metadata for a file in the database.

        Args:
            file_id: Database ID of the file
            metadata: Parsed issue metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if github entry exists for this file
            cursor.execute("SELECT id FROM github WHERE md_file_id = ?", (file_id,))
            github_entry = cursor.fetchone()

            if github_entry:
                # Update existing entry
                cursor.execute("""
                    UPDATE github SET
                        url = ?, num = ?, title = ?, labels = ?, type = ?,
                        assignees = ?, milestone = ?, project_key_vals = ?, state = ?,
                        created_at = ?, updated_at = ?, closed_at = ?, body = ?
                    WHERE md_file_id = ?
                """, (
                    metadata["url"], metadata["num"], metadata["title"],
                    ",".join(metadata["labels"]), metadata["type"],
                    ",".join(metadata["assignees"]), metadata["milestone"],
                    json.dumps(metadata.get("project_key_vals", {})), metadata["state"],
                    metadata["created_at"], metadata["updated_at"],
                    metadata["closed_at"], metadata["body"], file_id
                ))
            else:
                # This shouldn't happen in normal flow, but handle gracefully
                raise GitHubSyncError(f"No GitHub entry found for file ID {file_id}")

            conn.commit()

        finally:
            conn.close()

    def create_orphan_issue_entry(self, metadata: Dict[str, Any]) -> None:
        """
        Create a GitHub table entry for an issue that has no matching local file.

        Args:
            metadata: Parsed issue metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert with md_file_id = NULL to indicate orphaned issue
            cursor.execute("""
                INSERT INTO github (
                    md_file_id, is_issue, url, num, title, labels, type,
                    assignees, milestone, project_key_vals, state, created_at, updated_at,
                    closed_at, body
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                None, True, metadata["url"], metadata["num"], metadata["title"],
                ",".join(metadata["labels"]), metadata["type"],
                ",".join(metadata["assignees"]), metadata["milestone"],
                json.dumps(metadata.get("project_key_vals", {})),
                metadata["state"], metadata["created_at"], metadata["updated_at"],
                metadata["closed_at"], metadata["body"]
            ))

            conn.commit()

        finally:
            conn.close()

    def get_last_sync_time(self) -> Optional[str]:
        """
        Get the timestamp of the last successful sync.

        Returns:
            ISO 8601 timestamp string or None if no previous sync
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Create sync_status table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY,
                    last_sync_time TEXT NOT NULL,
                    sync_type TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Get the most recent GitHub issues sync
            cursor.execute("""
                SELECT last_sync_time FROM sync_status
                WHERE sync_type = 'github_issues'
                ORDER BY created_at DESC
                LIMIT 1
            """)

            result = cursor.fetchone()
            return result[0] if result else None

        finally:
            conn.close()

    def update_sync_time(self, sync_time: str) -> None:
        """
        Update the last sync timestamp.

        Args:
            sync_time: ISO 8601 timestamp string
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Ensure sync_status table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY,
                    last_sync_time TEXT NOT NULL,
                    sync_type TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                INSERT INTO sync_status (last_sync_time, sync_type)
                VALUES (?, 'github_issues')
            """, (sync_time,))

            conn.commit()

        finally:
            conn.close()

    def sync_issues(self, force_full_sync: bool = False) -> Dict[str, int]:
        """
        Synchronize GitHub issues with local database.

        Args:
            force_full_sync: If True, sync all issues regardless of last sync time

        Returns:
            Dictionary with sync statistics

        Raises:
            GitHubSyncError: If synchronization fails
            ConfigurationError: If sync is not enabled or misconfigured
            PartialSyncError: If sync completes with some errors
        """
        if not self.github_config.sync_enabled:
            raise ConfigurationError("GitHub sync is not enabled in configuration")

        sync_type = "full" if force_full_sync else "incremental"
        self.logger.info(f"Starting {sync_type} GitHub issues sync")

        # Check for resumable sync
        resumable_sync = self.sync_state.can_resume_sync(SyncOperation.GITHUB_TO_LOCAL)
        if resumable_sync and not force_full_sync:
            self.logger.info(f"Found resumable sync operation {resumable_sync.id}")
            sync_entry = resumable_sync
        else:
            # Start new sync operation
            metadata = {
                "sync_type": sync_type,
                "repo": f"{self.github_config.repo_owner}/{self.github_config.repo_name}"
            }
            sync_entry = self.sync_state.start_sync(SyncOperation.GITHUB_TO_LOCAL, metadata=metadata)

        try:
            # Determine sync parameters
            try:
                since = None if force_full_sync else self.get_last_sync_time()
                sync_start_time = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                raise DatabaseError(f"Failed to determine sync parameters: {str(e)}")

            # Fetch issues from GitHub
            try:
                issues = self.fetch_issues(since=since)
                # Update sync state with total items
                self.sync_state.update_sync_progress(
                    sync_entry.id,
                    metadata_updates={"total_issues": len(issues)}
                )
            except Exception as e:
                self.logger.error(f"Failed to fetch issues: {str(e)}")
                self.sync_state.complete_sync(sync_entry.id, SyncStatus.FAILED, str(e))
                raise

            # Track statistics
            stats = {
                "total_fetched": len(issues),
                "matched_files": 0,
                "orphaned_issues": 0,
                "updated_files": 0,
                "errors": 0
            }

            self.logger.info(f"Processing {len(issues)} issues")

            # Process each issue
            failed_issues = []
            processed_count = 0
            for i, issue in enumerate(issues):
                issue_num = issue.get('number', 'unknown')
                issue_title = issue.get('title', 'Unknown')

                try:
                    self.logger.debug(f"Processing issue #{issue_num} ({i+1}/{len(issues)}): {issue_title}")

                    # Update sync progress
                    self.sync_state.update_sync_progress(
                        sync_entry.id,
                        processed_items=processed_count,
                        current_item=f"issue-{issue_num}"
                    )

                    # Parse issue metadata
                    metadata = self.parse_issue_metadata(issue)

                    # Try to find matching local file
                    file_id = self.find_matching_file(
                        metadata["num"],
                        metadata["title"],
                        metadata["body"]
                    )

                    if file_id:
                        # Update existing file metadata
                        self.update_issue_metadata(file_id, metadata)
                        stats["matched_files"] += 1
                        stats["updated_files"] += 1
                        self.logger.debug(f"Updated metadata for issue #{issue_num} -> file ID {file_id}")
                    else:
                        # Create orphaned issue entry
                        self.create_orphan_issue_entry(metadata)
                        stats["orphaned_issues"] += 1
                        self.logger.debug(f"Created orphan entry for issue #{issue_num}")

                    processed_count += 1

                except Exception as e:
                    stats["errors"] += 1
                    error_msg = f"Error processing issue #{issue_num}: {str(e)}"
                    self.logger.error(error_msg)
                    failed_issues.append({
                        "issue_num": issue_num,
                        "issue_title": issue_title,
                        "error": str(e)
                    })

                    # Continue processing other issues unless it's a critical error
                    if isinstance(e, (ConfigurationError, DatabaseError)) and "database" in str(e).lower():
                        # Critical database error - stop processing
                        self.logger.error("Critical database error encountered, stopping sync")
                        break

            # Log final statistics
            self.logger.info(f"Sync completed: {stats['total_fetched']} fetched, "
                            f"{stats['matched_files']} matched, "
                            f"{stats['orphaned_issues']} orphaned, "
                            f"{stats['errors']} errors")

            # Log rate limit summary
            if self.client:
                self.client.log_rate_limit_summary()
                rate_stats = self.client.get_rate_limit_stats()
                stats.update({
                    "api_requests_made": rate_stats["requests_made"],
                    "rate_limit_hits": rate_stats["rate_limit_hits"],
                    "total_delay_time": rate_stats["total_delay_time"]
                })

            # Update sync timestamp on successful completion
            if stats["errors"] == 0:
                try:
                    self.update_sync_time(sync_start_time)
                    self.logger.info("Sync timestamp updated successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to update sync timestamp: {str(e)}")
                    # Don't fail the entire sync for this
            else:
                self.logger.warning(f"Sync completed with {stats['errors']} errors - timestamp not updated")

            # Complete sync operation
            if stats["errors"] == 0:
                self.sync_state.complete_sync(sync_entry.id, SyncStatus.COMPLETED)
            elif stats["errors"] < len(issues):
                # Partial success
                error_summary = f"{stats['errors']} of {len(issues)} issues failed"
                self.sync_state.complete_sync(sync_entry.id, SyncStatus.COMPLETED, error_summary)
            else:
                # Complete failure
                self.sync_state.complete_sync(sync_entry.id, SyncStatus.FAILED, f"All {stats['errors']} issues failed")

            # Raise PartialSyncError if there were errors but sync wasn't completely failed
            if stats["errors"] > 0 and stats["errors"] < len(issues):
                error_details = "; ".join([f"#{item['issue_num']}: {item['error']}" for item in failed_issues[:3]])
                if len(failed_issues) > 3:
                    error_details += f" and {len(failed_issues) - 3} more..."
                raise PartialSyncError(
                    f"Sync completed with {stats['errors']} errors: {error_details}",
                    stats
                )

            return stats

        except Exception as e:
            # Mark sync as failed on unhandled exception
            self.sync_state.complete_sync(sync_entry.id, SyncStatus.FAILED, str(e))
            raise