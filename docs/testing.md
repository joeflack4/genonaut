# Testing Documentation

Genonaut uses a comprehensive three-tier testing approach to ensure code quality and reliability across all components.

## Related documentation
- `test-troubleshooting-db-and-server.md`: When to read this? If you are having difficulties with tests involving: database setup, server startup, and E2E test execution.

## Test Worktree Setup

**IMPORTANT**: If you are working in a secondary git worktree (e.g., `/Users/joeflack4/projects/genonaut-wt2`), you must use dedicated infrastructure to avoid port conflicts with the main worktree.

See [testing-test-worktree.md](./testing-test-worktree.md) for complete instructions on:
- Starting worktree-specific services (API, Celery, Frontend)
- Running tests against the correct infrastructure
- Port and queue separation strategy
- Troubleshooting worktree-specific issues

**Quick Reference for Worktree 2:**
- Starting services: `make api-test-wt2` and `make celery-test-wt2` (and also `make frontend-dev-wt2` if needed)
- Running tests: `make test-wt2`, `make test-api-wt2`, `make frontend-test-e2e-wt2`

## API Server Management for Testing

**IMPORTANT**: When working with test API servers, use the environment-specific stop and restart commands instead of manually killing processes with `pkill` or `killall`.

**Why this matters:**
- Prevents accidentally killing API servers in other worktrees
- Pattern-matches on exact `--env-target` flag for precise targeting
- Includes proper cleanup with a 3-second wait period
- Essential when debugging test failures that may be caused by stale server state

**Common Testing Scenarios:**

**Restarting After Code Changes:**
```bash
# After changing Pydantic models or other non-hot-reload code:
make api-test-wt2-restart

# Or manually:
make api-test-wt2-stop
# ... clear Python bytecode cache if needed ...
make api-test-wt2
```

**Clearing Python Bytecode Cache:**
```bash
# When Uvicorn auto-reload doesn't pick up changes:
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
make api-test-wt2-restart
```

**Available Test Server Commands:**
- `make api-test-stop` / `make api-test-restart` - Worktree 1 test server (port 8001)
- `make api-test-wt2-stop` / `make api-test-wt2-restart` - Worktree 2 test server (port 8002)

**What NOT to do:**
```bash
# DON'T use generic pkill - kills ALL API servers:
pkill -f "run-api"

# DO use environment-specific commands:
make api-test-wt2-restart
```

See [docs/infra.md](./infra.md#api-server-management-stop-and-restart-commands) for the complete list of stop/restart commands for all environments.

## Testing Strategy

**🔄 Incremental Testing During Development**
Tests should be written and executed during each development phase, not just at the end. This ensures early detection of issues and maintains code quality throughout the development cycle.

> **Tip:** Initialize the test database (`make init-test`) and start the FastAPI test server (`make api-test`) before running database or API integration suites. This keeps tests isolated from dev/demo data.

**📊 Three-Tier Testing Architecture:**

| Test Type | Dependencies | Purpose | Speed |
|-----------|--------------|---------|-------|
| **Unit Tests** | None | Test individual components in isolation | ⚡ Fastest |
| **Database Tests** | Database Server | Test data layer and business logic | 🔄 Medium |
| **API Integration Tests** | Web Server + Database | Test complete workflows and endpoints | 🐌 Slowest |

## Design: Mock Tests vs Real API Tests

### Hybrid Testing Strategy

Genonaut uses a hybrid approach for E2E testing that combines mock-based tests for edge cases with real API tests for business logic validation.

### When to Use Mock Tests

**✅ Use Mock Tests For:**

**Edge Case Scenarios**
- Extreme pagination (page 50,000 of 1,000,000 records)
- Network failures and timeouts
- Malformed API responses
- Rate limiting scenarios
- Very large dataset simulations that would be impractical to seed

**Error Simulation**
- Connection drops during requests
- Specific HTTP status codes (500, 503, etc.)
- Malformed JSON responses
- Authentication failures
- Service unavailable scenarios

**Performance Baseline Testing**
- Memory exhaustion scenarios
- Extreme concurrency (1000+ simultaneous requests)
- Large payload handling
- Browser resource limits

**Example Mock Test Use Cases:**
```typescript
// Mock test for extreme pagination scenario
test('handles pagination with 1M+ records', async ({ page }) => {
  await setupMockApi(page, [{
    pattern: '/api/v1/content/unified',
    body: {
      pagination: { total_count: 10000000, total_pages: 1000000 }
    }
  }])
  // Test UI behavior with extreme numbers
})

// Mock test for network failure simulation
test('gracefully handles API timeout', async ({ page }) => {
  await setupMockApi(page, [{
    pattern: '/api/v1/content/unified',
    delay: 30000, // Simulate timeout
    status: 408
  }])
  // Test error handling and recovery
})
```

### When to Use Real API Tests

**✅ Use Real API Tests For:**

**Business Logic Validation**
- User authentication flows
- Content CRUD operations
- Search and filtering functionality
- Data consistency verification
- Basic pagination (realistic dataset sizes)

**Integration Testing**
- Database query correctness
- API contract validation
- Data serialization/deserialization
- Foreign key constraints
- Transaction handling

**User Workflow Testing**
- End-to-end user journeys
- Multi-step operations
- State management across pages
- Real data relationships

**Example Real API Test Use Cases:**
```typescript
// Real API test for business logic
test('filters content by type correctly', async ({ page }) => {
  // Uses actual database and API
  await page.goto('/gallery')
  await toggleContentTypeFilter(page, 'regular', false)

  const pagination = await getPaginationInfo(page)
  const apiResponse = await getUnifiedContent(page, { content_types: 'auto' })

  // Validates real data consistency
  expect(pagination.results).toBe(apiResponse.pagination.total_count)
})

// Real API test for user workflow
test('creates and edits content successfully', async ({ page }) => {
  await loginAsTestUser(page)
  await createTestContent(page, { title: 'Test Content' })
  await editContentMetadata(page, { title: 'Updated Title' })

  // Verifies actual database state
  const content = await getContentFromApi(page, testContentId)
  expect(content.title).toBe('Updated Title')
})
```

### Decision Matrix

| Scenario | Mock | Real API | Reason |
|----------|------|----------|--------|
| Normal pagination (10-100 pages) | ❌ | ✅ | Real data relationships needed |
| Extreme pagination (50K+ pages) | ✅ | ❌ | Impractical to seed that much data |
| User login flow | ❌ | ✅ | Test actual authentication logic |
| Network timeout handling | ✅ | ❌ | Need to simulate specific failure |
| Content type filtering | ❌ | ✅ | Validate SQL queries and results |
| Memory leak detection | ✅ | ❌ | Need controlled data patterns |
| Search functionality | ❌ | ✅ | Test real text matching algorithms |
| Rate limiting behavior | ✅ | ❌ | Simulate specific error responses |

### Test File Organization

**Mock Test Files:**
- `error-handling.spec.ts` - Network failures, timeouts, malformed responses
- `performance.spec.ts` - Extreme dataset simulations, memory testing
- `loading-errors.spec.ts` - Basic error state testing
- `gallery.spec.ts` - Edge case pagination scenarios (kept minimal)

**Real API Test Files:**
- `auth-real-api.spec.ts` - Authentication flows and user management
- `dashboard-real-api.spec.ts` - Dashboard functionality and statistics
- `gallery-real-api.spec.ts` - Gallery pagination and content display
- `search-filtering-real-api.spec.ts` - Search and filtering functionality
- `content-crud-real-api.spec.ts` - Content creation, editing, deletion
- `settings-real-api.spec.ts` - User settings and preferences
- `recommendations-real-api.spec.ts` - Recommendation system testing

### Implementation Guidelines

**Mock Test Guidelines:**
- Use precise mock patterns that match your edge case scenario
- Keep mock complexity minimal - focus on the specific edge case
- Document why the mock is needed vs real API
- Use defensive programming for pattern matching

**Real API Test Guidelines:**
- Use defensive skips when API server isn't available
- Verify sufficient test data exists before running assertions
- Clean up test data to maintain isolation
- Use helper functions for common API operations

### Migration Strategy

When converting from mock to real API tests:

1. **Evaluate necessity**: Does this test serve a legitimate edge case?
2. **Check implementation**: Is the functionality actually implemented?
3. **Assess data requirements**: Can this be tested with realistic data volumes?
4. **Convert or preserve**: Either convert to real API or preserve as edge case mock

This hybrid approach ensures comprehensive coverage while maintaining test performance and reliability.

## Test Commands

### Test Database Quickstart
```bash
# 1. Configure env vars (DATABASE_URL_TEST or DB_NAME_TEST)
make init-test             # once to seed the dedicated test DB

# 2. In a separate terminal
make api-test              # start FastAPI against the test database

# 3. Run suites in the primary terminal
make test-db               # repository + service tests
make test-api              # HTTP integration tests (hits api-test instance)
```

> The `make init-test` target truncates tables and resets identities so repeated runs stay deterministic.

### Quick Testing (Single Tier)
```bash
# Unit tests only (fastest, no setup required)
make test-unit

# Database tests (requires DB setup)
make test-db              # All database tests
make test-db-unit         # Database unit tests only (no DB required)
make test-db-integration  # Database integration tests only (DB required)

# API integration tests (requires web server running)
make test-api
```

## Database Initialization & Seeding Control

Behind the scenes, most setup commands and database fixtures call `initialize_database()` from `genonaut.db.init`. Its default behaviour is to:

- Detect the appropriate environment config and seed directory
- Create databases/schemas when missing
- Apply Alembic migrations (dropping/recreating tables if needed)
- Seed canonical TSV data (demo/test fixtures)

### `auto_seed` flag (default `True`)

For day-to-day usage—`make init-demo`, `make init-test`, `make migrate-*`, `make api-*`, `make test`, etc.—no changes are required. All of those pathways keep seeding data automatically because the default remains `auto_seed=True`.

You only pass `auto_seed=False` when a specific test needs to start from a truly empty schema. Example:

```python
initialize_database(
    database_url=test_db_url,
    create_db=True,
    drop_existing=True,
    environment="test",
    auto_seed=False,  # Opt-out when the test wants to create every record itself
)
```

Common scenarios:

- Verifying raw migration behaviour or Alembic bootstrap logic
- Suites that want to assert “no data exists until I insert it”
- Performance or isolation checks that might be skewed by the seed dataset

When you disable seeding, make sure you reseed afterwards if other suites rely on the canonical fixtures. The end-to-end initialization tests demonstrate this pattern (see below).

## Database Initialization Test Suite

`test/db/integration/test_database_end_to_end.py` validates the full bootstrapping pipeline (engine setup, Alembic migrations, seeding, schema sanity checks). We now run each case with `auto_seed=False`, then reseed automatically in the fixture teardown so the rest of the test run continues with the expected dataset.

Helpful commands:

```bash
source env/python_venv/bin/activate
ENV_TARGET=local-test pytest test/db/integration/test_database_end_to_end.py::TestDatabaseEndToEnd -q
```

Because the teardown step calls `initialize_database(..., auto_seed=True)` you do **not** need to rerun `make init-test` after executing this suite; the canonical seed data is restored automatically.

For lower-level coverage, `test/db/unit/test_database_initializer.py` exercises `DatabaseInitializer` directly—creating/dropping tables, enabling extensions, and seeding TSV directories. These tests run quickly against the local PostgreSQL test database (`ENV_TARGET=local-test`) and now expect the `auto_seed` behaviour documented above.

### Database Truncation Control

**⚠️ Important: Test Database Persistence**

The `genonaut_test` database is **persistent by default** - it will NOT be truncated between test runs. This preserves seeded data and prevents accidental data loss during development. Only the `genonaut_test_init` database is truncated automatically before tests.

**Configuration:**

The truncation behavior is controlled by `test/db/test_config.py`:

| Database | Default Behavior | Purpose |
|----------|------------------|---------|
| `genonaut_test` | **NOT truncated** | Main test database - persistent for test runs |
| `genonaut_test_init` | **Truncated** | Initialization test database - ephemeral |

**Environment Variable Overrides:**

```bash
# Force truncate genonaut_test (useful for clean slate)
TRUNCATE_TEST_DB=1 pytest test/

# Skip truncating genonaut_test_init (preserve data)
TRUNCATE_TEST_INIT_DB=0 pytest test/
```

**Example Usage:**

```bash
# Normal test run - genonaut_test data persists
pytest test/db/unit/

# Output:
# Skipping truncation of 'genonaut_test' database (persistent mode)
# To force truncation, set TRUNCATE_TEST_DB=1 environment variable

# Force clean slate - truncate all tables
TRUNCATE_TEST_DB=1 pytest test/db/unit/

# Output:
# Truncating 'genonaut_test' database before test session...
# Truncated 25 tables in 'genonaut_test'
```

**When to Truncate:**

- **Normal development:** Let `genonaut_test` persist (default)
- **Clean slate needed:** Use `TRUNCATE_TEST_DB=1` to reset
- **After schema changes:** Re-run `make init-test` to rebuild with migrations
- **Debugging test failures:** Try `TRUNCATE_TEST_DB=1` to rule out data pollution

**Implementation Details:**

The `pytest_sessionstart` hook in `test/conftest.py` checks the database name and configuration before deciding whether to truncate. This ensures that:
- Test data seeded via `make init-test` or `make import-demo-seed-to-test` persists across test runs
- Initialization tests that need empty databases can use `genonaut_test_init`
- Developers can force truncation when needed via environment variables

### Two-Database Architecture: Persistent vs Ephemeral

Genonaut uses two separate test databases with fundamentally different purposes and lifecycle management:

**`genonaut_test` (Persistent Database)**
- **Purpose**: Main test database for all standard test runs (unit, integration, API tests)
- **Seeding**: Initialized once via `make init-test`, data persists across test runs
- **Teardown**: Uses savepoint-based rollback for test isolation - seed data is NEVER deleted during tests
- **When to use**: All normal tests that rely on stable seed data (test users, content items, tags, etc.)
- **Risk**: Database initialization tests that call `initialize_database(drop_existing=True)` would wipe seed data if run against this database

**`genonaut_test_init` (Ephemeral Database)**
- **Purpose**: Dedicated database for testing database initialization logic itself
- **Seeding**: Recreated/reseeded as needed by initialization tests
- **Teardown**: Tests can freely drop tables, truncate data, or call `initialize_database(drop_existing=True)`
- **When to use**: Database initialization tests, migration tests, schema validation tests that need to start from empty state
- **Protection**: Keeps destructive initialization tests isolated from the persistent test database

This separation prevents database initialization tests from accidentally wiping seed data that other tests depend on. Tests that need to perform destructive operations (drop tables, recreate schema) should always use `genonaut_test_init` to avoid affecting the persistent `genonaut_test` database.

### `local-test-init` Environment

When you need to build or validate seeding/initialization flows without affecting the main test database, use the dedicated `local-test-init` environment. It lives alongside `config/local-test-init.json` and points at the `genonaut_test_init` database.

Handy commands:

```bash
# Create / reset the test-init database
make init-test-init

# Apply the latest migrations against test-init
make migrate-test-init

# Drop and recreate from scratch if needed
make recreate-test-init
```

Inside Python or custom scripts you can pass `ENV_TARGET=local-test-init` (or `--env-target local-test-init` to `genonaut.cli_main init-db`) to reuse the same configuration. This keeps the canonical `local-test` database seeded for the rest of the suite while giving you an isolated sandbox for migration + TSV experiments.

### Admin User Seeding for E2E Tests

**Background**: E2E tests depend on a specific admin user (`demo_admin`, ID: `121e194b-4caa-4b81-ad4f-86ca3919d5b9`) that exists in the `demo` database. This user and all related data must also exist in the `test` database for E2E tests to pass.

**Solution**: The export/import workflow now automatically includes the admin user and all related data:

**How it works:**
1. **Export** (`make export-demo-seed`): Exports demo database slices to TSV files
   - By default, includes admin user (`121e194b-4caa-4b81-ad4f-86ca3919d5b9`) and ALL dependencies
   - Uses recursive FK traversal to export related records (content items, interactions, jobs, etc.)
   - Exports to `test/db/input/rdbms_init_from_demo/`
   - Exported ~2000 total rows including 449 content items from admin user

2. **Import** (`make init-test`): Imports TSV files into test database
   - Admin user and all related data are automatically included
   - Test database now has deterministic, consistent data for E2E tests

**CLI Options:**

```bash
# Default: include admin user (recommended)
make export-demo-seed

# Exclude admin user if needed (not recommended for E2E test data)
python -m genonaut.db.demo.seed_data_gen.export_seed_from_demo --exclude-admin-user

# Use different admin user ID
python -m genonaut.db.demo.seed_data_gen.export_seed_from_demo --admin-user-id <UUID>

# Refresh test database with latest demo data
make refresh-test-seed-from-demo  # Runs export + import automatically
```

**Verifying Admin User:**

```bash
# Check admin user exists in test database
PGPASSWORD=chocolateRainbows858 psql -h localhost -U genonaut_admin -d genonaut_test \
  -c "SELECT id, username, email FROM users WHERE id = '121e194b-4caa-4b81-ad4f-86ca3919d5b9';"
```

Expected output:
```
                  id                  |  username  |          email
--------------------------------------+------------+-------------------------
 121e194b-4caa-4b81-ad4f-86ca3919d5b9 | demo_admin | demo-admin@genonaut.com
(1 row)
```

**Impact on E2E Tests:**
- E2E tests can reliably use `demo_admin` user in both demo and test databases
- Test data is deterministic and consistent
- No need for conditional logic based on which database is running
- Frontend E2E tests (e.g., `frontend/tests/e2e/utils/realApiHelpers.ts`) work consistently

**Troubleshooting:**

If E2E tests fail with 404 errors for admin user:
1. Verify which database API is connected to: `curl http://localhost:8001/api/v1/health`
2. Re-export and import: `make refresh-test-seed-from-demo`
3. Restart test API: `make api-test`
4. Run E2E tests: `make frontend-test-e2e`

### Comprehensive Testing
```bash
# Run all test suites in sequence
make test-all

# Legacy command (runs all tests at once)
make test
```

## Test Execution Requirements

### 1. Unit Tests (`make test-unit`)
**No external dependencies required** ✅
- **What's tested:** Pydantic models, configuration, exceptions, utilities
- **Setup required:** None
- **Speed:** Very fast (< 10 seconds)
- **Use case:** Quick validation during development

```bash
make test-unit
```

### 2. Database Tests (`make test-db`)
**Requires database server** 🗄️
- **What's tested:** Repositories, services, database operations, JSONB queries, schema models, DB initialization
- **Setup required:** PostgreSQL database running with credentials in `.env`
- **Speed:** Medium (30-60 seconds)
- **Use case:** Validate data layer and business logic

**Prerequisites:**
1. Database server running
2. Environment variables configured in `.env`
3. Database initialized: `make init-dev` or `make init-demo`

```bash
# Setup database first
make init-dev

# Run all database tests
make test-db

# Run only database unit tests (no DB required)
make test-db-unit

# Run only database integration tests (DB required)
make test-db-integration
```

#### Database Test Breakdown

**Database Unit Tests (`make test-db-unit`)**
- **No external dependencies required** ✅
- **What's tested:** SQLAlchemy models, database initialization logic
- **Speed:** Very fast (< 5 seconds)
- **Use case:** Quick validation of database models and utilities

**Database Integration Tests (`make test-db-integration`)**
- **Requires database server** 🗄️
- **What's tested:** Full database operations, seeding, PostgreSQL-specific features
- **Speed:** Medium (20-45 seconds)
- **Use case:** Validate database operations and data integrity

### 3. API Integration Tests (`make test-api`)
**Requires web server + database** 🌐
- **What's tested:** HTTP endpoints, complete workflows, error handling, authentication
- **Setup required:** API server running on `http://0.0.0.0:8001`
- **Speed:** Slowest (2-5 minutes)
- **Use case:** End-to-end validation of API functionality

**Prerequisites:**
1. Database server running and initialized
2. API server running on port 8001
3. All dependencies installed

```bash
# Terminal 1: Start API server
make api-dev    # or make api-demo

# Terminal 2: Run integration tests
make test-api
```

## Test Configuration

### Environment Variables for Testing
| Variable | Description | Default | Required For |
|----------|-------------|---------|--------------|
| `API_BASE_URL` | API server URL for integration tests | `http://0.0.0.0:8001` | API tests |
| `DATABASE_URL` | Database connection for DB tests | From config/env | DB & API tests |
| `ENV_TARGET` | Environment target (e.g., `local-test`) | `local-dev` | API tests |

### Custom Test Configuration
```bash
# Test against different API URL
API_BASE_URL=http://localhost:9000 make test-api

# Test with specific environment
ENV_TARGET=local-demo make test-api

# Run specific test file
pytest test/api/unit/test_models.py -v

# Run tests with coverage
pytest test/api/unit/ --cov=genonaut.api --cov-report=html
```

## PostgreSQL Test Database Setup

### Overview

Genonaut uses PostgreSQL for all database tests. This ensures tests run against the same database engine as production, enabling testing of PostgreSQL-specific features like:
- **JSONB**: Binary JSON storage with rich query capabilities
- **Table Partitioning**: Testing partitioned tables (e.g., `content_items_all`)
- **Table Inheritance**: PostgreSQL-specific inheritance features
- **pg_trgm**: Trigram similarity for text search
- **Performance Characteristics**: Realistic query performance testing

### Quick Start

**1. Initialize Test Database (One-time setup):**
```bash
make init-test
```

This creates and seeds the `genonaut_test` database with test data.

**2. Run Tests:**
```bash
# Database tests (requires PostgreSQL)
make test-db

# API tests (requires PostgreSQL + API server)
make api-test           # Terminal 1: Start test API server
make test-api           # Terminal 2: Run API tests
```

### Available PostgreSQL Fixtures

All PostgreSQL test fixtures are defined in `test/db/postgres_fixtures.py` and automatically available to all tests:

**Session-scoped fixtures (created once per test session):**
- `postgres_engine` - SQLAlchemy engine for the test database

**Function-scoped fixtures (created fresh for each test):**
- `postgres_session` - Database session with automatic rollback after test
- `postgres_session_no_rollback` - Session without automatic rollback (use with caution)

**Backward-compatible aliases:**
- `db_session` - Alias for `postgres_session` (used in DB integration tests)
- `test_db_session` - Alias for `postgres_session` (used in API unit tests)

### Using PostgreSQL Fixtures in Tests

**Basic Usage:**
```python
def test_create_user(postgres_session):
    """Test user creation with automatic rollback."""
    user = User(username="testuser", email="test@example.com")
    postgres_session.add(user)
    postgres_session.commit()

    # Verify user was created
    found = postgres_session.query(User).filter_by(username="testuser").first()
    assert found is not None

    # After test completes, changes are automatically rolled back
```

**Testing JSONB Operations:**
```python
def test_jsonb_preferences(postgres_session):
    """Test PostgreSQL JSONB column operations."""
    user = User(
        username="jsonb_user",
        email="jsonb@example.com",
        preferences={"theme": "dark", "notifications": {"email": True}}
    )
    postgres_session.add(user)
    postgres_session.commit()

    # Query with JSONB path access
    result = postgres_session.query(User).filter_by(username="jsonb_user").first()
    assert result.preferences["theme"] == "dark"
    assert result.preferences["notifications"]["email"] is True
```

**Multiple Commits in One Test:**
```python
def test_multiple_operations(postgres_session):
    """Test supports multiple commits within a single test."""
    # First operation
    user1 = User(username="user1", email="user1@example.com")
    postgres_session.add(user1)
    postgres_session.commit()

    # Second operation
    user2 = User(username="user2", email="user2@example.com")
    postgres_session.add(user2)
    postgres_session.commit()

    # Both users exist in this test
    assert postgres_session.query(User).count() == 2

    # After test completes, both are rolled back
```

### How Test Isolation Works

PostgreSQL test fixtures use **nested transactions with automatic rollback** to ensure complete test isolation:

1. **Outer Transaction**: Wraps the entire test (automatically rolled back)
2. **Nested Savepoints**: Created for each `commit()` call within the test
3. **Automatic Rollback**: All changes discarded after test completes

**Implementation:**
```python
@pytest.fixture(scope="function")
def postgres_session(postgres_engine):
    """Function-scoped session with automatic rollback."""
    connection = postgres_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    session.begin_nested()

    # Recreate savepoint after each commit
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    # Cleanup: rollback all changes
    session.close()
    transaction.rollback()
    connection.close()
```

**Benefits:**
- Tests can freely call `session.commit()` without affecting other tests
- Each test starts with a clean database state
- No manual cleanup required
- Fast execution (no database recreation between tests)

### Environment Configuration

PostgreSQL test database connection is configured via environment variables:

**Required Variables (in `env/.env` or `env/.env.test`):**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME_TEST=genonaut_test
DB_USER_ADMIN=genonaut_admin
DB_PASSWORD_ADMIN=your_password_here
```

**How It Works:**
- Tests use `ENV_TARGET=local-test` environment
- Configuration loaded from `config/local-test.json`
- Database credentials read from environment variables
- Connection string: `postgresql://user:pass@host:port/genonaut_test`

### Troubleshooting

**Issue: "relation does not exist" errors**
- **Cause**: Test database not initialized
- **Solution**: Run `make init-test` to create and seed test database

**Issue: Tests fail with "database is being accessed by other users"**
- **Cause**: Test database connections not closed properly
- **Solution**:
  ```bash
  # Force disconnect all sessions
  make db-force-disconnect-test

  # Reinitialize
  make init-test
  ```

**Issue: Test data persists between tests**
- **Cause**: Using `postgres_session_no_rollback` fixture
- **Solution**: Use `postgres_session` for automatic rollback

**Issue: "SSL connection" or "password authentication failed"**
- **Cause**: Database credentials not configured
- **Solution**:
  1. Copy `env/env.example` to `env/.env`
  2. Update `DB_PASSWORD_ADMIN` with correct password
  3. Verify connection: `make db-connect-test`

**Issue: Tests are slow or hanging**
- **Cause**: Database connection pool exhaustion
- **Solution**:
  - Check for unclosed sessions in test code
  - Ensure all tests use fixtures (not manual engine creation)
  - Verify `make init-test` completed successfully

### PostgreSQL-Specific Test Features

**Test PostgreSQL Features:**
```python
from test.db.postgres_fixtures import verify_postgres_features

def test_postgres_capabilities(postgres_session):
    """Verify PostgreSQL features are available."""
    features = verify_postgres_features(postgres_session)

    assert features["jsonb"], "JSONB should be supported"
    assert features["inheritance"], "Table inheritance should be supported"
    assert features["partitioning"], "Partitioning should be available"
```

**Helper Functions:**
```python
from test.db.postgres_fixtures import table_exists, count_rows, get_table_columns

def test_database_helpers(postgres_session):
    """Test database inspection helpers."""
    # Check if table exists
    assert table_exists(postgres_session, "users")

    # Get row count
    user_count = count_rows(postgres_session, "users")
    assert user_count >= 0

    # Inspect table columns
    columns = get_table_columns(postgres_session, "users")
    assert "id" in columns
    assert "username" in columns
```

## Test Organization

```
test/
├── api/                           # API-specific tests
│   ├── unit/                      # Unit tests (no dependencies)
│   │   ├── test_models.py         # Pydantic model validation
│   │   ├── test_config.py         # Configuration testing
│   │   ├── test_pagination_models.py      # Pagination model tests
│   │   ├── test_base_repository_pagination.py  # Repository pagination tests
│   │   └── test_exceptions.py     # Exception handling
│   ├── db/                        # API database tests (DB required)
│   │   ├── test_repositories.py   # Repository CRUD operations
│   │   └── test_services.py       # Business logic services
│   ├── integration/               # API tests (web server required)
│   │   ├── test_api_endpoints.py  # Individual endpoint tests
│   │   ├── test_content_endpoints_pagination.py  # Content pagination tests
│   │   ├── test_cursor_pagination.py  # Cursor-based pagination tests
│   │   └── test_workflows.py      # Complete workflow tests
│   └── stress/                    # Performance and stress tests
│       ├── test_pagination_stress.py      # Comprehensive pagination stress tests
│       ├── benchmark_pagination.py       # Standalone benchmarking tool
│       ├── run_stress_tests.py           # Test runner with presets
│       └── conftest.py           # Stress test fixtures and configuration
└── db/                            # Database-specific tests
    ├── unit/                      # Database unit tests (no dependencies)
    │   ├── test_schema.py         # SQLAlchemy model tests
    │   └── test_database_initializer.py  # DB initialization logic
    ├── integration/               # Database integration tests (DB required)
    │   ├── test_database_integration.py     # Full DB operations
    │   ├── test_database_seeding.py        # Data seeding tests
    │   ├── test_database_end_to_end.py     # End-to-end DB workflows
    │   ├── test_pagination_performance.py  # Database pagination performance tests
    │   └── test_database_postgres_integration.py  # PostgreSQL-specific tests
    ├── utils.py                   # Database test utilities
    └── input/                     # Test data files
        └── rdbms_init/           # TSV files for seeding
```

## Development Workflow

### 🔄 During Feature Development
1. **Write unit tests first** for new models/utilities
2. **Write database tests** for new repositories/services
3. **Write API tests** for new endpoints
4. **Run appropriate test tier** after each change

```bash
# Quick feedback loop during development
make test-unit

# Validate data changes
make test-db

# Full integration validation
make test-api
```

### ✅ Before Committing Code
```bash
# Run all tests to ensure nothing is broken
make test-all
```

### 🚀 Continuous Integration
```bash
# CI pipeline should run all test tiers
make test-unit    # Fast feedback
make test-db      # Data validation
make test-api     # Integration validation
```

## Troubleshooting Tests

### Common Issues and Solutions

**Unit Tests Failing:**
```bash
# Check for import errors or missing dependencies
pip install -r requirements.txt
make test-unit
```

**Database Tests Failing:**
```bash
# Verify database connection
make show-db-url

# Reinitialize database
make init-dev
make test-db
```

**API Tests Failing:**
```bash
# Check if API server is running
curl http://0.0.0.0:8001/api/v1/health

# Start API server if not running
make api-dev

# Run tests with custom URL if needed
API_BASE_URL=http://localhost:8001 make test-api
```

**Test Database Cleanup:**
```bash
# Clear excess test schemas
make clear-excess-test-schemas

# Full database reset
make init-dev
```

## Testing Best Practices

### ✅ Do's
- Write tests during development, not after
- Use appropriate test tier for the component being tested
- Run `make test-unit` frequently during development
- Run `make test-all` before committing
- Use descriptive test names and clear assertions
- Mock external dependencies in unit tests

### ❌ Don'ts
- Don't run API tests without starting the server
- Don't ignore test failures - investigate and fix
- Don't mix test types (unit tests shouldn't access database)
- Don't commit code with failing tests
- Don't skip testing edge cases and error conditions

## Performance Expectations

| Test Suite | Expected Duration | Parallelizable |
|------------|------------------|----------------|
| Unit Tests | < 10 seconds | ✅ Yes |
| Database Tests | 30-60 seconds | ⚠️ Limited |
| API Integration | 2-5 minutes | ❌ No |
| All Tests | 3-6 minutes | ⚠️ Sequential |

## Stress and Performance Testing

### Overview

Genonaut includes comprehensive stress testing capabilities to validate performance at scale and ensure the system can handle production workloads efficiently.

### Stress Test Suite

The stress testing infrastructure is located in `test/api/stress/` and includes:

| Component | Purpose | Features |
|-----------|---------|----------|
| **`test_pagination_stress.py`** | Core stress test suite | Large dataset simulation, concurrent testing, memory monitoring |
| **`benchmark_pagination.py`** | Standalone benchmarking tool | Performance metrics, response time analysis, throughput testing |
| **`run_stress_tests.py`** | Test runner with presets | Development, CI, and production test configurations |

### Running Stress Tests

#### Quick Development Tests
```bash
# Run with small dataset for quick validation (1K records)
python test/api/stress/run_stress_tests.py --config development

# Run specific stress test with small dataset
STRESS_TEST_DATASET_SIZE=1000 python -m pytest test/api/stress/test_pagination_stress.py::TestPaginationStress::test_pagination_with_large_dataset -v
```

#### CI/Production Tests
```bash
# CI pipeline configuration (10K records)
python test/api/stress/run_stress_tests.py --config ci

# Full production stress tests (100K records)
python test/api/stress/run_stress_tests.py --config production

# Custom configuration with specific parameters
python test/api/stress/run_stress_tests.py --config custom --dataset-size 50000 --concurrent-requests 10
```

#### Standalone Benchmarking
```bash
# Run performance benchmarks against API server
python test/api/stress/benchmark_pagination.py --base-url http://localhost:8001 --dataset-size 10000

# Save benchmark results to file
python test/api/stress/benchmark_pagination.py --output benchmark_results.json
```

### Stress Test Types

#### 1. Large Dataset Simulation
Tests pagination performance with datasets up to 100K records:
- **Database Operations**: Batch creation/deletion of large datasets
- **Query Performance**: Sub-200ms response times across all page depths
- **Memory Stability**: Validates memory usage remains under 300MB

#### 2. Deep Pagination Testing
Validates consistent performance across page depths:
- **Offset Pagination**: Performance degradation analysis
- **Cursor Pagination**: Consistent response times regardless of page position
- **Performance Degradation**: Ensures <3x performance degradation from first to deep pages

#### 3. Concurrent Request Handling
Tests system behavior under concurrent load:
- **Simultaneous Requests**: Up to 10 concurrent pagination requests
- **Success Rate**: Validates >90% success rate under load
- **Response Time Distribution**: Analyzes P95/P99 performance characteristics

#### 4. Memory Leak Detection
Extended testing to identify memory leaks:
- **Extended Pagination**: Tests 50+ consecutive page requests
- **Memory Growth Monitoring**: Tracks memory usage over time
- **Leak Detection**: Flags potential memory leaks (>50MB growth)

#### 5. Cursor Pagination Validation
Specialized testing for high-performance cursor pagination:
- **Cursor Stability**: Ensures cursors remain valid during concurrent data changes
- **Bidirectional Navigation**: Tests forward/backward navigation consistency
- **Performance Consistency**: Validates <20% variance in response times

### Performance Targets

#### Response Time Targets
| Scenario | Target | Actual Performance |
|----------|--------|-------------------|
| Single page query | < 200ms | ~50ms average |
| Deep pagination (page 100+) | < 400ms | ~60ms average |
| Concurrent requests (10x) | < 500ms average | ~200ms average |
| Cursor pagination | < 200ms (any page) | ~45ms consistent |

#### System Resource Targets
| Resource | Target | Monitoring |
|----------|--------|------------|
| Memory usage per worker | < 300MB | Stress tests monitor and validate |
| Database connections | < 20 active | Connection pool optimization |
| Query performance | < 100ms for optimized queries | Index effectiveness monitoring |

#### Throughput Targets
| Metric | Target | Validation Method |
|--------|--------|------------------|
| Concurrent pagination requests | 1000+ req/s | Load testing with multiple workers |
| Database query throughput | 500+ queries/s | Database performance monitoring |
| Cache hit rate (frontend) | > 80% | Frontend pagination cache metrics |

### Stress Test Configuration

#### Environment Variables
```bash
# Control dataset size for tests
STRESS_TEST_DATASET_SIZE=1000    # Number of records to create

# Concurrent request configuration
STRESS_TEST_CONCURRENT_REQUESTS=5  # Number of simultaneous requests

# Performance thresholds
STRESS_TEST_MAX_RESPONSE_TIME=200  # Maximum acceptable response time (ms)
STRESS_TEST_MAX_MEMORY_MB=300      # Maximum memory usage per worker
```

#### Test Presets

**Development Preset**:
- 1K records, 3 concurrent requests, 5 max pages
- Fast execution for development workflow
- Basic functionality validation

**CI Preset**:
- 10K records, 5 concurrent requests, 10 max pages
- Balanced execution time vs. coverage
- Suitable for continuous integration

**Production Preset**:
- 100K records, 10 concurrent requests, 50 max pages
- Comprehensive stress testing
- Full production readiness validation

### Monitoring and Analysis

#### Real-time Monitoring
```bash
# Monitor stress test execution with verbose output
python test/api/stress/run_stress_tests.py --config production -v

# Watch database performance during stress tests
python test/api/stress/benchmark_pagination.py --base-url http://localhost:8001 --dataset-size 50000
```

#### Performance Analysis
The stress test suite provides detailed performance analytics:
- **Response Time Distribution**: P50, P95, P99 metrics
- **Memory Usage Patterns**: Peak usage, growth trends, stability analysis
- **Error Rate Analysis**: Success rates, error categorization
- **Database Performance**: Query execution times, index effectiveness

#### Continuous Performance Monitoring
```bash
# Set up automated performance regression detection
python test/api/stress/benchmark_pagination.py --output baseline.json

# Compare against baseline in CI
python test/api/stress/benchmark_pagination.py --baseline baseline.json --fail-on-regression
```

## E2E Test Database Configuration

### Which Database Do E2E Tests Use?

**CRITICAL**: E2E tests use whichever API server is currently running on port 8001. The database behind that API server determines what data the tests see.

| API Server Command | Database Used | Environment | Typical Use Case |
|-------------------|---------------|-------------|------------------|
| `make api-demo` | `genonaut_demo` | `local-demo` | Local development, manual testing |
| `make api-dev` | `genonaut` | `local-dev` | Alternative development database |
| `make api-test` | `genonaut_test` | `local-test` | Automated E2E testing |

### How to Check Which Database is Running

**Method 1: Check the health endpoint (recommended)**
```bash
curl http://localhost:8001/api/v1/health | python -m json.tool
```

Response will show database name:
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "name": "genonaut_demo"  // <-- This tells you which database
  },
  "timestamp": "2025-10-25T23:30:00.000000"
}
```

**Method 2: Check running process**
```bash
ps aux | grep "run-api" | grep -v grep
```

Look for `--env-target` flag:
- `--env-target local-demo` -> `genonaut_demo` database
- `--env-target local-test` -> `genonaut_test` database
- `--env-target local-dev` -> `genonaut` database

### Running E2E Tests Against Different Databases

**Against Test Database (isolated, recommended for CI):**
```bash
# Terminal 1: Start test API
make api-test              # Uses genonaut_test database

# Terminal 2: Run E2E tests
cd frontend
npm run test:e2e
```

**Against Demo Database (development, manual testing):**
```bash
# Terminal 1: Start demo API (if not already running)
make api-demo              # Uses genonaut_demo database

# Terminal 2: Run E2E tests
cd frontend
npm run test:e2e           # Tests run against whatever is on port 8001
```

### Common Pitfalls

**Pitfall 1: "Test database missing data" but database has data**
- **Cause**: API server connected to wrong database (e.g., `genonaut_demo` instead of `genonaut_test`)
- **Solution**:
  1. Check health endpoint: `curl http://localhost:8001/api/v1/health`
  2. Kill wrong API server: `pkill -f "run-api"`
  3. Start correct API server: `make api-test`
  4. Verify: `curl http://localhost:8001/api/v1/health | grep name`

**Pitfall 2: E2E tests pass locally but fail in CI**
- **Cause**: Local tests running against `demo` database with different data than `test` database
- **Solution**: Always run E2E tests against `test` database before pushing:
  ```bash
  make api-test              # Ensure test API is running
  make frontend-test-e2e     # Run against test database
  ```

**Pitfall 3: E2E test data persists between runs**
- **Cause**: Using `demo` database which persists data
- **Solution**: Use `test` database which gets reset:
  ```bash
  make init-test             # Reset test database
  make api-test              # Start test API
  make frontend-test-e2e     # Run tests
  ```

**Pitfall 4: No `VITE_API_BASE_URL` passed**
`VITE_API_BASE_URL` defaults to http://127.0.0.1:8001 if not passed. 
Note that if you run `frontend-test-e2e-wt2`, it will use a localhost with port 8002 specifically designed to run off 
the test database.

### Best Practices

1. **For Development**: Use `demo` database (`make api-demo`) for manual testing
2. **For E2E Testing**: Use `test` database (`make api-test`) for automated tests
3. **Always Verify**: Check health endpoint before running E2E tests
4. **In CI/CD**: Always use `test` database with `make api-test`
5. **Before Debugging**: Verify which database is connected first

## Frontend Testing

Genonaut's React frontend has a comprehensive testing setup covering unit tests and end-to-end testing.

### Frontend Test Types

| Test Type | Framework | Purpose | Speed |
|-----------|-----------|---------|-------|
| **Unit/Integration** | Vitest + Testing Library | React components, hooks, services | ⚡ Fast |
| **End-to-End** | Playwright | Full user workflows | 🔄 Medium |

### Frontend Test Commands

```bash
# Unit tests only (fastest)
npm run test-unit          # Run unit tests only
make frontend-test-unit    # Same via Makefile

# All frontend tests (unit + e2e)
npm run test               # Run both unit and e2e tests
make frontend-test         # Same via Makefile

# E2E tests (excludes performance tests by default)
npm run test:e2e           # Run Playwright tests (excludes @performance)
make frontend-test-e2e     # Same via Makefile

# E2E Performance tests only
npm run test:e2e:performance              # Run performance tests only
make frontend-test-e2e-performance        # Same via Makefile
npm run test:e2e:performance:headed       # Performance tests with browser UI
make frontend-test-e2e-performance-headed # Same via Makefile
npm run test:e2e:performance:ui           # Performance tests in Playwright UI
make frontend-test-e2e-performance-ui     # Same via Makefile

# E2E tests with debug logging
npm run test:e2e:debug              # Run with verbose console/network logging
make frontend-test-e2e-debug        # Same via Makefile
npm run test:e2e:debug:headed       # Debug mode with browser UI
make frontend-test-e2e-debug-headed # Same via Makefile

# E2E performance tests with debug logging
npm run test:e2e:performance:debug              # Performance tests with debug logging
make frontend-test-e2e-performance-debug        # Same via Makefile
npm run test:e2e:performance:debug:headed       # Performance tests with debug + browser UI
make frontend-test-e2e-performance-debug-headed # Same via Makefile

# Additional test options
npm run test:watch         # Unit tests in watch mode
npm run test:coverage      # Unit tests with coverage
npm run test:e2e:headed    # E2E tests with browser UI
npm run test:e2e:ui        # Playwright UI mode
```

#### Frontend E2E Test Categories

Frontend E2E tests are split into two categories:

**1. Standard E2E Tests (Functional/Sanity)**
- Run with: `make frontend-test-e2e` or `npm run test:e2e`
- Focus on verifying correct functionality without time constraints
- Test user workflows, UI behavior, data integrity, navigation, etc.
- Faster execution (no performance measurement overhead)
- Excludes tests tagged with `@performance`

**2. Performance E2E Tests**
- Run with: `make frontend-test-e2e-performance` or `npm run test:e2e:performance`
- Focus on measuring performance with explicit time thresholds
- Test page load times, render times, interaction responsiveness, memory usage, etc.
- Includes only tests tagged with `@performance`
- Examples:
  - `performance.spec.ts` - All tests (page load, rendering, scrolling, memory, bundle size)
  - `search-filtering-real-api.spec.ts` - One test: "filter performance with large datasets @performance"

**Why the separation?**
- Performance tests are slower and can be flaky in CI/CD environments
- Standard tests run faster for quick feedback during development
- Performance tests can be run separately on dedicated hardware or as part of nightly builds
- Allows focusing on functional correctness vs. performance characteristics

### Debug Logging in E2E Tests

By default, E2E tests run with minimal console output to keep logs clean. To enable verbose logging for debugging:

**Debug Mode Features:**
- Console error stack traces (loading-errors.spec.ts)
- Network request/response logging (tag-hierarchy-debug.spec.ts)
- Page navigation details
- Element detection results

**Enable Debug Logging:**
```bash
# Via npm scripts
npm run test:e2e:debug              # Debug mode
npm run test:e2e:debug:headed       # Debug mode with browser UI

# Via Makefile
make frontend-test-e2e-debug        # Debug mode
make frontend-test-e2e-debug-headed # Debug mode with browser UI

# With real API
npm run test:e2e:real-api:debug              # Debug with real API
npm run test:e2e:real-api:debug:headed       # Debug with real API + browser UI
make frontend-test-e2e-real-api-debug        # Via Makefile
make frontend-test-e2e-real-api-debug-headed # Via Makefile

# Directly via environment variable
DEBUG_E2E=true npm run test:e2e
```

**What Gets Logged in Debug Mode:**
- `loading-errors.spec.ts`: Full console error stack traces
- `tag-hierarchy-debug.spec.ts`: REQUEST/RESPONSE for all network calls, page navigation, element detection

**Production Mode (default):**
- Minimal output for clean CI/CD logs
- Only test pass/fail results
- Error summaries without verbose details

### Frontend Unit Test Best Practices (Vitest + Testing Library)

When writing React component tests with Vitest and Testing Library, certain patterns help avoid test state pollution and timing issues.

**✅ Recommended Patterns:**

1. **Always use `userEvent.setup()` for test isolation**
   - **Why**: Global `userEvent` from `@testing-library/user-event` shares state between tests
   - **Issue**: Typed characters or interactions from one test can bleed into subsequent tests
   - **Solution**: Create a fresh userEvent instance per test with `userEvent.setup()`

   ```typescript
   // AVOID - Global userEvent causes state pollution
   import userEvent from '@testing-library/user-event'

   it('test 1', async () => {
     await userEvent.type(input, 'test')  // State persists!
   })

   it('test 2', async () => {
     await userEvent.type(input, 'other')  // May have leftover state from test 1
   })

   // PREFER - Isolated userEvent instance per test
   it('test 1', async () => {
     const user = userEvent.setup()
     await user.type(input, 'test')  // Fresh instance
   })

   it('test 2', async () => {
     const user = userEvent.setup()  // New instance, no pollution
     await user.type(input, 'other')
   })
   ```

2. **Use `fireEvent.change()` for long text inputs**
   - **Why**: `userEvent.type()` simulates typing character-by-character (realistic but slow)
   - **Issue**: Typing 500+ characters causes test timeouts and performance issues
   - **Solution**: Use `fireEvent.change()` for bulk text input when realism isn't needed

   ```typescript
   // AVOID - Typing 501 characters one by one is very slow
   await userEvent.type(descriptionInput, 'A'.repeat(501))  // 5+ seconds, may timeout

   // PREFER - Direct value change for long text
   fireEvent.change(descriptionInput, { target: { value: 'A'.repeat(501) } })  // <10ms
   ```

3. **Split complex multi-step tests into smaller, focused tests**
   - **Why**: Tests with multiple user interactions and assertions accumulate state and are brittle
   - **Issue**: Complex tests fail unpredictably due to timing, state pollution, or MUI Portal issues
   - **Solution**: Each test should: render once, perform ONE action, assert ONE thing

   ```typescript
   // AVOID - Complex multi-step test with many assertions
   it('should validate and submit form with trimmed data', async () => {
     render(...)
     await userEvent.type(nameInput, '  Test  ')
     await userEvent.type(descInput, 'A'.repeat(501))
     fireEvent.click(submitButton)
     await waitFor(() => {
       expect(screen.getByText('Description too long')).toBeInTheDocument()
     })
     await userEvent.clear(descInput)
     await userEvent.type(descInput, 'Valid')
     fireEvent.click(submitButton)
     await waitFor(() => {
       expect(onSubmit).toHaveBeenCalledWith({ name: 'Test', description: 'Valid' })
     })
   })

   // PREFER - Split into focused, single-purpose tests
   it('should accept whitespace in name input', async () => {
     const user = userEvent.setup()
     render(...)
     await user.type(nameInput, '  Test  ')
     expect(nameInput.value).toBe('  Test  ')
   })

   it('should show validation error for long description', async () => {
     const user = userEvent.setup()
     render(...)
     fireEvent.change(descInput, { target: { value: 'A'.repeat(501) } })
     fireEvent.click(submitButton)
     expect(await screen.findByText('Description too long')).toBeInTheDocument()
   })

   it('should trim name when submitting form', async () => {
     const user = userEvent.setup()
     render(...)
     await user.type(nameInput, '  Test  ')
     fireEvent.click(submitButton)
     await waitFor(() => {
       expect(onSubmit).toHaveBeenCalledWith({ name: 'Test', ... })
     })
   })
   ```

4. **Create fresh QueryClient instance per test**
   - **Why**: React Query caches data that can persist between tests
   - **Solution**: Use `beforeEach` to create new QueryClient, `afterEach` to clear it

   ```typescript
   let queryClient: QueryClient

   beforeEach(() => {
     queryClient = new QueryClient({
       defaultOptions: {
         queries: { retry: false },
         mutations: { retry: false },
       },
     })
   })

   afterEach(() => {
     cleanup()
     queryClient.clear()
   })
   ```

**Common Pitfalls:**

- **userEvent state pollution**: Tests pass individually but fail when run together
  - **Symptom**: Input fields contain unexpected characters from previous tests
  - **Fix**: Use `userEvent.setup()` for every test

- **Long text timeouts**: Tests timeout when typing many characters
  - **Symptom**: Test exceeds 5000ms timeout during `userEvent.type()`
  - **Fix**: Use `fireEvent.change()` for text longer than ~50 characters

- **Complex test failures**: Multi-step tests fail with cryptic errors
  - **Symptom**: "Element not found", "Timeout", or assertion failures deep in test
  - **Fix**: Break into smaller tests, each testing one behavior

**When These Patterns Were Discovered:**

These patterns emerged from fixing CategoryFormModal tests where:
- 4 tests passed individually but failed when run together (userEvent pollution)
- Tests timed out typing 501 'A' characters (performance issue)
- Complex form validation + submission tests were brittle (too many steps)

After refactoring with these patterns, all tests passed reliably.

### E2E Test Patterns to Avoid

Some test patterns have proven problematic in automated Playwright environments despite working correctly in manual testing. These patterns should be avoided in favor of alternative testing approaches.

**⚠️ Problematic Patterns:**

1. **Cursor-Based Pagination Navigation Tests**
   - **Issue**: Tests that click pagination buttons to navigate between pages fail with cursor-based pagination
   - **Why**: Playwright test helpers expect traditional page numbers, but cursor pagination uses URL parameters that update asynchronously
   - **Alternative**: Test pagination via API calls, or use direct URL navigation instead of button clicks

2. **Material UI Component Click Navigation**
   - **Issue**: Tests that click Material UI Chips, Buttons with complex interactions fail to trigger navigation
   - **Why**: MUI components' internal event handling may not propagate synthetic click events correctly in test environments
   - **Alternative**: Test navigation logic at unit test level with mocked routers, or use `force: true` option

3. **Tests Depending on `networkidle`**
   - **Issue**: Waiting for `networkidle` state doesn't guarantee React Query or other state management has finished updating
   - **Why**: Modern frontend frameworks batch requests and use background data fetching
   - **Alternative**: Wait for specific data-testid elements or UI state changes instead

4. **Navigation-Heavy E2E Tests**
   - **Issue**: Tests that rely on clicking through multiple navigation steps are brittle and environment-sensitive
   - **Why**: Each navigation point introduces timing, state management, and framework initialization dependencies
   - **Alternative**: Test navigation at unit level, test end states via direct URLs at E2E level

**✅ Recommended Alternatives:**

Instead of testing navigation interactions at E2E level:
- **Unit tests**: Test onClick handlers and navigation logic with mocked routers
- **API tests**: Verify pagination, filtering, and data operations via direct API calls
- **Component tests**: Test complex UI interactions in isolation with Testing Library
- **Direct URL tests**: Navigate directly to URLs instead of clicking through UI

### Handling React Query Timing Issues

For components with complex React Query dependencies that cause E2E test timing failures, use explicit loading indicators with data-testid attributes.

**Problem:**
Components that use React Query with multiple cascading hooks may not be ready for interaction even after `networkidle` or standard timeouts. This causes test failures with "element not found" or "timeout" errors.

**Solution:**
Add explicit loading state indicators to components and wait for them in tests.

**Pattern:**

```typescript
// Component: Add loading state indicators
function AnalyticsCard() {
  const { data, isLoading } = useQuery(...)

  if (isLoading) {
    return <div data-testid="analytics-loading">Loading...</div>
  }

  return (
    <div data-testid="analytics-loaded">
      {/* Your content */}
    </div>
  )
}

// Test Helper: Wait for data to load
async function waitForAnalyticsDataLoaded(page, section: 'route' | 'generation') {
  await page.waitForSelector(`[data-testid="${section}-analytics-loaded"]`, {
    timeout: 30000
  })
}

// Test: Use the helper before interactions
test('changes filter', async ({ page }) => {
  await page.goto('/analytics')
  await waitForAnalyticsDataLoaded(page, 'route')

  // Now safe to interact with filters
  await page.click('[data-testid="filter-select"]')
})
```

**When to use this pattern:**
- Components with multiple cascading React Query hooks
- Analytics/dashboard pages with slow aggregation queries
- Pages where `networkidle` doesn't guarantee data is ready
- Tests failing with "element not found" despite long timeouts

**When NOT to use:**
- Simple pages with single query
- Tests that already pass reliably
- Global application - only add to problematic components

**Example:**
Analytics E2E tests (`frontend/tests/e2e/analytics-real-api.spec.ts`) use this pattern successfully. The file contains both the old skipped tests (showing the problematic pattern) and new passing tests (using loading indicators) for educational comparison.

**Implementation:**
- See `frontend/tests/e2e/utils/realApiHelpers.ts` for the `waitForAnalyticsDataLoaded` helper
- See `frontend/src/components/analytics/RouteAnalyticsCard.tsx` and `GenerationAnalyticsCard.tsx` for component implementations
- 6 new tests created with pattern, all passing reliably

**📚 Detailed Documentation:**

For comprehensive analysis of problematic test patterns, including:
- Detailed failure symptoms and root cause analysis
- Investigation summaries with attempted fixes
- Alternative testing approaches with code examples
- Recommendations for future test development

See: [`notes/issues/groupings/tests/tests-skipped-troublesome-patterns.md`](../notes/issues/groupings/tests/tests-skipped-troublesome-patterns.md)

**Examples of Skipped Tests:**
- Gallery pagination navigation (cursor-based pagination + Playwright incompatibility)
- Image view tag chip navigation (Material UI Chip + React Router timing issues)

Both features are verified working through manual testing and code review, but the E2E test patterns proved too brittle for automated testing.

### Frontend Test Structure

```
frontend/
├── src/
│   ├── components/__tests__/      # Component unit tests
│   ├── hooks/__tests__/           # React hooks unit tests
│   ├── pages/__tests__/           # Page component tests
│   ├── services/__tests__/        # API service tests
│   └── app/__tests__/             # App shell and provider tests
└── tests/
    └── e2e/                       # Playwright end-to-end tests
        ├── auth.spec.ts           # Authentication flows
        ├── content.spec.ts        # Content management
        ├── dashboard.spec.ts      # Dashboard functionality
        ├── recommendations.spec.ts # Recommendation features
        └── settings.spec.ts       # Settings and profile
```

### Frontend Testing Setup

**Prerequisites for unit tests:**
- Node.js and npm dependencies installed
- No additional setup required

**Prerequisites for e2e tests:**
- Backend API server running (for full integration)
- Playwright browsers installed: `npx playwright install`

```bash
# Install frontend dependencies
cd frontend && npm install

# Install Playwright browsers (if not already done)
npx playwright install

# Run frontend tests
npm run test                    # All tests
npm run test-unit              # Unit tests only
npm run test:e2e               # E2E tests only
```

### Frontend Test Configuration

**Vitest Configuration (`vite.config.ts`):**
- Uses jsdom environment for DOM simulation
- Includes only `src/**/*.{test,spec}.{ts,tsx}` files
- Excludes e2e tests to prevent framework conflicts
- Coverage reporting with V8 provider

**Playwright Configuration:**
- Tests run against built frontend with mock API
- Supports headed/headless modes
- Configurable base URL for different environments

### Frontend Development Workflow

```bash
# During development
npm run test:watch            # Auto-run unit tests on changes
npm run test-unit            # Quick unit test validation

# Before committing
npm run test                 # Run all frontend tests
npm run lint                 # Code quality checks
npm run type-check          # TypeScript validation

# For debugging
npm run test:e2e:headed     # Run e2e tests with browser UI
npm run test:e2e:ui         # Use Playwright's debug UI
```

## Coverage Targets

**Backend:**
- **Unit Tests:** > 95% for models, utilities, exceptions
- **Database Tests:** > 90% for repositories and services
- **API Integration:** > 85% for endpoints and workflows

**Frontend:**
- **Unit Tests:** > 90% for components, hooks, services
- **E2E Tests:** Cover critical user journeys and workflows

**Overall:** > 85% combined coverage across frontend and backend
---

## ComfyUI Mock Server

### Overview

For testing image generation workflows without requiring a real ComfyUI instance, Genonaut includes a mock ComfyUI server that simulates the ComfyUI API.

**Location:** `test/_infra/mock_services/comfyui/`

**Purpose:**
- Test generation workflows in isolation
- Avoid dependency on external ComfyUI installation
- Enable fast, deterministic tests
- Simulate edge cases and error conditions

### Architecture

The mock server is a FastAPI application that mimics ComfyUI's REST API:

```
test/_infra/mock_services/comfyui/
├── server.py           # Mock ComfyUI server implementation
├── conftest.py         # Pytest fixtures for server lifecycle
├── input/              # Test images (used as mock generation output)
│   └── kernie_512x768.jpg
└── output/             # Generated "mock" images (copied from input/)
```

**How It Works:**
1. When a job is submitted via `POST /prompt`, the server generates a unique `prompt_id`
2. The server copies `input/kernie_512x768.jpg` to `output/` with a unique filename
3. When polled via `GET /history/{prompt_id}`, returns completion status with output file info
4. File naming follows ComfyUI pattern: `{prefix}_{counter}_.png`

### Running Tests with Mock Server

**Basic Usage:**

```python
def test_my_feature(mock_comfyui_config: dict):
    """Test uses mock ComfyUI server automatically."""
    # Settings are already configured to use mock server
    # - comfyui_url: http://localhost:8189
    # - comfyui_output_dir: test/_infra/mock_services/comfyui/output/
    
    # Your test code here
    job = generation_service.create_generation_job(...)
    process_comfy_job(db_session, job.id)
    # Job will use mock server
```

**Available Fixtures:**

- `mock_comfyui_server` (session-scoped): Starts/stops mock server
- `mock_comfyui_url` (function-scoped): Returns server URL, resets state
- `mock_comfyui_client` (function-scoped): ComfyUIClient configured for mock
- `mock_comfyui_config` (function-scoped): Full configuration (URL + output_dir)

### Environment Variables

Add these to your `.env` file for mock server configuration:

```bash
# ComfyUI Mock Server (for testing)
COMFYUI_MOCK_URL=http://localhost:8189
COMFYUI_MOCK_PORT=8189
```

These are already configured in `env/.env` and `env/env.example`.

### Test Layers

The mock server supports three layers of testing:

1. **Layer 1: Unit Tests (No Server)**
   - Use `unittest.mock` to patch ComfyUIClient
   - Fastest, no network calls
   - Example: `test/api/integration/test_error_scenarios.py`

2. **Layer 2: Mock Server (No Celery/Redis)**
   - Use mock HTTP server for realistic API testing
   - Tests ComfyUIClient integration
   - Example: `test/integrations/comfyui/test_comfyui_mock_server_client.py`

3. **Layer 3: End-to-End (Mock Server + Celery Simulation)**
   - Full workflow testing with `process_comfy_job()`
   - Tests complete generation pipeline
   - Example: `test/integrations/comfyui/test_comfyui_mock_server_e2e.py`

### Mock Server API Endpoints

The mock server implements these ComfyUI-compatible endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/system_stats` | GET | Health check |
| `/prompt` | POST | Submit workflow, returns `prompt_id` |
| `/history/{prompt_id}` | GET | Get workflow status and outputs |
| `/queue` | GET | Get queue status |
| `/object_info` | GET | Get available models |
| `/interrupt` | POST | Cancel workflow |

### Running Mock Server Tests

```bash
# Run all mock server tests
pytest test/integrations/comfyui/

# Run specific test layer
pytest test/integrations/comfyui/test_comfyui_mock_server_basic.py      # Layer 2: Basic
pytest test/integrations/comfyui/test_comfyui_mock_server_client.py     # Layer 2: Client
pytest test/integrations/comfyui/test_comfyui_mock_server_files.py      # Layer 2: Files
pytest test/integrations/comfyui/test_comfyui_mock_server_errors.py     # Layer 2: Errors
pytest test/integrations/comfyui/test_comfyui_mock_server_e2e.py        # Layer 3: E2E
```

### Troubleshooting

**Issue: Mock server fails to start**
- **Cause:** Port 8189 already in use
- **Solution:** Kill existing process: `lsof -ti:8189 | xargs kill -9`

**Issue: Tests can't find output files**
- **Cause:** `comfyui_output_dir` not set correctly
- **Solution:** Use `mock_comfyui_config` fixture instead of manual configuration

**Issue: Server state persists between tests**
- **Cause:** Using session-scoped fixture without reset
- **Solution:** Use `mock_comfyui_url` fixture which auto-resets state

**Issue: Tests fail with "prompt_id not found"**
- **Cause:** Job was submitted but not processed
- **Solution:** Call `process_comfy_job()` or ensure mock server had time to process

**Issue: Output files have wrong names**
- **Cause:** Filename prefix not set in workflow
- **Solution:** Set `filename_prefix` in SaveImage node of workflow

### Adding New Mock Endpoints

To extend the mock server with new endpoints:

1. Add endpoint to `test/_infra/mock_services/comfyui/server.py`:

```python
@app.get("/new_endpoint")
async def new_endpoint():
    return {"status": "ok"}
```

2. Update `MockComfyUIServer` class if state management needed

3. Add corresponding test in `test/integrations/comfyui/`

### Performance

- **Mock server startup:** ~100ms
- **Job submission:** <10ms
- **File generation:** <50ms (simple copy)
- **Full E2E test:** ~200-500ms

Much faster than real ComfyUI (which takes 5-30 seconds per generation).
