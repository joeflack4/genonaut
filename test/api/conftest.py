"""Shared fixtures for API integration tests targeting tag and content endpoints."""

import os
from typing import Dict, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from genonaut.api.main import create_app
from genonaut.api.dependencies import get_database_session
from genonaut.db.schema import User, Tag, TagParent

# Import PostgreSQL fixtures
from test.db.postgres_fixtures import postgres_engine, postgres_session


# Ensure FastAPI loads the lightweight test configuration once per test session.
os.environ.setdefault("APP_CONFIG_PATH", "config/local-test.json")
os.environ.setdefault("ENV_TARGET", "local-test")


@pytest.fixture()
def db_session(postgres_session) -> Generator[Session, None, None]:
    """Yield a PostgreSQL session for API tests.

    This fixture uses the PostgreSQL test database with automatic rollback
    for test isolation.
    """
    yield postgres_session


@pytest.fixture()
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient with the database dependency overridden.

    With PostgreSQL, the postgres_session fixture already handles transaction
    rollback, so we don't need to rollback here. Rollback in the override
    would delete fixture data created before the API call.
    """

    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            # Don't rollback here - postgres_session fixture handles cleanup
            # Rollback here would undo fixture data (sample_user, sample_tags, etc.)
            pass

    app.dependency_overrides[get_database_session] = override_get_db
    client = TestClient(app)

    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        client.close()


@pytest.fixture()
def sample_user(db_session: Session) -> User:
    """Create a sample active user for API tests."""

    user = User(
        id=uuid4(),
        username="api-test-user",
        email="api-test-user@example.com",
        preferences={"theme": "dark"},
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def sample_tags(db_session: Session) -> Dict[str, Tag]:
    """Create a small tag hierarchy for testing."""

    root = Tag(id=uuid4(), name="root-tag", tag_metadata={"group": "primary"})
    child = Tag(id=uuid4(), name="child-tag", tag_metadata={"group": "secondary"})
    leaf = Tag(id=uuid4(), name="leaf-tag", tag_metadata={"group": "tertiary"})

    db_session.add_all([root, child, leaf])
    db_session.commit()

    relationships = [
        TagParent(tag_id=child.id, parent_id=root.id),
        TagParent(tag_id=leaf.id, parent_id=child.id),
    ]
    db_session.add_all(relationships)
    db_session.commit()

    db_session.refresh(root)
    db_session.refresh(child)
    db_session.refresh(leaf)

    return {"root": root, "child": child, "leaf": leaf}
