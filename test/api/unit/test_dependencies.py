"""Tests for API dependency helpers."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from genonaut.api.dependencies import get_database_session


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
