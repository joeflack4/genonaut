# Phase 11 - Remaining Test Fixes (35 tests)

## Current Status
- **Total Tests**: 1117
- **Passing**: 1030 (92%)
- **Failing**: 17
- **Errors**: 18
- **Total Issues**: 35

## Completed Fixes (73 tests fixed)
- [x] Category 1: Fixed `existing_tag` variable syntax error (38 tests) - test/conftest.py line 161
- [x] Category 2: Fixed foreign key violations (2 tests) - Added proper fixtures in test_notification_service.py
- [x] Category 3: Fixed PostgreSQL database creation (5 tests) - test_database_end_to_end.py
- [x] Category 5: Fixed missing fixture attributes (12 tests) - test_flagged_content_repository.py
- [x] Category 6: Fixed JSONB/SQLite incompatibility (20 tests) - Updated conftest files
- [x] Category 7: Fixed PostgreSQL connection failures (6 tests) - test_database_seeding.py

## Remaining Issues to Fix (35 tests)

### Group A: test_database_end_to_end.py (4 failures)
**Issue**: Still getting Alembic ConfigParser errors with URL-encoded schema parameters
**Files**: test/db/integration/test_database_end_to_end.py

- [ ] Fix test_database_initialization_without_seeding
- [ ] Fix test_database_initialization_with_drop_existing
- [ ] Fix test_database_schema_validation
- [ ] Fix test_database_relationships_work_end_to_end

**Solution Strategy**:
1. Check if my previous fix was applied correctly (using base URL without schema)
2. If not applied, update setup_method to use `os.getenv('DATABASE_URL_TEST')` directly
3. Remove any `create_test_database_url()` calls that add URL-encoded parameters

**Files to Edit**:
- test/db/integration/test_database_end_to_end.py (lines 30-41)

---

### Group B: test_tag_repository.py Duplicate Key Violations (2 failures)
**Issue**: IntegrityError - duplicate key "user2@example.com" already exists
**Files**: test/db/integration/test_tag_repository.py

- [ ] Fix TestTagRepositoryRatings::test_get_tag_average_rating
- [ ] Fix TestTagRepositoryRatings::test_get_tags_sorted_by_rating

**Solution Strategy**:
1. Locate the TestTagRepositoryRatings class setup_method
2. Replace hardcoded emails with UUID-based unique emails
3. Example: `email=f"user{uuid4()}@example.com"` instead of `email="user2@example.com"`

**Files to Edit**:
- test/db/integration/test_tag_repository.py (TestTagRepositoryRatings class)

---

### Group C: test_tag_repository.py Data Leakage (4 failures)
**Issue**: Tests expect specific counts but get more due to data from previous tests
**Files**: test/db/integration/test_tag_repository.py

- [ ] Fix TestTagRepositoryHierarchy::test_get_root_tags (expects 2, gets 5)
- [ ] Fix TestTagRepositorySearch::test_get_all_paginated (expects 6, gets 9)
- [ ] Fix TestTagRepositorySearch::test_get_all_paginated_page_2 (pagination off)
- [ ] Fix TestTagRepositoryStatistics::test_get_hierarchy_statistics (expects 6, gets 9)

**Solution Strategy**:
1. These tests are seeing data from other tests in the same file
2. Option 1: Make assertions relative (e.g., `>= expected_count`)
3. Option 2: Add cleanup in setup_method to delete existing tags
4. Option 3: Use unique tag names per test with UUID prefixes

**Files to Edit**:
- test/db/integration/test_tag_repository.py (multiple test classes)

---

### Group D: test_tag_models.py Duplicate Key Violations (7 errors)
**Issue**: IntegrityError - duplicate key "test@example.com" already exists
**Files**: test/db/unit/test_tag_models.py

- [ ] Fix TestTagRatingModel::test_tag_rating_creation
- [ ] Fix TestTagRatingModel::test_tag_rating_unique_constraint
- [ ] Fix TestTagRatingModel::test_tag_rating_allows_half_stars
- [ ] Fix TestTagRatingModel::test_tag_rating_foreign_keys
- [ ] Fix TestTagRatingModel::test_multiple_users_can_rate_same_tag
- [ ] Fix TestTagRatingModel::test_user_can_rate_multiple_tags
- [ ] Fix TestTagRatingModel::test_tag_rating_relationships

**Solution Strategy**:
1. Find the fixture that creates users with "test@example.com"
2. Replace with UUID-based emails: `email=f"test-{uuid4()}@example.com"`
3. Check both class-level and test-level fixtures

**Files to Edit**:
- test/db/unit/test_tag_models.py (TestTagRatingModel class setup)

---

### Group E: Other Duplicate Key Violations (3 failures)
**Issue**: Various duplicate key violations with hardcoded identifiers
**Files**: Multiple

- [ ] Fix test_postgres_fixtures.py::TestPostgresFixtures::test_multiple_commits_in_test (username="user1")
- [ ] Fix test_database_initializer.py::TestDatabaseInitializer::test_drop_tables_success (email="test@example.com")
- [ ] Fix test_static_data_loader.py::test_loads_user_notifications_csv (email="test@example.com")

**Solution Strategy**:
1. For each test, find where users are created
2. Replace hardcoded emails/usernames with UUID-based unique values
3. Example: `username=f"user-{uuid4()}"` or `username=f"user-{uuid4().hex[:8]}"`

**Files to Edit**:
- test/db/test_postgres_fixtures.py
- test/db/unit/test_database_initializer.py
- test/db/unit/test_static_data_loader.py

---

### Group F: test_database_integration.py Data Leakage (1 failure)
**Issue**: test_generation_job_lifecycle expects 1 job, gets 2
**Files**: test/db/integration/test_database_integration.py

- [ ] Fix TestDatabaseIntegration::test_generation_job_lifecycle

**Solution Strategy**:
1. This test creates its own database but sees jobs from previous tests
2. Add cleanup at start of test: `session.query(GenerationJob).delete(); session.commit()`
3. Or change assertion to be relative: `assert len(completed_jobs) >= 1`

**Files to Edit**:
- test/db/integration/test_database_integration.py (line ~340)

---

## Implementation Checklist

### Phase 1: Fix UUID-Based Identifiers (15 tests)
- [ ] Import uuid4 in all affected test files
- [ ] Group B: test_tag_repository.py TestTagRepositoryRatings (2 tests)
- [ ] Group D: test_tag_models.py TestTagRatingModel (7 tests)
- [ ] Group E: test_postgres_fixtures.py (1 test)
- [ ] Group E: test_database_initializer.py (1 test)
- [ ] Group E: test_static_data_loader.py (1 test)
- [ ] Run tests to verify fixes

### Phase 2: Fix Data Leakage Issues (5 tests)
- [ ] Group C: test_tag_repository.py hierarchy/search/stats (4 tests)
- [ ] Group F: test_database_integration.py lifecycle (1 test)
- [ ] Run tests to verify fixes

### Phase 3: Fix Database End-to-End (4 tests)
- [ ] Group A: Verify test_database_end_to_end.py setup_method fix
- [ ] If not fixed, apply the fix to remove URL-encoded schema
- [ ] Run tests to verify fixes

### Phase 4: Final Verification
- [ ] Run full test suite: `make test`
- [ ] Verify all 35 tests now pass
- [ ] Update this document with final results

## Key Files Reference

### Test Files to Edit
1. test/db/integration/test_database_end_to_end.py
2. test/db/integration/test_tag_repository.py
3. test/db/integration/test_database_integration.py
4. test/db/unit/test_tag_models.py
5. test/db/test_postgres_fixtures.py
6. test/db/unit/test_database_initializer.py
7. test/db/unit/test_static_data_loader.py

### Pattern to Search For
- Hardcoded emails: `"test@example.com"`, `"user@example.com"`, `"user2@example.com"`
- Hardcoded usernames: `"testuser"`, `"user1"`, `"user2"`

### Pattern to Replace With
```python
from uuid import uuid4

# For emails
email=f"test-{uuid4()}@example.com"
email=f"user-{uuid4()}@example.com"

# For usernames (use hex for shorter strings)
username=f"user-{uuid4().hex[:8]}"
username=f"test-{uuid4().hex[:8]}"
```

## Notes
- All tests pass individually, failures only occur when run in the full suite
- Root cause: PostgreSQL persistence + hardcoded identifiers = collisions
- The truncate tables hook helps but doesn't fix class-level isolation issues
- UUID-based identifiers will make tests truly isolated and repeatable
