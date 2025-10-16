"""Repository for user search history operations."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from genonaut.db.schema import UserSearchHistory
from genonaut.api.repositories.base import BaseRepository


class UserSearchHistoryRepository(BaseRepository):
    """Repository for user search history database operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, UserSearchHistory)

    def add_search(self, user_id: UUID, search_query: str) -> UserSearchHistory:
        """Add a search query to user's history.

        Creates a new history entry for every search, including duplicates.
        This allows tracking search frequency and patterns over time.

        Args:
            user_id: UUID of the user
            search_query: The search query string

        Returns:
            UserSearchHistory record (newly created)
        """
        history_entry = UserSearchHistory(
            user_id=user_id,
            search_query=search_query,
            created_at=datetime.utcnow()
        )
        self.db.add(history_entry)
        self.db.commit()
        self.db.refresh(history_entry)
        return history_entry

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
        """
        return (
            self.db.query(UserSearchHistory)
            .filter(UserSearchHistory.user_id == user_id)
            .order_by(desc(UserSearchHistory.created_at))
            .limit(limit)
            .all()
        )

    def get_search_history_paginated(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[UserSearchHistory], int]:
        """Get user's search history with pagination.

        Args:
            user_id: UUID of the user
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of UserSearchHistory records, total count)
        """
        query = self.db.query(UserSearchHistory).filter(
            UserSearchHistory.user_id == user_id
        )

        total_count = query.count()

        offset = (page - 1) * page_size
        items = (
            query
            .order_by(desc(UserSearchHistory.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total_count

    def delete_search(self, user_id: UUID, history_id: int) -> bool:
        """Delete a specific search history entry.

        Args:
            user_id: UUID of the user (for authorization check)
            history_id: ID of the history entry to delete

        Returns:
            True if deleted, False if not found or unauthorized
        """
        history_entry = (
            self.db.query(UserSearchHistory)
            .filter(
                UserSearchHistory.id == history_id,
                UserSearchHistory.user_id == user_id
            )
            .first()
        )

        if not history_entry:
            return False

        self.db.delete(history_entry)
        self.db.commit()
        return True

    def clear_all_history(self, user_id: UUID) -> int:
        """Clear all search history for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Number of entries deleted
        """
        count = (
            self.db.query(UserSearchHistory)
            .filter(UserSearchHistory.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return count
