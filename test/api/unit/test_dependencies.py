"""Tests for API dependency helpers."""

import logging
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from genonaut.api.dependencies import (
    DatabaseManager,
    _is_statement_timeout_error,
    _yield_session,
    get_database_session,
)
from genonaut.api.context import RequestContext, reset_request_context, set_request_context
from genonaut.api.exceptions import StatementTimeoutError


class DummyOrig:
    """Helper object that mimics database driver errors."""

    def __init__(self, message: str = "error", pgcode: str | None = None, sqlstate: str | None = None):
        self._message = message
        self.pgcode = pgcode
        self.sqlstate = sqlstate

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self._message


def test_get_database_session_direct_invocation_returns_session():
    """Direct use of dependency helper should return a usable session."""

    session_gen = get_database_session()
    session = next(session_gen)

    try:
        assert isinstance(session, Session)
        result = session.execute(text("SELECT 1")).scalar_one()
        assert result == 1
    finally:
        session_gen.close()


def test_create_engine_applies_statement_timeout(monkeypatch):
    """Engine creation applies all timeout settings via connection options."""

    captured_kwargs = {}

    def fake_create_engine(url, **kwargs):  # type: ignore[no-redef]
        captured_kwargs.update(kwargs)
        return object()

    manager = DatabaseManager()

    monkeypatch.setattr("genonaut.api.dependencies.create_engine", fake_create_engine)
    monkeypatch.setattr(
        "genonaut.api.dependencies.get_database_url",
        lambda environment: "postgresql://example",
    )

    mock_settings = SimpleNamespace(
        statement_timeout="20s",
        lock_timeout="5s",
        idle_in_transaction_session_timeout="30s",
        db_echo=True,
        db_pool_pre_ping=True,
        db_pool_recycle=1800,
        db_pool_size=10,
        db_max_overflow=20,
    )
    monkeypatch.setattr("genonaut.api.dependencies.get_settings", lambda: mock_settings)

    engine = manager._create_engine("dev")
    assert engine is not None

    expected_options = (
        "-c statement_timeout=20s "
        "-c lock_timeout=5s "
        "-c idle_in_transaction_session_timeout=30s"
    )
    assert captured_kwargs["connect_args"] == {"options": expected_options}
    assert captured_kwargs["echo"] is True
    assert captured_kwargs["pool_pre_ping"] is True
    assert captured_kwargs["pool_recycle"] == 1800
    assert captured_kwargs["pool_size"] == 10
    assert captured_kwargs["max_overflow"] == 20


def test_create_engine_skips_timeout_for_non_postgres(monkeypatch):
    """Drivers that do not support options should not receive them."""

    captured_kwargs = {}

    def fake_create_engine(url, **kwargs):  # type: ignore[no-redef]
        captured_kwargs.update(kwargs)
        return object()

    monkeypatch.setattr("genonaut.api.dependencies.create_engine", fake_create_engine)
    monkeypatch.setattr(
        "genonaut.api.dependencies.get_database_url",
        lambda environment: "sqlite:///:memory:",
    )
    monkeypatch.setattr(
        "genonaut.api.dependencies.get_settings",
        lambda: SimpleNamespace(
            statement_timeout="25s",
            lock_timeout="5s",
            idle_in_transaction_session_timeout="30s",
            db_echo=False,
            db_pool_pre_ping=True,
            db_pool_recycle=1800,
            db_pool_size=10,
            db_max_overflow=20,
        ),
    )

    engine = DatabaseManager()._create_engine("test")
    assert engine is not None
    assert captured_kwargs.get("connect_args") in ({}, None)


def test_engine_respects_updated_statement_timeout_after_restart(monkeypatch):
    """Restarting the API picks up new timeout settings on fresh engines."""

    captured_options = []

    def fake_create_engine(url, **kwargs):  # type: ignore[no-redef]
        captured_options.append(kwargs["connect_args"]["options"])
        return object()

    monkeypatch.setattr("genonaut.api.dependencies.create_engine", fake_create_engine)
    monkeypatch.setattr(
        "genonaut.api.dependencies.get_database_url",
        lambda environment: "postgresql://example",
    )

    monkeypatch.setattr(
        "genonaut.api.dependencies.get_settings",
        lambda: SimpleNamespace(
            statement_timeout="10s",
            lock_timeout="5s",
            idle_in_transaction_session_timeout="30s",
            db_echo=False,
            db_pool_pre_ping=True,
            db_pool_recycle=1800,
            db_pool_size=10,
            db_max_overflow=20,
        ),
    )
    DatabaseManager()._create_engine("dev")

    monkeypatch.setattr(
        "genonaut.api.dependencies.get_settings",
        lambda: SimpleNamespace(
            statement_timeout="45s",
            lock_timeout="5s",
            idle_in_transaction_session_timeout="30s",
            db_echo=False,
            db_pool_pre_ping=True,
            db_pool_recycle=1800,
            db_pool_size=10,
            db_max_overflow=20,
        ),
    )
    DatabaseManager()._create_engine("dev")

    assert captured_options == [
        "-c statement_timeout=10s -c lock_timeout=5s -c idle_in_transaction_session_timeout=30s",
        "-c statement_timeout=45s -c lock_timeout=5s -c idle_in_transaction_session_timeout=30s",
    ]


def test_is_statement_timeout_error_detects_sqlstate():
    """Errors with the timeout SQLSTATE should be detected."""

    error = OperationalError("SELECT 1", None, DummyOrig(pgcode="57014"))
    assert _is_statement_timeout_error(error) is True


def test_is_statement_timeout_error_detects_timeout_message():
    """Fallback detection uses error message when SQLSTATE missing."""

    message = "canceling statement due to statement timeout"
    error = OperationalError("SELECT 1", None, DummyOrig(message=message))
    assert _is_statement_timeout_error(error) is True


def test_is_statement_timeout_error_non_timeout():
    """Non-timeout errors should not be misclassified."""

    error = OperationalError("SELECT 1", None, DummyOrig(pgcode="23505"))
    assert _is_statement_timeout_error(error) is False


def test_yield_session_raises_statement_timeout(monkeypatch, caplog):
    """Session helper should raise StatementTimeoutError when detected."""

    class DummySession:
        def __init__(self):
            self.rollback_called = False
            self.close_called = False

        def rollback(self):
            self.rollback_called = True

        def close(self):
            self.close_called = True

    dummy_session = DummySession()

    class DummyManager:
        def get_session_factory(self, environment):
            return lambda: dummy_session

    monkeypatch.setattr("genonaut.api.dependencies.get_database_manager", lambda: DummyManager())
    monkeypatch.setattr(
        "genonaut.api.dependencies.get_settings",
        lambda: SimpleNamespace(statement_timeout="12s"),
    )

    caplog.set_level(logging.WARNING, logger="genonaut.api.dependencies")

    generator = _yield_session("dev")
    session = next(generator)
    assert session is dummy_session

    with pytest.raises(StatementTimeoutError) as excinfo:
        generator.throw(OperationalError("SELECT 1", None, DummyOrig(pgcode="57014")))

    assert dummy_session.rollback_called is True
    assert dummy_session.close_called is True
    assert excinfo.value.timeout == "12s"
    assert excinfo.value.query == "SELECT 1"
    assert excinfo.value.context == {"environment": "dev"}
    timeout_records = [
        record for record in caplog.records if "exceeded timeout threshold" in record.message
    ]
    assert timeout_records, "Expected timeout log entry"
    assert timeout_records[0].timeout_context["environment"] == "dev"


def test_yield_session_includes_request_context(monkeypatch):
    """Request metadata should be included when present."""

    class DummySession:
        def __init__(self):
            self.rollback_called = False
            self.close_called = False

        def rollback(self):
            self.rollback_called = True

        def close(self):
            self.close_called = True

    dummy_session = DummySession()

    class DummyManager:
        def get_session_factory(self, environment):
            return lambda: dummy_session

    monkeypatch.setattr("genonaut.api.dependencies.get_database_manager", lambda: DummyManager())
    monkeypatch.setattr(
        "genonaut.api.dependencies.get_settings",
        lambda: SimpleNamespace(statement_timeout="18s"),
    )

    token = set_request_context(
        RequestContext(
            path="/api/v1/test",
            method="POST",
            endpoint="create_item",
            user_id="user-123",
        )
    )

    try:
        generator = _yield_session("demo")
        next(generator)

        with pytest.raises(StatementTimeoutError) as excinfo:
            generator.throw(OperationalError("INSERT INTO items", None, DummyOrig(pgcode="57014")))
    finally:
        reset_request_context(token)

    assert dummy_session.rollback_called is True
    assert dummy_session.close_called is True
    assert excinfo.value.timeout == "18s"
    assert excinfo.value.query == "INSERT INTO items"
    assert excinfo.value.context == {
        "environment": "demo",
        "path": "/api/v1/test",
        "method": "POST",
        "endpoint": "create_item",
        "user_id": "user-123",
    }
