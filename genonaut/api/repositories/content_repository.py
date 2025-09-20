"""Content repository for database operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc

from genonaut.db.schema import ContentItem
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.exceptions import DatabaseError


class ContentRepository(BaseRepository[ContentItem, Dict[str, Any], Dict[str, Any]]):
    """Repository for ContentItem entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, ContentItem)
    
    def get_by_creator(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Get content items by creator.
        
        Args:
            creator_id: Creator user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(ContentItem)
                .filter(ContentItem.creator_id == creator_id)
                .order_by(desc(ContentItem.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get content by creator {creator_id}: {str(e)}")

    # Alias expected by DB tests
    def get_by_creator_id(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        return self.get_by_creator(creator_id, skip=skip, limit=limit)
    
    def get_by_content_type(self, content_type: str, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Get content items by type.
        
        Args:
            content_type: Content type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(ContentItem)
                .filter(ContentItem.content_type == content_type)
                .order_by(desc(ContentItem.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get content by type {content_type}: {str(e)}")
    
    def get_public_content(self, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Get public content items.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of public content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(ContentItem)
                .filter(ContentItem.is_public == True)
                .filter(ContentItem.is_private == False)
                .order_by(desc(ContentItem.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get public content: {str(e)}")
    
    def search_by_title(self, search_term: str, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Search content items by title.
        
        Args:
            search_term: Search term for title
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(ContentItem)
                .filter(ContentItem.title.ilike(f"%{search_term}%"))
                .order_by(desc(ContentItem.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search content by title: {str(e)}")
    
    def search_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[ContentItem]:
        """Search content items by metadata using JSONB queries.
        
        Args:
            metadata_filter: Dictionary of metadata filters
            
        Returns:
            List of matching content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(ContentItem)
            
            # Apply JSONB filters for PostgreSQL
            for key, value in metadata_filter.items():
                # Use JSONB containment operator @>
                filter_condition = ContentItem.item_metadata.op('@>')(f'{{"{key}": "{value}"}}')
                query = query.filter(filter_condition)
            
            return query.order_by(desc(ContentItem.created_at)).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search content by metadata: {str(e)}")
    
    def search_by_tags(self, tags: List[str]) -> List[ContentItem]:
        """Search content items by tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            List of matching content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.db.query(ContentItem)
            
            # Search for any of the provided tags using JSONB overlap operator
            for tag in tags:
                query = query.filter(ContentItem.tags.op('?')(tag))
            
            return query.order_by(desc(ContentItem.created_at)).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search content by tags: {str(e)}")
    
    def get_top_rated(self, limit: int = 10) -> List[ContentItem]:
        """Get top-rated content items.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of top-rated content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return (
                self.db.query(ContentItem)
                .filter(ContentItem.quality_score > 0)
                .order_by(desc(ContentItem.quality_score))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get top rated content: {str(e)}")
    
    def get_recent(self, days: int = 7, limit: int = 100) -> List[ContentItem]:
        """Get recent content items.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent content items
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            return (
                self.db.query(ContentItem)
                .filter(ContentItem.created_at >= cutoff_date)
                .order_by(desc(ContentItem.created_at))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get recent content: {str(e)}")
    
    def update_quality_score(self, content_id: int, quality_score: float) -> ContentItem:
        """Update content quality score.
        
        Args:
            content_id: Content item ID
            quality_score: New quality score
            
        Returns:
            Updated content item
            
        Raises:
            EntityNotFoundError: If content not found
            DatabaseError: If database operation fails
        """
        try:
            content = self.get_or_404(content_id)
            content.quality_score = quality_score
            content.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content)
            return content
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update quality score for content {content_id}: {str(e)}")
