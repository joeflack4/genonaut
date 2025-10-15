"""API integration tests for content tag filtering.

Tests creating content with tags and querying via unified API with tag filters.
Verifies correct items returned for single/multiple tags with 'any' and 'all' logic.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from genonaut.db.schema import ContentItem, Tag


def test_create_and_query_with_single_tag(api_client: TestClient, db_session: Session, sample_user):
    """Test creating content with tags and querying with single tag filter."""
    from test.conftest import sync_content_tags_for_tests

    # Create tags
    nature_tag = Tag(id=uuid4(), name="Nature", tag_metadata={})
    city_tag = Tag(id=uuid4(), name="City", tag_metadata={})
    db_session.add_all([nature_tag, city_tag])
    db_session.commit()

    # Create content with different tags
    content1 = ContentItem(
        title="Forest Scene",
        content_type="image",
        content_data="/content/forest.png",
        path_thumb="/thumbs/placeholder.png",
        prompt="Forest scene",
        creator_id=sample_user.id,
        item_metadata={},
        is_private=False,
        quality_score=0.8,
    )
    content2 = ContentItem(
        title="City Skyline",
        content_type="image",
        content_data="/content/city.png",
        path_thumb="/thumbs/placeholder.png",
        prompt="City skyline",
        creator_id=sample_user.id,
        item_metadata={},
        is_private=False,
        quality_score=0.8,
    )
    db_session.add_all([content1, content2])
    db_session.commit()

    # Sync tags
    sync_content_tags_for_tests(db_session, content1.id, 'regular', [str(nature_tag.id)])
    sync_content_tags_for_tests(db_session, content2.id, 'regular', [str(city_tag.id)])

    # Query with single tag filter
    response = api_client.get(
        "/api/v1/content/unified",
        params={"page": 1, "page_size": 20, "tag_names": str(nature_tag.id)},
    )

    assert response.status_code == 200
    payload = response.json()

    # Should find content with Nature tag
    titles = [item["title"] for item in payload["items"]]
    assert "Forest Scene" in titles
    assert "City Skyline" not in titles


def test_query_with_multiple_tags_any_logic(api_client: TestClient, db_session: Session, sample_user):
    """Test querying with multiple tags using 'any' (OR) logic."""
    from test.conftest import sync_content_tags_for_tests

    # Create tags
    tag1 = Tag(id=uuid4(), name="Mountain", tag_metadata={})
    tag2 = Tag(id=uuid4(), name="Beach", tag_metadata={})
    tag3 = Tag(id=uuid4(), name="Desert", tag_metadata={})
    db_session.add_all([tag1, tag2, tag3])
    db_session.commit()

    # Create content with different tag combinations
    items_data = [
        ("Mountain Sunset", [str(tag1.id)]),
        ("Beach Waves", [str(tag2.id)]),
        ("Desert Dunes", [str(tag3.id)]),
        ("Mountain Beach Combo", [str(tag1.id), str(tag2.id)]),
    ]

    for title, tag_ids in items_data:
        content = ContentItem(
            title=title,
            content_type="image",
            content_data=f"/content/{title.replace(' ', '_').lower()}.png",
            path_thumb="/thumbs/placeholder.png",
            prompt=f"Prompt for {title}",
            creator_id=sample_user.id,
            item_metadata={},
            is_private=False,
            quality_score=0.8,
        )
        db_session.add(content)
        db_session.commit()
        sync_content_tags_for_tests(db_session, content.id, 'regular', tag_ids)

    # Query with multiple tags, 'any' logic (default)
    response = api_client.get(
        "/api/v1/content/unified",
        params=[
            ("page", 1),
            ("page_size", 20),
            ("tag_names", str(tag1.id)),
            ("tag_names", str(tag2.id)),
            ("tag_match", "any"),
        ],
    )

    assert response.status_code == 200
    payload = response.json()

    titles = [item["title"] for item in payload["items"]]

    # Should match items with Mountain OR Beach
    assert "Mountain Sunset" in titles
    assert "Beach Waves" in titles
    assert "Mountain Beach Combo" in titles
    # Should NOT match Desert (has tag3 only)
    assert "Desert Dunes" not in titles


def test_query_with_multiple_tags_all_logic(api_client: TestClient, db_session: Session, sample_user):
    """Test querying with multiple tags using 'all' (AND) logic."""
    from test.conftest import sync_content_tags_for_tests

    # Create tags
    tag1 = Tag(id=uuid4(), name="Nature", tag_metadata={})
    tag2 = Tag(id=uuid4(), name="Water", tag_metadata={})
    tag3 = Tag(id=uuid4(), name="Sunset", tag_metadata={})
    db_session.add_all([tag1, tag2, tag3])
    db_session.commit()

    # Create content with different tag combinations
    items_data = [
        ("Nature Scene", [str(tag1.id)]),
        ("Water Scene", [str(tag2.id)]),
        ("Nature + Water", [str(tag1.id), str(tag2.id)]),
        ("All Three Tags", [str(tag1.id), str(tag2.id), str(tag3.id)]),
    ]

    for title, tag_ids in items_data:
        content = ContentItem(
            title=title,
            content_type="image",
            content_data=f"/content/{title.replace(' ', '_').lower()}.png",
            path_thumb="/thumbs/placeholder.png",
            prompt=f"Prompt for {title}",
            creator_id=sample_user.id,
            item_metadata={},
            is_private=False,
            quality_score=0.8,
        )
        db_session.add(content)
        db_session.commit()
        sync_content_tags_for_tests(db_session, content.id, 'regular', tag_ids)

    # Query with multiple tags, 'all' logic
    response = api_client.get(
        "/api/v1/content/unified",
        params=[
            ("page", 1),
            ("page_size", 20),
            ("tag_names", str(tag1.id)),
            ("tag_names", str(tag2.id)),
            ("tag_match", "all"),
        ],
    )

    assert response.status_code == 200
    payload = response.json()

    titles = [item["title"] for item in payload["items"]]

    # Should match only items with BOTH Nature AND Water
    assert "Nature + Water" in titles
    assert "All Three Tags" in titles
    # Should NOT match items with only one tag
    assert "Nature Scene" not in titles
    assert "Water Scene" not in titles


def test_query_varied_tag_combinations(api_client: TestClient, db_session: Session, sample_user):
    """Test querying with varied tag combinations to ensure correct filtering."""
    from test.conftest import sync_content_tags_for_tests

    # Create 5 tags
    tags = [Tag(id=uuid4(), name=f"Tag{i}", tag_metadata={}) for i in range(5)]
    db_session.add_all(tags)
    db_session.commit()

    # Create 10 items with various tag combinations
    items_data = [
        ("Item 1", [str(tags[0].id)]),
        ("Item 2", [str(tags[1].id)]),
        ("Item 3", [str(tags[0].id), str(tags[1].id)]),
        ("Item 4", [str(tags[0].id), str(tags[2].id)]),
        ("Item 5", [str(tags[1].id), str(tags[2].id)]),
        ("Item 6", [str(tags[0].id), str(tags[1].id), str(tags[2].id)]),
        ("Item 7", [str(tags[3].id)]),
        ("Item 8", [str(tags[4].id)]),
        ("Item 9", [str(tags[0].id), str(tags[4].id)]),
        ("Item 10", [str(tags[0].id), str(tags[1].id), str(tags[2].id), str(tags[3].id)]),
    ]

    for title, tag_ids in items_data:
        content = ContentItem(
            title=title,
            content_type="image",
            content_data=f"/content/{title.replace(' ', '_').lower()}.png",
            path_thumb="/thumbs/placeholder.png",
            prompt=f"Prompt for {title}",
            creator_id=sample_user.id,
            item_metadata={},
            is_private=False,
            quality_score=0.8,
        )
        db_session.add(content)
        db_session.commit()
        sync_content_tags_for_tests(db_session, content.id, 'regular', tag_ids)

    # Query for items with Tag0 OR Tag1 (any logic)
    response_any = api_client.get(
        "/api/v1/content/unified",
        params=[
            ("page", 1),
            ("page_size", 20),
            ("tag_names", str(tags[0].id)),
            ("tag_names", str(tags[1].id)),
            ("tag_match", "any"),
        ],
    )

    assert response_any.status_code == 200
    titles_any = [item["title"] for item in response_any.json()["items"]]

    # Items with Tag0 OR Tag1
    expected_any = {"Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6", "Item 9", "Item 10"}
    actual_any = set(titles_any)
    assert expected_any.issubset(actual_any)

    # Query for items with Tag0 AND Tag1 (all logic)
    response_all = api_client.get(
        "/api/v1/content/unified",
        params=[
            ("page", 1),
            ("page_size", 20),
            ("tag_names", str(tags[0].id)),
            ("tag_names", str(tags[1].id)),
            ("tag_match", "all"),
        ],
    )

    assert response_all.status_code == 200
    titles_all = [item["title"] for item in response_all.json()["items"]]

    # Items with BOTH Tag0 AND Tag1
    expected_all = {"Item 3", "Item 6", "Item 10"}
    actual_all = set(titles_all)
    assert expected_all.issubset(actual_all)
