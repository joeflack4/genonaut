"""API tests for interactions by type filtering."""
from fastapi.testclient import TestClient

def test_interactions_by_type(api_client: TestClient):
    response = api_client.get("/api/v1/interactions/by-type/view")
    assert response.status_code in [200, 404]
