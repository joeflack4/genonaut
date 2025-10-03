"""Celery tasks for asynchronous job processing.

This module defines Celery tasks for generation jobs, primarily ComfyUI image generation.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:  # pragma: no cover - exercised indirectly
    from celery import Task
except ModuleNotFoundError:  # pragma: no cover
    class Task:  # minimal stand-in when Celery isn't installed
        abstract = True
from sqlalchemy.orm import Session

from genonaut.worker.queue_app import celery_app
from genonaut.api.dependencies import get_database_session
from genonaut.api.config import get_settings
from genonaut.worker.comfyui_client import (
    ComfyUIWorkerClient,
    ComfyUIConnectionError,
    ComfyUIWorkflowError,
)
from genonaut.api.services.workflow_builder import (
    WorkflowBuilder,
    GenerationRequest,
    SamplerParams,
    LoRAModel,
)
from genonaut.api.services.file_storage_service import FileStorageService
from genonaut.api.services.thumbnail_service import ThumbnailService
from genonaut.api.services.content_service import ContentService

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


def process_comfy_job(
    db: Session,
    job_id: int,
    override_params: Optional[Dict[str, Any]] = None,
    *,
    workflow_builder: Optional[WorkflowBuilder] = None,
    comfy_client: Optional[ComfyUIWorkerClient] = None,
    file_service: Optional[FileStorageService] = None,
    thumbnail_service: Optional[ThumbnailService] = None,
    content_service: Optional[ContentService] = None,
) -> Dict[str, Any]:
    """Core job processing logic extracted for testability."""

    from genonaut.db.schema import GenerationJob

    workflow_builder = workflow_builder or WorkflowBuilder()
    comfy_client = comfy_client or ComfyUIWorkerClient()
    file_service = file_service or FileStorageService()
    thumbnail_service = thumbnail_service or ThumbnailService()
    content_service = content_service or ContentService(db)

    logger.info("Starting ComfyUI job %s", job_id)

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    try:
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.error_message = None
        db.commit()
        logger.info("Job %s status updated to 'running'", job_id)

        job_params: Dict[str, Any] = dict(job.params or {})
        if override_params:
            job_params.update(override_params)

        sampler_defaults = SamplerParams()
        sampler_payload = job_params.get('sampler_params') or {}
        sampler = SamplerParams(
            seed=int(sampler_payload.get('seed', sampler_defaults.seed)),
            steps=int(sampler_payload.get('steps', sampler_defaults.steps)),
            cfg=float(sampler_payload.get('cfg', sampler_defaults.cfg)),
            sampler_name=sampler_payload.get('sampler_name', sampler_defaults.sampler_name),
            scheduler=sampler_payload.get('scheduler', sampler_defaults.scheduler),
            denoise=float(sampler_payload.get('denoise', sampler_defaults.denoise)),
        )

        lora_models_payload: List[Dict[str, Any]] = (
            job.lora_models or job_params.get('lora_models') or []
        )
        lora_models: List[LoRAModel] = []
        for item in lora_models_payload:
            if not isinstance(item, dict):
                continue
            name = item.get('name')
            if not name:
                continue
            lora_models.append(
                LoRAModel(
                    name=name,
                    strength_model=float(item.get('strength_model', 0.8)),
                    strength_clip=float(item.get('strength_clip', 0.8)),
                )
            )

        generation_request = GenerationRequest(
            prompt=job.prompt,
            negative_prompt=job.negative_prompt or job_params.get('negative_prompt', ""),
            checkpoint_model=job.checkpoint_model or job_params.get('checkpoint_model', settings.comfyui_default_checkpoint),
            lora_models=lora_models,
            width=job.width or job_params.get('width', settings.comfyui_default_width),
            height=job.height or job_params.get('height', settings.comfyui_default_height),
            batch_size=job.batch_size or job_params.get('batch_size', settings.comfyui_default_batch_size),
            sampler_params=sampler,
            filename_prefix=f"gen_job_{job.id}",
        )

        workflow = workflow_builder.build_workflow(generation_request)

        prompt_id = comfy_client.submit_generation(workflow, client_id=str(job.id))
        job.comfyui_prompt_id = prompt_id
        db.commit()
        logger.info("Job %s submitted to ComfyUI (prompt_id=%s)", job_id, prompt_id)

        workflow_status = comfy_client.wait_for_outputs(
            prompt_id, max_wait_time=settings.comfyui_max_wait_time
        )

        status_value = workflow_status.get('status', 'unknown')
        if status_value != 'completed':
            messages = workflow_status.get('messages') or []
            raise ComfyUIWorkflowError(
                f"ComfyUI reported status '{status_value}' for job {job_id}: {messages}"
            )

        outputs = workflow_status.get('outputs') or {}
        output_paths = comfy_client.collect_output_paths(outputs)
        if not output_paths:
            raise ComfyUIWorkflowError(f"No output files produced for job {job_id}")

        organized_paths = file_service.organize_generation_files(
            job.id,
            job.user_id,
            output_paths,
        )

        thumbnail_summary: Dict[str, Any] = {}
        if organized_paths:
            try:
                thumbnail_summary = thumbnail_service.generate_thumbnail_for_generation(
                    organized_paths,
                    job.id,
                )
            except Exception as thumb_err:  # pragma: no cover - defensive
                logger.warning(
                    "Thumbnail generation failed for job %s: %s", job_id, thumb_err
                )

        metadata = dict(job_params)
        metadata.update(
            {
                'output_paths': organized_paths,
                'thumbnails': thumbnail_summary,
                'comfyui_prompt_id': prompt_id,
                'workflow_messages': workflow_status.get('messages', []),
            }
        )

        primary_image = organized_paths[0] if organized_paths else None
        if not primary_image:
            raise ComfyUIWorkflowError(f"Unable to determine primary image path for job {job_id}")

        content_title = metadata.get('title') or job.prompt[:255]
        content_item = content_service.create_content(
            title=content_title,
            content_type='image',
            content_data=primary_image,
            prompt=job.prompt,
            creator_id=job.user_id,
            item_metadata=metadata,
        )

        job.content_id = content_item.id
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        job.params = metadata
        job.error_message = None

        db.commit()
        db.refresh(job)
        logger.info("Job %s completed successfully", job_id)

        return {
            "job_id": job_id,
            "status": job.status,
            "content_id": job.content_id,
            "output_paths": organized_paths,
            "prompt_id": prompt_id,
        }

    except Exception as exc:
        logger.error("Job %s failed: %s", job_id, exc, exc_info=True)

        try:
            db.rollback()
        except Exception:
            pass

        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = 'failed'
                job.error_message = str(exc)
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                db.commit()
        except Exception as update_error:  # pragma: no cover - defensive
            logger.error(
                "Failed to persist failure state for job %s: %s", job_id, update_error
            )

        raise


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="genonaut.worker.tasks.run_comfy_job",
    autoretry_for=(ComfyUIConnectionError, ComfyUIWorkflowError, Exception),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def run_comfy_job(self, job_id: int, override_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Celery task wrapper for :func:`process_comfy_job`."""

    db = self.db_session
    return process_comfy_job(
        db,
        job_id,
        override_params=override_params,
    )


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
