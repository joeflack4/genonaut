"""Content service for business logic operations."""

from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from sqlalchemy import desc, func, text, literal, or_, and_, case
from sqlalchemy.orm import Session

from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.repositories.tag_repository import TagRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.db.schema import ContentItem, ContentItemAuto, ContentItemAll, UserInteraction, User, ContentTag
from genonaut.api.services.flagged_content_service import FlaggedContentService
from genonaut.api.services.tag_query_planner import TagQueryPlanner
from genonaut.api.services.tag_query_builder import TagQueryBuilder
from genonaut.api.services.content_query_strategies import QueryStrategy, ORMQueryExecutor, RawSQLQueryExecutor
from genonaut.api.utils.tag_identifiers import expand_tag_identifiers
from genonaut.api.config import get_settings

_VALID_CONTENT_TYPES = {"text", "image", "video", "audio"}


class ContentService:
    """Service class for content business logic."""

    def __init__(self, db: Session, *, model: Type[ContentItem] = ContentItem):
        self.model: Type[ContentItem] = model
        self.db = db
        self.repository = ContentRepository(db, model=model)
        self.user_repository = UserRepository(db)

        # Initialize tag filtering components
        self.tag_repository = TagRepository(db)
        self.tag_query_planner = TagQueryPlanner(self.tag_repository)
        self.tag_query_builder = TagQueryBuilder(db, self.tag_query_planner)

        # Try to initialize flagging service (optional)
        self.flagging_service = None
        try:
            self.flagging_service = FlaggedContentService(db)
        except ValidationError:
            # Flag words file not configured - flagging will be disabled
            pass

    @staticmethod
    def _apply_tag_filter(query, column, tags: Optional[List[str]], tag_match: str):
        """Apply tag filtering according to the requested match logic."""

        if not tags:
            return query

        dialect_name = ""
        query_session = getattr(query, "session", None)
        if query_session and query_session.bind is not None:
            dialect_name = query_session.bind.dialect.name

        # SQLite (used in tests) does not support the JSON containment operators we rely on.
        # Defer tag filtering to Python post-processing for non-PostgreSQL backends.
        if dialect_name and dialect_name != "postgresql":
            return query

        normalized = (tag_match or "any").lower()
        unique_tags = list(dict.fromkeys(tags))
        if not unique_tags:
            return query

        if normalized == "all":
            # Use JSON containment operator to ensure all requested tags are present
            return query.filter(column.contains(unique_tags))

        # Default to "any" logic by OR-ing individual containment checks
        or_clauses = [column.contains([tag]) for tag in unique_tags]
        return query.filter(or_(*or_clauses))

    @staticmethod
    def _matches_tag_logic(item_tags: Optional[List[str]], tags: List[str], tag_match: str) -> bool:
        """Determine whether the provided tags satisfy the requested match logic."""

        if not tags:
            return True

        normalized = (tag_match or "any").lower()
        query_tags = [tag for tag in tags if tag]
        if not query_tags:
            return True

        flattened_tags: set[str] = set()
        for entry in item_tags or []:
            if isinstance(entry, str):
                flattened_tags.add(entry)
                continue

            if isinstance(entry, dict):
                for key in ("id", "slug", "name", "value"):
                    value = entry.get(key)
                    if isinstance(value, str) and value:
                        flattened_tags.add(value)
        tag_set = flattened_tags
        if normalized == "all":
            return all(tag in tag_set for tag in query_tags)
        return any(tag in tag_set for tag in query_tags)

    def _apply_tag_filter_via_junction(
        self,
        query,
        content_model,
        content_source: Optional[str],
        tag_uuids: List[UUID],
        tag_match: str
    ):
        """Apply tag filtering using content_tags junction table with adaptive query strategies.

        Uses TagQueryBuilder which selects optimal query strategy based on tag cardinalities:
        - Self-join for small K (K <= 3)
        - Group/HAVING for medium K with selective tags
        - Two-phase rarest-first for large K or common tags

        Args:
            query: SQLAlchemy query to filter
            content_model: ContentItem, ContentItemAuto, or ContentItemAll model class
            content_source: 'regular', 'auto', or None (for ContentItemAll with partition already filtered)
            tag_uuids: List of tag UUIDs to filter by
            tag_match: 'any' or 'all' matching logic

        Returns:
            Filtered query

        Note:
            When using ContentItemAll, content_source should be None since the partition
            is already filtered by source_type in the main query. For individual table
            queries (ContentItem/ContentItemAuto), content_source is required.
        """
        if not tag_uuids:
            return query

        # Determine content sources for query planning
        content_sources = []
        if content_source:
            content_sources = [content_source]
        elif hasattr(content_model, 'source_type'):
            # ContentItemAll - determine sources from query filters
            # For now, assume both sources unless explicitly filtered
            content_sources = ['regular', 'auto']
        else:
            # Fallback
            content_sources = ['regular', 'auto']

        # Use adaptive query builder
        return self.tag_query_builder.apply_tag_filter(
            query,
            content_model,
            tag_uuids,
            content_sources,
            tag_match
        )

    @staticmethod
    def _apply_enhanced_search_filter(query, content_model, search_term: Optional[str]):
        """Apply enhanced search filter with phrase and word matching.

        Uses search_parser to detect quoted phrases and individual words.
        Phrases use ILIKE for exact substring matching.
        Words use standard ILIKE for flexible matching (simpler than FTS for now).

        Args:
            query: SQLAlchemy query to filter
            content_model: ContentItem or ContentItemAuto model class
            search_term: Search query string (may contain quoted phrases)

        Returns:
            Filtered query
        """
        if not search_term or not search_term.strip():
            return query

        from genonaut.api.services.search_parser import parse_search_query

        parsed = parse_search_query(search_term)

        # Build search conditions
        search_conditions = []

        # Add phrase matching conditions - exact substring match
        for phrase in parsed.phrases:
            if phrase:
                phrase_condition = or_(
                    content_model.title.ilike(f"%{phrase}%"),
                    content_model.prompt.ilike(f"%{phrase}%")
                )
                search_conditions.append(phrase_condition)

        # Add word matching conditions - any word matches
        for word in parsed.words:
            if word:
                word_condition = or_(
                    content_model.title.ilike(f"%{word}%"),
                    content_model.prompt.ilike(f"%{word}%")
                )
                search_conditions.append(word_condition)

        # Combine all conditions with AND (all phrases and words must match)
        if search_conditions:
            query = query.filter(*search_conditions)

        return query

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
        prompt: Optional[str] = None,
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
            final_prompt = content_data_dict.get("prompt")
            final_creator_id = content_data_dict.get("creator_id")
            final_item_metadata = content_data_dict.get("item_metadata") or {}
            final_tags = content_data_dict.get("tags") or []
            final_is_private = content_data_dict.get("is_private", False)
        else:
            final_title = title
            final_content_type = content_type
            final_content_payload = content_data
            final_prompt = prompt
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

        if not final_prompt or not final_prompt.strip():
            raise ValidationError("Prompt cannot be empty")
        if len(final_prompt) > 20000:
            raise ValidationError("Prompt cannot exceed 20000 characters")

        payload = {
            "title": final_title.strip(),
            "content_type": final_content_type,
            "content_data": final_content_payload,
            "prompt": final_prompt.strip(),
            "creator_id": final_creator_id,
            "item_metadata": final_item_metadata,
            "is_private": final_is_private,
            "quality_score": 0.5,
        }

        # Create the content item
        content_item = self.repository.create(payload)

        # Sync tags to junction table if provided
        if final_tags:
            from uuid import UUID, uuid5
            from genonaut.api.utils.tag_identifiers import get_uuid_for_slug, TAG_UUID_NAMESPACE
            from genonaut.db.schema import Tag, ContentTag

            content_source = "auto" if self.model == ContentItemAuto else "regular"

            for tag in final_tags:
                # Convert tag to UUID
                tag_uuid = None
                if isinstance(tag, UUID):
                    tag_uuid = tag
                elif isinstance(tag, str):
                    try:
                        tag_uuid = UUID(tag)
                    except ValueError:
                        uuid_str = get_uuid_for_slug(tag)
                        if uuid_str:
                            tag_uuid = UUID(uuid_str)
                        else:
                            # Generate UUID for unknown tags
                            tag_uuid = uuid5(TAG_UUID_NAMESPACE, tag)
                            # Create tag if it doesn't exist
                            existing_tag = self.db.query(Tag).filter(Tag.id == tag_uuid).first()
                            if not existing_tag:
                                new_tag = Tag(
                                    id=tag_uuid,
                                    name=tag.replace('_', ' ').title(),
                                    tag_metadata={"auto_created": True, "slug": tag}
                                )
                                self.db.add(new_tag)
                                self.db.flush()

                if tag_uuid:
                    # Create junction table entry
                    existing = self.db.query(ContentTag).filter(
                        ContentTag.content_id == content_item.id,
                        ContentTag.content_source == content_source,
                        ContentTag.tag_id == tag_uuid
                    ).first()

                    if not existing:
                        content_tag = ContentTag(
                            content_id=content_item.id,
                            content_source=content_source,
                            tag_id=tag_uuid
                        )
                        self.db.add(content_tag)

            self.db.commit()

        # Automatically check for problematic words and flag if needed
        if self.flagging_service:
            try:
                # Extract text to analyze (prompt from metadata, or title as fallback)
                text_to_check = ""
                if final_item_metadata and isinstance(final_item_metadata, dict):
                    text_to_check = final_item_metadata.get("prompt", "")
                if not text_to_check:
                    text_to_check = final_title

                # Determine content source based on model type
                content_source = "auto" if self.model == ContentItemAuto else "regular"

                # Flag if problematic words found
                if text_to_check:
                    self.flagging_service.flag_content_item(
                        text=text_to_check,
                        content_item_id=content_item.id if content_source == "regular" else None,
                        content_item_auto_id=content_item.id if content_source == "auto" else None,
                        content_source=content_source,
                        creator_id=final_creator_id
                    )
            except Exception:
                # Don't fail content creation if flagging fails
                # Just log silently and continue
                pass

        return content_item

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

        if is_private is not None:
            update_data["is_private"] = is_private

        updated_content = self.repository.update(content_id, update_data)

        # Handle tags separately - update junction table
        if tags is not None:
            from uuid import UUID, uuid5
            from genonaut.api.utils.tag_identifiers import get_uuid_for_slug, TAG_UUID_NAMESPACE
            from genonaut.db.schema import Tag, ContentTag

            content_source = "auto" if self.model == ContentItemAuto else "regular"

            # Clear existing tags
            self.db.query(ContentTag).filter(
                ContentTag.content_id == content_id,
                ContentTag.content_source == content_source
            ).delete()

            # Add new tags
            for tag in tags:
                tag_uuid = None
                if isinstance(tag, UUID):
                    tag_uuid = tag
                elif isinstance(tag, str):
                    try:
                        tag_uuid = UUID(tag)
                    except ValueError:
                        uuid_str = get_uuid_for_slug(tag)
                        if uuid_str:
                            tag_uuid = UUID(uuid_str)
                        else:
                            tag_uuid = uuid5(TAG_UUID_NAMESPACE, tag)
                            existing_tag = self.db.query(Tag).filter(Tag.id == tag_uuid).first()
                            if not existing_tag:
                                new_tag = Tag(
                                    id=tag_uuid,
                                    name=tag.replace('_', ' ').title(),
                                    tag_metadata={"auto_created": True, "slug": tag}
                                )
                                self.db.add(new_tag)
                                self.db.flush()

                if tag_uuid:
                    content_tag = ContentTag(
                        content_id=content_id,
                        content_source=content_source,
                        tag_id=tag_uuid
                    )
                    self.db.add(content_tag)

            self.db.commit()

        return updated_content

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

        # Note: Python-side tag filtering is no longer supported since tags are in junction table
        # Tags should be filtered at database level using content_tags table
        if tags:
            # For now, skip Python filtering - tags should be filtered via database query
            pass

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
        """Get unified content statistics using cached stats with fallback.

        This method queries the gen_source_stats cache table for fast lookups,
        falling back to live queries if cache is empty.
        """
        from genonaut.db.schema import GenSourceStats

        session = self.repository.db

        # Try to get cached stats first
        user_regular_count = 0
        user_auto_count = 0

        if user_id:
            user_stats = session.query(GenSourceStats).filter(
                GenSourceStats.user_id == user_id
            ).all()

            for stat in user_stats:
                if stat.source_type == 'regular':
                    user_regular_count = stat.count
                elif stat.source_type == 'auto':
                    user_auto_count = stat.count

        # Get community stats from cache
        community_stats = session.query(GenSourceStats).filter(
            GenSourceStats.user_id.is_(None)
        ).all()

        community_regular_count = 0
        community_auto_count = 0
        for stat in community_stats:
            if stat.source_type == 'regular':
                community_regular_count = stat.count
            elif stat.source_type == 'auto':
                community_auto_count = stat.count

        # Fallback to live queries if cache is empty
        if not community_stats:
            community_regular_count = session.query(func.count(ContentItemAll.id)).filter(
                ContentItemAll.source_type == 'items'
            ).scalar() or 0

            community_auto_count = session.query(func.count(ContentItemAll.id)).filter(
                ContentItemAll.source_type == 'auto'
            ).scalar() or 0

        if user_id and not user_stats:
            user_regular_count = session.query(func.count(ContentItemAll.id)).filter(
                ContentItemAll.source_type == 'items',
                ContentItemAll.creator_id == user_id
            ).scalar() or 0

            user_auto_count = session.query(func.count(ContentItemAll.id)).filter(
                ContentItemAll.source_type == 'auto',
                ContentItemAll.creator_id == user_id
            ).scalar() or 0

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
        content_source_types: Optional[List[str]] = None,
        user_id: Optional[UUID] = None,
        search_term: Optional[str] = None,
        sort_field: str = "created_at",
        sort_order: str = "desc",
        tags: Optional[List[str]] = None,
        tag_match: str = "any",
        include_stats: bool = False,
    ) -> Dict[str, Any]:
        """
        Get paginated content from partitioned parent table content_items_all.

        This method now queries the partitioned parent table directly, which eliminates
        the need for manual UNION operations. PostgreSQL automatically handles partition
        pruning when filtering by source_type.

        Args:
            pagination: Pagination parameters (supports both offset and cursor pagination)
            content_types: List of content types to include ("regular", "auto") - LEGACY
            creator_filter: "all", "user", or "community" - LEGACY
            content_source_types: Specific combinations (e.g., ['user-regular', 'community-auto']) - PREFERRED
            user_id: User ID for filtering
            search_term: Search term for title filtering
            sort_field: Field to sort by (default: created_at)
            sort_order: Sort order ("asc" or "desc")
            tags: List of tag UUIDs/slugs to filter by
            tag_match: Tag matching logic ("any" for OR, "all" for AND)

        Returns:
            Dict with items, pagination metadata, and stats
        """
        import time
        import logging
        perf_logger = logging.getLogger("genonaut.performance")
        t_start = time.perf_counter()
        timings = {}

        session = self.repository.db

        # Normalize tags and extract UUIDs for junction table queries
        normalized_tags = list(dict.fromkeys(tags)) if tags else []
        tag_uuids = []
        if normalized_tags:
            from uuid import uuid5
            from genonaut.api.utils.tag_identifiers import get_uuid_for_slug, TAG_UUID_NAMESPACE

            for tag in normalized_tags:
                tag_uuid = None
                try:
                    if isinstance(tag, UUID):
                        tag_uuid = tag
                    else:
                        tag_uuid = UUID(str(tag))
                except (ValueError, AttributeError):
                    if isinstance(tag, str):
                        uuid_str = get_uuid_for_slug(tag)
                        if uuid_str:
                            tag_uuid = UUID(uuid_str)
                        else:
                            tag_uuid = uuid5(TAG_UUID_NAMESPACE, tag)

                if tag_uuid:
                    tag_uuids.append(tag_uuid)

        # For backward compatibility with JSONB array queries
        normalized_tags = expand_tag_identifiers(normalized_tags)

        # Use junction table filter (tags column removed from content tables)
        use_junction_table_filter = bool(tag_uuids)
        use_python_tag_filter = False

        t_after_tag_processing = time.perf_counter()
        timings['tag_processing'] = t_after_tag_processing - t_start

        # Map content_source_types to source_type values for partition pruning
        source_type_filters = []
        creator_filters = []  # List of (source_type, creator_condition) tuples

        if content_source_types is not None:
            # NEW APPROACH: Parse content_source_types to determine filters
            for cst in content_source_types:
                if cst == 'user-regular':
                    if user_id:
                        creator_filters.append(('items', ContentItemAll.creator_id == user_id))
                elif cst == 'user-auto':
                    if user_id:
                        creator_filters.append(('auto', ContentItemAll.creator_id == user_id))
                elif cst == 'community-regular':
                    if user_id:
                        creator_filters.append(('items', ContentItemAll.creator_id != user_id))
                elif cst == 'community-auto':
                    if user_id:
                        creator_filters.append(('auto', ContentItemAll.creator_id != user_id))

            # Extract unique source_types
            source_type_filters = list(set(st for st, _ in creator_filters))

        else:
            # LEGACY APPROACH: Use content_types and creator_filter
            if content_types is None:
                content_types = ["regular", "auto"]

            # Map legacy content_types to source_type values
            if "regular" in content_types:
                source_type_filters.append('items')
            if "auto" in content_types:
                source_type_filters.append('auto')

        if not source_type_filters:
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

        # Use strategy pattern for query execution (when using new content_source_types approach)
        # Cursor pagination not yet supported in strategies, so fall back to ORM for that case
        use_strategy_pattern = (
            content_source_types is not None and
            not pagination.cursor and
            not use_python_tag_filter
        )

        if use_strategy_pattern:
            # Select query strategy from config
            settings = get_settings()
            strategy_name = settings.content_query_strategy
            if strategy_name == QueryStrategy.RAW_SQL.value:
                executor = RawSQLQueryExecutor()
            else:
                executor = ORMQueryExecutor()

            t_before_query = time.perf_counter()
            timings['query_building'] = t_before_query - t_after_tag_processing

            # Execute query using strategy
            rows, total_count = executor.execute_query(
                session=session,
                pagination=pagination,
                content_source_types=content_source_types,
                user_id=user_id,
                tag_uuids=tag_uuids if not use_python_tag_filter else [],
                tag_match=tag_match,
                search_term=search_term,
                sort_field=sort_field,
                sort_order=sort_order,
            )

            t_after_query = time.perf_counter()
            timings['query_execution'] = t_after_query - t_before_query

            # Format results (raw SQL returns tuples, ORM returns RowProxy)
            items = []
            for row in rows:
                # Handle both tuple and ORM object results
                if hasattr(row, '_mapping'):
                    # SQLAlchemy Row object
                    items.append({
                        "id": row.id,
                        "title": row.title,
                        "content_type": row.content_type,
                        "content_data": row.content_data,
                        "path_thumb": row.path_thumb,
                        "path_thumbs_alt_res": row.path_thumbs_alt_res,
                        "prompt": row.prompt,
                        "creator_id": str(row.creator_id),
                        "creator_username": row.creator_username,
                        "item_metadata": row.item_metadata,
                        "is_private": row.is_private,
                        "quality_score": row.quality_score,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                        "source_type": row.source_type,
                    })
                else:
                    # Raw SQL tuple result (id, title, content_type, ...)
                    items.append({
                        "id": row[0],
                        "title": row[1],
                        "content_type": row[2],
                        "content_data": row[3],
                        "path_thumb": row[4],
                        "path_thumbs_alt_res": row[5],
                        "prompt": row[6],
                        "creator_id": str(row[7]),
                        "item_metadata": row[8],
                        "is_private": row[9],
                        "quality_score": row[10],
                        "created_at": row[11].isoformat() if row[11] else None,
                        "updated_at": row[12].isoformat() if row[12] else None,
                        "source_type": row[13],
                        "creator_username": row[14],
                    })

            t_after_serialization = time.perf_counter()
            timings['result_serialization'] = t_after_serialization - t_after_query

            # No cursor pagination support in strategy pattern yet
            use_cursor_pagination = False

        else:
            # Fall back to original ORM implementation for cursor pagination or legacy code paths
            # Build query against partitioned parent table (ORM class)
            query = session.query(
                ContentItemAll.id,
                ContentItemAll.title,
                ContentItemAll.content_type,
                ContentItemAll.content_data,
                ContentItemAll.path_thumb,
                ContentItemAll.path_thumbs_alt_res,
                ContentItemAll.prompt,
                ContentItemAll.creator_id,
                ContentItemAll.item_metadata,
                ContentItemAll.is_private,
                ContentItemAll.quality_score,
                ContentItemAll.created_at,
                ContentItemAll.updated_at,
                # Return actual partition values: 'items' for regular content, 'auto' for auto-generated
                ContentItemAll.source_type,
                User.username.label('creator_username')
            ).join(User, ContentItemAll.creator_id == User.id)

            # Apply partition pruning filter (CRITICAL for performance)
            # This enables PostgreSQL to skip scanning irrelevant partitions
            query = query.filter(ContentItemAll.source_type.in_(source_type_filters))

            # Apply creator filters for content_source_types approach
            if content_source_types is not None and creator_filters:
                # Build OR conditions for each (source_type, creator_condition) pair
                creator_conditions = []
                for source_type, condition in creator_filters:
                    creator_conditions.append(and_(ContentItemAll.source_type == source_type, condition))

                if creator_conditions:
                    query = query.filter(or_(*creator_conditions))

            # LEGACY: Apply creator filter if using old approach
            elif creator_filter != "all" and user_id:
                if creator_filter == "user":
                    query = query.filter(ContentItemAll.creator_id == user_id)
                elif creator_filter == "community":
                    query = query.filter(ContentItemAll.creator_id != user_id)

            # Apply search filter (using ORM class)
            if search_term:
                from genonaut.api.services.search_parser import parse_search_query
                parsed = parse_search_query(search_term)
                search_conditions = []

                for phrase in parsed.phrases:
                    if phrase:
                        phrase_condition = or_(
                            ContentItemAll.title.ilike(f"%{phrase}%"),
                            ContentItemAll.prompt.ilike(f"%{phrase}%")
                        )
                        search_conditions.append(phrase_condition)

                for word in parsed.words:
                    if word:
                        word_condition = or_(
                            ContentItemAll.title.ilike(f"%{word}%"),
                            ContentItemAll.prompt.ilike(f"%{word}%")
                        )
                        search_conditions.append(word_condition)

                if search_conditions:
                    query = query.filter(*search_conditions)

            # Apply tag filtering via junction table (using ORM class)
            tag_match_normalized = (tag_match or "any").lower()
            if tag_match_normalized not in {"any", "all"}:
                tag_match_normalized = "any"

            if not use_python_tag_filter and tag_uuids:
                unique_tags = list(dict.fromkeys(tag_uuids))

                if tag_match_normalized == "all":
                    # For "all" matching: content must have ALL specified tags
                    for tag_id in unique_tags:
                        exists_clause = session.query(ContentTag.content_id).filter(
                            ContentTag.content_id == ContentItemAll.id,
                            ContentTag.tag_id == tag_id
                        ).exists()
                        query = query.filter(exists_clause)
                else:
                    # For "any" matching: content must have AT LEAST ONE of the specified tags
                    exists_clause = session.query(ContentTag.content_id).filter(
                        ContentTag.content_id == ContentItemAll.id,
                        ContentTag.tag_id.in_(unique_tags)
                    ).exists()
                    query = query.filter(exists_clause)

            # Apply sorting (enables partition-wise sorting with MergeAppend)
            if sort_field == "created_at":
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(ContentItemAll.created_at), desc(ContentItemAll.id))
                else:
                    query = query.order_by(ContentItemAll.created_at, ContentItemAll.id)
            elif sort_field == "quality_score":
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(ContentItemAll.quality_score), desc(ContentItemAll.id))
                else:
                    query = query.order_by(ContentItemAll.quality_score, ContentItemAll.id)
            else:
                # Default sort by created_at desc
                query = query.order_by(desc(ContentItemAll.created_at), desc(ContentItemAll.id))

            # Apply cursor-based filtering if cursor is provided
            use_cursor_pagination = bool(pagination.cursor)
            if pagination.cursor:
                from genonaut.api.utils.cursor_pagination import decode_cursor, CursorError

                try:
                    cursor_created_at, cursor_id, cursor_src = decode_cursor(pagination.cursor)

                    # Apply cursor filter based on sort order (keyset pagination)
                    if sort_field == "created_at":
                        if sort_order.lower() == "desc":
                            query = query.filter(
                                or_(
                                    ContentItemAll.created_at < cursor_created_at,
                                    and_(
                                        ContentItemAll.created_at == cursor_created_at,
                                        ContentItemAll.id < cursor_id
                                    )
                                )
                            )
                        else:
                            query = query.filter(
                                or_(
                                    ContentItemAll.created_at > cursor_created_at,
                                    and_(
                                        ContentItemAll.created_at == cursor_created_at,
                                        ContentItemAll.id > cursor_id
                                    )
                                )
                            )
                except CursorError:
                    # Invalid cursor - ignore and fall back to OFFSET/LIMIT
                    pass

            # Get total count for pagination
            is_sqlite = session.bind and session.bind.dialect.name != "postgresql"
            if use_junction_table_filter and tag_uuids and not is_sqlite:
                # Return high estimate for tag-filtered queries on large datasets
                total_count = 999999
            else:
                try:
                    # Count query - remove ORDER BY for performance
                    count_query = query.order_by(None)
                    total_count = count_query.count()
                except Exception:
                    # Fallback to simple count
                    count_query = session.query(func.count(ContentItemAll.id)).filter(
                        ContentItemAll.source_type.in_(source_type_filters)
                    )
                    if search_term:
                        count_query = count_query.filter(ContentItemAll.title.ilike(f"%{search_term}%"))
                    total_count = count_query.scalar() or 0

            # Apply pagination
            offset = (pagination.page - 1) * pagination.page_size if pagination.page > 0 else 0
            if not use_cursor_pagination:
                query = query.offset(offset)
            query = query.limit(pagination.page_size)

            t_before_query = time.perf_counter()
            timings['query_building'] = t_before_query - t_after_tag_processing

            # Execute query and format results
            rows = query.all()

            t_after_query = time.perf_counter()
            timings['query_execution'] = t_after_query - t_before_query
            items = []
            for row in rows:
                items.append({
                    "id": row.id,
                    "title": row.title,
                    "content_type": row.content_type,
                    "content_data": row.content_data,
                    "path_thumb": row.path_thumb,
                    "path_thumbs_alt_res": row.path_thumbs_alt_res,
                    "prompt": row.prompt,
                    "creator_id": str(row.creator_id),
                    "creator_username": row.creator_username,
                    "item_metadata": row.item_metadata,
                    "is_private": row.is_private,
                    "quality_score": row.quality_score,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "source_type": row.source_type,
                })

            t_after_serialization = time.perf_counter()
            timings['result_serialization'] = t_after_serialization - t_after_query

            # Store cursor pagination flag for later
            use_cursor_pagination = bool(pagination.cursor)

        # Shared pagination metadata calculation (for both strategy and ORM paths)
        if total_count == 999999 and len(items) == 0 and pagination.page == 1:
            total_count = 0

        # Handle unknown count (-1) - occurs when COUNT query is skipped for performance
        if total_count == -1:
            total_pages = -1  # Unknown page count
            # Use cursor/item count to determine if there's more data
            has_next = len(items) == pagination.page_size  # Full page suggests more data
        else:
            total_pages = (total_count + pagination.page_size - 1) // pagination.page_size if pagination.page_size else 0
            has_next = pagination.page < total_pages

        has_previous = pagination.page > 1

        # Generate next/prev cursors (always, to support hybrid pagination)
        # Clients can use offset pagination for page 1, then switch to cursor pagination
        next_cursor = None
        prev_cursor = None
        if items:
            from genonaut.api.utils.cursor_pagination import create_next_cursor, create_prev_cursor

            # Generate next cursor if we got a full page (more results likely exist)
            if len(items) == pagination.page_size:
                next_cursor = create_next_cursor(items)

            # Generate prev cursor only if currently using cursor pagination
            if use_cursor_pagination and pagination.cursor:
                prev_cursor = create_prev_cursor(items)

        t_end = time.perf_counter()
        timings['total'] = t_end - t_start

        # Log detailed performance breakdown
        perf_logger.info(
            f"[SERVICE PERF] get_unified_content_paginated: "
            f"tag_proc={timings.get('tag_processing', 0)*1000:.2f}ms "
            f"query_build={timings.get('query_building', 0)*1000:.2f}ms "
            f"query_exec={timings.get('query_execution', 0)*1000:.2f}ms "
            f"serialization={timings.get('result_serialization', 0)*1000:.2f}ms "
            f"total={timings['total']*1000:.2f}ms "
            f"items_returned={len(items)}"
        )

        # Conditionally include stats based on include_stats parameter
        # Stats queries add ~800ms, so they're opt-in for performance
        response = {
            "items": items,
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
                "next_cursor": next_cursor,
                "prev_cursor": prev_cursor,
            },
        }

        if include_stats:
            response["stats"] = self.get_unified_content_stats(user_id)

        return response


class ContentAutoService(ContentService):
    """Service class specialised for ``ContentItemAuto`` records."""

    def __init__(self, db: Session):
        super().__init__(db, model=ContentItemAuto)
