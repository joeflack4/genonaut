# Route analytics

## Implementation tasks
- [x] Phase 1: Middleware and Redis storage
  - [x] Create RouteAnalyticsMiddleware in genonaut/api/middleware/route_analytics.py
  - [x] Implement Redis Stream writes
  - [x] Add query parameter normalization logic
  - [x] Test performance impact (target: < 1ms overhead)
  - [x] Add middleware to FastAPI app in main.py

- [x] Phase 2: PostgreSQL schema and configuration
  - [x] Create Alembic migration for route_analytics table
  - [x] Create Alembic migration for route_analytics_hourly table
  - [x] Add indexes as specified in schema
  - [x] Add cache-planning configuration to config/base.json
  - [x] Test migration on demo database
  - [x] Apply to all environments (dev, demo, test)

- [x] Phase 3: Celery tasks
  - [x] Implement transfer_route_analytics_to_postgres task (runs every 10 min)
  - [x] Implement aggregate_route_analytics_hourly task (runs hourly)
  - [x] Add tasks to config/base.json Celery Beat schedule
  - [ ] Test tasks manually
  - [ ] Verify data flow: Redis -> PostgreSQL -> Hourly aggregation

- [x] Phase 4: CLI tools for cache analysis (TWO SYSTEMS)
  - [x] System 1: Absolute thresholds (genonaut/cli/cache_analysis.py)
    - [x] Implement get_top_routes_for_caching(n, lookback_days, min_requests, min_latency)
    - [x] Add cache priority heuristic algorithm (frequency + latency + user_diversity)
    - [x] Add Makefile command: make cache-analysis n=10
    - [x] Output both human-readable table and JSON format
  - [x] System 2: Relative ranking (genonaut/cli/cache_analysis_relative.py)
    - [x] Implement get_top_routes_relative(n, lookback_days)
    - [x] Add percentile-based ranking algorithm
    - [x] Add Makefile command: make cache-analysis-relative n=10
    - [x] Output both human-readable table and JSON format (same schema as System 1)
  - [x] Add numpy dependency to requirements-unlocked.txt
  - [x] Document both CLIs in docs/api.md

- [x] Phase 5: Analytics API endpoints
  - [x] Create genonaut/api/routes/analytics.py with endpoints
  - [x] GET /api/v1/analytics/routes/cache-priorities
  - [x] GET /api/v1/analytics/routes/performance-trends
  - [x] GET /api/v1/analytics/routes/peak-hours
  - [x] Register router in genonaut/api/main.py
  - [x] Test all endpoints manually (all return 200 OK)
    - [x] New tests: Add automated tests for analytics endpoints (not done but moved to phase 7)

  NOTE: Phase 5 is now COMPLETE! All three API endpoints are working.
  Endpoints provide programmatic access to the CLI functionality.

- [x] Phase 6: Remove old PerformanceTimingMiddleware
  - [x] Verify new middleware captures all needed data
  - [x] Remove PerformanceTimingMiddleware from main.py
  - [x] Remove genonaut/api/middleware/performance_timing.py
  - [x] Update tests if needed

- [ ] Phase 7: Testing and documentation
  - See subsection below


### Phase 7: Testing and documentation

#### Documentation Tasks (COMPLETE)
  - [x] Docs: Update docs/api.md with analytics endpoints
    - Added comprehensive documentation for all 3 analytics endpoints
    - Included query parameters, response formats, and use cases
    - Location: docs/api.md lines 615-788
  - [x] Docs: Add example queries and usage to docs/
    - Created docs/route-analytics-examples.md with extensive examples
    - Includes SQL queries for monitoring, debugging, cache analysis
    - Includes API usage examples (curl, Python)
    - Includes CLI usage examples for both systems
    - Location: docs/route-analytics-examples.md

#### Test Creation Tasks (COMPLETE)
  - [x] New tests: Add unit tests for middleware
    - Created test/api/unit/test_route_analytics_middleware.py
    - 28 tests covering all helper functions and middleware behavior
    - Tests normalization, error handling, user ID extraction, etc.
  - [x] New tests: Add integration tests for Celery tasks
    - Created test/worker/test_route_analytics_tasks.py
    - 12 tests for transfer_route_analytics_to_postgres task
    - 6 tests for aggregate_route_analytics_hourly task
    - Tests data flow, error handling, idempotency
  - [x] New tests: Add tests for cache analysis CLI
    - Created test/cli/test_cache_analysis.py
    - 25+ tests for both System 1 (absolute) and System 2 (relative)
    - Tests score calculation, filtering, sorting, output formats
  - [x] New tests: Phase 5 - Add automated tests for analytics endpoints
    - Created test/api/test_route_analytics_endpoints.py
    - 14 tests covering all 3 analytics endpoints
    - Tests parameter validation, response formats, edge cases

#### Test Failures (38 FAILURES - NEED FIXES)
  - [ ] Fix SQL parameter binding issues in test fixtures (26 failures)
    - **Problem**: Test helper functions using incorrect JSONB parameter syntax
    - **Error**: `syntax error at or near ":"` in PostgreSQL
    - **Affected files**:
      - test/api/test_route_analytics_endpoints.py (10 failures)
      - test/cli/test_cache_analysis.py (15 failures)
      - test/worker/test_route_analytics_tasks.py (6 failures in aggregation tests)
    - **Root cause**: Using string concatenation `query_params_normalized::jsonb` instead of proper parameter binding
    - **Fix needed**: In test helper functions like `_create_sample_analytics_data()`:
      - Change from: `:query_params_normalized::jsonb`
      - Change to: Pass as string and let PostgreSQL handle JSONB conversion, OR
      - Use json.dumps() and bind as text, then cast in SQL properly
    - **Example location**: test/api/test_route_analytics_endpoints.py:88-90

  - [ ] Fix JSON serialization in transfer task (6 failures)
    - **Problem**: Transfer task can't adapt Python dict to PostgreSQL JSONB
    - **Error**: `(psycopg2.ProgrammingError) can't adapt type 'dict'`
    - **Affected file**: test/worker/test_route_analytics_tasks.py
    - **Affected tests**: All TestTransferRouteAnalyticsToPostgres tests (6 failures)
    - **Root cause**: In genonaut/worker/tasks.py:501-502
      - `query_params` and `query_params_normalized` are loaded from JSON strings
      - But then passed as Python dicts to SQLAlchemy
      - PostgreSQL can't automatically convert dict to JSONB
    - **Fix needed**: In genonaut/worker/tasks.py transfer_route_analytics_to_postgres():
      - Keep query_params as JSON strings, don't parse them
      - OR convert dicts back to JSON strings before inserting
      - Example: `json.dumps(params['query_params'])` before passing to execute()
    - **Location**: genonaut/worker/tasks.py:501-502

  - [ ] Fix mock setup in middleware test (1 failure)
    - **Problem**: Mock for request.state.user_id returns mock object instead of None
    - **Error**: `assert "<Mock name='mock.state.user_id' id='...'>" is None`
    - **Affected file**: test/api/unit/test_route_analytics_middleware.py
    - **Affected test**: TestGetUserIdFromRequest::test_no_user_id_available
    - **Root cause**: Mock.state creates auto-spec that has user_id attribute by default
    - **Fix needed**: Use `spec_set` or configure mock to raise AttributeError
    - **Example fix**:
      ```python
      request.state = Mock(spec=[])  # Empty spec, no attributes
      # OR
      type(request.state).user_id = PropertyMock(side_effect=AttributeError)
      ```
    - **Location**: test/api/unit/test_route_analytics_middleware.py:179-182

#### Test Suite Execution
  - [ ] Fix test failures first (38 failures to address)
  - [ ] Ensure tests pass: `make test`
    - **Status**: Ran, found 38 failures (see above)
    - **Result**: 1129 passed, 38 failed, 62 skipped
    - **Action needed**: Fix the 3 categories of failures above
  - [ ] Ensure tests pass: `make frontend-test-unit`
    - **Status**: Not yet run
  - [ ] Ensure tests pass: `make frontend-test-e2e`
    - **Status**: Not yet run
  - [ ] Ensure tests pass: `make test-long-running`
    - **Status**: Not yet run

#### Final acceptance criteria
If any of these fail, make new task above to address the failures.

- [ ] Ensure tests pass: `make test`
- [ ] Ensure tests pass: `make frontend-test-unit`
- [ ] Ensure tests pass: `make frontend-test-e2e`
- [ ] Ensure tests pass: `make test-long-running`
