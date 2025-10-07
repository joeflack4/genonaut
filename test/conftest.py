"""Test configuration and environment shims."""

import os
import sys
from functools import wraps
from types import ModuleType, SimpleNamespace
from uuid import uuid4

import requests
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from starlette.testclient import TestClient

os.environ["GENONAUT_TEST_UVICORN"] = "1"
os.environ["DATABASE_URL_TEST"] = "sqlite:///./test/_infra/test_genonaut_api.sqlite3"
os.environ["DATABASE_URL"] = "sqlite:///./test/_infra/test_genonaut_api.sqlite3"
os.environ["APP_ENV"] = "test"
os.environ["GENONAUT_DB_ENVIRONMENT"] = "test"

from genonaut.api.config import get_settings
from genonaut.api.dependencies import get_database_manager
from test.api.integration.config import TEST_API_BASE_URL


def _ensure_celery_stub() -> None:
    """Provide a minimal Celery stub when the package is unavailable."""

    if "celery" in sys.modules:
        return

    class _StubTask:  # pylint: disable=too-few-public-methods
        abstract = True

    class _StubCeleryApp:
        def __init__(self, *_, **__):
            self.conf = SimpleNamespace(update=lambda *a, **k: None, task_routes={})
            self.control = SimpleNamespace(revoke=lambda *a, **k: None)

        def task(self, *_, **__):
            def decorator(func):
                def delay(*args, **kwargs):
                    return SimpleNamespace(id=str(uuid4()))

                func.delay = delay  # type: ignore[attr-defined]
                func.apply_async = delay  # type: ignore[attr-defined]
                return func

            return decorator

    celery_module = ModuleType("celery")
    celery_module.Task = _StubTask
    celery_module.Celery = _StubCeleryApp
    celery_module.current_app = _StubCeleryApp()
    sys.modules["celery"] = celery_module


_ensure_celery_stub()


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **_):
    """Render JSONB columns as TEXT when tests run against SQLite."""

    return "TEXT"

from sqlalchemy import create_engine

from genonaut.db.schema import Base

get_settings.cache_clear()
get_database_manager.cache_clear()

_engine = create_engine(os.environ["DATABASE_URL"], echo=False)
Base.metadata.create_all(_engine)

from genonaut.api.main import app


# ---------------------------------------------------------------------------
# Requests adapter to route HTTP calls to in-process ASGI app (no sockets)
# ---------------------------------------------------------------------------

_original_request = requests.Session.request
_test_client = TestClient(app)


@wraps(_original_request)
def _patched_request(self, method, url, *args, **kwargs):
    if url.startswith(TEST_API_BASE_URL):
        timeout = kwargs.pop("timeout", None)  # TestClient does not use timeout
        json_payload = kwargs.pop("json", None)
        response = _test_client.request(
            method,
            url[len(TEST_API_BASE_URL):] or "/",
            params=kwargs.get("params"),
            data=kwargs.get("data"),
            json=json_payload,
            headers=kwargs.get("headers"),
        )
        return response

    return _original_request(self, method, url, *args, **kwargs)


requests.Session.request = _patched_request  # type: ignore[assignment]
