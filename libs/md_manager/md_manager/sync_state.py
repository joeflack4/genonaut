"""Sync state management for resuming interrupted operations."""

import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class SyncOperation(Enum):
    """Types of sync operations."""
    GITHUB_TO_LOCAL = "github_to_local"
    LOCAL_TO_GITHUB = "local_to_github"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """Sync operation status."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SyncStateEntry:
    """Represents a sync operation state."""
    id: Optional[int]
    operation: SyncOperation
    status: SyncStatus
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    total_items: Optional[int] = None
    processed_items: int = 0
    failed_items: int = 0
    current_item: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}


class SyncStateManager:
    """Manages sync operation state for resuming interrupted operations."""

    def __init__(self, db_path: str):
        """
        Initialize sync state manager.

        Args:
            db_path: Path to the database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_sync_state_table()

    def _init_sync_state_table(self) -> None:
        """Initialize the sync state table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_items INTEGER,
                    processed_items INTEGER DEFAULT 0,
                    failed_items INTEGER DEFAULT 0,
                    current_item TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_state_operation ON sync_state(operation)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_state_status ON sync_state(status)
            """)
            conn.commit()

    def start_sync(self, operation: SyncOperation, total_items: Optional[int] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> SyncStateEntry:
        """
        Start a new sync operation.

        Args:
            operation: Type of sync operation
            total_items: Total number of items to process
            metadata: Additional metadata for the operation

        Returns:
            SyncStateEntry for the new operation
        """
        now = datetime.now(timezone.utc)

        entry = SyncStateEntry(
            id=None,
            operation=operation,
            status=SyncStatus.STARTED,
            started_at=now,
            updated_at=now,
            total_items=total_items,
            metadata=metadata or {}
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_state
                (operation, status, started_at, updated_at, total_items, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                operation.value,
                SyncStatus.STARTED.value,
                now.isoformat(),
                now.isoformat(),
                total_items,
                json.dumps(metadata or {})
            ))
            entry.id = cursor.lastrowid
            conn.commit()

        self.logger.info(f"Started sync operation {operation.value} with ID {entry.id}")
        return entry

    def update_sync_progress(self, sync_id: int, processed_items: Optional[int] = None,
                           failed_items: Optional[int] = None, current_item: Optional[str] = None,
                           metadata_updates: Optional[Dict[str, Any]] = None) -> None:
        """
        Update sync operation progress.

        Args:
            sync_id: Sync operation ID
            processed_items: Number of items processed
            failed_items: Number of items that failed
            current_item: Current item being processed
            metadata_updates: Updates to metadata
        """
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            # Get current state
            cursor = conn.cursor()
            cursor.execute("""
                SELECT processed_items, failed_items, metadata
                FROM sync_state WHERE id = ?
            """, (sync_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Sync operation {sync_id} not found")

            current_processed, current_failed, current_metadata_json = row
            current_metadata = json.loads(current_metadata_json or "{}")

            # Update values
            new_processed = processed_items if processed_items is not None else current_processed
            new_failed = failed_items if failed_items is not None else current_failed

            if metadata_updates:
                current_metadata.update(metadata_updates)

            # Update database
            cursor.execute("""
                UPDATE sync_state
                SET status = ?, updated_at = ?, processed_items = ?,
                    failed_items = ?, current_item = ?, metadata = ?
                WHERE id = ?
            """, (
                SyncStatus.IN_PROGRESS.value,
                now.isoformat(),
                new_processed,
                new_failed,
                current_item,
                json.dumps(current_metadata),
                sync_id
            ))
            conn.commit()

    def complete_sync(self, sync_id: int, status: SyncStatus = SyncStatus.COMPLETED,
                     error_message: Optional[str] = None) -> None:
        """
        Mark sync operation as completed.

        Args:
            sync_id: Sync operation ID
            status: Final status of the operation
            error_message: Error message if operation failed
        """
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sync_state
                SET status = ?, updated_at = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            """, (
                status.value,
                now.isoformat(),
                now.isoformat(),
                error_message,
                sync_id
            ))
            conn.commit()

        self.logger.info(f"Completed sync operation {sync_id} with status {status.value}")

    def get_sync_state(self, sync_id: int) -> Optional[SyncStateEntry]:
        """
        Get sync operation state.

        Args:
            sync_id: Sync operation ID

        Returns:
            SyncStateEntry or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_state WHERE id = ?
            """, (sync_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_sync_entry(row)

    def get_active_syncs(self) -> List[SyncStateEntry]:
        """
        Get all active (not completed/failed/cancelled) sync operations.

        Returns:
            List of active sync operations
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_state
                WHERE status IN (?, ?)
                ORDER BY started_at ASC
            """, (SyncStatus.STARTED.value, SyncStatus.IN_PROGRESS.value))

            return [self._row_to_sync_entry(row) for row in cursor.fetchall()]

    def get_recent_syncs(self, limit: int = 10) -> List[SyncStateEntry]:
        """
        Get recent sync operations.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent sync operations
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_state
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))

            return [self._row_to_sync_entry(row) for row in cursor.fetchall()]

    def cancel_sync(self, sync_id: int) -> bool:
        """
        Cancel an active sync operation.

        Args:
            sync_id: Sync operation ID

        Returns:
            True if sync was cancelled, False if not found or not active
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sync_state
                SET status = ?, updated_at = ?, completed_at = ?
                WHERE id = ? AND status IN (?, ?)
            """, (
                SyncStatus.CANCELLED.value,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                sync_id,
                SyncStatus.STARTED.value,
                SyncStatus.IN_PROGRESS.value
            ))

            success = cursor.rowcount > 0
            conn.commit()

            if success:
                self.logger.info(f"Cancelled sync operation {sync_id}")

            return success

    def cleanup_old_syncs(self, days: int = 30) -> int:
        """
        Clean up old sync operation records.

        Args:
            days: Remove records older than this many days

        Returns:
            Number of records removed
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sync_state
                WHERE completed_at IS NOT NULL
                AND completed_at < ?
                AND status IN (?, ?, ?)
            """, (
                cutoff_date.isoformat(),
                SyncStatus.COMPLETED.value,
                SyncStatus.FAILED.value,
                SyncStatus.CANCELLED.value
            ))

            removed_count = cursor.rowcount
            conn.commit()

            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old sync records")

            return removed_count

    def _row_to_sync_entry(self, row: sqlite3.Row) -> SyncStateEntry:
        """Convert database row to SyncStateEntry."""
        return SyncStateEntry(
            id=row['id'],
            operation=SyncOperation(row['operation']),
            status=SyncStatus(row['status']),
            started_at=datetime.fromisoformat(row['started_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            total_items=row['total_items'],
            processed_items=row['processed_items'],
            failed_items=row['failed_items'],
            current_item=row['current_item'],
            error_message=row['error_message'],
            metadata=json.loads(row['metadata'] or "{}")
        )

    def can_resume_sync(self, operation: SyncOperation) -> Optional[SyncStateEntry]:
        """
        Check if there's an interrupted sync that can be resumed.

        Args:
            operation: Type of sync operation

        Returns:
            SyncStateEntry if resumable sync found, None otherwise
        """
        active_syncs = self.get_active_syncs()

        for sync_entry in active_syncs:
            if sync_entry.operation == operation:
                return sync_entry

        return None

    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get sync operation statistics.

        Returns:
            Dictionary with sync statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total syncs by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM sync_state
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Total syncs by operation
            cursor.execute("""
                SELECT operation, COUNT(*) as count
                FROM sync_state
                GROUP BY operation
            """)
            operation_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Average processing time for completed syncs
            cursor.execute("""
                SELECT AVG(julianday(completed_at) - julianday(started_at)) * 24 * 60 * 60 as avg_duration
                FROM sync_state
                WHERE status = ? AND completed_at IS NOT NULL
            """, (SyncStatus.COMPLETED.value,))

            avg_duration_row = cursor.fetchone()
            avg_duration = avg_duration_row[0] if avg_duration_row[0] else 0

            return {
                "status_counts": status_counts,
                "operation_counts": operation_counts,
                "average_duration_seconds": round(avg_duration, 2),
                "active_syncs": len(self.get_active_syncs())
            }