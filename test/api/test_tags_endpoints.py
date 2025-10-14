"""Integration tests for tag listing and hierarchy endpoints."""

from fastapi.testclient import TestClient

from genonaut.db.schema import TagRating


def test_list_tags_includes_rating_metadata(
    api_client: TestClient,
    db_session,
    sample_tags,
    sample_user,
):
    """GET /api/v1/tags should return paginated items with rating metadata."""

    child_tag = sample_tags["child"]
    rating = TagRating(user_id=sample_user.id, tag_id=child_tag.id, rating=4.5)
    db_session.add(rating)
    db_session.commit()

    response = api_client.get("/api/v1/tags/", params={"page": 1, "page_size": 10})

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["pagination"]["total_count"] == 3

    child_entry = next(item for item in payload["items"] if item["id"] == str(child_tag.id))
    assert child_entry["average_rating"] == 4.5
    assert child_entry["rating_count"] == 1


def test_get_tag_detail_returns_relationships(
    api_client: TestClient,
    sample_tags,
):
    """GET /api/v1/tags/{id} should surface parent/child relationships."""

    child_tag = sample_tags["child"]
    root_tag = sample_tags["root"]
    leaf_tag = sample_tags["leaf"]

    response = api_client.get(f"/api/v1/tags/{child_tag.id}")

    assert response.status_code == 200, response.json()
    detail = response.json()

    parent_ids = {parent["id"] for parent in detail["parents"]}
    child_ids = {child["id"] for child in detail["children"]}

    assert str(root_tag.id) in parent_ids
    assert str(leaf_tag.id) in child_ids
    assert detail["rating_count"] == 0
    assert detail["average_rating"] is None


def test_hierarchy_endpoint_optionally_includes_ratings(
    api_client: TestClient,
    db_session,
    sample_tags,
    sample_user,
):
    """GET /api/v1/tags/hierarchy?include_ratings=true exposes aggregated ratings."""

    child_tag = sample_tags["child"]
    db_session.add(TagRating(user_id=sample_user.id, tag_id=child_tag.id, rating=3.5))
    db_session.commit()

    response = api_client.get("/api/v1/tags/hierarchy", params={"include_ratings": "true"})

    assert response.status_code == 200, response.json()
    hierarchy = response.json()

    assert hierarchy["metadata"]["totalNodes"] == 3
    child_node = next(node for node in hierarchy["nodes"] if node["id"] == child_tag.name)
    assert child_node["average_rating"] == 3.5
    assert child_node["rating_count"] == 1


def test_children_endpoint_returns_direct_descendants(
    api_client: TestClient,
    sample_tags,
):
    """GET /api/v1/tags/{id}/children returns direct child summaries."""

    root_tag = sample_tags["root"]
    child_tag = sample_tags["child"]

    response = api_client.get(f"/api/v1/tags/{root_tag.id}/children")

    assert response.status_code == 200, response.json()
    children = response.json()

    assert len(children) == 1
    assert children[0]["id"] == str(child_tag.id)
    assert children[0]["name"] == child_tag.name


def test_hierarchy_metadata_all_fields(
    api_client: TestClient,
    db_session,
    sample_tags,
):
    """GET /api/v1/tags/hierarchy validates all metadata fields are present and correct."""
    response = api_client.get("/api/v1/tags/hierarchy")

    assert response.status_code == 200
    hierarchy = response.json()

    # Validate metadata structure
    assert "metadata" in hierarchy
    metadata = hierarchy["metadata"]

    # Validate all required fields are present
    assert "totalNodes" in metadata
    assert "totalRelationships" in metadata
    assert "rootCategories" in metadata
    assert "lastUpdated" in metadata
    assert "format" in metadata
    assert "version" in metadata

    # Validate values are correct (sample_tags has 3 tags: root, child, leaf)
    # root -> child -> leaf (2 relationships)
    assert metadata["totalNodes"] == 3
    assert metadata["totalRelationships"] == 2  # root -> child, child -> leaf
    assert metadata["rootCategories"] == 1  # only root has no parent

    # Validate data types
    assert isinstance(metadata["totalNodes"], int)
    assert isinstance(metadata["totalRelationships"], int)
    assert isinstance(metadata["rootCategories"], int)
    assert isinstance(metadata["lastUpdated"], str)
    assert isinstance(metadata["format"], str)
    assert isinstance(metadata["version"], str)

    # Validate format values
    assert metadata["format"] == "flat_array"
    assert metadata["version"] == "2.0"


def test_hierarchy_empty_state(
    api_client: TestClient,
    db_session,
):
    """GET /api/v1/tags/hierarchy handles empty hierarchy gracefully."""
    # No tags in database (no sample_tags fixture used)

    response = api_client.get("/api/v1/tags/hierarchy")

    assert response.status_code == 200
    hierarchy = response.json()

    # Validate response structure
    assert "nodes" in hierarchy
    assert "metadata" in hierarchy

    # Validate empty state
    assert hierarchy["nodes"] == []
    metadata = hierarchy["metadata"]
    assert metadata["totalNodes"] == 0
    assert metadata["totalRelationships"] == 0
    assert metadata["rootCategories"] == 0

    # Validate required fields still present
    assert "lastUpdated" in metadata
    assert "format" in metadata
    assert "version" in metadata
