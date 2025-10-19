"""Test to verify postgres_session fixture provides proper test isolation."""

import pytest
from genonaut.db.schema import User


class TestFixtureIsolation:
    """Test that postgres_session properly isolates tests."""

    def test_first_create_user(self, postgres_session):
        """First test creates a user with email test@isolation.com."""
        user = User(
            username="isolation_test_1",
            email="test@isolation.com",
            preferences={}
        )
        postgres_session.add(user)
        postgres_session.commit()

        # Verify user exists in this test
        found = postgres_session.query(User).filter_by(email="test@isolation.com").first()
        assert found is not None
        assert found.username == "isolation_test_1"

    def test_second_create_same_email(self, postgres_session):
        """Second test should be able to create user with same email (rollback should have happened)."""
        # This should NOT raise IntegrityError if rollback worked
        user = User(
            username="isolation_test_2",
            email="test@isolation.com",  # Same email as previous test
            preferences={}
        )
        postgres_session.add(user)
        postgres_session.commit()

        # Verify user exists in this test
        found = postgres_session.query(User).filter_by(email="test@isolation.com").first()
        assert found is not None
        assert found.username == "isolation_test_2"  # Should be THIS test's user

    def test_third_verify_isolation(self, postgres_session):
        """Third test verifies previous test data was rolled back."""
        # Should find no users with this email
        found = postgres_session.query(User).filter_by(email="test@isolation.com").first()
        assert found is None, "Previous test data should have been rolled back"
