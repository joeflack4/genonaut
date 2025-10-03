"""Celery tasks for asynchronous job processing.

This module defines Celery tasks for generation jobs, primarily ComfyUI image generation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from celery import Task
from sqlalchemy.orm import Session

from genonaut.worker.queue_app import celery_app
from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseTask(Task):
    """Base task class that provides database session management."""

    _db_session: Optional[Session] = None

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db_session is not None:
            self._db_session.close()
            self._db_session = None

    @property
    def db_session(self) -> Session:
        """Get or create database session for this task."""
        if self._db_session is None:
            self._db_session = next(get_database_session())
        return self._db_session


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="genonaut.worker.tasks.run_comfy_job",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    max_retries=3,
)
def run_comfy_job(self, job_id: int, workflow_params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a ComfyUI generation job asynchronously.

    This task:
    1. Updates job status to 'running'
    2. Submits workflow to ComfyUI
    3. Polls for completion or handles webhook
    4. Downloads and processes generated images
    5. Creates thumbnails
    6. Updates job with results

    Args:
        job_id: The generation job ID
        workflow_params: Parameters for the ComfyUI workflow

    Returns:
        Dict containing job_id, status, and artifact information

    Raises:
        Exception: If job processing fails
    """
    from genonaut.db.schema import GenerationJob

    db = self.db_session
    logger.info(f"Starting ComfyUI job {job_id}")

    try:
        # Step 1: Get job and update status to 'running'
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job {job_id} status updated to 'running'")

        # Step 2: Submit to ComfyUI (placeholder - will be implemented in Phase 5)
        # TODO: Implement ComfyUI client integration
        # comfyui_client = ComfyUIClient(settings.comfyui_url)
        # prompt_id = comfyui_client.submit_workflow(workflow_params)
        # job.comfyui_prompt_id = prompt_id
        # db.commit()

        logger.warning(f"ComfyUI integration not yet implemented for job {job_id}")

        # Step 3: Poll for completion or handle webhook (placeholder)
        # TODO: Implement polling or webhook handling
        # while not comfyui_client.is_complete(prompt_id):
        #     time.sleep(settings.comfyui_poll_interval)

        # Step 4: Download generated images (placeholder)
        # TODO: Implement image download and storage
        # images = comfyui_client.download_images(prompt_id)
        # output_paths = []
        # for img in images:
        #     path = save_image(img)
        #     output_paths.append(path)

        # Step 5: Create thumbnails (placeholder)
        # TODO: Implement thumbnail generation
        # thumbnail_paths = []
        # for img_path in output_paths:
        #     thumb_path = create_thumbnail(img_path)
        #     thumbnail_paths.append(thumb_path)

        # Step 6: Update job with results
        # TODO: When ComfyUI integration is complete, link to created ContentItem
        # job.content_id = created_content_item.id
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} completed successfully")

        return {
            "job_id": job_id,
            "status": "completed",
            "content_id": job.content_id,
        }

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)

        # Update job status to failed
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update job {job_id} status: {str(update_error)}")

        raise


@celery_app.task(name="genonaut.worker.tasks.cancel_job")
def cancel_job(job_id: int) -> Dict[str, Any]:
    """Cancel a running generation job.

    Args:
        job_id: The generation job ID to cancel

    Returns:
        Dict containing job_id and cancellation status
    """
    from genonaut.db.schema import GenerationJob

    db = next(get_database_session())
    logger.info(f"Cancelling job {job_id}")

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status not in ["pending", "running"]:
            raise ValueError(f"Cannot cancel job {job_id} with status '{job.status}'")

        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} cancelled successfully")

        return {
            "job_id": job_id,
            "status": "cancelled",
        }

    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()
