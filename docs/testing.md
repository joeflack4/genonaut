# Testing Documentation

Genonaut uses a comprehensive three-tier testing approach to ensure code quality and reliability across all components.

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
