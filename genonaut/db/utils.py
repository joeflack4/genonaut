"""Database utility functions for Genonaut.

This module provides utility functions for database operations including
URL construction and configuration management.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from .env file in the env/ directory
# Path from genonaut/db/init.py -> project_root/env/.env
env_path = Path(__file__).parent.parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


def get_database_url() -> str:
    """Get database URL from environment variables.
    
    For initialization tasks, uses admin credentials by default.
    
    Returns:
        Database URL string
        
    Raises:
        ValueError: If required environment variables are not set
    """
    # Try to get full DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.strip():
        return database_url
    
    # Otherwise, construct from individual components using admin credentials for initialization
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'genonaut')
    
    # Try admin credentials first (for initialization)
    admin_password = os.getenv('DB_PASSWORD_ADMIN')
    if admin_password:
        return f"postgresql://genonaut_admin:{admin_password}@{host}:{port}/{database}"
    
    # Fall back to legacy credentials for backward compatibility
    username = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    
    if not password:
        raise ValueError("Database password must be provided via DB_PASSWORD_ADMIN (preferred) or DB_PASSWORD/DATABASE_URL environment variable")
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"