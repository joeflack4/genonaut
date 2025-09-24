"""Shared fixtures for database integration tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from genonaut.db.schema import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()