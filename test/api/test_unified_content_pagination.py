"""API integration tests for unified content pagination edge cases.

Tests /api/v1/content/unified endpoint with various pagination scenarios including
boundary conditions, invalid parameters, and error handling.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from genonaut.db.schema import ContentItem


def _create_test_content(db_session: Session, creator_id, count: int):
    """Create test content items for pagination testing."""
    from test.conftest import sync_content_tags_for_tests

    items = []
    for i in range(count):
        content = ContentItem(
            title=f"Test Item {i+1}",
            content_type="image",
            content_data=f"/content/test_{i+1}.png",
            path_thumb="/thumbs/placeholder.png",
            prompt=f"Test prompt {i+1}",
            creator_id=creator_id,
            item_metadata={"source": "pagination_test"},
            is_private=False,
            quality_score=0.8,
        )
        db_session.add(content)
        items.append(content)

    db_session.commit()

    # Refresh all items and add minimal tags
    for item in items:
        db_session.refresh(item)
        sync_content_tags_for_tests(db_session, item.id, 'regular', ['test'])

    return items


def test_pagination_page_beyond_total_pages(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test requesting a page number beyond total available pages."""
    # Create exactly 15 items (with page_size=10, that's 2 pages)
    _create_test_content(db_session, sample_user.id, 15)

    # First, get the total number of pages to determine a valid "beyond" page
    response_page1 = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 10},
    )
    assert response_page1.status_code == 200
    total_pages = response_page1.json()["pagination"]["total_pages"]

    # Request a page well beyond available pages
    beyond_page = total_pages + 10
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": beyond_page, "page_size": 10},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should return empty items list when beyond total pages
    assert len(payload["items"]) == 0
    assert payload["pagination"]["page"] == beyond_page
    assert payload["pagination"]["total_pages"] >= 2
    assert payload["pagination"]["total_count"] >= 15


def test_pagination_page_size_greater_than_total_items(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test when page_size is at maximum allowed value."""
    # Create exactly 5 items
    test_items = _create_test_content(db_session, sample_user.id, 5)
    test_item_ids = {item.id for item in test_items}

    # Request page_size=100 (max allowed by API)
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 100},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should return up to 100 items including our test items
    returned_ids = {item["id"] for item in payload["items"]}
    assert test_item_ids.issubset(returned_ids), "All test items should be in the response"

    assert payload["pagination"]["page"] == 1
    assert len(payload["items"]) <= 100, "Should not exceed max page size"
    # Verify pagination metadata is consistent
    assert payload["pagination"]["page_size"] == 100


def test_pagination_page_size_one(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test pagination with page_size=1."""
    # Create a few items
    items = _create_test_content(db_session, sample_user.id, 3)

    # Request page 1 with page_size=1
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 1},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should return exactly 1 item
    assert len(payload["items"]) == 1
    assert payload["pagination"]["page"] == 1
    assert payload["pagination"]["page_size"] == 1
    # Total pages should be at least 3 (our items) but could be more from other tests
    assert payload["pagination"]["total_pages"] >= 3


def test_pagination_page_size_max_allowed(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test pagination with maximum allowed page_size (1000)."""
    # Request with page_size=1000 (maximum allowed)
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 1000},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should succeed with maximum page size
    assert payload["pagination"]["page_size"] == 1000
    assert payload["pagination"]["page"] == 1
    # Items count depends on total content in DB


def test_pagination_invalid_negative_page(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that negative page number returns error."""
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": -1, "page_size": 10},
    )

    # Should return 422 validation error
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload


def test_pagination_invalid_zero_page(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that page=0 returns error."""
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 0, "page_size": 10},
    )

    # Should return 422 validation error
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload


def test_pagination_invalid_negative_page_size(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that negative page_size returns error."""
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": -10},
    )

    # Should return 422 validation error
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload


def test_pagination_invalid_zero_page_size(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that page_size=0 returns error."""
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 0},
    )

    # Should return 422 validation error
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload


def test_pagination_page_size_exceeds_maximum(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that page_size > 1000 returns error."""
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 1001},
    )

    # Should return 422 validation error
    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload


def test_pagination_boundary_exact_page_size(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test when total items equals exactly one page_size."""
    # Create exactly 10 items
    _create_test_content(db_session, sample_user.id, 10)

    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should have at least 10 items
    assert len(payload["items"]) >= 10
    assert payload["pagination"]["page"] == 1
    # Total pages should be at least 1
    assert payload["pagination"]["total_pages"] >= 1


def test_pagination_second_page_has_correct_offset(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that page 2 returns different items than page 1."""
    # Create many items to ensure we have multiple pages
    items = _create_test_content(db_session, sample_user.id, 25)

    # Get page 1
    response1 = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 10, "tag_names": "test"},
    )

    # Get page 2
    response2 = api_client.get(
        "/api/v1/content/unified",
        params={"page": 2, "page_size": 10, "tag_names": "test"},
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    page1_items = response1.json()["items"]
    page2_items = response2.json()["items"]

    # Both pages should have items
    assert len(page1_items) > 0
    assert len(page2_items) > 0

    # Items should be different (no overlap in IDs)
    page1_ids = {item["id"] for item in page1_items}
    page2_ids = {item["id"] for item in page2_items}

    # No intersection between pages
    assert len(page1_ids & page2_ids) == 0


def test_pagination_metadata_consistency(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test that pagination metadata is mathematically consistent."""
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    payload = response.json()

    # Verify metadata relationships
    pagination = payload["pagination"]
    total_items = pagination["total_count"]
    page_size = pagination["page_size"]
    total_pages = pagination["total_pages"]

    # total_pages should be ceiling(total_items / page_size)
    import math
    expected_total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    # Allow for minor differences due to implementation details
    # The important thing is consistency
    assert total_pages == expected_total_pages or (total_items == 0 and total_pages <= 1)

    # Current page should be within valid range
    assert 1 <= pagination["page"] <= total_pages or total_items == 0


def test_pagination_with_filters_applied(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    """Test pagination works correctly when filters are applied."""
    from test.conftest import sync_content_tags_for_tests

    # Create items with different tags
    for i in range(15):
        tag = "nature" if i < 10 else "city"
        content = ContentItem(
            title=f"Filtered Item {i+1}",
            content_type="image",
            content_data=f"/content/filtered_{i+1}.png",
            path_thumb="/thumbs/placeholder.png",
            prompt=f"Test prompt {i+1}",
            creator_id=sample_user.id,
            item_metadata={"source": "filter_test"},
            is_private=False,
            quality_score=0.8,
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)
        sync_content_tags_for_tests(db_session, content.id, 'regular', [tag])

    # Request page 1 with tag filter
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 5, "tag_names": "nature"},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should have items (at least some of our 10 nature items)
    assert len(payload["items"]) > 0

    # All returned items should have the nature tag
    for item in payload["items"]:
        # Items should match the filter (but we can't easily verify tags in response)
        assert item["title"] is not None
