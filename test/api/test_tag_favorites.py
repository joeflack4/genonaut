"""Integration tests for tag favorites endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_add_favorite_updates_user_record(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    target_tag = sample_tags["child"]

    response = api_client.post(
        f"/api/v1/tags/{target_tag.id}/favorite",
        params={"user_id": str(sample_user.id)},
    )

    assert response.status_code == 200, response.json()
    db_session.refresh(sample_user)
    assert str(target_tag.id) in [str(tag_id) for tag_id in sample_user.favorite_tag_ids]


def test_get_favorites_returns_summary(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    api_client.post(
        f"/api/v1/tags/{sample_tags['root'].id}/favorite",
        params={"user_id": str(sample_user.id)},
    )

    response = api_client.get(
        "/api/v1/tags/favorites",
        params={"user_id": str(sample_user.id)},
    )

    assert response.status_code == 200, {"body": response.json(), "url": response.request.url}
    favorites = response.json()
    assert len(favorites) == 1
    assert favorites[0]["id"] == str(sample_tags["root"].id)


def test_remove_favorite_clears_entry(
    api_client: TestClient,
    db_session: Session,
    sample_tags,
    sample_user,
):
    tag_id = sample_tags["leaf"].id
    api_client.post(
        f"/api/v1/tags/{tag_id}/favorite",
        params={"user_id": str(sample_user.id)},
    )

    response = api_client.delete(
        f"/api/v1/tags/{tag_id}/favorite",
        params={"user_id": str(sample_user.id)},
    )

    assert response.status_code == 200, response.json()
    db_session.refresh(sample_user)
    assert sample_user.favorite_tag_ids == []
