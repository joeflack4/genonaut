# Database Initialization Tests - Status and Troubleshooting

**Date**: 2025-10-19
**File**: `test/db/integration/test_database_postgres_integration.py`
**Status**: 4 of 5 tests currently skipped, awaiting fixes

---

## Overview

The `TestPostgresDatabaseIntegration` class contains infrastructure tests that verify PostgreSQL database initialization functionality. These tests validate that the database initialization system (`genonaut/db/init.py`) correctly:

1. Creates databases and database users (admin, read-write, read-only)
2. Creates schema and tables
3. Manages multiple database environments (dev, demo)
4. Enforces proper database isolation between environments
5. Implements correct user role permissions

---

## Test Status

### Passing Tests
- [x] `test_database_and_user_creation` - Tests database and user creation using SQL template

### Skipped Tests (Currently Failing)
- [ ] `test_schema_creation_and_table_setup` - Verify tables exist in public schema after initialization
- [ ] `test_main_and_demo_databases_have_tables` - Verify both dev and demo DBs have expected tables
- [ ] `test_database_isolation_between_main_and_demo` - Verify data isolation between databases
- [ ] `test_user_permissions` - Verify role-based permission enforcement (admin/rw/ro)

---

## Problem Analysis

### Root Cause

These tests are **infrastructure tests** that test the `initialize_database()` function itself. This creates a fundamental conflict with standard pytest fixture patterns:

1. **Setup Fixture Conflict**: The test class uses `setup_database_once` fixture (class-scoped) to initialize a clean database before all tests
2. **Individual Test Needs**: Each test then calls `initialize_database()` again to test specific initialization scenarios
3. **Transaction Error Cascade**: When `initialize_database(drop_existing=True)` tries to drop tables:
   - If tables don't exist: PostgreSQL transaction error "table does not exist"
   - Transaction enters failed state
   - All subsequent operations fail with "current transaction is aborted"
4. **Table Already Exists Error**: When using `drop_existing=False`:
   - Tables created by `setup_database_once` already exist
   - `initialize_database()` tries to create them again
   - Fails with "relation already exists"

### Technical Details

#### Error Pattern 1: Transaction Abortion
```
sqlalchemy.exc.SQLAlchemyError: Failed to drop tables:
(psycopg2.errors.InFailedSqlTransaction) current transaction is aborted,
commands ignored until end of transaction block
[SQL: SET search_path TO public]
```

**Cause**: `drop_tables()` in `genonaut/db/init.py` tries to drop tables that don't exist, causing PostgreSQL to abort the transaction. Subsequent commands fail because the transaction is in a failed state.

#### Error Pattern 2: Duplicate Table
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable)
relation "users" already exists
```

**Cause**: When skipping `drop_existing=True` to avoid transaction errors, tables created by the setup fixture clash with tables the test tries to create.

### Why This Is Challenging

1. **Testing the Tester**: These tests validate the initialization infrastructure itself, not application logic
2. **State Management**: Each test needs different database states (fresh, populated, isolated)
3. **PostgreSQL Strictness**: Unlike SQLite, PostgreSQL:
   - Strictly enforces transactions
   - Aborts entire transaction on any error
   - Requires explicit rollback before continuing
4. **drop_tables() Implementation**: The `drop_tables()` method in `genonaut/db/init.py` doesn't handle missing tables gracefully - it raises exceptions rather than using `DROP TABLE IF EXISTS` patterns

---

## Attempted Solutions

### What We Tried

1. **Skip seeding data**: Added `seed_data_path=Path('/tmp/genonaut_empty_seed')` to prevent TSV seeding
   - Result: Solved seeding FK constraint errors
   - Status: Working

2. **Use migrations instead of create_tables()**: Passed `seed_data_path` instead of `schema_name` to trigger Alembic migrations
   - Result: Created trigger functions correctly
   - Status: Working

3. **Avoid database drops in teardown**: Changed teardown to drop tables instead of databases
   - Result: Eliminated "database is being accessed by other users" errors
   - Status: Working

4. **One-time setup**: Created `setup_database_once` fixture to initialize DB once for all tests
   - Result: First test passes, but conflicts with subsequent tests
   - Status: Partial - creates new problems

5. **Skip drop_existing**: Used `drop_existing=False` in test calls to `initialize_database()`
   - Result: "relation already exists" errors
   - Status: Failed

---

## Solution Approaches

### Option 1: Fix drop_tables() Method (Recommended)

**Strategy**: Make `drop_tables()` transaction-safe by handling missing tables gracefully.

**Implementation**:
```python
# In genonaut/db/init.py, modify drop_tables() to:
1. Use DROP TABLE IF EXISTS instead of DROP TABLE
2. Wrap each drop in try/except to continue on error
3. Use separate transactions for each drop operation
4. Add rollback on error before continuing
```

**Pros**:
- Fixes root cause
- Benefits all callers of drop_tables()
- Makes infrastructure more robust

**Cons**:
- Requires modifying core infrastructure code
- Need to ensure backwards compatibility

### Option 2: Isolate Test Databases

**Strategy**: Each test uses completely separate database instances.

**Implementation**:
```python
# In test setup:
1. Create unique database names for each test (e.g., genonaut_test_pg_1, _2, etc.)
2. Each test initializes its own database from scratch
3. Teardown drops entire database (no table conflicts)
```

**Pros**:
- Complete test isolation
- No shared state between tests

**Cons**:
- Slower (creates/drops full databases per test)
- More complex setup/teardown
- Potential connection leaks

### Option 3: Remove setup_database_once Fixture

**Strategy**: Let each test manage its own database lifecycle completely.

**Implementation**:
```python
# Remove class-scoped setup_database_once
# Each test:
1. Calls initialize_database() with custom parameters
2. Performs its assertions
3. Cleanup happens in teardown
```

**Pros**:
- Tests are truly independent
- Each test controls its environment

**Cons**:
- Still requires fixing drop_tables() for transaction safety
- Tests run slower (repeated initialization)

### Option 4: Separate Test Classes

**Strategy**: Group tests by initialization strategy.

**Implementation**:
```python
# Create separate test classes:
class TestDatabaseCreation:
    # Tests that need fresh databases

class TestDatabaseSchemas:
    # Tests that verify existing database structure

class TestDatabasePermissions:
    # Tests that verify user roles
```

**Pros**:
- Each class can have appropriate fixtures
- Clearer test organization

**Cons**:
- Duplication of setup code
- Still requires fixing drop_tables()

---

## Recommended Action Plan

### Phase 1: Fix Core Infrastructure (High Priority)
- [ ] Update `drop_tables()` in `genonaut/db/init.py` to be transaction-safe
  - [ ] Use `DROP TABLE IF EXISTS` syntax
  - [ ] Catch and log errors without aborting transaction
  - [ ] Add `ignore_errors=True` parameter for permissive mode
  - [ ] Test with both SQLite and PostgreSQL

### Phase 2: Update Test Structure (Medium Priority)
- [ ] Update `test_schema_creation_and_table_setup`
  - [ ] Use unique database name or ensure clean state
  - [ ] Verify it works with fixed drop_tables()
- [ ] Update `test_main_and_demo_databases_have_tables`
  - [ ] Remove reliance on setup_database_once
  - [ ] Create fresh databases for test
- [ ] Update `test_database_isolation_between_main_and_demo`
  - [ ] Ensure proper cleanup between test steps
- [ ] Update `test_user_permissions`
  - [ ] Verify works with transaction-safe drops

### Phase 3: Add Transaction Safety Tests (Low Priority)
- [ ] Add test for drop_tables() with missing tables
- [ ] Add test for drop_tables() in failed transaction
- [ ] Add test for drop_tables() with ignore_errors=True

### Alternative Quick Fix (If infrastructure changes blocked)
- [ ] Mark all 4 tests as `@pytest.mark.manual`
- [ ] Document manual test procedure
- [ ] Run periodically as integration validation
- [ ] Re-enable when drop_tables() is fixed

---

## Additional Context

### Environment Requirements

These tests require:
- PostgreSQL instance running on localhost:5432
- Environment variables set:
  - `DB_PASSWORD_ADMIN` (from `env/.env.shared`)
  - `DB_PASSWORD_RW` (from `env/.env.shared`)
  - `DB_PASSWORD_RO` (from `env/.env.shared`)
- Permissions to create/drop databases
- Permissions to create users (admin, rw, ro)

### Why Tests Were Previously Skipped

Before the current work, these tests were skipped because:
1. Environment variables weren't being loaded during pytest runs
2. No mechanism to load `env/.env.shared` in test context

**Fixed by**:
- Adding `load_env_for_runtime("env/.env.local-test")` in `test/conftest.py`
- Changing `@pytest.fixture(scope="class")` to `@classmethod` for `setup_class`

---

## Files Involved

### Test Files
- `test/db/integration/test_database_postgres_integration.py` - Main test file

### Infrastructure Files
- `genonaut/db/init.py` - Database initialization logic
  - `initialize_database()` - Main entry point
  - `DatabaseInitializer.drop_tables()` - **Needs fixing**
  - `DatabaseInitializer.create_tables()` - Table creation
  - `DatabaseInitializer.create_database_and_users()` - User/DB creation

### Configuration Files
- `test/conftest.py` - Test environment setup
- `env/.env.shared` - Shared credentials
- `env/.env.local-test` - Test-specific config

---

## Success Criteria

Tests will be considered fixed when:
1. All 5 tests pass consistently
2. No transaction abortion errors
3. No "table already exists" errors
4. Tests run in <30 seconds total
5. Tests can run in any order (pytest -k)
6. No manual cleanup required between runs

---

## Notes

- These tests are infrastructure-level, not application-level
- They verify the database setup tooling works correctly
- They are important for CI/CD and deployment validation
- Consider running as separate "infrastructure test" suite
- May benefit from dedicated test database per test class
