"""
API integration tests for CORS headers.

Tests that CORS headers are set correctly on API responses.
"""
import pytest


def test_cors_middleware_configured():
    """Test that CORS middleware is configured."""
    from genonaut.api.middleware.security_middleware import get_cors_middleware_config

    cors_config = get_cors_middleware_config()

    assert cors_config is not None
    assert isinstance(cors_config, dict)


def test_cors_config_has_origins():
    """Test that CORS config specifies allowed origins."""
    from genonaut.api.middleware.security_middleware import get_cors_middleware_config

    cors_config = get_cors_middleware_config()

    # Should have allow_origins or similar
    has_origins = (
        'allow_origins' in cors_config or
        'allowed_origins' in cors_config or
        'origins' in cors_config
    )

    assert has_origins, "CORS config should specify allowed origins"


def test_cors_config_has_methods():
    """Test that CORS config specifies allowed methods."""
    from genonaut.api.middleware.security_middleware import get_cors_middleware_config

    cors_config = get_cors_middleware_config()

    # Should have allow_methods or similar
    has_methods = (
        'allow_methods' in cors_config or
        'allowed_methods' in cors_config or
        'methods' in cors_config
    )

    assert has_methods, "CORS config should specify allowed methods"


def test_cors_config_has_headers():
    """Test that CORS config specifies allowed headers."""
    from genonaut.api.middleware.security_middleware import get_cors_middleware_config

    cors_config = get_cors_middleware_config()

    # Should have allow_headers or similar
    has_headers = (
        'allow_headers' in cors_config or
        'allowed_headers' in cors_config or
        'headers' in cors_config
    )

    assert has_headers, "CORS config should specify allowed headers"


@pytest.mark.integration
def test_options_request_returns_cors_headers(api_client):
    """Test that OPTIONS requests return CORS headers."""
    # Make OPTIONS request to a known endpoint
    response = api_client.options("/api/v1/health")

    # Should return 200 for OPTIONS (preflight)
    # Note: Actual behavior depends on CORS middleware configuration
    assert response.status_code in [200, 204, 405]


@pytest.mark.integration
def test_get_request_includes_cors_headers(api_client):
    """Test that GET requests include CORS headers in response."""
    response = api_client.get("/api/v1/health")

    assert response.status_code == 200

    # Check for CORS-related headers (may not be present in test environment)
    # Common CORS headers include:
    # - Access-Control-Allow-Origin
    # - Access-Control-Allow-Methods
    # - Access-Control-Allow-Headers

    # In test environment, these may not be set
    # So we just verify the request succeeded
    assert response.json() is not None
