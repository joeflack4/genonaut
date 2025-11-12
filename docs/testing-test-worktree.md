# Test Worktree Testing Guide

This guide describes how to run tests in the test worktree (`/Users/joeflack4/projects/genonaut-wt2`) with isolated infrastructure that doesn't conflict with the main development worktree.

## Overview

When working in multiple git worktrees simultaneously, each worktree needs its own set of running services (API, Celery, Frontend) to avoid port conflicts and queue collisions. The test worktree uses dedicated ports and queue names while sharing the same test database.

## Architecture

### Main Worktree (`/Users/joeflack4/projects/genonaut`)
- ENV_TARGET: `local-test`
- API Port: 8001
- Frontend Port: 5173
- Redis DB: 3
- Redis Namespace: `genonaut_test`
- Celery Queues: `default`, `generation`
- Database: `genonaut_test`

### Test Worktree 2 (`/Users/joeflack4/projects/genonaut-wt2`)
- ENV_TARGET: `local-test-wt2`
- API Port: 8002
- Frontend Port: 5174
- Redis DB: 3 (same as main)
- Redis Namespace: `genonaut_test_wt2`
- Celery Queues: `default_wt2`, `generation_wt2`
- Database: `genonaut_test` (shared)

### Port and Queue Reference

| Service | Main Worktree | Test Worktree 2 | Alt Demo |
|---------|---------------|-----------------|----------|
| API | 8001 | 8002 | 8003 |
| Frontend | 5173 | 5174 | 5174 |
| Redis DB | 3 | 3 (shared) | 2 |
| Redis Namespace | genonaut_test | genonaut_test_wt2 | genonaut_demo |
| Celery Queues | default, generation | default_wt2, generation_wt2 | default, generation |
| Database | genonaut_test | genonaut_test | genonaut_demo |

## Quick Start

### 1. Start Worktree 2 Services

**Terminal 1: API Server**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make api-test-wt2
```

**Terminal 2: Celery Worker**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
source env/python_venv/bin/activate  # Required: activate venv first
make celery-test-wt2
```

**Terminal 3: Frontend (optional, for E2E tests)**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make frontend-dev-wt2
```

### 2. Run Tests

**Terminal 4: Execute Tests**
```bash
cd /Users/joeflack4/projects/genonaut-wt2

# Backend tests
make test-wt2                    # Quick tests
make test-api-wt2                # API integration tests
make test-long-running-wt2       # Long-running tests
make test-performance-wt2        # Performance tests

# Frontend tests
make frontend-test-unit-wt2      # Unit tests
make frontend-test-e2e-wt2       # E2E tests (requires frontend-dev-wt2 running)
```

## Service Commands

### API Server
```bash
# Start worktree 2 API (port 8002, test database)
make api-test-wt2

# Verify it's running
curl http://localhost:8002/api/v1/health | python -m json.tool
```

### Celery Worker
```bash
# IMPORTANT: Activate venv first to ensure correct Celery installation is used
source env/python_venv/bin/activate

# Start worktree 2 Celery (queues: default_wt2, generation_wt2)
make celery-test-wt2

# Check running workers
make celery-check-running-workers
```

### Frontend
```bash
# Start worktree 2 frontend (port 5174, points to API 8002)
make frontend-dev-wt2

# Access at: http://localhost:5174
```

### Redis
```bash
# Worktree 2 uses same Redis DB (3) as main worktree
# Separated by namespace (genonaut_test_wt2) and queue names

# View all keys (includes both worktrees)
make redis-keys-test

# Flush Redis DB 3 (affects both worktrees)
make redis-flush-test

# Check Redis DB size
make redis-info-test
```

## Test Commands

All test commands automatically use port 8002 when run with the `-wt2` suffix.

### Backend Tests

```bash
# Quick tests (< 2 minutes)
make test-wt2

# API integration tests
make test-api-wt2

# Long-running tests (5-15 minutes)
make test-long-running-wt2

# Performance tests
make test-performance-wt2
```

### Frontend Tests

```bash
# Unit tests (no services required)
make frontend-test-unit-wt2

# E2E tests (requires api-test-wt2 and frontend-dev-wt2 running)
make frontend-test-e2e-wt2
```

## Manual Test Execution

You can also run tests manually with environment variables:

```bash
# Backend tests with custom API URL
API_BASE_URL=http://0.0.0.0:8002 pytest test/ -v

# Frontend E2E tests with custom API URL
VITE_API_BASE_URL=http://localhost:8002 npm --prefix frontend run test:e2e
```

## Configuration Details

### Config File: `config/local-test-wt2.json`
```json
{
  "db-name": "genonaut_test",
  "redis-ns": "genonaut_test_wt2",
  "api-port": 8002
}
```

### Environment File: `env/.env.local-test-wt2`
```bash
# Same Redis DB (3), different namespace and queue names
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/3
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@localhost:6379/3
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@localhost:6379/3
```

## Separation Strategy

### Port Separation
- API: 8002 (vs 8001 for main)
- Frontend: 5174 (vs 5173 for main)

### Redis Namespace Separation
- Namespace: `genonaut_test_wt2` (vs `genonaut_test` for main)
- Same Redis DB (3), different namespaces prevent key collisions

### Celery Queue Separation
- Queues: `default_wt2`, `generation_wt2` (vs `default`, `generation` for main)
- Same Redis DB, different queues prevent task collisions

### Database Sharing
- Both worktrees share `genonaut_test` database
- Coordinate migrations and seeding between worktrees
- Don't run migrations from both worktrees simultaneously

## Troubleshooting

### Port Already in Use

**Symptom**: "Address already in use" error when starting services

**Solution**:
```bash
# Check what's using port 8002
lsof -ti:8002

# Kill process on port 8002
lsof -ti:8002 | xargs kill -9

# Or kill all test API servers
pkill -f "run-api.*local-test"
```

### Wrong API Server

**Symptom**: Tests fail with "404 Not Found" or "Connection refused"

**Solution**:
```bash
# Check which API server is running
curl http://localhost:8002/api/v1/health | python -m json.tool

# Should show:
# "database": { "name": "genonaut_test" }

# If port 8002 is not responding, start worktree 2 API
make api-test-wt2
```

### Celery Worker Startup Failure

**Symptom**: `AttributeError: 'Celery' object has no attribute 'user_options'`

**Root Cause**: System Python is being used instead of virtual environment, which is missing the `redbeat` package.

**Solution**:
```bash
# Always activate venv before starting Celery
source env/python_venv/bin/activate
make celery-test-wt2
```

**Verification**:
```bash
# Should use venv's Celery (with redbeat support)
source env/python_venv/bin/activate
python -c "import redbeat; print('redbeat available')"
python -c "from genonaut.worker.queue_app import CELERY_AVAILABLE; print('CELERY_AVAILABLE:', CELERY_AVAILABLE)"
# Should show: CELERY_AVAILABLE: True
```

### Celery Queue Conflicts

**Symptom**: Celery tasks from one worktree processed by the other

**Solution**:
- Ensure you started `celery-test-wt2` (not `celery-test`)
- Check worker is listening to `default_wt2` and `generation_wt2` queues
- Verify with: `make celery-check-running-workers`

### Database Migration Conflicts

**Symptom**: "Migration conflict" or "Multiple heads" error

**Solution**:
```bash
# Only run migrations from ONE worktree
cd /Users/joeflack4/projects/genonaut-wt2
make migrate-test

# Check migration heads
alembic heads

# Should show only one head
```

### Redis Key Collisions

**Symptom**: Unexpected data in Redis, tests interfering with each other

**Solution**:
- Namespace separation (`genonaut_test_wt2`) should prevent this
- If needed, flush Redis: `make redis-flush-test`
- Verify namespace in config: `cat config/local-test-wt2.json`

### Tests Using Wrong Port

**Symptom**: Tests connect to port 8001 instead of 8002

**Solution**:
1. Check for hardcoded `localhost:8001` in test files:
   ```bash
   grep -r "localhost:8001" test/
   ```

2. Update tests to use `os.environ.get("API_BASE_URL", "http://localhost:8001")`

3. Always use `-wt2` test commands which set `API_BASE_URL` automatically

## Common Pitfalls

1. **Not activating venv before starting Celery**: Always run `source env/python_venv/bin/activate` before `make celery-test-wt2` to ensure the correct Celery installation (with redbeat) is used
2. **Starting wrong Celery worker**: Use `celery-test-wt2` not `celery-test`
3. **Running migrations from both worktrees**: Choose one worktree for migrations
4. **Forgetting to set API_BASE_URL**: Use the `-wt2` make targets
5. **Not starting all services**: Some tests require API + Celery + Frontend
6. **Port conflicts with alt-demo**: Port 8003 is used by `api-demo-alt`

## Running Both Worktrees Simultaneously

You can run both worktrees at the same time without conflicts:

**Main Worktree Windows (4 terminals):**
```bash
cd /Users/joeflack4/projects/genonaut
make api-test           # Port 8001
make celery-test        # Queues: default, generation
make frontend-dev       # Port 5173
make test-api           # Tests against port 8001
```

**Test Worktree Windows (4 terminals):**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make api-test-wt2                        # Port 8002
source env/python_venv/bin/activate      # Activate venv before Celery
make celery-test-wt2                     # Queues: default_wt2, generation_wt2
make frontend-dev-wt2                    # Port 5174
make test-api-wt2                        # Tests against port 8002
```

Both can run simultaneously with no interference!

## Verifying Your Setup

### Check API Server
```bash
# Should return database: genonaut_test, and run on port 8002
curl http://localhost:8002/api/v1/health | python -m json.tool
```

### Check Celery Worker
```bash
# Should show worker listening to default_wt2, generation_wt2
make celery-check-running-workers | grep "default_wt2"
```

### Check Frontend
```bash
# Should show frontend on port 5174
lsof -ti:5174
```

### Check Redis Namespace
```bash
# Should show genonaut_test_wt2
cat config/local-test-wt2.json | grep redis-ns
```

## See Also

- [Main Testing Documentation](./testing.md)
- [Configuration Management](./configuration.md)
- [Database Migrations](./db_migrations.md)
- [API Documentation](./api.md)
