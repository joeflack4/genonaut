"""Integration tests for content endpoint tag filtering enhancements."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from genonaut.db.schema import ContentItem


def _create_content(
    db_session: Session,
    *,
    title: str,
    creator_id,
    tags,
):
    """Utility to insert a ContentItem with common defaults."""

    content = ContentItem(
        title=title,
        content_type="image",
        content_data=f"/content/{title.replace(' ', '_').lower()}.png",
        path_thumb="/thumbs/placeholder.png",
        prompt=f"Prompt for {title}",
        creator_id=creator_id,
        item_metadata={"source": "test"},
        tags=tags,
        is_private=False,
        quality_score=0.8,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    return content


def test_unified_content_filters_by_single_tag_name(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    _create_content(db_session, title="Sunrise Peaks", creator_id=sample_user.id, tags=["nature", "mountain"])
    _create_content(db_session, title="Forest Walk", creator_id=sample_user.id, tags=["nature", "forest"])
    _create_content(db_session, title="City Lights", creator_id=sample_user.id, tags=["city", "night"])

    response = api_client.get(
        "/api/v1/content/unified",
        params={"tag_names": "nature", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    titles = {item["title"] for item in payload["items"]}

    assert titles == {"Sunrise Peaks", "Forest Walk"}
    assert payload["pagination"]["total_count"] == 2


def test_unified_content_tag_match_all_requires_all_tags(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    _create_content(db_session, title="Sunrise Peaks", creator_id=sample_user.id, tags=["nature", "mountain"])
    _create_content(db_session, title="Forest Walk", creator_id=sample_user.id, tags=["nature", "forest"])

    response = api_client.get(
        "/api/v1/content/unified",
        params=[
            ("tag_names", "nature"),
            ("tag_names", "mountain"),
            ("tag_match", "all"),
            ("page", "1"),
            ("page_size", "10"),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]

    assert len(items) == 1
    assert items[0]["title"] == "Sunrise Peaks"
    assert payload["pagination"]["total_count"] == 1
