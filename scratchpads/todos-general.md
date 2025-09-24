# General todos
The purpose of this is to document any future todos that involve features which are not on the current "docket", so to 
speak.  

## Generation Feature
Future implementation of content generation functionality. This feature will include:
- Job queue processing and management
- Generation workflow orchestration  
- Background task processing for generation jobs

### Deferred Tests (TODO: Re-enable after implementation)
- [ ] **TestGenerationJobEndpoints.test_list_generation_jobs** - Test listing generation jobs with status filtering and pagination
  - Location: `test/api/integration/test_api_endpoints.py::TestGenerationJobEndpoints::test_list_generation_jobs`
  - Purpose: Tests the generation job listing endpoint with query parameters for status and pagination

- [ ] **TestContentGenerationWorkflow.test_generation_job_lifecycle** - Test complete generation job lifecycle workflow
  - Location: `test/api/integration/test_workflows.py::TestContentGenerationWorkflow::test_generation_job_lifecycle`  
  - Purpose: End-to-end test of generation job creation, processing, status updates, and completion

- [ ] **TestRecommendationWorkflow.test_recommendation_system_workflow** - Test recommendation workflow with generation integration
  - Location: `test/api/integration/test_workflows.py::TestRecommendationWorkflow::test_recommendation_system_workflow`
  - Purpose: Tests recommendation generation and serving workflow that depends on generation functionality
