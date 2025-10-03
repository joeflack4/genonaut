"""Celery application configuration for Genonaut.

This module initializes the Celery application for asynchronous task processing.
Tasks are queued via Redis and executed by Celery workers.
"""

from celery import Celery
from genonaut.api.config import get_settings

# Get settings instance
settings = get_settings()

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
