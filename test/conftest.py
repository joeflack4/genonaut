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
os.environ["ENV_TARGET"] = "local-test"
os.environ["APP_CONFIG_PATH"] = "config/local-test.json"
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
from sqlalchemy.orm import Session

from genonaut.db.schema import Base, ContentTag

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


# ---------------------------------------------------------------------------
# Test utility for populating content_tags junction table (SQLite support)
# ---------------------------------------------------------------------------

def sync_content_tags_for_tests(session: Session, content_id: int, content_source: str, tags: list) -> None:
    """
    Populate content_tags junction table from a list of tags (slugs or UUIDs).

    This helper is used in SQLite tests to ensure the junction table is populated
    since we no longer store tags as arrays in the content tables.

    Args:
        session: Database session
        content_id: Content item ID
        content_source: 'regular' or 'auto'
        tags: List of tag slugs or UUIDs (can be strings or UUID objects)
    """
    if not tags:
        return

    from uuid import UUID
    from genonaut.api.utils.tag_identifiers import get_uuid_for_slug

    for tag in tags:
        # Convert to UUID
        tag_uuid = None
        if isinstance(tag, UUID):
            tag_uuid = tag
        elif isinstance(tag, str):
            # Try to parse as UUID first
            try:
                tag_uuid = UUID(tag)
            except ValueError:
                # If not a UUID, try to convert from slug
                uuid_str = get_uuid_for_slug(tag)
                if uuid_str:
                    tag_uuid = UUID(uuid_str)

        if not tag_uuid:
            # Skip invalid tags
            continue

        # Create junction table entry (skip if already exists)
        existing = session.query(ContentTag).filter(
            ContentTag.content_id == content_id,
            ContentTag.content_source == content_source,
            ContentTag.tag_id == tag_uuid
        ).first()

        if not existing:
            content_tag = ContentTag(
                content_id=content_id,
                content_source=content_source,
                tag_id=tag_uuid
            )
            session.add(content_tag)

    session.commit()
