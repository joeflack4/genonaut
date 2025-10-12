"""Integration tests covering tag rating endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from genonaut.db.schema import TagRating


def test_rate_tag_creates_rating(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    tag = sample_tags["leaf"]

    response = api_client.post(
        f"/api/v1/tags/{tag.id}/rate",
        params={"user_id": str(sample_user.id), "rating": 4.0},
    )

    assert response.status_code == 200, {"body": response.json(), "url": response.request.url}
    payload = response.json()
    assert payload["rating"] == 4.0

    stored = (
        db_session.query(TagRating)
        .filter(TagRating.user_id == sample_user.id, TagRating.tag_id == tag.id)
        .one()
    )
    assert stored.rating == 4.0


def test_get_user_tag_rating_returns_value(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    tag = sample_tags["child"]
    db_session.add(TagRating(user_id=sample_user.id, tag_id=tag.id, rating=3.5))
    db_session.commit()

    response = api_client.get(
        f"/api/v1/tags/{tag.id}/rating",
        params={"user_id": str(sample_user.id)},
    )

    assert response.status_code == 200, {"body": response.json(), "url": response.request.url}
    assert response.json()["rating"] == 3.5


def test_get_user_tag_ratings_map_filters_ids(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    child_tag = sample_tags["child"]
    leaf_tag = sample_tags["leaf"]

    db_session.add_all(
        [
            TagRating(user_id=sample_user.id, tag_id=child_tag.id, rating=2.5),
            TagRating(user_id=sample_user.id, tag_id=leaf_tag.id, rating=4.0),
        ]
    )
    db_session.commit()

    response = api_client.get(
        "/api/v1/tags/ratings",
        params=[
            ("user_id", str(sample_user.id)),
            ("tag_ids", str(child_tag.id)),
            ("tag_ids", str(leaf_tag.id)),
        ],
    )

    assert response.status_code == 200, {"body": response.json(), "url": response.request.url}
    ratings = response.json()["ratings"]
    assert str(child_tag.id) in ratings
    assert ratings[str(child_tag.id)] == 2.5
    assert ratings[str(leaf_tag.id)] == 4.0


def test_delete_tag_rating_removes_entry(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    tag = sample_tags["root"]
    db_session.add(TagRating(user_id=sample_user.id, tag_id=tag.id, rating=3.0))
    db_session.commit()

    response = api_client.delete(
        f"/api/v1/tags/{tag.id}/rate",
        params={"user_id": str(sample_user.id)},
    )

    assert response.status_code == 200, {"body": response.json(), "url": response.request.url}
    assert response.json()["success"] is True

    remaining = (
        db_session.query(TagRating)
        .filter(TagRating.user_id == sample_user.id, TagRating.tag_id == tag.id)
        .first()
    )
    assert remaining is None
