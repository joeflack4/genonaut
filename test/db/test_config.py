"""Test database configuration.

Controls database truncation behavior for different test databases.

Configuration:
- genonaut_test: Persistent test database (NOT truncated by default)
- genonaut_test_init: Initialization test database (truncated by default)

To override defaults, set environment variables:
- TRUNCATE_TEST_DB=1: Force truncate genonaut_test
- TRUNCATE_TEST_INIT_DB=0: Skip truncating genonaut_test_init
"""

import os
from typing import Dict


class TestDatabaseConfig:
    """Configuration for test database truncation behavior."""

    # Database names and their default truncation settings
    DEFAULT_TRUNCATION_CONFIG: Dict[str, bool] = {
        "genonaut_test": False,  # Persistent - do NOT truncate
        "genonaut_test_init": True,  # Ephemeral - truncate on each run
    }

    @classmethod
    def should_truncate_database(cls, database_name: str) -> bool:
        """Determine if a database should be truncated before tests.

        Args:
            database_name: Name of the database (e.g., 'genonaut_test')

        Returns:
            True if database should be truncated, False otherwise

        Environment variable overrides:
        - TRUNCATE_TEST_DB=1: Force truncate genonaut_test
        - TRUNCATE_TEST_INIT_DB=0: Skip truncating genonaut_test_init
        """
        # Check for environment variable overrides
        if database_name == "genonaut_test":
            env_override = os.getenv("TRUNCATE_TEST_DB")
            if env_override is not None:
                return env_override in ("1", "true", "True", "yes", "Yes")

        if database_name == "genonaut_test_init":
            env_override = os.getenv("TRUNCATE_TEST_INIT_DB")
            if env_override is not None:
                return env_override in ("1", "true", "True", "yes", "Yes")

        # Use default configuration
        return cls.DEFAULT_TRUNCATION_CONFIG.get(database_name, False)
