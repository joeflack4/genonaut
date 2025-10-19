"""Shared fixtures for database integration tests.

The PostgreSQL test database must be initialized before running tests:
    make init-test
"""

import pytest

# Import PostgreSQL fixtures from parent conftest
# These are already available through test/db/conftest.py
from test.db.postgres_fixtures import postgres_session, postgres_engine


# Create alias for backward compatibility
@pytest.fixture(scope="function")
def db_session(postgres_session):
    """Database session fixture (now uses PostgreSQL).

    This is an alias for postgres_session to maintain backward compatibility
    with existing tests that use db_session.

    The session automatically rolls back after each test for isolation.
    """
    return postgres_session