"""Bookmark category membership service for business logic."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.db.schema import BookmarkCategoryMember, Bookmark, BookmarkCategory
from genonaut.api.repositories.bookmark_category_member_repository import BookmarkCategoryMemberRepository
from genonaut.api.repositories.bookmark_repository import BookmarkRepository
from genonaut.api.repositories.bookmark_category_repository import BookmarkCategoryRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class BookmarkCategoryMemberService:
    """Service class for bookmark category membership business logic."""

    def __init__(self, db: Session):
        self.member_repo = BookmarkCategoryMemberRepository(db)
        self.bookmark_repo = BookmarkRepository(db)
        self.category_repo = BookmarkCategoryRepository(db)
        self.db = db

    def add_bookmark_to_category(
        self,
        bookmark_id: UUID,
        category_id: UUID,
        position: Optional[int] = None
    ) -> BookmarkCategoryMember:
        """Add a bookmark to a category.

        Args:
            bookmark_id: Bookmark ID
            category_id: Category ID
            position: Optional position within the category

        Returns:
            Created BookmarkCategoryMember instance

        Raises:
            EntityNotFoundError: If bookmark or category not found
            ValidationError: If bookmark and category belong to different users or membership already exists
        """
        # Verify bookmark exists and get user_id
        bookmark = self.bookmark_repo.get_or_404(bookmark_id)

        # Verify category exists
        category = self.category_repo.get_or_404(category_id)

        # Verify bookmark and category belong to same user
        if bookmark.user_id != category.user_id:
            raise ValidationError("Bookmark and category must belong to the same user")

        # Check if membership already exists
        if self.member_repo.exists(bookmark_id, category_id):
            raise ValidationError("Bookmark is already in this category")

        # Create membership
        return self.member_repo.add_bookmark_to_category(
            bookmark_id=bookmark_id,
            category_id=category_id,
            user_id=bookmark.user_id,
            position=position
        )

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
            True if removed successfully, False if membership didn't exist

        Raises:
            EntityNotFoundError: If bookmark or category not found
        """
        # Verify bookmark exists
        self.bookmark_repo.get_or_404(bookmark_id)

        # Verify category exists
        self.category_repo.get_or_404(category_id)

        return self.member_repo.remove_bookmark_from_category(bookmark_id, category_id)

    def update_bookmark_position(
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
            Updated BookmarkCategoryMember instance

        Raises:
            EntityNotFoundError: If bookmark, category, or membership not found
        """
        # Verify bookmark exists
        self.bookmark_repo.get_or_404(bookmark_id)

        # Verify category exists
        self.category_repo.get_or_404(category_id)

        return self.member_repo.update_position(bookmark_id, category_id, position)

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
            EntityNotFoundError: If category not found
        """
        # Verify category exists
        self.category_repo.get_or_404(category_id)

        return self.member_repo.get_bookmarks_in_category(
            category_id,
            skip=skip,
            limit=limit
        )

    def get_bookmarks_in_category_with_content(
        self,
        category_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "user_rating_then_created",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get bookmarks in a category with content data and user ratings.

        Args:
            category_id: Category ID
            user_id: User ID (for getting user ratings)
            skip: Number of records to skip
            limit: Maximum number of records to return
            sort_field: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            List of bookmark dictionaries with content and user_rating

        Raises:
            EntityNotFoundError: If category not found
        """
        # Verify category exists
        self.category_repo.get_or_404(category_id)

        results = self.member_repo.get_bookmarks_in_category_with_content(
            category_id,
            user_id,
            skip=skip,
            limit=limit,
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

    def count_bookmarks_in_category(self, category_id: UUID) -> int:
        """Count bookmarks in a category.

        Args:
            category_id: Category ID

        Returns:
            Number of bookmarks in the category

        Raises:
            EntityNotFoundError: If category not found
        """
        # Verify category exists
        self.category_repo.get_or_404(category_id)

        return self.member_repo.count_by_category(category_id)

    def get_bookmark_categories(self, bookmark_id: UUID) -> List[BookmarkCategoryMember]:
        """Get all categories that a bookmark belongs to.

        Args:
            bookmark_id: Bookmark ID

        Returns:
            List of category memberships

        Raises:
            EntityNotFoundError: If bookmark not found
        """
        # Verify bookmark exists
        self.bookmark_repo.get_or_404(bookmark_id)

        return self.member_repo.get_by_bookmark(bookmark_id)
