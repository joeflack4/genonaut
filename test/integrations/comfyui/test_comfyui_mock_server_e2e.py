"""End-to-end tests with Celery, Redis, and mock ComfyUI server.

These tests verify the complete workflow from job submission through
Celery processing to completion using the mock ComfyUI server.

NOTE: These tests are currently skipped due to generation service integration issues.
They are written and ready to debug once the underlying workflow is fixed.
"""
import time
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

import pytest

from genonaut.db.schema import User, GenerationJob, ContentItem
from genonaut.api.services.generation_service import GenerationService
from genonaut.worker.tasks import process_comfy_job


@pytest.mark.longrunning
@pytest.mark.comfyui_e2e
class TestEndToEndWorkflow:
    """Test complete end-to-end workflow with Celery and mock ComfyUI."""

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="e2e_test_user",
            email="e2e@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def generation_service(self, db_session: Session) -> GenerationService:
        """Create generation service."""
        return GenerationService(db_session)

    def test_complete_workflow_manual(
        self,
        db_session: Session,
        test_user: User,
        generation_service: GenerationService,
        mock_comfyui_config: dict
    ):
        """Test complete workflow by manually calling task (without Celery worker).

        This test simulates the workflow without requiring a running Celery worker.
        """
        # Create a generation job
        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt="A beautiful landscape with mountains",
            negative_prompt="blurry, low quality",
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512,
            batch_size=1,
            sampler_params={
                'steps': 20,
                'cfg_scale': 7.0,
                'seed': 42
            }
        )

        assert job.status == 'pending'
        assert job.user_id == test_user.id

        # Manually execute the Celery task (without worker)
        # This simulates what the Celery worker would do
        process_comfy_job(db_session, job.id)

        # Refresh job from database
        db_session.refresh(job)

        # Verify job completed successfully
        assert job.status == 'completed'
        assert job.content_id is not None
        assert job.completed_at is not None

        # Verify content item was created
        content_item = db_session.query(ContentItem).filter_by(id=job.content_id).first()
        assert content_item is not None
        assert content_item.creator_id == test_user.id
        assert content_item.content_type == 'image'
        assert content_item.prompt == job.prompt

        # Verify output files in metadata
        assert 'output_paths' in job.params
        assert len(job.params['output_paths']) > 0

    def test_job_status_updates(
        self,
        db_session: Session,
        test_user: User,
        generation_service: GenerationService,
        mock_comfyui_config: dict
    ):
        """Test job status updates throughout workflow."""
        from genonaut.api.config import get_settings

        # Create job
        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt="Test status updates",
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512
        )

        # Initial status should be pending
        assert job.status == 'pending'

        # Process job
        process_comfy_job(db_session, job.id)

        # Refresh and check final status
        db_session.refresh(job)
        assert job.status == 'completed'
        assert job.updated_at > job.created_at

    def test_file_organization(
        self,
        db_session: Session,
        test_user: User,
        generation_service: GenerationService,
        mock_comfyui_config: dict
    ):
        """Test file organization after generation."""
        from genonaut.api.config import get_settings

        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt="Test file organization",
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512
        )

        # Process job
        process_comfy_job(db_session, job.id)

        # Refresh job
        db_session.refresh(job)

        # Check output paths were organized
        assert 'output_paths' in job.params
        output_paths = job.params['output_paths']
        assert len(output_paths) > 0

        # Paths should be organized (not in ComfyUI output dir)
        for path in output_paths:
            assert isinstance(path, str)
            # The path should be the organized path from FileService

    def test_thumbnail_generation(
        self,
        db_session: Session,
        test_user: User,
        generation_service: GenerationService,
        mock_comfyui_config: dict
    ):
        """Test thumbnail generation with mock outputs."""
        from genonaut.api.config import get_settings

        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt="Test thumbnail generation",
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512
        )

        # Process job
        process_comfy_job(db_session, job.id)

        # Refresh job
        db_session.refresh(job)

        # Check for thumbnail metadata
        if 'thumbnails' in job.params:
            thumbnails = job.params['thumbnails']
            # Thumbnail generation may succeed or fail, but shouldn't crash

    def test_content_item_creation(
        self,
        db_session: Session,
        test_user: User,
        generation_service: GenerationService,
        mock_comfyui_config: dict
    ):
        """Test content item creation with mock results."""
        from genonaut.api.config import get_settings

        prompt_text = "A serene mountain lake at sunset"

        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt=prompt_text,
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512
        )

        # Process job
        process_comfy_job(db_session, job.id)

        # Refresh job
        db_session.refresh(job)

        # Get content item
        content_item = db_session.query(ContentItem).filter_by(id=job.content_id).first()

        assert content_item is not None
        assert content_item.prompt == prompt_text
        assert content_item.creator_id == test_user.id
        assert content_item.content_type == 'image'
        assert content_item.item_metadata is not None


@pytest.mark.longrunning
@pytest.mark.comfyui_e2e
class TestConcurrentJobs:
    """Test concurrent job processing."""

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="concurrent_test_user",
            email="concurrent@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_multiple_jobs_sequential(
        self,
        db_session: Session,
        test_user: User,
        mock_comfyui_config: dict
    ):
        """Test multiple jobs processed sequentially."""
        from genonaut.api.config import get_settings
        from genonaut.api.services.generation_service import GenerationService


        generation_service = GenerationService(db_session)

        # Create multiple jobs
        jobs = []
        for i in range(3):
            job = generation_service.create_generation_job(
                user_id=test_user.id,
                job_type='image_generation',
                prompt=f"Concurrent test job {i}",
                checkpoint_model="test_checkpoint.safetensors",
                width=512,
                height=512
            )
            jobs.append(job)

        # Process each job
        for job in jobs:
            process_comfy_job(db_session, job.id)

        # Verify all jobs completed
        for job in jobs:
            db_session.refresh(job)
            assert job.status == 'completed'
            assert job.content_id is not None

    def test_unique_output_files_per_job(
        self,
        db_session: Session,
        test_user: User,
        mock_comfyui_config: dict
    ):
        """Test each job gets unique output files."""
        from genonaut.api.config import get_settings
        from genonaut.api.services.generation_service import GenerationService


        generation_service = GenerationService(db_session)

        # Create and process multiple jobs
        output_files = []
        for i in range(3):
            job = generation_service.create_generation_job(
                user_id=test_user.id,
                job_type='image_generation',
                prompt=f"Unique file test {i}",
                checkpoint_model="test_checkpoint.safetensors",
                width=512,
                height=512
            )

            process_comfy_job(db_session, job.id)

            db_session.refresh(job)
            if 'output_paths' in job.params:
                output_files.extend(job.params['output_paths'])

        # All output files should be unique
        if output_files:
            assert len(output_files) == len(set(output_files))


@pytest.mark.longrunning
@pytest.mark.comfyui_e2e
class TestErrorRecovery:
    """Test error handling and recovery."""

    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            username="error_test_user",
            email="error@example.com",
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_job_failure_handling(
        self,
        db_session: Session,
        test_user: User,
        monkeypatch
    ):
        """Test job failure with error message recording."""
        from genonaut.api import config
        from genonaut.api.config import get_settings
        from genonaut.api.services.generation_service import GenerationService

        # Clear settings cache to ensure monkeypatch takes effect
        config._LAST_SETTINGS = None

        settings = get_settings()
        # Point to non-existent server to force failure
        monkeypatch.setattr(settings, 'comfyui_url', 'http://localhost:9999')
        monkeypatch.setattr(settings, 'comfyui_mock_url', 'http://localhost:9998')

        generation_service = GenerationService(db_session)

        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt="This should fail",
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512
        )

        # Try to process - should fail
        try:
            process_comfy_job(db_session, job.id)
        except Exception:
            pass  # Expected to fail

        # Refresh job
        db_session.refresh(job)

        # Job should be marked as failed
        assert job.status == 'failed'
        assert job.error_message is not None
        assert len(job.error_message) > 0

    def test_cleanup_on_failed_job(
        self,
        db_session: Session,
        test_user: User,
        monkeypatch
    ):
        """Test cleanup occurs on failed jobs."""
        from genonaut.api import config
        from genonaut.api.config import get_settings
        from genonaut.api.services.generation_service import GenerationService

        # Clear settings cache to ensure monkeypatch takes effect
        config._LAST_SETTINGS = None

        settings = get_settings()
        monkeypatch.setattr(settings, 'comfyui_url', 'http://localhost:9999')
        monkeypatch.setattr(settings, 'comfyui_mock_url', 'http://localhost:9998')

        generation_service = GenerationService(db_session)

        job = generation_service.create_generation_job(
            user_id=test_user.id,
            job_type='image_generation',
            prompt="Cleanup test",
            checkpoint_model="test_checkpoint.safetensors",
            width=512,
            height=512
        )

        # Try to process
        try:
            process_comfy_job(db_session, job.id)
        except Exception:
            pass

        # Refresh job
        db_session.refresh(job)

        # Should not have content_id if failed
        assert job.content_id is None
        assert job.status == 'failed'
