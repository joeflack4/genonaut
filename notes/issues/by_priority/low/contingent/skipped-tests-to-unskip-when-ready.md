# Candidates for Re-enabling Skipped Tests

## Skip Reason Tags
- **WEBSOCKET-TESTCLIENT-LIMITATION**: WebSocket tests that timeout due to limitations in FastAPI's TestClient. These require a real server + WebSocket client library for proper testing, or an async test harness that can properly simulate bidirectional WebSocket communication.
- **SQLITE-THREADING-LIMITATION**: Tests requiring concurrent database access from multiple threads. SQLite doesn't support concurrent writes from multiple threads - requires PostgreSQL with proper connection pooling for testing.

## Not Longrunning

### WebSocket Status Streaming
WebSocket job updates are now a core part of the frontend flow. These integration tests already mock Redis/pubsub; we should adapt them to the current FastAPI stack so we catch regressions in the new real-time experience.
- [ ] test/api/integration/test_websocket.py::test_websocket_connection_established @skipped-because-WEBSOCKET-TESTCLIENT-LIMITATION
- [ ] test/api/integration/test_websocket.py::test_websocket_relays_redis_messages @skipped-because-WEBSOCKET-TESTCLIENT-LIMITATION
- [ ] test/api/integration/test_websocket.py::test_websocket_handles_client_disconnect @skipped-because-WEBSOCKET-TESTCLIENT-LIMITATION
- [ ] test/api/integration/test_websocket.py::test_websocket_ping_pong @skipped-because-WEBSOCKET-TESTCLIENT-LIMITATION
- [ ] test/api/integration/test_websocket.py::test_multi_job_websocket_connection @skipped-because-WEBSOCKET-TESTCLIENT-LIMITATION
- [ ] test/api/integration/test_websocket.py::test_multi_job_websocket_empty_ids @skipped-because-WEBSOCKET-TESTCLIENT-LIMITATION

## Longrunning

### ComfyUI Load & Concurrency Suite
We now exercise sustained generation flows in staging; these load tests match the concurrency patterns we expect in production. Folding them into the longrunning suite would surface regressions in queue coordination or DB write throughput.
- [ ] test/integrations/comfyui/test_comfyui_mock_class_load_testing.py::test_concurrent_generation_requests_small_load @skipped-because-SQLITE-THREADING-LIMITATION
- [ ] test/integrations/comfyui/test_comfyui_mock_class_load_testing.py::test_concurrent_generation_requests_medium_load @skipped-because-SQLITE-THREADING-LIMITATION
- [ ] test/integrations/comfyui/test_comfyui_mock_class_load_testing.py::test_concurrent_generation_requests_high_load @skipped-because-SQLITE-THREADING-LIMITATION
- [ ] test/integrations/comfyui/test_comfyui_mock_class_load_testing.py::test_database_performance_under_concurrent_writes @skipped-because-SQLITE-THREADING-LIMITATION
