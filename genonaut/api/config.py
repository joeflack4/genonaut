"""Configuration management for the Genonaut API."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env_path = PROJECT_ROOT / "env" / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """API configuration settings."""

    # Existing database settings (inherited from existing setup)
    database_url: Optional[str] = None
    database_url_demo: Optional[str] = None
    database_url_test: Optional[str] = None
    db_host: str
    db_port: str
    db_name: str
    db_name_demo: str
    db_name_test: str
    db_password_admin: Optional[str] = None
    db_password_rw: Optional[str] = None
    db_password_ro: Optional[str] = None
    db_user: str = "postgres"
    db_password: Optional[str] = None
    db_echo: bool = False

    # New API settings
    api_secret_key: str
    api_host: str
    api_port: int
    api_debug: bool
    app_env: Literal["dev", "demo", "test"]

    # ComfyUI integration settings
    comfyui_url: str
    comfyui_timeout: int = 30
    comfyui_poll_interval: float = 2.0  # seconds between status polls
    comfyui_max_wait_time: int = 900  # maximum seconds to wait for a workflow to complete
    comfyui_output_dir: str
    comfyui_models_dir: str
    comfyui_default_checkpoint: str = "illustriousXL_v01.safetensors"
    comfyui_default_width: int = 832
    comfyui_default_height: int = 1216
    comfyui_default_batch_size: int = 1

    # ComfyUI Mock Server settings (for testing)
    comfyui_mock_url: str = "http://localhost:8189"
    comfyui_mock_port: int = 8189

    # Redis settings
    redis_url_demo: str
    redis_url_test: str
    redis_url_dev: str
    redis_ns_demo: str
    redis_ns_test: str
    redis_ns_dev: str

    # Celery settings
    celery_broker_url_demo: Optional[str] = None
    celery_result_backend_demo: Optional[str] = None
    celery_broker_url_test: Optional[str] = None
    celery_result_backend_test: Optional[str] = None
    celery_broker_url_dev: Optional[str] = None
    celery_result_backend_dev: Optional[str] = None

    class Config:
        env_file = PROJECT_ROOT / "env" / ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def redis_url(self) -> str:
        """Get Redis URL based on current environment."""
        return {
            "demo": self.redis_url_demo,
            "test": self.redis_url_test,
            "dev": self.redis_url_dev,
        }[self.app_env]

    @property
    def redis_ns(self) -> str:
        """Get Redis namespace based on current environment."""
        return {
            "demo": self.redis_ns_demo,
            "test": self.redis_ns_test,
            "dev": self.redis_ns_dev,
        }[self.app_env]

    @property
    def celery_broker_url(self) -> str:
        """Get Celery broker URL based on current environment."""
        fallback = self.redis_url
        return {
            "demo": self.celery_broker_url_demo or fallback,
            "test": self.celery_broker_url_test or fallback,
            "dev": self.celery_broker_url_dev or fallback,
        }[self.app_env]

    @property
    def celery_result_backend(self) -> str:
        """Get Celery result backend URL based on current environment."""
        fallback = self.redis_url
        return {
            "demo": self.celery_result_backend_demo or fallback,
            "test": self.celery_result_backend_test or fallback,
            "dev": self.celery_result_backend_dev or fallback,
        }[self.app_env]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
