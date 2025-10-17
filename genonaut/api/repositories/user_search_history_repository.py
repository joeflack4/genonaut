"""Repository for user search history operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import desc, func
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
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get user's search history with pagination, aggregated by unique query.

        Returns one row per unique search_query with count and most recent timestamp.

        Args:
            user_id: UUID of the user
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of aggregated search history dicts, total count of unique queries)
        """
        # Subquery to get count of unique search queries for pagination
        count_query = (
            self.db.query(UserSearchHistory.search_query)
            .filter(UserSearchHistory.user_id == user_id)
            .distinct()
        )
        total_count = count_query.count()

        # Main query: aggregate by search_query
        offset = (page - 1) * page_size
        aggregated_results = (
            self.db.query(
                UserSearchHistory.search_query,
                func.count(UserSearchHistory.id).label('search_count'),
                func.max(UserSearchHistory.created_at).label('last_searched_at')
            )
            .filter(UserSearchHistory.user_id == user_id)
            .group_by(UserSearchHistory.search_query)
            .order_by(desc(func.max(UserSearchHistory.created_at)))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # Convert to list of dicts
        items = [
            {
                'search_query': row.search_query,
                'search_count': row.search_count,
                'last_searched_at': row.last_searched_at,
                'user_id': user_id
            }
            for row in aggregated_results
        ]

        return items, total_count

    def delete_search(self, user_id: UUID, search_query: str) -> bool:
        """Delete all instances of a specific search query from user's history.

        Args:
            user_id: UUID of the user (for authorization check)
            search_query: The search query text to delete all instances of

        Returns:
            True if at least one entry was deleted, False if none found
        """
        deleted_count = (
            self.db.query(UserSearchHistory)
            .filter(
                UserSearchHistory.user_id == user_id,
                UserSearchHistory.search_query == search_query
            )
            .delete()
        )
        self.db.commit()
        return deleted_count > 0

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
