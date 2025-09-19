"""User repository for database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

from genonaut.db.schema import User
from genonaut.api.repositories.base import BaseRepository
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

    def update_preferences(self, user_id: int, preferences: Dict[str, Any]) -> User:
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

    def delete(self, user_id: int) -> User:
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
