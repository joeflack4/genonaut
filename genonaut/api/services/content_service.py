"""Content service for business logic operations."""

from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from sqlalchemy import desc, func, text, literal, or_
from sqlalchemy.orm import Session

from genonaut.api.exceptions import EntityNotFoundError, ValidationError
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.api.repositories.user_repository import UserRepository
from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.db.schema import ContentItem, ContentItemAuto, UserInteraction, User, ContentTag
from genonaut.api.services.flagged_content_service import FlaggedContentService
from genonaut.api.utils.tag_identifiers import expand_tag_identifiers

_VALID_CONTENT_TYPES = {"text", "image", "video", "audio"}


class ContentService:
    """Service class for content business logic."""

    def __init__(self, db: Session, *, model: Type[ContentItem] = ContentItem):
        self.model: Type[ContentItem] = model
        self.db = db
        self.repository = ContentRepository(db, model=model)
        self.user_repository = UserRepository(db)

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
        content_source: str,
        tag_uuids: List[UUID],
        tag_match: str
    ):
        """Apply tag filtering using content_tags junction table.

        This is the optimized approach for tag filtering that uses the normalized
        content_tags junction table instead of JSONB array operations.

        Args:
            query: SQLAlchemy query to filter
            content_model: ContentItem or ContentItemAuto model class
            content_source: 'regular' or 'auto' (for content_tags.content_source)
            tag_uuids: List of tag UUIDs to filter by
            tag_match: 'any' or 'all' matching logic

        Returns:
            Filtered query
        """
        if not tag_uuids:
            return query

        normalized = (tag_match or "any").lower()
        unique_tags = list(dict.fromkeys(tag_uuids))

        if not unique_tags:
            return query

        # Use EXISTS for better performance - PostgreSQL optimizes these well
        if normalized == "all":
            # For "all" matching: content must have ALL specified tags
            # Add an EXISTS clause for each tag
            for tag_id in unique_tags:
                exists_clause = self.db.query(ContentTag.content_id).filter(
                    ContentTag.content_id == content_model.id,
                    ContentTag.content_source == content_source,
                    ContentTag.tag_id == tag_id
                ).exists()
                query = query.filter(exists_clause)
            return query

        # For "any" matching: content must have AT LEAST ONE of the specified tags
        # Single EXISTS with IN clause
        exists_clause = self.db.query(ContentTag.content_id).filter(
            ContentTag.content_id == content_model.id,
            ContentTag.content_source == content_source,
            ContentTag.tag_id.in_(unique_tags)
        ).exists()
        return query.filter(exists_clause)

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
        content_source_types: Optional[List[str]] = None,
        user_id: Optional[UUID] = None,
        search_term: Optional[str] = None,
        sort_field: str = "created_at",
        sort_order: str = "desc",
        tags: Optional[List[str]] = None,
        tag_match: str = "any",
    ) -> Dict[str, Any]:
        """
        Get paginated content from both regular and auto tables.

        Args:
            pagination: Pagination parameters
            content_types: List of content types to include ("regular", "auto", or both) - LEGACY
            creator_filter: "all", "user", or "community" - LEGACY
            content_source_types: Specific combinations (e.g., ['user-regular', 'community-auto']) - PREFERRED
            user_id: User ID for filtering
            search_term: Search term for title filtering
            sort_field: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            tags: List of tags to filter by
            tag_match: Tag matching logic ("any" for OR, "all" for AND)
        """
        session = self.repository.db

        normalized_tags = list(dict.fromkeys(tags)) if tags else []

        # Extract UUIDs from input tags for junction table queries (before expansion)
        tag_uuids = []
        if normalized_tags:
            from uuid import uuid5
            from genonaut.api.utils.tag_identifiers import get_uuid_for_slug, TAG_UUID_NAMESPACE

            for tag in normalized_tags:
                tag_uuid = None
                try:
                    # Tags should be UUIDs (may be strings or UUID objects)
                    if isinstance(tag, UUID):
                        tag_uuid = tag
                    else:
                        # Try to parse as UUID string
                        tag_uuid = UUID(str(tag))
                except (ValueError, AttributeError):
                    # Not a valid UUID string - try to convert from slug
                    if isinstance(tag, str):
                        uuid_str = get_uuid_for_slug(tag)
                        if uuid_str:
                            tag_uuid = UUID(uuid_str)
                        else:
                            # Generate UUID for unknown tags (same as create/update logic)
                            tag_uuid = uuid5(TAG_UUID_NAMESPACE, tag)

                if tag_uuid:
                    tag_uuids.append(tag_uuid)

        # For backward compatibility with JSONB array queries, expand to include slugs
        normalized_tags = expand_tag_identifiers(normalized_tags)

        # Always use junction table now that tags column is removed
        use_junction_table_filter = bool(tag_uuids)
        use_python_tag_filter = False

        if session.bind is not None:
            if session.bind.dialect.name != "postgresql":
                # For SQLite, use junction table if we have UUIDs (tests populate it)
                use_junction_table_filter = bool(tag_uuids)
                use_python_tag_filter = False

        # Build unified query using UNION
        queries = []

        tag_match_normalized = (tag_match or "any").lower()
        if tag_match_normalized not in {"any", "all"}:
            tag_match_normalized = "any"

        # Parse content_source_types flags at function level so they're available in exception handlers
        include_user_regular = False
        include_user_auto = False
        include_community_regular = False
        include_community_auto = False

        # Use content_source_types if provided
        if content_source_types is not None:
            # Parse content_source_types to determine which queries to build
            include_user_regular = 'user-regular' in content_source_types
            include_user_auto = 'user-auto' in content_source_types
            include_community_regular = 'community-regular' in content_source_types
            include_community_auto = 'community-auto' in content_source_types

            # Build regular content query for user content
            if include_user_regular and user_id:
                user_regular_query = session.query(
                    ContentItem.id.label('id'),
                    ContentItem.title.label('title'),
                    ContentItem.content_type.label('content_type'),
                    ContentItem.content_data.label('content_data'),
                    ContentItem.path_thumb.label('path_thumb'),
                    ContentItem.path_thumbs_alt_res.label('path_thumbs_alt_res'),
                    ContentItem.prompt.label('prompt'),
                    ContentItem.creator_id.label('creator_id'),
                    ContentItem.item_metadata.label('item_metadata'),
                    ContentItem.is_private.label('is_private'),
                    ContentItem.quality_score.label('quality_score'),
                    ContentItem.created_at.label('created_at'),
                    ContentItem.updated_at.label('updated_at'),
                    literal('regular').label('source_type'),
                    User.username.label('creator_username')
                ).join(User, ContentItem.creator).filter(ContentItem.creator_id == user_id)

                if search_term:
                    user_regular_query = self._apply_enhanced_search_filter(user_regular_query, ContentItem, search_term)
                if not use_python_tag_filter:
                    user_regular_query = self._apply_tag_filter_via_junction(
                        user_regular_query,
                        ContentItem,
                        'regular',
                        tag_uuids,
                        tag_match_normalized,
                    )

                queries.append(user_regular_query)

            # Build regular content query for community content
            if include_community_regular and user_id:
                community_regular_query = session.query(
                    ContentItem.id.label('id'),
                    ContentItem.title.label('title'),
                    ContentItem.content_type.label('content_type'),
                    ContentItem.content_data.label('content_data'),
                    ContentItem.path_thumb.label('path_thumb'),
                    ContentItem.path_thumbs_alt_res.label('path_thumbs_alt_res'),
                    ContentItem.prompt.label('prompt'),
                    ContentItem.creator_id.label('creator_id'),
                    ContentItem.item_metadata.label('item_metadata'),
                    ContentItem.is_private.label('is_private'),
                    ContentItem.quality_score.label('quality_score'),
                    ContentItem.created_at.label('created_at'),
                    ContentItem.updated_at.label('updated_at'),
                    literal('regular').label('source_type'),
                    User.username.label('creator_username')
                ).join(User, ContentItem.creator).filter(ContentItem.creator_id != user_id)

                if search_term:
                    community_regular_query = self._apply_enhanced_search_filter(community_regular_query, ContentItem, search_term)
                if not use_python_tag_filter:
                    community_regular_query = self._apply_tag_filter_via_junction(
                        community_regular_query,
                        ContentItem,
                        'regular',
                        tag_uuids,
                        tag_match_normalized,
                    )

                queries.append(community_regular_query)

            # Build auto content query for user content
            if include_user_auto and user_id:
                user_auto_query = session.query(
                    ContentItemAuto.id.label('id'),
                    ContentItemAuto.title.label('title'),
                    ContentItemAuto.content_type.label('content_type'),
                    ContentItemAuto.content_data.label('content_data'),
                    ContentItemAuto.path_thumb.label('path_thumb'),
                    ContentItemAuto.path_thumbs_alt_res.label('path_thumbs_alt_res'),
                    ContentItemAuto.prompt.label('prompt'),
                    ContentItemAuto.creator_id.label('creator_id'),
                    ContentItemAuto.item_metadata.label('item_metadata'),
                    ContentItemAuto.is_private.label('is_private'),
                    ContentItemAuto.quality_score.label('quality_score'),
                    ContentItemAuto.created_at.label('created_at'),
                    ContentItemAuto.updated_at.label('updated_at'),
                    literal('auto').label('source_type'),
                    User.username.label('creator_username')
                ).join(User, ContentItemAuto.creator).filter(ContentItemAuto.creator_id == user_id)

                if search_term:
                    user_auto_query = self._apply_enhanced_search_filter(user_auto_query, ContentItemAuto, search_term)
                if not use_python_tag_filter:
                    user_auto_query = self._apply_tag_filter_via_junction(
                        user_auto_query,
                        ContentItemAuto,
                        'auto',
                        tag_uuids,
                        tag_match_normalized,
                    )

                queries.append(user_auto_query)

            # Build auto content query for community content
            if include_community_auto and user_id:
                community_auto_query = session.query(
                    ContentItemAuto.id.label('id'),
                    ContentItemAuto.title.label('title'),
                    ContentItemAuto.content_type.label('content_type'),
                    ContentItemAuto.content_data.label('content_data'),
                    ContentItemAuto.path_thumb.label('path_thumb'),
                    ContentItemAuto.path_thumbs_alt_res.label('path_thumbs_alt_res'),
                    ContentItemAuto.prompt.label('prompt'),
                    ContentItemAuto.creator_id.label('creator_id'),
                    ContentItemAuto.item_metadata.label('item_metadata'),
                    ContentItemAuto.is_private.label('is_private'),
                    ContentItemAuto.quality_score.label('quality_score'),
                    ContentItemAuto.created_at.label('created_at'),
                    ContentItemAuto.updated_at.label('updated_at'),
                    literal('auto').label('source_type'),
                    User.username.label('creator_username')
                ).join(User, ContentItemAuto.creator).filter(ContentItemAuto.creator_id != user_id)

                if search_term:
                    community_auto_query = self._apply_enhanced_search_filter(community_auto_query, ContentItemAuto, search_term)
                if not use_python_tag_filter:
                    community_auto_query = self._apply_tag_filter_via_junction(
                        community_auto_query,
                        ContentItemAuto,
                        'auto',
                        tag_uuids,
                        tag_match_normalized,
                    )

                queries.append(community_auto_query)

        # LEGACY APPROACH: Use content_types and creator_filter
        else:
            if content_types is None:
                content_types = ["regular", "auto"]

            # Regular content query
            if "regular" in content_types:
                regular_query = session.query(
                    ContentItem.id.label('id'),
                    ContentItem.title.label('title'),
                    ContentItem.content_type.label('content_type'),
                    ContentItem.content_data.label('content_data'),
                    ContentItem.path_thumb.label('path_thumb'),
                    ContentItem.path_thumbs_alt_res.label('path_thumbs_alt_res'),
                    ContentItem.prompt.label('prompt'),
                    ContentItem.creator_id.label('creator_id'),
                    ContentItem.item_metadata.label('item_metadata'),
                    ContentItem.is_private.label('is_private'),
                    ContentItem.quality_score.label('quality_score'),
                    ContentItem.created_at.label('created_at'),
                    ContentItem.updated_at.label('updated_at'),
                    literal('regular').label('source_type'),
                    User.username.label('creator_username')
                ).join(User, ContentItem.creator)

                # Apply filters
                if creator_filter == "user" and user_id:
                    regular_query = regular_query.filter(ContentItem.creator_id == user_id)
                elif creator_filter == "community" and user_id:
                    regular_query = regular_query.filter(ContentItem.creator_id != user_id)

                if search_term:
                    regular_query = self._apply_enhanced_search_filter(regular_query, ContentItem, search_term)

                # Apply tag filtering - match if content has at least 1 of the specified tags
                if not use_python_tag_filter:
                    regular_query = self._apply_tag_filter_via_junction(
                        regular_query,
                        ContentItem,
                        'regular',
                        tag_uuids,
                        tag_match_normalized,
                    )

                queries.append(regular_query)

            # Auto content query
            if "auto" in content_types:
                auto_query = session.query(
                    ContentItemAuto.id.label('id'),
                    ContentItemAuto.title.label('title'),
                    ContentItemAuto.content_type.label('content_type'),
                    ContentItemAuto.content_data.label('content_data'),
                    ContentItemAuto.path_thumb.label('path_thumb'),
                    ContentItemAuto.path_thumbs_alt_res.label('path_thumbs_alt_res'),
                    ContentItemAuto.prompt.label('prompt'),
                    ContentItemAuto.creator_id.label('creator_id'),
                    ContentItemAuto.item_metadata.label('item_metadata'),
                    ContentItemAuto.is_private.label('is_private'),
                    ContentItemAuto.quality_score.label('quality_score'),
                    ContentItemAuto.created_at.label('created_at'),
                    ContentItemAuto.updated_at.label('updated_at'),
                    literal('auto').label('source_type'),
                    User.username.label('creator_username')
                ).join(User, ContentItemAuto.creator)

                # Apply filters
                if creator_filter == "user" and user_id:
                    auto_query = auto_query.filter(ContentItemAuto.creator_id == user_id)
                elif creator_filter == "community" and user_id:
                    auto_query = auto_query.filter(ContentItemAuto.creator_id != user_id)

                if search_term:
                    auto_query = self._apply_enhanced_search_filter(auto_query, ContentItemAuto, search_term)

                # Apply tag filtering - match if content has at least 1 of the specified tags
                if not use_python_tag_filter:
                    auto_query = self._apply_tag_filter_via_junction(
                        auto_query,
                        ContentItemAuto,
                        'auto',
                        tag_uuids,
                        tag_match_normalized,
                    )

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
        # Quick optimization: Skip expensive count for tag-filtered junction table queries on PostgreSQL
        # For SQLite (tests), always compute accurate count
        is_sqlite = session.bind and session.bind.dialect.name != "postgresql"
        if use_junction_table_filter and tag_uuids and not is_sqlite:
            # Return a high estimate instead of accurate count to avoid timeout on large PostgreSQL datasets
            # This is acceptable for pagination UX - users rarely go beyond first few pages
            total_count = 999999  # High estimate to indicate "many results"
        else:
            try:
                # Count from the original union query (before sorting)
                original_union = queries[0] if len(queries) == 1 else queries[0].union_all(*queries[1:])
                count_subquery = original_union.subquery()
                total_count = session.query(func.count()).select_from(count_subquery).scalar() or 0
            except Exception:
                # Fallback: calculate count separately for each table
                total_count = 0

            # When using content_source_types, derive what to count from the parsed flags
            if content_source_types is not None:
                # NEW APPROACH: Count based on content_source_types
                if include_user_regular or include_community_regular:
                    regular_count_query = session.query(func.count(ContentItem.id))
                    if include_user_regular and not include_community_regular and user_id:
                        regular_count_query = regular_count_query.filter(ContentItem.creator_id == user_id)
                    elif include_community_regular and not include_user_regular and user_id:
                        regular_count_query = regular_count_query.filter(ContentItem.creator_id != user_id)
                    if search_term:
                        regular_count_query = regular_count_query.filter(ContentItem.title.ilike(f"%{search_term}%"))
                    total_count += regular_count_query.scalar() or 0

                if include_user_auto or include_community_auto:
                    auto_count_query = session.query(func.count(ContentItemAuto.id))
                    if include_user_auto and not include_community_auto and user_id:
                        auto_count_query = auto_count_query.filter(ContentItemAuto.creator_id == user_id)
                    elif include_community_auto and not include_user_auto and user_id:
                        auto_count_query = auto_count_query.filter(ContentItemAuto.creator_id != user_id)
                    if search_term:
                        auto_count_query = auto_count_query.filter(ContentItemAuto.title.ilike(f"%{search_term}%"))
                    total_count += auto_count_query.scalar() or 0
            else:
                # LEGACY APPROACH: Use content_types
                if content_types and "regular" in content_types:
                    regular_count_query = session.query(func.count(ContentItem.id))
                    if creator_filter == "user" and user_id:
                        regular_count_query = regular_count_query.filter(ContentItem.creator_id == user_id)
                    elif creator_filter == "community" and user_id:
                        regular_count_query = regular_count_query.filter(ContentItem.creator_id != user_id)
                    if search_term:
                        regular_count_query = regular_count_query.filter(ContentItem.title.ilike(f"%{search_term}%"))
                    total_count += regular_count_query.scalar() or 0

                if content_types and "auto" in content_types:
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
        paginated_query = unified_query
        if not use_python_tag_filter:
            paginated_query = unified_query.offset(offset).limit(pagination.page_size)

        # Execute query
        results = paginated_query.all()

        # Convert results to dictionaries
        items = []
        for row in results:
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

        if use_python_tag_filter:
            filtered_items = [
                item
                for item in items
                if self._matches_tag_logic(item.get("tags"), normalized_tags, tag_match_normalized)
            ]
            total_count = len(filtered_items)
            total_pages = (total_count + pagination.page_size - 1) // pagination.page_size if pagination.page_size else 0
            start = offset
            end = offset + pagination.page_size
            items = filtered_items[start:end]
            has_next = pagination.page < total_pages
            has_previous = pagination.page > 1 and total_pages > 0
        else:
            # If we used the 999999 estimate but got no results, correct the count
            if total_count == 999999 and len(items) == 0 and pagination.page == 1:
                total_count = 0
            total_pages = (total_count + pagination.page_size - 1) // pagination.page_size if pagination.page_size else 0
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
