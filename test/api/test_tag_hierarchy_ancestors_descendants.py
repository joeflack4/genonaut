"""API integration tests for tag hierarchy ancestors and descendants.

Tests /api/v1/tags/{tag_id}/ancestors and /api/v1/tags/{tag_id}/descendants endpoints
with varying max_depth parameters. Verifies depth metadata and recursion limits.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from genonaut.db.schema import Tag, TagParent


def test_ancestors_query_with_max_depth(api_client: TestClient, db_session: Session, sample_user):
    """Test ancestors endpoint with varying max_depth parameters."""
    # Create hierarchy: Root -> L1 -> L2 -> L3 -> L4 -> L5
    tags = []
    for i in range(6):
        tag = Tag(id=uuid4(), name=f"Level{i}", tag_metadata={})
        tags.append(tag)
        db_session.add(tag)

    db_session.flush()

    # Create parent relationships
    for i in range(1, 6):
        relationship = TagParent(tag_id=tags[i].id, parent_id=tags[i-1].id)
        db_session.add(relationship)

    db_session.commit()

    # Query ancestors of Level5 with max_depth=2
    response = api_client.get(
        f"/api/v1/tags/{tags[5].id}/ancestors",
        params={"max_depth": 2},
    )

    assert response.status_code == 200
    ancestors = response.json()

    # Verify response format (list of ancestors with name and depth)
    assert isinstance(ancestors, list)
    for ancestor in ancestors:
        assert "name" in ancestor
        assert "depth" in ancestor
        assert isinstance(ancestor["depth"], int)
        assert ancestor["depth"] >= 1


def test_descendants_query_with_max_depth(api_client: TestClient, db_session: Session, sample_user):
    """Test descendants endpoint with varying max_depth parameters."""
    # Create hierarchy: Root -> Child1, Root -> Child2, Child1 -> GrandChild1
    root = Tag(id=uuid4(), name="Root", tag_metadata={})
    child1 = Tag(id=uuid4(), name="Child1", tag_metadata={})
    child2 = Tag(id=uuid4(), name="Child2", tag_metadata={})
    grandchild1 = Tag(id=uuid4(), name="GrandChild1", tag_metadata={})
    grandchild2 = Tag(id=uuid4(), name="GrandChild2", tag_metadata={})

    db_session.add_all([root, child1, child2, grandchild1, grandchild2])
    db_session.commit()

    relationships = [
        TagParent(tag_id=child1.id, parent_id=root.id),
        TagParent(tag_id=child2.id, parent_id=root.id),
        TagParent(tag_id=grandchild1.id, parent_id=child1.id),
        TagParent(tag_id=grandchild2.id, parent_id=child1.id),
    ]
    db_session.add_all(relationships)
    db_session.commit()

    # Query descendants of Root with max_depth=1
    response1 = api_client.get(
        f"/api/v1/tags/{root.id}/descendants",
        params={"max_depth": 1},
    )

    assert response1.status_code == 200
    descendants1 = response1.json()

    # Verify response format
    assert isinstance(descendants1, list)
    for descendant in descendants1:
        assert "name" in descendant
        assert "depth" in descendant

    # Query descendants of Root with max_depth=2
    response2 = api_client.get(
        f"/api/v1/tags/{root.id}/descendants",
        params={"max_depth": 2},
    )

    assert response2.status_code == 200
    descendants2 = response2.json()

    # Verify response format
    assert isinstance(descendants2, list)
    for descendant in descendants2:
        assert "name" in descendant
        assert "depth" in descendant


def test_deep_hierarchy_depth_metadata(api_client: TestClient, db_session: Session, sample_user):
    """Test depth metadata is correct for deep hierarchies."""
    # Create 7-level deep hierarchy
    tags = []
    for i in range(7):
        tag = Tag(id=uuid4(), name=f"Depth{i}", tag_metadata={})
        tags.append(tag)
        db_session.add(tag)

    db_session.commit()

    # Create linear parent relationships
    for i in range(1, 7):
        relationship = TagParent(tag_id=tags[i].id, parent_id=tags[i-1].id)
        db_session.add(relationship)

    db_session.commit()

    # Query ancestors of Depth6 with max_depth=5
    response = api_client.get(
        f"/api/v1/tags/{tags[6].id}/ancestors",
        params={"max_depth": 5},
    )

    assert response.status_code == 200
    ancestors = response.json()

    # Verify depth values are correct
    for ancestor in ancestors:
        if ancestor["name"] == "Depth5":
            assert ancestor["depth"] == 1
        elif ancestor["name"] == "Depth4":
            assert ancestor["depth"] == 2
        elif ancestor["name"] == "Depth3":
            assert ancestor["depth"] == 3
        elif ancestor["name"] == "Depth2":
            assert ancestor["depth"] == 4
        elif ancestor["name"] == "Depth1":
            assert ancestor["depth"] == 5


def test_ancestors_no_ancestors(api_client: TestClient, db_session: Session, sample_user):
    """Test ancestors query for root tag with no parents."""
    # Create a root tag with no parents
    root = Tag(id=uuid4(), name="RootTag", tag_metadata={})
    db_session.add(root)
    db_session.commit()

    # Query ancestors
    response = api_client.get(
        f"/api/v1/tags/{root.id}/ancestors",
        params={"max_depth": 10},
    )

    assert response.status_code == 200
    ancestors = response.json()

    # Should return empty list
    assert len(ancestors) == 0


def test_descendants_no_descendants(api_client: TestClient, db_session: Session, sample_user):
    """Test descendants query for leaf tag with no children."""
    # Create a leaf tag with no children
    leaf = Tag(id=uuid4(), name="LeafTag", tag_metadata={})
    db_session.add(leaf)
    db_session.commit()

    # Query descendants
    response = api_client.get(
        f"/api/v1/tags/{leaf.id}/descendants",
        params={"max_depth": 10},
    )

    assert response.status_code == 200
    descendants = response.json()

    # Should return empty list
    assert len(descendants) == 0


def test_max_depth_boundary_value_1(api_client: TestClient, db_session: Session, sample_user):
    """Test max_depth=1 returns only immediate parents/children."""
    # Create simple hierarchy: Parent -> Child -> GrandChild
    parent = Tag(id=uuid4(), name="Parent", tag_metadata={})
    child = Tag(id=uuid4(), name="Child", tag_metadata={})
    grandchild = Tag(id=uuid4(), name="GrandChild", tag_metadata={})

    db_session.add_all([parent, child, grandchild])
    db_session.commit()

    relationships = [
        TagParent(tag_id=child.id, parent_id=parent.id),
        TagParent(tag_id=grandchild.id, parent_id=child.id),
    ]
    db_session.add_all(relationships)
    db_session.commit()

    # Query ancestors of GrandChild with max_depth=1
    response = api_client.get(
        f"/api/v1/tags/{grandchild.id}/ancestors",
        params={"max_depth": 1},
    )

    assert response.status_code == 200
    ancestors = response.json()
    assert isinstance(ancestors, list)

    # Query descendants of Parent with max_depth=1
    response2 = api_client.get(
        f"/api/v1/tags/{parent.id}/descendants",
        params={"max_depth": 1},
    )

    assert response2.status_code == 200
    descendants = response2.json()
    assert isinstance(descendants, list)


def test_max_depth_maximum_value_50(api_client: TestClient, db_session: Session, sample_user):
    """Test max_depth=50 (maximum allowed) queries deep hierarchy."""
    # Create moderately deep hierarchy (10 levels)
    tags = []
    for i in range(10):
        tag = Tag(id=uuid4(), name=f"Level{i}", tag_metadata={})
        tags.append(tag)
        db_session.add(tag)

    db_session.commit()

    for i in range(1, 10):
        relationship = TagParent(tag_id=tags[i].id, parent_id=tags[i-1].id)
        db_session.add(relationship)

    db_session.commit()

    # Query ancestors of Level9 with max_depth=50
    response = api_client.get(
        f"/api/v1/tags/{tags[9].id}/ancestors",
        params={"max_depth": 50},
    )

    assert response.status_code == 200
    ancestors = response.json()

    # Verify response format
    assert isinstance(ancestors, list)
    for ancestor in ancestors:
        assert "name" in ancestor
        assert "depth" in ancestor
        assert 1 <= ancestor["depth"] <= 50
