"""Tests for FastAPI exception handlers."""

from fastapi.testclient import TestClient

from genonaut.api.exceptions import StatementTimeoutError
from genonaut.api.main import create_app


def test_statement_timeout_handler_returns_standard_payload():
    """StatementTimeoutError should translate to a structured 504 response."""

    app = create_app()

    @app.get("/timeout-test")
    async def timeout_route():  # pragma: no cover - executed via TestClient
        raise StatementTimeoutError(
            "Database statement exceeded configured timeout (15s)",
            timeout="15s",
            query="SELECT * FROM table",
            context={"path": "/timeout-test", "user_id": "user-123"},
        )

    client = TestClient(app)
    response = client.get("/timeout-test")

    assert response.status_code == 504
    payload = response.json()
    assert payload["error_type"] == "statement_timeout"
    assert payload["timeout_duration"] == "15s"
    assert payload["message"].startswith("The operation took too long")
    assert payload["details"]["query"] == "SELECT * FROM table"
    assert payload["details"]["context"]["user_id"] == "user-123"


def test_statement_timeout_handler_omits_empty_details():
    """Details should be absent when no diagnostic information exists."""

    app = create_app()

    @app.get("/timeout-test-minimal")
    async def timeout_route_minimal():  # pragma: no cover - executed via TestClient
        raise StatementTimeoutError(
            "Database statement exceeded configured timeout (10s)",
            timeout="10s",
        )

    client = TestClient(app)
    response = client.get("/timeout-test-minimal")

    assert response.status_code == 504
    payload = response.json()
    assert payload["timeout_duration"] == "10s"
    assert "details" not in payload
