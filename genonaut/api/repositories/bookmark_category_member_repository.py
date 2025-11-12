"""Bookmark category membership repository for database operations."""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc, and_, nullslast, nullsfirst
from datetime import datetime

from genonaut.db.schema import BookmarkCategoryMember, Bookmark, BookmarkCategory, ContentItemAll, UserInteraction
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class BookmarkCategoryMemberRepository(BaseRepository[BookmarkCategoryMember, Dict[str, Any], Dict[str, Any]]):
    """Repository for BookmarkCategoryMember entity operations."""

    def __init__(self, db: Session):
        # Note: BookmarkCategoryMember has composite primary key, so we don't use BaseRepository's get() directly
        self.db = db
        self.model = BookmarkCategoryMember

    def get_by_bookmark_and_category(
        self,
        bookmark_id: UUID,
        category_id: UUID
    ) -> Optional[BookmarkCategoryMember]:
        """Get membership by bookmark and category.

        Args:
            bookmark_id: Bookmark ID
            category_id: Category ID

        Returns:
            BookmarkCategoryMember or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategoryMember)
                .filter(
                    BookmarkCategoryMember.bookmark_id == bookmark_id,
                    BookmarkCategoryMember.category_id == category_id
                )
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get membership for bookmark {bookmark_id}, category {category_id}: {str(e)}")

    def get_by_bookmark(self, bookmark_id: UUID) -> List[BookmarkCategoryMember]:
        """Get all category memberships for a bookmark.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            List of category memberships

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategoryMember)
                .filter(BookmarkCategoryMember.bookmark_id == bookmark_id)
                .order_by(BookmarkCategoryMember.created_at.desc())
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get memberships for bookmark {bookmark_id}: {str(e)}")

    def get_by_category(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BookmarkCategoryMember]:
        """Get all bookmark memberships in a category.

        Args:
            category_id: Category ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of bookmark memberships

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategoryMember)
                .filter(BookmarkCategoryMember.category_id == category_id)
                .order_by(
                    BookmarkCategoryMember.position.asc().nullslast(),
                    BookmarkCategoryMember.created_at.desc()
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get memberships for category {category_id}: {str(e)}")

    def get_bookmarks_in_category(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bookmark]:
        """Get bookmarks in a category with position ordering.

        Args:
            category_id: Category ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of bookmarks in the category

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Bookmark)
                .join(
                    BookmarkCategoryMember,
                    BookmarkCategoryMember.bookmark_id == Bookmark.id
                )
                .filter(
                    BookmarkCategoryMember.category_id == category_id,
                    Bookmark.deleted_at.is_(None)
                )
                .order_by(
                    BookmarkCategoryMember.position.asc().nullslast(),
                    BookmarkCategoryMember.created_at.desc()
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get bookmarks in category {category_id}: {str(e)}")

    def get_bookmarks_in_category_with_content(
        self,
        category_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "user_rating_then_created",
        sort_order: str = "desc"
    ) -> List[Tuple[Bookmark, Optional[ContentItemAll], Optional[int]]]:
        """Get bookmarks in a category with content data and user ratings.

        Args:
            category_id: Category ID
            user_id: User ID (for getting user ratings)
            skip: Number of records to skip
            limit: Maximum number of records to return
            sort_field: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            List of tuples: (Bookmark, ContentItemAll, user_rating)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Base query with JOINs
            query = (
                self.db.query(Bookmark, ContentItemAll, UserInteraction.rating)
                .join(
                    BookmarkCategoryMember,
                    BookmarkCategoryMember.bookmark_id == Bookmark.id
                )
                .filter(
                    BookmarkCategoryMember.category_id == category_id,
                    Bookmark.deleted_at.is_(None)
                )
                # JOIN with content_items_all using composite key
                .outerjoin(
                    ContentItemAll,
                    and_(
                        Bookmark.content_id == ContentItemAll.id,
                        Bookmark.content_source_type == ContentItemAll.source_type
                    )
                )
                # LEFT JOIN with user_interactions to get user's rating
                .outerjoin(
                    UserInteraction,
                    and_(
                        UserInteraction.user_id == user_id,
                        UserInteraction.content_item_id == Bookmark.content_id
                    )
                )
            )

            # Apply sorting
            order_func = desc if sort_order == "desc" else asc

            if sort_field == "user_rating_then_created":
                # Composite sort: user_rating DESC NULLS LAST, then bookmark created_at
                if sort_order == "desc":
                    query = query.order_by(
                        nullslast(desc(UserInteraction.rating)),
                        desc(Bookmark.created_at)
                    )
                else:
                    query = query.order_by(
                        nullsfirst(asc(UserInteraction.rating)),
                        asc(Bookmark.created_at)
                    )
            elif sort_field == "user_rating":
                query = query.order_by(nullslast(order_func(UserInteraction.rating)))
            elif sort_field == "quality_score":
                query = query.order_by(order_func(ContentItemAll.quality_score))
            elif sort_field == "datetime_added":
                query = query.order_by(order_func(Bookmark.created_at))
            elif sort_field == "datetime_created":
                query = query.order_by(order_func(ContentItemAll.created_at))
            elif sort_field == "alphabetical":
                query = query.order_by(order_func(ContentItemAll.title))
            else:
                # Default fallback to position ordering
                query = query.order_by(
                    BookmarkCategoryMember.position.asc().nullslast(),
                    BookmarkCategoryMember.added_at.desc()
                )

            return query.offset(skip).limit(limit).all()

        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get bookmarks with content in category {category_id}: {str(e)}")

    def add_bookmark_to_category(
        self,
        bookmark_id: UUID,
        category_id: UUID,
        user_id: UUID,
        position: Optional[int] = None
    ) -> BookmarkCategoryMember:
        """Add a bookmark to a category.

        Args:
            bookmark_id: Bookmark ID
            category_id: Category ID
            user_id: User ID (for composite FK constraint)
            position: Optional position within category

        Returns:
            Created BookmarkCategoryMember

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            membership = BookmarkCategoryMember(
                bookmark_id=bookmark_id,
                category_id=category_id,
                user_id=user_id,
                position=position,
                created_at=datetime.utcnow()
            )
            self.db.add(membership)
            self.db.commit()
            self.db.refresh(membership)
            return membership
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to add bookmark {bookmark_id} to category {category_id}: {str(e)}")

    def remove_bookmark_from_category(
        self,
        bookmark_id: UUID,
        category_id: UUID
    ) -> bool:
        """Remove a bookmark from a category.

        Args:
            bookmark_id: Bookmark ID
            category_id: Category ID

        Returns:
            True if removed successfully

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            membership = self.get_by_bookmark_and_category(bookmark_id, category_id)
            if membership is None:
                return False

            self.db.delete(membership)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to remove bookmark {bookmark_id} from category {category_id}: {str(e)}")

    def update_position(
        self,
        bookmark_id: UUID,
        category_id: UUID,
        position: int
    ) -> BookmarkCategoryMember:
        """Update bookmark position in a category.

        Args:
            bookmark_id: Bookmark ID
            category_id: Category ID
            position: New position

        Returns:
            Updated BookmarkCategoryMember

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            membership = self.get_by_bookmark_and_category(bookmark_id, category_id)
            if membership is None:
                raise DatabaseError(f"Membership not found for bookmark {bookmark_id}, category {category_id}")

            membership.position = position
            self.db.commit()
            self.db.refresh(membership)
            return membership
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update position for bookmark {bookmark_id} in category {category_id}: {str(e)}")

    def count_by_category(self, category_id: UUID) -> int:
        """Count bookmarks in a category.

        Args:
            category_id: Category ID

        Returns:
            Number of bookmarks in the category

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategoryMember)
                .filter(BookmarkCategoryMember.category_id == category_id)
                .count()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to count bookmarks in category {category_id}: {str(e)}")

    def exists(self, bookmark_id: UUID, category_id: UUID) -> bool:
        """Check if bookmark is in category.

        Args:
            bookmark_id: Bookmark ID
            category_id: Category ID

        Returns:
            True if membership exists

        Raises:
            DatabaseError: If database operation fails
        """
        return self.get_by_bookmark_and_category(bookmark_id, category_id) is not None

    def move_bookmarks_to_category(
        self,
        source_category_id: UUID,
        target_category_id: UUID
    ) -> int:
        """Move all bookmarks from source category to target category.

        Args:
            source_category_id: Category ID to move bookmarks from
            target_category_id: Category ID to move bookmarks to

        Returns:
            Number of bookmarks moved

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Update all memberships to point to new category
            result = (
                self.db.query(BookmarkCategoryMember)
                .filter(BookmarkCategoryMember.category_id == source_category_id)
                .update({BookmarkCategoryMember.category_id: target_category_id})
            )
            self.db.commit()
            return result
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(
                f"Failed to move bookmarks from {source_category_id} to {target_category_id}: {str(e)}"
            )
