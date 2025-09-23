"""Recommendation service for business logic operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from genonaut.db.schema import Recommendation, UserInteraction
from genonaut.api.repositories.recommendation_repository import RecommendationRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class RecommendationService:
    """Service class for recommendation business logic."""
    
    def __init__(self, db: Session):
        self.repository = RecommendationRepository(db)
        self.user_repository = UserRepository(db)
        self.content_repository = ContentRepository(db)
    
    def get_recommendation(self, recommendation_id: int) -> Recommendation:
        """Get recommendation by ID.
        
        Args:
            recommendation_id: Recommendation ID
            
        Returns:
            Recommendation instance
            
        Raises:
            EntityNotFoundError: If recommendation not found
        """
        return self.repository.get_or_404(recommendation_id)
    
    def get_user_recommendations(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        min_score: Optional[float] = None,
        unserved_only: bool = False
    ) -> List[Recommendation]:
        """Get recommendations for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            min_score: Minimum recommendation score
            unserved_only: If True, return only unserved recommendations
            
        Returns:
            List of recommendations for the user
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists and is active
        user = self.user_repository.get_or_404(user_id)
        if not user.is_active:
            raise ValidationError("Cannot get recommendations for inactive users")
        
        if unserved_only:
            return self.repository.get_unserved_recommendations(user_id, limit=limit)
        elif min_score is not None:
            return self.repository.get_top_recommendations(user_id, min_score=min_score, limit=limit)
        else:
            return self.repository.get_by_user(user_id, skip=skip, limit=limit)
    
    def get_content_recommendations(
        self, 
        content_item_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Recommendation]:
        """Get recommendations for a content item.
        
        Args:
            content_item_id: Content item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recommendations for the content item
            
        Raises:
            EntityNotFoundError: If content not found
        """
        # Verify content exists
        self.content_repository.get_or_404(content_item_id)
        return self.repository.get_by_content(content_item_id, skip=skip, limit=limit)

    def generate_recommendations(
        self,
        user_id: UUID,
        algorithm_version: str,
        limit: int = 10,
    ) -> List[Recommendation]:
        """Generate recommendations for a user.

        Currently returns existing unserved recommendations or falls back to the
        general user recommendation listing. Acts as a placeholder for a future
        generation pipeline while keeping the API functional for integration tests.
        """

        recommendations = self.get_user_recommendations(
            user_id=user_id,
            limit=limit,
            unserved_only=True,
        )

        if recommendations:
            return recommendations[:limit]

        return self.get_user_recommendations(
            user_id=user_id,
            limit=limit,
        )
    
    def create_recommendation(
        self,
        user_id_or_data = None,
        content_item_id: int = None,
        recommendation_score: float = None,
        algorithm_version: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        user_id: UUID = None
    ) -> Recommendation:
        """Create a new recommendation.
        
        Args:
            user_id_or_data: Either user_id UUID OR complete recommendation data dict
            content_item_id: Content item ID (if user_id_or_data is user_id)
            recommendation_score: Recommendation score (if user_id_or_data is user_id)
            algorithm_version: Algorithm version used (if user_id_or_data is user_id)
            metadata: Optional additional metadata (if user_id_or_data is user_id)
            user_id: User ID (keyword-only for API calls)
            
        Returns:
            Created recommendation
            
        Raises:
            ValidationError: If validation fails
            EntityNotFoundError: If user or content not found
        """
        # Handle different calling patterns
        if isinstance(user_id_or_data, dict):
            # Dictionary case (from tests)
            recommendation_data = user_id_or_data
            final_user_id = recommendation_data.get('user_id')
            final_content_item_id = recommendation_data.get('content_item_id')
            final_recommendation_score = recommendation_data.get('recommendation_score')
            final_algorithm_version = recommendation_data.get('algorithm_version')
            final_metadata = recommendation_data.get('metadata')
        elif user_id is not None:
            # Keyword arguments case (from API routes)
            final_user_id = user_id
            final_content_item_id = content_item_id
            final_recommendation_score = recommendation_score
            final_algorithm_version = algorithm_version
            final_metadata = metadata
        else:
            # Individual parameters case (from API - old style)
            final_user_id = user_id_or_data
            final_content_item_id = content_item_id
            final_recommendation_score = recommendation_score
            final_algorithm_version = algorithm_version
            final_metadata = metadata
        
        # Validate required fields
        if final_user_id is None or final_content_item_id is None or final_recommendation_score is None or final_algorithm_version is None:
            raise ValidationError("user_id, content_item_id, recommendation_score, and algorithm_version are required")
        
        # Validate user exists and is active
        user = self.user_repository.get_or_404(final_user_id)
        if not user.is_active:
            raise ValidationError("Cannot create recommendations for inactive users")
        
        # Validate content exists
        self.content_repository.get_or_404(final_content_item_id)
        
        # Validate recommendation score
        if not isinstance(final_recommendation_score, (int, float)) or final_recommendation_score < 0.0 or final_recommendation_score > 1.0:
            raise ValidationError("Recommendation score must be a number between 0.0 and 1.0")
        
        # Validate algorithm version
        if not final_algorithm_version or len(str(final_algorithm_version).strip()) == 0:
            raise ValidationError("Algorithm version cannot be empty")
        
        return self.repository.create_recommendation(
            user_id=final_user_id,
            content_item_id=final_content_item_id,
            recommendation_score=float(final_recommendation_score),
            algorithm_version=str(final_algorithm_version).strip(),
            metadata=final_metadata
        )
    
    def bulk_create_recommendations(
        self, 
        recommendations_data: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """Bulk create recommendations.
        
        Args:
            recommendations_data: List of recommendation data dictionaries
                Each dict should contain: user_id, content_item_id, recommendation_score, algorithm_version
                Optionally: rec_metadata
            
        Returns:
            List of created recommendations
            
        Raises:
            ValidationError: If validation fails for any recommendation
        """
        validated_data = []
        
        for i, data in enumerate(recommendations_data):
            try:
                # Validate required fields
                if 'user_id' not in data or 'content_item_id' not in data:
                    raise ValidationError(f"Recommendation {i}: user_id and content_item_id are required")
                if 'recommendation_score' not in data or 'algorithm_version' not in data:
                    raise ValidationError(f"Recommendation {i}: recommendation_score and algorithm_version are required")
                
                # Validate user exists (we'll do batch validation)
                user = self.user_repository.get(data['user_id'])
                if not user:
                    raise ValidationError(f"Recommendation {i}: User {data['user_id']} not found")
                if not user.is_active:
                    raise ValidationError(f"Recommendation {i}: User {data['user_id']} is inactive")
                
                # Validate content exists
                content = self.content_repository.get(data['content_item_id'])
                if not content:
                    raise ValidationError(f"Recommendation {i}: Content {data['content_item_id']} not found")
                
                # Validate recommendation score
                score = data['recommendation_score']
                if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
                    raise ValidationError(f"Recommendation {i}: Score must be between 0.0 and 1.0")
                
                # Validate algorithm version
                algorithm = data['algorithm_version']
                if not algorithm or len(str(algorithm).strip()) == 0:
                    raise ValidationError(f"Recommendation {i}: Algorithm version cannot be empty")
                
                validated_item = {
                    'user_id': data['user_id'],
                    'content_item_id': data['content_item_id'],
                    'recommendation_score': float(score),
                    'algorithm_version': str(algorithm).strip(),
                    'rec_metadata': data.get('rec_metadata', {}),
                    'is_served': False
                }
                validated_data.append(validated_item)
                
            except Exception as e:
                raise ValidationError(f"Validation failed for recommendation {i}: {str(e)}")
        
        return self.repository.bulk_create_recommendations(validated_data)
    
    def mark_recommendations_as_served(self, recommendation_ids: List[int]) -> int:
        """Mark recommendations as served.
        
        Args:
            recommendation_ids: List of recommendation IDs to mark as served
            
        Returns:
            Number of recommendations marked as served
            
        Raises:
            ValidationError: If recommendation IDs list is empty
        """
        if not recommendation_ids:
            raise ValidationError("Recommendation IDs list cannot be empty")
        
        # Validate that all recommendations exist
        for rec_id in recommendation_ids:
            self.repository.get_or_404(rec_id)
        
        return self.repository.mark_as_served(recommendation_ids)
    
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
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        return self.repository.get_recent_recommendations(user_id, days=days, limit=limit)
    
    def get_recommendations_by_algorithm(
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
        """
        return self.repository.get_by_algorithm(algorithm_version, skip=skip, limit=limit)
    
    def get_user_recommendation_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get recommendation statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with recommendation statistics
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        return self.repository.get_recommendation_stats(user_id)
    
    def update_recommendation(
        self,
        recommendation_id: int,
        recommendation_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Recommendation:
        """Update an existing recommendation.
        
        Args:
            recommendation_id: Recommendation ID
            recommendation_score: New recommendation score (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated recommendation
            
        Raises:
            EntityNotFoundError: If recommendation not found
            ValidationError: If validation fails
        """
        update_data = {}
        
        # Validate and set recommendation score if provided
        if recommendation_score is not None:
            if not isinstance(recommendation_score, (int, float)) or recommendation_score < 0.0 or recommendation_score > 1.0:
                raise ValidationError("Recommendation score must be a number between 0.0 and 1.0")
            update_data['recommendation_score'] = float(recommendation_score)
        
        # Set metadata if provided
        if metadata is not None:
            update_data['rec_metadata'] = metadata
        
        return self.repository.update(recommendation_id, update_data)
    
    def delete_recommendation(self, recommendation_id: int) -> bool:
        """Delete a recommendation.
        
        Args:
            recommendation_id: Recommendation ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            EntityNotFoundError: If recommendation not found
        """
        return self.repository.delete(recommendation_id)
    
    def generate_recommendations_for_user(
        self,
        user_id: UUID,
        algorithm_version: str,
        limit: int = 10
    ) -> List[Recommendation]:
        """Generate recommendations for a specific user.
        
        Args:
            user_id: User ID
            algorithm_version: Algorithm version to use
            limit: Maximum number of recommendations to generate
            
        Returns:
            List of generated recommendations
            
        Raises:
            EntityNotFoundError: If user not found
            ValidationError: If validation fails
        """
        # Verify user exists and is active
        user = self.user_repository.get_or_404(user_id)
        if not user.is_active:
            raise ValidationError("Cannot generate recommendations for inactive users")
        
        # Get available content items (excluding private content for now)
        available_content = self.content_repository.get_public_content(limit=100)
        
        recommendations = []
        for content in available_content[:limit]:
            # Calculate recommendation score using similarity calculation
            score = self._calculate_content_similarity(user, content)
            
            # Create recommendation
            recommendation = self.create_recommendation({
                'user_id': user_id,
                'content_item_id': content.id,
                'recommendation_score': score,
                'algorithm_version': algorithm_version,
                'metadata': {'generated_by': 'generate_recommendations_for_user'}
            })
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_content_similarity(self, user, content_item) -> float:
        """Calculate similarity score between user and content.
        
        This is a placeholder implementation for the recommendation algorithm.
        In a real system, this would use ML models, collaborative filtering, etc.
        
        Args:
            user: User object
            content_item: ContentItem object
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Placeholder algorithm - in practice this would be much more sophisticated
        # For now, return a reasonable score based on simple heuristics
        
        base_score = 0.5  # Default baseline score
        
        # Boost score if user has interacted with similar content types
        user_interactions = self.repository.db.query(UserInteraction).filter(
            UserInteraction.user_id == user.id
        ).all()
        
        similar_content_interactions = [
            interaction for interaction in user_interactions
            if interaction.content_item and interaction.content_item.content_type == content_item.content_type
        ]
        
        if similar_content_interactions:
            base_score += 0.2  # Boost for familiar content type
        
        # Add some randomization to avoid always returning the same scores
        import random
        random_factor = random.uniform(-0.1, 0.3)
        
        final_score = min(1.0, max(0.0, base_score + random_factor))
        return round(final_score, 2)

    def get_served_recommendations(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Recommendation]:
        """Get served recommendations for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of served recommendations for the user
            
        Raises:
            EntityNotFoundError: If user not found
        """
        # Verify user exists
        self.user_repository.get_or_404(user_id)
        
        # Get served recommendations (either is_served=True OR served_at is not null)
        session = self.repository.db
        query = session.query(Recommendation).filter(
            Recommendation.user_id == user_id
        ).filter(
            # A recommendation is considered served if either flag is set or served_at exists
            (Recommendation.is_served == True) | (Recommendation.served_at.isnot(None))
        ).order_by(Recommendation.served_at.desc().nullslast())
        
        return query.offset(skip).limit(limit).all()

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get overall recommendation statistics.
        
        Returns:
            Dictionary with recommendation statistics
        """
        total_recommendations = self.repository.count()
        served_recommendations = self.repository.count({'is_served': True})
        unserved_recommendations = total_recommendations - served_recommendations
        
        return {
            'total_recommendations': total_recommendations,
            'served_recommendations': served_recommendations,
            'unserved_recommendations': unserved_recommendations
        }
