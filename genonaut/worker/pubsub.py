"""Redis Pub/Sub utilities for job progress updates.

This module provides functions to publish job status updates to Redis channels,
enabling real-time notifications via WebSocket connections.
"""

import json
import logging
from typing import Any, Dict, Optional

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in some test environments
    redis = None  # type: ignore

from genonaut.api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_redis_client() -> Any:
    """Get a Redis client instance.

    Returns:
        Redis client configured with the current environment's URL
    """
    if redis is None:
        raise RuntimeError("redis package is required to use pubsub functionality. Install the 'redis' extra.")

    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_job_channel(job_id: int) -> str:
    """Get the Redis channel name for a specific job.

    Args:
        job_id: The generation job ID

    Returns:
        Namespaced channel name (e.g., "genonaut_dev:job:123")
    """
    return f"{settings.redis_ns}:job:{job_id}"


def publish_job_update(
    job_id: int,
    status: str,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Publish a job status update to Redis.

    Args:
        job_id: The generation job ID
        status: Job status (started, processing, completed, failed)
        data: Additional data to include in the update (e.g., progress percentage, error message)

    Example:
        >>> publish_job_update(123, "processing", {"progress": 50})
        >>> publish_job_update(123, "completed", {"content_id": 456, "output_paths": [...]})
        >>> publish_job_update(123, "failed", {"error": "Connection timeout"})
    """
    try:
        client = get_redis_client()
        channel = get_job_channel(job_id)

        message = {
            "job_id": job_id,
            "status": status,
            "timestamp": None,  # Will be set by Redis or client
        }

        if data:
            message.update(data)

        payload = json.dumps(message)
        subscribers = client.publish(channel, payload)

        logger.info(f"Published update to {channel}: {status} (subscribers: {subscribers})")

    except Exception as e:
        # Log error but don't fail the task
        logger.error(f"Failed to publish job update for job {job_id}: {e}", exc_info=True)


def publish_job_started(job_id: int) -> None:
    """Publish a 'started' status update for a job.

    Args:
        job_id: The generation job ID
    """
    publish_job_update(job_id, "started")


def publish_job_processing(job_id: int, progress: Optional[float] = None) -> None:
    """Publish a 'processing' status update for a job.

    Args:
        job_id: The generation job ID
        progress: Optional progress percentage (0-100)
    """
    data = {}
    if progress is not None:
        data["progress"] = progress

    publish_job_update(job_id, "processing", data)


def publish_job_completed(
    job_id: int,
    content_id: Optional[int] = None,
    output_paths: Optional[list] = None
) -> None:
    """Publish a 'completed' status update for a job.

    Args:
        job_id: The generation job ID
        content_id: ID of the created content item
        output_paths: List of output file paths
    """
    data = {}
    if content_id is not None:
        data["content_id"] = content_id
    if output_paths is not None:
        data["output_paths"] = output_paths

    publish_job_update(job_id, "completed", data)


def publish_job_failed(job_id: int, error: str) -> None:
    """Publish a 'failed' status update for a job.

    Args:
        job_id: The generation job ID
        error: Error message describing the failure
    """
    publish_job_update(job_id, "failed", {"error": error})
