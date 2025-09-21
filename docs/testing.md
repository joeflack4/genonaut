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
- **Setup required:** API server running on `http://0.0.0.0:8000`
- **Speed:** Slowest (2-5 minutes)
- **Use case:** End-to-end validation of API functionality

**Prerequisites:**
1. Database server running and initialized
2. API server running on port 8000
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
| `API_BASE_URL` | API server URL for integration tests | `http://0.0.0.0:8000` | API tests |
| `DATABASE_URL` | Database connection for DB tests | From `.env` | DB & API tests |
| `API_ENVIRONMENT` | Database environment (`dev`/`demo`) | `dev` | API tests |

### Custom Test Configuration
```bash
# Test against different API URL
API_BASE_URL=http://localhost:9000 make test-api

# Test with specific environment
API_ENVIRONMENT=demo make test-api

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
│   │   └── test_exceptions.py     # Exception handling
│   ├── db/                        # API database tests (DB required)
│   │   ├── test_repositories.py   # Repository CRUD operations
│   │   └── test_services.py       # Business logic services
│   └── integration/               # API tests (web server required)
│       ├── test_api_endpoints.py  # Individual endpoint tests
│       └── test_workflows.py      # Complete workflow tests
└── db/                            # Database-specific tests
    ├── unit/                      # Database unit tests (no dependencies)
    │   ├── test_schema.py         # SQLAlchemy model tests
    │   └── test_database_initializer.py  # DB initialization logic
    ├── integration/               # Database integration tests (DB required)
    │   ├── test_database_integration.py     # Full DB operations
    │   ├── test_database_seeding.py        # Data seeding tests
    │   ├── test_database_end_to_end.py     # End-to-end DB workflows
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
curl http://0.0.0.0:8000/api/v1/health

# Start API server if not running
make api-dev

# Run tests with custom URL if needed
API_BASE_URL=http://localhost:8000 make test-api
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

# E2E tests only
npm run test:e2e           # Run Playwright tests
make frontend-test-e2e     # Same via Makefile

# Additional test options
npm run test:watch         # Unit tests in watch mode
npm run test:coverage      # Unit tests with coverage
npm run test:e2e:headed    # E2E tests with browser UI
npm run test:e2e:ui        # Playwright UI mode
```

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