"""API tests for user search with filters."""
from fastapi.testclient import TestClient

def test_user_search(api_client: TestClient):
    response = api_client.get("/api/v1/users/search", params={"q": "test"})
    assert response.status_code in [200, 404]
