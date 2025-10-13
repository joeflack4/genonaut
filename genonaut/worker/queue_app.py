"""Celery application configuration for Genonaut.

This module initializes the Celery application for asynchronous task processing.
Tasks are queued via Redis and executed by Celery workers.
"""

from types import SimpleNamespace
from uuid import uuid4

try:  # pragma: no cover - exercised implicitly during imports
    from celery import Celery
except ModuleNotFoundError:  # pragma: no cover - only used in test environments
    class Celery:  # minimal stub mirroring Celery interface
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

    # Expose a stub current_app similar to Celery's global
    current_app = Celery()

import sys
from genonaut.api.config import get_settings

# Get settings instance
settings = get_settings()

# Only print configuration when actually running as a celery worker
# (not during import for tests or other uses)
def _is_celery_worker_process():
    """Check if this process is a celery worker.

    Returns True if:
    1. 'worker' is in command line arguments (celery worker command), OR
    2. Running in a celery worker context (detected via argv)
    """
    import os

    # Method 1: Check if CELERY_WORKER environment variable is set
    # (can be set explicitly when starting workers)
    if os.environ.get('CELERY_WORKER') == '1':
        return True

    # Method 2: Check command line arguments
    # celery -A genonaut.worker.queue_app:celery_app worker
    argv_str = ' '.join(sys.argv)
    return 'worker' in sys.argv and ('celery' in argv_str or __name__ in argv_str)

if _is_celery_worker_process():
    print(f"[Celery Worker] Environment: {settings.env_target or 'unknown'}")
    print(f"[Celery Worker] ComfyUI URL: {settings.comfyui_url}")
    print(f"[Celery Worker] Redis Namespace: {settings.redis_ns}")

# Initialize Celery app
celery_app = Celery(
    "genonaut",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Time limits
    task_time_limit=60 * 30,      # 30 minutes hard limit
    task_soft_time_limit=60 * 25,  # 25 minutes soft limit

    # Worker settings
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks

    # Task routing
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # Results
    result_expires=3600 * 24,  # Results expire after 24 hours
    result_backend_transport_options={
        'master_name': 'mymaster',
    },

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task discovery
    imports=("genonaut.worker.tasks",),
)

# Optional: Configure task routes for different queues
celery_app.conf.task_routes = {
    "genonaut.worker.tasks.run_comfy_job": {"queue": "generation"},
    "genonaut.worker.tasks.*": {"queue": "default"},
}
