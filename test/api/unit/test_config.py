"""Unit tests for API configuration."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from genonaut.config_loader import (
    apply_env_overrides,
    construct_database_url,
    deep_merge,
    load_config,
    load_config_files,
    load_env_for_runtime,
)
from genonaut.api.config import Settings, get_settings


class TestDeepMerge:
    """Test deep merge functionality."""

    def test_deep_merge_simple(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}
        # Ensure original not modified
        assert base == {"a": 1, "b": 2}

    def test_deep_merge_nested(self):
        """Test nested dictionary merge."""
        base = {"db": {"host": "localhost", "port": 5432}, "api": {"debug": False}}
        override = {"db": {"port": 5433, "name": "test"}, "api": {"debug": True}}
        result = deep_merge(base, override)
        assert result == {
            "db": {"host": "localhost", "port": 5433, "name": "test"},
            "api": {"debug": True},
        }

    def test_deep_merge_deep_nesting(self):
        """Test deeply nested merge."""
        base = {"a": {"b": {"c": {"d": 1}}}}
        override = {"a": {"b": {"c": {"e": 2}}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": {"d": 1, "e": 2}}}}

    def test_deep_merge_override_dict_with_value(self):
        """Test overriding a dict with a simple value."""
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        result = deep_merge(base, override)
        assert result == {"a": "string"}


class TestApplyEnvOverrides:
    """Test environment variable override functionality."""

    def test_env_override_basic(self):
        """Test basic env var override."""
        config = {"db-host": "localhost", "db-port": 5432}
        with patch.dict(os.environ, {"DB_HOST": "remotehost", "DB_PORT": "5433"}):
            result = apply_env_overrides(config)
            assert result["db-host"] == "remotehost"
            assert result["db-port"] == 5433

    def test_env_override_case_insensitive(self):
        """Test case-insensitive matching."""
        config = {"api-debug": False}
        with patch.dict(os.environ, {"API_DEBUG": "true"}):
            result = apply_env_overrides(config)
            assert result["api-debug"] is True

    def test_env_override_underscore_to_dash(self):
        """Test underscore to dash conversion."""
        config = {"redis-ns": "genonaut_dev"}
        with patch.dict(os.environ, {"REDIS_NS": "genonaut_test"}):
            result = apply_env_overrides(config)
            assert result["redis-ns"] == "genonaut_test"

    def test_env_override_boolean_conversion(self):
        """Test boolean conversion from env vars."""
        config = {"flag1": False, "flag2": True}
        with patch.dict(os.environ, {"FLAG1": "true", "FLAG2": "false"}):
            result = apply_env_overrides(config)
            assert result["flag1"] is True
            assert result["flag2"] is False

    def test_env_override_int_conversion(self):
        """Test integer conversion from env vars."""
        config = {"port": 8000}
        with patch.dict(os.environ, {"PORT": "9000"}):
            result = apply_env_overrides(config)
            assert result["port"] == 9000

    def test_env_override_no_change_if_not_in_config(self):
        """Test that env vars not in config don't get added."""
        config = {"db-host": "localhost"}
        with patch.dict(os.environ, {"RANDOM_VAR": "value"}):
            result = apply_env_overrides(config)
            # Should not add random-var
            assert "random-var" not in result
            assert result == {"db-host": "localhost"}


class TestConstructDatabaseUrl:
    """Test DATABASE_URL construction."""

    def test_construct_database_url_basic(self):
        """Test basic database URL construction."""
        config = {
            "db-host": "localhost",
            "db-port": 5432,
            "db-name": "genonaut",
            "db-user-admin": "admin",
        }
        with patch.dict(os.environ, {"DB_PASSWORD_ADMIN": "secret123"}, clear=False):
            url = construct_database_url(config)
            # Should use config values when no env overrides present
            assert "admin:secret123@localhost:5432/genonaut" in url

    def test_construct_database_url_env_override(self):
        """Test database URL with env var overrides."""
        config = {
            "db-host": "localhost",
            "db-port": 5432,
            "db-name": "genonaut",
            "db-user-admin": "admin",
        }
        with patch.dict(
            os.environ,
            {
                "DB_PASSWORD_ADMIN": "secret123",
                "DB_HOST": "remotehost",
                "DB_PORT": "5433",
            },
            clear=False,
        ):
            url = construct_database_url(config)
            # Env vars should take precedence
            assert "remotehost:5433" in url
            assert "secret123" in url

    def test_construct_database_url_missing_password(self):
        """Test that missing password raises error."""
        config = {
            "db-host": "localhost",
            "db-port": 5432,
            "db-name": "genonaut",
            "db-user-admin": "admin",
        }
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DB_PASSWORD_ADMIN.*required"):
                construct_database_url(config)


class TestLoadConfigFiles:
    """Test config file loading and merging."""

    def test_load_config_files_merge(self):
        """Test loading and merging base + env-specific config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create base config
            base_path = Path(tmpdir) / "config" / "base.json"
            base_path.parent.mkdir(parents=True)
            base_config = {
                "seed-data": {"main": "path1"},
                "db-host": "localhost",
                "db-port": 5432,
            }
            with open(base_path, "w") as f:
                json.dump(base_config, f)

            # Create env-specific config
            env_path = Path(tmpdir) / "config" / "local-dev.json"
            env_config = {"db-port": 5433, "db-name": "genonaut_dev"}
            with open(env_path, "w") as f:
                json.dump(env_config, f)

            # Mock PROJECT_ROOT
            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                result = load_config_files("config/local-dev.json")

            # Should have merged values
            assert result["seed-data"] == {"main": "path1"}
            assert result["db-host"] == "localhost"
            assert result["db-port"] == 5433  # Overridden
            assert result["db-name"] == "genonaut_dev"  # Added

    def test_load_config_files_missing_base(self):
        """Test error when base config is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                with pytest.raises(FileNotFoundError, match="Base config not found"):
                    load_config_files("config/local-dev.json")

    def test_load_config_files_missing_env(self):
        """Test error when env-specific config is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create base config
            base_path = Path(tmpdir) / "config" / "base.json"
            base_path.parent.mkdir(parents=True)
            with open(base_path, "w") as f:
                json.dump({}, f)

            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                with pytest.raises(FileNotFoundError, match="Environment config not found"):
                    load_config_files("config/nonexistent.json")


class TestLoadEnvForRuntime:
    """Test environment file loading."""

    def test_load_env_for_runtime_shared_only(self):
        """Test loading shared env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_path = Path(tmpdir) / "env" / ".env.shared"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text("SHARED_VAR=shared_value\n")

            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                with patch.dict(os.environ, {}, clear=True):
                    load_env_for_runtime(None)
                    assert os.environ.get("SHARED_VAR") == "shared_value"

    def test_load_env_for_runtime_with_env_file(self):
        """Test loading shared + env-specific file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Shared env
            shared_path = Path(tmpdir) / "env" / ".env.shared"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text("SHARED_VAR=shared\nOVERRIDE_ME=shared\n")

            # Env-specific
            env_path = Path(tmpdir) / "env" / ".env.local-dev"
            env_path.write_text("ENV_VAR=dev_value\nOVERRIDE_ME=dev\n")

            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                with patch.dict(os.environ, {}, clear=True):
                    load_env_for_runtime("env/.env.local-dev")
                    assert os.environ.get("SHARED_VAR") == "shared"
                    assert os.environ.get("ENV_VAR") == "dev_value"
                    assert os.environ.get("OVERRIDE_ME") == "dev"  # env-specific wins

    def test_load_env_for_runtime_missing_file_silent(self):
        """Test that missing env file is silently skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                # Should not raise an error, just skip the missing file
                load_env_for_runtime("env/.env.nonexistent")
                # Test passes if no exception is raised


class TestLoadConfig:
    """Test complete config loading (integration)."""

    def test_load_config_complete(self):
        """Test full config loading with all features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup config files
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()

            base_config = {"db-host": "localhost", "db-port": 5432, "api-debug": False}
            (config_dir / "base.json").write_text(json.dumps(base_config))

            env_config = {"db-port": 5433, "db-name": "test_db"}
            (config_dir / "local-test.json").write_text(json.dumps(env_config))

            # Setup env files
            env_dir = Path(tmpdir) / "env"
            env_dir.mkdir()

            (env_dir / ".env.shared").write_text("SHARED_SECRET_TEST=secret123\n")
            (env_dir / ".env.local-test").write_text(
                "TEST_VAR_CUSTOM=test_value\nDB_HOST=envhost\n"
            )

            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                # Don't clear environ, just add our test vars
                old_env = os.environ.copy()
                try:
                    result = load_config(
                        "config/local-test.json", "env/.env.local-test", apply_overrides=True
                    )

                    # Check merged config (env vars from test/conftest.py may override some values)
                    assert result["db-host"] == "envhost"  # Overridden by our test env var
                    assert "db-port" in result  # Should exist (may be overridden by env)
                    assert "db-name" in result  # Should exist (may be overridden by env)
                    assert result["api-debug"] is False  # From base config
                    # Env vars from our test files should be loaded
                    assert os.environ.get("SHARED_SECRET_TEST") == "secret123"
                    assert os.environ.get("TEST_VAR_CUSTOM") == "test_value"
                finally:
                    # Restore old environment
                    os.environ.clear()
                    os.environ.update(old_env)


class TestSettings:
    """Test the Settings configuration class."""

    def test_settings_with_config_path(self):
        """Test Settings loading from config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup minimal config
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()

            base_config = {
                "db-host": "localhost",
                "db-port": 5432,
                "db-name": "genonaut",
                "api-port": 8001,
                "api-host": "0.0.0.0",
            }
            (config_dir / "base.json").write_text(json.dumps(base_config))
            (config_dir / "local-dev.json").write_text(json.dumps({}))

            env_dir = Path(tmpdir) / "env"
            env_dir.mkdir()
            (env_dir / ".env.shared").write_text("API_SECRET_KEY=test_key\n")

            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                with patch("genonaut.api.config.PROJECT_ROOT", Path(tmpdir)):
                    with patch.dict(
                        os.environ,
                        {
                            "APP_CONFIG_PATH": str(config_dir / "local-dev.json"),
                            "ENV_TARGET": "local-dev",
                        },
                        clear=True,
                    ):
                        # Clear the cache
                        get_settings.cache_clear()
                        settings = get_settings()

                        assert settings.db_host == "localhost"
                        assert settings.db_port == 5432
                        assert settings.api_port == 8001
                        assert settings.env_target == "local-dev"
                        assert settings.environment_type == "dev"

    def test_settings_environment_type_extraction(self):
        """Test extracting environment type from ENV_TARGET."""
        test_cases = [
            ("local-dev", "dev"),
            ("local-demo", "demo"),
            ("local-test", "test"),
            ("cloud-prod", "prod"),
            ("cloud-dev", "dev"),
            ("dev", "dev"),  # No dash
            (None, "dev"),  # Default
        ]

        for env_target, expected_type in test_cases:
            settings = Settings(env_target=env_target)
            assert settings.environment_type == expected_type

    def test_settings_database_url_construction(self):
        """Test database URL is constructed from components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()

            config = {
                "db-host": "dbhost",
                "db-port": 5432,
                "db-name": "testdb",
                "db-user-admin": "admin",
            }
            (config_dir / "base.json").write_text(json.dumps(config))
            (config_dir / "local-test.json").write_text(json.dumps({}))

            env_dir = Path(tmpdir) / "env"
            env_dir.mkdir()
            (env_dir / ".env.shared").write_text("DB_PASSWORD_ADMIN=secret\n")

            with patch("genonaut.config_loader.PROJECT_ROOT", Path(tmpdir)):
                with patch("genonaut.api.config.PROJECT_ROOT", Path(tmpdir)):
                    with patch.dict(
                        os.environ,
                        {"APP_CONFIG_PATH": str(config_dir / "local-test.json")},
                        clear=True,
                    ):
                        get_settings.cache_clear()
                        settings = get_settings()

                        assert settings.database_url == "postgresql://admin:secret@dbhost:5432/testdb"

    def test_settings_singleton(self):
        """Test that get_settings returns cached instance."""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
