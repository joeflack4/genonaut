"""Bookmark category service for business logic."""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from datetime import datetime

from genonaut.db.schema import BookmarkCategory, Bookmark
from genonaut.api.repositories.bookmark_category_repository import BookmarkCategoryRepository
from genonaut.api.repositories.bookmark_category_member_repository import BookmarkCategoryMemberRepository
from genonaut.api.repositories.bookmark_repository import BookmarkRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class BookmarkCategoryService:
    """Service class for bookmark category business logic."""

    def __init__(self, db: Session):
        self.category_repo = BookmarkCategoryRepository(db)
        self.member_repo = BookmarkCategoryMemberRepository(db)
        self.bookmark_repo = BookmarkRepository(db)
        self.user_repo = UserRepository(db)
        self.db = db

    def get_category(self, category_id: UUID) -> BookmarkCategory:
        """Get category by ID.

        Args:
            category_id: Category ID

        Returns:
            BookmarkCategory instance

        Raises:
            EntityNotFoundError: If category not found
        """
        return self.category_repo.get_or_404(category_id)

    def get_user_categories(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[UUID] = None,
        is_public: Optional[bool] = None,
        sort_by_index: bool = True
    ) -> List[BookmarkCategory]:
        """Get categories for a user with optional filtering.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            parent_id: Optional filter by parent category ID
            is_public: Optional filter by public status
            sort_by_index: If True, sort by sort_index; otherwise by created_at

        Returns:
            List of user categories

        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)
        return self.category_repo.get_by_user(
            user_id,
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            is_public=is_public,
            sort_by_index=sort_by_index
        )

    def count_user_categories(
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
        """
        return self.category_repo.count_by_user(
            user_id,
            parent_id=parent_id,
            is_public=is_public
        )

    def create_category(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        cover_content_id: Optional[int] = None,
        cover_content_source_type: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        sort_index: Optional[int] = None,
        is_public: bool = False
    ) -> BookmarkCategory:
        """Create a new category.

        Args:
            user_id: User ID
            name: Category name
            description: Optional category description
            color: Optional hex color code
            icon: Optional icon identifier
            cover_content_id: Optional cover content item ID
            cover_content_source_type: Optional cover content source type
            parent_id: Optional parent category ID
            sort_index: Optional sort index for ordering
            is_public: Whether the category is public

        Returns:
            Created category instance

        Raises:
            EntityNotFoundError: If user or parent category not found
            ValidationError: If category with same name exists or validation fails
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)

        # Verify parent category exists and belongs to same user if provided
        if parent_id is not None:
            parent = self.category_repo.get_or_404(parent_id)
            if parent.user_id != user_id:
                raise ValidationError("Parent category must belong to the same user")

        # Check if category with same name exists for this user and parent
        existing = self.category_repo.get_by_user_and_name(user_id, name, parent_id)
        if existing:
            raise ValidationError(f"Category '{name}' already exists at this level")

        # Create category
        category_data = {
            'user_id': user_id,
            'name': name,
            'description': description,
            'color': color,
            'icon': icon,
            'cover_content_id': cover_content_id,
            'cover_content_source_type': cover_content_source_type,
            'parent_id': parent_id,
            'sort_index': sort_index,
            'is_public': is_public,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # Generate share token if public
        if is_public:
            category_data['share_token'] = uuid4()

        return self.category_repo.create(category_data)

    def update_category(
        self,
        category_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        cover_content_id: Optional[int] = None,
        cover_content_source_type: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        sort_index: Optional[int] = None,
        is_public: Optional[bool] = None
    ) -> BookmarkCategory:
        """Update a category.

        Args:
            category_id: Category ID
            name: New name (if provided)
            description: New description (if provided)
            color: New color (if provided)
            icon: New icon (if provided)
            cover_content_id: New cover content ID (if provided)
            cover_content_source_type: New cover content source type (if provided)
            parent_id: New parent category ID (if provided)
            sort_index: New sort index (if provided)
            is_public: New public status (if provided)

        Returns:
            Updated category instance

        Raises:
            EntityNotFoundError: If category not found
            ValidationError: If validation fails
        """
        category = self.category_repo.get_or_404(category_id)

        # Build update data (only include fields that were provided)
        update_data = {'updated_at': datetime.utcnow()}

        if name is not None:
            # Check if new name conflicts with existing category at same level
            parent = parent_id if parent_id is not None else category.parent_id
            existing = self.category_repo.get_by_user_and_name(
                category.user_id, name, parent
            )
            if existing and existing.id != category_id:
                raise ValidationError(f"Category '{name}' already exists at this level")
            update_data['name'] = name

        if description is not None:
            update_data['description'] = description
        if color is not None:
            update_data['color'] = color
        if icon is not None:
            update_data['icon'] = icon
        if cover_content_id is not None:
            update_data['cover_content_id'] = cover_content_id
        if cover_content_source_type is not None:
            update_data['cover_content_source_type'] = cover_content_source_type
        if parent_id is not None:
            # Verify parent belongs to same user
            if parent_id != category.id:  # Prevent self-parenting
                parent = self.category_repo.get_or_404(parent_id)
                if parent.user_id != category.user_id:
                    raise ValidationError("Parent category must belong to the same user")
                update_data['parent_id'] = parent_id
            else:
                raise ValidationError("Category cannot be its own parent")
        if sort_index is not None:
            update_data['sort_index'] = sort_index
        if is_public is not None:
            update_data['is_public'] = is_public
            # Generate share token if becoming public and doesn't have one
            if is_public and category.share_token is None:
                update_data['share_token'] = uuid4()

        return self.category_repo.update(category_id, update_data)

    def delete_category(self, category_id: UUID) -> bool:
        """Delete a category.

        Note: Child categories and memberships will be handled by database cascade rules.
        Application should handle re-parenting children if desired before deleting.

        Args:
            category_id: Category ID

        Returns:
            True if deleted successfully

        Raises:
            EntityNotFoundError: If category not found
        """
        return self.category_repo.delete(category_id)

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
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)
        return self.category_repo.get_root_categories(user_id, skip=skip, limit=limit)

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
            EntityNotFoundError: If category not found
        """
        # Verify category exists
        self.category_repo.get_or_404(category_id)
        return self.category_repo.get_child_categories(category_id, skip=skip, limit=limit)

    def get_category_tree(self, user_id: UUID) -> List[BookmarkCategory]:
        """Get all categories for a user (flat list for tree building).

        Args:
            user_id: User ID

        Returns:
            List of all categories (caller builds tree structure)

        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repo.get_or_404(user_id)
        return self.category_repo.get_category_tree(user_id)

    def get_by_share_token(self, share_token: UUID) -> BookmarkCategory:
        """Get category by share token for public access.

        Args:
            share_token: Share token

        Returns:
            BookmarkCategory instance

        Raises:
            EntityNotFoundError: If category not found
        """
        category = self.category_repo.get_by_share_token(share_token)
        if category is None:
            raise EntityNotFoundError("BookmarkCategory", share_token)
        return category
