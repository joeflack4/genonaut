# ComfyUI Integration Implementation Tasks - incomplete & semi-complete phases

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

## Phase 6: Advanced Features & Polish
### Performance & Optimization
- [x] 1. Add database query optimization
  - [x] 1.1. Add proper indexes for common queries
  - [x] 1.2. Optimize pagination queries
  - [x] 1.3. Add query result caching
- [x] 2. Frontend performance optimization
  - [x] 2.1. Image lazy loading
  - [x] 2.2. Virtual scrolling for large lists
  - [x] 2.3. Query caching and background updates
- [x] 3. Write performance tests
  - [x] 3.1. Load testing for concurrent generations
  - [x] 3.2. Database query performance tests
    - [ ] test_generation_list_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_by_user_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_by_status_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_by_model_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_statistics_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_with_user_join_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_date_range_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_complex_filter_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_generation_search_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_available_models_query_performance @skipped-until-SCHEMA_FINALIZATION
    - [ ] test_model_usage_statistics_performance @skipped-until-SCHEMA_FINALIZATION
  - [x] 3.3. Frontend rendering performance tests

### Error Handling & Monitoring
- [x] 4. Add comprehensive error handling
  - [x] 4.1. User-friendly error messages
  - [x] 4.2. Automatic retry logic
  - [x] 4.3. Error reporting and logging
- [x] 5. Add monitoring and metrics @dev
  - [x] 5.1. Generation success/failure rates
  - [x] 5.2. Performance metrics and alerts
  - [x] 5.3. User activity tracking
- [ ] 5.1. Enhanced error service features
  - [ ] test_progressive_error_disclosure @skipped-until-ENHANCED_ERROR_SERVICE
  - [ ] test_error_help_links_and_documentation @skipped-until-ENHANCED_ERROR_SERVICE
  - [ ] test_error_feedback_collection @skipped-until-ENHANCED_ERROR_SERVICE
  - [ ] test_multilingual_error_messages @skipped-until-MULTILINGUAL_SUPPORT
  - [ ] test_accessibility_in_error_communication @skipped-until-ACCESSIBILITY_FEATURES
- [x] 6. Write error handling tests
  - [x] 6.1. Test various failure scenarios
  - [x] 6.2. Test error recovery mechanisms
  - [x] 6.3. Test user experience during errors
    - [ ] test_comfyui_connection_failure @skipped-but-should-be-ready-to-finish
    - [ ] test_comfyui_timeout_failure @skipped-but-should-be-ready-to-finish
    - [ ] test_invalid_model_request @skipped-but-should-be-ready-to-finish
    - [ ] test_comfyui_server_error @skipped-but-should-be-ready-to-finish
    - [ ] test_comfyui_workflow_failure @skipped-but-should-be-ready-to-finish
    - [ ] test_file_system_error @skipped-but-should-be-ready-to-finish
    - [ ] test_memory_exhaustion_scenario @skipped-but-should-be-ready-to-finish
    - [ ] test_malformed_comfyui_response @skipped-but-should-be-ready-to-finish
    - [ ] test_network_interruption_during_generation @skipped-but-should-be-ready-to-finish
    - [ ] test_partial_generation_failure @skipped-but-should-be-ready-to-finish
    - [ ] test_api_error_response_structure @skipped-until-API_ENDPOINTS
    - [ ] test_validation_error_user_feedback @skipped-until-API_ENDPOINTS
    - [ ] test_model_not_found_error_guidance @skipped-until-API_ENDPOINTS
    - [ ] test_service_unavailable_error_experience @skipped-until-API_ENDPOINTS
    - [ ] test_rate_limit_error_user_guidance @skipped-until-RATE_LIMITING_MIDDLEWARE
    - [ ] test_generation_status_error_communication @skipped-until-API_ENDPOINTS

## Phase 7: Production Readiness

### Security & Validation
- [x] 7. Add input validation and sanitization
  - [x] 7.1. Prompt content filtering @question: What content filtering rules should be applied?
  - [x] 7.2. File path validation
  - [x] 7.3. Rate limiting per user @question: What rate limits should be applied per user?
- [x] 8. Add security headers and CORS
- [ ] 9. Write security tests
  - [ ] 9.1. Test input validation boundaries
  - [ ] 9.2. Test authentication edge cases
  - [ ] 9.3. Test file access controls

### Documentation & Deployment
- [ ] 10. Update API documentation
  - [ ] 10.1. OpenAPI schema for generation endpoints
  - [ ] 10.2. Usage examples and tutorials
- [ ] 11. Add deployment configuration @dev
  - [ ] 11.1. Docker setup for ComfyUI integration @dev
  - [ ] 11.2. Environment variable configuration @dev
  - [ ] 11.3. Production database migrations @dev
- [ ] 12. Write deployment tests @dev
  - [ ] 12.1. Test deployment scripts @dev
  - [ ] 12.2. Test configuration management @dev
  - [ ] 12.3. Test service health checks @dev

### Integration Testing & QA
- [ ] 13. End-to-end integration tests
  - [ ] 13.1. Test complete user workflows
  - [ ] 13.2. Test ComfyUI integration @dev (requires ComfyUI instance)
  - [ ] 13.3. Test worker queue integration @dev (requires worker queue setup)
- [ ] 14. Performance testing @question: What performance targets should we aim for?
  - [ ] 14.1. Load testing with multiple concurrent users
  - [ ] 14.2. Memory usage and leak testing
  - [ ] 14.3. Database performance under load
- [ ] 15. User acceptance testing @dev
  - [ ] 15.1. Manual testing of complete workflows @dev
  - [ ] 15.2. UI/UX feedback and improvements @dev
  - [ ] 15.3. Performance validation @dev

## Configuration & Dependencies

### Environment Setup
- [x] 16. @dev Install and configure ComfyUI instance
- [ ] 17. @dev Determine ComfyUI output directory paths (MacOS: ~/Documents/ComfyUI/output)
- [ ] 18. @dev Configure ComfyUI models directory mapping (MacOS: ~/Documents/ComfyUI/models/)
- [ ] 19. @question: Should we auto-detect OS (MacOS, Windows, Linux) or use configuration?
- [ ] 20. Add graceful degradation when ComfyUI unavailable
- [ ] 21. @dev Set up worker queue system @question: Prefer Ray, Celery, or Kafka?
- [ ] 22. @dev Configure production image storage @question: Local storage or AWS S3?

### Infrastructure Decisions
- [ ] 23. @dev Choose worker queue technology @question: What are your preferences for Ray vs Celery vs Kafka?
- [ ] 24. @dev Decide on ComfyUI instance architecture @question: Single shared instance or multiple instances?
- [ ] 25. @dev Configure rate limiting and resource constraints @question: What resource limits should be applied?
- [ ] 26. @dev Set up monitoring and alerting systems @question: What monitoring tools do you prefer?
- [ ] 27. @dev Plan backup and disaster recovery for generated images

### Model Management Strategy
- [ ] 28. @dev Decide on model discovery vs manual registration @question: Auto-discover models or manual registration?
- [ ] 29. @dev Set up model validation and security scanning
- [ ] 30. @dev Configure model storage and organization
- [ ] 31. @dev Plan model updates and versioning strategy

---

## Detailed Task Descriptions

#### 1.1. Add proper indexes for common queries
Add database indexes to optimize frequently used queries in the ComfyUI generation system:
- `generation_requests(user_id, created_at)` - for user generation history with date sorting
- `generation_requests(status, created_at)` - for pending/processing job queries
- `generation_requests(comfyui_prompt_id)` - for ComfyUI status polling lookups
- `available_models(type, is_active)` - for model selection queries
- Consider partial indexes for active models only to reduce index size

#### 1.2. Optimize pagination queries
Current pagination may be inefficient for large datasets. Implement:
- Cursor-based pagination using `created_at` timestamps instead of OFFSET
- Add `LIMIT` clauses to all queries
- Consider implementing database-level pagination hints
- Profile existing queries to identify slow pagination scenarios

#### 1.3. Add query result caching
Implement caching for expensive or frequently accessed data:
- Cache available models list (TTL: 1 hour, invalidate on model changes)
- Cache user generation statistics (TTL: 15 minutes)
- Redis or in-memory caching for generation status lookups
- Cache ComfyUI instance health status (TTL: 30 seconds)

#### 2.1. Image lazy loading
Implement lazy loading for generation history and galleries:
- Use Intersection Observer API for viewport detection
- Add skeleton loaders for images not yet loaded
- Preload next/previous images in image viewer
- Consider progressive image loading (blur → full quality)

#### 3.1. Load testing for concurrent generations
Set up comprehensive load testing to validate system performance:
- Test concurrent generation requests (target: 10+ simultaneous users)
- Measure queue processing throughput and latency
- Test database performance under concurrent read/write operations
- Validate ComfyUI instance stability under load
- Use tools like Apache JMeter, Locust, or custom scripts

#### 4.1. User-friendly error messages
Replace technical error messages with user-friendly alternatives:
- "ComfyUI connection failed" → "Image generation service temporarily unavailable"
- "Invalid model path" → "Selected model is currently unavailable"
- "Workflow validation error" → "Invalid generation parameters, please check your settings"
- Add error codes for technical debugging while keeping user messages clear

#### 4.2. Automatic retry logic
Implement smart retry mechanisms for transient failures:
- Retry ComfyUI connection failures (3 attempts, exponential backoff)
- Retry generation status polling on network timeouts
- Retry file operations for temporary I/O errors
- Do NOT retry on user input validation errors or permanent failures

#### 7.1. Prompt content filtering @question: What content filtering rules should be applied?
Implement content moderation for user prompts:
- Define blocked keywords/phrases for inappropriate content
- Consider using external APIs (OpenAI Moderation, Google Perspective)
- Implement both pre-generation filtering and post-generation review
- Log filtered attempts for monitoring and policy adjustment
- Allow configurable sensitivity levels

#### 7.3. Rate limiting per user @question: What rate limits should be applied per user?
Implement user-based rate limiting to prevent abuse:
- Consider limits like: 10 generations per hour, 50 per day for free users
- Higher limits for premium users or authenticated accounts
- Implement sliding window or token bucket algorithms
- Rate limit by IP address as fallback for unauthenticated users
- Queue overflow handling (reject vs queue with delay)

#### 11.1. Docker setup for ComfyUI integration @dev
Create Docker configuration for ComfyUI deployment:
- Dockerfile for ComfyUI with required models and dependencies
- Docker Compose setup linking Genonaut backend with ComfyUI
- Volume mounts for model directories and generated images
- Environment variable configuration for ComfyUI settings
- Health checks and restart policies

#### 13.2. Test ComfyUI integration @dev (requires ComfyUI instance)
Comprehensive integration testing with live ComfyUI:
- Test workflow submission and execution
- Test status polling and completion detection
- Test error scenarios (invalid workflows, timeouts)
- Test concurrent generation handling
- Validate image output format and storage

#### 14. Performance testing @question: What performance targets should we aim for?
Define and test against specific performance targets:
- Generation request response time: < 500ms for submission
- Database query response time: < 100ms for 95th percentile
- Frontend page load time: < 2s for generation page
- Image loading time: < 1s for thumbnails, < 3s for full images
- Concurrent user support: target number of simultaneous users

#### 20. Add graceful degradation when ComfyUI unavailable
Implement fallback behavior when ComfyUI is unavailable:
- Detect ComfyUI connection status on startup and periodically
- Display maintenance notice on generation page when unavailable
- Queue requests during temporary outages (with user notification)
- Provide clear error messages with estimated recovery time
- Consider read-only mode showing previous generations only

#### 21. @dev Set up worker queue system @question: Prefer Ray, Celery, or Kafka?
Choose and implement async task processing:
- **Ray**: Python-native, excellent for ML workloads, easier setup
- **Celery**: Mature, Redis/RabbitMQ backends, extensive monitoring
- **Kafka**: High throughput, complex setup, better for event streams
- Consider factors: deployment complexity, monitoring tools, team expertise
- Implement task queues for generation processing, status updates, cleanup

#### 28. @dev Decide on model discovery vs manual registration @question: Auto-discover models or manual registration?
Choose model management strategy:
- **Auto-discovery**: Scan ComfyUI directories, automatic model detection
  - Pros: No manual work, always up-to-date
  - Cons: Security risk, may include unwanted models
- **Manual registration**: Admin interface or CLI for model management
  - Pros: Better control, security validation, metadata management
  - Cons: Requires maintenance, may become outdated
- Consider hybrid approach: auto-discovery + manual approval/filtering

## Skipped Test Requirements

Tests marked with `@skipped-until-REQUIREMENT` need the following infrastructure before they can be enabled:

- **COMFYUI_INTEGRATION**: Requires ComfyUI instance running and proper integration with workflow execution
- **API_ENDPOINTS**: Requires API endpoints to be implemented/working as expected by tests
- **RATE_LIMITING_MIDDLEWARE**: Requires rate limiting middleware to be implemented
- **ENHANCED_ERROR_SERVICE**: Requires additional error service features (help links, feedback collection, progressive disclosure)
- **MULTILINGUAL_SUPPORT**: Requires internationalization support for error messages
- **ACCESSIBILITY_FEATURES**: Requires accessibility metadata and features in error responses
- **SCHEMA_FINALIZATION**: Requires database schema to be finalized with correct field structures for sampler parameters