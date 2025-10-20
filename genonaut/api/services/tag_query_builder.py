"""Tag filtering query builder with adaptive strategies.

Implements multiple query strategies for multi-tag content filtering:
- Self-join: For small K (K ≤ 3)
- Group/HAVING: For medium K with selective tags
- Two-phase rarest-first: For large K or common tags
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, literal_column
from sqlalchemy.orm import Query, Session, aliased

from genonaut.db.schema import ContentTag, ContentItemAll
from genonaut.api.services.tag_query_planner import (
    TagFilterStrategy,
    TagQueryPlanner,
    StrategyChoice
)


logger = logging.getLogger(__name__)


class TagQueryBuilder:
    """Builds optimized tag filtering queries based on strategy selection."""

    def __init__(self, session: Session, planner: TagQueryPlanner):
        """Initialize query builder.

        Args:
            session: SQLAlchemy session
            planner: Tag query planner for strategy selection
        """
        self.session = session
        self.planner = planner

    def apply_tag_filter(
        self,
        query: Query,
        content_model,
        tag_uuids: List[UUID],
        content_sources: List[str],
        tag_match: str = "all"
    ) -> Query:
        """Apply tag filtering with adaptive strategy selection.

        Args:
            query: Base SQLAlchemy query to filter
            content_model: ContentItemAll or specific content model
            tag_uuids: List of tag UUIDs to filter by
            content_sources: List of content source types ('regular', 'auto')
            tag_match: 'any' or 'all' (currently only 'all' uses adaptive strategies)

        Returns:
            Filtered query
        """
        if not tag_uuids:
            return query

        # Normalize and deduplicate tags
        unique_tags = list(dict.fromkeys(tag_uuids))

        # For "any" matching, use simple IN clause (existing behavior)
        if (tag_match or "any").lower() == "any":
            return self._apply_any_match(query, content_model, unique_tags, content_sources)

        # For "all" matching, use adaptive strategy
        return self._apply_all_match_adaptive(query, content_model, unique_tags, content_sources)

    def _apply_any_match(
        self,
        query: Query,
        content_model,
        tag_uuids: List[UUID],
        content_sources: List[str]
    ) -> Query:
        """Apply 'any' tag matching (OR logic) - content must have at least one tag.

        Uses simple EXISTS with IN clause (existing implementation).

        Args:
            query: Base query
            content_model: Content model class
            tag_uuids: Tag UUIDs to match
            content_sources: Content source types

        Returns:
            Filtered query
        """
        # Build EXISTS subquery
        subq = self.session.query(ContentTag.content_id).filter(
            ContentTag.content_id == content_model.id,
            ContentTag.tag_id.in_(tag_uuids)
        )

        # Add content_source filter if not using ContentItemAll
        if content_sources and hasattr(content_model, 'source_type'):
            # ContentItemAll has source_type, filter by that
            pass  # Already filtered in main query
        elif content_sources:
            # For specific tables, filter content_tags by content_source
            subq = subq.filter(ContentTag.content_source.in_(content_sources))

        exists_clause = subq.exists()
        return query.filter(exists_clause)

    def _apply_all_match_adaptive(
        self,
        query: Query,
        content_model,
        tag_uuids: List[UUID],
        content_sources: List[str]
    ) -> Query:
        """Apply 'all' tag matching with adaptive strategy selection.

        Args:
            query: Base query
            content_model: Content model class
            tag_uuids: Tag UUIDs to match (all must be present)
            content_sources: Content source types

        Returns:
            Filtered query
        """
        # Select strategy based on tag cardinalities
        choice = self.planner.pick_strategy(tag_uuids, content_sources)

        # Log strategy choice
        self.planner.log_strategy_choice(choice, tag_uuids)

        # Apply chosen strategy
        if choice.strategy == TagFilterStrategy.SELF_JOIN:
            return self._build_self_join_query(query, content_model, tag_uuids, content_sources)
        elif choice.strategy == TagFilterStrategy.GROUP_HAVING:
            return self._build_group_having_query(query, content_model, tag_uuids, content_sources)
        elif choice.strategy == TagFilterStrategy.TWO_PHASE_SINGLE:
            return self._build_two_phase_query(query, content_model, tag_uuids, content_sources, dual_seed=False)
        elif choice.strategy == TagFilterStrategy.TWO_PHASE_DUAL:
            return self._build_two_phase_query(query, content_model, tag_uuids, content_sources, dual_seed=True)
        else:
            # Fallback to group/having
            logger.warning(f"Unknown strategy {choice.strategy}, falling back to GROUP/HAVING")
            return self._build_group_having_query(query, content_model, tag_uuids, content_sources)

    def _build_self_join_query(
        self,
        query: Query,
        content_model,
        tag_uuids: List[UUID],
        content_sources: List[str]
    ) -> Query:
        """Build self-join query for small K (K ≤ 3).

        Uses separate EXISTS clauses for each tag.

        Args:
            query: Base query
            content_model: Content model class
            tag_uuids: Tag UUIDs (K ≤ 3)
            content_sources: Content source types

        Returns:
            Filtered query
        """
        for tag_id in tag_uuids:
            subq = self.session.query(ContentTag.content_id).filter(
                ContentTag.content_id == content_model.id,
                ContentTag.tag_id == tag_id
            )

            # Add content_source filter if applicable
            if content_sources and not hasattr(content_model, 'source_type'):
                subq = subq.filter(ContentTag.content_source.in_(content_sources))

            exists_clause = subq.exists()
            query = query.filter(exists_clause)

        return query

    def _build_group_having_query(
        self,
        query: Query,
        content_model,
        tag_uuids: List[UUID],
        content_sources: List[str]
    ) -> Query:
        """Build GROUP/HAVING query for medium K.

        Filters content_tags by tag list, groups by content_id, and uses HAVING to ensure
        all tags are present.

        Args:
            query: Base query
            content_model: Content model class
            tag_uuids: Tag UUIDs
            content_sources: Content source types

        Returns:
            Filtered query
        """
        # Build subquery: content IDs that have all required tags
        matched_subq = (
            self.session.query(ContentTag.content_id)
            .filter(ContentTag.tag_id.in_(tag_uuids))
        )

        # Add content_source filter if applicable
        if content_sources and not hasattr(content_model, 'source_type'):
            matched_subq = matched_subq.filter(ContentTag.content_source.in_(content_sources))

        # Group by content_id and require all tags present
        matched_subq = (
            matched_subq
            .group_by(ContentTag.content_id)
            .having(func.count(func.distinct(ContentTag.tag_id)) == len(tag_uuids))
        )

        # Apply as subquery filter
        return query.filter(content_model.id.in_(matched_subq))

    def _build_two_phase_query(
        self,
        query: Query,
        content_model,
        tag_uuids: List[UUID],
        content_sources: List[str],
        dual_seed: bool = False
    ) -> Query:
        """Build two-phase rarest-first query.

        Phase 1: Get candidates with rarest tag(s)
        Phase 2: Filter candidates to those with all tags

        Args:
            query: Base query
            content_model: Content model class
            tag_uuids: Tag UUIDs
            content_sources: Content source types
            dual_seed: If True, seed with two rarest tags; if False, seed with one

        Returns:
            Filtered query
        """
        # Get cardinalities to identify rarest tags
        cardinalities = self.planner.tag_repo.get_tags_cardinality_batch(
            tag_uuids,
            content_sources,
            default=self.planner.fallback_default_count
        )

        # Sum cardinalities across content sources for each tag
        tag_totals = {}
        for tag_id in tag_uuids:
            tag_totals[tag_id] = sum(
                cardinalities.get((tag_id, source), self.planner.fallback_default_count)
                for source in content_sources
            )

        # Sort tags by cardinality (rarest first)
        sorted_tags = sorted(tag_totals.items(), key=lambda x: x[1])

        # Get seed tag(s)
        if dual_seed and len(sorted_tags) >= 2:
            seed_tags = [sorted_tags[0][0], sorted_tags[1][0]]
        else:
            seed_tags = [sorted_tags[0][0]]

        # Phase 1: Get candidates with seed tag(s)
        seed_subq = (
            self.session.query(ContentTag.content_id)
            .filter(ContentTag.tag_id.in_(seed_tags))
        )

        if content_sources and not hasattr(content_model, 'source_type'):
            seed_subq = seed_subq.filter(ContentTag.content_source.in_(content_sources))

        if dual_seed:
            # For dual seed, require both seed tags
            seed_subq = (
                seed_subq
                .group_by(ContentTag.content_id)
                .having(func.count(func.distinct(ContentTag.tag_id)) == len(seed_tags))
            )

        # Phase 2: From candidates, filter to those with all tags
        matched_subq = (
            self.session.query(ContentTag.content_id)
            .filter(
                ContentTag.content_id.in_(seed_subq),
                ContentTag.tag_id.in_(tag_uuids)
            )
        )

        if content_sources and not hasattr(content_model, 'source_type'):
            matched_subq = matched_subq.filter(ContentTag.content_source.in_(content_sources))

        matched_subq = (
            matched_subq
            .group_by(ContentTag.content_id)
            .having(func.count(func.distinct(ContentTag.tag_id)) == len(tag_uuids))
        )

        # Apply as filter
        return query.filter(content_model.id.in_(matched_subq))
