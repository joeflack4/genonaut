"""Bidirectional synchronization coordinator for md-manager.

This module orchestrates synchronization between local markdown files and GitHub issues
in both directions, ensuring data consistency and proper conflict resolution.

Key Features:
- Coordinate GitHub → Local and Local → GitHub sync operations
- Manage sync timing and ordering to prevent conflicts
- Provide unified sync interface for CLI and programmatic use
- Handle complex bidirectional conflict scenarios
- Maintain sync state and history tracking
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

from .github_sync import GitHubIssueSyncer, GitHubSyncError
from .local_sync import LocalToGitHubSyncer, LocalSyncError, ConflictResolution, SyncConflict
from .config import GitHubConfig


class SyncMode(Enum):
    """Synchronization mode options."""
    GITHUB_TO_LOCAL = "github_to_local"
    LOCAL_TO_GITHUB = "local_to_github"
    BIDIRECTIONAL = "bidirectional"


class SyncStrategy(Enum):
    """Bidirectional sync strategy options."""
    GITHUB_FIRST = "github_first"  # Pull from GitHub first, then push local changes
    LOCAL_FIRST = "local_first"    # Push local changes first, then pull from GitHub
    TIMESTAMP_BASED = "timestamp_based"  # Use timestamps to determine sync order
    CONSERVATIVE = "conservative"  # Minimize conflicts, prefer manual resolution


@dataclass
class SyncResult:
    """Result of a bidirectional synchronization operation."""
    mode: SyncMode
    github_to_local_stats: Optional[Dict[str, Any]] = None
    local_to_github_stats: Optional[Dict[str, Any]] = None
    conflicts: List[SyncConflict] = None
    total_duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class BidirectionalSyncError(GitHubSyncError):
    """Exception raised during bidirectional synchronization operations."""
    pass


class BidirectionalSyncer:
    """
    Orchestrates bidirectional synchronization between local files and GitHub issues.

    This class manages the coordination of GitHub → Local and Local → GitHub sync
    operations to ensure data consistency and proper conflict resolution.
    """

    def __init__(self, db_path: str, github_config: GitHubConfig):
        """
        Initialize the bidirectional syncer.

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

        # Initialize sync components
        self.github_syncer = GitHubIssueSyncer(db_path, github_config)
        self.local_syncer = LocalToGitHubSyncer(db_path, github_config)

        self.logger.info("Initialized bidirectional syncer")

    def sync_github_to_local(
        self,
        force_full_sync: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Perform GitHub → Local synchronization.

        Args:
            force_full_sync: If True, sync all issues regardless of last sync time
            dry_run: If True, show what would be synced without making changes

        Returns:
            Dictionary with sync statistics

        Raises:
            GitHubSyncError: If GitHub → Local sync fails
        """
        self.logger.info("Starting GitHub → Local synchronization")

        if dry_run:
            # For dry run, we need to simulate the GitHub sync behavior
            self.logger.info("DRY RUN: GitHub → Local sync simulation")
            since = None if force_full_sync else self.github_syncer.get_last_sync_time()
            issues = self.github_syncer.fetch_issues(since=since)

            return {
                "total_fetched": len(issues),
                "matched_files": 0,  # Would need to simulate file matching
                "orphaned_issues": 0,
                "updated_files": 0,
                "errors": 0,
                "dry_run": True
            }

        return self.github_syncer.sync_issues(force_full_sync=force_full_sync)

    def sync_local_to_github(
        self,
        conflict_resolution: ConflictResolution = ConflictResolution.LOCAL_WINS,
        dry_run: bool = False,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform Local → GitHub synchronization.

        Args:
            conflict_resolution: Strategy for resolving conflicts
            dry_run: If True, show what would be synced without making changes
            since: ISO 8601 timestamp to sync changes since this time

        Returns:
            Dictionary with sync statistics

        Raises:
            LocalSyncError: If Local → GitHub sync fails
        """
        self.logger.info("Starting Local → GitHub synchronization")

        return self.local_syncer.sync_to_github(
            conflict_resolution=conflict_resolution,
            dry_run=dry_run,
            since=since
        )

    def sync_bidirectional(
        self,
        strategy: SyncStrategy = SyncStrategy.GITHUB_FIRST,
        conflict_resolution: ConflictResolution = ConflictResolution.LOCAL_WINS,
        force_full_sync: bool = False,
        dry_run: bool = False
    ) -> SyncResult:
        """
        Perform bidirectional synchronization.

        Args:
            strategy: Bidirectional sync strategy
            conflict_resolution: Strategy for resolving conflicts
            force_full_sync: If True, sync all issues regardless of last sync time
            dry_run: If True, show what would be synced without making changes

        Returns:
            SyncResult with detailed statistics and outcomes

        Raises:
            BidirectionalSyncError: If bidirectional sync fails
        """
        start_time = datetime.now()
        self.logger.info(f"Starting bidirectional synchronization with strategy: {strategy.value}")

        result = SyncResult(
            mode=SyncMode.BIDIRECTIONAL,
            conflicts=[]
        )

        try:
            if strategy == SyncStrategy.GITHUB_FIRST:
                # Pull from GitHub first, then push local changes
                self.logger.info("Phase 1: GitHub → Local sync")
                result.github_to_local_stats = self.sync_github_to_local(
                    force_full_sync=force_full_sync,
                    dry_run=dry_run
                )

                self.logger.info("Phase 2: Local → GitHub sync")
                result.local_to_github_stats = self.sync_local_to_github(
                    conflict_resolution=conflict_resolution,
                    dry_run=dry_run
                )

            elif strategy == SyncStrategy.LOCAL_FIRST:
                # Push local changes first, then pull from GitHub
                self.logger.info("Phase 1: Local → GitHub sync")
                result.local_to_github_stats = self.sync_local_to_github(
                    conflict_resolution=conflict_resolution,
                    dry_run=dry_run
                )

                self.logger.info("Phase 2: GitHub → Local sync")
                result.github_to_local_stats = self.sync_github_to_local(
                    force_full_sync=force_full_sync,
                    dry_run=dry_run
                )

            elif strategy == SyncStrategy.TIMESTAMP_BASED:
                # Analyze timestamps to determine optimal sync order
                sync_order = self._determine_timestamp_based_order()

                if sync_order == "github_first":
                    self.logger.info("Timestamp analysis suggests GitHub → Local first")
                    result.github_to_local_stats = self.sync_github_to_local(
                        force_full_sync=force_full_sync,
                        dry_run=dry_run
                    )
                    result.local_to_github_stats = self.sync_local_to_github(
                        conflict_resolution=conflict_resolution,
                        dry_run=dry_run
                    )
                else:
                    self.logger.info("Timestamp analysis suggests Local → GitHub first")
                    result.local_to_github_stats = self.sync_local_to_github(
                        conflict_resolution=conflict_resolution,
                        dry_run=dry_run
                    )
                    result.github_to_local_stats = self.sync_github_to_local(
                        force_full_sync=force_full_sync,
                        dry_run=dry_run
                    )

            elif strategy == SyncStrategy.CONSERVATIVE:
                # Use conservative approach with extensive conflict detection
                self.logger.info("Using conservative sync strategy")
                result = self._conservative_bidirectional_sync(
                    conflict_resolution=conflict_resolution,
                    force_full_sync=force_full_sync,
                    dry_run=dry_run
                )

            # Calculate total duration
            end_time = datetime.now()
            result.total_duration = (end_time - start_time).total_seconds()

            # Log summary
            self._log_bidirectional_summary(result)

            return result

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.total_duration = (datetime.now() - start_time).total_seconds()

            self.logger.error(f"Bidirectional sync failed: {str(e)}")
            raise BidirectionalSyncError(f"Bidirectional sync failed: {str(e)}")

    def _determine_timestamp_based_order(self) -> str:
        """
        Analyze timestamps to determine optimal sync order.

        Returns:
            "github_first" or "local_first" based on timestamp analysis
        """
        try:
            # Get last sync times for both directions
            github_last_sync = self.github_syncer.get_last_sync_time()

            # For simplicity, if we haven't synced from GitHub recently, do that first
            if not github_last_sync:
                return "github_first"

            # Parse timestamp
            github_sync_time = datetime.fromisoformat(github_last_sync.replace('Z', '+00:00'))
            hours_since_github_sync = (datetime.now(timezone.utc) - github_sync_time).total_seconds() / 3600

            # If GitHub sync is more than 1 hour old, sync from GitHub first
            if hours_since_github_sync > 1:
                return "github_first"
            else:
                return "local_first"

        except Exception as e:
            self.logger.warning(f"Failed to analyze timestamps: {e}. Defaulting to github_first")
            return "github_first"

    def _conservative_bidirectional_sync(
        self,
        conflict_resolution: ConflictResolution,
        force_full_sync: bool,
        dry_run: bool
    ) -> SyncResult:
        """
        Perform conservative bidirectional sync with extensive conflict detection.

        This approach minimizes the risk of data loss by detecting conflicts
        before making any changes and requiring manual resolution when needed.
        """
        result = SyncResult(mode=SyncMode.BIDIRECTIONAL, conflicts=[])

        # Step 1: Detect potential conflicts before any sync
        self.logger.info("Phase 1: Pre-sync conflict detection")

        # Get local file changes
        local_changes = self.local_syncer.detect_file_changes()
        local_conflicts = self.local_syncer.detect_conflicts(local_changes)

        if local_conflicts and conflict_resolution == ConflictResolution.MANUAL:
            result.conflicts = local_conflicts
            result.success = False
            result.error_message = f"Manual resolution required for {len(local_conflicts)} conflicts"
            return result

        # Step 2: Perform GitHub → Local sync with conflict awareness
        self.logger.info("Phase 2: Conservative GitHub → Local sync")
        try:
            result.github_to_local_stats = self.sync_github_to_local(
                force_full_sync=force_full_sync,
                dry_run=dry_run
            )
        except Exception as e:
            result.success = False
            result.error_message = f"GitHub → Local sync failed: {str(e)}"
            return result

        # Step 3: Re-evaluate conflicts after GitHub sync
        if not dry_run:
            updated_local_changes = self.local_syncer.detect_file_changes()
            updated_conflicts = self.local_syncer.detect_conflicts(updated_local_changes)

            if updated_conflicts:
                self.logger.warning(f"New conflicts detected after GitHub sync: {len(updated_conflicts)}")
                result.conflicts.extend(updated_conflicts)

        # Step 4: Perform Local → GitHub sync if no blocking conflicts
        if not result.conflicts or conflict_resolution != ConflictResolution.MANUAL:
            self.logger.info("Phase 3: Conservative Local → GitHub sync")
            try:
                result.local_to_github_stats = self.sync_local_to_github(
                    conflict_resolution=conflict_resolution,
                    dry_run=dry_run
                )
            except Exception as e:
                result.success = False
                result.error_message = f"Local → GitHub sync failed: {str(e)}"
                return result

        return result

    def _log_bidirectional_summary(self, result: SyncResult) -> None:
        """Log a comprehensive summary of bidirectional sync results."""
        self.logger.info("=== Bidirectional Sync Summary ===")

        if result.github_to_local_stats:
            gh_stats = result.github_to_local_stats
            self.logger.info(f"GitHub → Local: {gh_stats.get('total_fetched', 0)} issues, "
                           f"{gh_stats.get('matched_files', 0)} matched, "
                           f"{gh_stats.get('updated_files', 0)} updated")

        if result.local_to_github_stats:
            local_stats = result.local_to_github_stats
            self.logger.info(f"Local → GitHub: {local_stats.get('new_issues', 0)} created, "
                           f"{local_stats.get('updated_issues', 0)} updated, "
                           f"{local_stats.get('skipped_files', 0)} skipped")

        if result.conflicts:
            self.logger.warning(f"Conflicts: {len(result.conflicts)} unresolved")

        self.logger.info(f"Total duration: {result.total_duration:.2f}s")
        self.logger.info(f"Success: {result.success}")

        if result.error_message:
            self.logger.error(f"Error: {result.error_message}")

        self.logger.info("================================")

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current synchronization status.

        Returns:
            Dictionary with sync status information
        """
        try:
            github_last_sync = self.github_syncer.get_last_sync_time()

            # Get rate limit status if available
            rate_limit_status = None
            if self.github_syncer.client:
                rate_limit_status = self.github_syncer.client.get_rate_limit_status()

            return {
                "github_sync_enabled": self.github_config.sync_enabled,
                "last_github_sync": github_last_sync,
                "database_path": self.db_path,
                "repository": f"{self.github_config.repo_owner}/{self.github_config.repo_name}",
                "rate_limit_status": rate_limit_status
            }

        except Exception as e:
            self.logger.error(f"Failed to get sync status: {str(e)}")
            return {
                "error": str(e)
            }