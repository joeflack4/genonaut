"""User service for business logic operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from genonaut.db.schema import User, UserInteraction, ContentItem
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class UserService:
    """Service class for user business logic."""
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def get_user(self, user_id: int) -> User:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance
            
        Raises:
            EntityNotFoundError: If user not found
        """
        return self.repository.get_or_404(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None if not found
        """
        return self.repository.get_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User instance or None if not found
        """
        return self.repository.get_by_email(email)
    
    def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False
    ) -> List[User]:
        """Get list of users.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, return only active users
            
        Returns:
            List of users
        """
        if active_only:
            return self.repository.get_active_users(skip=skip, limit=limit)
        else:
            return self.repository.get_multi(skip=skip, limit=limit)
    
    def create_user(
        self, 
        username_or_data = None, 
        email: str = None, 
        preferences: Dict[str, Any] = None,
        *,
        username: str = None
    ) -> User:
        """Create a new user.
        
        Args:
            username_or_data: Either username string OR complete user data dict
            email: User email address (if username_or_data is username)
            preferences: Optional user preferences (if username_or_data is username)
            username: Username (keyword-only for API calls)
            
        Returns:
            Created user
            
        Raises:
            ValidationError: If username or email already exists
        """
        # Handle different calling patterns
        if isinstance(username_or_data, dict):
            # Dictionary case (from tests)
            user_data = username_or_data
            final_username = user_data.get('username')
            final_email = user_data.get('email')
            final_preferences = user_data.get('preferences') or {}
        elif username is not None:
            # Keyword arguments case (from API routes)
            final_username = username
            final_email = email
            final_preferences = preferences or {}
        else:
            # Individual parameters case (from API - old style)
            final_username = username_or_data
            final_email = email
            final_preferences = preferences or {}

        if not final_username or not final_email:
            raise ValidationError("Both username and email are required to create a user")

        # Validate username uniqueness
        if self.repository.username_exists(final_username):
            raise ValidationError("Username already exists")

        # Validate email uniqueness
        if self.repository.email_exists(final_email):
            raise ValidationError("Email already exists")
        
        # Validate email format (basic validation)
        if '@' not in final_email or '.' not in final_email.split('@')[-1]:
            raise ValidationError("Invalid email format")
        
        # Validate username format (basic validation)
        if len(final_username) < 3 or len(final_username) > 50:
            raise ValidationError("Username must be between 3 and 50 characters")
        
        payload = {
            'username': final_username,
            'email': final_email,
            'preferences': final_preferences,
            'is_active': True,
        }

        return self.repository.create(payload)
    
    def update_user(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """Update user information.
        
        Args:
            user_id: User ID
            username: New username (optional)
            email: New email (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated user
            
        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If username or email already exists
        """
        # Check if user exists
        user = self.repository.get_or_404(user_id)
        
        update_data = {}
        
        # Validate and set username if provided
        if username is not None:
            if username != user.username and self.repository.username_exists(username):
                raise ValidationError(f"Username '{username}' already exists")
            if len(username) < 3 or len(username) > 50:
                raise ValidationError("Username must be between 3 and 50 characters")
            update_data['username'] = username
        
        # Validate and set email if provided
        if email is not None:
            if email != user.email and self.repository.email_exists(email):
                raise ValidationError(f"Email '{email}' already exists")
            if '@' not in email or '.' not in email.split('@')[-1]:
                raise ValidationError("Invalid email format")
            update_data['email'] = email
        
        # Set active status if provided
        if is_active is not None:
            update_data['is_active'] = is_active
        
        return self.repository.update(user_id, update_data)
    
    def update_user_preferences(
        self, 
        user_id: int, 
        preferences: Dict[str, Any]
    ) -> User:
        """Update user preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences to merge with existing ones
            
        Returns:
            Updated user
            
        Raises:
            EntityNotFoundError: If user not found
        """
        return self.repository.update_preferences(user_id, preferences)

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Calculate aggregate statistics for a user's activity."""

        self.repository.get_or_404(user_id)
        session = self.repository.db

        total_interactions = (
            session.query(func.count())
            .select_from(UserInteraction)
            .filter(UserInteraction.user_id == user_id)
            .scalar()
        ) or 0

        content_created = (
            session.query(func.count())
            .select_from(ContentItem)
            .filter(ContentItem.creator_id == user_id)
            .scalar()
        ) or 0

        avg_rating = (
            session.query(func.avg(UserInteraction.rating))
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.rating.isnot(None),
            )
            .scalar()
        )

        return {
            "total_interactions": total_interactions,
            "content_created": content_created,
            "avg_rating_given": float(avg_rating) if avg_rating is not None else 0.0,
        }
    
    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user
            
        Raises:
            EntityNotFoundError: If user not found
        """
        return self.repository.update(user_id, {'is_active': False})
    
    def activate_user(self, user_id: int) -> User:
        """Activate a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user
            
        Raises:
            EntityNotFoundError: If user not found
        """
        return self.repository.update(user_id, {'is_active': True})
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            EntityNotFoundError: If user not found
        """
        return self.repository.delete(user_id)
    
    def search_users_by_preferences(
        self, 
        preferences_filter: Dict[str, Any]
    ) -> List[User]:
        """Search users by preferences.
        
        Args:
            preferences_filter: Dictionary of preference filters
            
        Returns:
            List of matching users
        """
        return self.repository.search_by_preferences(preferences_filter)
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        total_users = self.repository.count()
        active_users = self.repository.count({'is_active': True})
        inactive_users = total_users - active_users
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users
        }
