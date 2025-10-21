"""
Query execution strategies for unified content queries.

This module implements the Strategy Pattern to allow switching between different
query execution approaches (ORM vs Raw SQL) for performance optimization.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import text, or_, and_
from sqlalchemy.orm import Session

from genonaut.db.schema import ContentItemAll, ContentTag, User
from genonaut.api.models.requests import PaginationRequest


class QueryStrategy(Enum):
    """Strategy for executing unified content queries."""
    ORM = "orm"
    RAW_SQL = "raw_sql"


class ContentQueryExecutor(ABC):
    """Abstract base class for query execution strategies."""

    @abstractmethod
    def execute_query(
        self,
        session: Session,
        pagination: PaginationRequest,
        content_source_types: List[str],
        user_id: Optional[UUID],
        tag_uuids: List[UUID],
        tag_match: str,
        search_term: Optional[str],
        sort_field: str,
        sort_order: str,
    ) -> Tuple[List[Any], int]:
        """
        Execute the unified content query.

        Args:
            session: SQLAlchemy session
            pagination: Pagination parameters
            content_source_types: List of content source types (e.g., ['user-regular', 'community-auto'])
            user_id: Optional user ID for creator filtering
            tag_uuids: List of tag UUIDs to filter by
            tag_match: Tag matching logic ("any" or "all")
            search_term: Optional search term
            sort_field: Field to sort by
            sort_order: Sort order ("asc" or "desc")

        Returns:
            Tuple of (items, total_count)
        """
        pass


class ORMQueryExecutor(ContentQueryExecutor):
    """
    SQLAlchemy ORM-based query executor.

    This is the original implementation using SQLAlchemy's ORM layer.
    Slower due to ORM overhead, especially with EXISTS subqueries.
    """

    def execute_query(
        self,
        session: Session,
        pagination: PaginationRequest,
        content_source_types: List[str],
        user_id: Optional[UUID],
        tag_uuids: List[UUID],
        tag_match: str,
        search_term: Optional[str],
        sort_field: str,
        sort_order: str,
    ) -> Tuple[List[Any], int]:
        """Execute query using SQLAlchemy ORM."""

        # Map content_source_types to source_type values and build creator filters
        source_type_filters = []
        creator_filters = []  # List of (source_type, condition) tuples

        for cst in content_source_types:
            if cst == 'user-regular':
                if user_id:
                    creator_filters.append(('items', ContentItemAll.creator_id == user_id))
                    source_type_filters.append('items')
            elif cst == 'user-auto':
                if user_id:
                    creator_filters.append(('auto', ContentItemAll.creator_id == user_id))
                    source_type_filters.append('auto')
            elif cst == 'community-regular':
                if user_id:
                    creator_filters.append(('items', ContentItemAll.creator_id != user_id))
                    source_type_filters.append('items')
            elif cst == 'community-auto':
                if user_id:
                    creator_filters.append(('auto', ContentItemAll.creator_id != user_id))
                    source_type_filters.append('auto')

        # Extract unique source_types
        source_type_filters = list(set(source_type_filters))

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
            ContentItemAll.source_type,
            User.username.label('creator_username')
        ).join(User, ContentItemAll.creator_id == User.id)

        # Apply partition pruning filter
        query = query.filter(ContentItemAll.source_type.in_(source_type_filters))

        # Apply creator filters
        if creator_filters:
            creator_conditions = []
            for source_type, condition in creator_filters:
                creator_conditions.append(and_(ContentItemAll.source_type == source_type, condition))
            if creator_conditions:
                query = query.filter(or_(*creator_conditions))

        # Apply search filter
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

        # Apply tag filtering via junction table
        tag_match_normalized = (tag_match or "any").lower()
        if tag_match_normalized not in {"any", "all"}:
            tag_match_normalized = "any"

        if tag_uuids:
            unique_tags = list(dict.fromkeys(tag_uuids))

            if tag_match_normalized == "all":
                # For "all" matching: content must have ALL specified tags
                for tag_id in unique_tags:
                    exists_clause = session.query(ContentTag.content_id).filter(
                        ContentTag.content_id == ContentItemAll.id,
                        ContentTag.content_source == ContentItemAll.source_type,
                        ContentTag.tag_id == tag_id
                    ).exists()
                    query = query.filter(exists_clause)
            else:
                # For "any" matching: content must have AT LEAST ONE of the specified tags
                exists_clause = session.query(ContentTag.content_id).filter(
                    ContentTag.content_id == ContentItemAll.id,
                    ContentTag.content_source == ContentItemAll.source_type,
                    ContentTag.tag_id.in_(unique_tags)
                ).exists()
                query = query.filter(exists_clause)

        # Count total before pagination
        total_count = query.count()

        # Apply sorting
        sort_column = getattr(ContentItemAll, sort_field, ContentItemAll.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc(), ContentItemAll.id.asc())
        else:
            query = query.order_by(sort_column.desc(), ContentItemAll.id.desc())

        # Apply pagination
        if pagination.page_size:
            query = query.limit(pagination.page_size)
        if pagination.page and pagination.page_size:
            offset = (pagination.page - 1) * pagination.page_size
            query = query.offset(offset)

        items = query.all()

        return items, total_count


class RawSQLQueryExecutor(ContentQueryExecutor):
    """
    Raw SQL query executor for maximum performance.

    Bypasses SQLAlchemy ORM overhead by executing SQL directly.
    ~140x faster than ORM for complex queries with EXISTS subqueries.
    """

    def execute_query(
        self,
        session: Session,
        pagination: PaginationRequest,
        content_source_types: List[str],
        user_id: Optional[UUID],
        tag_uuids: List[UUID],
        tag_match: str,
        search_term: Optional[str],
        sort_field: str,
        sort_order: str,
    ) -> Tuple[List[Any], int]:
        """Execute query using raw SQL."""

        # Build WHERE conditions
        conditions = []
        params = {}

        # Map content_source_types to source_type values and build creator filters
        # The creator filter logic combines source_type and creator_id checks in OR clauses
        creator_conditions = []

        for cst in content_source_types:
            if cst == 'user-regular':
                if user_id:
                    creator_conditions.append(f"(content_items_all.source_type = 'items' AND content_items_all.creator_id = :user_id)")
            elif cst == 'user-auto':
                if user_id:
                    creator_conditions.append(f"(content_items_all.source_type = 'auto' AND content_items_all.creator_id = :user_id)")
            elif cst == 'community-regular':
                if user_id:
                    creator_conditions.append(f"(content_items_all.source_type = 'items' AND content_items_all.creator_id != :user_id)")
            elif cst == 'community-auto':
                if user_id:
                    creator_conditions.append(f"(content_items_all.source_type = 'auto' AND content_items_all.creator_id != :user_id)")

        # Add user_id param once (used by all conditions)
        if user_id:
            params["user_id"] = str(user_id)

        # Creator filters (complex OR conditions)
        if creator_conditions:
            conditions.append(f"({' OR '.join(creator_conditions)})")

        # Search term filter
        if search_term:
            from genonaut.api.services.search_parser import parse_search_query
            parsed = parse_search_query(search_term)
            search_conditions = []

            for idx, phrase in enumerate(parsed.phrases):
                if phrase:
                    search_conditions.append(
                        f"(content_items_all.title ILIKE :search_phrase_{idx} OR content_items_all.prompt ILIKE :search_phrase_{idx})"
                    )
                    params[f"search_phrase_{idx}"] = f"%{phrase}%"

            for idx, word in enumerate(parsed.words):
                if word:
                    search_conditions.append(
                        f"(content_items_all.title ILIKE :search_word_{idx} OR content_items_all.prompt ILIKE :search_word_{idx})"
                    )
                    params[f"search_word_{idx}"] = f"%{word}%"

            if search_conditions:
                conditions.append(f"({' AND '.join(search_conditions)})")

        # Tag filtering
        tag_match_normalized = (tag_match or "any").lower()
        if tag_match_normalized not in {"any", "all"}:
            tag_match_normalized = "any"

        if tag_uuids:
            unique_tags = list(dict.fromkeys(tag_uuids))

            if tag_match_normalized == "all":
                # For "all": content must have ALL tags
                for idx, tag_id in enumerate(unique_tags):
                    conditions.append(f"""
                        EXISTS (
                            SELECT 1 FROM content_tags
                            WHERE content_tags.content_id = content_items_all.id
                            AND content_tags.content_source = content_items_all.source_type
                            AND content_tags.tag_id = :tag_all_{idx}
                        )
                    """)
                    params[f"tag_all_{idx}"] = str(tag_id)
            else:
                # For "any": content must have AT LEAST ONE tag
                tag_placeholders = ', '.join([f":tag_any_{i}" for i in range(len(unique_tags))])
                conditions.append(f"""
                    EXISTS (
                        SELECT 1 FROM content_tags
                        WHERE content_tags.content_id = content_items_all.id
                        AND content_tags.content_source = content_items_all.source_type
                        AND content_tags.tag_id IN ({tag_placeholders})
                    )
                """)
                for idx, tag_id in enumerate(unique_tags):
                    params[f"tag_any_{idx}"] = str(tag_id)

        # Build WHERE clause
        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Build ORDER BY clause
        sort_direction = "DESC" if sort_order == "desc" else "ASC"
        order_by = f"content_items_all.{sort_field} {sort_direction}, content_items_all.id {sort_direction}"

        # Count query - skip for tag-filtered queries as it's slow
        # TODO: Implement efficient tag count via pre-computed stats or cursor pagination
        if tag_uuids:
            # Skip expensive COUNT for tag queries - return -1 to indicate unknown
            total_count = -1
        else:
            count_sql = f"""
                SELECT COUNT(*)
                FROM content_items_all
                WHERE {where_clause}
            """

            count_result = session.execute(text(count_sql), params).scalar()
            total_count = count_result or 0

        # Main query with pagination
        limit_clause = f"LIMIT :page_size" if pagination.page_size else ""
        offset_value = 0
        if pagination.page and pagination.page_size:
            offset_value = (pagination.page - 1) * pagination.page_size
        offset_clause = f"OFFSET :offset" if offset_value > 0 else ""

        params['page_size'] = pagination.page_size or 1000000
        params['offset'] = offset_value

        main_sql = f"""
            SELECT
                content_items_all.id,
                content_items_all.title,
                content_items_all.content_type,
                content_items_all.content_data,
                content_items_all.path_thumb,
                content_items_all.path_thumbs_alt_res,
                content_items_all.prompt,
                content_items_all.creator_id,
                content_items_all.item_metadata,
                content_items_all.is_private,
                content_items_all.quality_score,
                content_items_all.created_at,
                content_items_all.updated_at,
                content_items_all.source_type,
                users.username as creator_username
            FROM content_items_all
            JOIN users ON users.id = content_items_all.creator_id
            WHERE {where_clause}
            ORDER BY {order_by}
            {limit_clause} {offset_clause}
        """

        result = session.execute(text(main_sql), params)
        items = result.fetchall()

        return items, total_count
