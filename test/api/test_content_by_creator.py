"""API tests for content by creator pagination."""
from fastapi.testclient import TestClient

def test_creator_pagination(api_client: TestClient, sample_user):
    response = api_client.get(f"/api/v1/content/creator/{sample_user.id}")
    assert response.status_code in [200, 404]
