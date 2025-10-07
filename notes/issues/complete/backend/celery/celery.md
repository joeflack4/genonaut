# FastAPI + Celery + Redis
This spec shows how to add **Celery + Redis** to a FastAPI backend for job orchestration. Code snippets are just 
examples. They may not be optimal or even work if you copy/paste them as-is. Think through how best to implement. The 
snippets are only there for reference / inspiration. 

## Install Redis (done)

## Redis & Celery settings
New environment variables have been added in env/ to .env and env.example. They either start with 
REDIS_ or CELERY_. There are variables for use with the different databases: dev, test, demo.

```
REDIS_URL_DEMO=redis://localhost:6379/2
REDIS_URL_TEST=redis://localhost:6379/3
REDIS_URL_DEV=redis://localhost:6379/4
REDIS_NS_DEMO=genonaut_demo
REDIS_NS_TEST=genonaut_test
REDIS_NS_DEV=genonaut_dev
CELERY_BROKER_URL_DEMO=${REDIS_URL_DEMO}
CELERY_RESULT_BACKEND_DEMO=${REDIS_URL_DEMO}
CELERY_BROKER_URL_TEST=${REDIS_URL_TEST}
CELERY_RESULT_BACKEND_TEST=${REDIS_URL_TEST}
CELERY_BROKER_URL_DEV=${REDIS_URL_DEV}
CELERY_RESULT_BACKEND_DEV=${REDIS_URL_DEV}
```

**How does the backend know which Redis URL to use?**  
You'll need to program this to be responsive to the `APP_ENV` we pass already, which we currently have dictating
which Postgres DB to connect to. E.g. `make api-demo` does: 
`APP_ENV=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload`

**Single Redis Server for Three Local Environments (_demo, _test, _dev)**
DB Index Mapping: We’ll map each Postgres DB (suffix) to a **Redis logical DB** (0–15 are available by default).

```
_demo -> DB 2
_test -> DB 3
_dev  -> DB 4
```

Corresponding Redis URLs:

```
REDIS_URL_DEMO=redis://localhost:6379/2
REDIS_URL_TEST=redis://localhost:6379/3
REDIS_URL_DEV=redis://localhost:6379/4
```

> Why different DBs? Prevents collisions and lets you safely run `FLUSHDB` in one environment without touching the others.

**Selecting the Right URL in Code**
We already have `genonaut/api/config.py`. Below is just an example of what a fresh new `Settings` class woudl look like 
that incorporates redis and celery. Use it for inspiration. Udpate our existing Settings.

genonaut/api/config.py:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"  # "demo" | "test" | "dev"
    redis_url_demo: str = "redis://localhost:6379/2"
    redis_url_test: str = "redis://localhost:6379/3"
    redis_url_dev: str  = "redis://localhost:6379/4"

    redis_ns_demo: str = "genonaut_demo"
    redis_ns_test: str = "genonaut_test"
    redis_ns_dev:  str = "genonaut_dev"

    # Celery
    celery_broker_url_demo: str | None = None
    celery_result_backend_demo: str | None = None
    celery_broker_url_test: str | None = None
    celery_result_backend_test: str | None = None
    celery_broker_url_dev: str | None = None
    celery_result_backend_dev: str | None = None

    class Config:
        env_file = ".env"

    @property
    def redis_url(self) -> str:
        return {
            "demo": self.redis_url_demo,
            "test": self.redis_url_test,
            "dev":  self.redis_url_dev,
        }[self.app_env]

    @property
    def redis_ns(self) -> str:
        return {
            "demo": self.redis_ns_demo,
            "test": self.redis_ns_test,
            "dev":  self.redis_ns_dev,
        }[self.app_env]

    @property
    def celery_broker_url(self) -> str:
        fallback = self.redis_url
        return {
            "demo": self.celery_broker_url_demo or fallback,
            "test": self.celery_broker_url_test or fallback,
            "dev":  self.celery_broker_url_dev  or fallback,
        }[self.app_env]

    @property
    def celery_result_backend(self) -> str:
        fallback = self.redis_url
        return {
            "demo": self.celery_result_backend_demo or fallback,
            "test": self.celery_result_backend_test or fallback,
            "dev":  self.celery_result_backend_dev  or fallback,
        }[self.app_env]

settings = Settings()
```

Use `settings.redis_url`, `settings.redis_ns`, `settings.celery_broker_url`, `settings.celery_result_backend` throughout your app.

## Celery app

**genonaut/worker/queue_app.py**
```python
from celery import Celery
from app.core.settings import settings

celery = Celery(
    "genonaut",
    broker=settings.celery_broker_url or settings.redis_url,
    backend=settings.celery_result_backend or settings.redis_url,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_time_limit=60*30,      # 30 min per task
    task_soft_time_limit=60*25,
    worker_max_tasks_per_child=100,
)
```

---

## Define tasks

**genonaut/worker/tasks.py**
```python
from .queue_app import celery

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def run_comfy_job(self, job_id: str, workflow: dict):
    # 1) tell DB: STARTED
    # 2) submit to ComfyUI (HTTP to /prompt or ws)
    # 3) poll or wait for webhook; when images ready, persist to storage
    # 4) write metadata/thumbnails; DB: SUCCESS; return artifact ids
    return {"job_id": job_id, "artifacts": []}
```

---

## FastAPI endpoints
We already have endpoints around this. So use the existing generation jobs endpoints, but ensure that they are updated 
to use celery. If we don't have an endpoint for getting job status, then we need to make one for that.

```python
from fastapi import FastAPI
from genonaut.worker.tasks import run_comfy_job


@app.post("/jobs")
def create_job(payload: dict):
    job_id = "generate-uuid-and-insert-row"  # write PENDING row in DB
    run_comfy_job.delay(job_id, payload)     # enqueue
    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
def get_status(job_id: str):
    # read status from your DB (preferred)
    # or: from celery if you stored AsyncResult id
    return {"job_id": job_id, "status": "STARTED/SUCCESS/FAILURE"}
```

---

## Running the backend with celery
We already have makefile commands for running the API. The first line in the demo below is for the `api-demo` command.

We'll need to ensure that the celery workers are also running, whenever starting the API.

I think it will make sense at this time to create makefile functions for this, to reduce verbosity. And the makefile 
commands that we currently have for running the variations of the backend can be wrappers that pass params into this 
function.

As for the flower dashboard, perhaps we can have a `FLOWER_ACTIVE=true` variable in the makefile, so that this will be 
on by default. It should be able to be overridden by the user passing the environment variable when running the make 
command. 

Example:
```bash
# Start FastAPI
APP_ENV=demo uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8001 --reload

# Start Celery worker
celery -A app.worker.celery_app.celery worker --loglevel=INFO -Q default -n worker@%h

# Optional: Flower dashboard
celery -A app.worker.celery_app.celery flower
```

## DB
Use DB as the **source of truth** for job state; store Celery `task_id` on your job row. The table for this will be
`generation_jobs`.

### Table Merge (COMPLETED)
The `comfyui_generation_requests` and `generation_jobs` tables have been merged into `generation_jobs`. Key decisions:

**Field Naming:**
- `parameters` → `params` (JSONB type) - consolidated all generation parameters including sampler settings
- `result_content_id` → `content_id` - simpler, reflects 1:1 relationship with ContentItem
- Removed `sampler_params`, `output_paths`, `thumbnail_paths` - consolidated into params or handled via ContentItem

**Schema Updates:**
- `params`: JSONB field containing all generation parameters (sampler settings, dimensions, etc.)
- `content_id`: Foreign key to content_items table (1 job = 1 ContentItem)
- `celery_task_id`: String field for tracking async task (indexed)
- ComfyUI fields: `negative_prompt`, `checkpoint_model`, `lora_models` (JSONB), `width`, `height`, `batch_size`, `comfyui_prompt_id`

**Migration Status:**
- Migration `9872ef1e50c3_merge_generation_tables_celery_integration` applied to demo database ✓
- Data migrated from `comfyui_generation_requests` to `generation_jobs`
- Old table dropped after migration 

## Safety & Workflow Tips
- **Never run `FLUSHALL`** on a shared Redis; use `FLUSHDB` if you must, and only inside the env DB (`redis-cli -n 4 FLUSHDB` for _dev).
- **Key prefixing**: always prefix with `settings.redis_ns:`. This keeps keys readable and safer.
- **Optional split**: You can keep broker and result backend in different DBs per env (e.g., `broker -> DB 4`, `result -> DB 14`) if you want even cleaner separation.

For instant UI updates, such as displaying the image in the "image generation" page, have the worker push progress to 
Redis Pub/Sub and your FastAPI WebSocket relays it.

We're considering of also notifying the user when the image is complete, but mark this down as a last phase / future 
task.

## Webhooks
If ComfyUI supports webhooks, expose `/webhooks/comfyui` to mark jobs done without polling (still keep Celery to 
orchestrate and post-process).

## Reference info
**Quick Sanity Checks**  
- Show current DB: `redis-cli -n 4 INFO keyspace` (for _dev).
- List keys for the env: `redis-cli -n 4 KEYS 'genonaut_dev:*'` (dev), `-n 3` for test, `-n 2` for demo.
- Flush just one env: `redis-cli -n 4 FLUSHDB` (dev only).

## Imagination & Creativity
If there's anywhere else in the app that you think would benefit from celery other than the "Image Generation" page, 
make some optional later phase tasks. 

## Documentation
Update the `README.md` in regards to any setup that is necessary for Redis (or celery, if applicable).

