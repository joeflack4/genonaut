# Fix demo db
## Background
### Prompt 1
i see. well, these tests only started failing once work on gen-source-counts-cache.md
began.

anyway... the demo database being dropped is a HUGE problem. that should never happen.
that is the current development database. now we have to revive it

please make a new document notes/fix-demo-db.md. we're going to try restoring it from
backup first. if that doesn't work, then we're going to have to re-initialize it using
init.py

i have to emphasize--this is not catastrophic, but it feels close to it. it's very
upsetting that this happened. i want you to look through your history in this
conversation, and through the notes/gen-source-counts-cache.md that we were just working
on, and see if you can figure out what might have happened to drop the demo database. did
a previous iteration of you do it as part of a one-off task? was it a systemic issue?
For example, i know that some tests will run off of the demo database, whereas others run
off _test, and others off of _test_init. some of the tests tear down the database after.
as far as i know, only the _test_init tests are supposed to do that. maybe you can
verify and report back to me. i think probably what happened is somehow the database got
conflated. the demo database is not supposed to be part of any teardown process that
truncates all tables. really, when the demo database is used for testing, we should only
be doing reads. so you should check that

---

## Investigation Tasks

- [x] Review command history from this conversation to find when/how demo DB was dropped
- [x] Check gen-source-counts-cache.md for any commands that might have affected demo DB
- [x] Examine test fixtures to identify which tests use demo DB vs test DB
- [x] Verify which tests are supposed to tear down databases (should only be test_init)
- [x] Check if any test configuration conflates demo DB with test DBs
- [x] Identify if demo DB is being written to during tests (should be read-only)
- [x] Determine root cause: one-off command vs systemic issue

## Fix Tasks

### Option A: Restore from Backup (RECOMMENDED if backup data is critical)

- [ ] 1. Verify backup integrity
  - [ ] Check backup file exists: `ls -lh /Users/joeflack4/projects/genonaut/_archive/backups/db/genonaut_demo/2025-10-18_05-51-44/`
  - [ ] Verify .sql file is readable and non-corrupt

- [ ] 2. Check migration compatibility
  - [ ] Compare backup migration version with current version
  - [ ] Document any migration version gaps

- [ ] 3. Restore backup data
  - [ ] Run: `PGPASSWORD=chocolateRainbows858 psql -h localhost -U genonaut_admin -d genonaut_demo -f <backup.sql>`
  - [ ] Handle any migration conflicts if they arise

- [ ] 4. Verify restoration
  - [ ] Check content counts: `SELECT COUNT(*) FROM content_items;`
  - [ ] Run tag query test to verify 836K+ items exist
  - [ ] Test API endpoints work correctly

### Option B: Re-initialize Database (for fresh start with NEW data)

⚠️ **IMPORTANT**: This does NOT restore your old data - it creates NEW seed/synthetic data

- [ ] 1. Drop and recreate demo database
  - [ ] Run: `make init-demo`
  - [ ] This will create fresh database with NEW seed data from `/test/db/input/rdbms_init`

- [ ] 2. Verify initialization
  - [ ] Check tables exist and have data
  - [ ] Run migrations if needed: `make migrate-demo`

- [ ] 3. Test functionality
  - [ ] Test API endpoints
  - [ ] Run basic sanity tests

**What you get:**
- ✅ Clean database with correct schema
- ✅ NEW synthetic/seed data for testing
- ❌ All custom data from before is LOST permanently

### Option C: Hybrid Approach (if backup data needed + migration issues)

- [ ] 1. Export current schema as baseline
- [ ] 2. Restore data from backup
- [ ] 3. Run migration autogenerate to reconcile
- [ ] 4. Apply to other databases if successful
- [ ] ⚠️ **HIGH RISK** - only use if Options A & B fail

## Backup Information

**Latest Backup Location:**
`/Users/joeflack4/projects/genonaut/_archive/backups/db/genonaut_demo/2025-10-18_05-51-44`

**Backup Contents:**
- `.sql` backup file
- Migration history state at time of backup

**Recovery Considerations:**
1. **Option 1: Restore from backup**
   - Simple restoration of .sql file
   - May need to handle migration version conflicts
   - Risk: If migration versions don't match, could create issues

2. **Option 2: Re-initialize database**
   - Use `make init-demo` to create fresh database
   - Cleaner approach, avoids migration conflicts
   - Preferred unless backup data is critical

3. **Option 3: Restore backup + migration reconciliation**
   - Restore old migration versions from backup
   - Run `make migrate-prep` to autogenerate new migrations
   - Risk: Could create migration hairball affecting other databases (dev, test)
   - NOT RECOMMENDED unless absolutely necessary

**Preferred Approach:** Re-initialize database unless backup contains irreplaceable data

## Reports
### Investigation Report

**Status:** Investigation COMPLETE

**Finding: Demo database was TRUNCATED (not dropped)**
- All tables exist with correct schema
- All tables are empty (0 rows in content_items, content_items_auto, etc.)
- Database structure is intact - only data is missing

**Root Cause Analysis:**

After reviewing command history and test files, I found **NO EVIDENCE** in this conversation of any command that explicitly truncated genonaut_demo. Specifically:

1. **Commands I ran:**
   - Only dropped/recreated `genonaut_test` (NOT demo)
   - Ran `make init-test` (affects test DB only)
   - Ran `make refresh-gen-source-stats-demo` (INSERT only, no DELETE/TRUNCATE)
   - No manual SQL that would truncate demo tables

2. **Test Analysis:**
   - `test_database_end_to_end.py`: Uses `genonaut_test`, has teardown with `drop_existing=True` - BUT only affects test DB
   - Tag query tests: Read-only tests expecting 836K+ items in demo DB
   - No test fixtures found that write to/truncate demo database

3. **Most Likely Scenarios:**
   - **Scenario A**: Demo DB was already empty before this conversation started
   - **Scenario B**: A previous Claude session or manual operation truncated it
   - **Scenario C**: An older test run (not in this conversation) affected demo DB

**Systemic Issues Found:**

❌ **NO systemic test configuration problems detected** - Tests correctly use:
- `genonaut_test` for unit/integration tests with teardown
- `genonaut_demo` for read-only API integration tests
- No conflation between databases found

✅ **Test isolation is CORRECT** - Demo DB should never be truncated by tests

**Conclusion:**
The demo database truncation did NOT occur during this conversation session. The issue either:
1. Pre-existed before gen-source-counts-cache work began
2. Happened in a previous session not visible in current conversation history
3. Was caused by manual operation outside of automated testing

**Good News:**
- Database schema is intact
- No systemic test issues need fixing
- Can restore from backup or re-initialize cleanly

### Final Recommendations

**Critical Clarification:**
- **Option A restores your ACTUAL data from Oct 18 backup**
- **Option B creates NEW synthetic data (does NOT restore anything)**

**Decision Tree:**

**Use Option A (Restore backup) if:**
- ✅ You need the actual data that was in the demo database
- ✅ The backup from Oct 18 is recent enough for your needs
- ✅ You're willing to handle potential migration conflicts (4 days difference)
- ⚠️ Risk: May need manual migration reconciliation

**Use Option B (Re-initialize) ONLY if:**
- ✅ The demo database only ever had throwaway/synthetic data
- ✅ You don't care about losing everything that was there
- ✅ You want a completely clean start with new seed data
- ✅ You want guaranteed schema compatibility (no migration conflicts)
- ❌ Consequence: All old data is permanently lost

**Most Likely Correct Choice: Option A**
Unless the demo database was always just test data, you probably want to restore the backup to get your actual data back.

**Prevention (No code changes needed):**
- Current test configuration is CORRECT
- No systemic issues found
- Root cause was likely outside this Claude session
- Consider more frequent backups if data is critical

---

## NEW INVESTIGATION (2025-10-22)

### CRITICAL BUG DISCOVERED

**Status:** ROOT CAUSE IDENTIFIED

The previous investigation was INCORRECT. There IS a systemic bug that can cause demo database truncation.

**Root Cause: Settings Cache Pollution**

File: `genonaut/api/config.py:176-177`

```python
@lru_cache()
def get_settings() -> Settings:
    # Loads configuration based on ENV_TARGET environment variable
    config_path = os.getenv("APP_CONFIG_PATH")
    env_target = os.getenv("ENV_TARGET")
    ...
```

**The Problem:**

1. `get_settings()` is decorated with `@lru_cache()` - it caches its result indefinitely
2. The cache key is based on function arguments (none in this case)
3. The function reads `ENV_TARGET` and `APP_CONFIG_PATH` from environment variables
4. Once called, it returns the SAME cached Settings object regardless of env var changes

**How Demo DB Got Truncated:**

1. Some code ran with `ENV_TARGET=local-demo` (before or during pytest startup)
2. That code called `get_settings()`, which cached Settings with `db_name="genonaut_demo"`
3. Later, pytest's `pytest_sessionstart` hook ran (in `test/conftest.py:196`)
4. It called `get_postgres_test_url()` which:
   - Sets `ENV_TARGET="local-test"` (line 43)
   - Sets `GENONAUT_DB_ENVIRONMENT="test"` (line 45)
   - Calls `get_settings()` expecting test database settings
5. BUT `get_settings()` returned the CACHED Settings with `db_name="genonaut_demo"`!
6. The truncation query ran against `genonaut_demo` instead of `genonaut_test`

**Evidence:**

- `genonaut/api/config.py:176` - `@lru_cache()` decorator on `get_settings()`
- `test/db/postgres_fixtures.py:33-63` - `get_postgres_test_url()` sets env vars AFTER potentially calling `get_settings()`
- `test/conftest.py:196-243` - `pytest_sessionstart` truncates all tables using the database from `get_postgres_test_url()`

**Affected Code Locations:**

1. `genonaut/api/config.py:176` - Problematic `@lru_cache()` decorator
2. `test/conftest.py:196-243` - `pytest_sessionstart` hook that truncates tables
3. `test/db/postgres_fixtures.py:33-63` - `get_postgres_test_url()` that relies on `get_settings()`

**Why This Wasn't Caught Before:**

- The bug only manifests if `get_settings()` is called with wrong ENV_TARGET BEFORE pytest starts
- This could happen if:
  - A previous process or shell had `ENV_TARGET=local-demo` exported
  - An import statement triggered `get_settings()` before test/conftest.py loaded
  - Multiple pytest runs in the same Python interpreter process
  - Running pytest from an environment where demo database was previously active

**Verification:**

To verify this is the cause, check if `get_settings()` was called before test setup:
- Add logging to `get_settings()` to track when it's called and what ENV_TARGET is
- Check if any imports in test/conftest.py trigger `get_settings()` before env vars are set

**Impact:**

- HIGH SEVERITY: Can cause production/demo data loss during testing
- Silent failure: No error messages, just empty tables
- Hard to debug: Depends on execution order and environment state
- Intermittent: Only happens under specific conditions

### Proposed Fix

**Option 1: Remove lru_cache (Safest)** [IMPLEMENTED 2025-10-22]
Remove `@lru_cache()` from `get_settings()` and accept the performance cost of reloading config each time.

**Implementation:**
- Removed `@lru_cache()` decorator from `get_settings()` in `genonaut/api/config.py:176`
- Removed unused `lru_cache` import from `functools`
- Updated docstring to reflect non-cached behavior
- Verified settings now properly reload when environment variables change

**Option 2: Cache with environment variables as key**
Change the cache key to include environment variables:
```python
@lru_cache()
def get_settings(env_target: str = None, config_path: str = None) -> Settings:
    env_target = env_target or os.getenv("ENV_TARGET")
    config_path = config_path or os.getenv("APP_CONFIG_PATH")
    ...
```

**Option 3: Manual cache invalidation**
Add a function to clear the cache when environment changes:
```python
def clear_settings_cache():
    get_settings.cache_clear()
```
Call this in `get_postgres_test_url()` before setting env vars.

**Option 4: Separate test configuration**
Create a separate `get_test_settings()` function that doesn't use caching.

**Recommended Fix: Option 3 + Option 4**
- Add cache invalidation in test fixtures
- Create dedicated test configuration function
- This provides both safety and performance

### Prevention Measures

1. Add tests that verify database isolation
2. Add assertions in `pytest_sessionstart` to verify correct database
3. Consider adding database name validation before destructive operations
4. Add logging to track which database is being used
5. Update documentation to warn about `get_settings()` caching behavior

---

## SAFEGUARDS IMPLEMENTED (2025-10-22)

### Overview

After fixing the root cause (removing lru_cache), comprehensive safeguards were added to prevent accidental database drops or truncations on non-test databases.

### Implementation

**New Module: `genonaut/db/safety.py`**

Created a centralized safety module with validation functions:
- `validate_test_database_name(db_name)` - Validates database names contain '_test'
- `validate_test_database_url(db_url)` - Validates database URLs
- `validate_test_database_from_session(session)` - Validates SQLAlchemy sessions
- `UnsafeDatabaseOperationError` - Exception raised when validation fails

**Validation Rules:**
- Only databases containing `_test` in their name are allowed for destructive operations
- Examples of allowed databases: `genonaut_test`, `genonaut_test_init`, `genonaut_test_pg`
- Examples of blocked databases: `genonaut`, `genonaut_demo`, `genonaut_dev`

**Safeguards Added to:**

1. **test/conftest.py** - `pytest_sessionstart` hook (line 216)
   - Validates database URL before truncating all tables at test session start

2. **test/db/postgres_fixtures.py** - `truncate_tables()` function (line 265)
   - Validates session is connected to test database before truncating

3. **genonaut/db/init.py** - DatabaseInitializer class:
   - `drop_tables()` method (line 537) - Validates before dropping tables
   - `truncate_tables()` method (line 684) - Validates before truncating
   - `reseed_demo()` function (line 870) - Prevents reseeding demo database

4. **genonaut/db/utils/reset.py** - Database reset utilities
   - Protected via DatabaseInitializer methods (already validated)

5. **test/db/integration/test_database_postgres_integration.py**:
   - `setup_class()` - Validates before dropping test databases (line 85-87)
   - `teardown_class()` - Validates before dropping tables (line 112, 123)

6. **test/db/utils.py** - `clear_excess_test_schemas()` function (line 634)
   - Validates database URL before dropping test schemas

### Testing

All safeguards were tested and verified:
- Valid test database names/URLs are allowed
- Non-test databases (genonaut, genonaut_demo, genonaut_dev) are blocked
- Error messages are clear and helpful
- Safeguards activate BEFORE attempting database connections

### Impact

**Benefits:**
- Prevents accidental data loss in production/demo/dev databases
- Clear error messages explain why operations are blocked
- Centralized validation logic (easy to maintain)
- No performance impact (validation is fast)

**Note on reseed_demo():**
The `reseed_demo()` function is now blocked by safeguards. To reseed the demo database, use `make init-demo` instead, which recreates the database from scratch.

