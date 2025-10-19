"""Test configuration and environment shims."""

import os
import sys
from functools import wraps
from types import ModuleType, SimpleNamespace
from uuid import uuid4

import requests
from starlette.testclient import TestClient

os.environ["GENONAUT_TEST_UVICORN"] = "1"
os.environ["ENV_TARGET"] = "local-test"
os.environ["APP_CONFIG_PATH"] = "config/local-test.json"
os.environ["GENONAUT_DB_ENVIRONMENT"] = "test"

# Load environment variables from .env files (needed for PostgreSQL integration tests)
from genonaut.config_loader import load_env_for_runtime
load_env_for_runtime("env/.env.local-test")

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

from sqlalchemy.orm import Session

from genonaut.db.schema import Base, ContentTag

get_settings.cache_clear()
get_database_manager.cache_clear()

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
# Test utility for populating content_tags junction table
# ---------------------------------------------------------------------------

def sync_content_tags_for_tests(session: Session, content_id: int, content_source: str, tags: list) -> None:
    """
    Populate content_tags junction table from a list of tags (slugs or UUIDs).

    This helper is used in tests to ensure the junction table is populated
    since we no longer store tags as arrays in the content tables.

    For test tags that don't exist in the hierarchy, this function will create
    simple tag entries in the tags table.

    Args:
        session: Database session
        content_id: Content item ID
        content_source: 'regular' or 'auto'
        tags: List of tag slugs or UUIDs (can be strings or UUID objects)
    """
    if not tags:
        return

    from uuid import UUID, uuid5, NAMESPACE_DNS
    from genonaut.api.utils.tag_identifiers import get_uuid_for_slug, TAG_UUID_NAMESPACE
    from genonaut.db.schema import Tag

    for tag in tags:
        # Convert to UUID
        tag_uuid = None
        tag_name = None

        if isinstance(tag, UUID):
            tag_uuid = tag
        elif isinstance(tag, dict):
            # Handle tag objects with 'id', 'slug', 'name' fields
            if 'id' in tag:
                try:
                    tag_uuid = UUID(str(tag['id']))
                    tag_name = tag.get('name', '')
                except (ValueError, KeyError):
                    pass
        elif isinstance(tag, str):
            # Try to parse as UUID first
            try:
                tag_uuid = UUID(tag)
            except ValueError:
                # If not a UUID, try to convert from slug
                uuid_str = get_uuid_for_slug(tag)
                if uuid_str:
                    tag_uuid = UUID(uuid_str)
                else:
                    # For test tags not in hierarchy, generate UUID from slug
                    tag_uuid = uuid5(TAG_UUID_NAMESPACE, tag)

                # Store the tag name for later
                tag_name = tag.replace('_', ' ').title()

        if not tag_uuid:
            # Skip invalid tags
            continue

        # IMPORTANT: For PostgreSQL, ensure tag exists BEFORE creating content_tag
        existing_tag = session.query(Tag).filter(Tag.id == tag_uuid).first()
        if not existing_tag:
            # Create tag if it doesn't exist (for tests only)
            new_tag = Tag(
                id=tag_uuid,
                name=tag_name or f"Test Tag {tag_uuid}",
                tag_metadata={"test_tag": True, "slug": tag if isinstance(tag, str) else str(tag_uuid)}
            )
            session.add(new_tag)
            session.flush()  # Flush to ensure tag exists before content_tag

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


def pytest_sessionstart(session):
    """Clean the PostgreSQL test database before starting the test session.

    This hook runs once at the beginning of a pytest session (before any tests run).
    It truncates all tables in the test database to ensure a clean slate.

    This is necessary because some tests use fixtures that bypass the postgres_session
    rollback mechanism (like tests that create their own DatabaseInitializer), leaving
    data that can cause IntegrityError in subsequent test runs.
    """
    try:
        from sqlalchemy import create_engine, text
        from test.db.postgres_fixtures import get_postgres_test_url

        # Get test database URL
        db_url = get_postgres_test_url()
        engine = create_engine(db_url)

        # Truncate all tables
        with engine.connect() as conn:
            # Get all table names (excluding alembic version table)
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT LIKE 'alembic%'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]

            # Truncate each table
            for table in tables:
                try:
                    conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                except Exception:
                    # If truncate fails (e.g., table doesn't exist), continue
                    pass

            conn.commit()

        engine.dispose()

    except Exception as e:
        # If cleanup fails, print warning but don't fail the test session
        print(f"\nWarning: Failed to clean test database: {e}")
        print("Tests may fail due to existing data. Run 'make init-test' to reset the database.\n")
