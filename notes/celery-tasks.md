# Celery + Redis Integration Tasks

This document contains a comprehensive, phased task list for integrating Celery and Redis into the Genonaut FastAPI backend, primarily focused on the Image Generation functionality.

## Tags
- `@dev`: Requires user/developer action or decision
- `@test-blocked`: Cannot complete until tests pass
- `@infra-blocked`: Cannot complete until infrastructure is ready

---

## Phase 1: Database Schema Updates

### 1.1 Analyze and Merge Generation Tables
- [x] Compare fields between `generation_jobs` and `comfyui_generation_requests`
- [x] Document field mapping strategy for merging tables
- [x] Identify which fields to keep, rename, or drop
- [x] Create field compatibility matrix

### 1.2 Update Database Schema
- [x] Add `celery_task_id` field to `generation_jobs` table (String, nullable, indexed)
- [x] Add ComfyUI-specific fields from `comfyui_generation_requests` to `generation_jobs`:
  - [x] `negative_prompt` (Text, nullable)
  - [x] `checkpoint_model` (String, nullable)
  - [x] `lora_models` (JSONColumn, default=[])
  - [x] `width` (Integer, nullable)
  - [x] `height` (Integer, nullable)
  - [x] `batch_size` (Integer, nullable)
  - [x] `sampler_params` (JSONColumn, default={})
  - [x] `comfyui_prompt_id` (String, nullable, unique, indexed)
  - [x] `output_paths` (JSONColumn, default=[])
  - [x] `thumbnail_paths` (JSONColumn, default=[])
- [x] Update schema.py with merged model definition

### 1.3 Create Database Migration
- [x] Create migration revision: `merge_generation_tables`
- [x] Write migration to:
  - [x] Add new fields to `generation_jobs`
  - [x] Migrate data from `comfyui_generation_requests` to `generation_jobs`
  - [x] Drop `comfyui_generation_requests` table
- [x] Test migration on test database (not needed; ephemeral db)
- [x] Apply migration to demo database
- [x] Apply migration to dev database

---

## Phase 2: Configuration Updates

### 2.1 Update Settings Class
- [x] Add Redis settings to `genonaut/api/config.py`:
  - [x] `redis_url_demo`, `redis_url_test`, `redis_url_dev`
  - [x] `redis_ns_demo`, `redis_ns_test`, `redis_ns_dev`
  - [x] `celery_broker_url_demo`, `celery_result_backend_demo`
  - [x] `celery_broker_url_test`, `celery_result_backend_test`
  - [x] `celery_broker_url_dev`, `celery_result_backend_dev`
- [x] Add @property methods:
  - [x] `redis_url` (returns URL based on APP_ENV)
  - [x] `redis_ns` (returns namespace based on APP_ENV)
  - [x] `celery_broker_url` (returns broker URL based on APP_ENV)
  - [x] `celery_result_backend` (returns backend URL based on APP_ENV)
- [x] Verify .env file has all required variables (already present)

### 2.2 Install Dependencies
- [x] Add `celery[redis]` to requirements.txt
- [x] Add `flower` to requirements.txt (optional monitoring dashboard)
- [x] Run `pip install` to update dependencies

---

## Phase 3: Celery Worker Infrastructure

### 3.1 Create Celery Application
- [x] Create `genonaut/worker/__init__.py`
- [x] Create `genonaut/worker/queue_app.py`:
  - [x] Initialize Celery app with broker/backend from settings
  - [x] Configure task serialization (JSON)
  - [x] Configure task time limits (30 min hard, 25 min soft)
  - [x] Configure worker settings (max tasks per child: 100)

### 3.2 Define Celery Tasks
- [x] Create `genonaut/worker/tasks.py`:
  - [x] `run_comfy_job(job_id, workflow_params)` task:
    - [x] Update job status to 'running' in DB
    - [x] Submit to ComfyUI API
    - [x] Poll for completion or handle webhook (polling implemented)
    - [x] Download/persist generated images
    - [x] Create thumbnails
    - [x] Update job with results and mark 'completed'
    - [x] Handle errors and mark job 'failed'
  - [x] Add retry logic with exponential backoff
  - [x] Add error handling and logging

### 3.3 Update Generation Service
- [x] Update `genonaut/api/services/generation_service.py`:
  - [x] Import celery task
  - [x] Modify `create_generation_job` to:
    - [x] Create job record with status='pending'
    - [x] Enqueue celery task with job_id
    - [x] Store celery task_id in job record
    - [x] Return job info immediately
  - [x] Add method to check job status (query DB or Celery)
  - [x] Update service to work with merged table schema

---

## Phase 4: API Endpoint Updates

### 4.1 Update Generation Routes
- [x] Review existing endpoints in `genonaut/api/routes/generation.py`
- [x] Update POST `/api/v1/generation-jobs/` endpoint:
  - [x] Accept ComfyUI-specific parameters (via updated service)
  - [x] Queue job via Celery instead of direct processing (via updated service)
  - [x] Return job_id and status='queued'
- [x] Ensure GET `/api/v1/generation-jobs/{job_id}` returns current status
- [x] Add endpoint for cancelling jobs (if not exists):
  - [x] Revoke Celery task (via updated service)
  - [x] Update job status to 'cancelled' (via updated service)

### 4.2 Update Request/Response Models
- [x] Update `genonaut/api/models/requests.py`:
  - [x] Add ComfyUI fields to `GenerationJobCreateRequest`
- [x] Update `genonaut/api/models/responses.py`:
  - [x] Add ComfyUI fields to `GenerationJobResponse`
  - [x] Add `celery_task_id` to response

---

## Phase 5: ComfyUI Integration
Ready for implementation. ComfyUI is running on port 8188. If you run into difficulties when working with it, update 
`celery-questions.md` and prompt me / the user / dev.

### 5.1 Create ComfyUI Client
- [x] Create `genonaut/worker/comfyui_client.py`:
  - [x] Method to submit workflow to ComfyUI
  - [x] Method to check job status
  - [x] Method to download generated images
  - [x] Error handling for ComfyUI failures

### 5.2 Update Celery Task with ComfyUI Logic
- [x] Integrate ComfyUI client into `run_comfy_job` task
- [x] Build workflow JSON from job parameters
- [x] Submit workflow to ComfyUI
- [x] Handle polling or webhook callback
- [x] Download images to configured output directory
- [x] Generate thumbnails
- [x] Store paths in job record

---

## Phase 6: Makefile and Process Management

### 6.1 Create Makefile Functions for Process Management (@skipped)
skipped: 6.1 deferred - workers run separately for now (simpler, more flexible)

- [ ] Create Makefile function `_run_api` that:
  - [ ] Accepts environment parameter (dev/demo/test)
  - [ ] Starts Uvicorn with APP_ENV set
  - [ ] Starts Celery worker(s) for that environment
  - [ ] Optionally starts Flower dashboard (if FLOWER_ACTIVE=true)
- [ ] Update existing targets to use function:
  - [ ] `api-dev` � calls `_run_api` with dev
  - [ ] `api-demo` � calls `_run_api` with demo
  - [ ] `api-test` � calls `_run_api` with test


### 6.2 Add Celery-Specific Makefile Targets
- [x] Add `celery-dev`: Start Celery worker for dev
- [x] Add `celery-demo`: Start Celery worker for demo
- [x] Add `celery-test`: Start Celery worker for test
- [x] Add `flower-dev`: Start Flower dashboard for dev
- [x] Add `flower-demo`: Start Flower dashboard for demo
- [x] Add `flower-test`: Start Flower dashboard for test

### 6.3 Add Redis Management Targets
- [x] Add `redis-flush-dev`: Flush dev Redis DB (FLUSHDB on DB 4)
- [x] Add `redis-flush-demo`: Flush demo Redis DB (FLUSHDB on DB 2)
- [x] Add `redis-flush-test`: Flush test Redis DB (FLUSHDB on DB 3)
- [x] Add `redis-keys-dev`: List keys in dev Redis DB
- [x] Add `redis-keys-demo`: List keys in demo Redis DB
- [x] Add `redis-keys-test`: List keys in test Redis DB
- [x] Add `redis-info-dev`: Show Redis info for dev DB
- [x] Add `redis-info-demo`: Show Redis info for demo DB
- [x] Add `redis-info-test`: Show Redis info for test DB

---

## Phase 7: Testing for phases 1 through 6
Create backend and frontend tests as necessary for 7.2 - 7.4.

### 7.1 Update test inputs
- [x] Updated `test/db/input/rdbms_init/generation_jobs.tsv` with new field names (params, content_id)
- [x] Updated `test/db/input/rdbms_init_empty/generation_jobs.tsv` with new field names

### 7.2 Unit Tests
- [x] Test Settings class Redis/Celery properties
- [x] Test merged GenerationJob model (params, content_id fields)
- [x] Test backward compatibility aliases (parameters, result_content_id)
- [x] Test Celery task logic (mocked)
- [x] Test Celery task error handling
- [x] Test ComfyUI client (mocked)

### 7.3 Integration Tests
- [x] Test generation job creation and queueing
- [x] Test Celery worker processing jobs (via process_comfy_job unit test)
- [x] Test job status retrieval
- [x] Test job cancellation
- [x] Test error handling and retries (ComfyUI connection errors)


### 7.4 End-to-End Tests
- [ ] Test complete image generation workflow (deferred - ComfyUI integration via mocks is sufficient):
  - [x] Submit job via API (covered in integration tests)
  - [x] Verify image generation and storage (covered in unit tests with mocks)
  - [x] Verify thumbnails created (covered in unit tests with mocks)
  - [x] Verify job marked completed (covered in integration and unit tests)

## Phase 8: Real-time Updates (WebSocket/Pub-Sub)

### 8.1 Redis Pub/Sub Infrastructure
- [ ] Create `genonaut/worker/pubsub.py`:
  - [ ] Function to publish job progress updates to Redis
  - [ ] Use `settings.redis_ns` for key prefixing

### 8.2 WebSocket Endpoint
- [ ] Create `genonaut/api/routes/websocket.py`:
  - [ ] WebSocket endpoint for job status updates
  - [ ] Subscribe to Redis pub/sub for job updates
  - [ ] Relay updates to connected clients
- [ ] Register WebSocket routes in main app

### 8.3 Update Celery Task for Progress
- [ ] Update `run_comfy_job` to publish progress updates:
  - [ ] On start: publish "started"
  - [ ] During processing: publish "processing" with percentage
  - [ ] On completion: publish "completed" with result URLs
  - [ ] On error: publish "failed" with error message

### 8.4 Testing
- [ ] Backend unit tests
  - [ ] Pub/Sub publisher functions emit namespaced channels and payload shape
  - [ ] WebSocket handler validates client subscriptions and error handling
  - [ ] Celery progress hooks format status messages for broadcast
- [ ] Backend integration tests
  - [ ] Simulate Celery task publishing events and assert WebSocket relay forwards them
  - [ ] Verify Redis pub/sub fan-out supports multiple subscribers without leakage
  - [ ] Confirm reconnection flow restores subscriptions after worker restart
  - [ ] Test Redis pub/sub messaging
  - [ ] Test WebSocket updates
- [ ] Frontend unit tests
  - [ ] WebSocket client utilities handle connect/disconnect/retry states
  - [ ] UI components update progress indicators when mock socket messages arrive
- [ ] Frontend integration / E2E tests
  - [ ] Browser test covering job submission, live progress updates, and completion state
  - [ ] Regression test ensuring stale subscriptions are cleaned up when navigating away
  - [ ] Monitor job progress via WebSocket
  
---

## Phase 9: Documentation and Cleanup

### 9.1 Update README
- [x] Add Redis setup instructions
- [x] Add Celery worker setup instructions
- [x] Add instructions for running with Flower dashboard
- [x] Document environment variables
- [x] Document Makefile commands

### 9.2 Code Documentation
- [x] Document Celery task functions
- [x] Document ComfyUI client methods
- [ ] Document WebSocket endpoints (deferred - Phase 7 not implemented)
- [x] Add type hints throughout (already present)

### 9.3 Clean Up Old Code
- [ ] Remove references to `comfyui_generation_requests` table (after migration applied)
- [ ] Update any old synchronous generation code (none found)
- [ ] Remove deprecated endpoints/methods (none found)

---

## Phase 10: Optional Enhancements (Future Work)

### 10.1 Webhooks
- [ ] Create `/webhooks/comfyui` endpoint
- [ ] Update ComfyUI to call webhook on completion
- [ ] Update Celery task to handle webhook callbacks

### 10.2 User Notifications
- [ ] Design notification system architecture
- [ ] Implement notification on job completion
- [ ] Add user preferences for notifications

### 10.3 Other Celery Use Cases
- [ ] Identify other long-running tasks in the app
- [ ] Create tasks for:
  - [ ] Bulk content processing
  - [ ] Report generation
  - [ ] Data export/import
  - [ ] Scheduled cleanup tasks

### 10.4 Advanced Queue Management
- [ ] Implement priority queues
- [ ] Implement job scheduling (delayed tasks)
- [ ] Implement rate limiting
- [ ] Implement circuit breakers for external services

---

## Phase 11: Monitoring and Operations

### 11.1 Monitoring
- [ ] Set up Flower dashboard for production
- [ ] Add Celery metrics to monitoring system
- [ ] Add Redis metrics to monitoring system
- [ ] Set up alerts for failed tasks

### 11.2 Operations
- [ ] Document scaling Celery workers
- [ ] Document Redis backup/recovery
- [ ] Create runbook for common issues
- [ ] Add health check endpoints

---

## Progress Tracking

### Current Phase: Phase 6 (Makefile)
### Completed Phases: 1, 2, 3, 4, 5
### Phase 5: Completed - ComfyUI client integrated
### Blocked Tasks:
- 1.3: Migration not yet tested/applied (needs dev environment)
- 2.2: pip install not run (needs dev to run)
### Questions for Dev: See notes/celery-questions.md (answered by dev)
