"""Unit tests for API configuration."""

import os
import pytest
from unittest.mock import patch

from genonaut.api.config import Settings, get_settings


class TestSettings:
    """Test the Settings configuration class."""
    
    def test_settings_defaults(self):
        """Test default settings values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.api_secret_key == "your-secret-key-change-this-in-production"
            assert settings.api_environment == "dev"
            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 8000
            assert settings.api_debug is False
    
    def test_settings_from_env(self):
        """Test settings loaded from environment variables."""
        env_vars = {
            "API_SECRET_KEY": "test-secret-key",
            "API_ENVIRONMENT": "test-env",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "API_DEBUG": "true"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.api_secret_key == "test-secret-key"
            assert settings.api_environment == "test-env"
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000
            assert settings.api_debug is True
    
    def test_settings_database_url_demo_generation(self):
        """Test demo database URL generation."""
        # Set explicit demo URL
        env_vars = {
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/genonaut_main",
            "DATABASE_URL_DEMO": "postgresql://user:pass@localhost:5432/genonaut_test_env",
            "API_ENVIRONMENT": "test_env"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            # Should use the explicit demo URL
            expected_demo_url = "postgresql://user:pass@localhost:5432/genonaut_test_env"
            assert settings.database_url_demo == expected_demo_url
    
    def test_settings_custom_demo_url(self):
        """Test custom demo database URL."""
        env_vars = {
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/genonaut_main",
            "DATABASE_URL_DEMO": "postgresql://demo:pass@localhost:5432/custom_demo"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.database_url_demo == "postgresql://demo:pass@localhost:5432/custom_demo"

    def test_settings_support_test_environment(self):
        """Test that the test environment loads dedicated database settings."""
        env_vars = {
            "API_ENVIRONMENT": "test",
            "DATABASE_URL_TEST": "postgresql://tester:pass@localhost:5432/genonaut_test_env"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.api_environment == "test"
            assert settings.database_url_test == "postgresql://tester:pass@localhost:5432/genonaut_test_env"
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_settings_validation_port_range(self):
        """Test port validation."""
        with patch.dict(os.environ, {"API_PORT": "70000"}, clear=True):
            # Should not raise an error for high port numbers
            settings = Settings()
            assert settings.api_port == 70000
        
        with patch.dict(os.environ, {"API_PORT": "0"}, clear=True):
            settings = Settings()
            assert settings.api_port == 0
    
    def test_settings_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        # Test valid boolean values that Pydantic accepts
        valid_test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False)
        ]
        
        for env_value, expected in valid_test_cases:
            with patch.dict(os.environ, {"API_DEBUG": env_value}, clear=True):
                settings = Settings()
                assert settings.api_debug is expected, f"Failed for env_value: {env_value}"
        
        # Test default value when not set
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.api_debug is False, "Default should be False"
