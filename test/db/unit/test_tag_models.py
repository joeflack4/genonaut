"""Unit tests for tag-related database schema models.

Tests the Tag, TagParent, and TagRating models.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from genonaut.db.schema import Base, User, Tag, TagParent, TagRating


class TestTagModel:
    """Test cases for Tag model."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        # Use PostgreSQL test database (provided by conftest.py)
        self.session = db_session

    def test_tag_creation(self):
        """Test Tag model creation and basic attributes."""
        tag = Tag(
            name="Abstract Art",
            tag_metadata={"category": "art"},
        )

        assert tag.name == "Abstract Art"
        assert tag.tag_metadata == {"category": "art"}
        assert tag.id is None  # Not persisted yet

        # Test after persistence
        self.session.add(tag)
        self.session.commit()
        assert tag.id is not None
        assert isinstance(tag.id, uuid.UUID)
        assert isinstance(tag.created_at, datetime)
        assert isinstance(tag.updated_at, datetime)

    def test_tag_name_unique_constraint(self):
        """Test that Tag model enforces unique name constraint."""
        tag1 = Tag(name="Landscape", tag_metadata={})
        self.session.add(tag1)
        self.session.commit()

        # Try to create tag with duplicate name
        tag2 = Tag(name="Landscape", tag_metadata={})
        self.session.add(tag2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_tag_defaults(self):
        """Test Tag model default values."""
        tag = Tag(name="Portrait")

        self.session.add(tag)
        self.session.commit()

        # tag_metadata should default to empty dict
        assert tag.tag_metadata == {}
        assert tag.created_at is not None
        assert tag.updated_at is not None

    def test_tag_metadata_can_be_empty(self):
        """Test that tag_metadata can be an empty dict."""
        tag = Tag(name=f"Minimalism-{uuid.uuid4().hex[:8]}", tag_metadata={})

        self.session.add(tag)
        self.session.commit()

        assert tag.tag_metadata == {}

    def test_tag_metadata_can_store_complex_data(self):
        """Test that tag_metadata can store complex JSON data."""
        metadata = {
            "description": "A style of art",
            "examples": ["example1", "example2"],
            "nested": {"key": "value"}
        }
        tag = Tag(name="Surrealism", tag_metadata=metadata)

        self.session.add(tag)
        self.session.commit()

        # Re-query to ensure it was stored correctly
        retrieved_tag = self.session.query(Tag).filter(Tag.name == "Surrealism").first()
        assert retrieved_tag.tag_metadata == metadata


class TestTagParentModel:
    """Test cases for TagParent model (parent-child relationships)."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        # Use PostgreSQL test database (provided by conftest.py)
        self.session = db_session

        # Create test tags
        self.parent_tag = Tag(name="Art Styles", tag_metadata={})
        self.child_tag = Tag(name="Impressionism", tag_metadata={})

        self.session.add_all([self.parent_tag, self.child_tag])
        self.session.commit()

    def test_tag_parent_creation(self):
        """Test TagParent model creation."""
        relationship = TagParent(
            tag_id=self.child_tag.id,
            parent_id=self.parent_tag.id
        )

        self.session.add(relationship)
        self.session.commit()

        # Verify relationship was created
        assert relationship.tag_id == self.child_tag.id
        assert relationship.parent_id == self.parent_tag.id

    def test_tag_parent_composite_primary_key(self):
        """Test that TagParent enforces composite primary key uniqueness."""
        relationship1 = TagParent(
            tag_id=self.child_tag.id,
            parent_id=self.parent_tag.id
        )
        self.session.add(relationship1)
        self.session.commit()

        # Try to create duplicate relationship
        relationship2 = TagParent(
            tag_id=self.child_tag.id,
            parent_id=self.parent_tag.id
        )
        self.session.add(relationship2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_tag_parent_foreign_key_constraint(self):
        """Test that TagParent enforces foreign key constraints."""
        non_existent_uuid = uuid.uuid4()

        # Try to create relationship with non-existent tag
        relationship = TagParent(
            tag_id=non_existent_uuid,
            parent_id=self.parent_tag.id
        )
        self.session.add(relationship)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_tag_parent_cascade_delete(self):
        """Test that deleting a tag cascades to TagParent relationships."""
        # Create relationship
        relationship = TagParent(
            tag_id=self.child_tag.id,
            parent_id=self.parent_tag.id
        )
        self.session.add(relationship)
        self.session.commit()

        # Delete the child tag
        self.session.delete(self.child_tag)
        self.session.commit()

        # Relationship should be automatically deleted
        remaining_rels = self.session.query(TagParent).all()
        assert len(remaining_rels) == 0

    def test_tag_can_have_multiple_parents(self):
        """Test polyhierarchy: a tag can have multiple parents."""
        parent_tag2 = Tag(name="Visual Arts", tag_metadata={})
        self.session.add(parent_tag2)
        self.session.commit()

        # Create two parent relationships for the same child
        rel1 = TagParent(tag_id=self.child_tag.id, parent_id=self.parent_tag.id)
        rel2 = TagParent(tag_id=self.child_tag.id, parent_id=parent_tag2.id)

        self.session.add_all([rel1, rel2])
        self.session.commit()

        # Verify child has two parents
        parent_count = self.session.query(TagParent).filter(
            TagParent.tag_id == self.child_tag.id
        ).count()
        assert parent_count == 2

    def test_tag_can_have_multiple_children(self):
        """Test that a tag can have multiple children."""
        child_tag2 = Tag(name="Post-Impressionism", tag_metadata={})
        self.session.add(child_tag2)
        self.session.commit()

        # Create two child relationships for the same parent
        rel1 = TagParent(tag_id=self.child_tag.id, parent_id=self.parent_tag.id)
        rel2 = TagParent(tag_id=child_tag2.id, parent_id=self.parent_tag.id)

        self.session.add_all([rel1, rel2])
        self.session.commit()

        # Verify parent has two children
        child_count = self.session.query(TagParent).filter(
            TagParent.parent_id == self.parent_tag.id
        ).count()
        assert child_count == 2


class TestTagRatingModel:
    """Test cases for TagRating model."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        # Use PostgreSQL test database (provided by conftest.py)
        self.session = db_session

        # Create test user and tag with unique identifiers to avoid cross-test collisions
        user_suffix = uuid.uuid4().hex[:8]
        tag_suffix = uuid.uuid4().hex[:8]
        self.user_username = f"testuser-{user_suffix}"
        self.user_email = f"test-{user_suffix}@example.com"
        self.tag_name = f"Digital Art {tag_suffix}"

        self.user = User(username=self.user_username, email=self.user_email)
        self.tag = Tag(name=self.tag_name, tag_metadata={})

        self.session.add_all([self.user, self.tag])
        self.session.commit()

    def test_tag_rating_creation(self):
        """Test TagRating model creation."""
        rating = TagRating(
            user_id=self.user.id,
            tag_id=self.tag.id,
            rating=4.5
        )

        self.session.add(rating)
        self.session.commit()

        assert rating.id is not None
        assert rating.user_id == self.user.id
        assert rating.tag_id == self.tag.id
        assert rating.rating == 4.5
        assert isinstance(rating.created_at, datetime)
        assert isinstance(rating.updated_at, datetime)

    def test_tag_rating_unique_constraint(self):
        """Test that a user can only rate a tag once."""
        rating1 = TagRating(
            user_id=self.user.id,
            tag_id=self.tag.id,
            rating=4.0
        )
        self.session.add(rating1)
        self.session.commit()

        # Try to create another rating for same user and tag
        rating2 = TagRating(
            user_id=self.user.id,
            tag_id=self.tag.id,
            rating=5.0
        )
        self.session.add(rating2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_tag_rating_allows_half_stars(self):
        """Test that half-star ratings (0.5 increments) are allowed."""
        valid_ratings = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

        for i, rating_value in enumerate(valid_ratings):
            tag = Tag(name=f"Test Tag {i}", tag_metadata={})
            self.session.add(tag)
            self.session.flush()

            rating = TagRating(
                user_id=self.user.id,
                tag_id=tag.id,
                rating=rating_value
            )
            self.session.add(rating)

        self.session.commit()

        # All ratings should be persisted
        rating_count = self.session.query(TagRating).count()
        assert rating_count == len(valid_ratings)

    def test_tag_rating_foreign_keys(self):
        """Test that TagRating enforces foreign key constraints."""
        non_existent_uuid = uuid.uuid4()

        # Try to create rating with non-existent user
        rating = TagRating(
            user_id=non_existent_uuid,
            tag_id=self.tag.id,
            rating=3.0
        )
        self.session.add(rating)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_multiple_users_can_rate_same_tag(self):
        """Test that multiple users can rate the same tag."""
        suffix = uuid.uuid4().hex[:8]
        user2 = User(
            username=f"testuser-{suffix}",
            email=f"test-{suffix}@example.com",
        )
        self.session.add(user2)
        self.session.commit()

        rating1 = TagRating(user_id=self.user.id, tag_id=self.tag.id, rating=4.0)
        rating2 = TagRating(user_id=user2.id, tag_id=self.tag.id, rating=5.0)

        self.session.add_all([rating1, rating2])
        self.session.commit()

        # Verify both ratings exist
        rating_count = self.session.query(TagRating).filter(
            TagRating.tag_id == self.tag.id
        ).count()
        assert rating_count == 2

    def test_user_can_rate_multiple_tags(self):
        """Test that a user can rate multiple different tags."""
        tag2 = Tag(name="3D Art", tag_metadata={})
        self.session.add(tag2)
        self.session.commit()

        rating1 = TagRating(user_id=self.user.id, tag_id=self.tag.id, rating=4.0)
        rating2 = TagRating(user_id=self.user.id, tag_id=tag2.id, rating=5.0)

        self.session.add_all([rating1, rating2])
        self.session.commit()

        # Verify user has rated both tags
        rating_count = self.session.query(TagRating).filter(
            TagRating.user_id == self.user.id
        ).count()
        assert rating_count == 2

    def test_tag_rating_relationships(self):
        """Test that TagRating relationships to User and Tag work."""
        rating = TagRating(
            user_id=self.user.id,
            tag_id=self.tag.id,
            rating=4.0
        )
        self.session.add(rating)
        self.session.commit()

        # Test relationships
        assert rating.user is not None
        assert rating.user.username == self.user_username
        assert rating.tag is not None
        assert rating.tag.name == self.tag_name
