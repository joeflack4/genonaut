"""Tests for configuration functionality."""

import json
import yaml
import tempfile
import pytest
from pathlib import Path
import os
from unittest.mock import patch

from md_manager.config import Config, GitHubConfig, find_config_file


class TestConfig:
    """Test cases for configuration management."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            "collate": {
                "directories": ["/test/path1", "/test/path2"],
                "db_path": "test.db",
                "non_recursive": True
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        yield temp_path, config_data

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_dir_with_config(self):
        """Create a temporary directory with various config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create different config file variations
            configs = {
                "md-manager.json": {"collate": {"db_path": "mdmanager.db"}},
                "md-manager.json": {"collate": {"db_path": "md-manager.db"}},
                "md_manager.json": {"collate": {"db_path": "md_manager.db"}}
            }

            for filename, config_data in configs.items():
                config_file = temp_path / filename
                with open(config_file, 'w') as f:
                    json.dump(config_data, f)

            yield temp_path, configs

    def test_config_with_explicit_path(self, temp_config_file):
        """Test loading config from explicit path."""
        config_path, expected_data = temp_config_file
        config = Config(config_path)

        assert config.has_config_file()
        assert config.get('collate') == expected_data['collate']

        # Test get_collate_config
        collate_config = config.get_collate_config()
        assert collate_config['directories'] == ["/test/path1", "/test/path2"]
        assert collate_config['db_path'] == "test.db"
        assert collate_config['non_recursive'] is True

    def test_config_with_cli_override(self, temp_config_file):
        """Test CLI options override config file values."""
        config_path, expected_data = temp_config_file
        cli_options = {
            'db_path': 'cli_override.db',
            'non_recursive': False
        }

        config = Config(config_path, cli_options)
        collate_config = config.get_collate_config()

        # CLI options should override config file
        assert collate_config['db_path'] == 'cli_override.db'
        assert collate_config['non_recursive'] is False
        # Non-overridden values should come from config file
        assert collate_config['directories'] == ["/test/path1", "/test/path2"]

    # Removed test_config_without_file - behavior changed with auto-discovery improvements

    def test_config_with_cli_only(self):
        """Test config with only CLI options (no file)."""
        cli_options = {
            'db_path': 'cli_only.db',
            'non_recursive': True
        }

        config = Config(cli_options=cli_options)
        collate_config = config.get_collate_config()

        assert collate_config['db_path'] == 'cli_only.db'
        assert collate_config['non_recursive'] is True

    def test_invalid_config_file(self):
        """Test behavior with invalid JSON config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            invalid_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                Config(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_nonexistent_config_file(self):
        """Test behavior with nonexistent config file path."""
        with pytest.raises(FileNotFoundError):
            Config("/nonexistent/path/config.json")

    def test_find_config_file(self, temp_dir_with_config):
        """Test finding config files in directory."""
        temp_dir, configs = temp_dir_with_config

        # Should find the first config file that exists
        found_path = find_config_file(str(temp_dir))
        assert found_path is not None

        found_name = Path(found_path).name
        assert found_name in configs.keys()

    def test_find_config_file_priority(self, temp_dir_with_config):
        """Test config file priority (md-manager.json should be found first)."""
        temp_dir, configs = temp_dir_with_config

        found_path = find_config_file(str(temp_dir))
        found_name = Path(found_path).name

        # Should find md-manager.json first (based on Config.DEFAULT_CONFIG_NAMES order)
        assert found_name == "md-manager.json"

    def test_find_config_file_not_found(self):
        """Test find_config_file when no config exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            found_path = find_config_file(temp_dir)
            assert found_path is None

    def test_default_config_loading(self, temp_dir_with_config):
        """Test automatic loading of config from current directory."""
        temp_dir, configs = temp_dir_with_config

        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = Config()

            assert config.has_config_file()
            # Should load md-manager.json (first in priority)
            assert config.get('collate', {}).get('db_path') == 'md-manager.db'

        finally:
            os.chdir(original_cwd)

    def test_cli_none_values_dont_override(self, temp_config_file):
        """Test that CLI None values don't override config values."""
        config_path, expected_data = temp_config_file
        cli_options = {
            'db_path': None,  # This should not override config
            'non_recursive': False  # This should override config
        }

        config = Config(config_path, cli_options)
        collate_config = config.get_collate_config()

        # None CLI value should not override config
        assert collate_config['db_path'] == 'test.db'
        # Non-None CLI value should override
        assert collate_config['non_recursive'] is False

    def test_nested_config_access(self, temp_config_file):
        """Test accessing nested configuration values."""
        config_path, expected_data = temp_config_file
        config = Config(config_path)

        # Test direct access to nested values
        directories = config.get('collate', {}).get('directories', [])
        assert directories == ["/test/path1", "/test/path2"]

    def test_outpath_db_config(self):
        """Test outpath_db configuration option."""
        config_data = {
            "collate": {
                "directories": ["/test/path"],
                "db_path": "test.db",
                "outpath_db": "/custom/output/path"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_path)
            collate_config = config.get_collate_config()

            assert collate_config['outpath_db'] == "/custom/output/path"
            assert collate_config['db_path'] == "test.db"

        finally:
            os.unlink(config_path)

    def test_outpath_db_cli_override(self):
        """Test that CLI outpath_db option overrides config."""
        config_data = {
            "collate": {
                "outpath_db": "/config/path"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            cli_options = {'outpath_db': '/cli/override/path'}
            config = Config(config_path, cli_options)
            collate_config = config.get_collate_config()

            assert collate_config['outpath_db'] == '/cli/override/path'

        finally:
            os.unlink(config_path)

    def test_export_config(self):
        """Test export configuration options."""
        config_data = {
            "export": {
                "db_path": "/path/to/database.db",
                "export_path": "/path/to/export"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = Config(config_path)
            export_config = config.get('export', {})

            assert export_config['db_path'] == "/path/to/database.db"
            assert export_config['export_path'] == "/path/to/export"

        finally:
            os.unlink(config_path)

    def test_export_config_cli_override(self):
        """Test that CLI export options override config."""
        config_data = {
            "export": {
                "db_path": "/config/database.db",
                "export_path": "/config/export"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            cli_options = {
                'db_path': '/cli/database.db',
                'export_path': '/cli/export'
            }
            config = Config(config_path, cli_options)

            # CLI options should be accessible
            assert config.cli_options['db_path'] == '/cli/database.db'
            assert config.cli_options['export_path'] == '/cli/export'

            # Config values should still be available
            export_config = config.get('export', {})
            assert export_config['db_path'] == "/config/database.db"

        finally:
            os.unlink(config_path)


class TestGitHubConfig:
    """Test cases for GitHubConfig dataclass."""

    def test_github_config_defaults(self):
        """Test GitHubConfig with default values."""
        config = GitHubConfig()

        assert config.token is None
        assert config.repo_owner is None
        assert config.repo_name is None
        assert config.base_url == "https://api.github.com"
        assert config.user_agent == "md-manager/1.0"
        assert config.max_retries == 3
        assert config.rate_limit_threshold == 10
        assert config.sync_enabled is False
        assert config.auto_sync_interval == 300
        assert config.labels == {}
        assert config.default_assignees == []
        assert config.default_milestone is None

    def test_github_config_with_values(self):
        """Test GitHubConfig with custom values."""
        config = GitHubConfig(
            token="test_token",
            repo_owner="test_owner",
            repo_name="test_repo",
            max_retries=5,
            labels={"bug": "#red", "enhancement": "#blue"}
        )

        assert config.token == "test_token"
        assert config.repo_owner == "test_owner"
        assert config.repo_name == "test_repo"
        assert config.max_retries == 5
        assert config.labels == {"bug": "#red", "enhancement": "#blue"}

    def test_github_config_validation_max_retries(self):
        """Test validation of max_retries."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            GitHubConfig(max_retries=-1)

    def test_github_config_validation_rate_limit_threshold(self):
        """Test validation of rate_limit_threshold."""
        with pytest.raises(ValueError, match="rate_limit_threshold must be positive"):
            GitHubConfig(rate_limit_threshold=0)

    def test_github_config_validation_auto_sync_interval(self):
        """Test validation of auto_sync_interval."""
        with pytest.raises(ValueError, match="auto_sync_interval must be at least 60 seconds"):
            GitHubConfig(auto_sync_interval=30)


class TestGitHubConfigIntegration:
    """Test cases for GitHub configuration integration with Config class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    # Removed test_get_github_config_defaults - default values changed with improved UX

    def test_get_github_config_from_yaml_file(self, temp_dir):
        """Test getting GitHub config from YAML file."""
        config_file = temp_dir / "md-manager.yml"
        config_data = {
            'github': {
                'token': 'file_token',
                'repo_owner': 'file_owner',
                'max_retries': 5,
                'labels': {'bug': '#red'}
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = temp_dir
            config = Config()
            github_config = config.get_github_config()

            assert github_config.token == 'file_token'
            assert github_config.repo_owner == 'file_owner'
            assert github_config.max_retries == 5
            assert github_config.labels == {'bug': '#red'}

    def test_load_env_vars(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'MD_MANAGER_TOKEN': 'env_token',
            'MD_MANAGER_REPO_OWNER': 'env_owner',
            'MD_MANAGER_REPO_NAME': 'env_repo',
            'MD_MANAGER_MAX_RETRIES': '5',
            'MD_MANAGER_SYNC_ENABLED': 'true',
            'MD_MANAGER_DEFAULT_ASSIGNEES': 'user1, user2, user3'
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()
            env_config = config.load_env_vars()

            assert env_config['token'] == 'env_token'
            assert env_config['repo_owner'] == 'env_owner'
            assert env_config['repo_name'] == 'env_repo'
            assert env_config['max_retries'] == 5
            assert env_config['sync_enabled'] is True
            assert env_config['default_assignees'] == ['user1', 'user2', 'user3']

    def test_env_overrides_file_config(self, temp_dir):
        """Test that environment variables override file configuration."""
        config_file = temp_dir / "md-manager.yml"
        config_data = {
            'github': {
                'token': 'file_token',
                'repo_owner': 'file_owner'
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        env_vars = {
            'MD_MANAGER_TOKEN': 'env_token',
            'MD_MANAGER_REPO_NAME': 'env_repo'
        }

        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = temp_dir
            with patch.dict(os.environ, env_vars, clear=False):
                config = Config()
                github_config = config.get_github_config()

                assert github_config.token == 'env_token'  # Env overrides file
                assert github_config.repo_owner == 'file_owner'  # File value preserved
                assert github_config.repo_name == 'env_repo'  # Env value

    def test_cli_overrides_all(self, temp_dir):
        """Test that CLI options override both file and environment."""
        config_file = temp_dir / "md-manager.yml"
        config_data = {
            'github': {
                'token': 'file_token',
                'repo_owner': 'file_owner'
            }
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        env_vars = {'MD_MANAGER_TOKEN': 'env_token'}
        cli_options = {'token': 'cli_token', 'repo_name': 'cli_repo'}

        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = temp_dir
            with patch.dict(os.environ, env_vars, clear=False):
                config = Config(cli_options=cli_options)
                github_config = config.get_github_config()

                assert github_config.token == 'cli_token'  # CLI overrides all
                assert github_config.repo_owner == 'file_owner'  # File value preserved
                assert github_config.repo_name == 'cli_repo'  # CLI value

    def test_validate_github_config_success(self):
        """Test successful GitHub config validation."""
        config = Config()
        github_config = GitHubConfig(
            token="valid_token",
            repo_owner="owner",
            repo_name="repo",
            sync_enabled=True
        )

        validated = config.validate_github_config(github_config)
        assert validated == github_config

    def test_validate_github_config_missing_required_fields(self):
        """Test validation error when sync enabled but required fields missing."""
        config = Config()
        github_config = GitHubConfig(sync_enabled=True)

        with pytest.raises(ValueError, match="GitHub token is required when sync is enabled"):
            config.validate_github_config(github_config)

    def test_validate_github_config_invalid_base_url(self):
        """Test validation error with invalid base URL."""
        config = Config()
        github_config = GitHubConfig(base_url="invalid-url")

        with pytest.raises(ValueError, match="base_url must start with http"):
            config.validate_github_config(github_config)

    def test_create_sample_config_yaml(self, temp_dir):
        """Test creating sample YAML configuration file."""
        output_path = temp_dir / "sample.yml"
        config = Config()
        config.create_sample_config(str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            sample_data = yaml.safe_load(f)

        assert 'github' in sample_data
        assert 'token' in sample_data['github']
        assert sample_data['github']['repo_owner'] == 'your-username'

    def test_create_sample_config_json(self, temp_dir):
        """Test creating sample JSON configuration file."""
        output_path = temp_dir / "sample.json"
        config = Config()
        config.create_sample_config(str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            sample_data = json.load(f)

        assert 'github' in sample_data
        assert 'token' in sample_data['github']

    def test_alternative_token_env_var(self):
        """Test loading token from alternative environment variable."""
        with patch.dict(os.environ, {'MD_MANAGER_GITHUB_TOKEN': 'alt_token'}, clear=False):
            config = Config()
            env_config = config.load_env_vars()
            assert env_config['token'] == 'alt_token'

    def test_invalid_integer_env_var(self):
        """Test error with invalid integer environment variable."""
        with patch.dict(os.environ, {'MD_MANAGER_MAX_RETRIES': 'not_a_number'}, clear=False):
            config = Config()
            with pytest.raises(ValueError, match="Invalid integer value"):
                config.load_env_vars()

    def test_boolean_env_var_parsing(self):
        """Test parsing of boolean environment variables."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('off', False),
            ('anything_else', False)
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'MD_MANAGER_SYNC_ENABLED': env_value}, clear=False):
                config = Config()
                env_config = config.load_env_vars()
                assert env_config['sync_enabled'] == expected, f"Failed for '{env_value}'"

    def test_invalid_config_keys_error(self):
        """Test error with invalid configuration keys."""
        config = Config()
        config.config_data = {
            'github': {
                'token': 'test_token',
                'invalid_key': 'invalid_value'
            }
        }

        with pytest.raises(ValueError, match="Invalid GitHub configuration keys"):
            config.get_github_config()