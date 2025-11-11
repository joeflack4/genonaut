"""Bookmark repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc, and_

from genonaut.db.schema import Bookmark, BookmarkCategory, BookmarkCategoryMember
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class BookmarkRepository(BaseRepository[Bookmark, Dict[str, Any], Dict[str, Any]]):
    """Repository for Bookmark entity operations."""

    def __init__(self, db: Session):
        super().__init__(db, Bookmark)

    def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        pinned: Optional[bool] = None,
        is_public: Optional[bool] = None,
        category_id: Optional[UUID] = None
    ) -> List[Bookmark]:
        """Get bookmarks by user with optional filtering.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            pinned: Optional filter by pinned status
            is_public: Optional filter by public status
            category_id: Optional filter by category ID

        Returns:
            List of user bookmarks

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = (
                self.db.query(Bookmark)
                .filter(Bookmark.user_id == user_id)
                .filter(Bookmark.deleted_at.is_(None))  # Exclude soft-deleted
            )

            # Apply optional filters
            if pinned is not None:
                query = query.filter(Bookmark.pinned == pinned)
            if is_public is not None:
                query = query.filter(Bookmark.is_public == is_public)
            if category_id is not None:
                # Join with category members to filter by category
                query = query.join(
                    BookmarkCategoryMember,
                    and_(
                        BookmarkCategoryMember.bookmark_id == Bookmark.id,
                        BookmarkCategoryMember.category_id == category_id
                    )
                )

            return (
                query
                .order_by(desc(Bookmark.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get bookmarks by user {user_id}: {str(e)}")

    def get_by_user_and_content(
        self,
        user_id: UUID,
        content_id: int,
        content_source_type: str
    ) -> Optional[Bookmark]:
        """Get specific bookmark by user and content.

        Args:
            user_id: User ID
            content_id: Content item ID
            content_source_type: Content source type ('items' or 'auto')

        Returns:
            Bookmark or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Bookmark)
                .filter(
                    Bookmark.user_id == user_id,
                    Bookmark.content_id == content_id,
                    Bookmark.content_source_type == content_source_type,
                    Bookmark.deleted_at.is_(None)
                )
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get bookmark for user {user_id}, content {content_id}: {str(e)}")

    def get_pinned_bookmarks(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Bookmark]:
        """Get pinned bookmarks for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of pinned bookmarks

        Raises:
            DatabaseError: If database operation fails
        """
        return self.get_by_user(user_id, skip=skip, limit=limit, pinned=True)

    def count_by_user(
        self,
        user_id: UUID,
        pinned: Optional[bool] = None,
        is_public: Optional[bool] = None,
        category_id: Optional[UUID] = None
    ) -> int:
        """Count bookmarks for a user with optional filtering.

        Args:
            user_id: User ID
            pinned: Optional filter by pinned status
            is_public: Optional filter by public status
            category_id: Optional filter by category ID

        Returns:
            Number of matching bookmarks

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = (
                self.db.query(Bookmark)
                .filter(Bookmark.user_id == user_id)
                .filter(Bookmark.deleted_at.is_(None))
            )

            # Apply optional filters
            if pinned is not None:
                query = query.filter(Bookmark.pinned == pinned)
            if is_public is not None:
                query = query.filter(Bookmark.is_public == is_public)
            if category_id is not None:
                query = query.join(
                    BookmarkCategoryMember,
                    and_(
                        BookmarkCategoryMember.bookmark_id == Bookmark.id,
                        BookmarkCategoryMember.category_id == category_id
                    )
                )

            return query.count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to count bookmarks for user {user_id}: {str(e)}")

    def soft_delete(self, bookmark_id: UUID) -> bool:
        """Soft delete a bookmark by setting deleted_at timestamp.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            True if deleted successfully

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            from datetime import datetime
            bookmark = self.get_or_404(bookmark_id)
            bookmark.deleted_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(bookmark)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to soft delete bookmark {bookmark_id}: {str(e)}")
