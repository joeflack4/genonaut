"""Shared fixtures for pagination stress tests."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from genonaut.db.schema import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with in-memory SQLite for stress tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture(scope="function")
def large_db_session():
    """Create a test database session optimized for large datasets."""
    # Use faster settings for stress tests
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={
            "check_same_thread": False,
        },
        pool_pre_ping=True
    )

    # Create tables
    Base.metadata.create_all(engine)

    # Configure session for bulk operations
    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False  # Better for bulk operations
    )

    session = SessionLocal()

    # SQLite optimizations for bulk operations
    session.execute(text("PRAGMA journal_mode=WAL"))
    session.execute(text("PRAGMA synchronous=NORMAL"))
    session.execute(text("PRAGMA cache_size=10000"))
    session.execute(text("PRAGMA temp_store=MEMORY"))
    session.commit()

    yield session

    session.close()