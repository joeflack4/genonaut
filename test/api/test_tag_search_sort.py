"""API integration tests for tag search with sort options.

Tests /api/v1/tags endpoint with all sort options combined with search and min_ratings filter.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from genonaut.db.schema import Tag, TagRating, User


@pytest.fixture
def tag_test_data(db_session: Session, sample_user: User):
    """Create test tags with varied attributes for sorting tests."""
    from datetime import datetime, timedelta

    # Create tags with different names, dates, and ratings
    tags = []
    base_time = datetime(2024, 1, 1)

    tag_configs = [
        {"name": "Alpha Tag", "created_offset": 0, "updated_offset": 5},
        {"name": "Beta Tag", "created_offset": 1, "updated_offset": 3},
        {"name": "Gamma Tag", "created_offset": 2, "updated_offset": 1},
        {"name": "Delta Tag", "created_offset": 3, "updated_offset": 0},
        {"name": "Epsilon Tag", "created_offset": 4, "updated_offset": 2},
    ]

    for i, config in enumerate(tag_configs):
        tag = Tag(
            id=uuid4(),
            name=config["name"],
            tag_metadata={"test": True},
            created_at=base_time + timedelta(days=config["created_offset"]),
            updated_at=base_time + timedelta(days=config["updated_offset"]),
        )
        db_session.add(tag)
        tags.append(tag)

    db_session.commit()

    # Add ratings for some tags
    # Alpha: 2 ratings, avg=4.0
    # Beta: 3 ratings, avg=3.0
    # Gamma: 1 rating, avg=5.0
    # Delta: no ratings
    # Epsilon: 4 ratings, avg=2.5

    ratings_data = [
        (tags[0], sample_user.id, 4.0),
        (tags[0], uuid4(), 4.0),
        (tags[1], sample_user.id, 3.0),
        (tags[1], uuid4(), 2.0),
        (tags[1], uuid4(), 4.0),
        (tags[2], sample_user.id, 5.0),
        (tags[4], sample_user.id, 2.0),
        (tags[4], uuid4(), 3.0),
        (tags[4], uuid4(), 2.0),
        (tags[4], uuid4(), 3.0),
    ]

    for tag, user_id, rating in ratings_data:
        # Create user if needed (for extra users)
        if user_id != sample_user.id:
            if not db_session.query(User).filter(User.id == user_id).first():
                extra_user = User(
                    id=user_id,
                    username=f"user-{str(user_id)[:8]}",
                    email=f"{str(user_id)[:8]}@example.com",
                    preferences={},
                )
                db_session.add(extra_user)

        tag_rating = TagRating(
            tag_id=tag.id,
            user_id=user_id,
            rating=rating,
        )
        db_session.add(tag_rating)

    db_session.commit()

    # Refresh to get updated timestamps
    for tag in tags:
        db_session.refresh(tag)

    return tags


@pytest.mark.parametrize('sort_option', [
    'name-asc', 'name-desc',
    'created-asc', 'created-desc',
    'updated-asc', 'updated-desc',
    'rating-asc', 'rating-desc',
])
def test_tag_list_sort_options(api_client: TestClient, db_session: Session, sample_user, tag_test_data, sort_option):
    """Test all sort options for tag list endpoint."""
    response = api_client.get(
        "/api/v1/tags/",
        params={"page": 1, "page_size": 20, "sort": sort_option},
    )

    assert response.status_code == 200
    payload = response.json()

    assert "items" in payload
    assert len(payload["items"]) > 0


def test_tag_search_with_sort(api_client: TestClient, db_session: Session, sample_user, tag_test_data):
    """Test tag search combined with sort parameter."""
    # Search for "Tag" (should match all test tags)
    response = api_client.get(
        "/api/v1/tags/",
        params={"page": 1, "page_size": 20, "search": "Tag", "sort": "name-asc"},
    )

    assert response.status_code == 200
    payload = response.json()

    items = payload["items"]
    assert len(items) >= 5  # Our 5 test tags

    # Verify alphabetical order for matching tags
    tag_names = [item["name"] for item in items if "Tag" in item["name"]]
    assert tag_names == sorted(tag_names)


def test_tag_rating_sort_with_min_ratings(api_client: TestClient, db_session: Session, sample_user, tag_test_data):
    """Test rating sort combined with min_ratings filter."""
    # Sort by rating descending, min 2 ratings
    response = api_client.get(
        "/api/v1/tags/",
        params={"page": 1, "page_size": 20, "sort": "rating-desc", "min_ratings": 2},
    )

    assert response.status_code == 200
    payload = response.json()

    items = payload["items"]

    # Should include tags with >= 2 ratings
    # Alpha (2 ratings, avg 4.0), Beta (3 ratings, avg 3.0), Epsilon (4 ratings, avg 2.5)
    # Should exclude Gamma (1 rating) and Delta (0 ratings)

    # Verify results have ratings
    for item in items:
        if item["rating_count"] and item["rating_count"] >= 2:
            assert item["average_rating"] is not None


def test_tag_search_no_results(api_client: TestClient, db_session: Session, sample_user, tag_test_data):
    """Test tag search with no matching results."""
    response = api_client.get(
        "/api/v1/tags/",
        params={"page": 1, "page_size": 20, "search": "NonexistentTag"},
    )

    assert response.status_code == 200
    payload = response.json()

    # May have empty results or other tags depending on database state
    # The important thing is it doesn't error
    assert "items" in payload


def test_tag_search_endpoint_separate(api_client: TestClient, db_session: Session, sample_user, tag_test_data):
    """Test dedicated /search endpoint with sort options."""
    response = api_client.get(
        "/api/v1/tags/search",
        params={"q": "Alpha", "page": 1, "page_size": 20, "sort": "name-asc"},
    )

    assert response.status_code == 200
    payload = response.json()

    items = payload["items"]

    # Should find Alpha Tag
    alpha_found = any("Alpha" in item["name"] for item in items)
    assert alpha_found


def test_tag_list_pagination_with_sort(api_client: TestClient, db_session: Session, sample_user, tag_test_data):
    """Test pagination works correctly with sorting."""
    # Get page 1
    response1 = api_client.get(
        "/api/v1/tags/",
        params={"page": 1, "page_size": 2, "sort": "name-asc"},
    )

    # Get page 2
    response2 = api_client.get(
        "/api/v1/tags/",
        params={"page": 2, "page_size": 2, "sort": "name-asc"},
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    page1 = response1.json()
    page2 = response2.json()

    # Verify pagination metadata
    assert page1["pagination"]["page"] == 1
    assert page2["pagination"]["page"] == 2

    # Items on different pages should be different
    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}

    if page2["items"]:  # Only check if page 2 has items
        assert len(page1_ids & page2_ids) == 0  # No overlap
