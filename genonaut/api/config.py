"""Configuration management for the Genonaut API."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

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
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "genonaut"
    db_name_demo: str = "genonaut_demo"
    db_name_test: str = "genonaut_test"
    db_password_admin: Optional[str] = None
    db_password_rw: Optional[str] = None
    db_password_ro: Optional[str] = None
    db_user: str = "postgres"
    db_password: Optional[str] = None
    db_echo: bool = False

    # New API settings
    api_secret_key: str = "your-secret-key-change-this-in-production"
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_debug: bool = False
    app_env: str = "dev"  # dev, demo, or test

    # ComfyUI integration settings
    comfyui_url: str = "http://localhost:8188"
    comfyui_timeout: int = 30
    comfyui_poll_interval: float = 2.0  # seconds between status polls
    comfyui_max_wait_time: int = 900  # maximum seconds to wait for a workflow to complete
    comfyui_output_dir: str = "/Users/joeflack4/Documents/ComfyUI/output"
    comfyui_models_dir: str = "/tmp/comfyui_models"  # @dev: configure actual ComfyUI models directory
    comfyui_default_checkpoint: str = "illustriousXL_v01.safetensors"
    comfyui_default_width: int = 832
    comfyui_default_height: int = 1216
    comfyui_default_batch_size: int = 1

    # Redis settings
    redis_url_demo: str = "redis://localhost:6379/2"
    redis_url_test: str = "redis://localhost:6379/3"
    redis_url_dev: str = "redis://localhost:6379/4"
    redis_ns_demo: str = "genonaut_demo"
    redis_ns_test: str = "genonaut_test"
    redis_ns_dev: str = "genonaut_dev"

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
