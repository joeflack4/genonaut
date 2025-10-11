# Candidates for Re-enabling Skipped Tests

## Not Longrunning

### ComfyUI Error Scenario Coverage
Recent work on the image generation service (prompt submission, result polling, and error mapping) gives us the building blocks these scenario tests were waiting on. Re-enabling them would lock in regressions for the typical failure modes we now support.
- [x] test/api/integration/test_error_scenarios.py::test_comfyui_connection_failure
- [x] test/api/integration/test_error_scenarios.py::test_comfyui_timeout_failure
- [x] test/api/integration/test_error_scenarios.py::test_invalid_model_request
- [x] test/api/integration/test_error_scenarios.py::test_invalid_generation_parameters
- [x] test/api/integration/test_error_scenarios.py::test_comfyui_server_error
- [x] test/api/integration/test_error_scenarios.py::test_comfyui_workflow_failure
- [x] test/api/integration/test_error_scenarios.py::test_file_system_error
- [x] test/api/integration/test_error_scenarios.py::test_memory_exhaustion_scenario
- [x] test/api/integration/test_error_scenarios.py::test_concurrent_request_conflicts
- [x] test/api/integration/test_error_scenarios.py::test_malformed_comfyui_response
- [x] test/api/integration/test_error_scenarios.py::test_network_interruption_during_generation
- [x] test/api/integration/test_error_scenarios.py::test_partial_generation_failure

### ComfyUI Recovery Resilience
These skips point at issues we have largely addressed while stabilising job lifecycle handling (prompt IDs now stored as strings, retry/circuit breaker logic landed). Bringing them back would validate that the new recovery paths really work end-to-end.
- [x] test/api/integration/test_error_recovery.py::test_connection_recovery_after_downtime
- [x] test/api/integration/test_error_recovery.py::test_partial_service_degradation_handling
- [x] test/api/integration/test_error_recovery.py::test_graceful_degradation_during_high_error_rate

### Generation Job Listing Endpoint
The generation job listing API now exists and is exercised by the frontend queue view. Turning this test back on would give us integration coverage for filter/pagination behaviour around the new workflows.
- [x] test/api/integration/test_api_endpoints.py::test_list_generation_jobs

### ComfyUI Client Health Check
The ComfyUI client cache layer was rewritten when we added production health monitoring. This test only fails because of the old cache stub—worth re-enabling to ensure our health check path stays deterministic.
- [x] test/integrations/comfyui/test_comfyui_mock_server_client.py::test_health_check

### ComfyUI Query Performance Analytics
With sampler parameters now stored in the `params` JSON payload, we can refit these analytics queries to read from structured data instead of the old `steps` column. Reviving them would give us regression protection around the reporting endpoints we expose.
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_list_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_by_user_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_by_status_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_by_model_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_statistics_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_with_user_join_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_date_range_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_complex_filter_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_generation_search_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_available_models_query_performance
- [x] test/db/integration/test_comfyui_query_performance.py::test_model_usage_statistics_performance

## Longrunning

### ComfyUI Load & Concurrency Suite
We now exercise sustained generation flows in staging; these load tests match the concurrency patterns we expect in production. Folding them into the longrunning suite would surface regressions in queue coordination or DB write throughput.
- [x] test/integrations/comfyui/test_comfyui_mock_class_load_testing.py::test_generation_queue_processing_under_load

### ComfyUI Query Performance Stress
Large dataset performance is increasingly relevant now that generation history is persisted. This longrunning benchmark can move from "manual" to part of the scheduled performance suite once we hook it up to the refreshed schema helpers.
- [x] test/db/integration/test_comfyui_query_performance.py::test_large_dataset_query_performance
