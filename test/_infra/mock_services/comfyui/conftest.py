"""Pytest fixtures for ComfyUI mock server."""

import subprocess
import time
import requests
import pytest
from pathlib import Path
from typing import Generator


@pytest.fixture(scope="session")
def mock_comfyui_server() -> Generator[str, None, None]:
    """Start mock ComfyUI server for testing session.

    Returns:
        URL of the mock server
    """
    # Get server directory
    server_dir = Path(__file__).parent
    server_script = server_dir / "server.py"

    # Start server in background
    process = subprocess.Popen(
        ["python", str(server_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to be ready
    server_url = "http://localhost:8189"
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            response = requests.get(f"{server_url}/system_stats", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.1)
    else:
        process.kill()
        raise RuntimeError("Mock ComfyUI server failed to start")

    yield server_url

    # Cleanup: stop server
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def mock_comfyui_url(mock_comfyui_server: str) -> str:
    """Get mock ComfyUI server URL.

    This is a function-scoped fixture that resets server state
    between tests.
    """
    # Import here to avoid circular dependencies
    from test._infra.mock_services.comfyui.server import reset_server

    # Reset server state before each test
    reset_server()

    return mock_comfyui_server


@pytest.fixture
def mock_comfyui_client(mock_comfyui_url: str):
    """Create a ComfyUIClient configured to use mock server."""
    from genonaut.api.services.comfyui_client import ComfyUIClient
    from genonaut.api.config import get_settings

    # Temporarily override the ComfyUI URL
    settings = get_settings()
    original_url = settings.comfyui_url
    settings.comfyui_url = mock_comfyui_url

    client = ComfyUIClient()

    # Clear any cached health status
    if hasattr(client, 'cache_service'):
        try:
            # Clear the health cache key
            client.cache_service.redis_client.delete('comfyui:health')
        except:
            pass  # Ignore if cache not available

    yield client

    # Restore original URL
    settings.comfyui_url = original_url
