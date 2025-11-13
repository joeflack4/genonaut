# Test Failures - Long-Running Tests (test-long-running)

This document tracks failures from the long-running test suite.

## Test Suite: Backend Long-Running Tests (test-long-running-wt2)

**Results**: 33 passed, 8 skipped, 7 failed (different tests)
**Run time**: ~413s (6:53 minutes)
**Last updated**: 2025-11-13

**Status**: ORIGINALLY REPORTED TESTS NOW PASSING

### ComfyUI Error Recovery Tests (medium) - RESOLVED

**Root cause**: Tests were failing due to monkeypatch issues with settings, but are now working correctly.

**Resolution**: Both error recovery tests are now PASSING. The error handling properly marks jobs as 'failed' when connection errors occur.

**Affected tests**:
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_job_failure_handling
- [x] test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_cleanup_on_failed_job

**Note**: The long-running test suite now shows 7 DIFFERENT failures related to output file paths (not the tests listed above). These are unrelated to the originally reported error recovery issues and appear to be pre-existing or newly introduced file path collection issues in the ComfyUI client.
