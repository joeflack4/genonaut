"""Tests for PostgreSQL fixtures module.

This test file verifies that the PostgreSQL test fixtures are working correctly.
Run with: pytest test/db/test_postgres_fixtures.py -v
"""

import pytest
from sqlalchemy import text

from test.db.postgres_fixtures import (
    postgres_session,
    postgres_session_no_rollback,
    verify_postgres_features,
    table_exists,
    count_rows,
    get_table_columns,
)
from genonaut.db.schema import User, ContentItem


class TestPostgresFixtures:
    """Test PostgreSQL fixtures functionality."""

    def test_postgres_session_basic(self, postgres_session):
        """Test basic PostgreSQL session functionality."""
        # Query should work
        result = postgres_session.execute(text("SELECT 1 AS value"))
        assert result.scalar() == 1

    def test_postgres_session_rollback(self, postgres_session):
        """Test that postgres_session automatically rolls back changes."""
        # Create a user
        user = User(username="test_rollback_user", email="rollback@test.com")
        postgres_session.add(user)
        postgres_session.commit()

        # Verify user exists in this session
        found = postgres_session.query(User).filter_by(username="test_rollback_user").first()
        assert found is not None
        assert found.username == "test_rollback_user"

        # After test, changes should be rolled back (verified by next test)

    def test_postgres_session_isolation(self, postgres_session):
        """Test that each test gets a clean database state."""
        # User from previous test should NOT exist
        user = postgres_session.query(User).filter_by(username="test_rollback_user").first()
        assert user is None, "Previous test's user should be rolled back"

    def test_postgres_features(self, postgres_session):
        """Test PostgreSQL-specific features verification."""
        features = verify_postgres_features(postgres_session)

        # JSONB should be supported
        assert features["jsonb"], "PostgreSQL should support JSONB"

        # Should support table inheritance
        assert features["inheritance"], "PostgreSQL should support table inheritance"

        # Partitioning depends on whether content_items_all is created
        # (may be False if migrations haven't been run)

    def test_table_exists_helper(self, postgres_session):
        """Test table_exists helper function."""
        # users table should exist
        assert table_exists(postgres_session, "users")

        # Non-existent table should return False
        assert not table_exists(postgres_session, "nonexistent_table_xyz")

    def test_get_table_columns_helper(self, postgres_session):
        """Test get_table_columns helper function."""
        columns = get_table_columns(postgres_session, "users")

        # users table should have standard columns
        assert "id" in columns
        assert "username" in columns
        assert "email" in columns
        assert "created_at" in columns

    def test_count_rows_helper(self, postgres_session):
        """Test count_rows helper function."""
        # Get initial count
        initial_count = count_rows(postgres_session, "users")
        assert isinstance(initial_count, int)
        assert initial_count >= 0

    def test_multiple_commits_in_test(self, postgres_session):
        """Test that multiple commits work within a test."""
        # First commit
        user1 = User(username="user1", email="user1@test.com")
        postgres_session.add(user1)
        postgres_session.commit()

        # Verify first user exists
        found1 = postgres_session.query(User).filter_by(username="user1").first()
        assert found1 is not None

        # Second commit
        user2 = User(username="user2", email="user2@test.com")
        postgres_session.add(user2)
        postgres_session.commit()

        # Verify both users exist
        found2 = postgres_session.query(User).filter_by(username="user2").first()
        assert found2 is not None

        # Both changes should be rolled back after test

    def test_postgres_jsonb_operations(self, postgres_session):
        """Test JSONB operations work correctly."""
        # Create user with JSONB preferences
        user = User(
            username="jsonb_test_user",
            email="jsonb@test.com",
            preferences={"theme": "dark", "language": "en", "notifications": {"email": True, "push": False}}
        )
        postgres_session.add(user)
        postgres_session.commit()

        # Query the user back
        result = postgres_session.query(User).filter_by(username="jsonb_test_user").first()

        # Verify JSONB data is correctly stored and retrieved
        assert result is not None
        assert result.username == "jsonb_test_user"
        assert result.preferences["theme"] == "dark"
        assert result.preferences["language"] == "en"
        assert result.preferences["notifications"]["email"] is True
        assert result.preferences["notifications"]["push"] is False


