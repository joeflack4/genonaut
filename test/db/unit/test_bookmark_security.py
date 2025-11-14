"""Security tests for bookmark Row-Level Security (RLS) via composite foreign keys.

These tests verify that the database-level composite FK constraints correctly prevent
cross-user data contamination, even when the application layer has no authentication.

IMPORTANT: These tests verify DATABASE security constraints, not API authentication.
The API currently has NO authentication layer and accepts user_id as a query parameter,
which is insecure for production. See docs/security.md for details.
"""

import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from genonaut.db.schema import (
    User,
    ContentItemAll,
    Bookmark,
    BookmarkCategory,
    BookmarkCategoryMember
)


@pytest.fixture
def user_a(postgres_session: Session):
    """Create first test user."""
    user = User(
        id=uuid.uuid4(),
        username=f"user_a_{uuid.uuid4().hex[:8]}",
        email=f"user_a_{uuid.uuid4().hex[:8]}@example.com",
        preferences={"test": True},
        is_active=True
    )
    postgres_session.add(user)
    postgres_session.commit()
    postgres_session.refresh(user)
    return user


@pytest.fixture
def user_b(postgres_session: Session):
    """Create second test user."""
    user = User(
        id=uuid.uuid4(),
        username=f"user_b_{uuid.uuid4().hex[:8]}",
        email=f"user_b_{uuid.uuid4().hex[:8]}@example.com",
        preferences={"test": True},
        is_active=True
    )
    postgres_session.add(user)
    postgres_session.commit()
    postgres_session.refresh(user)
    return user


@pytest.fixture
def content_for_user_a(postgres_session: Session, user_a: User):
    """Create content item for user A."""
    from sqlalchemy import text
    content = ContentItemAll(
        id=postgres_session.execute(text("SELECT nextval('content_items_id_seq')")).scalar(),
        source_type='items',
        title="User A's Content",
        content_type='text',
        content_data='Test content for user A',
        prompt='Test prompt',
        creator_id=user_a.id,
        is_private=False
    )
    postgres_session.add(content)
    postgres_session.commit()
    postgres_session.refresh(content)
    return content


@pytest.fixture
def bookmark_for_user_a(postgres_session: Session, user_a: User, content_for_user_a: ContentItemAll):
    """Create bookmark for user A."""
    bookmark = Bookmark(
        id=uuid.uuid4(),
        user_id=user_a.id,
        content_id=content_for_user_a.id,
        content_source_type='items',
        note="User A's bookmark",
        pinned=False,
        is_public=False
    )
    postgres_session.add(bookmark)
    postgres_session.commit()
    postgres_session.refresh(bookmark)
    return bookmark


@pytest.fixture
def category_for_user_a(postgres_session: Session, user_a: User):
    """Create bookmark category for user A."""
    category = BookmarkCategory(
        id=uuid.uuid4(),
        user_id=user_a.id,
        name="User A's Category",
        description="Test category",
        is_public=False
    )
    postgres_session.add(category)
    postgres_session.commit()
    postgres_session.refresh(category)
    return category


@pytest.fixture
def category_for_user_b(postgres_session: Session, user_b: User):
    """Create bookmark category for user B."""
    category = BookmarkCategory(
        id=uuid.uuid4(),
        user_id=user_b.id,
        name="User B's Category",
        description="Test category",
        is_public=False
    )
    postgres_session.add(category)
    postgres_session.commit()
    postgres_session.refresh(category)
    return category


@pytest.mark.db
class TestBookmarkRLS:
    """Test bookmark Row-Level Security constraints."""

    def test_composite_fk_prevents_cross_user_bookmark_to_category(
        self,
        postgres_session: Session,
        bookmark_for_user_a: Bookmark,
        category_for_user_b: BookmarkCategory,
        user_a: User,
        user_b: User
    ):
        """Test that composite FK prevents adding User A's bookmark to User B's category.

        This verifies the core RLS mechanism: the bookmark_category_members table has
        composite FKs to both bookmarks(id, user_id) and bookmark_categories(id, user_id).

        If user_id doesn't match between bookmark and category, the FK constraint fails.
        """
        # Attempt to create membership with mismatched user_ids
        member = BookmarkCategoryMember(
            bookmark_id=bookmark_for_user_a.id,
            category_id=category_for_user_b.id,
            user_id=user_b.id  # Trying to use User B's user_id
        )
        postgres_session.add(member)

        # Should fail due to composite FK constraint
        with pytest.raises(IntegrityError) as exc_info:
            postgres_session.commit()

        # Verify it's the composite FK constraint failing
        error_msg = str(exc_info.value).lower()
        assert 'fk_bookmark_member' in error_msg or 'foreign key' in error_msg

        postgres_session.rollback()

    def test_composite_fk_allows_same_user_bookmark_to_category(
        self,
        postgres_session: Session,
        bookmark_for_user_a: Bookmark,
        category_for_user_a: BookmarkCategory,
        user_a: User
    ):
        """Test that composite FK allows adding User A's bookmark to User A's category.

        This is the positive case - when user_id matches, the operation succeeds.
        """
        # Create membership with matching user_ids
        member = BookmarkCategoryMember(
            bookmark_id=bookmark_for_user_a.id,
            category_id=category_for_user_a.id,
            user_id=user_a.id
        )
        postgres_session.add(member)

        # Should succeed
        postgres_session.commit()

        # Verify membership was created
        retrieved = postgres_session.query(BookmarkCategoryMember).filter_by(
            bookmark_id=bookmark_for_user_a.id,
            category_id=category_for_user_a.id
        ).first()

        assert retrieved is not None
        assert retrieved.user_id == user_a.id

    def test_composite_fk_prevents_wrong_user_id_in_membership(
        self,
        postgres_session: Session,
        bookmark_for_user_a: Bookmark,
        category_for_user_a: BookmarkCategory,
        user_a: User,
        user_b: User
    ):
        """Test that providing wrong user_id in membership fails FK constraints.

        Even if bookmark and category belong to same user (A), if we try to
        use a different user_id (B) in the membership, the FK constraint fails.
        """
        # Attempt to create membership with wrong user_id
        member = BookmarkCategoryMember(
            bookmark_id=bookmark_for_user_a.id,
            category_id=category_for_user_a.id,
            user_id=user_b.id  # Wrong user_id!
        )
        postgres_session.add(member)

        # Should fail due to composite FK constraint
        with pytest.raises(IntegrityError) as exc_info:
            postgres_session.commit()

        error_msg = str(exc_info.value).lower()
        assert 'fk_bookmark_member' in error_msg or 'foreign key' in error_msg

        postgres_session.rollback()

    def test_category_parent_must_belong_to_same_user(
        self,
        postgres_session: Session,
        category_for_user_a: BookmarkCategory,
        user_b: User
    ):
        """Test that hierarchical categories enforce same-user constraint.

        The bookmark_categories table has a self-referential FK with composite
        (parent_id, user_id) constraint to ensure parent belongs to same user.
        """
        # Attempt to create a child category for User B with User A's category as parent
        child_category = BookmarkCategory(
            id=uuid.uuid4(),
            user_id=user_b.id,  # User B
            name="User B's Child Category",
            parent_id=category_for_user_a.id,  # But parent belongs to User A!
            is_public=False
        )
        postgres_session.add(child_category)

        # Should fail due to composite FK constraint on parent
        with pytest.raises(IntegrityError) as exc_info:
            postgres_session.commit()

        error_msg = str(exc_info.value).lower()
        assert 'fk_bookmark_category_parent_same_user' in error_msg or 'foreign key' in error_msg

        postgres_session.rollback()


@pytest.mark.db
class TestBookmarkUniqueConstraints:
    """Test bookmark unique constraints."""

    def test_unique_bookmark_per_user_content(
        self,
        postgres_session: Session,
        user_a: User,
        content_for_user_a: ContentItemAll
    ):
        """Test that a user cannot bookmark the same content twice.

        Unique constraint: (user_id, content_id, content_source_type)
        """
        # Create first bookmark
        bookmark1 = Bookmark(
            id=uuid.uuid4(),
            user_id=user_a.id,
            content_id=content_for_user_a.id,
            content_source_type='items',
            note="First bookmark",
            pinned=False,
            is_public=False
        )
        postgres_session.add(bookmark1)
        postgres_session.commit()

        # Attempt to create duplicate
        bookmark2 = Bookmark(
            id=uuid.uuid4(),  # Different ID
            user_id=user_a.id,  # Same user
            content_id=content_for_user_a.id,  # Same content
            content_source_type='items',  # Same source type
            note="Duplicate bookmark",  # Different note
            pinned=True,  # Different settings
            is_public=True
        )
        postgres_session.add(bookmark2)

        # Should fail due to unique constraint
        with pytest.raises(IntegrityError) as exc_info:
            postgres_session.commit()

        error_msg = str(exc_info.value).lower()
        assert 'uq_bookmark_user_content' in error_msg or 'unique' in error_msg

        postgres_session.rollback()

    def test_different_users_can_bookmark_same_content(
        self,
        postgres_session: Session,
        user_a: User,
        user_b: User,
        content_for_user_a: ContentItemAll
    ):
        """Test that different users can bookmark the same content.

        The unique constraint is scoped to user_id, so different users
        can bookmark the same content.
        """
        # User A bookmarks content
        bookmark_a = Bookmark(
            id=uuid.uuid4(),
            user_id=user_a.id,
            content_id=content_for_user_a.id,
            content_source_type='items',
            note="User A's bookmark",
            pinned=False,
            is_public=False
        )
        postgres_session.add(bookmark_a)
        postgres_session.commit()

        # User B bookmarks same content - should succeed
        bookmark_b = Bookmark(
            id=uuid.uuid4(),
            user_id=user_b.id,
            content_id=content_for_user_a.id,
            content_source_type='items',
            note="User B's bookmark",
            pinned=False,
            is_public=False
        )
        postgres_session.add(bookmark_b)
        postgres_session.commit()

        # Verify both bookmarks exist
        assert postgres_session.query(Bookmark).filter_by(user_id=user_a.id).count() >= 1
        assert postgres_session.query(Bookmark).filter_by(user_id=user_b.id).count() >= 1
