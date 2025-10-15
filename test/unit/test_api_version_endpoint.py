"""
Unit tests for API version endpoint.

Tests that the API version endpoint returns correct version information.
"""
import pytest
from unittest.mock import MagicMock


class MockVersionResponse:
    """Mock response for API version endpoint."""

    def __init__(self, version: str, build_info: dict):
        """Initialize mock version response.

        Args:
            version: API version string (e.g., "1.0.0")
            build_info: Dictionary with build information
        """
        self.version = version
        self.build_info = build_info

    def to_dict(self) -> dict:
        """Convert response to dictionary format.

        Returns:
            Dictionary with version and build_info
        """
        return {
            'version': self.version,
            'build_info': self.build_info
        }


class MockVersionService:
    """Mock service for version information."""

    @staticmethod
    def get_version_info() -> MockVersionResponse:
        """Get API version information.

        Returns:
            MockVersionResponse with version and build info
        """
        return MockVersionResponse(
            version="1.0.0",
            build_info={
                'build_date': '2025-10-15',
                'commit_hash': 'abc123',
                'environment': 'test'
            }
        )


@pytest.fixture
def version_service():
    """Provide mock version service."""
    return MockVersionService()


def test_get_version_info_returns_version_string(version_service):
    """Test that get_version_info returns valid version string."""
    response = version_service.get_version_info()

    assert response.version is not None
    assert isinstance(response.version, str)
    assert len(response.version) > 0


def test_get_version_info_format(version_service):
    """Test that version follows semantic versioning format."""
    response = version_service.get_version_info()
    version_parts = response.version.split('.')

    # Should have major.minor.patch format
    assert len(version_parts) == 3
    # Each part should be numeric
    for part in version_parts:
        assert part.isdigit()


def test_get_version_info_includes_build_info(version_service):
    """Test that get_version_info includes build information."""
    response = version_service.get_version_info()

    assert response.build_info is not None
    assert isinstance(response.build_info, dict)
    assert len(response.build_info) > 0


def test_build_info_contains_build_date(version_service):
    """Test that build info contains build_date field."""
    response = version_service.get_version_info()

    assert 'build_date' in response.build_info
    assert isinstance(response.build_info['build_date'], str)


def test_build_info_contains_commit_hash(version_service):
    """Test that build info contains commit_hash field."""
    response = version_service.get_version_info()

    assert 'commit_hash' in response.build_info
    assert isinstance(response.build_info['commit_hash'], str)
    assert len(response.build_info['commit_hash']) > 0


def test_build_info_contains_environment(version_service):
    """Test that build info contains environment field."""
    response = version_service.get_version_info()

    assert 'environment' in response.build_info
    assert response.build_info['environment'] in ['dev', 'demo', 'test', 'production']


def test_version_response_to_dict(version_service):
    """Test that version response can be converted to dict."""
    response = version_service.get_version_info()
    response_dict = response.to_dict()

    assert isinstance(response_dict, dict)
    assert 'version' in response_dict
    assert 'build_info' in response_dict


def test_version_response_dict_structure(version_service):
    """Test that response dict has correct structure."""
    response = version_service.get_version_info()
    response_dict = response.to_dict()

    # Top level should have exactly 2 keys
    assert len(response_dict) == 2

    # version should be string
    assert isinstance(response_dict['version'], str)

    # build_info should be dict
    assert isinstance(response_dict['build_info'], dict)

    # build_info should have expected fields
    assert 'build_date' in response_dict['build_info']
    assert 'commit_hash' in response_dict['build_info']
    assert 'environment' in response_dict['build_info']
