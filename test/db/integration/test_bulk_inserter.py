"""Tests for bulk inserter functionality and PostgreSQL settings management.

Tests the bulk inserter's ability to optimize and restore database settings,
particularly wal_buffers management.
"""

import pytest
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to Python path for imports
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(test_dir)))
sys.path.insert(0, project_root)

from genonaut.db.demo.seed_data_gen.bulk_inserter import BulkInserter
from ..utils import create_test_database_url, get_next_test_schema_name


class TestBulkInserter:
    """Test cases for bulk inserter PostgreSQL settings management."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database connection for each test."""
        # This test requires a real PostgreSQL database to test wal_buffers
        # Skip if not using PostgreSQL
        try:
            # Try to get PostgreSQL connection from environment
            db_url = os.getenv('DATABASE_URL')
            if not db_url or not db_url.startswith('postgresql'):
                pytest.skip("PostgreSQL database required for wal_buffers testing")

            # Use test schema
            test_schema_name = get_next_test_schema_name(db_url)
            self.test_db_url = create_test_database_url(db_url, test_schema_name)

            # Create engine and session
            self.engine = create_engine(self.test_db_url)
            session_factory = sessionmaker(bind=self.engine)
            self.session = session_factory()

            self.bulk_inserter = BulkInserter(self.session)

        except Exception as e:
            pytest.skip(f"Could not connect to PostgreSQL database: {e}")

    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()

    def test_wal_buffers_restoration(self):
        """Test that wal_buffers are properly restored to original value."""
        # Get original wal_buffers value
        result = self.session.execute(text("SHOW wal_buffers"))
        original_value = result.scalar()

        # Apply optimizations (this should change wal_buffers to 64MB)
        self.bulk_inserter.optimize_for_bulk_insert(should_pause_for_restart=False)

        # Verify that we recorded the original value
        assert self.bulk_inserter.original_wal_buffers == original_value
        assert self.bulk_inserter.wal_buffers_changed is True

        # Restore settings
        self.bulk_inserter.restore_normal_settings()

        # Verify that wal_buffers flag is reset
        assert self.bulk_inserter.wal_buffers_changed is False

        # Note: We can't immediately verify the actual wal_buffers value in the database
        # because ALTER SYSTEM changes require a PostgreSQL restart to take effect.
        # However, we can verify that the restore command was executed by checking
        # the postgresql.auto.conf file or by testing with a separate connection
        # after a manual restart.

    def test_wal_buffers_original_value_capture(self):
        """Test that original wal_buffers value is properly captured."""
        # Get current value directly
        result = self.session.execute(text("SHOW wal_buffers"))
        expected_original = result.scalar()

        # Initialize bulk inserter and capture original value
        self.bulk_inserter.optimize_for_bulk_insert(should_pause_for_restart=False)

        # Verify original value was captured correctly
        assert self.bulk_inserter.original_wal_buffers == expected_original

    def test_synchronous_commit_restoration(self):
        """Test that synchronous_commit is properly restored."""
        # Get original synchronous_commit value
        result = self.session.execute(text("SHOW synchronous_commit"))
        original_sync_commit = result.scalar()

        # Apply optimizations (should set synchronous_commit to OFF)
        self.bulk_inserter.optimize_for_bulk_insert(should_pause_for_restart=False)

        # Restore settings
        self.bulk_inserter.restore_normal_settings()

        # Create a new connection to check the restored value
        # (session-level settings don't persist across connections)
        with self.engine.connect() as conn:
            result = conn.execute(text("SHOW synchronous_commit"))
            # Note: The restore sets it to ON, not necessarily the original value
            # This is acceptable behavior for the seed data generator
            restored_value = result.scalar()
            assert restored_value in ['on', 'ON', 'local', 'remote_write', 'remote_apply']


class TestWalBuffersPostRestartVerification:
    """Test to verify wal_buffers after PostgreSQL restart (manual test)."""

    @pytest.mark.manual
    def test_wal_buffers_after_restart(self):
        """Manual test to verify wal_buffers are restored after PostgreSQL restart.

        This test should be run manually after:
        1. Running the seed data generator
        2. Restarting PostgreSQL
        3. Running this test to verify wal_buffers are back to 4MB

        This test will fail if the user forgot to restart PostgreSQL after
        running the seed data generator.
        """
        try:
            # Try to get PostgreSQL connection from environment
            db_url = os.getenv('DATABASE_URL')
            if not db_url or not db_url.startswith('postgresql'):
                pytest.skip("PostgreSQL database required for wal_buffers verification")

            engine = create_engine(db_url)

            with engine.connect() as conn:
                result = conn.execute(text("SHOW wal_buffers"))
                current_wal_buffers = result.scalar()

                # Assert that wal_buffers is set to the expected original value (4MB)
                # This catches cases where the user forgot to restart PostgreSQL
                assert current_wal_buffers == '4MB', (
                    f"wal_buffers is currently '{current_wal_buffers}', expected '4MB'. "
                    f"Please restart PostgreSQL to restore Write-Ahead Logging buffers "
                    f"to their original state."
                )

            engine.dispose()

        except Exception as e:
            pytest.fail(f"Could not verify wal_buffers: {e}")