"""Content repository for database operations."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from genonaut.api.exceptions import DatabaseError
from genonaut.api.repositories.base import BaseRepository
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
