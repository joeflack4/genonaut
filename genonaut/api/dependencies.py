"""Dependency injection for the Genonaut API."""

import logging
from functools import lru_cache
from typing import Dict, Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from genonaut.api.config import get_settings, Settings
from genonaut.api.context import get_request_context
from genonaut.api.exceptions import StatementTimeoutError
from genonaut.db.utils import get_database_url, resolve_database_environment


SUPPORTED_ENVIRONMENTS = {"dev", "demo", "test"}

logger = logging.getLogger(__name__)

STATEMENT_TIMEOUT_SQLSTATE = "57014"


def _is_statement_timeout_error(error: SQLAlchemyError) -> bool:
    """Check whether the SQLAlchemy error represents a statement timeout."""

    if not isinstance(error, OperationalError):
        return False

    origin = getattr(error, "orig", None)
    if origin is not None:
        code = getattr(origin, "pgcode", None) or getattr(origin, "sqlstate", None)
        if code == STATEMENT_TIMEOUT_SQLSTATE:
            return True

        # Also check the origin's class name for QueryCanceled
        origin_class = type(origin).__name__
        if origin_class == "QueryCanceled":
            return True

    message = str(error).lower()
    return "statement timeout" in message or "canceling statement" in message


class DatabaseManager:
    """Database session manager for different environments."""

    def __init__(self):
        self._engines: Dict[str, Engine] = {}
        self._session_factories: Dict[str, sessionmaker] = {}

    def _create_engine(self, environment: str):
        """Create SQLAlchemy engine for the specified database."""
        resolved_env = resolve_database_environment(environment=environment)
        try:
            settings = get_settings()
            database_url = get_database_url(environment=resolved_env)
            connect_args = {}
            if database_url.startswith("postgresql"):
                # Set session-level timeouts via PostgreSQL options
                connect_args["options"] = (
                    f"-c statement_timeout={settings.statement_timeout} "
                    f"-c lock_timeout={settings.lock_timeout} "
                    f"-c idle_in_transaction_session_timeout={settings.idle_in_transaction_session_timeout}"
                )
            engine_kwargs = {
                "echo": settings.db_echo,
                "pool_pre_ping": settings.db_pool_pre_ping,
                "pool_recycle": settings.db_pool_recycle,
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
            }
            if connect_args:
                engine_kwargs["connect_args"] = connect_args

            engine = create_engine(
                database_url,
                **engine_kwargs,
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
    except SQLAlchemyError as exc:
        session.rollback()

        if _is_statement_timeout_error(exc):
            settings = get_settings()
            request_context = get_request_context()
            context_data = {"environment": environment}

            if request_context is not None:
                context_data.update(
                    {
                        "path": request_context.path,
                        "method": request_context.method,
                        "endpoint": request_context.endpoint,
                        "user_id": request_context.user_id,
                    }
                )

            statement = getattr(exc, "statement", None)
            if statement is not None and not isinstance(statement, str):
                statement = str(statement)

            context_data = {key: value for key, value in context_data.items() if value is not None}

            log_context = dict(context_data)
            if statement:
                log_context["query"] = statement[:512]
            log_context["timeout"] = settings.statement_timeout

            logger.warning(
                f"Database query exceeded timeout threshold of {settings.statement_timeout}",
                extra={"timeout_context": log_context},
                exc_info=exc,
            )

            message = (
                "Database statement exceeded configured timeout "
                f"({settings.statement_timeout})"
            )

            raise StatementTimeoutError(
                message,
                timeout=settings.statement_timeout,
                query=statement,
                context=context_data,
                original_error=exc,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(exc)}"
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
    # When invoked outside FastAPI's dependency system (e.g., Celery workers),
    # the default value is still the ``Depends`` sentinel. Fallback to loading
    # settings manually so standalone callers work as expected.
    if not isinstance(settings, Settings):
        settings = get_settings()

    environment = settings.environment_type or "dev"
    if environment not in SUPPORTED_ENVIRONMENTS:
        environment = "dev"

    if environment == "demo":
        yield from get_demo_session()
    elif environment == "test":
        yield from get_test_session()
    else:
        yield from get_dev_session()
