from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from genonaut.db.schema import UserInteraction, ContentItem
from genonaut.api.repositories.interaction_repository import InteractionRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class InteractionService:
    """Service class for user interaction business logic."""
    
    def __init__(self, db: Session):
        self.repository = InteractionRepository(db)
        self.user_repository = UserRepository(db)
        self.content_repository = ContentRepository(db)
    
    def get_interaction(self, interaction_id: int) -> UserInteraction:
        """Get interaction by ID.
        
        Args:
            interaction_id: Interaction ID
            
        Returns:
            User interaction instance
            
        Raises:
            EntityNotFoundError: If interaction not found
        """
        return self.repository.get_or_404(interaction_id)
    
    def get_user_interactions(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserInteraction]:
        """Get interactions for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of user interactions
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        return self.repository.get_by_user(user_id, skip=skip, limit=limit)
    
    def get_content_interactions(
        self, 
        content_item_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserInteraction]:
        """Get interactions for a content item.
        
        Args:
            content_item_id: Content item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of interactions for the content item
            
        Raises:
            EntityNotFoundError: If content not found
        """
        # Verify content exists
        self.content_repository.get_or_404(content_item_id)
        return self.repository.get_by_content(content_item_id, skip=skip, limit=limit)
    
    def record_interaction(
        self,
        user_id_or_data = None,
        content_item_id: int = None,
        interaction_type: str = None,
        rating: Optional[int] = None,
        duration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        user_id: UUID = None
    ) -> UserInteraction:
        """Record a new user interaction.
        
        Args:
            user_id_or_data: Either user_id UUID OR complete interaction data dict
            content_item_id: Content item ID (if user_id_or_data is user_id)
            interaction_type: Type of interaction (if user_id_or_data is user_id)
            rating: Optional rating (if user_id_or_data is user_id)
            duration: Optional duration in seconds (if user_id_or_data is user_id)
            metadata: Optional additional metadata (if user_id_or_data is user_id)
            user_id: User ID (keyword-only for API calls)
            
        Returns:
            Created interaction
            
        Raises:
            ValidationError: If validation fails
            EntityNotFoundError: If user or content not found
        """
        # Handle different calling patterns
        if isinstance(user_id_or_data, dict):
            # Dictionary case (from tests)
            interaction_data = user_id_or_data
            final_user_id = interaction_data.get('user_id')
            final_content_item_id = interaction_data.get('content_item_id')
            final_interaction_type = interaction_data.get('interaction_type')
            final_rating = interaction_data.get('rating')
            final_duration = interaction_data.get('duration')
            final_metadata = interaction_data.get('metadata')
        elif user_id is not None:
            # Keyword arguments case (from API routes)
            final_user_id = user_id
            final_content_item_id = content_item_id
            final_interaction_type = interaction_type
            final_rating = rating
            final_duration = duration
            final_metadata = metadata
        else:
            # Individual parameters case (from API - old style)
            final_user_id = user_id_or_data
            final_content_item_id = content_item_id
            final_interaction_type = interaction_type
            final_rating = rating
            final_duration = duration
            final_metadata = metadata
        
        # Validate required fields
        if final_user_id is None or final_content_item_id is None or final_interaction_type is None:
            raise ValidationError("user_id, content_item_id, and interaction_type are required")
        
        # Validate user exists
        try:
            user = self.user_repository.get_or_404(final_user_id)
        except EntityNotFoundError:
            raise ValidationError("User not found")
        
        if not user.is_active:
            raise ValidationError("Cannot record interactions for inactive users")
        
        # Validate content exists
        try:
            self.content_repository.get_or_404(final_content_item_id)
        except EntityNotFoundError:
            raise ValidationError("Content not found")
        
        # Validate interaction type
        valid_interaction_types = ['view', 'like', 'share', 'download', 'bookmark', 'comment', 'rate']
        if final_interaction_type not in valid_interaction_types:
            raise ValidationError(f"Invalid interaction type. Must be one of: {valid_interaction_types}")
        
        # Validate rating if provided
        if final_rating is not None:
            if not isinstance(final_rating, int) or final_rating < 1 or final_rating > 5:
                raise ValidationError("Rating must be an integer between 1 and 5")
        
        # Validate duration if provided
        if final_duration is not None:
            if not isinstance(final_duration, int) or final_duration < 0:
                raise ValidationError("Duration must be a non-negative integer")
        
        return self.repository.record_interaction(
            user_id=final_user_id,
            content_item_id=final_content_item_id,
            interaction_type=final_interaction_type,
            rating=final_rating,
            duration=final_duration,
            metadata=final_metadata
        )
    
    def get_recent_user_interactions(
        self, 
        user_id: UUID, 
        days: int = 30, 
        limit: int = 100
    ) -> List[UserInteraction]:
        """Get recent interactions for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent interactions
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        return self.repository.get_recent_interactions(user_id, days=days, limit=limit)
    
    def get_interactions_by_type(
        self, 
        interaction_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserInteraction]:
        """Get interactions by type.
        
        Args:
            interaction_type: Type of interaction
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of interactions of the specified type
        """
        return self.repository.get_by_interaction_type(interaction_type, skip=skip, limit=limit)
    
    def get_user_content_interaction(
        self, 
        user_id: UUID, 
        content_item_id: int, 
        interaction_type: str
    ) -> Optional[UserInteraction]:
        """Get specific user-content interaction.
        
        Args:
            user_id: User ID
            content_item_id: Content item ID
            interaction_type: Type of interaction
            
        Returns:
            User interaction or None if not found
            
        Raises:
            EntityNotFoundError: If user or content not found
        """
        # Verify user and content exist
        self.user_repository.get_or_404(user_id)
        self.content_repository.get_or_404(content_item_id)
        
        return self.repository.get_user_content_interaction(user_id, content_item_id, interaction_type)
    
    def get_content_interaction_stats(self, content_item_id: int) -> Dict[str, Any]:
        """Get interaction statistics for a content item.
        
        Args:
            content_item_id: Content item ID
            
        Returns:
            Dictionary with interaction statistics
            
        Raises:
            EntityNotFoundError: If content not found
        """
        # Verify content exists
        self.content_repository.get_or_404(content_item_id)
        return self.repository.get_interaction_stats_by_content(content_item_id)
    
    def get_user_interaction_summary(self, user_id: UUID) -> Dict[str, Any]:
        """Get interaction summary for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user interaction summary
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        return self.repository.get_user_interaction_summary(user_id)
    
    def update_interaction(
        self,
        interaction_id: int,
        rating: Optional[int] = None,
        duration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """Update an existing interaction.
        
        Args:
            interaction_id: Interaction ID
            rating: New rating (optional)
            duration: New duration (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated interaction
            
        Raises:
            EntityNotFoundError: If interaction not found
            ValidationError: If validation fails
        """
        update_data = {}
        
        # Validate and set rating if provided
        if rating is not None:
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                raise ValidationError("Rating must be an integer between 1 and 5")
            update_data['rating'] = rating
        
        # Validate and set duration if provided
        if duration is not None:
            if not isinstance(duration, int) or duration < 0:
                raise ValidationError("Duration must be a non-negative integer")
            update_data['duration'] = duration
        
        # Set metadata if provided
        if metadata is not None:
            update_data['interaction_metadata'] = metadata
        
        return self.repository.update(interaction_id, update_data)
    
    def delete_interaction(self, interaction_id: int) -> bool:
        """Delete an interaction.
        
        Args:
            interaction_id: Interaction ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            EntityNotFoundError: If interaction not found
        """
        return self.repository.delete(interaction_id)
    
    def get_user_behavior_analytics(self, user_id: UUID) -> Dict[str, Any]:
        """Get behavior analytics for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user behavior analytics
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        
        # Get total interactions for user
        total_interactions = self.repository.count({'user_id': user_id})
        
        # Count by interaction type for this user
        interaction_types = ['view', 'like', 'share', 'download', 'bookmark', 'comment', 'rate']
        type_breakdown = {}
        for interaction_type in interaction_types:
            count = self.repository.count({'user_id': user_id, 'interaction_type': interaction_type})
            if count > 0:
                type_breakdown[interaction_type] = count
        
        # Get favorite content types by analyzing user's interactions
        session = self.repository.db
        content_type_query = (
            session.query(ContentItem.content_type, func.count(UserInteraction.id))
            .join(UserInteraction, ContentItem.id == UserInteraction.content_item_id)
            .filter(UserInteraction.user_id == user_id)
            .group_by(ContentItem.content_type)
            .order_by(func.count(UserInteraction.id).desc())
            .all()
        )
        
        favorite_content_types = {}
        for content_type, count in content_type_query:
            favorite_content_types[content_type] = count
        
        return {
            'total_interactions': total_interactions,
            'interaction_types': type_breakdown,
            'favorite_content_types': favorite_content_types
        }
    
    def get_interaction_stats(self) -> Dict[str, Any]:
        """Get overall interaction statistics.
        
        Returns:
            Dictionary with interaction statistics
        """
        total_interactions = self.repository.count()
        
        # Count by interaction type
        interaction_types = ['view', 'like', 'share', 'download', 'bookmark', 'comment', 'rate']
        type_breakdown = {}
        for interaction_type in interaction_types:
            type_breakdown[interaction_type] = self.repository.count({'interaction_type': interaction_type})
        
        return {
            'total_interactions': total_interactions,
            'type_breakdown': type_breakdown
        }