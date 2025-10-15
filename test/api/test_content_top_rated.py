"""
API integration tests for top-rated content endpoint.

Tests GET /api/v1/content/top-rated/all endpoint.
"""
import pytest


@pytest.mark.integration
def test_get_top_rated_content_endpoint_exists(api_client):
    """Test that top-rated content endpoint exists."""
    response = api_client.get("/api/v1/content/top-rated/all")

    # Should return 200 or 422 (if missing required params), not 404
    assert response.status_code in [200, 422]


@pytest.mark.integration
def test_get_top_rated_content_returns_list(api_client, sample_user):
    """Test that top-rated endpoint returns a list."""
    response = api_client.get(
        "/api/v1/content/top-rated/all",
        params={'limit': 10}
    )

    assert response.status_code == 200
    data = response.json()

    assert 'items' in data or 'content' in data or isinstance(data, list)


@pytest.mark.integration
def test_get_top_rated_content_respects_limit(api_client, sample_user):
    """Test that limit parameter works correctly."""
    response = api_client.get(
        "/api/v1/content/top-rated/all",
        params={'limit': 5}
    )

    assert response.status_code == 200
    data = response.json()

    # Extract items list
    items = data.get('items', data.get('content', data if isinstance(data, list) else []))

    # Should return at most 5 items
    assert len(items) <= 5


@pytest.mark.integration
def test_get_top_rated_content_sorted_by_quality(api_client, db_session, sample_user):
    """Test that results are sorted by quality_score descending."""
    # Create some test content with different quality scores
    from genonaut.db.schema import ContentItem
    from datetime import datetime, timezone

    content_items = [
        ContentItem(content_type="image", path_thumb="/thumb/test.png", item_metadata={}, is_private=False, 
            creator_id=sample_user.id,
            title=f"Test Content {i}",
            prompt="test prompt",
            content_data=f"/test/path{i}.png",
            quality_score=0.1 * i,  # 0.1, 0.2, 0.3, 0.4, 0.5
            created_at=datetime.now(timezone.utc)
        )
        for i in range(1, 6)
    ]

    db_session.add_all(content_items)
    db_session.commit()

    # Get top rated
    response = api_client.get(
        "/api/v1/content/top-rated/all",
        params={'limit': 5}
    )

    assert response.status_code == 200
    data = response.json()

    items = data.get('items', data.get('content', data if isinstance(data, list) else []))

    if len(items) >= 2:
        # Quality scores should be in descending order
        scores = [item.get('quality_score', 0) for item in items if item.get('quality_score') is not None]

        if len(scores) >= 2:
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], "Quality scores should be descending"


@pytest.mark.integration
def test_get_top_rated_content_limit_validation(api_client):
    """Test that limit parameter works correctly."""
    # Test with valid limit
    response = api_client.get(
        "/api/v1/content/top-rated/all",
        params={'limit': 5}
    )

    # Should return 200 success
    assert response.status_code == 200

    # Try with negative limit (may or may not be validated)
    response_neg = api_client.get(
        "/api/v1/content/top-rated/all",
        params={'limit': -1}
    )

    # Should return either 200 (with empty results) or 422 (validation error)
    assert response_neg.status_code in [200, 422]


@pytest.mark.integration
def test_get_top_rated_content_empty_database(api_client):
    """Test top-rated endpoint with empty database."""
    response = api_client.get(
        "/api/v1/content/top-rated/all",
        params={'limit': 10}
    )

    # Should return 200 with empty list
    assert response.status_code == 200
    data = response.json()

    items = data.get('items', data.get('content', data if isinstance(data, list) else []))

    # Should be a list (possibly empty)
    assert isinstance(items, list)
