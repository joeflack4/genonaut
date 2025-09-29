"""Configuration management for Markdown Manager."""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class AuthMethod(Enum):
    """Supported GitHub authentication methods."""
    TOKEN = "token"           # Personal access token
    APP = "app"              # GitHub App authentication
    OAUTH = "oauth"          # OAuth flow


class Environment(Enum):
    """Environment types for configuration profiles."""
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"
    TEST = "test"


@dataclass
class GitHubAppConfig:
    """GitHub App authentication configuration."""
    app_id: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_content: Optional[str] = None
    installation_id: Optional[str] = None


@dataclass
class OAuthConfig:
    """OAuth authentication configuration."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    scopes: List[str] = field(default_factory=lambda: ["repo"])


@dataclass
class RepositoryConfig:
    """Configuration for a specific repository."""
    owner: str
    name: str
    labels: Dict[str, str] = field(default_factory=dict)
    default_assignees: List[str] = field(default_factory=list)
    default_milestone: Optional[str] = None
    sync_enabled: bool = True


@dataclass
class GitHubConfig:
    """Enhanced GitHub configuration settings with multiple auth methods."""

    # Authentication
    auth_method: AuthMethod = AuthMethod.TOKEN
    token: Optional[str] = None
    app_config: Optional[GitHubAppConfig] = None
    oauth_config: Optional[OAuthConfig] = None

    # Repository settings (for backward compatibility)
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None

    # Multiple repositories support
    repositories: List[RepositoryConfig] = field(default_factory=list)

    # API settings
    base_url: str = "https://api.github.com"
    user_agent: str = "md-manager/1.0"
    max_retries: int = 3
    rate_limit_threshold: int = 10

    # Sync settings
    sync_enabled: bool = False
    auto_sync_interval: int = 300  # seconds

    # Default settings (for backward compatibility)
    labels: Dict[str, str] = field(default_factory=dict)
    default_assignees: list = field(default_factory=list)
    default_milestone: Optional[str] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.rate_limit_threshold < 1:
            raise ValueError("rate_limit_threshold must be positive")
        if self.auto_sync_interval < 60:
            raise ValueError("auto_sync_interval must be at least 60 seconds")


class Config:
    """Configuration management with JSON file support and CLI override precedence."""

    DEFAULT_CONFIG_NAMES = [
        "md-manager.yml",
        "md-manager.yaml",
        "md-manager.json",
        "md_manager.yml",
        "md_manager.yaml",
        "md_manager.json"
    ]

    def __init__(self,
                 config_path: Optional[str] = None,
                 cli_options: Optional[Dict[str, Any]] = None,
                 environment: Optional[Environment] = None,
                 load_dotenv: bool = True):
        """
        Initialize configuration with enhanced profile and environment support.

        Args:
            config_path: Explicit path to config file
            cli_options: CLI options that override config file values
            environment: Environment profile (dev, staging, prod, test)
            load_dotenv: Whether to load .env files
        """
        self.config_data = {}
        self.cli_options = cli_options or {}
        self.environment = environment

        # Load .env files if available and requested
        if load_dotenv and DOTENV_AVAILABLE:
            self._load_env_files()

        # Load config file
        if config_path:
            self._load_config_file(config_path)
        else:
            self._load_default_config()

        # Apply environment-specific overrides
        if environment:
            self._apply_environment_overrides(environment)

    def _load_config_file(self, config_path: str) -> None:
        """Load configuration from specified file (JSON or YAML)."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith(('.yml', '.yaml')):
                    self.config_data = yaml.safe_load(f) or {}
                else:
                    self.config_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {config_path}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            file_type = "YAML" if config_path.endswith(('.yml', '.yaml')) else "JSON"
            raise ValueError(f"Invalid {file_type} in config file {config_path}: {e}")

    def _load_default_config(self) -> None:
        """Load configuration from default locations."""
        current_dir = Path.cwd()

        for config_name in self.DEFAULT_CONFIG_NAMES:
            config_path = current_dir / config_name
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        if config_name.endswith(('.yml', '.yaml')):
                            self.config_data = yaml.safe_load(f) or {}
                        else:
                            self.config_data = json.load(f)
                    return
                except (json.JSONDecodeError, yaml.YAMLError, OSError):
                    # Skip invalid config files and try the next one
                    continue

        # No config file found - use empty config
        self.config_data = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with CLI precedence.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value (CLI override > config file > default)
        """
        # CLI options take precedence over config file
        if key in self.cli_options:
            return self.cli_options[key]

        return self.config_data.get(key, default)

    def get_collate_config(self) -> Dict[str, Any]:
        """Get configuration specific to collate command."""
        collate_config = self.config_data.get('collate', {})

        # Merge with CLI options (CLI takes precedence)
        result = collate_config.copy()
        for key, value in self.cli_options.items():
            if value is not None:  # Only override with non-None CLI values
                result[key] = value

        return result

    def has_config_file(self) -> bool:
        """Check if a config file was found and loaded."""
        return bool(self.config_data)

    def load_env_vars(self) -> Dict[str, Any]:
        """
        Load GitHub configuration from environment variables.

        Returns:
            Configuration dictionary from environment variables
        """
        env_config = {}
        env_prefix = "MD_MANAGER_"

        # Map environment variables to config keys
        env_mappings = {
            f"{env_prefix}TOKEN": "token",
            f"{env_prefix}GITHUB_TOKEN": "token",  # Alternative name
            f"{env_prefix}REPO_OWNER": "repo_owner",
            f"{env_prefix}REPO_NAME": "repo_name",
            f"{env_prefix}BASE_URL": "base_url",
            f"{env_prefix}USER_AGENT": "user_agent",
            f"{env_prefix}MAX_RETRIES": "max_retries",
            f"{env_prefix}RATE_LIMIT_THRESHOLD": "rate_limit_threshold",
            f"{env_prefix}SYNC_ENABLED": "sync_enabled",
            f"{env_prefix}AUTO_SYNC_INTERVAL": "auto_sync_interval",
            f"{env_prefix}DEFAULT_MILESTONE": "default_milestone"
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ['max_retries', 'rate_limit_threshold', 'auto_sync_interval']:
                    try:
                        env_config[config_key] = int(value)
                    except ValueError:
                        raise ValueError(f"Invalid integer value for {env_var}: {value}")
                elif config_key == 'sync_enabled':
                    env_config[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    env_config[config_key] = value

        # Handle default assignees from environment (comma-separated)
        assignees_env = os.getenv(f"{env_prefix}DEFAULT_ASSIGNEES")
        if assignees_env:
            env_config['default_assignees'] = [a.strip() for a in assignees_env.split(',') if a.strip()]

        return env_config

    def get_github_config(self) -> GitHubConfig:
        """
        Get GitHub configuration, merging file config with environment variables.

        Returns:
            GitHubConfig instance
        """
        # Get GitHub section from config file
        file_github_config = self.config_data.get('github', {})

        # Load from environment
        env_config = self.load_env_vars()

        # Merge configurations (env takes precedence)
        merged_config = file_github_config.copy()
        merged_config.update(env_config)

        # Override with CLI options if present
        for key, value in self.cli_options.items():
            if value is not None and key in GitHubConfig.__dataclass_fields__:
                merged_config[key] = value

        # Create GitHubConfig instance
        try:
            return GitHubConfig(**merged_config)
        except TypeError as e:
            # Handle unexpected configuration keys
            valid_fields = {f.name for f in GitHubConfig.__dataclass_fields__.values()}
            invalid_keys = set(merged_config.keys()) - valid_fields
            if invalid_keys:
                raise ValueError(f"Invalid GitHub configuration keys: {', '.join(invalid_keys)}")
            raise ValueError(f"GitHub configuration error: {e}")

    def validate_github_config(self, config: Optional[GitHubConfig] = None) -> GitHubConfig:
        """
        Validate GitHub configuration and return validated config.

        Args:
            config: Optional config to validate, or load from sources

        Returns:
            Validated GitHubConfig instance

        Raises:
            ValueError: If configuration is invalid
        """
        if config is None:
            config = self.get_github_config()

        errors = []

        # Check required fields for sync operations
        if config.sync_enabled:
            if not config.token:
                errors.append("GitHub token is required when sync is enabled")
            if not config.repo_owner:
                errors.append("Repository owner is required when sync is enabled")
            if not config.repo_name:
                errors.append("Repository name is required when sync is enabled")

        # Validate URLs
        if config.base_url and not config.base_url.startswith(('http://', 'https://')):
            errors.append("base_url must start with http:// or https://")

        # Validate user agent format
        if not config.user_agent or '/' not in config.user_agent:
            errors.append("user_agent must be in format 'name/version'")

        if errors:
            raise ValueError("GitHub configuration validation errors:\n" + "\n".join(f"- {error}" for error in errors))

        return config

    def _load_env_files(self) -> None:
        """Load environment variables from .env files."""
        env_files = [
            ".env",
            ".env.local",
            f".env.{self.environment.value}" if self.environment else None
        ]

        for env_file in env_files:
            if env_file and Path(env_file).exists():
                load_dotenv(env_file, override=False)

    def _apply_environment_overrides(self, environment: Environment) -> None:
        """Apply environment-specific configuration overrides."""
        env_key = f"environments.{environment.value}"
        env_config = self.config_data.get("environments", {}).get(environment.value, {})

        if env_config:
            # Merge environment-specific config with base config
            self._deep_merge(self.config_data, env_config)

    def _deep_merge(self, base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> None:
        """Deep merge override_dict into base_dict."""
        for key, value in override_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value

    def get_repository_config(self, repo_identifier: str) -> Optional[RepositoryConfig]:
        """
        Get configuration for a specific repository.

        Args:
            repo_identifier: Repository identifier in format "owner/name"

        Returns:
            RepositoryConfig if found, None otherwise
        """
        github_config = self.get_github_config()

        # Check repositories list
        for repo in github_config.repositories:
            if f"{repo.owner}/{repo.name}" == repo_identifier:
                return repo

        # Check backward compatibility with single repo config
        if (github_config.repo_owner and github_config.repo_name and
            f"{github_config.repo_owner}/{github_config.repo_name}" == repo_identifier):
            return RepositoryConfig(
                owner=github_config.repo_owner,
                name=github_config.repo_name,
                labels=github_config.labels,
                default_assignees=github_config.default_assignees,
                default_milestone=github_config.default_milestone,
                sync_enabled=github_config.sync_enabled
            )

        return None

    def list_configured_repositories(self) -> List[str]:
        """
        Get list of all configured repository identifiers.

        Returns:
            List of repository identifiers in format "owner/name"
        """
        github_config = self.get_github_config()
        repos = []

        # Add repositories from repositories list
        for repo in github_config.repositories:
            repos.append(f"{repo.owner}/{repo.name}")

        # Add backward compatibility repo if not already in list
        if github_config.repo_owner and github_config.repo_name:
            repo_id = f"{github_config.repo_owner}/{github_config.repo_name}"
            if repo_id not in repos:
                repos.append(repo_id)

        return repos

    def create_sample_config(self, output_path: str = "md-manager.yml") -> None:
        """
        Create a sample configuration file.

        Args:
            output_path: Path where to create the sample config file
        """
        sample_config = {
            'github': {
                # Authentication methods
                'auth_method': 'token',  # Options: token, app, oauth
                'token': '${MD_MANAGER_TOKEN}',  # For token auth

                # GitHub App authentication (alternative to token)
                'app_config': {
                    'app_id': '${GITHUB_APP_ID}',
                    'private_key_path': '${GITHUB_PRIVATE_KEY_PATH}',
                    'installation_id': '${GITHUB_INSTALLATION_ID}'
                },

                # OAuth configuration (alternative to token)
                'oauth_config': {
                    'client_id': '${GITHUB_CLIENT_ID}',
                    'client_secret': '${GITHUB_CLIENT_SECRET}',
                    'redirect_uri': 'http://localhost:8080/callback',
                    'scopes': ['repo']
                },

                # Single repository (backward compatibility)
                'repo_owner': 'your-username',
                'repo_name': 'your-repo',

                # Multiple repositories support
                'repositories': [
                    {
                        'owner': 'your-username',
                        'name': 'repo1',
                        'sync_enabled': True,
                        'labels': {'priority': 'high'},
                        'default_assignees': ['maintainer'],
                        'default_milestone': 'v1.0'
                    },
                    {
                        'owner': 'your-org',
                        'name': 'repo2',
                        'sync_enabled': True
                    }
                ],

                # API settings
                'base_url': 'https://api.github.com',
                'user_agent': 'md-manager/1.0',
                'max_retries': 3,
                'rate_limit_threshold': 10,
                'sync_enabled': False,
                'auto_sync_interval': 300,

                # Default settings
                'labels': {
                    'bug': '#d73a4a',
                    'enhancement': '#a2eeef',
                    'documentation': '#0075ca'
                },
                'default_assignees': [],
                'default_milestone': None
            },

            # Environment-specific configurations
            'environments': {
                'dev': {
                    'github': {
                        'base_url': 'https://api.github.com',
                        'sync_enabled': True,
                        'auto_sync_interval': 60
                    }
                },
                'staging': {
                    'github': {
                        'repo_name': 'your-repo-staging',
                        'sync_enabled': True
                    }
                },
                'prod': {
                    'github': {
                        'sync_enabled': False,
                        'auto_sync_interval': 600
                    }
                }
            }
        }

        output_file = Path(output_path)
        if output_path.endswith('.json'):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)


def find_config_file(start_dir: str = None) -> Optional[str]:
    """
    Find a config file in the specified directory or current working directory.

    Args:
        start_dir: Directory to search (defaults to current working directory)

    Returns:
        Path to config file if found, None otherwise
    """
    search_dir = Path(start_dir) if start_dir else Path.cwd()

    for config_name in Config.DEFAULT_CONFIG_NAMES:
        config_path = search_dir / config_name
        if config_path.exists():
            return str(config_path)

    return None