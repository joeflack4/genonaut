# FastAPI + Celery + Redis Setup Guide (macOS)

This guide shows how to add **Celery + Redis** to a FastAPI backend for job orchestration.

---

## 2) Settings

**.env**
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

**app/core/settings.py**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 3) Celery app

**app/worker/celery_app.py**
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

## 4) Define tasks

**app/worker/tasks.py**
```python
from .celery_app import celery

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def run_comfy_job(self, job_id: str, workflow: dict):
    # 1) tell DB: STARTED
    # 2) submit to ComfyUI (HTTP to /prompt or ws)
    # 3) poll or wait for webhook; when images ready, persist to storage
    # 4) write metadata/thumbnails; DB: SUCCESS; return artifact ids
    return {"job_id": job_id, "artifacts": []}
```

---

## 5) FastAPI endpoints

**app/main.py**
```python
from fastapi import FastAPI
from app.worker.tasks import run_comfy_job

app = FastAPI()

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

## 6) Run it

```bash
# Start FastAPI
uvicorn app.main:app --reload

# Start Celery worker
celery -A app.worker.celery_app.celery worker --loglevel=INFO -Q default -n worker@%h

# Optional: Flower dashboard
celery -A app.worker.celery_app.celery flower
```

---

## Tips

- Use DB as the **source of truth** for job state; store Celery `task_id` on your job row.
- For instant UI updates, have the worker push progress to Redis Pub/Sub and your FastAPI WebSocket relays it.
- If ComfyUI supports webhooks, expose `/webhooks/comfyui` to mark jobs done without polling (still keep Celery to orchestrate and post-process).









-----------------









# Single Redis Server for Three Local Environments (_demo, _test, _dev)
## 1) DB Index Mapping

We’ll map each Postgres DB (suffix) to a **Redis logical DB** (0–15 are available by default).

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

---

## 2) .env Examples (this is already done; env/.env and env/env.example are already updated)

Create or update your `.env` with per-environment URLs and a namespace prefix (used for keys/queues).

```env
# Redis URLs (single server, 3 logical DBs)
REDIS_URL_DEMO=redis://localhost:6379/2
REDIS_URL_TEST=redis://localhost:6379/3
REDIS_URL_DEV=redis://localhost:6379/4

# Active environment (one of: demo, test, dev)
APP_ENV=dev

# Optional: per-env namespaces for keys/queues (recommended)
REDIS_NS_DEMO=genonaut_demo
REDIS_NS_TEST=genonaut_test
REDIS_NS_DEV=genonaut_dev

# Celery (you can keep broker and result in the same DB, or split them—see §4)
CELERY_BROKER_URL_DEMO=${REDIS_URL_DEMO}
CELERY_RESULT_BACKEND_DEMO=${REDIS_URL_DEMO}

CELERY_BROKER_URL_TEST=${REDIS_URL_TEST}
CELERY_RESULT_BACKEND_TEST=${REDIS_URL_TEST}

CELERY_BROKER_URL_DEV=${REDIS_URL_DEV}
CELERY_RESULT_BACKEND_DEV=${REDIS_URL_DEV}
```

---

## 3) Selecting the Right URL in Code

**app/core/settings.py**

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

---

## 4) Celery Wiring (Single Redis, Separate DBs)

**app/worker/celery_app.py**

```python
from celery import Celery
from app.core.settings import settings

celery = Celery(
    "genonaut",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Optional: put tasks in per-env queues
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_time_limit=60*30,
    task_soft_time_limit=60*25,
    worker_max_tasks_per_child=100,
    task_default_queue=f"{settings.redis_ns}:queue:default",
)
```

**app/worker/tasks.py**

```python
from .celery_app import celery
from app.core.settings import settings

def k(key: str) -> str:
    # Namespace your keys to avoid collisions across envs
    return f"{settings.redis_ns}:{key}"

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def run_comfy_job(self, job_id: str, workflow: dict):
    # Example: publish progress channel per env
    progress_channel = k(f"progress:{job_id}")
    # ... do work ...
    return {"job_id": job_id, "artifacts": []}
```

---

## 5) Running Workers Per Environment

You can run a worker per environment by switching `APP_ENV` before launching.

**Dev**

```bash
export APP_ENV=dev
celery -A app.worker.celery_app.celery worker --loglevel=INFO -Q genonaut_dev:queue:default -n worker-dev@%h
```

**Test**

```bash
export APP_ENV=test
celery -A app.worker.celery_app.celery worker --loglevel=INFO -Q genonaut_test:queue:default -n worker-test@%h
```

**Demo**

```bash
export APP_ENV=demo
celery -A app.worker.celery_app.celery worker --loglevel=INFO -Q genonaut_demo:queue:default -n worker-demo@%h
```

> You can also run multiple workers simultaneously if you want, each with different `APP_ENV` values (they’ll connect to different logical DBs).

---

## 6) Using the Right URL from FastAPI

Example endpoint that enqueues a job and records which env it went to:

```python
from fastapi import APIRouter
from app.core.settings import settings
from app.worker.tasks import run_comfy_job

router = APIRouter()

@router.post("/jobs")
def create_job(payload: dict):
    job_id = "uuid-here"   # insert DB row as PENDING
    # Enqueue in the env-specific queue
    run_comfy_job.apply_async(args=[job_id, payload], queue=f"{settings.redis_ns}:queue:default")
    return {
        "job_id": job_id,
        "env": settings.app_env,
        "broker": settings.celery_broker_url,
        "backend": settings.celery_result_backend,
        "status": "queued",
    }
```

---

## 7) Safety & Workflow Tips

- **Never run `FLUSHALL`** on a shared Redis; use `FLUSHDB` if you must, and only inside the env DB (`redis-cli -n 4 FLUSHDB` for _dev).
- **Key prefixing**: always prefix with `settings.redis_ns:`. This keeps keys readable and safer.
- **Optional split**: You can keep broker and result backend in different DBs per env (e.g., `broker -> DB 4`, `result -> DB 14`) if you want even cleaner separation.
- **Flower**: monitor tasks per env by running Flower separately with different `APP_ENV` values:
  ```bash
  export APP_ENV=dev && celery -A app.worker.celery_app.celery flower --port=5555
  export APP_ENV=test && celery -A app.worker.celery_app.celery flower --port=5556
  ```

---

## 8) Quick Sanity Checks

- Show current DB: `redis-cli -n 4 INFO keyspace` (for _dev).
- List keys for the env: `redis-cli -n 4 KEYS 'genonaut_dev:*'` (dev), `-n 3` for test, `-n 2` for demo.
- Flush just one env: `redis-cli -n 4 FLUSHDB` (dev only).

---

## 9) Summary

- One Redis server is enough for local dev.
- Use **different logical DBs + key namespaces** to isolate environments.
- Switch environments via `APP_ENV` and pick URLs automatically with your settings class.
- Optional: separate queues per env, run multiple workers side-by-side, and monitor with Flower.
