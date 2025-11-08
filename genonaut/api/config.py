"""Configuration management for the Genonaut API."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from genonaut.config_loader import construct_database_url, load_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _kebab_to_snake(s: str) -> str:
    """Convert kebab-case to snake_case."""
    return s.replace("-", "_")


def _convert_config_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert kebab-case keys to snake_case for Python compatibility."""
    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[_kebab_to_snake(key)] = _convert_config_keys(value)
        else:
            result[_kebab_to_snake(key)] = value
    return result


class Settings(BaseModel):
    """API configuration settings."""

    # Environment target (e.g., 'local-dev', 'cloud-prod')
    env_target: Optional[str] = Field(default=None)

    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "genonaut"
    db_user_ro: str = "genonaut_ro"
    db_user_rw: str = "genonaut_rw"
    db_user_admin: str = "genonaut_admin"
    db_user_admin_uuid: Optional[str] = None
    db_user_for_init: str = "postgres"
    db_echo: bool = False

    # Database passwords (from env vars only, never in config files)
    db_password_admin: Optional[str] = None
    db_password_rw: Optional[str] = None
    db_password_ro: Optional[str] = None
    db_password_for_init: Optional[str] = None

    # Computed database URL
    database_url: Optional[str] = None

    # API settings
    api_secret_key: str = "change-me-in-production"
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_debug: bool = False
    test_api_base_url: str = "http://0.0.0.0:8099"

    # Redis settings
    redis_ns: str = "genonaut_dev"
    redis_url: Optional[str] = None

    # ComfyUI integration settings
    comfyui_url: str = "http://localhost:8000"
    comfyui_timeout: int = 30
    comfyui_poll_interval: float = 2.0
    comfyui_max_wait_time: int = 900
    comfyui_output_dir: str = "/tmp/comfyui/output"
    comfyui_models_dir: str = "/tmp/comfyui_models"
    comfyui_default_checkpoint: str = "illustriousXL_v01.safetensors"
    comfyui_default_width: int = 832
    comfyui_default_height: int = 1216
    comfyui_default_batch_size: int = 1
    comfyui_mock_url: str = "http://localhost:8189"
    comfyui_mock_output_dir: str = "test/_infra/mock_services/comfyui/output"
    comfyui_mock_models_dir: str = "test/_infra/mock_services/comfyui/models"
    comfyui_mock_port: int = 8189

    # Celery settings
    celery_result_backend: Optional[str] = None
    celery_broker_url: Optional[str] = None

    # Database timeout configuration
    statement_timeout: str = "15s"

    # Database connection pool configuration
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 1800  # 30 minutes in seconds
    db_pool_pre_ping: bool = True
    lock_timeout: str = "5s"
    idle_in_transaction_session_timeout: str = "30s"

    # Debugging configuration
    enable_faulthandler: bool = True  # Enable stack trace dumping with SIGUSR1

    # Seed data configuration (from base.json)
    seed_data: Optional[Dict[str, str]] = None
    seed_data_premade: Optional[Dict[str, str]] = None
    seed_data_generator: Optional[Dict[str, Any]] = None
    backup_dir: Optional[str] = None
    storage_dir: Optional[str] = None
    images_dir: Optional[str] = None

    # Performance configuration
    performance: Optional[Dict[str, Any]] = None

    # Query strategy configuration
    content_query_strategy: str = Field(
        default="raw_sql",
        description="Query execution strategy for unified content queries: 'orm' or 'raw_sql'"
    )

    # Celery configuration
    celery: Optional[Dict[str, Any]] = None

    class Config:
        case_sensitive = False
        extra = "ignore"

    @field_validator("database_url", mode="before")
    @classmethod
    def construct_db_url(cls, v: Optional[str], info) -> Optional[str]:
        """Construct database URL if not provided."""
        if v:
            return v

        # Try to construct from environment and other fields
        try:
            # Get the config from validation context if available
            # For now, we'll construct it in get_settings()
            return None
        except Exception:
            return None

    @property
    def environment_type(self) -> str:
        """Extract environment type from ENV_TARGET (e.g., 'local-dev' -> 'dev')."""
        if not self.env_target:
            return "dev"

        # Extract the type portion (e.g., 'local-dev' -> 'dev', 'cloud-prod' -> 'prod')
        if "-" in self.env_target:
            return self.env_target.split("-")[-1]
        return self.env_target

    @field_validator("statement_timeout", "lock_timeout", "idle_in_transaction_session_timeout")
    @classmethod
    def validate_timeout(cls, value: str, info) -> str:
        """Validate and normalize timeout format."""
        field_name = info.field_name
        if value is None:
            raise ValueError(f"{field_name} must include a duration like '15s' or '500ms'")

        if isinstance(value, (int, float)):
            # Force string conversion before validation so that units are required
            value = str(value)

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be provided as a string")

        cleaned_value = value.strip().lower()
        if not re.fullmatch(r"\d+(ms|s|min)", cleaned_value):
            raise ValueError(
                f"{field_name} must be an integer followed by a unit: 'ms', 's', or 'min'"
            )

        return cleaned_value


_LAST_SETTINGS: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance.

    Loads configuration from:
    1. JSON config files (base.json + environment-specific)
    2. Environment variables (including from .env files)

    Returns:
        Settings instance with complete configuration
    """
    global _LAST_SETTINGS
    # Get config path from environment (set by CLI)
    config_path = os.getenv("APP_CONFIG_PATH")
    env_target = os.getenv("ENV_TARGET")

    if not config_path:
        # Fallback for backward compatibility
        config_path = "config/local-dev.json"
        env_target = env_target or "local-dev"

    # Derive env file from ENV_TARGET if not explicitly set
    env_file = None
    if env_target:
        env_file = f"env/.env.{env_target}"

    # Load configuration (this also loads .env files)
    config = load_config(config_path, env_file=env_file)

    # Convert kebab-case keys to snake_case
    config = _convert_config_keys(config)

    # Set ENV_TARGET in config
    if env_target:
        config["env_target"] = env_target

    # Get passwords from environment (never from config files)
    config["db_password_admin"] = os.getenv("DB_PASSWORD_ADMIN")
    config["db_password_rw"] = os.getenv("DB_PASSWORD_RW")
    config["db_password_ro"] = os.getenv("DB_PASSWORD_RO")
    config["db_password_for_init"] = os.getenv("DB_PASSWORD_FOR_INIT")

    # Get API secret from environment
    if "API_SECRET_KEY" in os.environ:
        config["api_secret_key"] = os.getenv("API_SECRET_KEY")

    # Get Redis URL from environment
    if "REDIS_URL" in os.environ:
        config["redis_url"] = os.getenv("REDIS_URL")

    # Get Celery URLs from environment
    if "CELERY_BROKER_URL" in os.environ:
        config["celery_broker_url"] = os.getenv("CELERY_BROKER_URL")
    else:
        # Fallback to Redis URL
        config["celery_broker_url"] = config.get("redis_url") or config.get("celery_result_backend")

    # Create settings instance
    settings = Settings(**config)

    # Construct database URL if not already set
    if not settings.database_url and settings.db_password_admin:
        try:
            # Build a config dict for construct_database_url (needs kebab-case)
            db_config = {
                "db-host": settings.db_host,
                "db-port": settings.db_port,
                "db-name": settings.db_name,
                "db-user-admin": settings.db_user_admin,
            }
            settings.database_url = construct_database_url(db_config)
        except ValueError:
            pass  # Database URL will remain None if password not available

    _LAST_SETTINGS = settings
    return settings


def get_cached_settings() -> Optional[Settings]:
    """Return the most recently loaded settings instance if available."""

    return _LAST_SETTINGS
