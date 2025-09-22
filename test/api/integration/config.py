"""Configuration for API integration tests."""

import os

# API server configuration for testing
TEST_API_BASE_URL = os.getenv("TEST_API_BASE_URL", "http://0.0.0.0:8099")
TEST_TIMEOUT = 30  # seconds for API requests
SERVER_STARTUP_TIMEOUT = 10  # seconds to wait for server startup
HEALTH_CHECK_INTERVAL = 0.5  # seconds between health checks