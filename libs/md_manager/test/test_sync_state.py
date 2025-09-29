"""Tests for sync state management."""

import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from md_manager.sync_state import (
    SyncStateManager, SyncStateEntry, SyncOperation, SyncStatus
)


class TestSyncStateManager:
    """Test cases for SyncStateManager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def state_manager(self, temp_db):
        """SyncStateManager instance for testing."""
        return SyncStateManager(temp_db)

    def test_sync_state_table_creation(self, temp_db):
        """Test that sync state table is created correctly."""
        manager = SyncStateManager(temp_db)
        # Table should exist and be accessible
        assert Path(temp_db).exists()

    def test_start_sync_operation(self, state_manager):
        """Test starting a new sync operation."""
        metadata = {"repo": "test/repo", "force": True}

        entry = state_manager.start_sync(
            SyncOperation.GITHUB_TO_LOCAL,
            total_items=100,
            metadata=metadata
        )

        assert entry.id is not None
        assert entry.operation == SyncOperation.GITHUB_TO_LOCAL
        assert entry.status == SyncStatus.STARTED
        assert entry.total_items == 100
        assert entry.processed_items == 0
        assert entry.failed_items == 0
        assert entry.metadata == metadata
        assert entry.started_at is not None
        assert entry.updated_at is not None

    def test_update_sync_progress(self, state_manager):
        """Test updating sync operation progress."""
        entry = state_manager.start_sync(SyncOperation.LOCAL_TO_GITHUB, total_items=50)

        state_manager.update_sync_progress(
            entry.id,
            processed_items=25,
            failed_items=2,
            current_item="issue-123.md",
            metadata_updates={"last_processed": "issue-122.md"}
        )

        updated_entry = state_manager.get_sync_state(entry.id)

        assert updated_entry.status == SyncStatus.IN_PROGRESS
        assert updated_entry.processed_items == 25
        assert updated_entry.failed_items == 2
        assert updated_entry.current_item == "issue-123.md"
        assert updated_entry.metadata["last_processed"] == "issue-122.md"

    def test_complete_sync_success(self, state_manager):
        """Test completing sync operation successfully."""
        entry = state_manager.start_sync(SyncOperation.BIDIRECTIONAL)

        state_manager.complete_sync(entry.id, SyncStatus.COMPLETED)

        completed_entry = state_manager.get_sync_state(entry.id)

        assert completed_entry.status == SyncStatus.COMPLETED
        assert completed_entry.completed_at is not None
        assert completed_entry.error_message is None

    def test_complete_sync_with_error(self, state_manager):
        """Test completing sync operation with error."""
        entry = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)

        error_message = "Network timeout occurred"
        state_manager.complete_sync(entry.id, SyncStatus.FAILED, error_message)

        failed_entry = state_manager.get_sync_state(entry.id)

        assert failed_entry.status == SyncStatus.FAILED
        assert failed_entry.completed_at is not None
        assert failed_entry.error_message == error_message

    def test_get_sync_state_nonexistent(self, state_manager):
        """Test getting state for non-existent sync operation."""
        entry = state_manager.get_sync_state(99999)
        assert entry is None

    def test_get_active_syncs(self, state_manager):
        """Test getting active sync operations."""
        # Start multiple syncs
        entry1 = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)
        entry2 = state_manager.start_sync(SyncOperation.LOCAL_TO_GITHUB)
        entry3 = state_manager.start_sync(SyncOperation.BIDIRECTIONAL)

        # Progress one sync
        state_manager.update_sync_progress(entry2.id, processed_items=10)

        # Complete one sync
        state_manager.complete_sync(entry3.id, SyncStatus.COMPLETED)

        active_syncs = state_manager.get_active_syncs()

        assert len(active_syncs) == 2
        active_ids = {sync.id for sync in active_syncs}
        assert entry1.id in active_ids
        assert entry2.id in active_ids
        assert entry3.id not in active_ids

    def test_get_recent_syncs(self, state_manager):
        """Test getting recent sync operations."""
        # Start multiple syncs with small delays
        entries = []
        for i in range(5):
            entry = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)
            entries.append(entry)
            time.sleep(0.01)

        recent_syncs = state_manager.get_recent_syncs(limit=3)

        assert len(recent_syncs) == 3
        # Should be in reverse chronological order (newest first)
        assert recent_syncs[0].id == entries[-1].id
        assert recent_syncs[1].id == entries[-2].id
        assert recent_syncs[2].id == entries[-3].id

    def test_cancel_active_sync(self, state_manager):
        """Test cancelling an active sync operation."""
        entry = state_manager.start_sync(SyncOperation.LOCAL_TO_GITHUB)
        state_manager.update_sync_progress(entry.id, processed_items=5)

        success = state_manager.cancel_sync(entry.id)
        assert success is True

        cancelled_entry = state_manager.get_sync_state(entry.id)
        assert cancelled_entry.status == SyncStatus.CANCELLED
        assert cancelled_entry.completed_at is not None

    def test_cancel_completed_sync(self, state_manager):
        """Test that completed sync cannot be cancelled."""
        entry = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)
        state_manager.complete_sync(entry.id, SyncStatus.COMPLETED)

        success = state_manager.cancel_sync(entry.id)
        assert success is False

        # Status should remain completed
        entry_after = state_manager.get_sync_state(entry.id)
        assert entry_after.status == SyncStatus.COMPLETED

    def test_cancel_nonexistent_sync(self, state_manager):
        """Test cancelling non-existent sync operation."""
        success = state_manager.cancel_sync(99999)
        assert success is False

    def test_cleanup_old_syncs(self, state_manager):
        """Test cleaning up old sync operations."""
        # Create some old completed syncs by manipulating timestamps
        import sqlite3

        entry1 = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)
        entry2 = state_manager.start_sync(SyncOperation.LOCAL_TO_GITHUB)
        entry3 = state_manager.start_sync(SyncOperation.BIDIRECTIONAL)

        state_manager.complete_sync(entry1.id, SyncStatus.COMPLETED)
        state_manager.complete_sync(entry2.id, SyncStatus.FAILED)
        # Leave entry3 active

        # Manually update timestamps to make them old
        old_date = (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()

        with sqlite3.connect(state_manager.db_path) as conn:
            conn.execute("""
                UPDATE sync_state
                SET completed_at = ?
                WHERE id IN (?, ?)
            """, (old_date, entry1.id, entry2.id))
            conn.commit()

        removed_count = state_manager.cleanup_old_syncs(days=30)

        assert removed_count == 2

        # Verify entries are removed
        assert state_manager.get_sync_state(entry1.id) is None
        assert state_manager.get_sync_state(entry2.id) is None
        # Active sync should remain
        assert state_manager.get_sync_state(entry3.id) is not None

    def test_can_resume_sync(self, state_manager):
        """Test checking for resumable sync operations."""
        # No active syncs initially
        resumable = state_manager.can_resume_sync(SyncOperation.GITHUB_TO_LOCAL)
        assert resumable is None

        # Start a sync
        entry = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)

        # Should be resumable
        resumable = state_manager.can_resume_sync(SyncOperation.GITHUB_TO_LOCAL)
        assert resumable is not None
        assert resumable.id == entry.id

        # Different operation should not be resumable
        resumable_other = state_manager.can_resume_sync(SyncOperation.LOCAL_TO_GITHUB)
        assert resumable_other is None

        # Complete the sync
        state_manager.complete_sync(entry.id, SyncStatus.COMPLETED)

        # Should no longer be resumable
        resumable_after = state_manager.can_resume_sync(SyncOperation.GITHUB_TO_LOCAL)
        assert resumable_after is None

    def test_get_sync_statistics(self, state_manager):
        """Test getting sync operation statistics."""
        # Create various sync operations
        entry1 = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)
        entry2 = state_manager.start_sync(SyncOperation.LOCAL_TO_GITHUB)
        entry3 = state_manager.start_sync(SyncOperation.BIDIRECTIONAL)
        entry4 = state_manager.start_sync(SyncOperation.GITHUB_TO_LOCAL)

        # Complete some operations
        state_manager.complete_sync(entry1.id, SyncStatus.COMPLETED)
        state_manager.complete_sync(entry2.id, SyncStatus.FAILED)
        # Leave entry3 and entry4 active

        stats = state_manager.get_sync_statistics()

        assert stats["status_counts"][SyncStatus.COMPLETED.value] == 1
        assert stats["status_counts"][SyncStatus.FAILED.value] == 1
        assert stats["status_counts"][SyncStatus.STARTED.value] == 2

        assert stats["operation_counts"][SyncOperation.GITHUB_TO_LOCAL.value] == 2
        assert stats["operation_counts"][SyncOperation.LOCAL_TO_GITHUB.value] == 1
        assert stats["operation_counts"][SyncOperation.BIDIRECTIONAL.value] == 1

        assert stats["active_syncs"] == 2
        assert "average_duration_seconds" in stats


class TestSyncStateEntry:
    """Test cases for SyncStateEntry dataclass."""

    def test_sync_state_entry_creation(self):
        """Test SyncStateEntry creation with all fields."""
        now = datetime.now(timezone.utc)
        metadata = {"test": "data"}

        entry = SyncStateEntry(
            id=1,
            operation=SyncOperation.GITHUB_TO_LOCAL,
            status=SyncStatus.IN_PROGRESS,
            started_at=now,
            updated_at=now,
            total_items=100,
            processed_items=50,
            failed_items=2,
            current_item="file.md",
            metadata=metadata
        )

        assert entry.id == 1
        assert entry.operation == SyncOperation.GITHUB_TO_LOCAL
        assert entry.status == SyncStatus.IN_PROGRESS
        assert entry.total_items == 100
        assert entry.processed_items == 50
        assert entry.failed_items == 2
        assert entry.current_item == "file.md"
        assert entry.metadata == metadata

    def test_sync_state_entry_minimal(self):
        """Test SyncStateEntry creation with minimal fields."""
        now = datetime.now(timezone.utc)

        entry = SyncStateEntry(
            id=None,
            operation=SyncOperation.LOCAL_TO_GITHUB,
            status=SyncStatus.STARTED,
            started_at=now,
            updated_at=now
        )

        assert entry.id is None
        assert entry.operation == SyncOperation.LOCAL_TO_GITHUB
        assert entry.status == SyncStatus.STARTED
        assert entry.completed_at is None
        assert entry.total_items is None
        assert entry.processed_items == 0
        assert entry.failed_items == 0
        assert entry.current_item is None
        assert entry.error_message is None
        assert entry.metadata == {}

    def test_sync_state_entry_metadata_initialization(self):
        """Test that metadata is initialized to empty dict when None."""
        now = datetime.now(timezone.utc)

        entry = SyncStateEntry(
            id=1,
            operation=SyncOperation.BIDIRECTIONAL,
            status=SyncStatus.STARTED,
            started_at=now,
            updated_at=now,
            metadata=None
        )

        assert entry.metadata == {}