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
from genonaut.api.config import get_settings, get_cached_settings
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
from genonaut.api.services.notification_service import NotificationService
from genonaut.worker.pubsub import (
    publish_job_started,
    publish_job_processing,
    publish_job_completed,
    publish_job_failed,
)

logger = logging.getLogger(__name__)
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

    active_settings = get_cached_settings() or get_settings()

    workflow_builder = workflow_builder or WorkflowBuilder()
    file_service = file_service or FileStorageService()
    thumbnail_service = thumbnail_service or ThumbnailService()
    content_service = content_service or ContentService(db)

    logger.info("Starting ComfyUI job %s", job_id)

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    # Determine backend URL and directories based on job params (default to kerniegen)
    backend_url = None
    output_dir = None
    models_dir = None
    backend_choice = 'kerniegen'  # Default
    if not comfy_client:
        job_params_temp = dict(job.params or {})
        if override_params:
            job_params_temp.update(override_params)
        backend_choice = job_params_temp.get('backend', 'kerniegen')
        logger.info("Job %s: Backend choice from params: %s", job_id, backend_choice)
        if backend_choice == 'comfyui':
            backend_url = active_settings.comfyui_url
            output_dir = active_settings.comfyui_output_dir
            models_dir = active_settings.comfyui_models_dir
            logger.info("Job %s: Using ComfyUI backend URL: %s", job_id, backend_url)
            logger.info("Job %s: Using ComfyUI output dir: %s", job_id, output_dir)
        else:
            backend_url = active_settings.comfyui_mock_url
            output_dir = active_settings.comfyui_mock_output_dir
            models_dir = active_settings.comfyui_mock_models_dir
            logger.info("Job %s: Using KernieGen backend URL: %s", job_id, backend_url)
            logger.info("Job %s: Using KernieGen output dir: %s", job_id, output_dir)

    comfy_client = comfy_client or ComfyUIWorkerClient(
        settings=active_settings,
        backend_url=backend_url,
        output_dir=output_dir,
        models_dir=models_dir
    )

    try:
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.error_message = None
        db.commit()
        logger.info("Job %s status updated to 'running'", job_id)

        # Publish "started" status update
        publish_job_started(job_id)

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
            checkpoint_model=job.checkpoint_model or job_params.get('checkpoint_model', active_settings.comfyui_default_checkpoint),
            lora_models=lora_models,
            width=job.width or job_params.get('width', active_settings.comfyui_default_width),
            height=job.height or job_params.get('height', active_settings.comfyui_default_height),
            batch_size=job.batch_size or job_params.get('batch_size', active_settings.comfyui_default_batch_size),
            sampler_params=sampler,
            filename_prefix=f"gen_job_{job.id}",
        )

        workflow = workflow_builder.build_workflow(generation_request)

        prompt_id = comfy_client.submit_generation(workflow, client_id=str(job.id))
        job.comfyui_prompt_id = prompt_id
        db.commit()
        logger.info("Job %s submitted to ComfyUI (prompt_id=%s)", job_id, prompt_id)

        # Publish "processing" status update
        publish_job_processing(job_id)

        workflow_status = comfy_client.wait_for_outputs(
            prompt_id, max_wait_time=active_settings.comfyui_max_wait_time
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

        # For KernieGen (mock), use paths directly without organizing
        # For ComfyUI (real), organize files into user directory structure
        if backend_choice == 'kerniegen':
            organized_paths = output_paths
            logger.info("Job %s: Using KernieGen paths directly: %s", job_id, organized_paths)
        else:
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
                'comfyui_results_url': workflow_status.get('history_url'),
                'comfyui_results': workflow_status.get('raw_history'),
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

        # Publish "completed" status update
        publish_job_completed(job_id, content_id=content_item.id, output_paths=organized_paths)

        # Create notification for job completion
        try:
            notification_service = NotificationService(db)
            notification_service.create_job_completion_notification(
                user_id=job.user_id,
                job_id=job_id,
                content_id=content_item.id
            )
        except Exception as notif_error:
            logger.warning("Failed to create completion notification for job %s: %s", job_id, notif_error)

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

                # Publish "failed" status update
                publish_job_failed(job_id, error=str(exc))

                # Create notification for job failure
                try:
                    notification_service = NotificationService(db)
                    notification_service.create_job_failure_notification(
                        user_id=job.user_id,
                        job_id=job_id,
                        error_message=str(exc)[:500]  # Truncate long error messages
                    )
                except Exception as notif_error:
                    logger.warning("Failed to create failure notification for job %s: %s", job_id, notif_error)

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


# Scheduled Tasks

@celery_app.task(name="genonaut.worker.tasks.refresh_tag_cardinality_stats")
def refresh_tag_cardinality_stats() -> Dict[str, Any]:
    """Refresh tag cardinality statistics for query planning.

    This scheduled task runs daily to update the tag_cardinality_stats table
    with current counts of content items per (tag_id, content_source) pair.
    These statistics are used by the adaptive tag query planner to select
    optimal query strategies.

    Returns:
        Dict with refresh results
    """
    logger.info("Starting scheduled tag cardinality stats refresh")

    db = next(get_database_session())

    try:
        from genonaut.api.repositories.tag_repository import TagRepository

        repo = TagRepository(db)
        count = repo.refresh_tag_cardinality_stats()

        logger.info(f"Successfully refreshed {count} tag-source cardinality stats")

        return {
            "status": "success",
            "stats_refreshed": count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to refresh tag cardinality stats: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="genonaut.worker.tasks.refresh_gen_source_stats")
def refresh_gen_source_stats() -> Dict[str, Any]:
    """Refresh generation source statistics for gallery UI display.

    This scheduled task runs hourly to update the gen_source_stats table
    with current counts of content items per (user_id, source_type) pair.
    These statistics are used by the gallery UI to quickly display counts.

    Returns:
        Dict with refresh results
    """
    logger.info("Starting scheduled gen source stats refresh")

    db = next(get_database_session())

    try:
        from genonaut.api.repositories.content_repository import ContentRepository

        repo = ContentRepository(db)
        count = repo.refresh_gen_source_stats()

        logger.info(f"Successfully refreshed {count} gen source stats")

        return {
            "status": "success",
            "stats_refreshed": count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to refresh gen source stats: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="genonaut.worker.tasks.transfer_route_analytics_to_postgres")
def transfer_route_analytics_to_postgres() -> Dict[str, Any]:
    """Transfer route analytics events from Redis to PostgreSQL.

    This scheduled task runs every 10 minutes to batch-transfer route analytics
    events from Redis Streams to the route_analytics PostgreSQL table.
    After successful transfer, old entries are trimmed from Redis.

    Returns:
        Dict with transfer results
    """
    import json
    from sqlalchemy import text
    from genonaut.worker.pubsub import get_redis_client

    logger.info("Starting route analytics transfer from Redis to PostgreSQL")

    db = next(get_database_session())
    redis_client = None

    try:
        settings = get_settings()
        redis_client = get_redis_client()
        stream_key = f"{settings.redis_ns}:route_analytics:stream"

        # Read events from Redis Stream
        # Read up to 1000 events at a time
        events = redis_client.xread({stream_key: '0-0'}, count=1000, block=None)

        if not events:
            logger.info("No route analytics events to transfer")
            return {
                "status": "success",
                "events_transferred": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Extract events from response format: [(stream_name, [(id, data), ...])]
        stream_name, event_list = events[0]
        event_count = len(event_list)

        logger.info(f"Found {event_count} route analytics events to transfer")

        # Batch insert events to PostgreSQL
        insert_query = text("""
            INSERT INTO route_analytics (
                route, method, user_id, timestamp, duration_ms, status_code,
                query_params, query_params_normalized,
                request_size_bytes, response_size_bytes,
                error_type, cache_status, created_at
            ) VALUES (
                :route, :method, :user_id, :timestamp, :duration_ms, :status_code,
                :query_params, :query_params_normalized,
                :request_size_bytes, :response_size_bytes,
                :error_type, :cache_status, :created_at
            )
        """)

        events_inserted = 0
        last_event_id = None

        for event_id, event_data in event_list:
            try:
                # Parse event data
                timestamp = datetime.fromtimestamp(float(event_data.get('timestamp', 0)))
                params = {
                    'route': event_data.get('route', ''),
                    'method': event_data.get('method', 'GET'),
                    'user_id': event_data.get('user_id') or None,
                    'timestamp': timestamp,
                    'duration_ms': int(event_data.get('duration_ms', 0)),
                    'status_code': int(event_data.get('status_code', 500)),
                    'query_params': event_data.get('query_params', '{}'),
                    'query_params_normalized': event_data.get('query_params_normalized', '{}'),
                    'request_size_bytes': int(event_data.get('request_size_bytes', 0)) or None,
                    'response_size_bytes': int(event_data.get('response_size_bytes', 0)) or None,
                    'error_type': event_data.get('error_type') or None,
                    'cache_status': event_data.get('cache_status') or None,
                    'created_at': timestamp,  # Use event timestamp as created_at
                }

                db.execute(insert_query, params)
                events_inserted += 1
                last_event_id = event_id

            except Exception as e:
                logger.error(f"Failed to insert event {event_id}: {str(e)}")
                # Continue processing other events

        # Commit all inserts
        db.commit()

        logger.info(f"Successfully inserted {events_inserted} route analytics events")

        # Trim processed events from Redis Stream
        if last_event_id:
            try:
                redis_client.xtrim(stream_key, maxlen=100000, approximate=True)
                logger.info(f"Trimmed Redis stream to last 100K entries")
            except Exception as e:
                logger.warning(f"Failed to trim Redis stream: {str(e)}")

        return {
            "status": "success",
            "events_transferred": events_inserted,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to transfer route analytics: {str(e)}", exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()
        if redis_client:
            redis_client.close()


@celery_app.task(name="genonaut.worker.tasks.aggregate_route_analytics_hourly")
def aggregate_route_analytics_hourly(reference_time: Optional[str] = None) -> Dict[str, Any]:
    """Aggregate route analytics into hourly metrics.

    This scheduled task runs hourly to calculate aggregated statistics
    from raw route_analytics events and store them in route_analytics_hourly
    for fast cache planning queries.

    Args:
        reference_time: Optional ISO format timestamp string for testing.
                       When provided, uses this time instead of NOW().
                       Should be the "current" hour for aggregation.

    Returns:
        Dict with aggregation results
    """
    from sqlalchemy import text

    logger.info("Starting hourly route analytics aggregation")

    db = next(get_database_session())

    try:
        # Aggregate last hour of data
        # Use ON CONFLICT DO UPDATE for idempotency (can re-run safely)

        if reference_time:
            # For testing: use provided reference time
            aggregation_query = text("""
                INSERT INTO route_analytics_hourly (
                    timestamp, route, method, query_params_normalized,
                    total_requests, successful_requests, client_errors, server_errors,
                    avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms,
                    unique_users, avg_request_size_bytes, avg_response_size_bytes,
                    cache_hits, cache_misses, created_at
                )
                SELECT
                    DATE_TRUNC('hour', timestamp) as hour,
                    route,
                    method,
                    query_params_normalized,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as successful_requests,
                    SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as client_errors,
                    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as server_errors,
                    AVG(duration_ms)::INTEGER as avg_duration_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p50_duration_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p95_duration_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p99_duration_ms,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(request_size_bytes)::INTEGER as avg_request_size_bytes,
                    AVG(response_size_bytes)::INTEGER as avg_response_size_bytes,
                    COALESCE(SUM(CASE WHEN cache_status = 'hit' THEN 1 ELSE 0 END), 0) as cache_hits,
                    COALESCE(SUM(CASE WHEN cache_status = 'miss' THEN 1 ELSE 0 END), 0) as cache_misses,
                    CURRENT_TIMESTAMP as created_at
                FROM route_analytics
                WHERE timestamp >= DATE_TRUNC('hour', CAST(:reference_time AS timestamptz) - INTERVAL '1 hour')
                    AND timestamp < DATE_TRUNC('hour', CAST(:reference_time AS timestamptz))
                GROUP BY hour, route, method, query_params_normalized
                ON CONFLICT (timestamp, route, method, query_params_normalized) DO UPDATE SET
                    total_requests = EXCLUDED.total_requests,
                    successful_requests = EXCLUDED.successful_requests,
                    client_errors = EXCLUDED.client_errors,
                    server_errors = EXCLUDED.server_errors,
                    avg_duration_ms = EXCLUDED.avg_duration_ms,
                    p50_duration_ms = EXCLUDED.p50_duration_ms,
                    p95_duration_ms = EXCLUDED.p95_duration_ms,
                    p99_duration_ms = EXCLUDED.p99_duration_ms,
                    unique_users = EXCLUDED.unique_users,
                    avg_request_size_bytes = EXCLUDED.avg_request_size_bytes,
                    avg_response_size_bytes = EXCLUDED.avg_response_size_bytes,
                    cache_hits = EXCLUDED.cache_hits,
                    cache_misses = EXCLUDED.cache_misses
            """)
            result = db.execute(aggregation_query, {"reference_time": reference_time})
        else:
            # For production: use NOW()
            aggregation_query = text("""
                INSERT INTO route_analytics_hourly (
                    timestamp, route, method, query_params_normalized,
                    total_requests, successful_requests, client_errors, server_errors,
                    avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms,
                    unique_users, avg_request_size_bytes, avg_response_size_bytes,
                    cache_hits, cache_misses, created_at
                )
                SELECT
                    DATE_TRUNC('hour', timestamp) as hour,
                    route,
                    method,
                    query_params_normalized,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as successful_requests,
                    SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as client_errors,
                    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as server_errors,
                    AVG(duration_ms)::INTEGER as avg_duration_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p50_duration_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p95_duration_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p99_duration_ms,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(request_size_bytes)::INTEGER as avg_request_size_bytes,
                    AVG(response_size_bytes)::INTEGER as avg_response_size_bytes,
                    COALESCE(SUM(CASE WHEN cache_status = 'hit' THEN 1 ELSE 0 END), 0) as cache_hits,
                    COALESCE(SUM(CASE WHEN cache_status = 'miss' THEN 1 ELSE 0 END), 0) as cache_misses,
                    CURRENT_TIMESTAMP as created_at
                FROM route_analytics
                WHERE timestamp >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
                    AND timestamp < DATE_TRUNC('hour', NOW())
                GROUP BY hour, route, method, query_params_normalized
                ON CONFLICT (timestamp, route, method, query_params_normalized) DO UPDATE SET
                    total_requests = EXCLUDED.total_requests,
                    successful_requests = EXCLUDED.successful_requests,
                    client_errors = EXCLUDED.client_errors,
                    server_errors = EXCLUDED.server_errors,
                    avg_duration_ms = EXCLUDED.avg_duration_ms,
                    p50_duration_ms = EXCLUDED.p50_duration_ms,
                    p95_duration_ms = EXCLUDED.p95_duration_ms,
                    p99_duration_ms = EXCLUDED.p99_duration_ms,
                    unique_users = EXCLUDED.unique_users,
                    avg_request_size_bytes = EXCLUDED.avg_request_size_bytes,
                    avg_response_size_bytes = EXCLUDED.avg_response_size_bytes,
                    cache_hits = EXCLUDED.cache_hits,
                    cache_misses = EXCLUDED.cache_misses
            """)
            result = db.execute(aggregation_query)
        db.commit()

        rows_affected = result.rowcount

        logger.info(f"Successfully aggregated route analytics (rows affected: {rows_affected})")

        return {
            "status": "success",
            "rows_aggregated": rows_affected,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to aggregate route analytics: {str(e)}", exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="genonaut.worker.tasks.transfer_generation_events_to_postgres")
def transfer_generation_events_to_postgres() -> Dict[str, Any]:
    """Transfer generation events from Redis to PostgreSQL.

    This scheduled task runs every 10 minutes to batch-transfer generation
    events from Redis Streams to the generation_events PostgreSQL table.
    After successful transfer, old entries are trimmed from Redis.

    Returns:
        Dict with transfer results
    """
    import json
    from sqlalchemy import text
    from genonaut.worker.pubsub import get_redis_client

    logger.info("Starting generation events transfer from Redis to PostgreSQL")

    db = next(get_database_session())
    redis_client = None

    try:
        settings = get_settings()
        redis_client = get_redis_client()
        stream_key = f"{settings.redis_ns}:generation_events:stream"

        # Read events from Redis Stream (up to 1000 at a time)
        events = redis_client.xread({stream_key: '0-0'}, count=1000, block=None)

        if not events:
            logger.info("No generation events to transfer")
            return {
                "status": "success",
                "events_transferred": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Extract events from response format: [(stream_name, [(id, data), ...])]
        stream_name, event_list = events[0]
        event_count = len(event_list)

        logger.info(f"Found {event_count} generation events to transfer")

        # Batch insert events to PostgreSQL
        insert_query = text("""
            INSERT INTO generation_events (
                event_type, generation_id, user_id, timestamp,
                generation_type, duration_ms, success, error_type, error_message,
                queue_wait_time_ms, generation_time_ms, model_checkpoint,
                image_dimensions, batch_size, prompt_tokens, created_at
            ) VALUES (
                :event_type, :generation_id, :user_id, :timestamp,
                :generation_type, :duration_ms, :success, :error_type, :error_message,
                :queue_wait_time_ms, :generation_time_ms, :model_checkpoint,
                :image_dimensions, :batch_size, :prompt_tokens, :created_at
            )
        """)

        events_inserted = 0
        last_event_id = None

        for event_id, event_data in event_list:
            try:
                # Parse event data
                timestamp_str = event_data.get('timestamp', '')
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                else:
                    timestamp = datetime.utcnow()

                # Parse optional fields
                generation_id = event_data.get('generation_id') or None
                user_id = event_data.get('user_id') or None
                duration_ms = event_data.get('duration_ms')
                success = event_data.get('success')
                image_dimensions = event_data.get('image_dimensions')
                batch_size = event_data.get('batch_size')
                prompt_tokens = event_data.get('prompt_tokens')
                queue_wait_time_ms = event_data.get('queue_wait_time_ms')
                generation_time_ms = event_data.get('generation_time_ms')

                params = {
                    'event_type': event_data.get('event_type', 'request'),
                    'generation_id': generation_id,
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'generation_type': event_data.get('generation_type') or None,
                    'duration_ms': int(duration_ms) if duration_ms and duration_ms != '' else None,
                    'success': success == 'True' if isinstance(success, str) else success,
                    'error_type': event_data.get('error_type') or None,
                    'error_message': event_data.get('error_message') or None,
                    'queue_wait_time_ms': int(queue_wait_time_ms) if queue_wait_time_ms and queue_wait_time_ms != '' else None,
                    'generation_time_ms': int(generation_time_ms) if generation_time_ms and generation_time_ms != '' else None,
                    'model_checkpoint': event_data.get('model_checkpoint') or None,
                    'image_dimensions': image_dimensions if image_dimensions and image_dimensions != '' else None,
                    'batch_size': int(batch_size) if batch_size and batch_size != '' else None,
                    'prompt_tokens': int(prompt_tokens) if prompt_tokens and prompt_tokens != '' else None,
                    'created_at': timestamp,
                }

                db.execute(insert_query, params)
                events_inserted += 1
                last_event_id = event_id

            except Exception as e:
                logger.error(f"Failed to insert event {event_id}: {str(e)}")
                # Continue processing other events

        # Commit all inserts
        db.commit()

        logger.info(f"Successfully inserted {events_inserted} generation events")

        # Trim processed events from Redis Stream
        if last_event_id:
            try:
                redis_client.xtrim(stream_key, maxlen=100000, approximate=True)
                logger.info(f"Trimmed Redis stream to last 100K entries")
            except Exception as e:
                logger.warning(f"Failed to trim Redis stream: {str(e)}")

        return {
            "status": "success",
            "events_transferred": events_inserted,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to transfer generation events: {str(e)}", exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()
        if redis_client:
            redis_client.close()


@celery_app.task(name="genonaut.worker.tasks.aggregate_generation_metrics_hourly")
def aggregate_generation_metrics_hourly(reference_time: Optional[str] = None) -> Dict[str, Any]:
    """Aggregate generation events into hourly metrics.

    This scheduled task runs hourly to calculate aggregated statistics
    from raw generation_events and store them in generation_metrics_hourly
    for fast analytics queries.

    Args:
        reference_time: Optional ISO format timestamp string for testing.
                       When provided, uses this time instead of NOW().
                       Should be the "current" hour for aggregation.

    Returns:
        Dict with aggregation results
    """
    from sqlalchemy import text

    logger.info("Starting hourly generation metrics aggregation")

    db = next(get_database_session())

    try:
        # Aggregate last hour of data
        # Use ON CONFLICT DO UPDATE for idempotency (can re-run safely)

        if reference_time:
            # For testing: use provided reference time
            aggregation_query = text("""
                INSERT INTO generation_metrics_hourly (
                    timestamp,
                    total_requests, successful_generations, failed_generations, cancelled_generations,
                    avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms,
                    unique_users, avg_queue_length, max_queue_length,
                    total_images_generated, created_at
                )
                SELECT
                    DATE_TRUNC('hour', timestamp) as hour,
                    SUM(CASE WHEN event_type = 'request' THEN 1 ELSE 0 END) as total_requests,
                    SUM(CASE WHEN event_type = 'completion' AND success = true THEN 1 ELSE 0 END) as successful_generations,
                    SUM(CASE WHEN event_type = 'completion' AND success = false THEN 1 ELSE 0 END) as failed_generations,
                    SUM(CASE WHEN event_type = 'cancellation' THEN 1 ELSE 0 END) as cancelled_generations,
                    AVG(CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as avg_duration_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as p50_duration_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as p95_duration_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as p99_duration_ms,
                    COUNT(DISTINCT user_id) as unique_users,
                    NULL as avg_queue_length,
                    NULL as max_queue_length,
                    SUM(CASE WHEN event_type = 'completion' AND success = true THEN COALESCE(batch_size, 1) ELSE 0 END) as total_images_generated,
                    CURRENT_TIMESTAMP as created_at
                FROM generation_events
                WHERE timestamp >= DATE_TRUNC('hour', CAST(:reference_time AS timestamptz) - INTERVAL '1 hour')
                    AND timestamp < DATE_TRUNC('hour', CAST(:reference_time AS timestamptz))
                GROUP BY hour
                ON CONFLICT (timestamp) DO UPDATE SET
                    total_requests = EXCLUDED.total_requests,
                    successful_generations = EXCLUDED.successful_generations,
                    failed_generations = EXCLUDED.failed_generations,
                    cancelled_generations = EXCLUDED.cancelled_generations,
                    avg_duration_ms = EXCLUDED.avg_duration_ms,
                    p50_duration_ms = EXCLUDED.p50_duration_ms,
                    p95_duration_ms = EXCLUDED.p95_duration_ms,
                    p99_duration_ms = EXCLUDED.p99_duration_ms,
                    unique_users = EXCLUDED.unique_users,
                    total_images_generated = EXCLUDED.total_images_generated
            """)
            result = db.execute(aggregation_query, {"reference_time": reference_time})
        else:
            # For production: use NOW()
            aggregation_query = text("""
                INSERT INTO generation_metrics_hourly (
                    timestamp,
                    total_requests, successful_generations, failed_generations, cancelled_generations,
                    avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms,
                    unique_users, avg_queue_length, max_queue_length,
                    total_images_generated, created_at
                )
                SELECT
                    DATE_TRUNC('hour', timestamp) as hour,
                    SUM(CASE WHEN event_type = 'request' THEN 1 ELSE 0 END) as total_requests,
                    SUM(CASE WHEN event_type = 'completion' AND success = true THEN 1 ELSE 0 END) as successful_generations,
                    SUM(CASE WHEN event_type = 'completion' AND success = false THEN 1 ELSE 0 END) as failed_generations,
                    SUM(CASE WHEN event_type = 'cancellation' THEN 1 ELSE 0 END) as cancelled_generations,
                    AVG(CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as avg_duration_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as p50_duration_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as p95_duration_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY CASE WHEN event_type = 'completion' THEN duration_ms ELSE NULL END)::INTEGER as p99_duration_ms,
                    COUNT(DISTINCT user_id) as unique_users,
                    NULL as avg_queue_length,
                    NULL as max_queue_length,
                    SUM(CASE WHEN event_type = 'completion' AND success = true THEN COALESCE(batch_size, 1) ELSE 0 END) as total_images_generated,
                    CURRENT_TIMESTAMP as created_at
                FROM generation_events
                WHERE timestamp >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
                    AND timestamp < DATE_TRUNC('hour', NOW())
                GROUP BY hour
                ON CONFLICT (timestamp) DO UPDATE SET
                    total_requests = EXCLUDED.total_requests,
                    successful_generations = EXCLUDED.successful_generations,
                    failed_generations = EXCLUDED.failed_generations,
                    cancelled_generations = EXCLUDED.cancelled_generations,
                    avg_duration_ms = EXCLUDED.avg_duration_ms,
                    p50_duration_ms = EXCLUDED.p50_duration_ms,
                    p95_duration_ms = EXCLUDED.p95_duration_ms,
                    p99_duration_ms = EXCLUDED.p99_duration_ms,
                    unique_users = EXCLUDED.unique_users,
                    total_images_generated = EXCLUDED.total_images_generated
            """)
            result = db.execute(aggregation_query)

        db.commit()
        rows_affected = result.rowcount

        logger.info(f"Successfully aggregated generation metrics (rows affected: {rows_affected})")

        return {
            "status": "success",
            "rows_aggregated": rows_affected,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to aggregate generation metrics: {str(e)}", exc_info=True)
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()
