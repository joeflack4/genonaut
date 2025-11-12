"""Bookmark service for business logic."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from genonaut.db.schema import Bookmark, BookmarkCategory, BookmarkCategoryMember
from genonaut.api.repositories.bookmark_repository import BookmarkRepository
from genonaut.api.repositories.bookmark_category_repository import BookmarkCategoryRepository
from genonaut.api.repositories.bookmark_category_member_repository import BookmarkCategoryMemberRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class BookmarkService:
    """Service class for bookmark business logic."""

    def __init__(self, db: Session):
        self.bookmark_repo = BookmarkRepository(db)
        self.category_repo = BookmarkCategoryRepository(db)
        self.member_repo = BookmarkCategoryMemberRepository(db)
        self.user_repo = UserRepository(db)
        self.content_repo = ContentRepository(db)
        self.db = db

    def get_bookmark(self, bookmark_id: UUID) -> Bookmark:
        """Get bookmark by ID.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            Bookmark instance

        Raises:
            EntityNotFoundError: If bookmark not found
        """
        return self.bookmark_repo.get_or_404(bookmark_id)

    def get_user_bookmarks(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        pinned: Optional[bool] = None,
        is_public: Optional[bool] = None,
        category_id: Optional[UUID] = None
    ) -> List[Bookmark]:
        """Get bookmarks for a user with optional filtering.

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
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)
        return self.bookmark_repo.get_by_user(
            user_id,
            skip=skip,
            limit=limit,
            pinned=pinned,
            is_public=is_public,
            category_id=category_id
        )

    def get_user_bookmarks_with_content(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        pinned: Optional[bool] = None,
        is_public: Optional[bool] = None,
        category_id: Optional[UUID] = None,
        sort_field: str = "user_rating_then_created",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get bookmarks with content data for a user with optional filtering.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            pinned: Optional filter by pinned status
            is_public: Optional filter by public status
            category_id: Optional filter by category ID
            sort_field: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            List of bookmark dictionaries with content and user_rating

        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)

        results = self.bookmark_repo.get_by_user_with_content(
            user_id,
            skip=skip,
            limit=limit,
            pinned=pinned,
            is_public=is_public,
            category_id=category_id,
            sort_field=sort_field,
            sort_order=sort_order
        )

        # Transform results into dictionary format
        bookmarks_with_content = []
        for bookmark, content, user_rating in results:
            bookmark_dict = {
                'bookmark': bookmark,
                'content': content,
                'user_rating': user_rating
            }
            bookmarks_with_content.append(bookmark_dict)

        return bookmarks_with_content

    def count_user_bookmarks(
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
        """
        return self.bookmark_repo.count_by_user(
            user_id,
            pinned=pinned,
            is_public=is_public,
            category_id=category_id
        )

    def create_bookmark(
        self,
        user_id: UUID,
        content_id: int,
        content_source_type: str,
        note: Optional[str] = None,
        pinned: bool = False,
        is_public: bool = False
    ) -> Bookmark:
        """Create a new bookmark.

        Args:
            user_id: User ID
            content_id: Content item ID to bookmark
            content_source_type: Content source type ('items' or 'auto')
            note: Optional note about the bookmark
            pinned: Whether the bookmark is pinned
            is_public: Whether the bookmark is public

        Returns:
            Created bookmark instance

        Raises:
            EntityNotFoundError: If user or content not found
            ValidationError: If bookmark already exists
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)

        # Verify content exists
        # Note: content_repo.get() expects just id, not composite key
        # We'll need to verify content exists differently
        # For now, we'll let the foreign key constraint handle this

        # Check if bookmark already exists (not soft-deleted)
        existing = self.bookmark_repo.get_by_user_and_content(
            user_id, content_id, content_source_type
        )
        if existing:
            raise ValidationError(f"Bookmark already exists for this content item")

        # Create bookmark
        bookmark_data = {
            'user_id': user_id,
            'content_id': content_id,
            'content_source_type': content_source_type,
            'note': note,
            'pinned': pinned,
            'is_public': is_public,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        return self.bookmark_repo.create(bookmark_data)

    def update_bookmark(
        self,
        bookmark_id: UUID,
        note: Optional[str] = None,
        pinned: Optional[bool] = None,
        is_public: Optional[bool] = None
    ) -> Bookmark:
        """Update a bookmark.

        Args:
            bookmark_id: Bookmark ID
            note: New note (if provided)
            pinned: New pinned status (if provided)
            is_public: New public status (if provided)

        Returns:
            Updated bookmark instance

        Raises:
            EntityNotFoundError: If bookmark not found
        """
        bookmark = self.bookmark_repo.get_or_404(bookmark_id)

        # Build update data (only include fields that were provided)
        update_data = {'updated_at': datetime.utcnow()}
        if note is not None:
            update_data['note'] = note
        if pinned is not None:
            update_data['pinned'] = pinned
        if is_public is not None:
            update_data['is_public'] = is_public

        return self.bookmark_repo.update(bookmark_id, update_data)

    def delete_bookmark(self, bookmark_id: UUID) -> bool:
        """Soft delete a bookmark.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            True if deleted successfully

        Raises:
            EntityNotFoundError: If bookmark not found
        """
        return self.bookmark_repo.soft_delete(bookmark_id)

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
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)
        return self.bookmark_repo.get_pinned_bookmarks(user_id, skip=skip, limit=limit)
