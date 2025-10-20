"""Tag filtering query strategy planner.

Implements adaptive query strategy selection for multi-tag content filtering
based on tag cardinality statistics and configuration thresholds.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple
from uuid import UUID

from genonaut.api.config import get_settings
from genonaut.api.repositories.tag_repository import TagRepository


logger = logging.getLogger(__name__)


class TagFilterStrategy(str, Enum):
    """Available query strategies for tag filtering."""

    SELF_JOIN = "self_join"
    GROUP_HAVING = "group_having"
    TWO_PHASE_SINGLE = "two_phase_single"
    TWO_PHASE_DUAL = "two_phase_dual"


@dataclass
class StrategyChoice:
    """Result of strategy selection with metadata."""

    strategy: TagFilterStrategy
    k: int  # Number of tags
    rarest_count: int  # Cardinality of rarest tag
    estimated_candidates: int  # Estimated intermediate result size
    reason: str  # Explanation of why this strategy was chosen


class TagQueryPlanner:
    """Selects optimal query strategy for multi-tag content filtering.

    Uses tag cardinality statistics and configuration thresholds to choose
    between self-join, group/having, and two-phase rarest-first strategies.
    """

    def __init__(self, tag_repo: TagRepository, config: Dict = None):
        """Initialize planner with tag repository and configuration.

        Args:
            tag_repo: Repository for accessing tag cardinality stats
            config: Optional configuration dict (uses get_settings() if None)
        """
        self.tag_repo = tag_repo

        # Load configuration
        if config is None:
            settings = get_settings()
            config = settings.performance.get("query_planner_tag_prejoin", {}) if settings.performance else {}

        self.small_k_threshold = config.get("small_k_threshold", 3)
        self.group_having_rarest_ceiling = config.get("group_having_rarest_ceiling", 50000)
        self.two_phase_min_k_for_dual_seed = config.get("two_phase_min_k_for_dual_seed", 7)
        self.two_phase_dual_seed_floor = config.get("two_phase_dual_seed_floor", 150000)
        self.seed_candidate_cap = config.get("seed_candidate_cap", 50000)
        self.enable_two_phase = config.get("enable_two_phase", True)
        self.enable_group_having = config.get("enable_group_having", True)
        self.enable_self_join = config.get("enable_self_join", True)

        # Stats configuration
        stats_config = config.get("stats", {})
        self.fallback_default_count = stats_config.get("fallback_default_count", 1000000)

        # Telemetry configuration
        telemetry_config = config.get("telemetry", {})
        self.log_strategy_choice = telemetry_config.get("log_strategy_choice", True)
        self.log_estimates = telemetry_config.get("log_estimates", True)

    def pick_strategy(
        self,
        tag_ids: List[UUID],
        content_sources: List[str]
    ) -> StrategyChoice:
        """Select optimal query strategy for given tags and content sources.

        Args:
            tag_ids: List of tag UUIDs to filter by
            content_sources: List of content source types ('regular', 'auto')

        Returns:
            StrategyChoice with selected strategy and metadata
        """
        k = len(tag_ids)

        # Get cardinality stats for all tag-source combinations
        cardinalities = self.tag_repo.get_tags_cardinality_batch(
            tag_ids,
            content_sources,
            default=self.fallback_default_count
        )

        # Sum cardinalities across content sources for each tag
        tag_totals: Dict[UUID, int] = {}
        for tag_id in tag_ids:
            tag_totals[tag_id] = sum(
                cardinalities.get((tag_id, source), self.fallback_default_count)
                for source in content_sources
            )

        # Sort tags by cardinality (rarest first)
        sorted_tags = sorted(tag_totals.items(), key=lambda x: x[1])
        rarest_tag_id, rarest_count = sorted_tags[0] if sorted_tags else (None, self.fallback_default_count)

        # Strategy selection logic

        # 1. Small K: Use self-join for K <= threshold
        if k <= self.small_k_threshold and self.enable_self_join:
            return StrategyChoice(
                strategy=TagFilterStrategy.SELF_JOIN,
                k=k,
                rarest_count=rarest_count,
                estimated_candidates=rarest_count,
                reason=f"K={k} <= small_k_threshold={self.small_k_threshold}"
            )

        # 2. Selective rarest tag: Use group/having if rarest is already selective
        if rarest_count <= self.group_having_rarest_ceiling and self.enable_group_having:
            # Estimate: rarest tag gives us candidates, then we filter with HAVING
            estimated_candidates = rarest_count
            return StrategyChoice(
                strategy=TagFilterStrategy.GROUP_HAVING,
                k=k,
                rarest_count=rarest_count,
                estimated_candidates=estimated_candidates,
                reason=f"rarest_count={rarest_count} <= group_having_ceiling={self.group_having_rarest_ceiling}"
            )

        # 3. Two-phase strategy: Use rarest tag(s) to seed, then filter
        if self.enable_two_phase:
            # Check if we should use dual-seed (two rarest tags)
            if (k >= self.two_phase_min_k_for_dual_seed and
                rarest_count > self.two_phase_dual_seed_floor):

                # Get second rarest count
                second_rarest_count = sorted_tags[1][1] if len(sorted_tags) > 1 else rarest_count

                # Estimate seed size as intersection of two rarest
                # Rough heuristic: (count1 * count2) / total_items
                # For simplicity, use min(count1, count2) * 0.5
                estimated_candidates = min(rarest_count, second_rarest_count) // 2

                # Cap the seed size
                if estimated_candidates <= self.seed_candidate_cap:
                    return StrategyChoice(
                        strategy=TagFilterStrategy.TWO_PHASE_DUAL,
                        k=k,
                        rarest_count=rarest_count,
                        estimated_candidates=estimated_candidates,
                        reason=f"K={k} >= dual_seed_min_k={self.two_phase_min_k_for_dual_seed}, "
                               f"rarest={rarest_count} > dual_seed_floor={self.two_phase_dual_seed_floor}"
                    )

            # Single-seed two-phase
            estimated_candidates = rarest_count
            if estimated_candidates <= self.seed_candidate_cap:
                return StrategyChoice(
                    strategy=TagFilterStrategy.TWO_PHASE_SINGLE,
                    k=k,
                    rarest_count=rarest_count,
                    estimated_candidates=estimated_candidates,
                    reason=f"Two-phase single seed, rarest_count={rarest_count}"
                )

        # Fallback: Use group/having even if above ceiling
        if self.log_strategy_choice:
            logger.warning(
                f"No optimal strategy found for K={k}, rarest={rarest_count}. "
                f"Falling back to GROUP/HAVING."
            )

        return StrategyChoice(
            strategy=TagFilterStrategy.GROUP_HAVING,
            k=k,
            rarest_count=rarest_count,
            estimated_candidates=rarest_count,
            reason=f"Fallback to GROUP/HAVING (K={k}, rarest={rarest_count})"
        )

    def log_strategy_choice(self, choice: StrategyChoice, tag_ids: List[UUID]) -> None:
        """Log strategy selection for telemetry.

        Args:
            choice: Selected strategy choice
            tag_ids: Tag IDs being filtered
        """
        if not self.log_strategy_choice:
            return

        logger.info(
            f"Tag filter strategy selected: {choice.strategy.value} | "
            f"K={choice.k} | rarest_count={choice.rarest_count} | "
            f"estimated_candidates={choice.estimated_candidates} | "
            f"reason={choice.reason} | "
            f"tags={[str(tid) for tid in tag_ids[:3]]}{'...' if len(tag_ids) > 3 else ''}"
        )
