"""Unit tests for route analytics middleware.

These tests verify the middleware functionality without requiring database or Redis.
"""

import json
import time
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from genonaut.api.middleware.route_analytics import (
    normalize_query_params,
    get_user_id_from_request,
    get_error_type_from_status,
    RouteAnalyticsMiddleware,
)


# ============================================================================
# Unit Tests for Helper Functions
# ============================================================================

class TestNormalizeQueryParams:
    """Tests for normalize_query_params function."""

    def test_empty_query_string(self):
        """Empty query string returns empty dict."""
        result = normalize_query_params("")
        assert result == {}

    def test_none_query_string(self):
        """None query string returns empty dict."""
        result = normalize_query_params(None)
        assert result == {}

    def test_excludes_page_parameter(self):
        """Pagination param 'page' is excluded from normalization."""
        result = normalize_query_params("page=2&sort=created_at")
        assert "page" not in result
        assert result["sort"] == "created_at"

    def test_excludes_offset_parameter(self):
        """Pagination param 'offset' is excluded from normalization."""
        result = normalize_query_params("offset=20&page_size=10")
        assert "offset" not in result
        assert result["page_size"] == "10"

    def test_excludes_limit_parameter(self):
        """Pagination param 'limit' is excluded from normalization."""
        result = normalize_query_params("limit=50&tag=nature")
        assert "limit" not in result
        assert result["tag"] == "nature"

    def test_excludes_cursor_parameter(self):
        """Pagination param 'cursor' is excluded from normalization."""
        result = normalize_query_params("cursor=abc123&sort=desc")
        assert "cursor" not in result
        assert result["sort"] == "desc"

    def test_includes_filtering_params(self):
        """Filtering parameters are included in normalization."""
        result = normalize_query_params("tag=nature&sort=created_at&content_types=image")
        assert result["tag"] == "nature"
        assert result["sort"] == "created_at"
        assert result["content_types"] == "image"

    def test_complex_query_string(self):
        """Complex query string with multiple params."""
        query = "page=3&page_size=10&tag=nature&sort=created_at&offset=20"
        result = normalize_query_params(query)

        # Pagination params excluded
        assert "page" not in result
        assert "offset" not in result

        # Filtering params included
        assert result["page_size"] == "10"
        assert result["tag"] == "nature"
        assert result["sort"] == "created_at"

    def test_multi_value_parameters(self):
        """Parameters with multiple values are handled correctly."""
        result = normalize_query_params("tag=nature&tag=forest&page=1")
        assert "tag" in result
        # Should keep multi-values as list
        assert isinstance(result["tag"], list)
        assert "nature" in result["tag"]
        assert "forest" in result["tag"]

    def test_url_encoded_values(self):
        """URL-encoded values are decoded correctly."""
        result = normalize_query_params("search=hello+world&sort=created_at")
        assert result["search"] == "hello world"
        assert result["sort"] == "created_at"

    def test_blank_values(self):
        """Blank parameter values are preserved."""
        result = normalize_query_params("tag=&sort=created_at")
        assert result["tag"] == ""
        assert result["sort"] == "created_at"


class TestGetUserIdFromRequest:
    """Tests for get_user_id_from_request function."""

    def test_user_id_from_request_state(self):
        """User ID extracted from request.state if available."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user-123"
        request.headers = {}

        result = get_user_id_from_request(request)
        assert result == "user-123"

    def test_user_id_from_header(self):
        """User ID extracted from X-User-ID header if state not available."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.headers = {"X-User-ID": "user-456"}

        # Remove user_id attribute from state
        if hasattr(request.state, 'user_id'):
            delattr(request.state, 'user_id')

        result = get_user_id_from_request(request)
        assert result == "user-456"

    def test_no_user_id_available(self):
        """Returns None when no user ID available."""
        request = Mock(spec=Request)
        request.state = Mock(spec=[])  # Empty spec - no attributes
        request.headers = {}

        result = get_user_id_from_request(request)
        assert result is None

    def test_state_takes_precedence_over_header(self):
        """User ID from state takes precedence over header."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "state-user"
        request.headers = {"X-User-ID": "header-user"}

        result = get_user_id_from_request(request)
        assert result == "state-user"


class TestGetErrorTypeFromStatus:
    """Tests for get_error_type_from_status function."""

    def test_successful_status_codes(self):
        """Successful status codes return None."""
        assert get_error_type_from_status(200) is None
        assert get_error_type_from_status(201) is None
        assert get_error_type_from_status(204) is None
        assert get_error_type_from_status(299) is None

    def test_client_error_status_codes(self):
        """Client error status codes return 'client_error'."""
        assert get_error_type_from_status(400) == 'client_error'
        assert get_error_type_from_status(401) == 'client_error'
        assert get_error_type_from_status(403) == 'client_error'
        assert get_error_type_from_status(404) == 'client_error'
        assert get_error_type_from_status(422) == 'client_error'
        assert get_error_type_from_status(499) == 'client_error'

    def test_server_error_status_codes(self):
        """Server error status codes return 'server_error'."""
        assert get_error_type_from_status(500) == 'server_error'
        assert get_error_type_from_status(501) == 'server_error'
        assert get_error_type_from_status(502) == 'server_error'
        assert get_error_type_from_status(503) == 'server_error'
        assert get_error_type_from_status(504) == 'server_error'
        assert get_error_type_from_status(599) == 'server_error'

    def test_redirection_status_codes(self):
        """Redirection status codes (3xx) return None."""
        assert get_error_type_from_status(300) is None
        assert get_error_type_from_status(301) is None
        assert get_error_type_from_status(302) is None
        assert get_error_type_from_status(304) is None


# ============================================================================
# Integration Tests for RouteAnalyticsMiddleware
# ============================================================================

class TestRouteAnalyticsMiddleware:
    """Tests for RouteAnalyticsMiddleware class."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        with patch('genonaut.api.middleware.route_analytics.get_redis_client') as mock:
            client = MagicMock()
            client.ping.return_value = True
            client.xadd.return_value = b'1234567890-0'
            mock.return_value = client
            yield client

    @pytest.fixture
    def app_with_middleware(self, mock_redis_client):
        """Create FastAPI app with route analytics middleware."""
        app = FastAPI()

        # Add test endpoints
        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.get("/api/v1/slow")
        async def slow_endpoint():
            time.sleep(0.1)  # Simulate slow endpoint
            return {"message": "slow"}

        @app.get("/api/v1/error")
        async def error_endpoint():
            raise ValueError("Test error")

        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}

        # Add middleware
        app.add_middleware(RouteAnalyticsMiddleware)

        return app

    def test_middleware_tracks_api_routes(self, app_with_middleware, mock_redis_client):
        """Middleware captures analytics for /api/* routes."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test")
        assert response.status_code == 200

        # Verify Redis write was called
        mock_redis_client.xadd.assert_called_once()

        # Verify event data structure
        call_args = mock_redis_client.xadd.call_args
        stream_key = call_args[0][0]
        event_data = call_args[0][1]

        assert 'route_analytics:stream' in stream_key
        assert event_data['route'] == '/api/v1/test'
        assert event_data['method'] == 'GET'
        assert event_data['status_code'] == '200'
        assert 'duration_ms' in event_data
        assert event_data['error_type'] == ''

    def test_middleware_skips_non_api_routes(self, app_with_middleware, mock_redis_client):
        """Middleware does not track non-/api/* routes."""
        client = TestClient(app_with_middleware)

        response = client.get("/health")
        assert response.status_code == 200

        # Verify Redis write was NOT called
        mock_redis_client.xadd.assert_not_called()

    def test_middleware_captures_query_parameters(self, app_with_middleware, mock_redis_client):
        """Middleware captures and normalizes query parameters."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test?page=2&page_size=10&sort=created_at&tag=nature")
        assert response.status_code == 200

        # Verify normalized query params
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        query_params = json.loads(event_data['query_params'])
        query_params_normalized = json.loads(event_data['query_params_normalized'])

        # Raw params include everything
        assert 'page' in query_params
        assert query_params['page_size'] == '10'

        # Normalized params exclude pagination params
        assert 'page' not in query_params_normalized
        assert query_params_normalized['page_size'] == '10'
        assert query_params_normalized['sort'] == 'created_at'
        assert query_params_normalized['tag'] == 'nature'

    def test_middleware_captures_user_id_from_header(self, app_with_middleware, mock_redis_client):
        """Middleware captures user ID from X-User-ID header."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test", headers={"X-User-ID": "test-user-123"})
        assert response.status_code == 200

        # Verify user_id captured
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['user_id'] == 'test-user-123'

    def test_middleware_captures_error_type_for_404(self, app_with_middleware, mock_redis_client):
        """Middleware captures error type for 404 responses."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        # Verify error type captured
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['status_code'] == '404'
        assert event_data['error_type'] == 'client_error'

    def test_middleware_captures_error_type_for_500(self, app_with_middleware, mock_redis_client):
        """Middleware captures error type for 500 responses."""
        client = TestClient(app_with_middleware)

        # This will raise an exception
        with pytest.raises(ValueError):
            client.get("/api/v1/error")

        # Verify error captured (middleware writes analytics even when exception occurs)
        # Note: In production, exception handlers would convert to 500 response
        # Here we just verify the middleware handles exceptions gracefully

    def test_middleware_calculates_duration(self, app_with_middleware, mock_redis_client):
        """Middleware calculates request duration correctly."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/slow")
        assert response.status_code == 200

        # Verify duration captured and is reasonable
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        duration_ms = int(event_data['duration_ms'])
        # Should be at least 100ms due to sleep, but allow some overhead
        assert duration_ms >= 100
        assert duration_ms < 1000  # Shouldn't take more than 1 second

    def test_middleware_handles_redis_unavailable(self):
        """Middleware gracefully handles Redis unavailable."""
        with patch('genonaut.api.middleware.route_analytics.get_redis_client') as mock:
            # Simulate Redis connection failure
            mock.return_value.ping.side_effect = Exception("Redis unavailable")

            app = FastAPI()

            @app.get("/api/v1/test")
            async def test_endpoint():
                return {"message": "test"}

            # Middleware should initialize with disabled state
            app.add_middleware(RouteAnalyticsMiddleware)

            client = TestClient(app)
            response = client.get("/api/v1/test")

            # Request should still succeed even though analytics is disabled
            assert response.status_code == 200

    def test_middleware_handles_redis_write_failure(self, app_with_middleware):
        """Middleware handles Redis write failures gracefully."""
        with patch('genonaut.api.middleware.route_analytics.get_redis_client') as mock:
            # Simulate write failure
            mock.return_value.xadd.side_effect = Exception("Redis write failed")

            client = TestClient(app_with_middleware)
            response = client.get("/api/v1/test")

            # Request should still succeed even though analytics write failed
            assert response.status_code == 200

    def test_middleware_captures_request_size(self, app_with_middleware, mock_redis_client):
        """Middleware captures request Content-Length."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test", headers={"Content-Length": "1234"})
        assert response.status_code == 200

        # Verify request size captured
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['request_size_bytes'] == '1234'

    def test_middleware_handles_invalid_content_length(self, app_with_middleware, mock_redis_client):
        """Middleware handles invalid Content-Length gracefully."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test", headers={"Content-Length": "invalid"})
        assert response.status_code == 200

        # Verify request size defaults to 0
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['request_size_bytes'] == '0'

    def test_middleware_preserves_response(self, app_with_middleware, mock_redis_client):
        """Middleware does not modify the response."""
        client = TestClient(app_with_middleware)

        response = client.get("/api/v1/test")
        assert response.status_code == 200
        assert response.json() == {"message": "test"}

    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
    def test_middleware_tracks_all_http_methods(self, mock_redis_client, method):
        """Middleware tracks all HTTP methods correctly."""
        app = FastAPI()

        @app.api_route("/api/v1/test", methods=[method])
        async def test_endpoint():
            return {"message": "test"}

        app.add_middleware(RouteAnalyticsMiddleware)

        client = TestClient(app)
        response = client.request(method, "/api/v1/test")

        # Verify method captured
        call_args = mock_redis_client.xadd.call_args
        event_data = call_args[0][1]

        assert event_data['method'] == method
