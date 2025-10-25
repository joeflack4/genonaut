# AGENTS.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Genonaut is a project to implement recommender systems for generative AI that can perpetually produce content (text, 
image, video, audio) based on user preferences.

## Environment Setup
**IMPORTANT**: Before starting any work, activate the virtual environment:
```bash
source env/python_venv/bin/activate
```
This must be done at the beginning of every session before running any Python commands, tests, or other project operations.

## How to familiarize yourself with the project
- Read `README.md` in the root of the repository, then follow links to detailed docs
- Key documentation: [developer.md](docs/developer.md), [testing.md](docs/testing.md), [api.md](docs/api.md), [db.md](docs/db.md)
- For frontend work, also read [frontend/AGENTS.md](frontend/AGENTS.md)

## Directory structure
- `config/` - JSON configuration sets that define environment-specific application settings.
- `docs/` - Project documentation for developers, testing practices, API usage, and database details.
- `env/` - Environment assets including example dotenv files, the local Python virtual environment, and Redis configs.
- `frontend/` - Vite-powered frontend application, tests, and related tooling.
- `genonaut/` - Core backend source code, including FastAPI services, models, and business logic.
- `infra/` - Infrastructure and deployment tooling such as Terraform, Kubernetes, or automation scripts.
- `notes/` - Working documentation to manage current, future, and prior tasks; almost all files here are markdown.
- `test/` - Additional testing resources and harnesses outside the main backend and frontend test suites.

## Quick Reference

### Essential Commands
```bash
# Database
make init-demo              # Initialize demo database
make api-demo               # Start API server (demo DB)
make migrate-demo           # Generate and apply DB migration

# Testing
make test-unit              # Unit tests (backend)
make test-db                # Database tests
make test-api               # API integration tests
make test-all               # All backend tests
make frontend-test          # All frontend tests

# Services
make celery-dev             # Start Celery worker
make flower-dev             # Celery monitoring UI
make frontend-dev           # Start frontend dev server
make beat-status            # Check Celery Beat schedule status

# Redis
make redis-flush-dev        # Clear Redis data
```

## Code / architecture style
- Whenever possible, functions / methods should be pure functions.
- Use types often, especially for all function / method parameters.

## Standard Operating Procedures
### Common steps to do whenever creating/updating any task / feature
1. Notes: Specs and todo lists. If there is a major task that you are working on (involves many steps / tests), 
there should be a `.md` file in `notes/` where the design is documented and there are checklists. When creating 
todo lists, ensure that tasks are not simply represeneted by bullets (`-`), but checkboxes (`- [ ]`). Ensure that when 
they are complete, they are checked off (`- [x]`).
2. Consult `notes/general-todos.md`. This is a list of uncategorized todo's / plans. See if any of these apply to your 
current task at hand. If any todos seem like they should belong in the note document you are working on, move them
there. If they are already done, check them off. Example: It may be that a test is currently being skipped, but when you
implement some functionality you are planning, you will want to enable these tests. Claude specifically: You have 
TodoWrite and TodoRead functionality. You can utilize those tools here.
3. Add tests following the three-tier testing approach (see [docs/testing.md](docs/testing.md)):
   - **Unit tests** (`make test-unit`) - No dependencies, fastest (<10s)
   - **Database tests** (`make test-db`) - Requires DB running, medium speed (30-60s)
   - **API integration tests** (`make test-api`) - Requires API server + DB, slowest (2-5min)
   - Run all: `make test-all`

   Before database/API tests, initialize test DB: `make init-test` and start test server: `make api-test`
4. Whenever you touch frontend or UI-adjacent code, add or update stable `data-testid` attributes on new layouts, 
sections, list items, loading/empty states, and interactive controls. Follow the conventions documented in 
`frontend/AGENTS.md#data-test-ids` (e.g. `page-or-component-element` naming, using MUI `inputProps`/`slotProps`), and 
update affected unit/E2E tests.
5. Add documentation: Module level docstrings, class level docstrings, function level docstrings, and method / function
level docstrings. Function / method docstrings should include information about parameters and returns, and a 
description. 
6. Periodic code commenting. For example, for a function that has several distinct steps, where each step involves a 
block of code (e.g. a `for` loop with several operations), put at least 1 comment above each block, explaining what it 
does.
7. If any new Python requirements / packages are added to the project, include them (unversioned) in the 
`requirements-unlocked.txt` file.
8.  If the new feature has a CLI, document it in a "Features" section in the `README.md`. Include a table showing the 
args, their description, defaults, data types, etc.
9. Consider otherwise any other documentation that might need to be added or updated in `README.md` after adding a 
feature, and either do those updates or ask for input.
10. Ensure that the whole test suite passes before completion of a feature or major task.
11. If there is a command involved that needs to work, but for which it does not make sense to have a test (like if you 
are asked to fix a one-off script or command), then make sure to run the command to ensure that it works, unless asked 
not to or otherwise if you think it is inadvisable to do so.

### Frontend Testing
Frontend uses Vitest for unit tests and Playwright for E2E tests (see [docs/testing.md](docs/testing.md)):

**Commands:**
- `make frontend-test-unit` or `npm run test-unit` - Unit tests only (fastest)
- `make frontend-test-e2e` or `npm run test:e2e` - E2E tests (excludes @performance tests)
- `make frontend-test-e2e-performance` - Performance E2E tests only
- `make frontend-test-e2e-debug` - E2E with verbose logging
- `make frontend-test` or `npm run test` - All frontend tests

**Prerequisites for E2E:**
- Backend API running (for real API tests)
- Playwright browsers installed: `npx playwright install`

**CRITICAL - Database Configuration for E2E:**
E2E tests use whichever API server is running on port 8001. Always check which database is connected before debugging test failures:

```bash
# Check which database is connected (database name in response)
curl http://localhost:8001/api/v1/health | python -m json.tool

# For E2E testing: use test database
make api-test              # Connects to genonaut_test

# For development: use demo database
make api-demo              # Connects to genonaut_demo
```

Common pitfall: Tests show "missing data" error but data exists -> API connected to wrong database (e.g., demo instead of test).

See [docs/testing.md#e2e-test-database-configuration](docs/testing.md#e2e-test-database-configuration) for detailed troubleshooting.

**Test types:**
- **Mock tests** - For edge cases (extreme pagination, network failures, error simulation)
- **Real API tests** - For business logic (user workflows, CRUD operations, integration testing)

### Performance Test Marking
When adding tests that measure performance (not just functional correctness), mark them appropriately:

**Backend (pytest):**
- Use `@pytest.mark.performance` decorator

**Frontend Playwright E2E:**
- Add `@performance` tag to test names: `test('my test @performance', async ({ page }) => { ... })`
- Include explicit time-based assertions
- Run separately with: `make frontend-test-e2e-performance`
- Standard functional tests (excludes @performance): `make frontend-test-e2e` 

### Documentation updates
When adding documentation:
- For detailed documentation, create files in `docs/` (e.g., `docs/api.md`, `docs/db.md`, `docs/testing.md`)
- Keep `README.md` concise with essential commands and links to detailed docs
- Update `docs/developer.md` with links to new documentation files
- Ensure cross-references between documentation files are working

### Local infrastructure
During development, the following processes should always be running:
- Postgres
- Web API (port 8001)
- Redis (port 6379)
- Celery queue worker (connects to redis) 
- ComfyUI or ComfyUI Mock - image generation service (port 8189)
- Frontend (port 5173)

### Database FYIs
#### Multiple database environments
Locally, there are three databases: dev, demo, and test
- **demo** is the canonical database for local development
- **dev** is an alternative development database
- **test** is isolated for automated testing (gets reset frequently)

During development, the web API runs on port 8001 and typically uses the demo database. Commands follow the pattern `make api-demo`, `make init-demo`, `make migrate-demo`, etc.

### Configuration
Configuration uses a two-tier system:
- **JSON config files** (`config/*.json`) - Non-sensitive application settings (committed to git)
- **.env files** (`env/.env.*`) - Sensitive credentials and secrets (excluded from git)

Load order (lowest to highest priority):
1. `config/base.json` - Base config
2. `config/{ENV_TARGET}.json` - Environment-specific config (e.g., `local-dev`, `local-demo`)
3. `env/.env.shared` - Shared secrets
4. `env/.env.{ENV_TARGET}` - Environment-specific secrets
5. Process environment variables
6. `env/.env` - Local developer overrides (gitignored)

Frontend configuration lives in `frontend/src/config/`. See [docs/configuration.md](docs/configuration.md) for details. 

### Database Migrations (Alembic)
**CRITICAL**: DO NOT edit existing Alembic version files in `genonaut/db/migrations/versions/`. Treat them as immutable history.

**SOP for schema changes:**
1. Modify SQLAlchemy models (do not write raw SQL)
2. Generate migration: `make migrate-demo` (or `migrate-dev`, `migrate-test`, `migrate-all`)
   - This runs `alembic revision --autogenerate -m "description"` and `alembic upgrade head`
3. Before creating new migrations, verify single head: `alembic heads` should show only one revision
4. Apply to all environments: `make migrate-demo`, `make migrate-dev`, `make migrate-test`
5. Test suite should pass after all environments are upgraded

**Important notes:**
- Forward-only in prod; rollbacks are for local/dev only
- For non-null columns: add with `server_default`, backfill, then remove default
- For indexes on large tables: use `postgresql_concurrently=True` with `autocommit_block()`
- See [docs/db_migrations.md](docs/db_migrations.md) for detailed procedures and troubleshooting

### Service Management
If at any point you need a service to be running (e.g. database, backend web API, frontend, or other services), you should:

1. **Start required services**: Go ahead and try to start the process as a background process using appropriate commands
(e.g., `make start-db`, `npm run dev`, `python -m uvicorn app:app`, etc.).

2. **Restart existing services**: If you need to restart a service that is already running, try to stop and start the 
process again. Use commands like:
   - `pkill -f <process_name>` or `killall <service>` to stop
   - Then start the service again with the appropriate command
   
3. **Check service status**: Before starting, you can check if a service is already running using commands like:
   - `ps aux | grep <service_name>`
   - `lsof -i :<port_number>` for services running on specific ports
   
4. **Use project-specific commands**: Look for Makefile targets, npm scripts, or other project-specific commands for 
service management (e.g., `make start-services`, `docker-compose up -d`, etc.).

Always prioritize using project-specific service management commands when available, as they are likely configured with
the correct parameters and dependencies.

### Async Task Processing (Celery + Redis)
Genonaut uses Celery with Redis for asynchronous tasks (primarily image generation via ComfyUI).

**Running workers:**
- `make celery-dev` (or `celery-demo`, `celery-test`) - Start Celery worker
- `make flower-dev` - Monitoring dashboard at http://localhost:5555

**Typical workflow:**
```bash
# Terminal 1: API server
make api-demo

# Terminal 2: Celery worker
make celery-dev

# Terminal 3: (Optional) Flower monitoring
make flower-dev
```

**Redis management:**
- `make redis-keys-dev` - List all keys
- `make redis-flush-dev` - Clear Redis data (use with caution!)

See [docs/queuing.md](docs/queuing.md) for details on WebSocket real-time updates and job monitoring.

### API Server
FastAPI backend with 77 endpoints across users, content, tags, interactions, recommendations, generation jobs, and system health.

**Running API:**
- `make api-dev`, `make api-demo`, or `make api-test`
- Access docs at http://localhost:8001/docs (Swagger) or http://localhost:8001/redoc

**Pagination:** All list endpoints support both offset-based and cursor-based pagination. Use cursor pagination for 
large datasets (>10K items) for consistent performance. See [docs/api.md](docs/api.md) for details.

**Statement timeouts:** The API enforces a PostgreSQL `statement_timeout` (default 15s dev, 30s prod) to prevent runaway
queries. Timeout errors return HTTP 504 with `error_type: "statement_timeout"`. Configure in `config/*.json` as `statement-timeout`.

### Database (PostgreSQL)
**Schema:** Core tables include `users`, `content_items`, `content_items_auto`, `user_interactions`, `recommendations`, 
`generation_jobs`, `tags`, `tag_parents`, `tag_ratings`.

**Performance:**
- Target: <200ms for any pagination query, <100ms for optimized queries

See [docs/db.md](docs/db.md) for detailed schema, JSONB patterns, and performance monitoring queries.

### File Writing and Character Encoding

When using the `Write` tool to create or update files:

1. **Use plain ASCII characters whenever possible**: Stick to standard alphanumeric characters, basic punctuation, and 
common symbols
2. **Avoid special Unicode characters**: Do not use:
   - Arrow symbols: `→` `←` `↑` `↓` `⇒` `⇐` (use `-` or `->` instead)
   - Checkmarks and X marks: `✓` `✗` `✅` `❌` (use `[YES]`/`[NO]` or `[X]` or `[ ]` instead)
   - Fancy bullets: `•` `◦` `▪` (use `-` or `*` instead)
   - Emoji or decorative Unicode characters
3. **Stick to markdown-safe characters**: Use standard markdown formatting:
   - Lists: `-` or `*` for bullets
   - Code blocks: triple backticks
   - Emphasis: `*` or `_`
   - Bold: `**` or `__`

**Why this matters**: The Write tool can sometimes corrupt special Unicode characters during file creation.

**Example - Good**:
```markdown
- [x] Feature implemented
- [ ] Not yet completed
- Step 1 -> Step 2 -> Step 3
```

### Web Requests
When making web requests:

1. **External domains**: Always ask for user permission before making web requests to domains outside of localhost, 
0.0.0.0, or 127.0.0.1
2. **Local development**: You may proceed without asking for permission when making requests to:
   - localhost
   - 0.0.0.0
   - 127.0.0.1

These local addresses are considered safe for development and testing purposes.
