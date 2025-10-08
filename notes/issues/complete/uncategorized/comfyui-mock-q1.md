# ComfyUI Integration Q&A

## Question 1: What does the response look like when we submit an image? What kind of JSON response do we expect?

### Initial Submission Response

When we submit a workflow to ComfyUI via `POST /prompt`, we expect:

```json
{
  "prompt_id": "12345678-abcd-1234-abcd-123456789abc"
}
```

**Code Reference:** `genonaut/api/services/comfyui_client.py:115-120`

### Completion/History Response

When we poll for status via `GET /history/{prompt_id}`, we expect:

```json
{
  "12345678-abcd-1234-abcd-123456789abc": {
    "status": {
      "completed": true,
      "messages": []
    },
    "outputs": {
      "9": {
        "images": [
          {
            "filename": "gen_job_123_00001_.png",
            "subfolder": "",
            "type": "output"
          }
        ]
      }
    }
  }
}
```

**Code Reference:** `genonaut/api/services/comfyui_client.py:180-189`

The node ID (e.g., "9") represents the SaveImage node in the workflow. Multiple nodes can have outputs.

---

## Question 2: Does the response say what the file name or path will be of the resulting file created?

**Yes**, the response includes both `filename` and `subfolder` fields for each generated image.

### Response Structure

```json
{
  "filename": "gen_job_123_00001_.png",
  "subfolder": "",
  "type": "output"
}
```

- **`filename`**: The actual filename created by ComfyUI
- **`subfolder`**: Optional subdirectory within the ComfyUI output directory
- **`type`**: Usually "output"

The full path is constructed as: `{comfyui_output_dir}/{subfolder}/{filename}`

**Code Reference:** `genonaut/api/services/comfyui_client.py:296-307`

---

## Question 3: If not, did we figure out any good idea to determine this? How do we handle multiple users creating multiple images?

**We DO get the filename from ComfyUI**, but we also **control the filename prefix** to ensure uniqueness per job.

### Our Strategy

1. **Filename Prefix Control**: We set `filename_prefix` in the workflow to uniquely identify each job
   - Format: `gen_job_{job_id}` (e.g., `gen_job_123`)
   - ComfyUI appends a counter: `gen_job_123_00001_.png`, `gen_job_123_00002_.png`, etc.

   **Code Reference:** `genonaut/worker/tasks.py:144`

2. **File Organization**: After ComfyUI completes, we:
   - Extract the filename and subfolder from the response
   - Use `FileService.organize_generation_files()` to move/organize files
   - Store organized paths in the database with the job record

   **Code Reference:** `genonaut/worker/tasks.py:169-177`

3. **Database Tracking**: Each job stores:
   - `job.id` (unique per job)
   - `job.user_id` (which user owns it)
   - `job.comfyui_prompt_id` (ComfyUI's tracking ID)
   - `job.params['output_paths']` (final organized file paths)
   - `job.content_id` (links to ContentItem with metadata)

### Multi-User Isolation

- Each job has a unique `job_id`, which becomes part of the filename prefix
- Files are organized by user_id after generation
- Database ensures each image is linked to the correct user and job

**Summary**: We're protected from filename collisions through:
- Unique job IDs in filename prefix
- ComfyUI's auto-incrementing counters
- Post-processing file organization
- Database tracking of all relationships

---

## Question 4: Does our testing currently implement a mock of ComfyUI to emulate its behavior?

**Yes**, but it's a **simple mock using Python's `unittest.mock`**, not a full web server.

### Current Mocking Approach

We use **`unittest.mock.Mock` and `patch`** to mock the `ComfyUIClient` class in tests.

#### Example from Load Testing

**Code Reference:** `test/integrations/test_comfyui_load_testing.py:52-69`

```python
@pytest.fixture
def generation_service(self, db_session: Session) -> ComfyUIGenerationService:
    """Create a generation service with mocked ComfyUI client."""
    repository = ComfyUIGenerationRepository(db_session)

    # Mock the ComfyUI client to avoid actual API calls
    with patch('genonaut.api.services.comfyui_generation_service.ComfyUIClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock successful workflow submission
        mock_client.submit_workflow.return_value = {"prompt_id": "test-prompt-123"}
        mock_client.get_status.return_value = {
            "status": {"status_str": "success"},
            "outputs": {"9": {"images": [{"filename": "test_image.png", "type": "output"}]}}
        }

        service = ComfyUIGenerationService(repository, mock_client)
        yield service
```

#### Example from Error Scenarios

**Code Reference:** `test/api/integration/test_error_scenarios.py:54-60`

```python
@pytest.fixture
def generation_service(self, db_session: Session) -> ComfyUIGenerationService:
    """Create a generation service with mocked dependencies."""
    service = ComfyUIGenerationService(db_session)
    # Mock the client after service creation
    service.comfyui_client = Mock(spec=ComfyUIClient)
    return service
```

### What Gets Mocked

The tests mock these key methods:
- `submit_workflow()` - returns mock `prompt_id`
- `get_status()` / `get_workflow_status()` - returns mock completion status
- `wait_for_completion()` - returns mock outputs
- Connection errors (using `side_effect` to raise exceptions)

### What's NOT Implemented

**We do NOT have:**
- A standalone mock HTTP server that behaves like ComfyUI
- A test harness that accepts real HTTP requests at `http://localhost:8189`
- Integration tests that exercise the full HTTP request/response cycle

### Files Using ComfyUI Mocks

1. `test/integrations/test_comfyui_load_testing.py` - Load testing with mocks
2. `test/api/integration/test_error_scenarios.py` - Error handling tests
3. `test/api/integration/test_user_error_experience.py` - User error experience tests
4. `test/api/integration/test_error_recovery.py` - Error recovery tests
5. `test/services/test_thumbnail_service.py` - Thumbnail service tests

### Recommendation

If you want to create a **mock ComfyUI HTTP server** for more realistic integration testing, we would need to:

1. Create a simple Flask/FastAPI server that mimics ComfyUI's API endpoints:
   - `POST /prompt` - return mock `prompt_id`
   - `GET /history/{prompt_id}` - return mock workflow status
   - `GET /queue` - return mock queue status
   - `GET /object_info` - return mock model info
   - `POST /interrupt` - accept cancellation requests

2. Start this server during test setup (e.g., in a pytest fixture)

3. Configure tests to use `http://localhost:{test_port}` instead of the real ComfyUI URL

4. Optionally save test files to a temp directory to simulate output files

This would provide **end-to-end HTTP testing** while keeping tests fast and isolated.

**Current Status**: [NO] No mock HTTP server exists yet
**Current Approach**: [YES] Using `unittest.mock.Mock` to patch `ComfyUIClient` methods
