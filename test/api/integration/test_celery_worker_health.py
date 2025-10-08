"""Tests for Celery worker health checking."""

from unittest.mock import patch, MagicMock
import pytest
from fastapi import status
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from genonaut.db.schema import User
from genonaut.api.main import create_app


class TestCeleryWorkerHealth:
    """Test Celery worker availability checking."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_generation_job_creation_fails_when_workers_unavailable(self, client, test_user):
        """Test that job creation returns 503 when Celery workers are not available."""
        # Mock the worker check to return False (workers unavailable)
        with patch('genonaut.api.services.generation_service.check_celery_workers_available', return_value=False):
            job_data = {
                "user_id": str(test_user.id),
                "job_type": "image",
                "prompt": "A beautiful sunset over mountains",
                "width": 512,
                "height": 768,
                "batch_size": 1,
            }

            response = client.post("/api/v1/generation-jobs/", json=job_data)

            # Should return 503 Service Unavailable
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            # Check error message structure (FastAPI wraps in "detail")
            data = response.json()
            assert "detail" in data
            assert "error" in data["detail"]
            assert "message" in data["detail"]["error"]
            assert "queuing service" in data["detail"]["error"]["message"].lower()
            assert data["detail"]["error"]["service"] == "celery_worker"
            assert data["detail"]["error"]["status"] == "unavailable"

    def test_generation_job_creation_succeeds_when_workers_available(self, client, test_user):
        """Test that job creation works normally when workers are available."""
        # This test verifies that the health check doesn't interfere when workers are available
        # The actual job creation is tested elsewhere; we just need to verify no 503 error
        with patch('genonaut.api.services.generation_service.check_celery_workers_available', return_value=True):
            job_data = {
                "user_id": str(test_user.id),
                "job_type": "image",
                "prompt": "A beautiful sunset over mountains",
                "width": 512,
                "height": 768,
                "batch_size": 1,
            }

            response = client.post("/api/v1/generation-jobs/", json=job_data)

            # Should NOT return 503 when workers are available
            # (may get other errors like 404 for user, but that's expected in test isolation)
            assert response.status_code != status.HTTP_503_SERVICE_UNAVAILABLE

    def test_check_celery_workers_with_no_stats(self):
        """Test worker check returns False when stats() returns None."""
        from genonaut.api.services.generation_service import check_celery_workers_available

        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = None
        mock_inspect.ping.return_value = None

        mock_control = MagicMock()
        mock_control.inspect.return_value = mock_inspect

        with patch('genonaut.api.services.generation_service.celery_current_app') as mock_app:
            mock_app.control = mock_control
            result = check_celery_workers_available()
            assert result is False

    def test_check_celery_workers_with_empty_stats(self):
        """Test worker check returns False when stats() returns empty dict."""
        from genonaut.api.services.generation_service import check_celery_workers_available

        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = {}
        mock_inspect.ping.return_value = {}

        mock_control = MagicMock()
        mock_control.inspect.return_value = mock_inspect

        with patch('genonaut.api.services.generation_service.celery_current_app') as mock_app:
            mock_app.control = mock_control
            result = check_celery_workers_available()
            assert result is False

    def test_check_celery_workers_with_no_ping_response(self):
        """Test worker check returns False when ping() returns None even if stats has data."""
        from genonaut.api.services.generation_service import check_celery_workers_available

        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = {"worker1": {"some": "stats"}}
        mock_inspect.ping.return_value = None

        mock_control = MagicMock()
        mock_control.inspect.return_value = mock_inspect

        with patch('genonaut.api.services.generation_service.celery_current_app') as mock_app:
            mock_app.control = mock_control
            result = check_celery_workers_available()
            assert result is False

    def test_check_celery_workers_with_active_workers(self):
        """Test worker check returns True when both stats and ping succeed."""
        from genonaut.api.services.generation_service import check_celery_workers_available

        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = {
            "worker1@host": {
                "pool": {"max-concurrency": 4},
                "total": {"tasks": 10}
            }
        }
        mock_inspect.ping.return_value = {
            "worker1@host": {"ok": "pong"}
        }

        mock_control = MagicMock()
        mock_control.inspect.return_value = mock_inspect

        with patch('genonaut.api.services.generation_service.celery_current_app') as mock_app:
            mock_app.control = mock_control
            result = check_celery_workers_available()
            assert result is True

    def test_check_celery_workers_handles_exceptions(self):
        """Test worker check returns False when exception occurs."""
        from genonaut.api.services.generation_service import check_celery_workers_available

        mock_control = MagicMock()
        mock_control.inspect.side_effect = Exception("Connection failed")

        with patch('genonaut.api.services.generation_service.celery_current_app') as mock_app:
            mock_app.control = mock_control
            result = check_celery_workers_available()
            assert result is False

    def test_check_celery_workers_in_test_environment(self):
        """Test worker check returns True in test environment (SimpleNamespace stub)."""
        from genonaut.api.services.generation_service import check_celery_workers_available
        from types import SimpleNamespace

        # Simulate test environment with SimpleNamespace stub
        mock_control = SimpleNamespace(revoke=lambda *a, **k: None)

        with patch('genonaut.api.services.generation_service.celery_current_app') as mock_app:
            mock_app.control = mock_control
            result = check_celery_workers_available()
            assert result is True
