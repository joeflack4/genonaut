"""Shared fixtures for API integration tests targeting tag and content endpoints."""

import os
from typing import Dict, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from genonaut.api.main import create_app
from genonaut.api.dependencies import get_database_session
from genonaut.db.schema import Base, User, Tag, TagParent


# Ensure FastAPI loads the lightweight test configuration once per test session.
os.environ.setdefault("APP_CONFIG_PATH", "config/local-test.json")
os.environ.setdefault("ENV_TARGET", "local-test")


@pytest.fixture()
def engine() -> Generator:
    """Provide an in-memory SQLite engine for API tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session bound to the in-memory database."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient with the database dependency overridden."""

    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            db_session.rollback()

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
