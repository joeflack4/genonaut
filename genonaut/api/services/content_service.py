"""Content service for business logic operations."""

from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from sqlalchemy import desc, func, text, literal
from sqlalchemy.orm import Session

from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.db.schema import ContentItem, ContentItemAuto, UserInteraction

_VALID_CONTENT_TYPES = {"text", "image", "video", "audio"}


class ContentService:
    """Service class for content business logic."""

    def __init__(self, db: Session, *, model: Type[ContentItem] = ContentItem):
        self.model: Type[ContentItem] = model
        self.repository = ContentRepository(db, model=model)
        self.user_repository = UserRepository(db)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------
    def get_content(self, content_id: int) -> Any:
        """Return a single content record or raise ``EntityNotFoundError``."""

        return self.repository.get_or_404(content_id)

    def get_content_list(
        self,
        skip: int = 0,
        limit: int = 100,
        content_type: Optional[str] = None,
        creator_id: Optional[int] = None,
        public_only: bool = False,
    ) -> List[Any]:
        """Return paginated content subject to optional filters."""

        if public_only:
            return self.repository.get_public_content(skip=skip, limit=limit)
        if content_type:
            return self.repository.get_by_content_type(content_type, skip=skip, limit=limit)
        if creator_id:
            return self.repository.get_by_creator(creator_id, skip=skip, limit=limit)
        return self.repository.get_multi(skip=skip, limit=limit)

    def create_content(
        self,
        content_data_dict: Optional[Dict[str, Any]] = None,
        *,
        title: Optional[str] = None,
        content_type: Optional[str] = None,
        content_data: Optional[Any] = None,
        creator_id: Optional[int] = None,
        item_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_private: Optional[bool] = None,
    ) -> Any:
        """Create a new content record."""

        if content_data_dict is not None:
            final_title = content_data_dict.get("title")
            final_content_type = content_data_dict.get("content_type")
            final_content_payload = content_data_dict.get("content_data")
            final_creator_id = content_data_dict.get("creator_id")
            final_item_metadata = content_data_dict.get("item_metadata") or {}
            final_tags = content_data_dict.get("tags") or []
            final_is_private = content_data_dict.get("is_private", False)
        else:
            final_title = title
            final_content_type = content_type
            final_content_payload = content_data
            final_creator_id = creator_id
            final_item_metadata = item_metadata or {}
            final_tags = tags or []
            final_is_private = False if is_private is None else is_private

        if final_creator_id is None:
            raise ValidationError("Creator ID is required")

        try:
            self.user_repository.get_or_404(final_creator_id)
        except EntityNotFoundError as exc:
            raise ValidationError("Creator not found") from exc

        if final_content_type not in _VALID_CONTENT_TYPES:
            raise ValidationError(
                f"Invalid content type. Must be one of: {sorted(_VALID_CONTENT_TYPES)}"
            )

        if not final_title or not final_title.strip():
            raise ValidationError("Title cannot be empty")
        if len(final_title) > 255:
            raise ValidationError("Title cannot exceed 255 characters")

        if not final_content_payload or not str(final_content_payload).strip():
            raise ValidationError("Content data cannot be empty")

        payload = {
            "title": final_title.strip(),
            "content_type": final_content_type,
            "content_data": final_content_payload,
            "creator_id": final_creator_id,
            "item_metadata": final_item_metadata,
            "tags": final_tags,
            "is_private": final_is_private,
            "quality_score": 0.5,
        }

        return self.repository.create(payload)

    def update_content(
        self,
        content_id: int,
        title: Optional[str] = None,
        content_data: Optional[str] = None,
        item_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        is_private: Optional[bool] = None,
    ) -> Any:
        """Update a content record in place."""

        content = self.repository.get_or_404(content_id)
        update_data: Dict[str, Any] = {}

        if title is not None:
            if not title.strip():
                raise ValidationError("Title cannot be empty")
            if len(title) > 255:
                raise ValidationError("Title cannot exceed 255 characters")
            update_data["title"] = title.strip()

        if content_data is not None:
            if not content_data.strip():
                raise ValidationError("Content data cannot be empty")
            update_data["content_data"] = content_data

        if item_metadata is not None:
            update_data["item_metadata"] = item_metadata

        if tags is not None:
            update_data["tags"] = tags

        if is_private is not None:
            update_data["is_private"] = is_private

        return self.repository.update(content_id, update_data)

    def delete_content(self, content_id: int) -> bool:
        """Delete a content record."""

        return self.repository.delete(content_id)

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------
    def search_content(self, search_params: Dict[str, Any]) -> List[Any]:
        """Search by title, metadata, tags, or visibility settings."""

        search_term = search_params.get("search_term")
        metadata_filter = search_params.get("metadata_filter") or {}
        tags = search_params.get("tags") or []
        content_type = search_params.get("content_type")
        public_only = search_params.get("public_only", False)
        skip = search_params.get("skip", 0)
        limit = search_params.get("limit", 100)

        query = self.repository.db.query(self.model)

        if search_term:
            query = query.filter(self.model.title.ilike(f"%{search_term}%"))
        if content_type:
            query = query.filter(self.model.content_type == content_type)
        if public_only:
            query = query.filter(self.model.is_private.is_(False))

        results = query.order_by(desc(self.model.created_at)).all()

        if tags:
            tag_set = set(tags)

            def has_tags(item: Any) -> bool:
                item_tags = set(item.tags or [])
                return tag_set.issubset(item_tags)

            results = [item for item in results if has_tags(item)]

        if metadata_filter:
            def metadata_matches(item: Any) -> bool:
                metadata = item.item_metadata or {}
                return all(metadata.get(key) == value for key, value in metadata_filter.items())

            results = [item for item in results if metadata_matches(item)]

        return results[skip : skip + limit]

    def get_top_rated_content(self, limit: int = 10) -> List[Any]:
        """Return top-rated content records."""

        return self.repository.get_top_rated(limit=limit)

    def get_recent_content(self, days: int = 7, limit: int = 100) -> List[Any]:
        """Return content created within the given time window."""

        return self.repository.get_recent(days=days, limit=limit)

    # ------------------------------------------------------------------
    # Analytics and quality helpers
    # ------------------------------------------------------------------
    def update_content_quality(self, content_id: int, quality_score: float) -> Any:
        """Update the quality score for a content record."""

        if not 0 <= quality_score <= 1:
            raise ValidationError("Quality score must be between 0 and 1")
        return self.repository.update_quality_score(content_id, quality_score)

    def get_content_analytics(self, content_id: int) -> Dict[str, Any]:
        """Return aggregated interaction metrics for a content record."""

        self.repository.get_or_404(content_id)
        session = self.repository.db

        total_views = (
            session.query(func.count())
            .select_from(UserInteraction)
            .filter(
                UserInteraction.content_item_id == content_id,
                UserInteraction.interaction_type == "view",
            )
            .scalar()
        ) or 0

        total_likes = (
            session.query(func.count())
            .select_from(UserInteraction)
            .filter(
                UserInteraction.content_item_id == content_id,
                UserInteraction.interaction_type == "like",
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
            "total_views": total_views,
            "total_likes": total_likes,
            "avg_rating": float(avg_rating) if avg_rating is not None else 0.0,
        }

    def update_quality_score(self, content_id: int, quality_score: float) -> Any:
        """Alias retained for backwards compatibility with older callers."""

        return self.update_content_quality(content_id, quality_score)

    def get_content_stats(self) -> Dict[str, Any]:
        """Return basic statistics for the configured content model."""

        total_content = self.repository.count()
        private_content = self.repository.count({"is_private": True})

        type_breakdown = {
            content_type: self.repository.count({"content_type": content_type})
            for content_type in _VALID_CONTENT_TYPES
        }

        return {
            "total_content": total_content,
            "private_content": private_content,
            "type_breakdown": type_breakdown,
        }

    # ------------------------------------------------------------------
    # Paginated methods with enhanced performance
    # ------------------------------------------------------------------

    def get_content_list_paginated(self, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated content list with enhanced performance."""
        return self.repository.get_paginated(pagination)

    def get_content_by_creator_paginated(self, creator_id: UUID, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated content by creator with enhanced performance."""
        return self.repository.get_by_creator_paginated(creator_id, pagination)

    def get_content_by_type_paginated(self, content_type: str, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated content by type with enhanced performance."""
        return self.repository.get_by_content_type_paginated(content_type, pagination)

    def get_public_content_paginated(self, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated public content with enhanced performance."""
        return self.repository.get_public_content_paginated(pagination)

    def get_top_rated_content_paginated(self, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated top-rated content with enhanced performance."""
        return self.repository.get_top_rated_paginated(pagination)

    def get_recent_content_paginated(self, pagination: PaginationRequest, days: int = 7) -> PaginatedResponse:
        """Get paginated recent content with enhanced performance."""
        return self.repository.get_recent_paginated(pagination, days=days)

    def search_content_paginated(self, search_params: Dict[str, Any], pagination: PaginationRequest) -> PaginatedResponse:
        """Search content with pagination and enhanced performance."""
        search_term = search_params.get("search_term")
        metadata_filter = search_params.get("metadata_filter") or {}
        tags = search_params.get("tags") or []

        if search_term:
            return self.repository.search_by_title_paginated(search_term, pagination)
        elif metadata_filter:
            return self.repository.search_by_metadata_paginated(metadata_filter, pagination)
        elif tags:
            return self.repository.search_by_tags_paginated(tags, pagination)
        else:
            # Default to general paginated list
            filters = {}
            if search_params.get("content_type"):
                filters["content_type"] = search_params["content_type"]
            if search_params.get("creator_id"):
                filters["creator_id"] = search_params["creator_id"]
            if search_params.get("public_only"):
                filters["is_private"] = False

            return self.repository.get_paginated(pagination, filters=filters)

    # ------------------------------------------------------------------
    # Unified content methods
    # ------------------------------------------------------------------

    def get_unified_content_stats(self, user_id: Optional[UUID] = None) -> Dict[str, int]:
        """Get unified content statistics across both regular and auto tables."""
        session = self.repository.db

        # Count user's regular content
        user_regular_count = 0
        user_auto_count = 0
        if user_id:
            user_regular_count = session.query(func.count(ContentItem.id)).filter(
                ContentItem.creator_id == user_id
            ).scalar() or 0

            user_auto_count = session.query(func.count(ContentItemAuto.id)).filter(
                ContentItemAuto.creator_id == user_id
            ).scalar() or 0

        # Count total (community) content
        community_regular_count = session.query(func.count(ContentItem.id)).scalar() or 0
        community_auto_count = session.query(func.count(ContentItemAuto.id)).scalar() or 0

        return {
            "user_regular_count": user_regular_count,
            "user_auto_count": user_auto_count,
            "community_regular_count": community_regular_count,
            "community_auto_count": community_auto_count,
        }

    def get_unified_content_paginated(
        self,
        pagination: PaginationRequest,
        content_types: Optional[List[str]] = None,
        creator_filter: str = "all",
        user_id: Optional[UUID] = None,
        search_term: Optional[str] = None,
        sort_field: str = "created_at",
        sort_order: str = "desc",
        **filters
    ) -> Dict[str, Any]:
        """
        Get paginated content from both regular and auto tables.

        Args:
            pagination: Pagination parameters
            content_types: List of content types to include ("regular", "auto", or both)
            creator_filter: "all", "user", or "community"
            user_id: User ID for filtering
            search_term: Search term for title filtering
            sort_field: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            **filters: Additional filters
        """
        if content_types is None:
            content_types = ["regular", "auto"]

        session = self.repository.db

        # Build unified query using UNION
        queries = []

        # Regular content query
        if "regular" in content_types:
            regular_query = session.query(
                ContentItem.id.label('id'),
                ContentItem.title.label('title'),
                ContentItem.content_type.label('content_type'),
                ContentItem.content_data.label('content_data'),
                ContentItem.creator_id.label('creator_id'),
                ContentItem.item_metadata.label('item_metadata'),
                ContentItem.tags.label('tags'),
                ContentItem.is_private.label('is_private'),
                ContentItem.quality_score.label('quality_score'),
                ContentItem.created_at.label('created_at'),
                ContentItem.updated_at.label('updated_at'),
                literal('regular').label('source_type')
            )

            # Apply filters
            if creator_filter == "user" and user_id:
                regular_query = regular_query.filter(ContentItem.creator_id == user_id)
            elif creator_filter == "community" and user_id:
                regular_query = regular_query.filter(ContentItem.creator_id != user_id)

            if search_term:
                regular_query = regular_query.filter(ContentItem.title.ilike(f"%{search_term}%"))

            queries.append(regular_query)

        # Auto content query
        if "auto" in content_types:
            auto_query = session.query(
                ContentItemAuto.id.label('id'),
                ContentItemAuto.title.label('title'),
                ContentItemAuto.content_type.label('content_type'),
                ContentItemAuto.content_data.label('content_data'),
                ContentItemAuto.creator_id.label('creator_id'),
                ContentItemAuto.item_metadata.label('item_metadata'),
                ContentItemAuto.tags.label('tags'),
                ContentItemAuto.is_private.label('is_private'),
                ContentItemAuto.quality_score.label('quality_score'),
                ContentItemAuto.created_at.label('created_at'),
                ContentItemAuto.updated_at.label('updated_at'),
                literal('auto').label('source_type')
            )

            # Apply filters
            if creator_filter == "user" and user_id:
                auto_query = auto_query.filter(ContentItemAuto.creator_id == user_id)
            elif creator_filter == "community" and user_id:
                auto_query = auto_query.filter(ContentItemAuto.creator_id != user_id)

            if search_term:
                auto_query = auto_query.filter(ContentItemAuto.title.ilike(f"%{search_term}%"))

            queries.append(auto_query)

        if not queries:
            # Return empty result if no content types specified
            return {
                "items": [],
                "pagination": {
                    "page": pagination.page,
                    "page_size": pagination.page_size,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False,
                },
                "stats": self.get_unified_content_stats(user_id),
            }

        # Combine queries with UNION
        if len(queries) == 1:
            unified_query = queries[0]
        else:
            unified_query = queries[0].union_all(*queries[1:])

        # Add sorting - create a subquery first to be able to order by the labeled columns
        subquery = unified_query.subquery()

        if sort_field == "created_at":
            if sort_order.lower() == "desc":
                unified_query = session.query(subquery).order_by(desc(subquery.c.created_at))
            else:
                unified_query = session.query(subquery).order_by(subquery.c.created_at)
        elif sort_field == "quality_score":
            if sort_order.lower() == "desc":
                unified_query = session.query(subquery).order_by(desc(subquery.c.quality_score))
            else:
                unified_query = session.query(subquery).order_by(subquery.c.quality_score)
        else:
            # Default sort by created_at desc
            unified_query = session.query(subquery).order_by(desc(subquery.c.created_at))

        # Get total count for pagination - use a simpler approach
        try:
            # Count from the original union query (before sorting)
            original_union = queries[0] if len(queries) == 1 else queries[0].union_all(*queries[1:])
            count_subquery = original_union.subquery()
            total_count = session.query(func.count()).select_from(count_subquery).scalar() or 0
        except Exception:
            # Fallback: calculate count separately for each table
            total_count = 0
            if "regular" in content_types:
                regular_count_query = session.query(func.count(ContentItem.id))
                if creator_filter == "user" and user_id:
                    regular_count_query = regular_count_query.filter(ContentItem.creator_id == user_id)
                elif creator_filter == "community" and user_id:
                    regular_count_query = regular_count_query.filter(ContentItem.creator_id != user_id)
                if search_term:
                    regular_count_query = regular_count_query.filter(ContentItem.title.ilike(f"%{search_term}%"))
                total_count += regular_count_query.scalar() or 0

            if "auto" in content_types:
                auto_count_query = session.query(func.count(ContentItemAuto.id))
                if creator_filter == "user" and user_id:
                    auto_count_query = auto_count_query.filter(ContentItemAuto.creator_id == user_id)
                elif creator_filter == "community" and user_id:
                    auto_count_query = auto_count_query.filter(ContentItemAuto.creator_id != user_id)
                if search_term:
                    auto_count_query = auto_count_query.filter(ContentItemAuto.title.ilike(f"%{search_term}%"))
                total_count += auto_count_query.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        unified_query = unified_query.offset(offset).limit(pagination.page_size)

        # Execute query
        results = unified_query.all()

        # Convert results to dictionaries
        items = []
        for row in results:
            items.append({
                "id": row.id,
                "title": row.title,
                "content_type": row.content_type,
                "content_data": row.content_data,
                "creator_id": str(row.creator_id),
                "item_metadata": row.item_metadata,
                "tags": row.tags,
                "is_private": row.is_private,
                "quality_score": row.quality_score,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "source_type": row.source_type,
            })

        # Calculate pagination metadata
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1

        return {
            "items": items,
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            },
            "stats": self.get_unified_content_stats(user_id),
        }


class ContentAutoService(ContentService):
    """Service class specialised for ``ContentItemAuto`` records."""

    def __init__(self, db: Session):
        super().__init__(db, model=ContentItemAuto)
