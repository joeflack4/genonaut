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
    api_environment: str = "dev"  # dev, demo, or test
    
    class Config:
        env_file = PROJECT_ROOT / "env" / ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
