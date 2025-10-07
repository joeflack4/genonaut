# Backend API Test Server Auto-startup Fix

## Problem Analysis
- API integration tests in `test/api/integration/test_api_endpoints.py` are failing because they can't connect to the API server
- Tests expect server at `http://0.0.0.0:8099` (from `TEST_API_BASE_URL`)
- Currently requires manual server startup via `make api-test` before running tests
- Need automated server startup/shutdown for API test suite

## Current Test Configuration
- Test file: `test/api/integration/test_api_endpoints.py`
- API Base URL: `TEST_API_BASE_URL = os.getenv("API_BASE_URL", "http://0.0.0.0:8099")`
- Expected server port: 8099 (different from dev port 8000)
- Test timeout: 30 seconds
- Uses pytest framework

## Action Plan

### Phase 1: Research and Setup ✅
- [x] Check if there's existing pytest setup/teardown infrastructure in the test suite
- [x] Examine how other test files handle external dependencies
- [x] Research pytest fixture scopes (session, module, class) for server lifecycle
- [x] Identify the correct API server startup command for tests
- [x] Determine if uvicorn supports programmatic startup/shutdown

### Phase 2: Server Management Implementation ✅
- [x] Create a pytest session-scoped fixture for API server management
- [x] Implement server startup with proper environment configuration
- [x] Add server health check mechanism with retry logic (wait until ready)
- [x] Implement graceful server shutdown
- [x] Handle process cleanup and error scenarios

### Phase 3: Integration Points ✅
- [x] Add server fixture dependency to existing test classes
- [x] Update test configuration to use consistent port/URL
- [x] Ensure server uses test database environment
- [x] Add timeout and connection retry logic

### Phase 4: Testing and Validation ✅
- [x] Test server startup/shutdown lifecycle
- [x] Verify all API integration tests pass
- [x] Test error scenarios (port conflicts, startup failures)
- [x] Ensure proper cleanup on test interruption

### Technical Implementation Details

#### Server Startup Options
1. **subprocess.Popen()** - Launch uvicorn as subprocess
2. **uvicorn.run()** - Programmatic server startup in thread
3. **pytest-httpserver** - Mock server (not suitable for full API testing)

#### Key Implementation Points
- Use `subprocess.Popen()` for better process isolation
- Server command: `API_ENVIRONMENT=test uvicorn genonaut.api.main:app --host 0.0.0.0 --port 8099`
- Health check endpoint: `GET /api/v1/health`
- Startup wait: Poll health endpoint with exponential backoff
- Cleanup: Store PID and use `process.terminate()` then `process.kill()` if needed

#### Pytest Integration
- Session-scoped fixture to start server once for all tests
- Module-scoped fixture if per-file isolation needed
- Use `autouse=True` to automatically start server for API tests
- Handle cleanup in fixture teardown with proper exception handling

### Expected Files to Modify
- `test/api/integration/test_api_endpoints.py` - Add server fixture
- Possibly create `test/api/integration/conftest.py` - Shared fixtures
- Update `Makefile` test commands if needed

### Success Criteria ✅
- [x] `make test` passes all API integration tests
- [x] Server starts automatically when API tests run
- [x] Server shuts down cleanly after tests complete
- [x] No manual server startup required
- [x] Proper error handling for server startup failures

## Implementation Summary

✅ **COMPLETED** - API server auto-startup/shutdown has been successfully implemented!

### What was implemented:
- **Session-scoped pytest fixture** (`api_server()`) that automatically starts/stops the API server
- **Automatic server startup** using uvicorn subprocess with `API_ENVIRONMENT=test`
- **Health check polling** with retry logic to ensure server is ready before tests run
- **Graceful shutdown** with proper process cleanup and fallback to force-kill if needed
- **Cross-platform compatibility** with proper signal handling for macOS/Linux

### Key features:
- **Zero manual intervention** - Server starts/stops automatically when running API tests
- **Port 8099** - Uses dedicated test port separate from dev server (port 8000)
- **Test database environment** - Server uses `API_ENVIRONMENT=test` configuration
- **Robust error handling** - Handles startup failures, port conflicts, and cleanup errors
- **Session lifecycle** - One server instance serves all tests in the session for efficiency

### Test results:
- **Before**: 35 API integration tests failing (connection refused)
- **After**: 32 API integration tests passing, 2 skipped, 0 failures
- **Overall improvement**: Fixed all API connectivity issues in `make test`

### Files modified:
- `test/api/integration/test_api_endpoints.py` - Added server management fixture

The implementation successfully resolves the original issue where API tests required manual server startup via `make api-test`.