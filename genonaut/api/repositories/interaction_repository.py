"""User interaction repository for database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta

from genonaut.db.schema import UserInteraction
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class InteractionRepository(BaseRepository[UserInteraction, Dict[str, Any], Dict[str, Any]]):
    """Repository for UserInteraction entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, UserInteraction)
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[UserInteraction]:
        """Get interactions by user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of user interactions
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(UserInteraction)
                .filter(UserInteraction.user_id == user_id)
                .order_by(desc(UserInteraction.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get interactions by user {user_id}: {str(e)}")

    # Aliases expected by legacy tests
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[UserInteraction]:
        return self.get_by_user(user_id, skip=skip, limit=limit)
    
    def get_by_content(self, content_item_id: int, skip: int = 0, limit: int = 100) -> List[UserInteraction]:
        """Get interactions by content item.
        
        Args:
            content_item_id: Content item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of interactions for the content item
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(UserInteraction)
                .filter(UserInteraction.content_item_id == content_item_id)
                .order_by(desc(UserInteraction.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get interactions by content {content_item_id}: {str(e)}")

    def get_by_content_id(self, content_item_id: int, skip: int = 0, limit: int = 100) -> List[UserInteraction]:
        return self.get_by_content(content_item_id, skip=skip, limit=limit)
    
    def get_by_interaction_type(
        self, 
        interaction_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserInteraction]:
        """Get interactions by type.
        
        Args:
            interaction_type: Type of interaction (view, like, share, etc.)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of interactions of the specified type
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(UserInteraction)
                .filter(UserInteraction.interaction_type == interaction_type)
                .order_by(desc(UserInteraction.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get interactions by type {interaction_type}: {str(e)}")
    
    def get_user_content_interaction(
        self, 
        user_id: int, 
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
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(UserInteraction)
                .filter(
                    UserInteraction.user_id == user_id,
                    UserInteraction.content_item_id == content_item_id,
                    UserInteraction.interaction_type == interaction_type
                )
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get user-content interaction: {str(e)}")
    
    def get_recent_interactions(
        self, 
        user_id: int, 
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
            DatabaseError: If database operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            return (
                self.db.query(UserInteraction)
                .filter(
                    UserInteraction.user_id == user_id,
                    UserInteraction.created_at >= cutoff_date
                )
                .order_by(desc(UserInteraction.created_at))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recent interactions for user {user_id}: {str(e)}")
    
    def get_interaction_stats_by_content(self, content_item_id: int) -> Dict[str, Any]:
        """Get interaction statistics for a content item.
        
        Args:
            content_item_id: Content item ID
            
        Returns:
            Dictionary with interaction statistics
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = (
                self.db.query(
                    UserInteraction.interaction_type,
                    func.count(UserInteraction.id).label('count'),
                    func.avg(UserInteraction.rating).label('avg_rating'),
                    func.avg(UserInteraction.duration).label('avg_duration')
                )
                .filter(UserInteraction.content_item_id == content_item_id)
                .group_by(UserInteraction.interaction_type)
                .all()
            )
            
            stats = {}
            for row in result:
                stats[row.interaction_type] = {
                    'count': row.count,
                    'avg_rating': float(row.avg_rating) if row.avg_rating else None,
                    'avg_duration': float(row.avg_duration) if row.avg_duration else None
                }
            
            return stats
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get interaction stats for content {content_item_id}: {str(e)}")
    
    def get_user_interaction_summary(self, user_id: int) -> Dict[str, Any]:
        """Get interaction summary for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user interaction summary
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = (
                self.db.query(
                    UserInteraction.interaction_type,
                    func.count(UserInteraction.id).label('count'),
                    func.avg(UserInteraction.rating).label('avg_rating')
                )
                .filter(UserInteraction.user_id == user_id)
                .group_by(UserInteraction.interaction_type)
                .all()
            )
            
            summary = {}
            for row in result:
                summary[row.interaction_type] = {
                    'count': row.count,
                    'avg_rating': float(row.avg_rating) if row.avg_rating else None
                }
            
            # Get total interactions
            total_interactions = (
                self.db.query(func.count(UserInteraction.id))
                .filter(UserInteraction.user_id == user_id)
                .scalar()
            )
            
            summary['total_interactions'] = total_interactions
            return summary
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get interaction summary for user {user_id}: {str(e)}")
    
    def record_interaction(
        self,
        user_id: int,
        content_item_id: int,
        interaction_type: str,
        rating: Optional[int] = None,
        duration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """Record a new user interaction.
        
        Args:
            user_id: User ID
            content_item_id: Content item ID
            interaction_type: Type of interaction
            rating: Optional rating (1-5)
            duration: Optional duration in seconds
            metadata: Optional additional metadata
            
        Returns:
            Created interaction
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            interaction_data = {
                'user_id': user_id,
                'content_item_id': content_item_id,
                'interaction_type': interaction_type,
                'rating': rating,
                'duration': duration,
                'interaction_metadata': metadata or {}
            }
            
            return self.create(interaction_data)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to record interaction: {str(e)}")
