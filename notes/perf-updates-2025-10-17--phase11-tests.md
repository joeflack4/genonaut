# Phase 11 Test Fixes - SQLite to PostgreSQL Migration

## Overview
After migrating tests from SQLite to PostgreSQL, many tests are now failing. This document categorizes the failures and tracks fixes.

## Test Failure Categories

### Category 1: Missing `existing_tag` Variable (NameError) ✅ FIXED
**Root Cause**: The `existing_tag` fixture or variable is not defined in test scope after migration.
**Count**: 22 failures + 16 errors = 38 total

#### Failures
- [x] test/api/db/test_repositories.py::TestContentRepository::test_create_content
- [x] test/api/db/test_repositories.py::TestContentAutoRepository::test_create_auto_content
- [x] test/api/db/test_services.py::TestContentService::test_create_content_success
- [x] test/api/db/test_services.py::TestContentService::test_content_response_handles_missing_path_thumb
- [x] test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_match_any
- [x] test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_match_all
- [x] test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_uuid_filter
- [x] test/api/db/test_services.py::TestContentService::test_get_unified_content_tag_objects_filter
- [x] test/api/db/test_services.py::TestContentAutoService::test_create_auto_content_success
- [x] test/api/test_content_endpoints.py::test_unified_content_filters_by_single_tag_name
- [x] test/api/test_content_endpoints.py::test_unified_content_tag_match_all_requires_all_tags
- [x] test/api/test_content_tag_filtering_integration.py::test_create_and_query_with_single_tag
- [x] test/api/test_content_tag_filtering_integration.py::test_query_with_multiple_tags_any_logic
- [x] test/api/test_content_tag_filtering_integration.py::test_query_with_multiple_tags_all_logic
- [x] test/api/test_content_tag_filtering_integration.py::test_query_varied_tag_combinations
- [x] test/api/test_unified_content_pagination.py::test_pagination_page_beyond_total_pages
- [x] test/api/test_unified_content_pagination.py::test_pagination_page_size_greater_than_total_items
- [x] test/api/test_unified_content_pagination.py::test_pagination_page_size_one
- [x] test/api/test_unified_content_pagination.py::test_pagination_boundary_exact_page_size
- [x] test/api/test_unified_content_pagination.py::test_pagination_second_page_has_correct_offset
- [x] test/api/test_unified_content_pagination.py::test_pagination_with_filters_applied
- [x] test/db/integration/test_database_integration.py::TestDatabaseIntegration::test_user_content_relationship_integrity

#### Errors (tests that failed to run due to setup failure)
- [x] test/api/db/test_repositories.py::TestContentRepository::test_get_content_by_creator
- [x] test/api/db/test_repositories.py::TestContentRepository::test_get_content_by_type
- [x] test/api/db/test_repositories.py::TestContentRepository::test_search_content_by_title
- [x] test/api/db/test_repositories.py::TestContentRepository::test_update_quality_score
- [x] test/api/db/test_repositories.py::TestInteractionRepository::test_create_interaction
- [x] test/api/db/test_repositories.py::TestInteractionRepository::test_get_user_interactions
- [x] test/api/db/test_repositories.py::TestInteractionRepository::test_get_content_interactions
- [x] test/api/db/test_repositories.py::TestInteractionRepository::test_get_interactions_by_type
- [x] test/api/db/test_repositories.py::TestRecommendationRepository::test_create_recommendation
- [x] test/api/db/test_repositories.py::TestRecommendationRepository::test_get_user_recommendations
- [x] test/api/db/test_repositories.py::TestRecommendationRepository::test_get_unserved_recommendations
- [x] test/api/db/test_repositories.py::TestRecommendationRepository::test_mark_as_served
- [x] test/api/db/test_services.py::TestUserService::test_get_user_statistics
- [x] test/api/db/test_services.py::TestContentService::test_search_content
- [x] test/api/db/test_services.py::TestContentService::test_update_content_quality
- [x] test/api/db/test_services.py::TestContentService::test_get_content_analytics
- [x] test/api/db/test_services.py::TestContentService::test_content_response_includes_path_thumb
- [x] test/api/db/test_services.py::TestContentService::test_get_unified_content_paginated_includes_path_thumb
- [x] test/api/db/test_services.py::TestContentAutoService::test_auto_content_list_filters
- [x] test/api/db/test_services.py::TestInteractionService::test_record_interaction
- [x] test/api/db/test_services.py::TestInteractionService::test_record_interaction_invalid_user
- [x] test/api/db/test_services.py::TestInteractionService::test_get_user_behavior_analytics
- [x] test/api/db/test_services.py::TestRecommendationService::test_create_recommendation
- [x] test/api/db/test_services.py::TestRecommendationService::test_generate_recommendations_for_user
- [x] test/api/db/test_services.py::TestRecommendationService::test_get_served_recommendations
- [x] test/api/db/test_services.py::TestRecommendationService::test_bulk_create_recommendations
- [x] test/api/db/test_services.py::TestGenerationService::test_complete_job

### Category 2: Foreign Key Violations (DatabaseError)
**Root Cause**: Tests inserting records with hardcoded IDs that don't exist in related tables.
**Count**: 2 failures

- [x] test/api/unit/test_notification_service.py::TestNotificationService::test_create_job_completion_notification
- [x] test/api/unit/test_notification_service.py::TestNotificationService::test_create_job_failure_notification

### Category 3: PostgreSQL Database Creation Failures ✅ FIXED
**Root Cause**: Tests trying to use tempfile paths as PostgreSQL database names (psql failed with return code 2).
**Count**: 5 failures

- [x] test/db/integration/test_database_end_to_end.py::TestDatabaseEndToEnd::test_complete_database_initialization_with_all_options
- [x] test/db/integration/test_database_end_to_end.py::TestDatabaseEndToEnd::test_database_initialization_without_seeding
- [x] test/db/integration/test_database_end_to_end.py::TestDatabaseEndToEnd::test_database_initialization_with_drop_existing
- [x] test/db/integration/test_database_end_to_end.py::TestDatabaseEndToEnd::test_database_schema_validation
- [x] test/db/integration/test_database_end_to_end.py::TestDatabaseEndToEnd::test_database_relationships_work_end_to_end

### Category 4: Duplicate Key Violations (IntegrityError)
**Root Cause**: PostgreSQL doesn't auto-rollback on errors like SQLite; test isolation issues with unique constraints.
**Count**: 4 failures + 18 errors = 22 total

#### Failures
- [x] test/db/integration/test_tag_repository.py::TestTagRepositoryRatings::test_get_tag_average_rating
- [x] test/db/integration/test_tag_repository.py::TestTagRepositoryRatings::test_get_tags_sorted_by_rating
- [x] test/db/test_postgres_fixtures.py::TestPostgresFixtures::test_multiple_commits_in_test
- [x] test/db/unit/test_database_initializer.py::TestDatabaseInitializer::test_drop_tables_success

#### Errors
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_user_defaults
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_content_item_creation
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_content_item_auto_creation
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_content_item_creator_relationship
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_content_item_auto_creator_relationship
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_user_interaction_creation
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_user_interaction_relationships
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_recommendation_creation
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_generation_job_creation
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_generation_job_with_result
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_model_timestamps
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_generation_job_backward_compatibility_aliases
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_checkpoint_model_path_unique_constraint
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_lora_model_path_unique_constraint
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_tag_rating_creation
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_tag_rating_unique_constraint
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_tag_rating_allows_half_stars
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_tag_rating_foreign_keys
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_multiple_users_can_rate_same_tag
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_user_can_rate_multiple_tags
- [x] test/db/unit/test_tag_models.py::TestTagRatingModel::test_tag_rating_relationships
- [x] test/db/unit/test_static_data_loader.py::test_loads_user_notifications_csv

### Category 5: Missing Test Fixture Attributes ✅ FIXED
**Root Cause**: Test class setup not properly executed (missing self.engine).
**Count**: 12 errors

- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_create_flagged_content
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_by_id
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_by_id_not_found
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_by_content_item
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_paginated_no_filters
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_paginated_with_creator_filter
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_paginated_with_risk_score_filter
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_paginated_with_reviewed_filter
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_paginated_sorting
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_update_review_status
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_update_review_status_not_found
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_delete_not_found
- [x] test/db/unit/test_flagged_content_repository.py::TestFlaggedContentRepository::test_get_statistics

### Category 6: JSONB Type with SQLite (CompileError) ✅ FIXED
**Root Cause**: Tests still using SQLite instead of PostgreSQL, but schema now has JSONB types.
**Count**: 11 errors (regular) + 9 errors (long-running) = 20 total

#### Regular Tests
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_comfyui_client_health_check
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_simple_generation_request_creation
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_comfyui_workflow_submission
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_batch_generation
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_generation_with_lora_request
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_thumbnail_paths_in_request
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_generation_cancellation_request
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_different_image_dimensions_request[256-256]
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_different_image_dimensions_request[512-768]
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_different_image_dimensions_request[768-512]
- [x] test/integrations/comfyui/test_comfyui_mock_class_generation.py::TestComfyUIIntegration::test_different_image_dimensions_request[1024-1024]

#### Long-Running Tests
- [x] test/api/stress/test_pagination_stress.py::TestPaginationStress::test_pagination_with_large_dataset
- [x] test/api/stress/test_pagination_stress.py::TestPaginationStress::test_deep_pagination_performance
- [x] test/integrations/comfyui/test_comfyui_mock_class_load_testing.py::TestComfyUILoadTesting::test_generation_queue_processing_under_load
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_complete_workflow_manual
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_job_status_updates
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_file_organization
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_thumbnail_generation
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_content_item_creation
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_multiple_jobs_sequential
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_unique_output_files_per_job
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_job_failure_handling
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_cleanup_on_failed_job

### Category 7: PostgreSQL Connection Failures (Long-Running) ✅ FIXED
**Root Cause**: Tests trying to create databases with invalid names (tempfile paths).
**Count**: 6 errors

- [x] test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_seed_database_from_tsv_files
- [x] test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_seed_database_with_custom_input_dir
- [x] test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_database_relationships_after_seeding
- [x] test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_json_field_parsing
- [x] test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_boolean_field_parsing
- [x] test/db/integration/test_database_seeding.py::TestDatabaseSeeding::test_numeric_field_parsing

### Category 8: Other Failures
**Count**: 2 failures

- [x] test/db/integration/test_database_integration.py::TestDatabaseIntegration::test_generation_job_lifecycle - Assert error (expected 1, got 2 generation jobs)
- [x] test/db/unit/test_schema.py::TestSchemaModels::test_user_unique_constraints - Did not raise IntegrityError

## Summary Statistics
- Total test failures: 0
- Total test errors: 0
- Total issues: 0
- **Fixed**: 108 (38 + 2 + 5 + 22 + 12 + 20 + 6 + 2 + 1)
- **Deferred**: 0
- **Remaining**: 0

## Skip/Delete Candidates

None currently. Will re-evaluate if fixes prove too difficult.

## Progress Tracking

### Category 1: Missing `existing_tag` - 38 items
- Fixed: 38 (Fixed conftest.py line 161 - missing newline)
- Remaining: 0

### Category 2: Foreign Key Violations - 2 items
- Fixed: 2 (Added fixtures for test_generation_job and test_content_item)
- Remaining: 0

### Category 3: PostgreSQL Database Creation - 5 items ✅ FIXED
- Fixed: 5 (Updated test_database_end_to_end.py to use proper PostgreSQL schema)
- Remaining: 0

### Category 4: Duplicate Key Violations - 22 items ✅ FIXED
- Fixed: 22 (Replaced hardcoded identifiers with UUID-based values and added per-test cleanup where needed)
- Remaining: 0

### Category 5: Missing Fixture Attributes - 12 items ✅ FIXED
- Fixed: 12 (Removed teardown_method that referenced non-existent self.engine)
- Remaining: 0

### Category 6: JSONB/SQLite Incompatibility - 20 items ✅ FIXED
- Fixed: 20 (Updated conftest.py files to use postgres_session instead of SQLite)
  - test/integrations/comfyui/conftest.py
  - test/api/stress/conftest.py
- Remaining: 0

### Category 7: PostgreSQL Connection Failures - 6 items ✅ FIXED
- Fixed: 6 (Updated test_database_seeding.py to use proper PostgreSQL schema)
- Remaining: 0

### Category 8: Other - 2 items ✅ FIXED
- Fixed: 2 (Scoped assertions to test-generated data and ensured fixtures raise the expected IntegrityError)
- Remaining: 0

## Fix Strategies

### For Category 1 (Missing `existing_tag`)
Need to investigate the fixture setup for tags. Likely need to add a fixture or modify test setup.

### For Category 2 (Foreign Key Violations)
Update tests to create actual related records instead of using hardcoded IDs.

### For Category 3 & 7 (PostgreSQL Database Creation)
Update test fixtures to use proper PostgreSQL test schema naming instead of tempfile paths.

### For Category 4 (Duplicate Key Violations)
Ensure proper transaction rollback and test isolation with PostgreSQL.

### For Category 5 (Missing Fixture Attributes)
Fix test class setup methods to properly initialize engine and session.

### For Category 6 (JSONB/SQLite)
Convert tests to use PostgreSQL instead of SQLite.

### For Category 8 (Other)
Investigate each case individually.



# Phase 11 - Remaining Test Fixes (35 tests)

## Current Status
- **Total Tests**: 1127
- **Passing**: 1065 (95%)
- **Failing**: 0
- **Errors**: 0
- **Total Issues**: 0

## Environment Notes
- `config/local-test.json` test database persists between runs and is already initialized; skip `make init-test` unless data corruption is suspected.
- `config/local-test-init.json` is dedicated to initialization/seeding tests and should be created and torn down automatically during suites that cover that workflow.
- If test data appears incorrect, either rebuild the `local-test` database (once sandbox connectivity allows) or adjust fixtures/tests to accommodate the current dataset.
- Current sandbox restrictions prevent direct `psql`/`pg_isready` calls, so rely on test execution to surface connectivity issues.

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

- [x] Fix test_database_initialization_without_seeding
- [x] Fix test_database_initialization_with_drop_existing
- [x] Fix test_database_schema_validation
- [x] Fix test_database_relationships_work_end_to_end

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

- [x] Fix TestTagRepositoryRatings::test_get_tag_average_rating
- [x] Fix TestTagRepositoryRatings::test_get_tags_sorted_by_rating

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

- [x] Fix TestTagRepositoryHierarchy::test_get_root_tags (expects 2, gets 5)
- [x] Fix TestTagRepositorySearch::test_get_all_paginated (expects 6, gets 9)
- [x] Fix TestTagRepositorySearch::test_get_all_paginated_page_2 (pagination off)
- [x] Fix TestTagRepositoryStatistics::test_get_hierarchy_statistics (expects 6, gets 9)

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

- [x] Fix TestTagRatingModel::test_tag_rating_creation
- [x] Fix TestTagRatingModel::test_tag_rating_unique_constraint
- [x] Fix TestTagRatingModel::test_tag_rating_allows_half_stars
- [x] Fix TestTagRatingModel::test_tag_rating_foreign_keys
- [x] Fix TestTagRatingModel::test_multiple_users_can_rate_same_tag
- [x] Fix TestTagRatingModel::test_user_can_rate_multiple_tags
- [x] Fix TestTagRatingModel::test_tag_rating_relationships

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

- [x] Fix test_postgres_fixtures.py::TestPostgresFixtures::test_multiple_commits_in_test (username="user1")
- [x] Fix test_database_initializer.py::TestDatabaseInitializer::test_drop_tables_success (email="test@example.com")
- [x] Fix test_static_data_loader.py::test_loads_user_notifications_csv (email="test@example.com")

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

- [x] Fix TestDatabaseIntegration::test_generation_job_lifecycle

**Solution Strategy**:
1. This test creates its own database but sees jobs from previous tests
2. Add cleanup at start of test: `session.query(GenerationJob).delete(); session.commit()`
3. Or change assertion to be relative: `assert len(completed_jobs) >= 1`

**Files to Edit**:
- test/db/integration/test_database_integration.py (line ~340)

---

## Implementation Checklist

### Phase 1: Fix UUID-Based Identifiers (15 tests)
- [x] Import uuid4 in all affected test files
- [x] Group B: test_tag_repository.py TestTagRepositoryRatings (2 tests)
- [x] Group D: test_tag_models.py TestTagRatingModel (7 tests)
- [x] Group E: test_postgres_fixtures.py (1 test)
- [x] Group E: test_database_initializer.py (1 test)
- [x] Group E: test_static_data_loader.py (1 test)
- [x] Run tests to verify fixes *(targeted suites now pass under `ENV_TARGET=local-test`)*

### Phase 2: Fix Data Leakage Issues (5 tests)
- [x] Group C: test_tag_repository.py hierarchy/search/stats (4 tests)
- [x] Group F: test_database_integration.py lifecycle (1 test)
- [x] Run tests to verify fixes *(lifecycle assertion updated to use UUID-prefixed username)*

### Phase 3: Fix Database End-to-End (4 tests)
- [x] Group A: Verify test_database_end_to_end.py setup_method fix
- [x] If not fixed, apply the fix to remove URL-encoded schema
- [x] Run tests to verify fixes *(end-to-end suite passes with `auto_seed=False` and post-test restoration)*

### Phase 4: Final Verification
- [x] Run full test suite: `make test`
- [x] Verify all 35 tests now pass
- [x] Update this document with final results

## Progress Summary (latest)
- Added dedicated `.env` fixtures under `test/api/unit/input/config_precedence/env/` so the config precedence suite exercises the documented load order (base → env JSON → shared env → env target → process env → local overrides).
- Introduced `auto_seed` flag on `initialize_database` to make seeding optional for tests that need empty tables while keeping automatic seeding for dev/demo flows; updated unit tests to cover both seeded and non-seeded paths.
- End-to-end database tests now run with `auto_seed=False` and restore the canonical seeded dataset after each case, preventing downstream suites from observing empty tables.
- Hardened `DatabaseInitializer.drop_tables()` to tolerate missing legacy schemas, fall back to manual drops, and always reset the search path so follow-on migrations succeed.
- Generation lifecycle integration test now uses UUID-prefixed usernames and narrows assertions to the job/user under test, avoiding global deletes that previously wiped shared fixtures.
- Full `make test` (ENV_TARGET=local-test) completes with `1065 passed, 62 skipped, 50 deselected` (pytest exit success; the CLI command hit the harness timeout after reporting the summary).

## Current Failures (2025-10-20 run)
- None — targeted runs and full `make test` complete without failures.

## Key Files Reference

### Test Files to Edit
1. test/api/unit/input/config_precedence/env/.env.shared
2. test/api/unit/input/config_precedence/env/.env.test-env
3. test/api/unit/input/config_precedence/env/.env
4. test/db/integration/test_database_end_to_end.py
5. test/db/integration/test_database_integration.py
6. test/db/unit/test_database_initializer.py
7. test/db/utils.py

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

## Follow-ups
- [x] Document `local-test-init.json` usage in `docs/testing.md` if it remains undocumented.

## Notes
- `initialize_database(auto_seed=False)` is now the supported way to stand up an empty schema inside tests; callers must restore the seeded dataset afterwards if later suites depend on fixtures.
- Config precedence tests rely on the new sample env files; keep them in sync with the documented load order when adding future precedence cases.
- Avoid global table wipes in database integration tests—prefer scoping assertions (filtering by the resources created in each test) to preserve the seeded dataset for the remainder of the run.
- Continue using UUID-based identifiers in fixtures to prevent cross-suite collisions when the PostgreSQL database retains state between tests.
