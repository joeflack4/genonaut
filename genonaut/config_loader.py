"""Configuration loader for Genonaut.

Handles loading and merging of JSON configs and .env files with proper precedence.

Load order (lowest to highest precedence):
1. config/base.json
2. config/{ENV_TARGET}.json
3. env/.env.shared
4. env/.env.{ENV_TARGET}
5. process env (CI, shell)
6. local env/.env (developer overrides, optional)
"""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with values to override base

    Returns:
        Merged dictionary
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_env_for_runtime(env_file: Optional[str] = None) -> None:
    """Load environment variables with proper precedence.

    Load order (lowest to highest precedence):
    1. env/.env.shared
    2. env/.env.{ENV_TARGET} (passed as env_file)
    3. process environment (existing env vars from shell/CI)
    4. env/.env (developer local overrides, highest precedence)

    Args:
        env_file: Optional path to environment-specific .env file
    """
    shared = PROJECT_ROOT / "env" / ".env.shared"
    local_default = PROJECT_ROOT / "env" / ".env"

    # Capture the current process environment before loading any files
    # These should have higher precedence than .env.shared and env_file
    # but lower precedence than .env
    original_process_env = os.environ.copy()

    # 1) shared (base layer)
    if shared.exists():
        load_dotenv(shared, override=True)

    # 2) explicit env file (override values from shared)
    if env_file:
        env_path = Path(env_file)
        if not env_path.is_absolute():
            env_path = PROJECT_ROOT / env_file
        # Only load if file exists (optional)
        if env_path.exists():
            load_dotenv(env_path, override=True)

    # 3) restore original process env vars (they should override env files)
    # Only restore vars that were present before we started loading files
    for key, value in original_process_env.items():
        os.environ[key] = value

    # 4) developer .env (override EVERYTHING including process env)
    if local_default.exists():
        load_dotenv(local_default, override=True)


def load_config_files(config_path: str) -> Dict[str, Any]:
    """Load and merge JSON config files.

    Loads base.json and merges with environment-specific config.

    Args:
        config_path: Path to environment-specific config file

    Returns:
        Merged configuration dictionary
    """
    base_config_path = PROJECT_ROOT / "config" / "base.json"

    # Load base config
    if not base_config_path.exists():
        raise FileNotFoundError(f"Base config not found: {base_config_path}")

    with open(base_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Load and merge environment-specific config
    env_config_path = Path(config_path)
    if not env_config_path.is_absolute():
        env_config_path = PROJECT_ROOT / config_path

    if env_config_path.exists():
        with open(env_config_path, "r", encoding="utf-8") as f:
            env_config = json.load(f)
        config = deep_merge(config, env_config)
    else:
        raise FileNotFoundError(f"Environment config not found: {env_config_path}")

    return config


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to config.

    Environment variables can override config values using case-insensitive matching
    with underscores converted to dashes. For example:
    - DB_HOST overrides db-host
    - API_PORT overrides api-port

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with env var overrides applied
    """
    result = deepcopy(config)

    # Create a mapping of normalized keys to original keys
    key_map = {}
    for key in config.keys():
        normalized = key.lower().replace("-", "_")
        key_map[normalized] = key

    # Check environment variables
    for env_key, env_value in os.environ.items():
        normalized_env_key = env_key.lower()

        if normalized_env_key in key_map:
            config_key = key_map[normalized_env_key]

            # Try to convert to appropriate type
            # If the original config value is a bool, int, or float, convert
            if isinstance(result[config_key], bool):
                result[config_key] = env_value.lower() in ("true", "1", "yes")
            elif isinstance(result[config_key], int):
                try:
                    result[config_key] = int(env_value)
                except ValueError:
                    pass
            elif isinstance(result[config_key], float):
                try:
                    result[config_key] = float(env_value)
                except ValueError:
                    pass
            else:
                result[config_key] = env_value

    return result


def construct_database_url(config: Dict[str, Any]) -> str:
    """Construct DATABASE_URL from config components and env vars.

    Args:
        config: Configuration dictionary containing db-* keys

    Returns:
        Fully constructed database URL
    """
    # Get password from environment (required)
    password = os.getenv("DB_PASSWORD_ADMIN")
    if not password:
        raise ValueError("DB_PASSWORD_ADMIN environment variable is required")

    # Get other components from config or env (env takes precedence)
    host = os.getenv("DB_HOST") or config.get("db-host", "localhost")
    port = os.getenv("DB_PORT") or config.get("db-port", 5432)
    name = os.getenv("DB_NAME") or config.get("db-name", "genonaut")
    user = os.getenv("DB_USER_ADMIN") or config.get("db-user-admin", "genonaut_admin")

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def load_config(
    config_path: str,
    env_file: Optional[str] = None,
    apply_overrides: bool = True
) -> Dict[str, Any]:
    """Load complete configuration with env files and overrides.

    Args:
        config_path: Path to environment-specific JSON config
        env_file: Optional path to environment-specific .env file
        apply_overrides: Whether to apply env var overrides to config

    Returns:
        Complete configuration dictionary
    """
    # Load env files first
    load_env_for_runtime(env_file)

    # Load and merge JSON configs
    config = load_config_files(config_path)

    # Apply environment variable overrides if requested
    if apply_overrides:
        config = apply_env_overrides(config)

    return config
