"""Pytest configuration for ComfyUI mock server tests."""

import pytest
import sys
from pathlib import Path

# Add the mock server directory to the path
mock_server_dir = Path(__file__).parent.parent.parent / "_infra/mock_services/comfyui"
sys.path.insert(0, str(mock_server_dir))

# Import fixtures from mock server conftest
from test._infra.mock_services.comfyui.conftest import (
    mock_comfyui_server,
    mock_comfyui_server_dynamic,
    mock_comfyui_url,
    mock_comfyui_url_dynamic,
    mock_comfyui_client,
    mock_comfyui_client_dynamic,
    mock_comfyui_worker_client_dynamic
)

# Import PostgreSQL test database fixtures
from test.db.postgres_fixtures import postgres_session, postgres_engine


@pytest.fixture
def db_session(postgres_session):
    """Database session fixture (now uses PostgreSQL).

    This is an alias for postgres_session to maintain backward compatibility
    with existing tests that use db_session.

    The session automatically rolls back after each test for isolation.
    """
    return postgres_session


@pytest.fixture
def mock_comfyui_config(mock_comfyui_url: str, monkeypatch):
    """Configure settings to use mock ComfyUI server with correct paths."""
    from genonaut.api.config import get_settings

    settings = get_settings()
    original_url = settings.comfyui_url
    original_output_dir = settings.comfyui_output_dir

    mock_output_dir = str(Path(__file__).parent.parent.parent / "_infra/mock_services/comfyui/output")

    monkeypatch.setattr(settings, 'comfyui_url', mock_comfyui_url)
    monkeypatch.setattr(settings, 'comfyui_output_dir', mock_output_dir)

    yield {
        "url": mock_comfyui_url,
        "output_dir": mock_output_dir
    }

    # Restore original settings
    monkeypatch.setattr(settings, 'comfyui_url', original_url)
    monkeypatch.setattr(settings, 'comfyui_output_dir', original_output_dir)


@pytest.fixture
def mock_comfyui_config_dynamic(mock_comfyui_url_dynamic: str, monkeypatch):
    """Configure settings to use mock ComfyUI server in dynamic generation mode with correct paths."""
    from genonaut.api import config as config_module
    from genonaut.api.config import get_settings

    # Clear settings cache to ensure monkeypatch takes effect
    config_module._LAST_SETTINGS = None

    settings = get_settings()
    original_url = settings.comfyui_url
    original_output_dir = settings.comfyui_output_dir

    mock_output_dir = str(Path(__file__).parent.parent.parent / "_infra/mock_services/comfyui/output")

    monkeypatch.setattr(settings, 'comfyui_url', mock_comfyui_url_dynamic)
    monkeypatch.setattr(settings, 'comfyui_output_dir', mock_output_dir)

    # Clear cache again after monkeypatching to force re-read on next get_settings()
    config_module._LAST_SETTINGS = None

    yield {
        "url": mock_comfyui_url_dynamic,
        "output_dir": mock_output_dir
    }

    # Restore original settings
    monkeypatch.setattr(settings, 'comfyui_url', original_url)
    monkeypatch.setattr(settings, 'comfyui_output_dir', original_output_dir)
    config_module._LAST_SETTINGS = None


__all__ = [
    "mock_comfyui_server",
    "mock_comfyui_server_dynamic",
    "mock_comfyui_url",
    "mock_comfyui_url_dynamic",
    "mock_comfyui_client",
    "mock_comfyui_client_dynamic",
    "mock_comfyui_worker_client_dynamic",
    "db_session",
    "mock_comfyui_config",
    "mock_comfyui_config_dynamic"
]
