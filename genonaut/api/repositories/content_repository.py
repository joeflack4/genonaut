"""Content repository for database operations."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from genonaut.api.exceptions import DatabaseError
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.db.schema import ContentItem


class ContentRepository(BaseRepository[ContentItem, Dict[str, Any], Dict[str, Any]]):
    """Repository for ``ContentItem``-style entity operations."""

    def __init__(self, db: Session, model: Type[ContentItem] = ContentItem):
        super().__init__(db, model)

    def get_by_creator(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Return content authored by the specified creator."""

        try:
            return (
                self.db.query(self.model)
                .filter(self.model.creator_id == creator_id)
                .order_by(desc(self.model.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:  # pragma: no cover - defensive
            raise DatabaseError(f"Failed to get content by creator {creator_id}: {exc}")

    def get_by_creator_id(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Alias for backwards compatibility with existing tests."""

        return self.get_by_creator(creator_id, skip=skip, limit=limit)

    def get_by_content_type(self, content_type: str, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Return content filtered by ``content_type``."""

        try:
            return (
                self.db.query(self.model)
                .filter(self.model.content_type == content_type)
                .order_by(desc(self.model.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to get content by type {content_type}: {exc}")

    def get_public_content(self, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Return only public (non-private) content records."""

        try:
            return (
                self.db.query(self.model)
                .filter(self.model.is_private.is_(False))
                .order_by(desc(self.model.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to get public content: {exc}")

    def search_by_title(self, search_term: str, skip: int = 0, limit: int = 100) -> List[ContentItem]:
        """Perform case-insensitive ``LIKE`` search on titles."""

        try:
            return (
                self.db.query(self.model)
                .filter(self.model.title.ilike(f"%{search_term}%"))
                .order_by(desc(self.model.created_at))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to search content by title: {exc}")

    def search_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[ContentItem]:
        """Filter by JSON metadata using PostgreSQL containment operators."""

        try:
            query = self.db.query(self.model)

            for key, value in metadata_filter.items():
                filter_condition = self.model.item_metadata.op('@>')(f'{{"{key}": "{value}"}}')
                query = query.filter(filter_condition)

            return query.order_by(desc(self.model.created_at)).all()
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to search content by metadata: {exc}")

    def search_by_tags(self, tags: List[str]) -> List[ContentItem]:
        """Return items whose tag array contains every tag in ``tags``."""

        try:
            query = self.db.query(self.model)
            for tag in tags:
                query = query.filter(self.model.tags.op('?')(tag))
            return query.order_by(desc(self.model.created_at)).all()
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to search content by tags: {exc}")

    def get_top_rated(self, limit: int = 10) -> List[ContentItem]:
        """Return the highest-rated content records."""

        try:
            return (
                self.db.query(self.model)
                .filter(self.model.quality_score > 0)
                .order_by(desc(self.model.quality_score))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to get top rated content: {exc}")

    def get_recent(self, days: int = 7, limit: int = 100) -> List[ContentItem]:
        """Return content created within the last ``days`` days."""

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return (
                self.db.query(self.model)
                .filter(self.model.created_at >= cutoff_date)
                .order_by(desc(self.model.created_at))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as exc:  # pragma: no cover
            raise DatabaseError(f"Failed to get recent content: {exc}")

    def update_quality_score(self, content_id: int, quality_score: float) -> ContentItem:
        """Update the stored quality score for a single content record."""

        try:
            content = self.get_or_404(content_id)
            content.quality_score = quality_score
            content.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(content)
            return content
        except SQLAlchemyError as exc:  # pragma: no cover
            self.db.rollback()
            raise DatabaseError(f"Failed to update quality score for content {content_id}: {exc}")

    # Paginated Methods with Enhanced Performance

    def get_by_creator_paginated(self, creator_id: UUID, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated content by creator with enhanced performance."""
        try:
            filters = {"creator_id": creator_id}
            # Use default created_at DESC sorting for better performance with composite index
            if not pagination.sort_field:
                pagination.sort_field = "created_at"
                pagination.sort_order = "desc"

            return self.get_paginated(pagination, filters=filters)
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get paginated content by creator {creator_id}: {exc}")

    def get_public_content_paginated(self, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated public content with enhanced performance."""
        try:
            filters = {"is_private": False}
            # Use default created_at DESC sorting for better performance
            if not pagination.sort_field:
                pagination.sort_field = "created_at"
                pagination.sort_order = "desc"

            return self.get_paginated(pagination, filters=filters)
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get paginated public content: {exc}")

    def get_by_content_type_paginated(self, content_type: str, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated content by type with enhanced performance."""
        try:
            filters = {"content_type": content_type}
            # Use default created_at DESC sorting for better performance
            if not pagination.sort_field:
                pagination.sort_field = "created_at"
                pagination.sort_order = "desc"

            return self.get_paginated(pagination, filters=filters)
        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get paginated content by type {content_type}: {exc}")

    def search_by_title_paginated(self, search_term: str, pagination: PaginationRequest) -> PaginatedResponse:
        """Perform paginated case-insensitive LIKE search on titles."""
        try:
            query = self.db.query(self.model)
            query = query.filter(self.model.title.ilike(f"%{search_term}%"))

            # Apply sorting
            if pagination.sort_field and hasattr(self.model, pagination.sort_field):
                sort_field = getattr(self.model, pagination.sort_field)
                if pagination.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(self.model.created_at))

            # Get total count and paginated results
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = (pagination.skip + pagination.page_size) < total_count
            has_previous = pagination.page > 1

            from genonaut.api.models.responses import PaginationMeta
            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total_count,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=items, pagination=pagination_meta)

        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to search content by title: {exc}")

    def search_by_metadata_paginated(self, metadata_filter: Dict[str, Any], pagination: PaginationRequest) -> PaginatedResponse:
        """Paginated search by JSON metadata using PostgreSQL containment operators."""
        try:
            query = self.db.query(self.model)

            for key, value in metadata_filter.items():
                filter_condition = self.model.item_metadata.op('@>')(f'{{"{key}": "{value}"}}')
                query = query.filter(filter_condition)

            # Apply sorting
            if pagination.sort_field and hasattr(self.model, pagination.sort_field):
                sort_field = getattr(self.model, pagination.sort_field)
                if pagination.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(self.model.created_at))

            # Get total count and paginated results
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = (pagination.skip + pagination.page_size) < total_count
            has_previous = pagination.page > 1

            from genonaut.api.models.responses import PaginationMeta
            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total_count,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=items, pagination=pagination_meta)

        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to search content by metadata: {exc}")

    def search_by_tags_paginated(self, tags: List[str], pagination: PaginationRequest) -> PaginatedResponse:
        """Paginated search for items whose tag array contains every tag in tags."""
        try:
            query = self.db.query(self.model)
            for tag in tags:
                query = query.filter(self.model.tags.op('?')(tag))

            # Apply sorting
            if pagination.sort_field and hasattr(self.model, pagination.sort_field):
                sort_field = getattr(self.model, pagination.sort_field)
                if pagination.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(self.model.created_at))

            # Get total count and paginated results
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = (pagination.skip + pagination.page_size) < total_count
            has_previous = pagination.page > 1

            from genonaut.api.models.responses import PaginationMeta
            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total_count,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=items, pagination=pagination_meta)

        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to search content by tags: {exc}")

    def get_top_rated_paginated(self, pagination: PaginationRequest) -> PaginatedResponse:
        """Get paginated highest-rated content records."""
        try:
            # Override sort settings for top-rated query
            pagination.sort_field = "quality_score"
            pagination.sort_order = "desc"

            filters = {}
            # We can add a filter for quality_score > 0 if needed
            query = self.db.query(self.model)
            query = query.filter(self.model.quality_score > 0)
            query = query.order_by(desc(self.model.quality_score))

            # Get total count and paginated results
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = (pagination.skip + pagination.page_size) < total_count
            has_previous = pagination.page > 1

            from genonaut.api.models.responses import PaginationMeta
            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total_count,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=items, pagination=pagination_meta)

        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get top rated content: {exc}")

    def get_recent_paginated(self, pagination: PaginationRequest, days: int = 7) -> PaginatedResponse:
        """Get paginated content created within the last specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(self.model)
            query = query.filter(self.model.created_at >= cutoff_date)
            query = query.order_by(desc(self.model.created_at))

            # Get total count and paginated results
            total_count = query.count()
            items = query.offset(pagination.skip).limit(pagination.page_size).all()

            # Calculate pagination metadata
            has_next = (pagination.skip + pagination.page_size) < total_count
            has_previous = pagination.page > 1

            from genonaut.api.models.responses import PaginationMeta
            pagination_meta = PaginationMeta(
                page=pagination.page,
                page_size=pagination.page_size,
                total_count=total_count,
                has_next=has_next,
                has_previous=has_previous
            )

            return PaginatedResponse(items=items, pagination=pagination_meta)

        except SQLAlchemyError as exc:
            raise DatabaseError(f"Failed to get recent content: {exc}")
