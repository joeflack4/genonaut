"""Integration tests for TagRepository."""

import pytest
from uuid import uuid4
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from genonaut.db.schema import Base, Tag, TagParent, TagRating, TagCardinalityStats, User
from genonaut.api.repositories.tag_repository import TagRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.exceptions import DatabaseError


# db_session fixture now provided by conftest.py (PostgreSQL)


@pytest.fixture
def repository(db_session):
    """Create TagRepository instance."""
    return TagRepository(db_session)


@pytest.fixture
def sample_tags(db_session):
    """Create sample tag hierarchy."""
    # Ensure a clean slate for each test run to avoid data leakage across tests
    db_session.query(TagRating).delete()
    db_session.query(TagParent).delete()
    db_session.query(Tag).delete()
    db_session.commit()

    # Root tags
    root1 = Tag(name="Art", tag_metadata={})
    root2 = Tag(name="Science", tag_metadata={})

    # Children of Art
    child1 = Tag(name="Digital Art", tag_metadata={})
    child2 = Tag(name="Traditional Art", tag_metadata={})

    # Grandchildren
    grandchild1 = Tag(name="3D Modeling", tag_metadata={})
    grandchild2 = Tag(name="Painting", tag_metadata={})

    db_session.add_all([root1, root2, child1, child2, grandchild1, grandchild2])
    db_session.flush()

    # Create relationships
    rel1 = TagParent(tag_id=child1.id, parent_id=root1.id)
    rel2 = TagParent(tag_id=child2.id, parent_id=root1.id)
    rel3 = TagParent(tag_id=grandchild1.id, parent_id=child1.id)
    rel4 = TagParent(tag_id=grandchild2.id, parent_id=child2.id)

    db_session.add_all([rel1, rel2, rel3, rel4])
    db_session.commit()

    return {
        "root1": root1,
        "root2": root2,
        "child1": child1,
        "child2": child2,
        "grandchild1": grandchild1,
        "grandchild2": grandchild2
    }


@pytest.fixture
def sample_user(db_session):
    """Create sample user."""
    unique_suffix = uuid4().hex[:8]
    user = User(
        username=f"testuser-{unique_suffix}",
        email=f"test-{unique_suffix}@example.com",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestTagRepositoryBasicOperations:
    """Test basic CRUD operations."""

    def test_get_by_name(self, repository, sample_tags):
        """Test getting tag by name."""
        tag = repository.get_by_name("Art")
        assert tag is not None
        assert tag.name == "Art"

    def test_get_by_name_not_found(self, repository):
        """Test getting non-existent tag."""
        tag = repository.get_by_name("NonExistent")
        assert tag is None

    def test_get_by_names(self, repository, sample_tags):
        """Test batch fetch by names."""
        tags = repository.get_by_names(["Art", "Science", "NonExistent"])
        assert len(tags) == 2
        names = [t.name for t in tags]
        assert "Art" in names
        assert "Science" in names

    def test_get_by_ids(self, repository, sample_tags):
        """Test batch fetch by IDs."""
        tag_ids = [sample_tags["root1"].id, sample_tags["root2"].id]
        tags = repository.get_by_ids(tag_ids)
        assert len(tags) == 2


class TestTagRepositoryHierarchy:
    """Test hierarchy operations."""

    def test_get_root_tags(self, repository, sample_tags):
        """Test getting root tags."""
        roots = repository.get_root_tags()
        assert len(roots) == 2
        names = [t.name for t in roots]
        assert "Art" in names
        assert "Science" in names

    def test_get_children(self, repository, sample_tags):
        """Test getting direct children."""
        children = repository.get_children(sample_tags["root1"].id)
        assert len(children) == 2
        names = [t.name for t in children]
        assert "Digital Art" in names
        assert "Traditional Art" in names

    def test_get_children_empty(self, repository, sample_tags):
        """Test getting children of leaf node."""
        children = repository.get_children(sample_tags["grandchild1"].id)
        assert len(children) == 0

    def test_get_parents(self, repository, sample_tags):
        """Test getting direct parents."""
        parents = repository.get_parents(sample_tags["child1"].id)
        assert len(parents) == 1
        assert parents[0].name == "Art"

    def test_get_parents_root(self, repository, sample_tags):
        """Test getting parents of root node."""
        parents = repository.get_parents(sample_tags["root1"].id)
        assert len(parents) == 0



class TestTagRepositorySearch:
    """Test search and pagination."""

    def test_search_tags(self, repository, sample_tags):
        """Test searching tags by name."""
        pagination = PaginationRequest(page=1, page_size=10)
        result = repository.search_tags("Art", pagination)

        # Should find: Art, Digital Art, Traditional Art
        assert result.pagination.total_count == 3
        names = [t.name for t in result.items]
        assert "Art" in names

    def test_search_tags_case_insensitive(self, repository, sample_tags):
        """Test case-insensitive search."""
        pagination = PaginationRequest(page=1, page_size=10)
        result = repository.search_tags("art", pagination)
        assert result.pagination.total_count == 3

    def test_search_tags_multiple_terms(self, repository, sample_tags, db_session):
        """Test multi-word queries match any term."""
        extra_tag = Tag(name="3D-render", tag_metadata={})
        db_session.add(extra_tag)
        db_session.commit()

        pagination = PaginationRequest(page=1, page_size=10)
        result = repository.search_tags("3d art", pagination)

        names = [t.name for t in result.items]
        assert any("Art" in name for name in names)
        assert result.pagination.total_count >= 1

    def test_search_tags_exact_phrase(self, repository, sample_tags, db_session):
        """Test quoted search performs exact matching."""
        extra_tag = Tag(name="3D-render", tag_metadata={})
        db_session.add(extra_tag)
        db_session.commit()

        pagination = PaginationRequest(page=1, page_size=10)
        result = repository.search_tags('"3d-render"', pagination)

        names = [t.name for t in result.items]
        assert "3D-render" in names

    def test_get_all_paginated(self, repository, sample_tags):
        """Test pagination."""
        pagination = PaginationRequest(page=1, page_size=3)
        result = repository.get_all_paginated(pagination, sort="name")

        assert len(result.items) == 3
        assert result.pagination.total_count == 6
        assert result.pagination.has_next
        assert not result.pagination.has_previous

    def test_get_all_paginated_page_2(self, repository, sample_tags):
        """Test second page."""
        pagination = PaginationRequest(page=2, page_size=3)
        result = repository.get_all_paginated(pagination, sort="name")

        assert len(result.items) == 3
        assert not result.pagination.has_next
        assert result.pagination.has_previous


class TestTagRepositoryRatings:
    """Test rating operations."""

    def test_upsert_rating_create(self, repository, sample_tags, sample_user):
        """Test creating a new rating."""
        rating = repository.upsert_rating(
            sample_user.id,
            sample_tags["root1"].id,
            4.5
        )

        assert rating.id is not None
        assert rating.rating == 4.5
        assert rating.user_id == sample_user.id
        assert rating.tag_id == sample_tags["root1"].id

    def test_upsert_rating_update(self, repository, sample_tags, sample_user):
        """Test updating existing rating."""
        # Create initial rating
        repository.upsert_rating(sample_user.id, sample_tags["root1"].id, 3.0)

        # Update it
        updated = repository.upsert_rating(sample_user.id, sample_tags["root1"].id, 5.0)
        assert updated.rating == 5.0

        # Verify only one rating exists
        from genonaut.db.schema import TagRating
        count = repository.db.query(TagRating).filter(
            TagRating.user_id == sample_user.id,
            TagRating.tag_id == sample_tags["root1"].id
        ).count()
        assert count == 1

    def test_get_user_rating(self, repository, sample_tags, sample_user):
        """Test getting user's rating."""
        repository.upsert_rating(sample_user.id, sample_tags["root1"].id, 4.0)

        rating = repository.get_user_rating(sample_user.id, sample_tags["root1"].id)
        assert rating is not None
        assert rating.rating == 4.0

    def test_get_user_rating_not_found(self, repository, sample_tags, sample_user):
        """Test getting non-existent rating."""
        rating = repository.get_user_rating(sample_user.id, sample_tags["root1"].id)
        assert rating is None

    def test_delete_rating(self, repository, sample_tags, sample_user):
        """Test deleting a rating."""
        repository.upsert_rating(sample_user.id, sample_tags["root1"].id, 4.0)

        result = repository.delete_rating(sample_user.id, sample_tags["root1"].id)
        assert result is True

        # Verify it's deleted
        rating = repository.get_user_rating(sample_user.id, sample_tags["root1"].id)
        assert rating is None

    def test_delete_rating_not_found(self, repository, sample_tags, sample_user):
        """Test deleting non-existent rating."""
        result = repository.delete_rating(sample_user.id, sample_tags["root1"].id)
        assert result is False

    def test_get_tag_average_rating(self, repository, sample_tags, sample_user, db_session):
        """Test computing average rating."""
        # Create another user
        suffix = uuid4().hex[:8]
        user2 = User(
            username=f"user-{suffix}",
            email=f"user-{suffix}@example.com",
        )
        db_session.add(user2)
        db_session.commit()

        # Add ratings
        repository.upsert_rating(sample_user.id, sample_tags["root1"].id, 4.0)
        repository.upsert_rating(user2.id, sample_tags["root1"].id, 5.0)

        avg_rating, count = repository.get_tag_average_rating(sample_tags["root1"].id)
        assert count == 2
        assert avg_rating == 4.5

    def test_get_tag_average_rating_no_ratings(self, repository, sample_tags):
        """Test average with no ratings."""
        avg_rating, count = repository.get_tag_average_rating(sample_tags["root1"].id)
        assert count == 0
        assert avg_rating == 0.0

    def test_get_tags_sorted_by_rating(self, repository, sample_tags, sample_user, db_session):
        """Test getting tags sorted by rating."""
        # Create another user
        suffix = uuid4().hex[:8]
        user2 = User(
            username=f"user-{suffix}",
            email=f"user-{suffix}@example.com",
        )
        db_session.add(user2)
        db_session.commit()

        # Add ratings to different tags
        repository.upsert_rating(sample_user.id, sample_tags["root1"].id, 5.0)
        repository.upsert_rating(user2.id, sample_tags["root1"].id, 5.0)

        repository.upsert_rating(sample_user.id, sample_tags["child1"].id, 3.0)
        repository.upsert_rating(user2.id, sample_tags["child1"].id, 4.0)

        pagination = PaginationRequest(page=1, page_size=10)
        result = repository.get_tags_sorted_by_rating(pagination, min_ratings=2)

        # Should return all tags with rated ones first (by rating desc) followed by unrated alphabetically
        names = [tag.name for tag in result.items]

        assert names[:2] == ["Art", "Digital Art"]
        assert names[2:] == ["3D Modeling", "Painting", "Science", "Traditional Art"]

        # Total count should include unrated tags as well
        assert result.pagination.total_count == 6


class TestTagRepositoryStatistics:
    """Test statistics operations."""

    def test_get_hierarchy_statistics(self, repository, sample_tags):
        """Test getting global statistics."""
        stats = repository.get_hierarchy_statistics()

        assert stats["totalNodes"] == 6
        assert stats["totalRelationships"] == 4
        assert stats["rootCategories"] == 2

    def test_get_popular_tags_aggregated(self, repository, sample_tags, db_session):
        """Test get_popular_tags() aggregating across all sources."""
        tag1 = sample_tags["root1"]
        tag2 = sample_tags["child1"]
        tag3 = sample_tags["grandchild1"]

        # Create cardinality stats
        stats = [
            TagCardinalityStats(tag_id=tag1.id, content_source="items", cardinality=100),
            TagCardinalityStats(tag_id=tag1.id, content_source="auto", cardinality=50),
            TagCardinalityStats(tag_id=tag2.id, content_source="items", cardinality=30),
            TagCardinalityStats(tag_id=tag2.id, content_source="auto", cardinality=20),
            TagCardinalityStats(tag_id=tag3.id, content_source="items", cardinality=10),
        ]
        db_session.add_all(stats)
        db_session.commit()

        # Get top 10 popular tags (aggregated)
        results = repository.get_popular_tags(limit=10)

        # Should return tags ordered by total cardinality (tag1: 150, tag2: 50, tag3: 10)
        assert len(results) == 3
        assert results[0][0].id == tag1.id
        assert results[0][1] == 150

        assert results[1][0].id == tag2.id
        assert results[1][1] == 50

        assert results[2][0].id == tag3.id
        assert results[2][1] == 10

    def test_get_popular_tags_filtered_by_source(self, repository, sample_tags, db_session):
        """Test get_popular_tags() filtering by content source."""
        tag1 = sample_tags["root1"]
        tag2 = sample_tags["child1"]

        stats = [
            TagCardinalityStats(tag_id=tag1.id, content_source="items", cardinality=50),
            TagCardinalityStats(tag_id=tag1.id, content_source="auto", cardinality=200),
            TagCardinalityStats(tag_id=tag2.id, content_source="items", cardinality=100),
            TagCardinalityStats(tag_id=tag2.id, content_source="auto", cardinality=10),
        ]
        db_session.add_all(stats)
        db_session.commit()

        # Filter by 'items' source
        results = repository.get_popular_tags(limit=10, content_source="items")

        # When filtering by 'items', tag2 should be first (100 > 50)
        assert len(results) == 2
        assert results[0][0].id == tag2.id
        assert results[0][1] == 100
        assert results[1][0].id == tag1.id
        assert results[1][1] == 50

    def test_get_popular_tags_with_limit(self, repository, sample_tags, db_session):
        """Test get_popular_tags() respects limit parameter."""
        tag1 = sample_tags["root1"]
        tag2 = sample_tags["child1"]
        tag3 = sample_tags["grandchild1"]

        stats = [
            TagCardinalityStats(tag_id=tag1.id, content_source="items", cardinality=100),
            TagCardinalityStats(tag_id=tag2.id, content_source="items", cardinality=75),
            TagCardinalityStats(tag_id=tag3.id, content_source="items", cardinality=50),
        ]
        db_session.add_all(stats)
        db_session.commit()

        # Limit to top 2
        results = repository.get_popular_tags(limit=2)

        assert len(results) == 2
        assert results[0][0].id == tag1.id
        assert results[1][0].id == tag2.id

    def test_get_popular_tags_with_min_cardinality(self, repository, sample_tags, db_session):
        """Test get_popular_tags() filters by minimum cardinality."""
        tag1 = sample_tags["root1"]
        tag2 = sample_tags["child1"]
        tag3 = sample_tags["grandchild1"]

        stats = [
            TagCardinalityStats(tag_id=tag1.id, content_source="items", cardinality=100),
            TagCardinalityStats(tag_id=tag2.id, content_source="items", cardinality=50),
            TagCardinalityStats(tag_id=tag3.id, content_source="items", cardinality=5),
        ]
        db_session.add_all(stats)
        db_session.commit()

        # Require minimum cardinality of 10
        results = repository.get_popular_tags(limit=10, min_cardinality=10)

        # Should exclude tag3 (cardinality=5 < min=10)
        assert len(results) == 2
        assert results[0][0].id == tag1.id
        assert results[1][0].id == tag2.id

    def test_get_popular_tags_empty_when_no_stats(self, repository, sample_tags):
        """Test get_popular_tags() returns empty list when no stats exist."""
        results = repository.get_popular_tags(limit=10)
        assert results == []
