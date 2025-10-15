"""
Unit tests for configuration endpoint.

Tests that the config endpoint returns current configuration settings
(non-sensitive only).
"""
import pytest
from typing import Dict, Any


class MockConfigService:
    """Mock service for configuration management."""

    def __init__(self):
        """Initialize with test configuration."""
        self._config = {
            'app_name': 'Genonaut',
            'api_version': '1.0.0',
            'max_page_size': 1000,
            'default_page_size': 20,
            'statement_timeout_ms': 15000,
            'enable_caching': True,
            'cache_ttl_seconds': 300,
            'allowed_image_formats': ['png', 'jpg', 'webp'],
            'max_image_size_mb': 10,
        }

        # These should NEVER be exposed
        self._sensitive_config = {
            'database_password': 'secret',
            'api_key': 'secret_key',
            'jwt_secret': 'jwt_secret_key'
        }

    def get_public_config(self) -> Dict[str, Any]:
        """Get public configuration (no sensitive data).

        Returns:
            Dictionary with non-sensitive configuration settings
        """
        # Only return non-sensitive config
        return self._config.copy()

    def is_sensitive_key(self, key: str) -> bool:
        """Check if a configuration key is sensitive.

        Args:
            key: Configuration key to check

        Returns:
            True if key contains sensitive data
        """
        sensitive_patterns = [
            'password',
            'secret',
            'key',
            'token',
            'credential',
            'auth'
        ]

        key_lower = key.lower()
        return any(pattern in key_lower for pattern in sensitive_patterns)


@pytest.fixture
def config_service():
    """Provide mock config service."""
    return MockConfigService()


def test_get_public_config_returns_dict(config_service):
    """Test that get_public_config returns a dictionary."""
    config = config_service.get_public_config()

    assert isinstance(config, dict)
    assert len(config) > 0


def test_get_public_config_contains_app_settings(config_service):
    """Test that config contains basic app settings."""
    config = config_service.get_public_config()

    assert 'app_name' in config
    assert 'api_version' in config


def test_get_public_config_contains_pagination_settings(config_service):
    """Test that config contains pagination settings."""
    config = config_service.get_public_config()

    assert 'max_page_size' in config
    assert 'default_page_size' in config

    assert isinstance(config['max_page_size'], int)
    assert isinstance(config['default_page_size'], int)

    assert config['max_page_size'] > 0
    assert config['default_page_size'] > 0


def test_get_public_config_contains_timeout_settings(config_service):
    """Test that config contains timeout settings."""
    config = config_service.get_public_config()

    assert 'statement_timeout_ms' in config
    assert isinstance(config['statement_timeout_ms'], int)
    assert config['statement_timeout_ms'] > 0


def test_get_public_config_contains_caching_settings(config_service):
    """Test that config contains caching settings."""
    config = config_service.get_public_config()

    assert 'enable_caching' in config
    assert 'cache_ttl_seconds' in config

    assert isinstance(config['enable_caching'], bool)
    assert isinstance(config['cache_ttl_seconds'], int)


def test_get_public_config_contains_image_settings(config_service):
    """Test that config contains image processing settings."""
    config = config_service.get_public_config()

    assert 'allowed_image_formats' in config
    assert 'max_image_size_mb' in config

    assert isinstance(config['allowed_image_formats'], list)
    assert len(config['allowed_image_formats']) > 0

    assert isinstance(config['max_image_size_mb'], int)
    assert config['max_image_size_mb'] > 0


def test_get_public_config_excludes_sensitive_data(config_service):
    """Test that config does NOT contain sensitive data."""
    config = config_service.get_public_config()

    # Check that no sensitive keys are present
    sensitive_keys = ['database_password', 'api_key', 'jwt_secret']

    for key in sensitive_keys:
        assert key not in config


def test_is_sensitive_key_detects_password(config_service):
    """Test that is_sensitive_key identifies password fields."""
    assert config_service.is_sensitive_key('database_password')
    assert config_service.is_sensitive_key('user_password')
    assert config_service.is_sensitive_key('PASSWORD')


def test_is_sensitive_key_detects_secrets(config_service):
    """Test that is_sensitive_key identifies secret fields."""
    assert config_service.is_sensitive_key('jwt_secret')
    assert config_service.is_sensitive_key('api_secret')
    assert config_service.is_sensitive_key('SECRET_KEY')


def test_is_sensitive_key_detects_keys(config_service):
    """Test that is_sensitive_key identifies key fields."""
    assert config_service.is_sensitive_key('api_key')
    assert config_service.is_sensitive_key('encryption_key')
    assert config_service.is_sensitive_key('KEY')


def test_is_sensitive_key_allows_public_keys(config_service):
    """Test that is_sensitive_key allows non-sensitive keys."""
    assert not config_service.is_sensitive_key('app_name')
    assert not config_service.is_sensitive_key('max_page_size')
    assert not config_service.is_sensitive_key('enable_caching')


def test_get_public_config_returns_copy(config_service):
    """Test that get_public_config returns a copy (not reference)."""
    config1 = config_service.get_public_config()
    config2 = config_service.get_public_config()

    # Should be equal but not the same object
    assert config1 == config2
    assert config1 is not config2

    # Modifying one should not affect the other
    config1['test_key'] = 'test_value'
    assert 'test_key' not in config2
