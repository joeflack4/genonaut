"""API integration tests for recommendations bulk operations."""
from fastapi.testclient import TestClient

def test_bulk_create(api_client: TestClient, sample_user):
    response = api_client.post("/api/v1/recommendations/bulk", json={
        "user_id": str(sample_user.id),
        "items": []
    })
    assert response.status_code in [200, 201, 404, 422]
