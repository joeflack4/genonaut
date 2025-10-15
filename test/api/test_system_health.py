"""API tests for system health check."""
from fastapi.testclient import TestClient

def test_health_check(api_client: TestClient):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data or 'healthy' in str(data).lower()
