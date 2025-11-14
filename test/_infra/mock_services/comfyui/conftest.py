"""Pytest fixtures for ComfyUI mock server."""

import subprocess
import time
import requests
import pytest
from pathlib import Path
from typing import Generator


def _start_mock_server(disable_static_return: bool = False, port: int = 8189) -> tuple:
    """Helper function to start mock ComfyUI server with specified mode.

    Args:
        disable_static_return: If True, enable dynamic file generation mode
        port: Port to run server on (default: 8189)

    Returns:
        Tuple of (process, server_url)
    """
    # Get server directory
    server_dir = Path(__file__).parent
    server_script = server_dir / "server.py"

    # Build command with optional flags
    cmd = ["python", str(server_script), "--port", str(port)]
    if disable_static_return:
        cmd.append("--disable-static-return")

    # Start server in background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to be ready
    server_url = f"http://localhost:{port}"
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            response = requests.get(f"{server_url}/system_stats", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.1)
    else:
        # Get error output before killing process
        stdout, stderr = process.communicate(timeout=1)
        process.kill()
        error_msg = f"Mock ComfyUI server failed to start on port {port}.\nStderr: {stderr.decode() if stderr else 'None'}\nStdout: {stdout.decode() if stdout else 'None'}"
        raise RuntimeError(error_msg)

    return process, server_url


@pytest.fixture(scope="session")
def mock_comfyui_server() -> Generator[str, None, None]:
    """Start mock ComfyUI server in static return mode (default).

    Static mode returns input file path directly without copying files.
    This is the default behavior for performance and deployed test infrastructure.

    Returns:
        URL of the mock server
    """
    process, server_url = _start_mock_server(disable_static_return=False)

    yield server_url

    # Cleanup: stop server
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture(scope="session")
def mock_comfyui_server_dynamic() -> Generator[str, None, None]:
    """Start mock ComfyUI server in dynamic generation mode.

    Dynamic mode copies input file to output directory with unique filenames.
    Use this fixture for tests that verify unique file generation per job.

    Runs on port 8190 (separate from static mode server on 8189) to avoid
    port conflicts when both fixtures are used in the same test session.

    Returns:
        URL of the mock server
    """
    process, server_url = _start_mock_server(disable_static_return=True, port=8190)

    yield server_url

    # Cleanup: stop server
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def mock_comfyui_url(mock_comfyui_server: str) -> str:
    """Get mock ComfyUI server URL (static return mode).

    This is a function-scoped fixture that resets server state
    between tests.
    """
    # Reset server state before each test via HTTP endpoint
    try:
        requests.post(f"{mock_comfyui_server}/reset", timeout=2)
    except requests.exceptions.RequestException:
        # If reset fails, that's okay - server might not support it yet
        pass

    return mock_comfyui_server


@pytest.fixture
def mock_comfyui_url_dynamic(mock_comfyui_server_dynamic: str) -> str:
    """Get mock ComfyUI server URL (dynamic generation mode).

    Use this fixture for tests that verify unique file generation per job.
    This is a function-scoped fixture that resets server state between tests.
    """
    # Reset server state before each test via HTTP endpoint
    try:
        requests.post(f"{mock_comfyui_server_dynamic}/reset", timeout=2)
    except requests.exceptions.RequestException:
        # If reset fails, that's okay - server might not support it yet
        pass

    return mock_comfyui_server_dynamic


@pytest.fixture
def mock_comfyui_client(mock_comfyui_url: str):
    """Create a ComfyUIClient configured to use mock server (static return mode)."""
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


@pytest.fixture
def mock_comfyui_client_dynamic(mock_comfyui_url_dynamic: str):
    """Create a ComfyUIClient configured to use mock server (dynamic generation mode).

    Use this fixture for tests that verify unique file generation per job.
    """
    from genonaut.api.services.comfyui_client import ComfyUIClient
    from genonaut.api.config import get_settings
    from pathlib import Path

    # Temporarily override the ComfyUI URL
    settings = get_settings()
    original_url = settings.comfyui_url
    settings.comfyui_url = mock_comfyui_url_dynamic

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


@pytest.fixture
def mock_comfyui_worker_client_dynamic(mock_comfyui_url_dynamic: str):
    """Create a ComfyUIWorkerClient configured to use mock server (dynamic generation mode).

    This fixture creates a worker client that can be passed to process_comfy_job().
    Use this for E2E tests that verify unique file generation per job.
    """
    from genonaut.worker.comfyui_client import ComfyUIWorkerClient
    from pathlib import Path

    mock_output_dir = str(Path(__file__).parent / "output")

    client = ComfyUIWorkerClient(
        backend_url=mock_comfyui_url_dynamic,
        output_dir=mock_output_dir
    )

    yield client
