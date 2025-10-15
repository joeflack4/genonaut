# Long-Running and Performance-Related Tests Analysis

## Overview
This document provides a comprehensive analysis of all long-running and performance-related tests in the Genonaut test 
suite, categorizing them by their purpose and characteristics.

## Test Statistics

- **Total tests in test/**: 746
- **Quick tests** (`make test`): 698 tests
- **Long-running tests** (`make test-long-running`): 40 tests
- **Performance tests** (`make test-performance`): 7 tests
- **Ontology performance tests** (`make test-ontology-perf`): 18 tests
- **API server tests** (`make test-api-server`): 56 tests

**Note**: Some tests have multiple markers (e.g., both `longrunning` and `comfyui_poll`), so individual category counts 
may overlap.

## Test Categories

### 1. Long-Running Tests (@pytest.mark.longrunning) - 40 tests

These tests are marked as `longrunning` because they take significant time to execute (> 5 seconds), often due to:
- Database operations on large datasets
- Polling/waiting for completion
- Concurrent/stress testing
- File I/O operations

#### 1.1 Performance-Related Long-Running Tests (18 tests)

**Location**: test/api/stress/, test/db/integration/, test/api/integration/

These tests explicitly measure performance metrics like response time, throughput, memory usage:

**Pagination & Database Performance** (10 tests):
- `test_million_record_pagination_performance` - Measures pagination performance with 1M+ records
- `test_cursor_pagination_consistency` - Tests cursor-based pagination with large datasets
- `test_pagination_with_large_dataset` - Stress test for pagination with 100K records
- `test_deep_pagination_performance` - Tests performance when paginating deep into results
- `test_concurrent_pagination_load` - Concurrent pagination requests (10 simultaneous)
- `test_cursor_pagination_performance` - Performance benchmarks for cursor pagination
- `test_memory_usage_stability` - Monitors memory usage during pagination
- `test_pagination_performance_benchmarks` - Comprehensive pagination benchmarks
- `test_large_dataset_query_performance` - ComfyUI-related query performance with large datasets
- `test_large_dataset_pagination_performance` - Database pagination performance tests

**Load Testing** (5 tests):
- `test_concurrent_generation_requests_small_load` - 3 concurrent generation requests
- `test_concurrent_generation_requests_medium_load` - 10 concurrent requests
- `test_concurrent_generation_requests_high_load` - 25 concurrent requests
- `test_generation_queue_processing_under_load` - Queue processing under load
- `test_database_performance_under_concurrent_writes` - Database write performance

**File I/O Performance** (3 tests):
- `test_concurrent_jobs_unique_files` - File generation under concurrent load
- `test_output_files_exist_on_disk` - File system I/O validation
- `test_multiple_images_same_job` - Multiple file output performance

#### 1.2 Non-Performance Long-Running Tests (22 tests)

**Location**: test/integrations/comfyui/

These tests are long-running due to polling delays, waiting for completion, or end-to-end workflows, but do NOT 
explicitly measure performance metrics:

**ComfyUI Polling Tests** (@pytest.mark.comfyui_poll) - 8 tests:
- `test_get_history_pending` - Wait for job processing (0.6s delay)
- `test_get_history_completed` - Polling for completion
- `test_output_file_generation` - Wait for file generation
- `test_multiple_jobs_unique_files` - Sequential job polling
- `test_get_workflow_status_completed` - Status polling
- `test_wait_for_completion` - Explicit wait testing
- `test_get_output_files` - File retrieval after completion
- `test_workflow_with_client_id` - Client ID workflow with polling

**ComfyUI E2E Workflow Tests** (@pytest.mark.comfyui_e2e) - 9 tests:
- `test_complete_workflow_manual` - Full workflow without Celery
- `test_job_status_updates` - Status transitions during workflow
- `test_file_organization` - File system organization validation
- `test_thumbnail_generation` - Thumbnail creation workflow
- `test_content_item_creation` - Content creation workflow
- `test_multiple_jobs_sequential` - Sequential job execution
- `test_unique_output_files_per_job` - Unique file naming validation
- `test_job_failure_handling` - Error handling in workflows
- `test_cleanup_on_failed_job` - Cleanup operations

**ComfyUI Error Scenarios** - 2 tests:
- `test_workflow_timeout` - Timeout handling
- `test_workflow_without_save_node` - Missing node error handling

**File Output Tests** - 3 tests:
- `test_output_file_naming_pattern` - File naming validation
- `test_output_file_subfolder` - Subfolder organization
- `test_filename_counter_increments` - Counter increment logic

### 2. Performance Tests (@pytest.mark.performance) - 7 tests

**Location**: test/api/performance/, test/api/integration/

These tests measure performance against a **live demo server** (port 8001) and require the server to be running before 
tests execute.

**Requirement**: `make api-demo` must be running

**Gallery Tag Performance Tests** (7 tests):
- `test_canonical_tag_query_performance` - Target: < 3 seconds
  - Tests the specific query that was timing out
  - All 4 content_source_types + single tag filter
  - Measures end-to-end HTTP request time
- `test_canonical_query_without_tag_is_fast` - Baseline (no tag): < 2 seconds
  - Same query without tag filter to isolate tag filtering performance
- `test_tag_query_with_multiple_tags` - Multi-tag query: < 3 seconds
  - Tests "any" matching with multiple tags
- `test_measure_query_performance_detailed` - 5 runs with statistics
  - Provides average, min, max timing across multiple runs
  - Useful for identifying variance and cold/warm cache effects
- 3 additional tests in test/api/integration/ (duplicates with same logic)

**Performance Characteristics**:
- All tests are **integration tests** hitting live HTTP endpoints
- Measure **wall-clock time** including network, serialization, database
- Assert on **maximum acceptable response time**
- Do NOT measure throughput, memory, or concurrency

### 3. Ontology Performance Tests (@pytest.mark.ontology_perf) - 18 tests

**Location**: test/ontologies/tags/

These tests validate performance and correctness of the tag ontology system, including CLI tools and large dataset handling.

**Performance Tests** (test_performance.py) - 8 tests:
- `test_large_tag_extraction_performance` - Extract 4000 tags in < 1 second
- `test_hierarchy_validation_performance` - Validate 1100-node hierarchy in < 2 seconds
- `test_tag_lookup_performance` - 10K lookups in < 100ms
- `test_tsv_parsing_performance` - Parse 1000 row TSV in < 1 second
- `test_memory_usage_under_load` - Memory constraints (< 50MB for 10K tags)
- `test_concurrent_access_performance` - Thread-safe concurrent access
- `test_cache_hit_performance` - Cache performance validation
- `test_large_file_processing_performance` - 10K line file processing

**Integration/CLI Tests** (test_integration.py) - 10 tests:
- Makefile goal execution tests (subprocess calls)
- Script import and dependency tests
- File generation pipeline tests
- Error handling and robustness tests
- Documentation synchronization tests

**Characteristics**:
- Most tests involve **subprocess calls** (running Python scripts via CLI)
- Tests validate **both correctness and performance**
- Memory usage monitoring with psutil
- Large dataset handling (1000-10000 items)

### 4. API Server Tests (@pytest.mark.api_server) - 56 tests

**Location**: test/api/integration/

These tests **start their own test API server** using uvicorn and hit live HTTP endpoints.

**Key Characteristic**: The test suite automatically boots the API server as a subprocess in test fixtures, runs tests, and tears it down.

**Test Coverage**:
- Workflow tests (test_workflows.py)
- Flagged content API (test_flagged_content_api.py)
- General API endpoints (test_api_endpoints.py)

**Differences from `@pytest.mark.performance`**:
- `api_server` tests start their own server (subprocess)
- `performance` tests require demo server to already be running
- `api_server` tests use test database/configuration
- `performance` tests use demo database/configuration

**Note**: None of the api_server tests are also marked as longrunning.

## Test Marker Relationships

### Overlapping Markers

Some tests have multiple markers. Here's the overlap analysis:

- **comfyui_poll AND longrunning**: 16 tests
  - All comfyui_poll tests are also longrunning (due to polling delays)
- **comfyui_e2e AND longrunning**: 9 tests
  - All comfyui_e2e tests are also longrunning (due to workflow execution time)
- **api_server AND longrunning**: 0 tests
  - No overlap - api_server tests are generally fast
- **ontology_perf AND longrunning**: 0 tests
  - Ontology tests are standalone, not marked as longrunning
- **performance AND longrunning**: 0 tests
  - Performance tests are separate from longrunning

### Independent Test Groups

These marker groups are **mutually exclusive**:
1. Quick tests (no special markers)
2. Performance tests (@pytest.mark.performance)
3. Ontology performance tests (@pytest.mark.ontology_perf)
4. API server tests (@pytest.mark.api_server)
5. Long-running tests (@pytest.mark.longrunning) - includes comfyui_poll and comfyui_e2e

## Make Target Relationships

### `make test` (698 tests)
Runs: `-m "not longrunning and not manual and not performance"`
- Fast feedback tests (< 5 seconds per test)
- Unit tests, integration tests, database tests
- No polling, no large datasets, no server startup

### `make test-long-running` (40 tests)
Runs: `-m "longrunning"`
- Includes ALL comfyui_poll tests (16 tests)
- Includes ALL comfyui_e2e tests (9 tests)
- Includes performance benchmarks (pagination, query, load tests)
- Takes 5-15 minutes to complete

### `make test-performance` (7 tests)
Runs: `-m "performance"`
- **Requires demo server running on port 8001**
- Tests gallery tag query performance
- Measures HTTP request response times
- Independent from test-long-running

### `make test-ontology-perf` (18 tests)
Runs: `-m "ontology_perf"`
- Tests tag ontology system performance
- CLI tool validation
- Large dataset handling
- Independent from all other test groups

### `make test-api-server` (56 tests)
Runs: `-m "api_server"`
- Starts its own test server (subprocess)
- Tests HTTP endpoints with test database
- Workflow, flagged content, and general API tests
- Independent from longrunning (no overlap)

### `make test-comfyui-poll` (16 tests)
Runs: `-m "comfyui_poll"`
- Subset of test-long-running
- Tests that poll for completion (0.5-1s delays)
- All marked as longrunning

### `make test-comfyui-e2e` (9 tests)
Runs: `-m "comfyui_e2e"`
- Subset of test-long-running
- End-to-end workflow tests
- All marked as longrunning

### `make test-all` (745 tests)
Runs: `-m "not manual"`
- Runs ALL non-manual tests (99.9% of test suite)
- Includes test-quick (698)
- Includes test-long-running (40)
- Includes test-performance (7)
- Includes test-ontology-perf (18)
- Includes test-api-server (56)
- **Total: 745 unique tests** (some markers overlap, so no double-counting)
- Takes 15-20 minutes
- **Requires demo server on port 8001** (for performance tests)

## Summary: Performance vs Non-Performance Classification

### Performance-Related Tests (Total: ~43 unique tests)

1. **Explicit Performance Measurement (18 tests)**:
   - test/api/stress/test_pagination_stress.py (7 tests)
   - test/db/integration/test_pagination_performance.py (1 test)
   - test/db/integration/test_comfyui_query_performance.py (1 test)
   - test/api/integration/test_unified_content_pagination.py (2 tests)
   - test/integrations/comfyui/test_comfyui_mock_class_load_testing.py (5 tests)
   - test/integrations/comfyui/test_comfyui_mock_server_files.py (3 tests - file I/O performance)

2. **HTTP Performance Tests (7 tests)**:
   - test/api/performance/test_gallery_tag_performance.py (3 tests)
   - test/api/integration/test_gallery_tag_performance.py (4 tests)

3. **Ontology Performance Tests (18 tests)**:
   - test/ontologies/tags/test_performance.py (8 tests)
   - test/ontologies/tags/test_integration.py (10 tests)

### Non-Performance Long-Running Tests (Total: 22 tests)

1. **Polling/Waiting Tests (16 tests)**:
   - ComfyUI polling tests (@comfyui_poll)
   - These wait for completion but don't measure performance

2. **Workflow Tests (9 tests)**:
   - ComfyUI E2E workflow tests (@comfyui_e2e)
   - Validate correctness of workflows, not performance

3. **Error Scenario Tests (2 tests)**:
   - Timeout handling
   - Missing node handling

4. **File System Tests (3 tests - non-performance)**:
   - File naming pattern validation
   - Subfolder organization
   - Counter increment logic

### API Server Tests (56 tests - separate category)
- Start their own test server
- Test HTTP endpoints
- Not primarily performance-focused (measure correctness)
- But some may include basic timing checks

## Recommendations

1. **Test Organization is Correct**: The Makefile structure properly organizes tests by their execution requirements and characteristics.

2. **Marker Consistency**:
   - All comfyui_poll tests are correctly marked as longrunning
   - All comfyui_e2e tests are correctly marked as longrunning
   - Performance tests are correctly isolated
   - No need to change existing marker structure

3. **Running Tests**:
   - **Daily development**: `make test` (698 tests, ~2 minutes)
   - **Before commits**: `make test` + `make test-long-running` (738 tests, ~7-17 minutes)
   - **Before releases**: `make test-all` (745 tests, requires demo server, ~15-20 minutes)
   - **Performance validation**: `make test-performance` (requires demo server running)

4. **Performance Test Classification**:
   - ~18 tests in test-long-running explicitly measure performance (benchmarks, load tests)
   - ~22 tests in test-long-running are long-running due to polling/workflows (not performance)
   - 7 tests in test-performance measure HTTP response times
   - 18 tests in test-ontology-perf validate ontology system performance

## Conclusion

The test suite has a clear separation of concerns:
- **Quick tests**: Fast feedback for development
- **Long-running tests**: Include both performance tests (18) and workflow/polling tests (22)
- **Performance tests**: HTTP endpoint performance against live demo server
- **Ontology performance**: Tag system performance and CLI validation
- **API server tests**: Integration tests with test server

The current organization is appropriate and well-structured. The only overlap is intentional (comfyui_poll and 
comfyui_e2e are subsets of longrunning), which makes sense given their execution characteristics.
