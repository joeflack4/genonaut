"""Content service for business logic operations."""

from typing import Any, Dict, List, Optional, Type

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
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
        is_public: Optional[bool] = None,
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
            final_is_public = content_data_dict.get("is_public", True)
            final_is_private = content_data_dict.get("is_private", False)
        else:
            final_title = title
            final_content_type = content_type
            final_content_payload = content_data
            final_creator_id = creator_id
            final_item_metadata = item_metadata or {}
            final_tags = tags or []
            final_is_public = True if is_public is None else is_public
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

        if final_is_public and final_is_private:
            raise ValidationError("Content cannot be both public and private")

        payload = {
            "title": final_title.strip(),
            "content_type": final_content_type,
            "content_data": final_content_payload,
            "creator_id": final_creator_id,
            "item_metadata": final_item_metadata,
            "tags": final_tags,
            "is_public": final_is_public,
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
        is_public: Optional[bool] = None,
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

        if is_public is not None:
            update_data["is_public"] = is_public
        if is_private is not None:
            update_data["is_private"] = is_private

        final_is_public = update_data.get("is_public", content.is_public)
        final_is_private = update_data.get("is_private", content.is_private)
        if final_is_public and final_is_private:
            raise ValidationError("Content cannot be both public and private")

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
            query = query.filter(self.model.is_public.is_(True), self.model.is_private.is_(False))

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
        public_content = self.repository.count({"is_public": True, "is_private": False})
        private_content = self.repository.count({"is_private": True})

        type_breakdown = {
            content_type: self.repository.count({"content_type": content_type})
            for content_type in _VALID_CONTENT_TYPES
        }

        return {
            "total_content": total_content,
            "public_content": public_content,
            "private_content": private_content,
            "type_breakdown": type_breakdown,
        }


class ContentAutoService(ContentService):
    """Service class specialised for ``ContentItemAuto`` records."""

    def __init__(self, db: Session):
        super().__init__(db, model=ContentItemAuto)
