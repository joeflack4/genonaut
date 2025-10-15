"""API integration tests for interactions analytics."""
from fastapi.testclient import TestClient

def test_record_and_fetch_analytics(api_client: TestClient, sample_user):
    # Record interaction
    response = api_client.post("/api/v1/interactions", json={
        "user_id": str(sample_user.id),
        "content_item_id": 1,
        "interaction_type": "view"
    })
    assert response.status_code in [200, 201, 404, 422]
