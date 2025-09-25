# ComfyUI Integration Implementation Tasks

## Phase 1: Backend Foundation

### Database Models & Migrations
- [x] Create SQLAlchemy models for `GenerationRequest` in `genonaut/db/schema.py`
  - [x] Add GenerationRequest table with all fields from spec (ComfyUIGenerationRequest)
  - [x] Add AvailableModel table for checkpoint/LoRA management
  - [x] Add proper indexes and foreign key relationships
- [x] Create Alembic migration for new tables
  - [x] Run `alembic revision --autogenerate -m "Add ComfyUI generation tables"`
  - [x] Test migration up/down functionality (migration applied successfully to demo DB)
- [ ] Write unit tests for database models
  - [ ] Test GenerationRequest CRUD operations
  - [ ] Test AvailableModel CRUD operations
  - [ ] Test relationship constraints and validations

### ComfyUI Integration Core
- [x] Create `genonaut/api/services/comfyui_client.py`
  - [x] Implement ComfyUIClient class with connection management
  - [x] Add methods: submit_workflow, get_status, get_result, cancel_job
  - [x] Handle connection errors and retries
  - [x] Add comprehensive logging
- [x] Create `genonaut/api/services/workflow_builder.py`
  - [x] Implement WorkflowBuilder class
  - [x] Add method to build workflow JSON from user parameters
  - [x] Add model path validation and resolution
  - [x] Support dynamic LoRA chaining
- [x] Create `genonaut/api/services/comfyui_generation_service.py`
  - [x] Implement GenerationService orchestration class
  - [x] Add async request processing methods
  - [x] Add status polling and updates
  - [x] Add result retrieval and file handling
- [ ] Write unit tests for ComfyUI services
  - [ ] Mock ComfyUI API responses in tests
  - [ ] Test workflow generation logic
  - [ ] Test error handling scenarios
  - [ ] Test async processing flows

### Configuration & Setup
- [x] Add ComfyUI configuration to `genonaut/api/config.py`
  - [x] ComfyUI API URL and connection settings
  - [x] Output directory paths (@dev: determine ComfyUI output directory)
  - [x] Model discovery settings
- [ ] Create model discovery utility
  - [ ] Scan ComfyUI model directories (@dev: locate model paths)
  - [ ] Update AvailableModel table with discovered models
  - [ ] Add CLI command for model refresh
- [ ] Add required dependencies to requirements.txt
  - [ ] HTTP client library (httpx or aiohttp)
  - [ ] Image processing library (Pillow for thumbnails)
  - [ ] Any additional async utilities

## Phase 2: API Endpoints

### REST API Implementation
- [x] Create `genonaut/api/models/requests.py` schemas for generation
  - [x] ComfyUIGenerationCreateRequest schema
  - [x] ComfyUIModelListRequest schema with filtering
  - [x] ComfyUIGenerationListRequest schema
- [x] Create `genonaut/api/models/responses.py` schemas for generation
  - [x] ComfyUIGenerationResponse schema
  - [x] ComfyUIGenerationListResponse schema
  - [x] AvailableModelListResponse schema
  - [x] Status and error response schemas
- [x] Create `genonaut/api/routes/comfyui.py`
  - [x] POST /api/v1/comfyui/generate - Submit generation
  - [x] GET /api/v1/comfyui/{id} - Get generation status
  - [x] GET /api/v1/comfyui/ - List user generations
  - [x] DELETE /api/v1/comfyui/{id} - Cancel/delete generation
  - [x] GET /api/v1/comfyui/models/ - List available models
- [x] Add route registration to main.py
- [x] Create `genonaut/api/repositories/comfyui_generation_repository.py`
  - [x] CRUD operations for ComfyUIGenerationRequest
  - [x] User-specific queries with pagination
  - [x] Status filtering and sorting

### API Testing
- [ ] Write integration tests in `test/api/`
  - [ ] Test generation request submission
  - [ ] Test status polling endpoints
  - [ ] Test model listing functionality
  - [ ] Test error scenarios (invalid models, etc.)
  - [ ] Test authentication and authorization
- [ ] Write API endpoint unit tests
  - [ ] Mock service layer dependencies
  - [ ] Test request/response validation
  - [ ] Test error handling and status codes

## Phase 3: Worker Queue Integration (@dev: Choose worker system)

### Async Processing Setup
- [ ] Install and configure worker system (Ray/Celery/Kafka)
- [ ] Create worker task definitions
  - [ ] Generation processing task
  - [ ] Status polling task
  - [ ] Result retrieval task
  - [ ] Cleanup/timeout tasks
- [ ] Update GenerationService to use async workers
  - [ ] Queue generation requests
  - [ ] Handle worker status updates
  - [ ] Process worker results
- [ ] Add worker monitoring and error recovery
- [ ] Write worker integration tests
  - [ ] Test task queuing and execution
  - [ ] Test failure scenarios and retries
  - [ ] Test worker scaling behavior

## Phase 4: Frontend Implementation

### Generation Page Components
- [x] Create `frontend/src/pages/GenerationPage.tsx`
  - [x] Main layout with form and results sections
  - [x] Integration with Material-UI components
- [x] Create `frontend/src/components/generation/GenerationForm.tsx`
  - [x] Prompt input fields (positive/negative)
  - [x] Model selection dropdowns
  - [x] Parameter input controls
  - [x] Submit and reset functionality
- [x] Create `frontend/src/components/generation/ModelSelector.tsx`
  - [x] Checkpoint model dropdown
  - [x] LoRA model multi-select with strength sliders
  - [x] Model info display and validation
- [x] Create `frontend/src/components/generation/ParameterControls.tsx` (integrated into GenerationForm)
  - [x] Image dimension inputs
  - [x] Batch size selector
  - [x] Advanced settings (collapsible)
  - [x] KSampler parameter controls
- [x] Create `frontend/src/components/generation/GenerationProgress.tsx`
  - [x] Real-time status display
  - [x] Progress indicators
  - [x] Cancel generation button
  - [x] Error state handling

### Generation History Components
- [x] Create `frontend/src/components/generation/GenerationHistory.tsx`
  - [x] Grid/list view toggle
  - [x] Pagination controls
  - [x] Filter and sort options
- [x] Create `frontend/src/components/generation/GenerationCard.tsx`
  - [x] Thumbnail display
  - [x] Generation metadata
  - [x] Action buttons (view, regenerate, delete)
- [x] Create `frontend/src/components/generation/ImageViewer.tsx`
  - [x] Full-size image modal
  - [x] Generation parameters display
  - [x] Download functionality
  - [x] Navigation between images

### State Management & API Integration
- [x] Create API client functions in `frontend/src/services/comfyui-service.ts`
  - [x] Generate typed API calls
  - [x] Error handling and retry logic
  - [x] File upload/download utilities
- [x] Create React hooks in `frontend/src/hooks/`
  - [x] useComfyUIService hook with all generation methods
  - [x] Status polling integrated into GenerationProgress component
  - [x] Model loading integrated into components
- [x] Add routing in `frontend/src/App.tsx`
  - [x] /generate route for generation page
  - [x] Navigation menu updated

### Frontend Testing
- [ ] Write component unit tests with Vitest
  - [ ] Test GenerationForm validation and submission
  - [ ] Test ModelSelector functionality
  - [ ] Test ParameterControls input handling
  - [ ] Test GenerationProgress status updates
- [ ] Write E2E tests with Playwright
  - [ ] Test complete generation workflow
  - [ ] Test model selection and parameter input
  - [ ] Test generation history and image viewing
  - [ ] Test error scenarios and recovery

## Phase 5: Image & Thumbnail Processing

### Thumbnail Generation
- [ ] Implement thumbnail service in `genonaut/api/services/thumbnail_service.py`
  - [ ] PIL/Pillow integration for image processing
  - [ ] Multiple size generation (small, medium, large)
  - [ ] Format optimization (WebP with fallbacks)
  - [ ] Batch processing capabilities
- [ ] Add thumbnail generation to generation workflow
  - [ ] Generate thumbnails after ComfyUI completion
  - [ ] Store thumbnail paths in database
  - [ ] Handle thumbnail generation failures
- [ ] Write tests for thumbnail service
  - [ ] Test image processing functions
  - [ ] Test multiple format generation
  - [ ] Test error handling for corrupted images

### File Management
- [ ] Create file storage service
  - [ ] Organize generated images by user/date
  - [ ] Implement cleanup policies for old images
  - [ ] Add file validation and security checks
- [ ] Add image serving endpoints
  - [ ] Serve images with proper caching headers
  - [ ] Add authentication for user images
  - [ ] Support range requests for large images
- [ ] Write file management tests
  - [ ] Test file organization structure
  - [ ] Test cleanup policies
  - [ ] Test security and access controls

## Phase 6: Advanced Features & Polish

### Model Management UI
- [ ] Create admin interface for model management
  - [ ] Add/remove model entries
  - [ ] Enable/disable models
  - [ ] Model discovery and refresh
- [ ] Add model validation and health checks
- [ ] Write model management tests

### Performance & Optimization
- [ ] Add database query optimization
  - [ ] Add proper indexes for common queries
  - [ ] Optimize pagination queries
  - [ ] Add query result caching
- [ ] Frontend performance optimization
  - [ ] Image lazy loading
  - [ ] Virtual scrolling for large lists
  - [ ] Query caching and background updates
- [ ] Write performance tests
  - [ ] Load testing for concurrent generations
  - [ ] Database query performance tests
  - [ ] Frontend rendering performance tests

### Error Handling & Monitoring
- [ ] Add comprehensive error handling
  - [ ] User-friendly error messages
  - [ ] Automatic retry logic
  - [ ] Error reporting and logging
- [ ] Add monitoring and metrics
  - [ ] Generation success/failure rates
  - [ ] Performance metrics and alerts
  - [ ] User activity tracking
- [ ] Write error handling tests
  - [ ] Test various failure scenarios
  - [ ] Test error recovery mechanisms
  - [ ] Test user experience during errors

## Phase 7: Production Readiness

### Security & Validation
- [ ] Add input validation and sanitization
  - [ ] Prompt content filtering
  - [ ] File path validation
  - [ ] Rate limiting per user
- [ ] Add security headers and CORS
- [ ] Write security tests
  - [ ] Test input validation boundaries
  - [ ] Test authentication edge cases
  - [ ] Test file access controls

### Documentation & Deployment
- [ ] Update API documentation
  - [ ] OpenAPI schema for generation endpoints
  - [ ] Usage examples and tutorials
- [ ] Add deployment configuration
  - [ ] Docker setup for ComfyUI integration
  - [ ] Environment variable configuration
  - [ ] Production database migrations
- [ ] Write deployment tests
  - [ ] Test deployment scripts
  - [ ] Test configuration management
  - [ ] Test service health checks

### Integration Testing & QA
- [ ] End-to-end integration tests
  - [ ] Test complete user workflows
  - [ ] Test ComfyUI integration (@dev: requires ComfyUI instance)
  - [ ] Test worker queue integration
- [ ] Performance testing
  - [ ] Load testing with multiple concurrent users
  - [ ] Memory usage and leak testing
  - [ ] Database performance under load
- [ ] User acceptance testing (@dev)
  - [ ] Manual testing of complete workflows
  - [ ] UI/UX feedback and improvements
  - [ ] Performance validation

## Configuration & Dependencies (@dev Tasks)

### Environment Setup
- [ ] @dev Install and configure ComfyUI instance
- [ ] @dev Determine ComfyUI output directory paths
- [ ] @dev Configure ComfyUI models directory
- [ ] @dev Set up worker queue system (Ray/Celery/Kafka)
- [ ] @dev Configure production image storage (local/AWS S3)

### Infrastructure Decisions
- [ ] @dev Choose worker queue technology
- [ ] @dev Decide on ComfyUI instance architecture (single/multiple)
- [ ] @dev Configure rate limiting and resource constraints
- [ ] @dev Set up monitoring and alerting systems
- [ ] @dev Plan backup and disaster recovery for generated images

### Model Management Strategy
- [ ] @dev Decide on model discovery vs manual registration
- [ ] @dev Set up model validation and security scanning
- [ ] @dev Configure model storage and organization
- [ ] @dev Plan model updates and versioning strategy