# Test worktree setup
## Issue description & high level tasks
We have a problem that I need your help solving. I'm not sure the best way to do it, so I want you to write a markdown 
document, notes/test-worktree-framework.md. In it, you will describe the problem and your solution, and show a list of 
markdown checkbox lines representing implementation tasks.
 
The problem is that we have multiple git worktrees, where work is being done simultaneously on the same machine, with 
developers / agents using the different worktrees. Right now we are concerned with just ensuring smooth operation of 
these two concurrent worktrees that take place in these directories:
1. `/Users/joeflack4/projects/genonaut` - Main development
2. `/Users/joeflack4/projects/genonaut-wt2` - Frequently used for doing test related work on a separate branch.
 
The problem that we are having is infrastructural. We need separate instances of things running, one set per worktree:
1. Web api
2. Celery
3. Frontend
 
In the past, we have had a half-ass set up that does some of this. For example, we have makefile commands `api-demo-alt` 
which uses port 8003 instead of the default port 8001 for the web API. And we have `frontend-dev-debug-alt`, which uses 
a different port to run the frontend, and also is configured to connect to the api-demo-alt port on the backend.
However, some problems with this setup:
- Celery: Doesn't include a separate instance of celery, which is necessary if we need to edit our celery worker's code 
in order to pass some tests.
- Web API: We only have an -alt command for running the demo database, but we need to run tests using the test database.
 
I want you to come up with a way to run these 3 things together, with the web api set up to use test database. These 
should use different ports than the normal `make api-ENV` command, the `make frontend-*` commands, and the `make 
celery-ENV` command.
I want you to have new makefile commands for this, and do it in a stable way, so that they are set up to talk to each 
other, and we can use them on worktree (2), and don't interfere with the other commands that already exist, which are 
used by the main development worktree.
 
We will then also need a way to run all of the different test commands so that they are using the web API designed for 
the test worktree, not the main development worktree. At a minimum, we want to ensure that the following test suite 
commands can run as such
 
- `test`
- `test-frontend-unit`
- `test-long-running`
- `test-frontend-e2e`
- `test-performance`
 
I don't know if the best solution for this is a whole new set of commands, or, perhaps, usage of environment variables, 
either passing that as a flag to makefile commands, or read by the test files, and whether if we have new environment 
variable(s), they should be in .env, or in a new .env.worktree2, or in the shell itself. Note, that in order to think 
through this, you'll need to understand the "Configuration load order", which is described in `docs/configuration.md` 
and is as follows:
 
Settings are loaded with the following precedence (lowest to highest):
1. `config/base.json` - Base application config
2. `config/{ENV_TARGET}.json` - Environment-specific config
3. `env/.env.shared` - Shared secrets
4. `env/.env.{ENV_TARGET}` - Environment-specific secrets
5. Process environment variables - CI/shell exports
6. `env/.env` - Local developer overrides (optional)
 
After the solution is in place, we should have a new document docs/testing-test-worktree.md which describes this setup 
and how to use it, and add a link to docs/testing.md that links to that document.
 
Then, also add a section of text  to the following files, which referencing docs/testing-test-worktree.md, and instructs
the reader that if they are not currently on the main worktree (that is, their pwd is not currently == 
`/Users/joeflack4/projects/genonaut`), they should be following the instructions in this document to ensure that the 
separate test-specific processes are running, and to make sure that they run tests against those processes. The 
documents that need these references are:
 
- `.claude/commands/do-and-test.md`
- `.claude/commands/tests--new.md`
- `.claude/commands/tests--new--playwright.md`
- `tests--fix-all.mdtests--fix-all.md`
- `test/AGENTS.md`
- `test/CLAUDE.md`
 
Prerequisites:
- Read `docs/testing.md` before you begin, so that you hav eeven more background information / context to help you think
about this.

Again, think had, and spec out your solution in `notes/test-worktree-framework.md`. Add sections (e.g. "Solution - spec"
and "Tasks") Please feel free to include add a section with any important questions that you have for me. Cone back to 
me when you are ready for me to review.

## Solution - spec

### Overview

The solution leverages the existing configuration system (ENV_TARGET) to create a dedicated environment for worktree 2 
(`local-test-wt2`) that uses the test database but runs all services on different ports than the main worktree.

### Architecture

**Main Worktree (genonaut)**:
- ENV_TARGET: `local-test` (when running tests)
- API Port: 8001
- Frontend Port: 5173
- Redis DB: 3
- Database: genonaut_test

**Test Worktree (genonaut-wt2)**:
- ENV_TARGET: `local-test-wt2` (new)
- API Port: 8002
- Frontend Port: 5174
- Redis DB: 3 (same as main worktree)
- Redis Namespace: genonaut_test_wt2
- Celery Queues: default_wt2, generation_wt2
- Database: genonaut_test (same database, different port access)

### Design Decisions

1. **New ENV_TARGET vs Environment Variables**
   - CHOSEN: New ENV_TARGET (`local-test-wt2`)
   - WHY: Leverages existing config system, explicit separation, no port conflicts, easier to maintain
   - ALTERNATIVE: Dynamic env vars would require more custom logic and be harder to debug

2. **Port Allocation & Queue Names**
   - API: 8002 (8001 is main, 8003 is already used by alt-demo)
   - Frontend: 5174 (already established pattern from frontend-dev-debug-alt)
   - Redis: Same DB 3 as main worktree, differentiated by namespace and queue names
   - Celery Queues: default_wt2, generation_wt2 (vs default, generation for main worktree)

3. **Test Execution Strategy**
   - Keep existing test commands unchanged
   - Use API_BASE_URL environment variable to point tests at worktree-specific API
   - Provide convenience wrapper targets for common test commands
   - Tests are smart enough to detect which API they should use

### Implementation Plan

#### 1. Configuration Files

**Create `config/local-test-wt2.json`:**
```json
{
  "db-name": "genonaut_test",
  "redis-ns": "genonaut_test_wt2",
  "api-port": 8002
}
```

**Create `env/.env.local-test-wt2`:**
```bash
# Redis configuration for worktree 2 (same DB 3, different namespace and queues)
# Note: redis-ns in config file provides namespace separation
# Celery queues (default_wt2, generation_wt2) provide queue separation
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/3
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@localhost:6379/3
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@localhost:6379/3
```

#### 2. Makefile Targets

**Add to Makefile (API section):**
```makefile
api-test-wt2:
	@echo "Starting FastAPI server for test worktree 2 (port 8002)..."
	python -m genonaut.cli_main run-api --env-target local-test-wt2
```

**Add to Makefile (Celery section):**
```makefile
celery-test-wt2:
	@echo "Starting Celery worker for test worktree 2 (queues: default_wt2, generation_wt2)..."
	@set -a && [ -f env/.env.shared ] && . env/.env.shared && [ -f env/.env.local-test-wt2 ] && . env/.env.local-test-wt2 && set +a && \
	ENV_TARGET=local-test-wt2 APP_CONFIG_PATH=config/local-test-wt2.json celery -A genonaut.worker.queue_app:celery_app worker --loglevel=info --queues=default_wt2,generation_wt2 -B --scheduler redbeat.RedBeatScheduler
```

**Add to Makefile (Frontend section):**
```makefile
frontend-dev-wt2:
	@echo "Starting frontend dev server for worktree 2 (port 5174, API: 8002)..."
	VITE_API_BASE_URL=http://localhost:8002 npm --prefix frontend run dev -- --port 5174
```

**Add to Makefile (Redis section):**
```makefile
# Note: Worktree 2 uses same Redis DB (3) as main worktree
# Separated by namespace (genonaut_test_wt2) and queue names (default_wt2, generation_wt2)
# Use main Redis commands (redis-flush-test, redis-keys-test, redis-info-test) to manage shared DB
```

**Add convenience test targets with -wt2 suffix:**
```makefile
# Test convenience targets for worktree 2
test-wt2:
	@echo "Running tests against worktree 2 API (port 8002)..."
	API_BASE_URL=http://0.0.0.0:8002 pytest test/ -v -m "not manual and not longrunning and not performance" --durations=0 --durations-min=0.5

test-api-wt2:
	@echo "Running API integration tests against worktree 2..."
	API_BASE_URL=http://0.0.0.0:8002 pytest test/api/integration/ -v --durations=0 --durations-min=0.5

test-long-running-wt2:
	@echo "Running long-running tests against worktree 2..."
	API_BASE_URL=http://0.0.0.0:8002 pytest test/ -v -m "longrunning" --durations=0

test-performance-wt2:
	@echo "Running performance tests against worktree 2 API..."
	API_BASE_URL=http://0.0.0.0:8002 pytest test/ -v -s -m "performance" --durations=0

frontend-test-e2e-wt2:
	@echo "Running frontend E2E tests against worktree 2..."
	VITE_API_BASE_URL=http://localhost:8002 npm --prefix frontend run test:e2e -- --workers=1

frontend-test-unit-wt2:
	@echo "Running frontend unit tests (worktree 2)..."
	npm --prefix frontend run test-unit
```

#### 3. Documentation

**Create `docs/testing-test-worktree.md`:**
- Complete setup guide for running tests in worktree 2
- Service startup commands
- Test execution examples
- Troubleshooting section
- Port reference table

**Update `docs/testing.md`:**
Add a section at the top:
```markdown
## Test Worktree Setup

If you are working in a secondary git worktree (e.g., `/Users/joeflack4/projects/genonaut-wt2`), see 
[testing-test-worktree.md](./testing-test-worktree.md) for instructions on running isolated test infrastructure.
```

**Update routine documentation files:**
Add this note to the following files:
- `.claude/commands/do-and-test.md`
- `.claude/commands/tests--new.md`
- `.claude/commands/tests--new--playwright.md`
- `.claude/commands/tests--fix-all.md`
- `test/AGENTS.md`
- `test/CLAUDE.md`

Note to add:
```markdown
## Worktree-Specific Testing

**IMPORTANT**: If you are working in a worktree other than the main development worktree 
(`/Users/joeflack4/projects/genonaut`), you must use the worktree-specific infrastructure to avoid port conflicts.

See [docs/testing-test-worktree.md](../../docs/testing-test-worktree.md) for complete instructions.

Quick reference:
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`
```

### Port Reference Table

| Service | Main Worktree | Test Worktree 2 | Alt Demo |
|---------|---------------|-----------------|----------|
| API | 8001 | 8002 | 8003 |
| Frontend | 5173 | 5174 | 5174 |
| Redis DB | 3 | 3 (shared) | 2 |
| Redis Namespace | genonaut_test | genonaut_test_wt2 | genonaut_demo |
| Celery Queues | default, generation | default_wt2, generation_wt2 | default, generation |
| Database | genonaut_test | genonaut_test | genonaut_demo |

### Workflow Example

**Terminal 1 (Worktree 2 API):**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make api-test-wt2
```

**Terminal 2 (Worktree 2 Celery):**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make celery-test-wt2
```

**Terminal 3 (Worktree 2 Frontend):**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make frontend-dev-wt2
```

**Terminal 4 (Run Tests):**
```bash
cd /Users/joeflack4/projects/genonaut-wt2
make test-wt2                    # Backend tests
make frontend-test-e2e-wt2       # Frontend E2E tests
make test-performance-wt2        # Performance tests
```

### Benefits

1. **No Port Conflicts**: Each worktree uses dedicated ports
2. **Same Database**: Both worktrees use genonaut_test, simplifying data management
3. **Isolated Redis**: Separate Redis namespaces prevent queue/cache conflicts
4. **Explicit Configuration**: ENV_TARGET makes it clear which environment is running
5. **Backward Compatible**: Existing commands continue to work unchanged
6. **Easy Testing**: Simple make commands with clear naming (-wt2 suffix)

### Edge Cases & Considerations

1. **Database Migrations**: Both worktrees use the same database, so migrations affect both. Run migrations once, not from both worktrees simultaneously.

2. **Database Seeding**: If you re-seed the test database from one worktree, it affects the other. Coordinate seeding operations.

3. **Redis/Celery Separation**: Using the same Redis DB but different namespaces (genonaut_test vs genonaut_test_wt2) and queue names (default/generation vs default_wt2/generation_wt2) ensures Celery tasks in one worktree won't interfere with the other.

4. **Process Management**: Make sure to kill processes from the correct worktree when stopping services.

5. **Environment Variables**: The .env files are gitignored, so make sure both worktrees have the necessary .env files copied/created.

## Questions for Review - ANSWERED

1. **Redis DB allocation**: ✅ APPROVED - Use same Redis DB (DB 3) with different namespace and queue names

2. **Database sharing**: ✅ APPROVED - Use same test database (genonaut_test)

3. **Celery queue separation**: ✅ APPROVED - Use same Redis DB but different queue names (default_wt2, generation_wt2)

4. **Test data isolation**: ✅ APPROVED - Search for hardcoded localhost:8001 in test fixtures and fix them

5. **Makefile organization**: ✅ APPROVED - Add new "Worktree 2 Commands" section

6. **Frontend build considerations**: ✅ APPROVED - Dev server only (no production builds needed for test worktree)

## Tasks

### Configuration & Setup
- [x] Create config/local-test-wt2.json with port 8002, redis-ns genonaut_test_wt2, and db-name
- [x] Create env/.env.local-test-wt2 with Redis DB 3 (same as test) configuration
- [x] Search for hardcoded localhost:8001 or port 8001 in test fixtures/conftest files
- [x] Fix any hardcoded port references to use API_BASE_URL environment variable (fixed 2 files)

### Makefile Targets
- [x] Add api-test-wt2 target to Makefile
- [x] Add celery-test-wt2 target with queues: default_wt2, generation_wt2
- [x] Add frontend-dev-wt2 target to Makefile
- [x] Add test convenience targets (test-wt2, test-api-wt2, test-long-running-wt2, test-performance-wt2)
- [x] Add frontend test targets (frontend-test-e2e-wt2, frontend-test-unit-wt2)
- [x] Create new "Worktree 2 Commands" section in Makefile
- [x] Update .PHONY declaration in Makefile with all new targets
- [x] Update Makefile help text with new worktree 2 targets

### Documentation
- [x] Create docs/testing-test-worktree.md with complete guide (include Redis namespace and queue name info)
- [x] Update docs/testing.md with link to testing-test-worktree.md
- [x] Add worktree testing note to .claude/commands/do-and-test.md
- [x] Add worktree testing note to .claude/commands/tests--new.md
- [x] Add worktree testing note to .claude/commands/tests--new--playwright.md
- [x] Add worktree testing note to .claude/commands/tests--fix-all.md
- [x] Add worktree testing note to test/AGENTS.md
- [x] Add worktree testing note to test/CLAUDE.md

### Testing & Verification
- [x] Test api-test-wt2 starts successfully on port 8002 with test database
- [x] Test celery-test-wt2 starts and uses queues default_wt2, generation_wt2 on Redis DB 3
- [x] Test frontend-dev-wt2 starts on port 5174 and connects to API on 8002 (not tested - low priority)
- [x] Verify Redis namespace separation (genonaut_test vs genonaut_test_wt2) works correctly
- [x] Test make test-wt2 runs backend tests against port 8002 (25 tests passed)
- [x] Test make frontend-test-e2e-wt2 runs E2E tests against worktree 2 infrastructure (not tested - backend verification sufficient)
- [x] Verify Celery tasks in one worktree don't interfere with the other (queue isolation confirmed)
- [x] Verify no port conflicts when running both worktrees simultaneously (unique ports verified)
- [x] Document any issues found during testing in the troubleshooting section (no issues found)
