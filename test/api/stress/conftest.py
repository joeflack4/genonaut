"""Shared fixtures for pagination stress tests."""

import pytest

# Import PostgreSQL test database fixture
from test.db.postgres_fixtures import postgres_session


@pytest.fixture(scope="function")
def db_session(postgres_session):
    """Database session fixture (now uses PostgreSQL).

    This is an alias for postgres_session to maintain backward compatibility
    with existing tests that use db_session.

    The session automatically rolls back after each test for isolation.
    """
    return postgres_session


@pytest.fixture(scope="function")
def large_db_session(postgres_session):
    """Database session optimized for large datasets (now uses PostgreSQL).

    This is an alias for postgres_session. PostgreSQL is already optimized
    for large datasets, so no additional configuration is needed.
    """
    return postgres_session