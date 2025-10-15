"""API integration tests for tag hierarchy refresh."""
from fastapi.testclient import TestClient

def test_hierarchy_refresh(api_client: TestClient):
    response = api_client.post("/api/v1/tags/hierarchy/refresh")
    assert response.status_code == 200
    
def test_hierarchy_updated(api_client: TestClient):
    response = api_client.get("/api/v1/tags/hierarchy")
    assert response.status_code == 200
    data = response.json()
    assert "hierarchy" in data or "nodes" in data or isinstance(data, list)
