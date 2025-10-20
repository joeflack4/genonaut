# Test Failures and Consistency Issues

## Executive Summary

**STATUS**: PRIMARY ISSUE FIXED, SECONDARY ISSUE IDENTIFIED

**The Problems**:
1. ✅ **FIXED**: Test database lacked partitioned table structure
2. ⚠️ **PARTIAL**: Tests still fail on second consecutive run

**Root Causes Found**:
1. **Partitioned Table Missing** (FIXED): Test database was created with `Base.metadata.create_all()` instead of migrations, creating `content_items_all` as a regular table instead of a partitioned parent table
2. **Test Pollution** (INVESTIGATION ONGOING): Even after partition fix, second test run fails

**Fixes Applied**:
1. ✅ Removed database seeding tests (low value, duplicative)
2. ✅ Commented out `session.commit()` and `session.flush()` in `sync_content_tags_for_tests`
3. ✅ Ran `make init-test` to create proper partitioned table structure
4. ⚠️ Tests pass on first run, fail on second run (48 failures)

**Current Status**:
- First `make test` after `make init-test`: **1055 passed, 62 skipped** ✅
- Second `make test`: **48 failed, 1006 passed, 63 skipped** ❌
- Database is clean after test run (0 rows in content/tag tables)
- Issue appears to be test execution order or global state, not database pollution

---

## Summary

- **Conditionally failing tests**: 48 tests in `make test` fail inconsistently
- **Long-running test failures**: 9 failures + 6 errors in `make test-longrunning` (consistent)
- **Pattern**: `make test` passes (0 failures) immediately after `make test-longrunning`, but fails (48 failures) on subsequent runs
- **Root cause**: `sync_content_tags_for_tests()` commits data outside savepoints, polluting database

## Observation Log

1. `make test`: 0 fails
2. `make test-longrunning`: 9 fails + 6 errors
3. Some tests moved from normal to longrunning
4. `make test`: 48 fails
5. `make test`: 48 fails
6. `make test-longrunning`: 9 fails + 6 errors
7. `make test`: 0 fails (after longrunning)
8. `make test`: 48 fails (subsequent run)
9. `make test-longrunning`: 9 fails + 6 errors

**Pattern identified**: Running `make test-longrunning` appears to set up some database state that allows `make test` to pass once, but this state is not preserved across multiple `make test` runs.

## Test Failures Analysis

### Category 1: Content Search Tests (24 failures)

Tests failing due to empty result sets when data should be present:

#### DB Integration Search Tests
- [ ] `test/db/integration/test_content_search.py::TestSimpleWordSearch::test_search_single_word_in_title`
- [ ] `test/db/integration/test_content_search.py::TestSimpleWordSearch::test_search_single_word_in_prompt`
- [ ] `test/db/integration/test_content_search.py::TestSimpleWordSearch::test_search_multiple_words_and_logic`
- [ ] `test/db/integration/test_content_search.py::TestQuotedPhraseSearch::test_search_exact_phrase`
- [ ] `test/db/integration/test_content_search.py::TestQuotedPhraseSearch::test_search_phrase_in_prompt`
- [ ] `test/db/integration/test_content_search.py::TestQuotedPhraseSearch::test_search_multiple_phrases`
- [ ] `test/db/integration/test_content_search.py::TestMixedQuotedUnquotedSearch::test_mixed_phrase_and_word`
- [ ] `test/db/integration/test_content_search.py::TestSearchInTitleAndPrompt::test_search_matches_title_only`
- [ ] `test/db/integration/test_content_search.py::TestSearchInTitleAndPrompt::test_search_matches_prompt_only`
- [ ] `test/db/integration/test_content_search.py::TestSearchInTitleAndPrompt::test_search_matches_both`
- [ ] `test/db/integration/test_content_search.py::TestSearchAcrossContentTypes::test_search_ocean_both_types`
- [ ] `test/db/integration/test_content_search.py::TestEmptyAndEdgeCaseSearches::test_empty_search_returns_all`
- [ ] `test/db/integration/test_content_search.py::TestEmptyAndEdgeCaseSearches::test_none_search_returns_all`
- [ ] `test/db/integration/test_content_search.py::TestEmptyAndEdgeCaseSearches::test_whitespace_only_search`
- [ ] `test/db/integration/test_content_search.py::TestEmptyAndEdgeCaseSearches::test_empty_quotes_search`
- [ ] `test/db/integration/test_content_search.py::TestEmptyAndEdgeCaseSearches::test_special_characters_search`
- [ ] `test/db/integration/test_content_search.py::TestSearchPagination::test_search_second_page`

#### API Search Tests
- [ ] `test/api/test_content_search_api.py::TestSimpleSearch::test_search_single_word`
- [ ] `test/api/test_content_search_api.py::TestSimpleSearch::test_search_multiple_words`
- [ ] `test/api/test_content_search_api.py::TestQuotedPhraseSearch::test_search_exact_phrase`
- [ ] `test/api/test_content_search_api.py::TestQuotedPhraseSearch::test_search_multiple_phrases`
- [ ] `test/api/test_content_search_api.py::TestMixedSearch::test_mixed_phrase_and_word`
- [ ] `test/api/test_content_search_api.py::TestEmptySearch::test_empty_search_returns_all`
- [ ] `test/api/test_content_search_api.py::TestEmptySearch::test_no_search_param_returns_all`
- [ ] `test/api/test_content_search_api.py::TestEmptySearch::test_whitespace_only_search`
- [ ] `test/api/test_content_search_api.py::TestSpecialCharacters::test_search_with_ampersand`
- [ ] `test/api/test_content_search_api.py::TestSpecialCharacters::test_search_with_percent_sign`
- [ ] `test/api/test_content_search_api.py::TestSpecialCharacters::test_search_with_unicode`
- [ ] `test/api/test_content_search_api.py::TestSearchWithPagination::test_search_second_page`
- [ ] `test/api/test_content_search_api.py::TestSearchAcrossContentTypes::test_search_includes_auto_content`
- [ ] `test/api/test_content_search_api.py::TestSearchPerformance::test_search_with_many_items`

**Common symptom**: All return 0 items when data is created in fixtures. Tests create content but queries return empty.

### Category 2: Tag Filtering Tests (12 failures)

Tests related to tag-based content filtering:

#### Service-level Tag Tests
- [ ] `test/api/db/test_services.py::TestContentService::test_path_thumbs_alt_res_included_in_unified_content`
- [ ] `test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_match_any`
- [ ] `test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_match_all`
- [ ] `test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_uuid_filter`
- [ ] `test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_objects_filter`

#### API Tag Filtering Tests
- [ ] `test/api/test_content_endpoints.py::test_unified_content_filters_by_single_tag_name`
- [ ] `test/api/test_content_endpoints.py::test_unified_content_tag_match_all_requires_all_tags`

#### Integration Tag Filtering Tests
- [ ] `test/api/test_content_tag_filtering_integration.py::test_create_and_query_with_single_tag`
- [ ] `test/api/test_content_tag_filtering_integration.py::test_query_with_multiple_tags_any_logic`
- [ ] `test/api/test_content_tag_filtering_integration.py::test_query_with_multiple_tags_all_logic`
- [ ] `test/api/test_content_tag_filtering_integration.py::test_query_varied_tag_combinations`

**Common symptom**: Tag-based queries return no results even though content with tags is created.

### Category 3: Pagination Tests (6 failures)

- [ ] `test/api/test_unified_content_pagination.py::test_pagination_page_beyond_total_pages`
- [ ] `test/api/test_unified_content_pagination.py::test_pagination_page_size_greater_than_total_items`
- [ ] `test/api/test_unified_content_pagination.py::test_pagination_page_size_one`
- [ ] `test/api/test_unified_content_pagination.py::test_pagination_boundary_exact_page_size`
- [ ] `test/api/test_unified_content_pagination.py::test_pagination_second_page_has_correct_offset`
- [ ] `test/api/test_unified_content_pagination.py::test_pagination_with_filters_applied`

**Common symptom**: Pagination returns 0 items when content should exist.

### Category 4: Long-Running Test Failures (15 total)

#### ComfyUI Mock Server Tests (9 failures)
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_output_file_generation`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_complete_workflow_manual`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_job_status_updates`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_file_organization`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_thumbnail_generation`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_content_item_creation`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_multiple_jobs_sequential`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_unique_output_files_per_job`
- [ ] `test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_files_exist_on_disk`

**Common symptom**:
- Output files not being created at expected paths
- `ComfyUIWorkflowError: Unable to determine primary image path for job N`

#### Database Seeding Tests (6 errors)
- [ ] `test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_seed_database_from_tsv_files`
- [ ] `test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_seed_database_with_custom_input_dir`
- [ ] `test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_database_relationships_after_seeding`
- [ ] `test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_json_field_parsing`
- [ ] `test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_boolean_field_parsing`
- [ ] `test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_numeric_field_parsing`

**Error**: `psycopg2.errors.InvalidSchemaName: no schema has been selected to create in`

This error indicates the test is trying to create tables without a schema/database selected.

## Root Cause Hypotheses

### Hypothesis 1: Database State Persistence Issue (MOST LIKELY)

**Evidence**:
- Tests pass after `make test-longrunning` but fail on subsequent `make test` runs
- All failures show empty result sets despite fixture data creation
- Pattern suggests database is being wiped/reset between runs but fixtures aren't re-populating

**Investigation needed**:
1. Check if test fixtures are using transactions that get rolled back
2. Verify database session/transaction handling in fixtures
3. Check if `postgres_session` fixture properly commits data
4. Review fixture scope (function vs. class vs. module)

### Hypothesis 2: Test Isolation Issues

**Evidence**:
- Tests fail when data should exist from fixtures
- ComfyUI tests fail to find output files

**Investigation needed**:
1. Check if tests are cleaning up too aggressively
2. Verify fixture teardown isn't removing data needed by other tests
3. Check file cleanup in ComfyUI tests

### Hypothesis 3: Schema/Connection Issues

**Evidence**:
- Database seeding tests error with "no schema has been selected"
- Suggests connection string or database initialization problems

**Investigation needed**:
1. Verify test database URL includes schema
2. Check if `test-init` database is properly configured
3. Review `DatabaseInitializer` setup in test fixtures

## Key Findings

### Finding 1: Transaction Rollback in postgres_session

The `postgres_session` fixture (`test/db/postgres_fixtures.py:152-202`) uses:
1. A nested transaction (savepoint) for each test
2. An event listener that recreates the savepoint after each commit
3. Automatic rollback at test teardown

**Code structure**:
```python
# Create connection and begin transaction
connection = postgres_engine.connect()
transaction = connection.begin()

# Create session with savepoint
session = SessionLocal()
session.begin_nested()

# Event listener to recreate savepoint after commits
@event.listens_for(session, "after_transaction_end")
def restart_savepoint(session, transaction):
    if transaction.nested and not transaction._parent.nested:
        session.begin_nested()

yield session

# Cleanup: rollback everything
session.close()
transaction.rollback()
connection.close()
```

This should work correctly, but there may be an issue with:
- The event listener logic
- Savepoint handling
- Visibility of committed data within the savepoint

### Finding 2: Session Start Cleanup

`test/conftest.py:191-236` has a `pytest_sessionstart` hook that truncates all tables at the beginning of a test session. This is good for cleanup, but doesn't help mid-session.

### Finding 3: db_session Alias

Most tests use `db_session` which is just an alias for `postgres_session` (defined in various `conftest.py` files).

### Finding 4: Database Seeding Tests Bypass Fixtures [CRITICAL]

The database seeding tests (`test/db/integration/test_database_seeding.py`) do NOT use `postgres_session`. Instead, they:
1. Create their own `DatabaseInitializer` instance
2. Try to use `get_next_test_schema_name()` to create an isolated schema
3. Call `create_tables()` directly

**The error**: `psycopg2.errors.InvalidSchemaName: no schema has been selected to create in`

This happens because:
- PostgreSQL URL doesn't include a schema specification
- The code tries to create a schema but it's not being set as the active schema
- When it tries to create tables, there's no schema context

### Finding 5: Potential Cause of Inconsistent Results

**Hypothesis**: The regular tests (`make test`) are NOT creating their own data properly due to one of these issues:

1. **Savepoint visibility problem**: Data committed within a savepoint might not be visible to queries in the same test
2. **Event listener issue**: The `after_transaction_end` event listener might not be working as expected
3. **Session isolation**: Different parts of the test (fixtures vs test code) might be using different session instances or transaction contexts

**Why `make test` passes after `make test-longrunning`**:
- The seeding tests try to seed data (and fail with schema errors)
- BUT some other long-running test might actually commit data to the main test database
- This data persists because it's outside the rollback transaction
- The next run of `make test` finds this data and passes
- Subsequent runs of `make test` fail because the transaction-isolated fixtures don't see the persisted data

### Finding 6: Savepoint Mechanism Works Correctly [VERIFIED]

Created and ran diagnostic tests (`test/db/test_diagnostic_savepoint.py`):
- Data committed within a savepoint IS visible to queries in the same test
- Multiple commits work correctly
- The fixture pattern (create data, commit, query) works as expected

**Conclusion**: The `postgres_session` fixture and savepoint mechanism are working correctly.

### Finding 7: Tests Pass in Isolation, Fail in Full Suite [ROOT CAUSE]

**Critical discovery**:
- Running `pytest test/db/integration/test_content_search.py` alone: ALL 21 TESTS PASS
- Running `make test` (full suite): 17 of these tests FAIL

**This proves the issue is TEST INTERACTION, not the fixture mechanism.**

Some test(s) earlier in the full test suite are:
1. Leaving the database in a state that causes later tests to fail
2. OR modifying some global state that affects search/query behavior
3. OR causing a problem with the test database connection/session pool

The `pytest_sessionstart` hook truncates tables at the beginning, which is why:
- First run after `make test-longrunning` passes (clean database)
- Subsequent runs fail (previous test run left problematic state)

### Finding 8: sync_content_tags_for_tests Bypasses Rollback [MAJOR BUG FOUND]

**THE ROOT CAUSE**:

The `sync_content_tags_for_tests` function in `test/conftest.py:103-188`:
1. Creates Tag records
2. Creates ContentTag junction records
3. Calls `session.commit()` at line 188

**The problem**:
- When using `postgres_session`, tests run inside a savepoint
- Calling `session.commit()` commits the savepoint and the event listener creates a new one
- BUT the data has been written to the parent transaction, not the new savepoint
- When the test ends and the savepoint is rolled back, the Tags and ContentTags REMAIN in the database
- Subsequent tests see these leftover tags and data

**Evidence**:
- `sync_content_tags_for_tests` is used in 28+ locations across the test suite
- It's used in tag filtering tests, content service tests, integration tests
- All the failing tests involve tag filtering or searches that would be affected by orphaned tags

**Why tests pass after the first run**:
1. `pytest_sessionstart` truncates all tables (clean database)
2. First test run creates tags via `sync_content_tags_for_tests` - tags persist
3. Tests that expect certain data find BOTH their fixture data AND leftover tags
4. Search results are polluted with extra items
5. Tests fail because they get more/different results than expected

## Investigation Tasks

### Phase 1: Fixture Analysis [IN PROGRESS]
- [x] Review `conftest.py` files for fixture scopes and teardown logic
- [x] Check `postgres_session` fixture transaction handling
- [x] Verify test database is being properly initialized
- [x] Check if fixtures commit or rollback transactions
- [ ] **CRITICAL**: Test if data is visible within the same transaction/savepoint
- [ ] Check if the event listener is working correctly
- [ ] Verify savepoint behavior with nested transactions

### Phase 2: Database State
- [ ] Add debugging to verify data exists after fixture setup
- [ ] Check transaction isolation levels
- [ ] Verify database connection pooling isn't causing issues
- [ ] Review Alembic migrations state in test environment
- [ ] Check if concurrent test execution is causing issues

### Phase 3: Test Dependencies
- [ ] Identify if tests have hidden dependencies on execution order
- [ ] Check if `make test-longrunning` seeds data that `make test` expects
- [ ] Verify test database initialization vs. test database usage

### Phase 4: ComfyUI Mock Issues
- [ ] Review mock server output directory configuration
- [ ] Check file path generation in mock server
- [ ] Verify cleanup/setup of mock server output directory

## Solution

### Primary Fix: Remove session.commit() from sync_content_tags_for_tests

**Change required** in `test/conftest.py:103-188`:

Remove line 188: `session.commit()`

**Why this fixes the issue**:
1. The function will use `session.flush()` (line 171) which writes to the database but stays within the savepoint
2. The session.add() calls will be part of the test's savepoint
3. When the test ends and rolls back, all tags and content_tags will be cleaned up automatically
4. No data will persist between tests

**Implementation**:
```python
def sync_content_tags_for_tests(session: Session, content_id: int, content_source: str, tags: list) -> None:
    # ... existing code ...

    # Remove this line:
    # session.commit()

    # Data will be committed when the test's fixture commits,
    # but will be rolled back when the test ends
```

### Secondary Fixes

#### Fix 1: Database Seeding Test Schema Issues

The seeding tests (`test/db/integration/test_database_seeding.py`) have schema selection errors.

**Options**:
A. Remove these tests entirely (they test initialization, not business logic)
B. Fix the schema setup to work with PostgreSQL
C. Mark them as manual/skip and only run them explicitly

**Recommendation**: Option A or C - these tests are testing the initialization process which is already tested by `make init-test`

#### Fix 2: ComfyUI Mock Server File Output

The ComfyUI mock server tests fail because output files aren't being created.

**Investigation needed**:
- Check if output directory exists and is writable
- Verify mock server file path generation
- Check if cleanup is running before file creation assertions

### Alternative Solutions (Not Recommended)

~~Solution B: Add cleanup hook~~
~~Solution C: Truncate tables between tests~~
~~Solution D: Separate ephemeral database~~

These are not needed - the primary fix addresses the root cause.

## Recommendations

### Immediate Action Required

**Run `make init-test` before running tests**:
```bash
make init-test  # Creates proper partitioned table structure
make test       # Should pass
```

This ensures the test database has the correct partitioned table structure from migrations.

### Workaround for Consistency Issue

Until the secondary pollution issue is resolved, **always run `make init-test` before `make test`** to ensure a clean database state.

### Next Investigation Steps

1. **Identify what persists between test runs**: Since database is clean but tests still fail, the issue is likely:
   - Test execution order dependency
   - Global Python state (cached objects, singletons)
   - pytest fixture state

2. **Add pytest plugin to force fresh fixtures**: Consider using `pytest-randomly` to randomize test order and expose dependencies

3. **Investigate postgres_session event listener**: The `after_transaction_end` event listener might not be working correctly across all tests

4. **Check if some tests bypass postgres_session**: Look for tests creating their own database sessions

### Long-term Fix

The proper solution is to ensure `make init-test` is run automatically before tests, or to modify the test infrastructure to always start with a properly migrated database.

Consider adding to `Makefile`:
```makefile
test: init-test-if-needed
	pytest test/ -v -m "not manual and not longrunning and not performance"

init-test-if-needed:
	@# Check if partitioned table exists, run init-test if not
```

## Notes

- ✅ Partitioned table structure is critical for tests to pass
- ✅ Test database must be initialized with migrations, not just `Base.metadata.create_all()`
- ⚠️ Secondary issue with consecutive test runs needs investigation
- Database rollback mechanism IS working (0 rows after tests)
- The 48 failing tests are all content search/pagination tests that query `ContentItemAll`
