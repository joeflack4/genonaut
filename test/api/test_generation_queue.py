"""API tests for generation job queue processing."""
from fastapi.testclient import TestClient

def test_queue_next(api_client: TestClient):
    response = api_client.get("/api/v1/generation-jobs/queue/next")
    assert response.status_code in [200, 404]
