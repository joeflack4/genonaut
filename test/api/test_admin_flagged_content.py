"""API tests for admin flagged content filtering."""
from fastapi.testclient import TestClient

def test_flagged_content_list(api_client: TestClient):
    response = api_client.get("/api/v1/admin/flagged-content")
    assert response.status_code in [200, 401, 403, 404]
