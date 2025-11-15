"""Bookmark category membership service for business logic."""

from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from datetime import datetime
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
        member = self.member_repo.add_bookmark_to_category(
            bookmark_id=bookmark_id,
            category_id=category_id,
            user_id=bookmark.user_id,
            position=position
        )

        # Update category's updated_at timestamp
        category.updated_at = datetime.utcnow()
        self.db.commit()

        return member

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
        category = self.category_repo.get_or_404(category_id)

        # Remove membership
        removed = self.member_repo.remove_bookmark_from_category(bookmark_id, category_id)

        # Update category's updated_at timestamp if removal was successful
        if removed:
            category.updated_at = datetime.utcnow()
            self.db.commit()

        return removed

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

    def sync_bookmark_categories(
        self,
        bookmark_id: UUID,
        category_ids: List[UUID],
        user_id: UUID
    ) -> List[BookmarkCategoryMember]:
        """Synchronize bookmark category memberships in a single operation.

        This method compares the requested category IDs with existing memberships
        and performs adds/removes as needed. It also handles the special case where
        an empty list is provided, defaulting to the "Uncategorized" category.

        Args:
            bookmark_id: Bookmark ID to sync
            category_ids: List of category IDs the bookmark should belong to
            user_id: User ID (for validation and default category lookup)

        Returns:
            List of final category memberships after sync

        Raises:
            EntityNotFoundError: If bookmark or any category not found
            ValidationError: If bookmark or categories don't belong to user
        """
        # Verify bookmark exists and belongs to user
        bookmark = self.bookmark_repo.get_or_404(bookmark_id)
        if bookmark.user_id != user_id:
            raise ValidationError("Bookmark does not belong to the specified user")

        # Handle empty category list: default to "Uncategorized"
        if not category_ids:
            # Get or create "Uncategorized" category for this user
            uncategorized = self.category_repo.get_by_user_and_name(
                user_id=user_id,
                name="Uncategorized",
                parent_id=None
            )
            if not uncategorized:
                # Create Uncategorized category if it doesn't exist
                uncategorized = self.category_repo.create({
                    'user_id': user_id,
                    'name': 'Uncategorized',
                    'description': 'Default category for uncategorized bookmarks',
                    'is_public': False
                })
            category_ids = [uncategorized.id]

        # Verify all categories exist and belong to user
        categories = []
        for category_id in category_ids:
            category = self.category_repo.get_or_404(category_id)
            if category.user_id != user_id:
                raise ValidationError(f"Category {category_id} does not belong to the specified user")
            categories.append(category)

        # Get existing memberships
        existing_memberships = self.member_repo.get_by_bookmark(bookmark_id)
        existing_category_ids: Set[UUID] = {m.category_id for m in existing_memberships}
        new_category_ids: Set[UUID] = set(category_ids)

        # Determine what to add and remove
        to_add = new_category_ids - existing_category_ids
        to_remove = existing_category_ids - new_category_ids

        # Track affected categories for updated_at updates
        affected_category_ids: Set[UUID] = to_add | to_remove

        # Remove old memberships
        for category_id in to_remove:
            self.member_repo.remove_bookmark_from_category(bookmark_id, category_id)

        # Add new memberships
        for category_id in to_add:
            self.member_repo.add_bookmark_to_category(
                bookmark_id=bookmark_id,
                category_id=category_id,
                user_id=user_id,
                position=None
            )

        # Update updated_at for all affected categories
        for category_id in affected_category_ids:
            category = self.category_repo.get(category_id)
            if category:
                category.updated_at = datetime.utcnow()

        # Commit all changes
        self.db.commit()

        # Return final memberships
        return self.member_repo.get_by_bookmark(bookmark_id)

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
