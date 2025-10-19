"""Shared fixtures for API integration tests."""

import os
import pytest
import requests
import subprocess
import time
import signal
import atexit
from typing import Dict, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from genonaut.db.schema import Base
from .config import (
    TEST_API_BASE_URL,
    TEST_TIMEOUT,
    SERVER_STARTUP_TIMEOUT,
    HEALTH_CHECK_INTERVAL
)


@pytest.fixture(scope="session", autouse=True)
def api_server():
    """Start and stop the API server for testing."""
    # Extract host and port from TEST_API_BASE_URL
    url_parts = TEST_API_BASE_URL.replace("http://", "").replace("https://", "")
    host, port = url_parts.split(":")
    port = int(port)

    # Start the server process
    server_process = None
    try:
        print(f"\nStarting API server on {host}:{port} for testing...")

        # Command to start the server with test environment
        cmd = [
            "uvicorn",
            "genonaut.api.main:app",
            "--host", host,
            "--port", str(port),
            "--log-level", "warning"  # Reduce noise in test output
        ]

        # Set environment variables for test configuration
        env = os.environ.copy()
        env["ENV_TARGET"] = "local-test"
        env["APP_CONFIG_PATH"] = "config/local-test.json"

        # Start the server process
        server_process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )

        # Wait for server to be ready
        _wait_for_server_ready()
        print("API server is ready at", TEST_API_BASE_URL)

        yield  # Server is running during tests

    finally:
        # Cleanup: Stop the server
        if server_process:
            print("\nStopping API server...")
            try:
                if hasattr(os, 'killpg'):
                    # Kill the entire process group (Unix/Linux/macOS)
                    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                else:
                    # Windows fallback
                    server_process.terminate()

                # Wait a bit for graceful shutdown
                try:
                    server_process.wait(timeout=5)
                    print("API server stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
                    else:
                        server_process.kill()
                    print("API server force stopped")
            except Exception as e:
                print(f"Error stopping server: {e}")


def _wait_for_server_ready():
    """Wait for the API server to be ready to accept requests."""
    import requests

    start_time = time.time()
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        try:
            response = requests.get(f"{TEST_API_BASE_URL}/api/v1/health", timeout=TEST_TIMEOUT)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException:
            # Server not ready yet
            pass

        time.sleep(HEALTH_CHECK_INTERVAL)

    raise TimeoutError(f"API server did not start within {SERVER_STARTUP_TIMEOUT} seconds")


@pytest.fixture(scope="function")
def db_session():
    """Database session fixture for API integration tests (now uses PostgreSQL).

    Note: This imports the PostgreSQL session from our fixtures.
    The PostgreSQL test database must be initialized before running tests:
        make init-test

    The session automatically rolls back after each test for isolation.
    """
    from test.db.postgres_fixtures import create_postgres_test_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import event

    # Create engine and session with transaction rollback
    engine = create_postgres_test_engine()
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    session.begin_nested()

    # Recreate savepoint after each commit
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


class APITestClient:
    """Helper class for making API requests during testing."""

    def __init__(self, base_url: str = TEST_API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, params=params, timeout=TEST_TIMEOUT)

    def post(self, endpoint: str, json: Optional[Dict] = None) -> requests.Response:
        """Make POST request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, json=json, timeout=TEST_TIMEOUT)

    def put(self, endpoint: str, json: Optional[Dict] = None) -> requests.Response:
        """Make PUT request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, json=json, timeout=TEST_TIMEOUT)

    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, timeout=TEST_TIMEOUT)


@pytest.fixture
def api_client():
    """Provide API test client for making requests."""
    return APITestClient()