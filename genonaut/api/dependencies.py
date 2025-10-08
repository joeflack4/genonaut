"""Dependency injection for the Genonaut API."""

from functools import lru_cache
from typing import Dict, Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from genonaut.api.config import get_settings, Settings
from genonaut.db.utils import get_database_url, resolve_database_environment


SUPPORTED_ENVIRONMENTS = {"dev", "demo", "test"}


class DatabaseManager:
    """Database session manager for different environments."""

    def __init__(self):
        self._engines: Dict[str, Engine] = {}
        self._session_factories: Dict[str, sessionmaker] = {}

    def _create_engine(self, environment: str):
        """Create SQLAlchemy engine for the specified database."""
        resolved_env = resolve_database_environment(environment=environment)
        try:
            database_url = get_database_url(environment=resolved_env)
            engine = create_engine(
                database_url,
                echo=get_settings().db_echo,
                pool_pre_ping=True,
                pool_recycle=300,
            )
            return engine
        except Exception as exc:
            raise SQLAlchemyError(f"Failed to create database engine: {exc}")

    def _get_engine(self, environment: str):
        resolved_env = resolve_database_environment(environment=environment)
        if resolved_env not in self._engines:
            self._engines[resolved_env] = self._create_engine(resolved_env)
        return self._engines[resolved_env]

    def get_session_factory(self, environment: str):
        resolved_env = resolve_database_environment(environment=environment)
        if resolved_env not in self._session_factories:
            self._session_factories[resolved_env] = sessionmaker(
                bind=self._get_engine(resolved_env),
                autocommit=False,
                autoflush=False,
            )
        return self._session_factories[resolved_env]


@lru_cache()
def get_database_manager() -> DatabaseManager:
    """Get cached database manager instance."""
    return DatabaseManager()


def _yield_session(environment: str) -> Generator[Session, None, None]:
    db_manager = get_database_manager()
    session_factory = db_manager.get_session_factory(environment)
    session = session_factory()
    try:
        yield session
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        session.close()


def get_dev_session() -> Generator[Session, None, None]:
    """Dependency to get development database session."""
    yield from _yield_session("dev")


def get_demo_session() -> Generator[Session, None, None]:
    """Dependency to get demo database session."""
    yield from _yield_session("demo")


def get_test_session() -> Generator[Session, None, None]:
    """Dependency to get test database session."""
    yield from _yield_session("test")


def get_database_session(settings: Settings = Depends(get_settings)) -> Generator[Session, None, None]:
    """Dependency to get database session based on environment setting."""
    environment = settings.environment_type or "dev"
    if environment not in SUPPORTED_ENVIRONMENTS:
        environment = "dev"

    if environment == "demo":
        yield from get_demo_session()
    elif environment == "test":
        yield from get_test_session()
    else:
        yield from get_dev_session()
