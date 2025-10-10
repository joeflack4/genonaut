# Long-Running Test Candidates

## Mock ComfyUI job completion polls
These tests call `ComfyUIClient.wait_for_completion` against the mock server. The mock adds a 0.5s processing delay while the client polls every 2s, so each assertion waits for real wall-clock time, and loops compound the cost.
- test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_get_history_pending
- test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_get_history_completed
- test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_output_file_generation
- test/integrations/comfyui/test_comfyui_mock_server_basic.py::TestMockServerBasics::test_multiple_jobs_unique_files
- test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_get_workflow_status_completed
- test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_wait_for_completion
- test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_get_output_files
- test/integrations/comfyui/test_comfyui_mock_server_client.py::TestComfyUIClientIntegration::test_workflow_with_client_id
- test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_file_naming_pattern
- test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_file_subfolder
- test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_concurrent_jobs_unique_files
- test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_output_files_exist_on_disk
- test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_multiple_images_same_job
- test/integrations/comfyui/test_comfyui_mock_server_files.py::TestMockServerFileOutput::test_filename_counter_increments
- test/integrations/comfyui/test_comfyui_mock_server_errors.py::TestMockServerErrorScenarios::test_workflow_timeout
- test/integrations/comfyui/test_comfyui_mock_server_errors.py::TestMockServerErrorScenarios::test_workflow_without_save_node

## ComfyUI end-to-end job processing
Each of these invokes `process_comfy_job`, which submits a workflow to the mock server and blocks on `wait_for_outputs`. The default poll interval is 2s, so even the happy path takes multiple seconds, and some tests process several jobs back-to-back.
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_complete_workflow_manual
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_job_status_updates
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_file_organization
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_thumbnail_generation
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestEndToEndWorkflow::test_content_item_creation
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_multiple_jobs_sequential
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestConcurrentJobs::test_unique_output_files_per_job
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_job_failure_handling
- test/integrations/comfyui/test_comfyui_mock_server_e2e.py::TestErrorRecovery::test_cleanup_on_failed_job

## Live API server integration suites
These suites boot a real uvicorn process via the session-scoped `api_server` fixture. Startup polls `/health` every 0.5s up to 10s, and the tests themselves perform many HTTP requests against the running service, so they noticeably stretch `make test`.
- test/api/integration/test_api_endpoints.py::TestSystemEndpoints::*
- test/api/integration/test_api_endpoints.py::TestUserEndpoints::*
- test/api/integration/test_api_endpoints.py::TestContentEndpoints::*
- test/api/integration/test_api_endpoints.py::TestInteractionEndpoints::*
- test/api/integration/test_api_endpoints.py::TestRecommendationEndpoints::*
- test/api/integration/test_api_endpoints.py::TestGenerationJobEndpoints::*
- test/api/integration/test_api_endpoints.py::TestComfyUIEndpoints::*
- test/api/integration/test_api_endpoints.py::TestErrorHandling::*
- test/api/integration/test_flagged_content_api.py::TestFlaggedContentAPI::*
- test/api/integration/test_workflows.py::TestCompleteUserWorkflow::test_user_content_interaction_workflow

## Ontology performance and CLI checks
These tests construct large temporary datasets, spawn `make` subprocesses, or iterate over heavy data structures. They also include explicit sleeps for concurrency checks, so they routinely exceed a few seconds apiece.
- test/ontologies/tags/test_performance.py::TestLargeDatasetHandling::test_large_tag_extraction_performance
- test/ontologies/tags/test_performance.py::TestLargeDatasetHandling::test_hierarchy_validation_performance
- test/ontologies/tags/test_performance.py::TestLargeDatasetHandling::test_pattern_analysis_performance
- test/ontologies/tags/test_performance.py::TestMemoryUsage::test_tag_processing_memory_usage
- test/ontologies/tags/test_performance.py::TestMemoryUsage::test_hierarchy_generation_memory_efficiency
- test/ontologies/tags/test_performance.py::TestExecutionTime::test_query_execution_time
- test/ontologies/tags/test_performance.py::TestExecutionTime::test_validation_speed
- test/ontologies/tags/test_performance.py::TestConcurrentAccess::test_file_read_safety
- test/ontologies/tags/test_integration.py::TestMakefileGoals::test_ontology_stats_goal
- test/ontologies/tags/test_integration.py::TestMakefileGoals::test_ontology_help_integration
- test/ontologies/tags/test_integration.py::TestScriptDependencies::test_script_imports
- test/ontologies/tags/test_integration.py::TestScriptDependencies::test_script_main_functions
- test/ontologies/tags/test_integration.py::TestFileGeneration::test_hierarchy_file_generation
- test/ontologies/tags/test_integration.py::TestFileGeneration::test_data_file_consistency
- test/ontologies/tags/test_integration.py::TestErrorHandling::test_missing_files_handling
- test/ontologies/tags/test_integration.py::TestErrorHandling::test_malformed_hierarchy_handling
- test/ontologies/tags/test_integration.py::TestDocumentationSync::test_readme_reflects_structure
- test/ontologies/tags/test_integration.py::TestDocumentationSync::test_makefile_help_completeness
