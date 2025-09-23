"""Configuration management for synthetic data generator."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import uuid


class SeedDataConfig(BaseModel):
    """Configuration schema for seed data generation."""

    # Batch sizes
    batch_size_users: int = Field(default=1000, ge=1, le=10000)
    batch_size_content_items: int = Field(default=2000, ge=1, le=10000)
    batch_size_content_items_auto: int = Field(default=2000, ge=1, le=10000)
    batch_size_generation_jobs: int = Field(default=5000, ge=1, le=20000)

    # Target row counts
    target_rows_users: int = Field(default=1000, ge=1, le=100000)
    target_rows_content_items: int = Field(default=20000, ge=1, le=1000000)
    target_rows_content_items_auto: int = Field(default=100000, ge=1, le=1000000)

    # Generation parameters
    max_workers: int = Field(default=4, ge=1, le=16)
    prompt_min_general_phrases: int = Field(default=0, ge=0, le=10)
    prompt_max_general_phrases: int = Field(default=10, ge=0, le=10)
    prompt_min_domain_phrases: int = Field(default=4, ge=1, le=30)
    prompt_max_domain_phrases: int = Field(default=30, ge=1, le=30)

    # File paths
    images_dir: str = Field(default="io/storage/images/")

    # Admin user
    admin_user_uuid: Optional[str] = None

    @validator('admin_user_uuid')
    def validate_admin_uuid(cls, v):
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("admin_user_uuid must be a valid UUID string")
        return v

    @validator('prompt_max_general_phrases')
    def validate_general_phrases_range(cls, v, values):
        min_val = values.get('prompt_min_general_phrases', 0)
        if v < min_val:
            raise ValueError("prompt_max_general_phrases must be >= prompt_min_general_phrases")
        return v

    @validator('prompt_max_domain_phrases')
    def validate_domain_phrases_range(cls, v, values):
        min_val = values.get('prompt_min_domain_phrases', 1)
        if v < min_val:
            raise ValueError("prompt_max_domain_phrases must be >= prompt_min_domain_phrases")
        return v


class ConfigManager:
    """Manages configuration loading and CLI overrides."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.base_config = self._load_base_config()

    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration from config.json."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        return config.get('seed_data_generator', {})

    def get_config(self, cli_overrides: Optional[Dict[str, Any]] = None) -> SeedDataConfig:
        """Get merged configuration with CLI overrides."""
        # Start with base config
        merged_config = self.base_config.copy()

        # Load admin UUID from environment
        admin_uuid = os.getenv('DB_USER_ADMIN_UUID')
        if admin_uuid:
            merged_config['admin_user_uuid'] = admin_uuid

        # Apply CLI overrides
        if cli_overrides:
            merged_config.update(cli_overrides)

        # Load images_dir from main config if not in seed_data_generator section
        if 'images_dir' not in merged_config:
            with open(self.config_path, 'r') as f:
                full_config = json.load(f)
                merged_config['images_dir'] = full_config.get('images_dir', 'io/storage/images/')

        return SeedDataConfig(**merged_config)

    def validate_admin_uuid(self, config: SeedDataConfig) -> str:
        """Validate and return admin UUID, raising error with helpful message if missing."""
        if not config.admin_user_uuid:
            # Generate a sample UUID for the error message
            sample_uuid = str(uuid.uuid4())
            error_msg = (
                f"DB_USER_ADMIN_UUID environment variable is required.\n"
                f"Please add this to your env/.env file:\n"
                f"DB_USER_ADMIN_UUID={sample_uuid}\n"
                f"You can copy the UUID above or generate your own."
            )
            print(f"Generated sample UUID: {sample_uuid}")
            raise RuntimeError(error_msg)

        return config.admin_user_uuid