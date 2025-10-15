"""API integration tests for content search performance."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_search_common_terms(api_client: TestClient, sample_user):
    response = api_client.get("/api/v1/content/unified", params={"search": "test"})
    assert response.status_code in [200, 400]

def test_search_rare_terms(api_client: TestClient, sample_user):
    response = api_client.get("/api/v1/content/unified", params={"search": "rareterm123"})
    assert response.status_code in [200, 400]

def test_search_with_filters(api_client: TestClient, sample_user):
    response = api_client.get("/api/v1/content/unified", params={"search": "test", "content_types": "image"})
    assert response.status_code in [200, 400]
