"""Recommendation repository for database operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta

from genonaut.db.schema import Recommendation
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class RecommendationRepository(BaseRepository[Recommendation, Dict[str, Any], Dict[str, Any]]):
    """Repository for Recommendation entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Recommendation)
    
    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Recommendation]:
        """Get recommendations for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recommendations for the user
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .order_by(desc(Recommendation.recommendation_score))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recommendations for user {user_id}: {str(e)}")

    def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Recommendation]:
        return self.get_by_user(user_id, skip=skip, limit=limit)
    
    def get_by_content(self, content_item_id: int, skip: int = 0, limit: int = 100) -> List[Recommendation]:
        """Get recommendations for a content item.
        
        Args:
            content_item_id: Content item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recommendations for the content item
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Recommendation)
                .filter(Recommendation.content_item_id == content_item_id)
                .order_by(desc(Recommendation.recommendation_score))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recommendations for content {content_item_id}: {str(e)}")

    def get_by_content_id(self, content_item_id: int, skip: int = 0, limit: int = 100) -> List[Recommendation]:
        return self.get_by_content(content_item_id, skip=skip, limit=limit)
    
    def get_top_recommendations(
        self, 
        user_id: UUID, 
        min_score: float = 0.5, 
        limit: int = 10
    ) -> List[Recommendation]:
        """Get top recommendations for a user.
        
        Args:
            user_id: User ID
            min_score: Minimum recommendation score
            limit: Maximum number of records to return
            
        Returns:
            List of top recommendations
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Recommendation)
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.recommendation_score >= min_score
                )
                .order_by(desc(Recommendation.recommendation_score))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get top recommendations for user {user_id}: {str(e)}")
    
    def get_unserved_recommendations(
        self, 
        user_id: UUID, 
        limit: int = 20
    ) -> List[Recommendation]:
        """Get unserved recommendations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of unserved recommendations
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Recommendation)
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.is_served.is_(False),
                    Recommendation.served_at.is_(None),
                )
                .order_by(desc(Recommendation.recommendation_score))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get unserved recommendations for user {user_id}: {str(e)}")
    
    def get_by_algorithm(
        self, 
        algorithm_version: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Recommendation]:
        """Get recommendations by algorithm version.
        
        Args:
            algorithm_version: Algorithm version
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recommendations from the algorithm
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(Recommendation)
                .filter(Recommendation.algorithm_version == algorithm_version)
                .order_by(desc(Recommendation.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recommendations by algorithm {algorithm_version}: {str(e)}")
    
    def get_recent_recommendations(
        self, 
        user_id: UUID, 
        days: int = 7, 
        limit: int = 50
    ) -> List[Recommendation]:
        """Get recent recommendations for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent recommendations
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            return (
                self.db.query(Recommendation)
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.created_at >= cutoff_date
                )
                .order_by(desc(Recommendation.recommendation_score))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recent recommendations for user {user_id}: {str(e)}")
    
    def mark_as_served(self, recommendation_ids: List[int]) -> List[Recommendation]:
        """Mark recommendations as served.
        
        Args:
            recommendation_ids: List of recommendation IDs to mark as served
            
        Returns:
            Number of recommendations marked as served
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            if not recommendation_ids:
                return []

            recommendations = (
                self.db.query(Recommendation)
                .filter(Recommendation.id.in_(recommendation_ids))
                .all()
            )

            now = datetime.utcnow()
            for recommendation in recommendations:
                recommendation.is_served = True
                recommendation.served_at = now

            self.db.commit()
            return recommendations
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to mark recommendations as served: {str(e)}")
    
    def get_recommendation_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get recommendation statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with recommendation statistics
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Total recommendations
            total = (
                self.db.query(func.count(Recommendation.id))
                .filter(Recommendation.user_id == user_id)
                .scalar()
            )
            
            # Served recommendations
            served = (
                self.db.query(func.count(Recommendation.id))
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.is_served == True
                )
                .scalar()
            )
            
            # Average score
            avg_score = (
                self.db.query(func.avg(Recommendation.recommendation_score))
                .filter(Recommendation.user_id == user_id)
                .scalar()
            )
            
            # Algorithm breakdown
            algorithm_stats = (
                self.db.query(
                    Recommendation.algorithm_version,
                    func.count(Recommendation.id).label('count'),
                    func.avg(Recommendation.recommendation_score).label('avg_score')
                )
                .filter(Recommendation.user_id == user_id)
                .group_by(Recommendation.algorithm_version)
                .all()
            )
            
            algorithm_breakdown = {}
            for row in algorithm_stats:
                algorithm_breakdown[row.algorithm_version] = {
                    'count': row.count,
                    'avg_score': float(row.avg_score) if row.avg_score else 0.0
                }
            
            return {
                'total_recommendations': total or 0,
                'served_recommendations': served or 0,
                'unserved_recommendations': (total or 0) - (served or 0),
                'average_score': float(avg_score) if avg_score else 0.0,
                'algorithm_breakdown': algorithm_breakdown
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recommendation stats for user {user_id}: {str(e)}")
    
    def create_recommendation(
        self,
        user_id: UUID,
        content_item_id: int,
        recommendation_score: float,
        algorithm_version: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Recommendation:
        """Create a new recommendation.
        
        Args:
            user_id: User ID
            content_item_id: Content item ID
            recommendation_score: Recommendation score (0-1)
            algorithm_version: Algorithm version used
            metadata: Optional additional metadata
            
        Returns:
            Created recommendation
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            recommendation_data = {
                'user_id': user_id,
                'content_item_id': content_item_id,
                'recommendation_score': recommendation_score,
                'algorithm_version': algorithm_version,
                'rec_metadata': metadata or {}
            }
            
            return self.create(recommendation_data)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create recommendation: {str(e)}")
    
    def bulk_create_recommendations(
        self, 
        recommendations_data: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """Bulk create recommendations.
        
        Args:
            recommendations_data: List of recommendation data dictionaries
            
        Returns:
            List of created recommendations
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            recommendations = []
            for data in recommendations_data:
                recommendation = Recommendation(**data)
                recommendations.append(recommendation)
                self.db.add(recommendation)
            
            self.db.commit()
            
            # Refresh all objects
            for recommendation in recommendations:
                self.db.refresh(recommendation)
            
            return recommendations
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to bulk create recommendations: {str(e)}")
