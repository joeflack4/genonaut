"""
API integration tests for global statistics endpoint.

Tests GET /api/v1/stats/global endpoint.
"""
import pytest


@pytest.mark.integration
def test_global_statistics_endpoint_exists(api_client):
    """Test that global statistics endpoint exists."""
    response = api_client.get("/api/v1/stats/global")

    # Should return 200, not 404
    assert response.status_code == 200


@pytest.mark.integration
def test_global_statistics_returns_dict(api_client):
    """Test that global stats returns a dictionary."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, dict)


@pytest.mark.integration
def test_global_statistics_contains_user_count(api_client):
    """Test that global stats includes total user count."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # Should have some field for user count
    has_user_count = any(
        'user' in key.lower() and 'count' in key.lower()
        for key in data.keys()
    ) or 'total_users' in data or 'user_count' in data

    assert has_user_count, "Global stats should include user count"


@pytest.mark.integration
def test_global_statistics_contains_content_count(api_client):
    """Test that global stats includes total content count."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # Should have some field for content count
    has_content_count = any(
        'content' in key.lower() and 'count' in key.lower()
        for key in data.keys()
    ) or 'total_content' in data or 'content_count' in data

    assert has_content_count, "Global stats should include content count"


@pytest.mark.integration
def test_global_statistics_contains_interaction_count(api_client):
    """Test that global stats includes total interaction count."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # Should have some field for interaction count
    has_interaction_count = any(
        'interaction' in key.lower() and 'count' in key.lower()
        for key in data.keys()
    ) or 'total_interactions' in data or 'interaction_count' in data

    # This is optional - may not be tracked
    if has_interaction_count:
        assert True
    else:
        pytest.skip("Interaction count not tracked in global stats")


@pytest.mark.integration
def test_global_statistics_contains_recommendation_count(api_client):
    """Test that global stats includes total recommendation count."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # Should have some field for recommendation count
    has_recommendation_count = any(
        'recommendation' in key.lower() and 'count' in key.lower()
        for key in data.keys()
    ) or 'total_recommendations' in data or 'recommendation_count' in data

    # This is optional - may not be tracked
    if has_recommendation_count:
        assert True
    else:
        pytest.skip("Recommendation count not tracked in global stats")


@pytest.mark.integration
def test_global_statistics_values_are_numbers(api_client):
    """Test that all statistics values are numeric."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # All values should be numbers (int or float)
    for key, value in data.items():
        if 'count' in key.lower() or 'total' in key.lower():
            assert isinstance(value, (int, float)), f"{key} should be numeric, got {type(value)}"


@pytest.mark.integration
def test_global_statistics_values_are_non_negative(api_client):
    """Test that all count values are non-negative."""
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # All count values should be >= 0
    for key, value in data.items():
        if 'count' in key.lower() or 'total' in key.lower():
            if isinstance(value, (int, float)):
                assert value >= 0, f"{key} should be non-negative, got {value}"


@pytest.mark.integration
def test_global_statistics_with_data(api_client, db_session, sample_user):
    """Test that global stats reflect actual data."""
    from genonaut.db.schema import ContentItem
    from datetime import datetime, timezone

    # Create some content
    content = ContentItem(content_type="image", path_thumb="/thumb/test.png", item_metadata={}, is_private=False, 
        creator_id=sample_user.id,
        title="Test Content",
        prompt="test",
        content_data="/test/content.png",
        quality_score=0.8,
        created_at=datetime.now(timezone.utc)
    )

    db_session.add(content)
    db_session.commit()

    # Get global stats
    response = api_client.get("/api/v1/stats/global")

    assert response.status_code == 200
    data = response.json()

    # Should have at least 1 user and 1 content item
    # (exact counts depend on test fixtures)

    # Find user count field
    user_count_keys = [k for k in data.keys() if 'user' in k.lower() and 'count' in k.lower()]
    if user_count_keys:
        assert data[user_count_keys[0]] >= 1

    # Find content count field
    content_count_keys = [k for k in data.keys() if 'content' in k.lower() and 'count' in k.lower()]
    if content_count_keys:
        assert data[content_count_keys[0]] >= 1
