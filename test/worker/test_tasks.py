"""Unit tests for Celery worker tasks."""

import uuid
from typing import Any, Dict, List, Generator

import pytest
from sqlalchemy.orm import Session
from genonaut.db.schema import User, GenerationJob, ContentItem
from genonaut.worker.tasks import process_comfy_job

# Import PostgreSQL fixtures
from test.db.postgres_fixtures import postgres_engine, postgres_session


@pytest.fixture()
def db_session(postgres_session) -> Generator[Session, None, None]:
    """Yield a PostgreSQL session for worker tests.

    This fixture uses the PostgreSQL test database with automatic rollback
    for test isolation. Provides isolation between tests.
    """
    yield postgres_session


class DummyComfyClient:
    """Stub ComfyUI client that simulates a successful workflow."""

    def __init__(self):
        self.submitted_workflow: Dict[str, Any] | None = None

    def submit_generation(self, workflow: Dict[str, Any], client_id: str | None = None) -> str:
        self.submitted_workflow = workflow
        return "prompt-123"

    def wait_for_outputs(self, prompt_id: str, max_wait_time: int | None = None) -> Dict[str, Any]:
        assert prompt_id == "prompt-123"
        return {
            "status": "completed",
            "messages": ["ok"],
            "outputs": {
                "5": {
                    "images": [
                        {"filename": "image.png", "subfolder": ""},
                    ]
                }
            },
        }

    def collect_output_paths(self, outputs: Dict[str, Any]) -> List[str]:
        assert "5" in outputs
        return ["/tmp/comfy/image.png"]


class DummyFileStorageService:
    """Stub file storage that simply echoes input paths."""

    def organize_generation_files(self, generation_id, user_id, file_paths):
        return [f"/organized/{generation_id}/{idx}.png" for idx, _ in enumerate(file_paths, start=1)]


class DummyThumbnailService:
    """Stub thumbnail generation service."""

    def generate_thumbnail_for_generation(self, image_paths, generation_id):
        return {path: {"webp": [f"{path}.webp"]} for path in image_paths}


class DummyContentService:
    """Content service stub that persists ``ContentItem`` rows."""

    def __init__(self, session):
        self.session = session

    def create_content(self, *, title, content_type, content_data, prompt, creator_id, item_metadata, **_):
        content = ContentItem(
            title=title,
            content_type=content_type,
            content_data=content_data,
            prompt=prompt,
            creator_id=creator_id,
            item_metadata=item_metadata,
        )
        self.session.add(content)
        self.session.commit()
        self.session.refresh(content)
        return content


def test_process_comfy_job_happy_path(db_session):
    """End-to-end processing succeeds with stubbed external services."""

    # Prepare user and job rows
    user = User(
        id=uuid.uuid4(),
        username="worker-test",
        email="worker@test.dev",
    )
    db_session.add(user)
    db_session.commit()

    job = GenerationJob(
        user_id=user.id,
        job_type="image",
        prompt="A whimsical sunrise over the lake",
        params={
            "sampler_params": {"steps": 12, "cfg": 6.5},
            "negative_prompt": "low quality"
        },
        status="pending",
    )
    db_session.add(job)
    db_session.commit()

    result = process_comfy_job(
        db_session,
        job.id,
        comfy_client=DummyComfyClient(),
        file_service=DummyFileStorageService(),
        thumbnail_service=DummyThumbnailService(),
        content_service=DummyContentService(db_session),
    )

    db_session.refresh(job)

    assert result["status"] == "completed"
    assert job.status == "completed"
    assert job.content_id is not None
    assert "output_paths" in job.params
    assert job.params["output_paths"]
    assert job.params["thumbnails"]


class FailingComfyClient:
    """Stub ComfyUI client that simulates a failure."""

    def submit_generation(self, workflow: Dict[str, Any], client_id: str | None = None) -> str:
        from genonaut.worker.comfyui_client import ComfyUIConnectionError
        raise ComfyUIConnectionError("Failed to connect to ComfyUI server")


def test_process_comfy_job_handles_errors(db_session):
    """Task marks job as failed when ComfyUI client raises an error."""

    user = User(
        id=uuid.uuid4(),
        username="error-test",
        email="error@test.dev",
    )
    db_session.add(user)
    db_session.commit()

    job = GenerationJob(
        user_id=user.id,
        job_type="image",
        prompt="This should fail",
        params={},
        status="pending",
    )
    db_session.add(job)
    db_session.commit()

    try:
        process_comfy_job(
            db_session,
            job.id,
            comfy_client=FailingComfyClient(),
        )
        assert False, "Expected ComfyUIConnectionError to be raised"
    except Exception as e:
        # Error should propagate
        assert "Failed to connect to ComfyUI server" in str(e)

    db_session.refresh(job)

    # Job should be marked as failed
    assert job.status == "failed"
    assert job.error_message is not None
    assert "Failed to connect to ComfyUI server" in job.error_message
    assert job.completed_at is not None
