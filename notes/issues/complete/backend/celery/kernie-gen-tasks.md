# KernieGen Integration - Issue Analysis and Tasks

## Problem Summary
The mock ComfyUI server (kernie-gen) is not receiving requests when you click "generate" in the image generation page, despite:
- Changing `COMFYUI_URL` to `http://localhost:8189` in `.env`
- Starting the mock server on port 8189
- Restarting the API server

## Root Cause
The Celery worker process is still using the old configuration that points to `http://localhost:8000`.

### Technical Details
1. **Configuration loading**: Both the API server and Celery worker load settings via `get_settings()` (genonaut/api/config.py:127)
2. **Cached settings**: The `get_settings()` function uses `@lru_cache()`, meaning settings are loaded once and cached for the lifetime of the process
3. **Worker independence**: The Celery worker runs as a separate process from the API server
4. **ComfyUI client initialization**: When the worker processes a generation job, it creates a `ComfyUIWorkerClient` which reads `self.settings.comfyui_url` (genonaut/api/services/comfyui_client.py:36)

### Flow of Events
1. User clicks "generate" in UI
2. API server (with NEW config) receives request and creates a generation job
3. API server queues the job to Celery via Redis
4. Celery worker (with OLD cached config) picks up the job
5. Worker creates `ComfyUIWorkerClient` which connects to `http://localhost:8000` (the old URL)
6. Request fails because nothing is running on port 8189
7. Mock server on port 8189 receives no traffic

## Tasks

### Immediate Fix
- [ ] Restart the Celery worker process for the local-demo environment
  - Stop: Find and kill the existing `celery` process (e.g., `pkill -f "celery.*local-demo"`)
  - Start: Run `make celery-demo` to start with fresh config

### Verification
- [ ] Confirm mock server is running: `curl http://localhost:8189/` should return mock server info
- [ ] Click "generate" in the UI
- [ ] Check mock server logs for incoming POST request to `/prompt`
- [ ] Verify job completes successfully

### Documentation Improvements
- [ ] Add note to CLAUDE.md or docs about restarting workers when config changes
- [ ] Consider adding a troubleshooting section to developer docs
- [ ] Document the relationship between API server, Celery worker, and configuration

### Future Enhancements (Optional)
- [ ] Add health check endpoint that shows which ComfyUI URL is in use
- [ ] Add configuration validation on startup that warns about mismatched configs
- [ ] Consider hot-reloading config for workers (complex, may not be worth it)
- [ ] Add a "service status" page showing which services are running and their configs

## Expected Outcome
After restarting the Celery worker, the mock ComfyUI server should receive workflow submissions when you click "generate", and you should see log output like:
```
INFO:     127.0.0.1:XXXXX - "POST /prompt HTTP/1.1" 200 OK
```
