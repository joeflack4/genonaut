"""Content service for business logic operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from genonaut.db.schema import ContentItem, UserInteraction
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.exceptions import ValidationError, EntityNotFoundError


class ContentService:
    """Service class for content business logic."""
    
    def __init__(self, db: Session):
        self.repository = ContentRepository(db)
        self.user_repository = UserRepository(db)
    
    def get_content(self, content_id: int) -> ContentItem:
        """Get content item by ID.
        
        Args:
            content_id: Content item ID
            
        Returns:
            Content item instance
            
        Raises:
            EntityNotFoundError: If content not found
        """
        return self.repository.get_or_404(content_id)
    
    def get_content_list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        content_type: Optional[str] = None,
        creator_id: Optional[int] = None,
        public_only: bool = False
    ) -> List[ContentItem]:
        """Get list of content items with filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            content_type: Filter by content type
            creator_id: Filter by creator ID
            public_only: If True, return only public content
            
        Returns:
            List of content items
        """
        if public_only:
            return self.repository.get_public_content(skip=skip, limit=limit)
        elif content_type:
            return self.repository.get_by_content_type(content_type, skip=skip, limit=limit)
        elif creator_id:
            return self.repository.get_by_creator(creator_id, skip=skip, limit=limit)
        else:
            return self.repository.get_multi(skip=skip, limit=limit)
    
    def create_content(
        self, 
        content_data_dict: Dict[str, Any] = None,
        *,
        title: str = None,
        content_type: str = None,
        content_data: Any = None,
        creator_id: int = None,
        item_metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        is_public: bool = None,
        is_private: bool = None
    ) -> ContentItem:
        """Create a new content item.
        
        Args:
            content_data_dict: Complete content data dict (for test calls)
            title: Content title (for API calls)
            content_type: Type of content (text, image, video, audio)
            content_data: The actual content or reference to it
            creator_id: ID of the user creating the content
            item_metadata: Optional metadata
            tags: Optional list of tags
            is_public: Whether content is publicly visible
            is_private: Whether content is private
            
        Returns:
            Created content item
            
        Raises:
            ValidationError: If validation fails
            EntityNotFoundError: If creator not found
        """
        # Handle different calling patterns
        if content_data_dict is not None:
            # Dictionary case (from tests)
            final_title = content_data_dict.get('title')
            final_content_type = content_data_dict.get('content_type')
            final_content_payload = content_data_dict.get('content_data')
            final_creator_id = content_data_dict.get('creator_id')
            final_item_metadata = content_data_dict.get('item_metadata') or {}
            final_tags = content_data_dict.get('tags') or []
            final_is_public = content_data_dict.get('is_public', True)
            final_is_private = content_data_dict.get('is_private', False)
        else:
            # Keyword arguments case (from API routes)
            final_title = title
            final_content_type = content_type
            final_content_payload = content_data
            final_creator_id = creator_id
            final_item_metadata = item_metadata or {}
            final_tags = tags or []
            final_is_public = is_public if is_public is not None else True
            final_is_private = is_private if is_private is not None else False

        final_quality_score = 0.5  # Default quality score

        try:
            self.user_repository.get_or_404(final_creator_id)
        except EntityNotFoundError as exc:
            raise ValidationError("Creator not found") from exc

        # Validate content type
        valid_content_types = ['text', 'image', 'video', 'audio']
        if final_content_type not in valid_content_types:
            raise ValidationError(f"Invalid content type. Must be one of: {valid_content_types}")

        # Validate title
        if not final_title or len(final_title.strip()) == 0:
            raise ValidationError("Title cannot be empty")
        if len(final_title) > 255:
            raise ValidationError("Title cannot exceed 255 characters")

        # Validate content data
        if not final_content_payload or len(str(final_content_payload).strip()) == 0:
            raise ValidationError("Content data cannot be empty")

        # Validate privacy settings
        if final_is_public and final_is_private:
            raise ValidationError("Content cannot be both public and private")

        content_data_payload = {
            'title': final_title.strip(),
            'content_type': final_content_type,
            'content_data': final_content_payload,
            'creator_id': final_creator_id,
            'item_metadata': final_item_metadata,
            'tags': final_tags,
            'is_public': final_is_public,
            'is_private': final_is_private,
            'quality_score': final_quality_score
        }

        return self.repository.create(content_data_payload)
    
    def update_content(
        self,
        content_id: int,
        title: Optional[str] = None,
        content_data: Optional[str] = None,
        item_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        is_private: Optional[bool] = None
    ) -> ContentItem:
        """Update content item.
        
        Args:
            content_id: Content item ID
            title: New title (optional)
            content_data: New content data (optional)
            item_metadata: New metadata (optional)
            tags: New tags list (optional)
            is_public: New public status (optional)
            is_private: New private status (optional)
            
        Returns:
            Updated content item
            
        Raises:
            EntityNotFoundError: If content not found
            ValidationError: If validation fails
        """
        # Check if content exists
        content = self.repository.get_or_404(content_id)
        
        update_data = {}
        
        # Validate and set title if provided
        if title is not None:
            if not title or len(title.strip()) == 0:
                raise ValidationError("Title cannot be empty")
            if len(title) > 255:
                raise ValidationError("Title cannot exceed 255 characters")
            update_data['title'] = title.strip()
        
        # Validate and set content data if provided
        if content_data is not None:
            if not content_data or len(content_data.strip()) == 0:
                raise ValidationError("Content data cannot be empty")
            update_data['content_data'] = content_data
        
        # Set metadata if provided
        if item_metadata is not None:
            update_data['item_metadata'] = item_metadata
        
        # Set tags if provided
        if tags is not None:
            update_data['tags'] = tags
        
        # Validate and set privacy settings
        if is_public is not None:
            update_data['is_public'] = is_public
        if is_private is not None:
            update_data['is_private'] = is_private
        
        # Check privacy conflict
        final_is_public = update_data.get('is_public', content.is_public)
        final_is_private = update_data.get('is_private', content.is_private)
        if final_is_public and final_is_private:
            raise ValidationError("Content cannot be both public and private")
        
        return self.repository.update(content_id, update_data)
    
    def delete_content(self, content_id: int) -> bool:
        """Delete a content item.
        
        Args:
            content_id: Content item ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            EntityNotFoundError: If content not found
        """
        return self.repository.delete(content_id)
    
    def search_content(self, search_params: Dict[str, Any]) -> List[ContentItem]:
        """Search content items.
        
        Args:
            search_term: Search term for title
            metadata_filter: Dictionary of metadata filters
            tags: List of tags to search for
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching content items
        """
        search_term = search_params.get('search_term')
        metadata_filter = search_params.get('metadata_filter') or {}
        tags = search_params.get('tags') or []
        content_type = search_params.get('content_type')
        public_only = search_params.get('public_only', False)
        skip = search_params.get('skip', 0)
        limit = search_params.get('limit', 100)

        query = self.repository.db.query(ContentItem)

        if search_term:
            query = query.filter(ContentItem.title.ilike(f"%{search_term}%"))
        if content_type:
            query = query.filter(ContentItem.content_type == content_type)
        if public_only:
            query = query.filter(ContentItem.is_public.is_(True), ContentItem.is_private.is_(False))

        results = query.order_by(desc(ContentItem.created_at)).all()

        if tags:
            tag_set = set(tags)

            def has_tags(item: ContentItem) -> bool:
                item_tags = set(item.tags or [])
                return tag_set.issubset(item_tags)

            results = [item for item in results if has_tags(item)]

        if metadata_filter:
            def metadata_matches(item: ContentItem) -> bool:
                metadata = item.item_metadata or {}
                for key, value in metadata_filter.items():
                    if metadata.get(key) != value:
                        return False
                return True

            results = [item for item in results if metadata_matches(item)]

        return results[skip:skip + limit]

    def get_top_rated_content(self, limit: int = 10) -> List[ContentItem]:
        """Get top-rated content items.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of top-rated content items
        """
        return self.repository.get_top_rated(limit=limit)
    
    def get_recent_content(self, days: int = 7, limit: int = 100) -> List[ContentItem]:
        """Get recent content items.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent content items
        """
        return self.repository.get_recent(days=days, limit=limit)

    def update_content_quality(self, content_id: int, quality_score: float) -> ContentItem:
        """Update the quality score for a content item."""

        if quality_score < 0 or quality_score > 1:
            raise ValidationError("Quality score must be between 0 and 1")

        return self.repository.update_quality_score(content_id, quality_score)

    def get_content_analytics(self, content_id: int) -> Dict[str, Any]:
        """Return aggregated interaction metrics for a content item."""

        self.repository.get_or_404(content_id)
        session = self.repository.db

        total_views = (
            session.query(func.count())
            .select_from(UserInteraction)
            .filter(
                UserInteraction.content_item_id == content_id,
                UserInteraction.interaction_type == 'view',
            )
            .scalar()
        ) or 0

        total_likes = (
            session.query(func.count())
            .select_from(UserInteraction)
            .filter(
                UserInteraction.content_item_id == content_id,
                UserInteraction.interaction_type == 'like',
            )
            .scalar()
        ) or 0

        avg_rating = (
            session.query(func.avg(UserInteraction.rating))
            .filter(
                UserInteraction.content_item_id == content_id,
                UserInteraction.rating.isnot(None),
            )
            .scalar()
        )

        return {
            'total_views': total_views,
            'total_likes': total_likes,
            'avg_rating': float(avg_rating) if avg_rating is not None else 0.0,
        }
    
    def update_quality_score(self, content_id: int, quality_score: float) -> ContentItem:
        """Update content quality score.
        
        Args:
            content_id: Content item ID
            quality_score: New quality score (0.0 to 1.0)
            
        Returns:
            Updated content item
            
        Raises:
            EntityNotFoundError: If content not found
            ValidationError: If quality score is invalid
        """
        if quality_score < 0.0 or quality_score > 1.0:
            raise ValidationError("Quality score must be between 0.0 and 1.0")
        
        return self.repository.update_quality_score(content_id, quality_score)
    
    def get_content_stats(self) -> Dict[str, Any]:
        """Get content statistics.
        
        Returns:
            Dictionary with content statistics
        """
        total_content = self.repository.count()
        public_content = self.repository.count({'is_public': True, 'is_private': False})
        private_content = self.repository.count({'is_private': True})
        
        # Count by content type
        content_types = ['text', 'image', 'video', 'audio']
        type_breakdown = {}
        for content_type in content_types:
            type_breakdown[content_type] = self.repository.count({'content_type': content_type})
        
        return {
            'total_content': total_content,
            'public_content': public_content,
            'private_content': private_content,
            'type_breakdown': type_breakdown
        }
