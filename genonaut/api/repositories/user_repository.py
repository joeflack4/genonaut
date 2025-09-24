"""User repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

from genonaut.db.schema import User
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.api.exceptions import DatabaseError


class UserRepository(BaseRepository[User, Dict[str, Any], Dict[str, Any]]):
    """Repository for User entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user by username {username}: {str(e)}")
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User instance or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user by email {email}: {str(e)}")
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active users
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(User)
                .filter(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get active users: {str(e)}")
    
    def search_by_preferences(self, preferences_filter: Dict[str, Any]) -> List[User]:
        """Search users by preferences using JSONB queries.
        
        Args:
            preferences_filter: Dictionary of preference filters
            
        Returns:
            List of matching users
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(User)
            
            # Apply JSONB filters for PostgreSQL
            for key, value in preferences_filter.items():
                # Use JSONB containment operator @>
                filter_condition = User.preferences.op('@>')(f'{{"{key}": "{value}"}}')
                query = query.filter(filter_condition)
            
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search users by preferences: {str(e)}")

    def get_by_preferences_filter(self, preferences_filter: Dict[str, Any]) -> List[User]:
        """Compatibility wrapper that performs preference filtering.

        Falls back to in-memory filtering when JSONB operators are unavailable (e.g. SQLite).
        """

        if not preferences_filter:
            return self.db.query(User).all()

        dialect = getattr(self.db.bind, "dialect", None)
        if dialect and dialect.name == "postgresql":
            return self.search_by_preferences(preferences_filter)

        users = self.db.query(User).all()

        def matches(user: User) -> bool:
            prefs = user.preferences or {}
            for key, value in preferences_filter.items():
                if prefs.get(key) != value:
                    return False
            return True

        return [user for user in users if matches(user)]

    def update_preferences(self, user_id: UUID, preferences: Dict[str, Any]) -> User:
        """Update user preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences dictionary
            
        Returns:
            Updated user instance
            
        Raises:
            EntityNotFoundError: If user not found
            DatabaseError: If database operation fails
        """
        try:
            user = self.get_or_404(user_id)
            
            # Merge with existing preferences
            if user.preferences:
                user.preferences.update(preferences)
            else:
                user.preferences = preferences

            flag_modified(user, "preferences")
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update preferences for user {user_id}: {str(e)}")

    def delete(self, user_id: UUID) -> User:
        """Soft delete a user by marking them inactive.

        Args:
            user_id: User ID

        Returns:
            Updated user instance with ``is_active`` set to ``False``.

        Raises:
            EntityNotFoundError: If user not found.
            DatabaseError: If database operation fails.
        """

        try:
            user = self.get_or_404(user_id)
            if not user.is_active:
                return user

            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
            return user
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseError(f"Failed to deactivate user {user_id}: {exc}")
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(User.id).filter(User.username == username).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check username existence: {str(e)}")
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.db.query(User.id).filter(User.email == email).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check email existence: {str(e)}")

    # ------------------------------------------------------------------
    # Paginated methods with enhanced performance
    # ------------------------------------------------------------------

    def get_active_users_paginated(self, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated active users with enhanced performance."""
        try:
            filters = {"is_active": True}
            # Use default created_at DESC sorting for better performance
            if not pagination.sort_field:
                pagination.sort_field = "created_at"
                pagination.sort_order = "desc"

            return self.get_paginated(pagination, filters=filters)
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get paginated active users: {exc}")

    def search_by_preferences_paginated(self, preferences_filter: Dict[str, Any],
                                       pagination: PaginationRequest) -> PaginatedResponse:
        """Search users by preferences with pagination."""
        try:
            from genonaut.api.models.responses import PaginationMeta
            from sqlalchemy import desc, asc

            query = self.db.query(User)

            # Apply JSONB filters for PostgreSQL
            dialect = getattr(self.db.bind, "dialect", None)
            if dialect and dialect.name == "postgresql":
                for key, value in preferences_filter.items():
                    filter_condition = User.preferences.op('@>')(f'{{"{key}": "{value}"}}')
                    query = query.filter(filter_condition)
            else:
                # For non-PostgreSQL, we'll need to get all and filter in memory
                # This is less efficient but works for smaller datasets
                all_users = query.all()
                filtered_users = []
                for user in all_users:
                    prefs = user.preferences or {}
                    if all(prefs.get(key) == value for key, value in preferences_filter.items()):
                        filtered_users.append(user)

                # Manual pagination for in-memory filtering
                total_count = len(filtered_users)
                start_idx = pagination.skip
                end_idx = start_idx + pagination.page_size
                items = filtered_users[start_idx:end_idx]

                has_next = end_idx < total_count
                has_previous = pagination.page > 1

                pagination_meta = PaginationMeta(
                    page=pagination.page,
                    page_size=pagination.page_size,
                    total_count=total_count,
                    has_next=has_next,
                    has_previous=has_previous
                )

                return PaginatedResponse(items=items, pagination=pagination_meta)

            # PostgreSQL path - use database-level pagination
            # Apply sorting
            if pagination.sort_field and hasattr(User, pagination.sort_field):
                sort_field = getattr(User, pagination.sort_field)
                if pagination.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(User.created_at))

            # Get total count and paginated results
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = (pagination.skip + pagination.page_size) < total_count
            has_previous = pagination.page > 1

            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total_count,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=items, pagination=pagination_meta)

        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to search users by preferences: {exc}")
