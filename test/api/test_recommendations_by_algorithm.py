"""API tests for recommendations by algorithm."""
from fastapi.testclient import TestClient

def test_by_algorithm(api_client: TestClient):
    response = api_client.get("/api/v1/recommendations/by-algorithm/collaborative")
    assert response.status_code in [200, 404]
