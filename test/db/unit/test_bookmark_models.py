"""Unit tests for bookmark database schema models.

Tests the Bookmark, BookmarkCategory, and BookmarkCategoryMember models
including constraints, relationships, and partitioned table support.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
import uuid

from genonaut.db.schema import (
    User,
    ContentItem,
    ContentItemAuto,
    Bookmark,
    BookmarkCategory,
    BookmarkCategoryMember,
)


class TestBookmarkModels:
    """Test cases for Bookmark SQLAlchemy model."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        self.session = db_session

        # Create test users
        self.test_user1 = User(
            username="bookmark_user1",
            email="bookmark1@example.com",
        )
        self.test_user2 = User(
            username="bookmark_user2",
            email="bookmark2@example.com",
        )

        self.session.add_all([self.test_user1, self.test_user2])
        self.session.commit()

        # Create test content items (regular and auto)
        self.test_content = ContentItem(
            title="Test Image",
            content_type="image",
            content_data="/path/to/image.jpg",
            prompt="Test prompt",
            creator_id=self.test_user1.id
        )
        self.test_auto_content = ContentItemAuto(
            title="Auto Image",
            content_type="image",
            content_data="/path/to/auto.jpg",
            prompt="Auto prompt",
            creator_id=self.test_user1.id
        )

        self.session.add_all([self.test_content, self.test_auto_content])
        self.session.commit()

    def test_bookmark_creation(self):
        """Test Bookmark model creation with required fields."""
        bookmark = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items',
            note="Great image!",
            pinned=True
        )

        self.session.add(bookmark)
        self.session.commit()

        assert bookmark.user_id == self.test_user1.id
        assert bookmark.content_id == self.test_content.id
        assert bookmark.content_source_type == 'items'
        assert bookmark.note == "Great image!"
        assert bookmark.pinned is True
        assert bookmark.is_public is False  # Default
        assert bookmark.deleted_at is None

    def test_bookmark_auto_content(self):
        """Test bookmarking auto-generated content with source_type='auto'."""
        bookmark = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_auto_content.id,
            content_source_type='auto',
            note="Nice auto-generated image"
        )

        self.session.add(bookmark)
        self.session.commit()

        assert bookmark.content_source_type == 'auto'
        assert bookmark.content_id == self.test_auto_content.id

    def test_bookmark_defaults(self):
        """Test Bookmark model default values."""
        bookmark = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )

        self.session.add(bookmark)
        self.session.commit()

        assert bookmark.pinned is False
        assert bookmark.is_public is False
        assert bookmark.note is None
        assert bookmark.deleted_at is None
        assert isinstance(bookmark.created_at, datetime)
        assert isinstance(bookmark.updated_at, datetime)
        assert isinstance(bookmark.id, uuid.UUID)

    def test_bookmark_unique_constraint_user_content(self):
        """Test that a user cannot bookmark the same content twice."""
        # Create first bookmark
        bookmark1 = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )
        self.session.add(bookmark1)
        self.session.commit()

        # Try to create duplicate bookmark (same user + content)
        bookmark2 = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items',
            note="Different note"
        )
        self.session.add(bookmark2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_bookmark_different_users_same_content(self):
        """Test that different users can bookmark the same content."""
        bookmark1 = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )
        bookmark2 = Bookmark(
            user_id=self.test_user2.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )

        self.session.add_all([bookmark1, bookmark2])
        self.session.commit()

        # Should succeed - different users
        assert bookmark1.id != bookmark2.id

    def test_bookmark_relationships(self):
        """Test Bookmark relationships with User and ContentItemAll."""
        bookmark = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )

        self.session.add(bookmark)
        self.session.commit()

        # Test user relationship
        assert bookmark.user.username == "bookmark_user1"
        assert bookmark in self.test_user1.bookmarks

    def test_bookmark_soft_delete(self):
        """Test soft delete functionality with deleted_at timestamp."""
        bookmark = Bookmark(
            user_id=self.test_user1.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )

        self.session.add(bookmark)
        self.session.commit()

        # Soft delete
        bookmark.deleted_at = datetime.utcnow()
        self.session.commit()

        assert bookmark.deleted_at is not None
        # Bookmark still exists in DB but marked deleted
        found = self.session.query(Bookmark).filter_by(id=bookmark.id).first()
        assert found is not None
        assert found.deleted_at is not None


class TestBookmarkCategoryModels:
    """Test cases for BookmarkCategory SQLAlchemy model."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        self.session = db_session

        # Create test user
        self.test_user = User(
            username="category_user",
            email="category@example.com",
        )
        self.session.add(self.test_user)
        self.session.commit()

        # Create test content for cover images
        self.cover_content = ContentItem(
            title="Cover Image",
            content_type="image",
            content_data="/path/to/cover.jpg",
            prompt="Cover prompt",
            creator_id=self.test_user.id
        )
        self.session.add(self.cover_content)
        self.session.commit()

    def test_category_creation(self):
        """Test BookmarkCategory model creation with required fields."""
        category = BookmarkCategory(
            user_id=self.test_user.id,
            name="Favorites",
            description="My favorite images",
            color_hex="#FF5733",
            icon="star"
        )

        self.session.add(category)
        self.session.commit()

        assert category.name == "Favorites"
        assert category.description == "My favorite images"
        assert category.color_hex == "#FF5733"
        assert category.icon == "star"
        assert category.user_id == self.test_user.id

    def test_category_with_cover_content(self):
        """Test category with cover image from content_items_all."""
        category = BookmarkCategory(
            user_id=self.test_user.id,
            name="Nature",
            cover_content_id=self.cover_content.id,
            cover_content_source_type='items'
        )

        self.session.add(category)
        self.session.commit()

        assert category.cover_content_id == self.cover_content.id
        assert category.cover_content_source_type == 'items'

    def test_category_defaults(self):
        """Test BookmarkCategory model default values."""
        category = BookmarkCategory(
            user_id=self.test_user.id,
            name="Defaults Test"
        )

        self.session.add(category)
        self.session.commit()

        assert category.is_public is False
        assert category.description is None
        assert category.color_hex is None
        assert category.icon is None
        assert category.parent_id is None
        assert category.sort_index is None
        assert category.share_token is None
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)

    def test_category_hierarchical_parent_child(self):
        """Test hierarchical category structure with parent-child relationship."""
        parent = BookmarkCategory(
            user_id=self.test_user.id,
            name="Animals"
        )
        self.session.add(parent)
        self.session.commit()

        child = BookmarkCategory(
            user_id=self.test_user.id,
            name="Cats",
            parent_id=parent.id
        )
        self.session.add(child)
        self.session.commit()

        # Test parent_id is set correctly
        assert child.parent_id == parent.id

        # Query to verify the relationship
        queried_child = self.session.query(BookmarkCategory).filter_by(
            id=child.id
        ).first()
        assert queried_child.parent_id == parent.id

    def test_category_unique_name_per_parent(self):
        """Test unique constraint on (user_id, name, parent_id)."""
        parent = BookmarkCategory(
            user_id=self.test_user.id,
            name="Parent"
        )
        self.session.add(parent)
        self.session.commit()

        # First child
        child1 = BookmarkCategory(
            user_id=self.test_user.id,
            name="Duplicate",
            parent_id=parent.id
        )
        self.session.add(child1)
        self.session.commit()

        # Try to create another child with same name under same parent
        child2 = BookmarkCategory(
            user_id=self.test_user.id,
            name="Duplicate",
            parent_id=parent.id
        )
        self.session.add(child2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_category_same_name_different_parent(self):
        """Test that same category name is allowed under different parents."""
        parent1 = BookmarkCategory(
            user_id=self.test_user.id,
            name="Parent1"
        )
        parent2 = BookmarkCategory(
            user_id=self.test_user.id,
            name="Parent2"
        )
        self.session.add_all([parent1, parent2])
        self.session.commit()

        # Create children with same name but different parents
        child1 = BookmarkCategory(
            user_id=self.test_user.id,
            name="SameName",
            parent_id=parent1.id
        )
        child2 = BookmarkCategory(
            user_id=self.test_user.id,
            name="SameName",
            parent_id=parent2.id
        )
        self.session.add_all([child1, child2])
        self.session.commit()

        # Should succeed - different parents
        assert child1.id != child2.id

    def test_category_share_token_unique(self):
        """Test that share_token is unique across all categories."""
        token = uuid.uuid4()

        category1 = BookmarkCategory(
            user_id=self.test_user.id,
            name="Category1",
            share_token=token
        )
        self.session.add(category1)
        self.session.commit()

        # Try to create another category with same token
        category2 = BookmarkCategory(
            user_id=self.test_user.id,
            name="Category2",
            share_token=token
        )
        self.session.add(category2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_category_parent_deletion_restricted(self):
        """Test that categories with children cannot be deleted due to composite FK.

        The composite FK (parent_id, user_id) prevents simple CASCADE deletion
        because it would try to set both columns to NULL, violating the NOT NULL
        constraint on user_id. In practice, the application should either:
        1. Re-parent children before deleting parent
        2. Delete all children first
        3. Restrict deletion of categories that have children
        """
        parent = BookmarkCategory(
            user_id=self.test_user.id,
            name="ParentWithChildren"
        )
        self.session.add(parent)
        self.session.commit()

        child = BookmarkCategory(
            user_id=self.test_user.id,
            name="Child",
            parent_id=parent.id
        )
        self.session.add(child)
        self.session.commit()

        # Attempting to delete parent with children should fail
        with pytest.raises(IntegrityError):
            self.session.execute(
                text(f"DELETE FROM bookmark_categories WHERE id = '{parent.id}'")
            )
            self.session.commit()

        # Rollback the failed transaction
        self.session.rollback()


class TestBookmarkCategoryMemberModels:
    """Test cases for BookmarkCategoryMember SQLAlchemy model."""

    @pytest.fixture(autouse=True)
    def setup_method(self, db_session):
        """Set up test database and session for each test."""
        self.session = db_session

        # Create test user
        self.test_user = User(
            username="member_user",
            email="member@example.com",
        )
        self.session.add(self.test_user)
        self.session.commit()

        # Create test content
        self.test_content = ContentItem(
            title="Member Test Image",
            content_type="image",
            content_data="/path/to/member.jpg",
            prompt="Member prompt",
            creator_id=self.test_user.id
        )
        self.session.add(self.test_content)
        self.session.commit()

        # Create bookmark
        self.test_bookmark = Bookmark(
            user_id=self.test_user.id,
            content_id=self.test_content.id,
            content_source_type='items'
        )
        self.session.add(self.test_bookmark)
        self.session.commit()

        # Create category
        self.test_category = BookmarkCategory(
            user_id=self.test_user.id,
            name="Test Category"
        )
        self.session.add(self.test_category)
        self.session.commit()

    def test_member_creation(self):
        """Test BookmarkCategoryMember creation linking bookmark to category."""
        member = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id,
            position=0
        )

        self.session.add(member)
        self.session.commit()

        assert member.bookmark_id == self.test_bookmark.id
        assert member.category_id == self.test_category.id
        assert member.user_id == self.test_user.id
        assert member.position == 0
        assert isinstance(member.added_at, datetime)

    def test_member_composite_primary_key(self):
        """Test that (bookmark_id, category_id) is the primary key."""
        member1 = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id
        )
        self.session.add(member1)
        self.session.commit()

        # Try to add same bookmark to same category again
        member2 = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id,
            position=5  # Different position
        )
        self.session.add(member2)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_member_same_user_constraint(self):
        """Test that composite FK ensures bookmark and category belong to same user."""
        # Create another user with their own bookmark and category
        other_user = User(
            username="other_member_user",
            email="other_member@example.com"
        )
        self.session.add(other_user)
        self.session.commit()

        other_content = ContentItem(
            title="Other Image",
            content_type="image",
            content_data="/path/to/other.jpg",
            prompt="Other prompt",
            creator_id=other_user.id
        )
        self.session.add(other_content)
        self.session.commit()

        other_bookmark = Bookmark(
            user_id=other_user.id,
            content_id=other_content.id,
            content_source_type='items'
        )
        self.session.add(other_bookmark)
        self.session.commit()

        # Try to add user1's bookmark to user2's category
        # This should fail due to composite FK constraint
        member = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=other_user.id  # Different user - should violate FK constraint
        )
        self.session.add(member)

        with pytest.raises(IntegrityError):
            self.session.commit()

    def test_member_position_tracking(self):
        """Test position field for manual ordering within category."""
        # Create multiple bookmarks
        content2 = ContentItem(
            title="Second Image",
            content_type="image",
            content_data="/path/to/second.jpg",
            prompt="Second prompt",
            creator_id=self.test_user.id
        )
        self.session.add(content2)
        self.session.commit()

        bookmark2 = Bookmark(
            user_id=self.test_user.id,
            content_id=content2.id,
            content_source_type='items'
        )
        self.session.add(bookmark2)
        self.session.commit()

        # Add bookmarks to category with different positions
        member1 = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id,
            position=0
        )
        member2 = BookmarkCategoryMember(
            bookmark_id=bookmark2.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id,
            position=1
        )

        self.session.add_all([member1, member2])
        self.session.commit()

        # Verify positions
        assert member1.position == 0
        assert member2.position == 1

    def test_member_cascade_delete_bookmark(self):
        """Test that deleting bookmark cascades to membership.

        Uses raw SQL to test database-level CASCADE behavior.
        """
        member = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id
        )
        self.session.add(member)
        self.session.commit()

        bookmark_id = self.test_bookmark.id

        # Delete bookmark using raw SQL to test database-level CASCADE
        self.session.execute(
            text(f"DELETE FROM bookmarks WHERE id = '{bookmark_id}'")
        )
        self.session.commit()

        # Membership should be automatically deleted by CASCADE
        found = self.session.query(BookmarkCategoryMember).filter_by(
            bookmark_id=bookmark_id
        ).first()
        assert found is None

    def test_member_cascade_delete_category(self):
        """Test that deleting category cascades to membership.

        Uses raw SQL to test database-level CASCADE behavior.
        """
        member = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id
        )
        self.session.add(member)
        self.session.commit()

        category_id = self.test_category.id

        # Delete category using raw SQL to test database-level CASCADE
        self.session.execute(
            text(f"DELETE FROM bookmark_categories WHERE id = '{category_id}'")
        )
        self.session.commit()

        # Membership should be automatically deleted by CASCADE
        found = self.session.query(BookmarkCategoryMember).filter_by(
            category_id=category_id
        ).first()
        assert found is None

    def test_member_relationships(self):
        """Test BookmarkCategoryMember relationships with Bookmark and Category."""
        member = BookmarkCategoryMember(
            bookmark_id=self.test_bookmark.id,
            category_id=self.test_category.id,
            user_id=self.test_user.id
        )

        self.session.add(member)
        self.session.commit()

        # Test relationships
        assert member.bookmark.id == self.test_bookmark.id
        assert member.category.id == self.test_category.id
        assert member in self.test_bookmark.category_memberships
        assert member in self.test_category.bookmark_memberships
