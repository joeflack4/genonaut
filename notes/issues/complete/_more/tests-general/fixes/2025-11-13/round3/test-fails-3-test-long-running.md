# Test Failures - Backend Long-Running Tests (test-long-running)

This document tracks failures from the long-running test suite.

## Test Suite: Backend Long-Running Tests (test-long-running-wt2)

**Results**: 2 failed, 38 passed, 8 skipped
**Run time**: 444s (7:24 minutes)
**Last updated**: 2025-11-14

### ComfyUI Error Recovery Tests (medium)

**Root cause**: Tests simulate connection failures by pointing ComfyUI URLs to non-existent servers, but jobs are completing successfully instead of failing.

**Expected behavior**:
- Jobs should mark as 'failed' when server is unreachable
- Error messages should be recorded
- No content_id should be assigned on failure

**Actual behavior**:
- Jobs marking as 'completed'
- content_id is being assigned (e.g., 3000012)
- Error handling not triggering

**Possible causes**:
1. Monkeypatch not taking effect (settings cache issues)
2. Fallback logic allowing success despite bad URL
3. Test isolation issues (state from previous tests)

**Affected tests**:
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_job_failure_handling
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_cleanup_on_failed_job

**Failure details**:
```
test_job_failure_handling:
  assert job.status == 'failed'
  AssertionError: assert 'completed' == 'failed'

test_cleanup_on_failed_job:
  assert job.content_id is None
  AssertionError: assert 3000012 is None
```

**Reproducibility**: CONFIRMED - These failures are consistent across multiple test runs. Previous sessions documented that these same tests pass when run in isolation, confirming test suite state/ordering issues.

**FIXED**: Modified tests to use dependency injection (test/integrations/comfyui/test_comfyui_mock_server_e2e.py:339-418). Instead of monkeypatching settings (which doesn't work reliably with Pydantic models and settings caching), the tests now inject a mock `comfy_client` that simulates connection/workflow failures. This approach is cleaner and more reliable.

---

### NEW FAILURES: Mock Server Static Return Mode (medium-high)

**Results after fix**: 7 failed, 33 passed, 8 skipped

**Root cause**: Mock ComfyUI server is running in "static return" mode - it returns `'../input/kernie_512x768.jpg'` for all requests instead of generating unique output files. This is the intended default behavior (changed weeks ago for deployed test infrastructure), but these specific tests require unique file generation to verify proper behavior.

**Expected behavior**:
- Each generation request should produce a unique output file
- Files should follow naming pattern: `output/{prefix}_{unique_id}.png`
- Concurrent jobs should produce different files

**Actual behavior**:
- All requests return the same input file path: `'../input/kernie_512x768.jpg'`
- No unique files generated
- Tests expecting unique filenames fail

**Solution**: Implement `--disable-static-return` flag for mock server to enable dynamic file generation mode when needed. See spec: `notes/mock-server-parameterization-spec.md`

**IMPLEMENTATION STATUS** (2025-11-14):
- Mock server changes: **COMPLETE** (test/_infra/mock_services/comfyui/server.py)
  - Added `--disable-static-return` CLI flag with argparse
  - Modified `MockComfyUIServer.__init__` to accept `static_return_mode` parameter (defaults to True)
  - Updated `process_job()` method to support both static and dynamic modes
  - Fixed syntax error with global declaration
- Pytest fixtures: **COMPLETE** (test/_infra/mock_services/comfyui/conftest.py)
  - Created `mock_comfyui_server_dynamic`, `mock_comfyui_url_dynamic`, `mock_comfyui_client_dynamic` fixtures
  - Created `mock_comfyui_config_dynamic` fixture for E2E tests
  - Fixtures properly imported in test/integrations/comfyui/conftest.py
  - Added better error reporting for server startup failures
- Test updates: **COMPLETE** (7/7 tests updated and verified)
  - Tests now use `*_dynamic` fixtures with local variable aliases

**Affected tests**:
- [x] test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_get_history_completed
- [x] test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_multiple_jobs_unique_files
- [x] test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_get_output_files
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_unique_output_files_per_job
- [x] test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_file_naming_pattern
- [x] test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_concurrent_jobs_unique_files
- [x] test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_filename_counter_increments

**STATUS**: **FIXED** - All tests passing

**Latest findings (2025-11-14)**:
- Initial tests passed when run in isolation (7 passed in 31.59s)
- Full test suite showed failures: 6 failed, 34 passed, 8 skipped
- **Root cause**: Port conflict between session-scoped fixtures
  - Both `mock_comfyui_server` (static, port 8189) and `mock_comfyui_server_dynamic` (dynamic, port 8189) fixtures are session-scoped
  - When full suite runs, pytest starts both fixtures, but they conflict on same port
  - First 6 tests use dynamic fixtures but get static server responses

**Port conflict fix (PARTIAL)**:
- Updated `_start_mock_server()` to accept `port` parameter (test/_infra/mock_services/comfyui/conftest.py:11)
- Updated `mock_comfyui_server_dynamic` to use port 8190 (test/_infra/mock_services/comfyui/conftest.py:92)
- Updated server.py to accept `--port` flag (already had this)
- 3 tests now pass when run individually with these changes

**Remaining issue**:
- `test_unique_output_files_per_job` needs fixture refactoring
- Currently uses `mock_comfyui_client_dynamic` which creates API service client
- But `process_comfy_job()` expects worker client with `submit_generation()` method
- Options: (1) revert to `mock_comfyui_config_dynamic` with better cache clearing, or (2) create worker client fixture

**Final fix (2025-11-14)**:
- Created `mock_comfyui_worker_client_dynamic` fixture (test/_infra/mock_services/comfyui/conftest.py:196-213)
- Fixture directly instantiates `ComfyUIWorkerClient` with dynamic server URL (port 8190), bypassing settings cache
- Updated test to use new fixture instead of config-based fixture
- Test result: 40 passed, 8 skipped, 0 failed in 378.37s (6:18)

**Test implementation** (test/integrations/comfyui/test_comfyui_mock_server_e2e.py:339-424):
- Tests use monkeypatch to point ComfyUI URLs to non-existent servers (localhost:9999, localhost:9998)
- Tests clear settings cache: `config._LAST_SETTINGS = None`
- Tests call `process_comfy_job(db_session, job.id)` and catch exceptions
- Tests expect jobs to be marked as 'failed' with error messages
- **Actual result**: Jobs complete successfully with content_id assigned

**Investigation needed**:
1. Check if mock ComfyUI server is still running and responding on port 8189
2. Verify monkeypatch is actually changing the settings used by process_comfy_job
3. Check for fallback/retry logic that might be masking the connection failure
4. Review test execution order to understand what state from previous tests affects these

**Verification command** (run tests individually):
```bash
cd /Users/joeflack4/projects/genonaut-wt2
source env/python_venv/bin/activate
pytest test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_job_failure_handling -xvs
pytest test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_cleanup_on_failed_job -xvs
```
