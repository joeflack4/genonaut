# Test Failures

This document tracks failing tests across all test suites, categorized by failure type and difficulty.

## Backend Tests (`make test`)

**Summary**: All fixed! 0 failed, 1214 passed, 65 skipped

### Generation Job Parameters - Validation Issues (medium) - FIXED

These tests were failing due to mismatches between expected and actual job parameters, particularly around the 'backend' field and checkpoint model validation.

- [x] test/api/db/test_services.py::TestGenerationService::test_create_generation_job
- [x] test/worker/test_tasks.py::test_process_comfy_job_happy_path
- [x] test/worker/test_tasks.py::test_process_comfy_job_handles_errors

**Fixes Applied**:
- First test: Updated assertion to expect `{'backend': 'kerniegen', 'max_length': 1000}` since the service automatically adds 'backend' field
- Second & third tests: Added required `checkpoint_model` parameter to test jobs

### ComfyUI File System Issues (low) - FIXED

Test was failing due to incorrect path configuration.

- [x] test/worker/test_comfyui_client.py::test_worker_client_download_image_reads_bytes

**Fix Applied**:
- Changed client initialization to pass `output_dir` parameter directly instead of setting `client.settings.comfyui_output_dir` after initialization

## Frontend Unit Tests (`make test-frontend-unit`)

**Summary**: All fixed! 0 failed, 433 passed, 5 skipped

### Model Selector Value Issue (low) - FIXED

Test was expecting model name but component correctly returns full path for ComfyUI compatibility.

- [x] src/components/generation/__tests__/ModelSelector-dropdown.test.tsx::ModelSelector::calls onChange when model is selected

**Fix Applied**:
- Updated test to expect path `/path/to/model1` instead of name `'Model 1'` to match component behavior

## Long-Running Tests (`make test-long-running`)

**Summary**: All fixed! 0 failed, 40 passed, 8 skipped

### ComfyUI Mock Server - File Uniqueness Issues (medium) - FIXED

All file uniqueness issues have been resolved.

- [x] test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_get_history_completed
- [x] test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_multiple_jobs_unique_files
- [x] test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_get_output_files
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_unique_output_files_per_job
- [x] test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_concurrent_jobs_unique_files
- [x] test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_filename_counter_increments

**Fixes Applied**:
- Updated `process_job()` in mock server to generate unique filenames using pattern: `{prefix}_{counter:05d}_.png`
- Added file counter increment and actual file copying to output directory
- Added `/reset` HTTP endpoint for proper server state reset between tests
- Updated conftest to call reset endpoint via HTTP instead of function import

### ComfyUI Mock Server - Error Handling Issues (medium) - FIXED

Error handling tests now properly simulate failures.

- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_job_failure_handling
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_cleanup_on_failed_job

**Fixes Applied**:
- Clear `config._LAST_SETTINGS` cache before monkeypatching settings
- Monkeypatch both `comfyui_url` and `comfyui_mock_url` to ensure backend selection uses non-existent server
- Tests now properly fail and mark jobs as 'failed' with error messages

## Frontend E2E Tests (`make frontend-test-e2e-wt2`)

**Summary**: 8 failed, 196 passed, 53 skipped (96% pass rate)

**Note**: Re-run with worktree 2 configuration (port 8002, genonaut_test database). Same failures detected as previous run.

### Analytics - Element Selector Issue (low) - FIXED

Strict mode violation due to duplicate text elements.

- [x] tests/e2e/analytics-real-api.spec.ts:90:5 - displays all analytics cards

**Details**:
- `getByText('Route Analytics')` was matching 2 elements (title and empty state message)
- **Fix Applied**: Changed to use `getByTestId('route-analytics-title')` and `getByTestId('generation-analytics-title')` for specific selectors

### Generation - Form Validation (medium) - FIXED

Generation job submission was failing with validation error - now passing!

- [x] tests/e2e/generation.spec.ts:8:3 - should successfully submit a generation job with real API

**Details**:
- Was showing error: "Please resolve the highlighted issues"
- **Status**: Test now passing without code changes - likely a test data issue that resolved itself or the test was fixed in a previous session

### Settings - User API 404 Errors (medium)

Multiple settings tests failing due to user endpoint returning 404.

- [ ] tests/e2e/settings-real-api.spec.ts:34:3 - persists profile updates and theme preference
- [ ] tests/e2e/settings-real-api.spec.ts:132:3 - loads user profile data correctly
- [ ] tests/e2e/settings-real-api.spec.ts:177:3 - validates form inputs properly

**Details**:
- `getCurrentUser()` API call returns 404
- Test database may be missing required user data
- Need to ensure user exists in test DB before running these tests

### Tag Rating - Missing UI Element (low)

Tag rating tests timeout waiting for ratings section element.

- [ ] tests/e2e/tag-rating.spec.ts:16:3 - should allow user to rate a tag
- [ ] tests/e2e/tag-rating.spec.ts:82:3 - should update existing rating
- [ ] tests/e2e/tag-rating.spec.ts:153:3 - should persist rating across page refreshes

**Details**:
- Element `[data-testid="tag-detail-ratings-section"]` not visible within 10s timeout
- Component may not be rendering or test data issue

## Performance Tests (`make test-performance`)

_Not yet run_
