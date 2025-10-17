"""Service layer for user search history business logic."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from genonaut.db.schema import UserSearchHistory
from genonaut.api.repositories.user_search_history_repository import UserSearchHistoryRepository
from genonaut.api.exceptions import ValidationError


class UserSearchHistoryService:
    """Service for managing user search history."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = UserSearchHistoryRepository(db)

    def add_search(self, user_id: UUID, search_query: str) -> UserSearchHistory:
        """Add a search query to user's history.

        Validates the search query and adds it to the database.
        Does not deduplicate - every search is recorded.

        Args:
            user_id: UUID of the user
            search_query: The search query string

        Returns:
            Created UserSearchHistory record

        Raises:
            ValidationError: If search_query is invalid
        """
        if not search_query or not search_query.strip():
            raise ValidationError("Search query cannot be empty")

        if len(search_query) > 500:
            raise ValidationError("Search query cannot exceed 500 characters")

        return self.repository.add_search(user_id, search_query.strip())

    def get_recent_searches(
        self,
        user_id: UUID,
        limit: int = 3
    ) -> List[UserSearchHistory]:
        """Get user's most recent search queries.

        Args:
            user_id: UUID of the user
            limit: Maximum number of recent searches to return (default 3)

        Returns:
            List of UserSearchHistory records, most recent first

        Raises:
            ValidationError: If limit is invalid
        """
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")

        return self.repository.get_recent_searches(user_id, limit)

    def get_search_history_paginated(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Get user's search history with pagination.

        Args:
            user_id: UUID of the user
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with items and pagination metadata

        Raises:
            ValidationError: If pagination parameters are invalid
        """
        if page < 1:
            raise ValidationError("Page must be >= 1")

        if page_size < 1 or page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")

        items, total_count = self.repository.get_search_history_paginated(
            user_id, page, page_size
        )

        total_pages = (total_count + page_size - 1) // page_size if page_size else 0

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

    def delete_search(self, user_id: UUID, search_query: str) -> bool:
        """Delete all instances of a specific search query from user's history.

        Args:
            user_id: UUID of the user (for authorization check)
            search_query: The search query text to delete

        Returns:
            True if at least one entry deleted, False if not found or unauthorized
        """
        return self.repository.delete_search(user_id, search_query)

    def clear_all_history(self, user_id: UUID) -> int:
        """Clear all search history for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Number of entries deleted
        """
        return self.repository.clear_all_history(user_id)
