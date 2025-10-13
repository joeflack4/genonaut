"""Integration tests for content endpoint tag filtering enhancements."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from genonaut.db.schema import ContentItem, ContentTag


def _cleanup_user_content(db_session: Session, creator_id):
    """Remove all content for a user to ensure test isolation."""
    # Delete content_tags entries first (foreign key constraint)
    content_ids = [c.id for c in db_session.query(ContentItem).filter_by(creator_id=creator_id).all()]
    if content_ids:
        db_session.query(ContentTag).filter(
            ContentTag.content_id.in_(content_ids),
            ContentTag.content_source == 'regular'
        ).delete(synchronize_session=False)
    # Delete content items
    db_session.query(ContentItem).filter_by(creator_id=creator_id).delete()
    db_session.commit()


def _create_content(
    db_session: Session,
    *,
    title: str,
    creator_id,
    tags,
):
    """Utility to insert a ContentItem with common defaults."""
    from test.conftest import sync_content_tags_for_tests

    content = ContentItem(
        title=title,
        content_type="image",
        content_data=f"/content/{title.replace(' ', '_').lower()}.png",
        path_thumb="/thumbs/placeholder.png",
        prompt=f"Prompt for {title}",
        creator_id=creator_id,
        item_metadata={"source": "test"},
        is_private=False,
        quality_score=0.8,
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    sync_content_tags_for_tests(db_session, content.id, 'regular', tags)
    return content


def test_unified_content_filters_by_single_tag_name(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    # Clean up any existing content for this user to ensure test isolation
    _cleanup_user_content(db_session, sample_user.id)

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

    # The query returns content from all users, not just sample_user
    # So we check that our expected items are present, but there may be others from test fixtures
    assert "Sunrise Peaks" in titles
    assert "Forest Walk" in titles
    # Don't assert exact count since other tests may have created content with "nature" tag


def test_unified_content_tag_match_all_requires_all_tags(
    api_client: TestClient,
    db_session: Session,
    sample_user,
):
    # Clean up any existing content for this user to ensure test isolation
    _cleanup_user_content(db_session, sample_user.id)

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

    # Check that Sunrise Peaks is in results (it has both nature AND mountain tags)
    titles = [item["title"] for item in items]
    assert "Sunrise Peaks" in titles
    # Forest Walk should NOT be in results (has nature but not mountain)
    assert "Forest Walk" not in titles
