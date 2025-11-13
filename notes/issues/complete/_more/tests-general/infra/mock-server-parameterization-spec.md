# Mock ComfyUI Server Parameterization - Spec

## Overview
The mock ComfyUI server currently uses "static return" mode - it returns the same input image path for all generation requests. This works well for deployed test infrastructure but breaks tests that verify unique file generation per job.

**Solution**: Add optional `--disable-static-return` flag to enable dynamic file generation mode.

## Behavior Modes

### Mode 1: Static Return (DEFAULT - current behavior)
- **When**: No `--disable-static-return` flag passed
- **Behavior**: Return path to input image directly: `'../input/kernie_512x768.jpg'`
- **Use case**: Deployed test infrastructure, tests that don't care about unique files
- **Performance**: Fast, no file I/O

### Mode 2: Dynamic Generation (NEW)
- **When**: `--disable-static-return` flag passed
- **Behavior**: Copy input image to output directory with unique filename
  - Generate unique filename using prompt_id or counter
  - Pattern: `output/<prefix>_<unique_id>.png`
  - Return the new output file path
- **Use case**: Tests verifying unique file generation, file naming patterns, concurrent job handling
- **Performance**: Slower due to file copying

## Implementation Tasks

### Phase 1: Mock Server Changes
- [x] Update mock server CLI to accept `--disable-static-return` flag
  - File: `test/_infra/mock_services/comfyui/server.py`
  - Add argparse parameter for the flag
  - Store flag state in server instance

- [x] Modify image generation endpoint to support both modes
  - Check if `--disable-static-return` flag is set
  - If TRUE (dynamic mode):
    - Generate unique filename based on counter
    - Copy `input/kernie_512x768.jpg` to `output/<unique_name>.png`
    - Return output path in history response
  - If FALSE (static mode - default):
    - Return `'../input/kernie_512x768.jpg'` directly (current behavior)

### Phase 2: Pytest Fixture Updates
- [x] Update `mock_comfyui_server` fixture in `test/_infra/mock_services/comfyui/conftest.py`
  - Added `disable_static_return` parameter to `_start_mock_server` helper
  - Pass `--disable-static-return` flag to server startup if parameter is True

- [x] Create variant fixture (optional but recommended)
  - Created `mock_comfyui_server_dynamic`, `mock_comfyui_url_dynamic`, `mock_comfyui_client_dynamic` fixtures
  - Created `mock_comfyui_config_dynamic` for E2E tests
  - Makes test code cleaner

### Phase 3: Test Updates
- [x] Update failing tests to use dynamic mode:
  - `test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_get_history_completed`
  - `test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_multiple_jobs_unique_files`
  - `test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_get_output_files`
  - `test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_unique_output_files_per_job`
  - `test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_file_naming_pattern`
  - `test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_concurrent_jobs_unique_files`
  - `test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_filename_counter_increments`

- [x] Update each test to:
  - Use `*_dynamic` fixtures with local variable aliases for minimal code changes
  - All tests updated and verified passing

### Phase 4: Server Restart & Verification
- [x] Kill existing mock ComfyUI server process (if running)
  - Not needed - fixtures handle server lifecycle automatically

- [x] Run one failing test to verify the fix works
  - Ran: `pytest test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_file_naming_pattern -xvs`
  - Result: PASSED

- [x] Run all 7 failing tests to verify complete fix
  - All 7 tests passed in 31.59s

- [ ] Run full long-running test suite to ensure no regressions
  - `make test-long-running-wt2`
  - Verify: 40 passed, 8 skipped, 0 failed

## Technical Details

### File Structure
```
test/_infra/mock_services/comfyui/
├── input/
│   └── kernie_512x768.jpg          # Source image
├── output/
│   └── <generated files>.png       # Dynamically generated (when flag set)
├── mock_server.py                   # Server implementation
└── conftest.py                      # Pytest fixtures
```

### Unique Filename Generation Strategy
Options (choose one):
1. **Prompt ID based**: `output/{prefix}_{prompt_id}.png`
2. **Counter based**: `output/{prefix}_{counter:05d}.png`
3. **Timestamp based**: `output/{prefix}_{timestamp}.png`

Recommendation: **Prompt ID based** - aligns with ComfyUI's actual behavior and ensures uniqueness per request.

### Fixture Scope Consideration
- Current fixture scope: Likely `session` or `module`
- Keep same scope to avoid slowdown
- Server state (counter) should persist across tests in same session

## Testing Strategy

### Verification Tests
After implementation, verify:
1. Static mode still works for existing tests (default behavior)
2. Dynamic mode generates unique files for each request
3. File naming follows expected pattern
4. Concurrent requests generate different files
5. No test suite slowdown

### Rollback Plan
If issues arise:
1. Revert mock server changes
2. Mark failing tests as `@pytest.mark.skip` with reason
3. File issue for future investigation

## Notes

- **Why not always use dynamic mode?** Performance and deployed infrastructure expectations
- **Why not fix tests to work with static mode?** Tests are validating real ComfyUI behavior (unique file generation)
- **File cleanup**: Dynamic mode should cleanup generated files after test suite (implement in fixture teardown)

## Success Criteria
- [x] All 7 previously failing long-running tests pass (verified: 7 passed in 31.59s)
- [x] Documentation updated in test files explaining when to use each mode (docstrings added to dynamic fixtures and tests)
