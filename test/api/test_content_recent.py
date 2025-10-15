"""
API integration tests for recent content endpoint.

Tests GET /api/v1/content/recent/all endpoint with days parameter.
"""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.mark.integration
def test_get_recent_content_endpoint_exists(api_client):
    """Test that recent content endpoint exists."""
    response = api_client.get("/api/v1/content/recent/all")

    # Should return 200 or 422, not 404
    assert response.status_code in [200, 422]


@pytest.mark.integration
def test_get_recent_content_returns_list(api_client):
    """Test that recent content endpoint returns a list."""
    response = api_client.get(
        "/api/v1/content/recent/all",
        params={'days': 7, 'limit': 10}
    )

    assert response.status_code == 200
    data = response.json()

    assert 'items' in data or 'content' in data or isinstance(data, list)


@pytest.mark.integration
def test_get_recent_content_days_7(api_client, db_session, sample_user):
    """Test that days=7 returns last week's content."""
    from genonaut.db.schema import ContentItem

    # Create content from 5 days ago (should be included)
    recent_content = ContentItem(
        creator_id=sample_user.id,
        title="Recent Content",
        content_type="image",
        content_data="/test/recent.png",
        path_thumb="/thumb/recent.png",
        prompt="recent test",
        item_metadata={},
        is_private=False,
        quality_score=0.8,
        created_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    # Create content from 10 days ago (should be excluded)
    old_content = ContentItem(
        creator_id=sample_user.id,
        title="Old Content",
        content_type="image",
        content_data="/test/old.png",
        path_thumb="/thumb/old.png",
        prompt="old test",
        item_metadata={},
        is_private=False,
        quality_score=0.7,
        created_at=datetime.now(timezone.utc) - timedelta(days=10)
    )

    db_session.add_all([recent_content, old_content])
    db_session.commit()

    recent_id = recent_content.id
    old_id = old_content.id

    # Get content from last 7 days
    response = api_client.get(
        "/api/v1/content/recent/all",
        params={'days': 7, 'limit': 100}
    )

    assert response.status_code == 200
    data = response.json()

    items = data.get('items', data.get('content', data if isinstance(data, list) else []))
    item_ids = [item['id'] for item in items]

    # Recent content should be included
    assert recent_id in item_ids

    # Old content should NOT be included
    assert old_id not in item_ids


@pytest.mark.integration
def test_get_recent_content_days_30(api_client, db_session, sample_user):
    """Test that days=30 returns last month's content."""
    from genonaut.db.schema import ContentItem

    # Create content from 20 days ago (should be included)
    content_20_days = ContentItem(
        creator_id=sample_user.id,
        title="Content 20 Days Ago",
        content_type="image",
        content_data="/test/20days.png",
        path_thumb="/thumb/20days.png",
        prompt="test",
        item_metadata={},
        is_private=False,
        quality_score=0.8,
        created_at=datetime.now(timezone.utc) - timedelta(days=20)
    )

    # Create content from 40 days ago (should be excluded)
    content_40_days = ContentItem(
        creator_id=sample_user.id,
        title="Content 40 Days Ago",
        content_type="image",
        content_data="/test/40days.png",
        path_thumb="/thumb/40days.png",
        prompt="test",
        item_metadata={},
        is_private=False,
        quality_score=0.7,
        created_at=datetime.now(timezone.utc) - timedelta(days=40)
    )

    db_session.add_all([content_20_days, content_40_days])
    db_session.commit()

    id_20 = content_20_days.id
    id_40 = content_40_days.id

    # Get content from last 30 days
    response = api_client.get(
        "/api/v1/content/recent/all",
        params={'days': 30, 'limit': 100}
    )

    assert response.status_code == 200
    data = response.json()

    items = data.get('items', data.get('content', data if isinstance(data, list) else []))
    item_ids = [item['id'] for item in items]

    # 20-day-old content should be included
    assert id_20 in item_ids

    # 40-day-old content should NOT be included
    assert id_40 not in item_ids


@pytest.mark.integration
def test_get_recent_content_respects_limit(api_client):
    """Test that limit parameter is respected."""
    response = api_client.get(
        "/api/v1/content/recent/all",
        params={'days': 7, 'limit': 3}
    )

    assert response.status_code == 200
    data = response.json()

    items = data.get('items', data.get('content', data if isinstance(data, list) else []))

    # Should return at most 3 items
    assert len(items) <= 3


@pytest.mark.integration
def test_get_recent_content_date_filtering_accurate(api_client, db_session, sample_user):
    """Test that date filtering is accurate (not off by one day)."""
    from genonaut.db.schema import ContentItem

    # Create content from 6 days ago (should be included in days=7 filter)
    recent_content = ContentItem(
        creator_id=sample_user.id,
        title="Content 6 Days Ago",
        content_type="image",
        content_data="/test/6days.png",
        path_thumb="/thumb/6days.png",
        prompt="test",
        item_metadata={},
        is_private=False,
        quality_score=0.8,
        created_at=datetime.now(timezone.utc) - timedelta(days=6)
    )

    db_session.add(recent_content)
    db_session.commit()

    content_id = recent_content.id

    # Get content from last 7 days - should include content from 6 days ago
    response = api_client.get(
        "/api/v1/content/recent/all",
        params={'days': 7, 'limit': 100}
    )

    assert response.status_code == 200
    data = response.json()

    items = data.get('items', data.get('content', data if isinstance(data, list) else []))
    item_ids = [item['id'] for item in items]

    # Content from 6 days ago should be included
    assert content_id in item_ids
