"""Bookmark category repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc, and_

from genonaut.db.schema import BookmarkCategory, BookmarkCategoryMember, Bookmark
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class BookmarkCategoryRepository(BaseRepository[BookmarkCategory, Dict[str, Any], Dict[str, Any]]):
    """Repository for BookmarkCategory entity operations."""

    def __init__(self, db: Session):
        super().__init__(db, BookmarkCategory)

    def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[UUID] = None,
        is_public: Optional[bool] = None,
        sort_by_index: bool = True
    ) -> List[BookmarkCategory]:
        """Get categories by user with optional filtering.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            parent_id: Optional filter by parent category ID (None for root categories)
            is_public: Optional filter by public status
            sort_by_index: If True, sort by sort_index; otherwise by created_at

        Returns:
            List of user categories

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(BookmarkCategory).filter(BookmarkCategory.user_id == user_id)

            # Apply optional filters
            if parent_id is not None:
                query = query.filter(BookmarkCategory.parent_id == parent_id)
            if is_public is not None:
                query = query.filter(BookmarkCategory.is_public == is_public)

            # Apply sorting
            if sort_by_index:
                # Sort by sort_index (nulls last), then by created_at
                query = query.order_by(
                    BookmarkCategory.sort_index.asc().nullslast(),
                    BookmarkCategory.created_at.desc()
                )
            else:
                query = query.order_by(desc(BookmarkCategory.created_at))

            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get categories by user {user_id}: {str(e)}")

    def get_by_user_and_name(
        self,
        user_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None
    ) -> Optional[BookmarkCategory]:
        """Get category by user, name, and parent.

        Args:
            user_id: User ID
            name: Category name
            parent_id: Parent category ID (None for root categories)

        Returns:
            BookmarkCategory or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(BookmarkCategory).filter(
                BookmarkCategory.user_id == user_id,
                BookmarkCategory.name == name
            )

            # Handle parent_id comparison (NULL requires special handling)
            if parent_id is None:
                query = query.filter(BookmarkCategory.parent_id.is_(None))
            else:
                query = query.filter(BookmarkCategory.parent_id == parent_id)

            return query.first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get category by name for user {user_id}: {str(e)}")

    def get_root_categories(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BookmarkCategory]:
        """Get root categories (categories without parents) for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of root categories

        Raises:
            DatabaseError: If database operation fails
        """
        return self.get_by_user(user_id, skip=skip, limit=limit, parent_id=None)

    def get_child_categories(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[BookmarkCategory]:
        """Get child categories of a parent category.

        Args:
            category_id: Parent category ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of child categories

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategory)
                .filter(BookmarkCategory.parent_id == category_id)
                .order_by(
                    BookmarkCategory.sort_index.asc().nullslast(),
                    BookmarkCategory.created_at.desc()
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get child categories for {category_id}: {str(e)}")

    def get_category_tree(self, user_id: UUID) -> List[BookmarkCategory]:
        """Get all categories for a user in tree structure.

        Args:
            user_id: User ID

        Returns:
            List of all categories (caller must build tree structure)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategory)
                .filter(BookmarkCategory.user_id == user_id)
                .order_by(
                    BookmarkCategory.sort_index.asc().nullslast(),
                    BookmarkCategory.created_at.desc()
                )
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get category tree for user {user_id}: {str(e)}")

    def count_by_user(
        self,
        user_id: UUID,
        parent_id: Optional[UUID] = None,
        is_public: Optional[bool] = None
    ) -> int:
        """Count categories for a user with optional filtering.

        Args:
            user_id: User ID
            parent_id: Optional filter by parent category ID
            is_public: Optional filter by public status

        Returns:
            Number of matching categories

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(BookmarkCategory).filter(BookmarkCategory.user_id == user_id)

            # Apply optional filters
            if parent_id is not None:
                query = query.filter(BookmarkCategory.parent_id == parent_id)
            if is_public is not None:
                query = query.filter(BookmarkCategory.is_public == is_public)

            return query.count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to count categories for user {user_id}: {str(e)}")

    def get_by_share_token(self, share_token: UUID) -> Optional[BookmarkCategory]:
        """Get category by share token for public access.

        Args:
            share_token: Share token

        Returns:
            BookmarkCategory or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(BookmarkCategory)
                .filter(
                    BookmarkCategory.share_token == share_token,
                    BookmarkCategory.is_public == True
                )
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get category by share token: {str(e)}")
