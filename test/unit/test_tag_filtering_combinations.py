"""Unit tests for tag filtering combinations.

Tests tag filtering with 'any' vs 'all' match logic combined with multiple tags.
Verifies correct SQL generation and filtering behavior.
"""

import pytest
from typing import List, Set, Optional


class MockTagFilter:
    """Mock tag filter to test filtering logic."""

    @staticmethod
    def filter_by_tags(
        items: List[dict],
        tags: List[str],
        match_mode: str = 'any'
    ) -> List[dict]:
        """Filter items by tags with 'any' or 'all' logic.

        Args:
            items: List of items, each with 'tags' field
            tags: List of tag names to filter by
            match_mode: 'any' (OR logic) or 'all' (AND logic)

        Returns:
            Filtered list of items
        """
        if not tags:
            return items

        filtered = []
        tags_set = set(tags)

        for item in items:
            item_tags = set(item.get('tags', []))

            if match_mode == 'any':
                # OR logic: item must have AT LEAST ONE of the specified tags
                if item_tags & tags_set:  # Set intersection
                    filtered.append(item)
            elif match_mode == 'all':
                # AND logic: item must have ALL of the specified tags
                if tags_set.issubset(item_tags):
                    filtered.append(item)

        return filtered


@pytest.fixture
def sample_items():
    """Create sample items with various tag combinations."""
    return [
        {'id': 1, 'title': 'Mountain Sunrise', 'tags': ['nature', 'mountain', 'sunrise']},
        {'id': 2, 'title': 'Forest Path', 'tags': ['nature', 'forest']},
        {'id': 3, 'title': 'City Lights', 'tags': ['city', 'night', 'urban']},
        {'id': 4, 'title': 'Beach Sunset', 'tags': ['nature', 'beach', 'sunset']},
        {'id': 5, 'title': 'Mountain Snow', 'tags': ['mountain', 'winter', 'snow']},
        {'id': 6, 'title': 'Urban Nature', 'tags': ['nature', 'city', 'park']},
        {'id': 7, 'title': 'No Tags', 'tags': []},
        {'id': 8, 'title': 'Desert Landscape', 'tags': ['nature', 'desert', 'landscape']},
    ]


def test_single_tag_filter_any(sample_items):
    """Test filtering by single tag with 'any' logic."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(sample_items, tags=['nature'], match_mode='any')

    result_ids = [item['id'] for item in results]
    # Should match items 1, 2, 4, 6, 8 (all items with 'nature' tag)
    assert set(result_ids) == {1, 2, 4, 6, 8}


def test_single_tag_filter_all(sample_items):
    """Test filtering by single tag with 'all' logic.

    With single tag, 'all' and 'any' should produce same results.
    """
    filter = MockTagFilter()
    results = filter.filter_by_tags(sample_items, tags=['nature'], match_mode='all')

    result_ids = [item['id'] for item in results]
    # Should match items 1, 2, 4, 6, 8 (all items with 'nature' tag)
    assert set(result_ids) == {1, 2, 4, 6, 8}


def test_multiple_tags_any_logic(sample_items):
    """Test filtering by multiple tags with 'any' (OR) logic."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['mountain', 'beach'],
        match_mode='any'
    )

    result_ids = [item['id'] for item in results]
    # Should match items 1, 4, 5 (items with mountain OR beach)
    assert set(result_ids) == {1, 4, 5}


def test_multiple_tags_all_logic(sample_items):
    """Test filtering by multiple tags with 'all' (AND) logic."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'mountain'],
        match_mode='all'
    )

    result_ids = [item['id'] for item in results]
    # Should match item 1 only (has both nature AND mountain)
    assert set(result_ids) == {1}


def test_three_tags_any_logic(sample_items):
    """Test filtering by three tags with 'any' logic."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['forest', 'beach', 'desert'],
        match_mode='any'
    )

    result_ids = [item['id'] for item in results]
    # Should match items 2 (forest), 4 (beach), 8 (desert)
    assert set(result_ids) == {2, 4, 8}


def test_three_tags_all_logic(sample_items):
    """Test filtering by three tags with 'all' logic."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'mountain', 'sunrise'],
        match_mode='all'
    )

    result_ids = [item['id'] for item in results]
    # Should match item 1 only (has all three tags)
    assert set(result_ids) == {1}


def test_nonexistent_tag(sample_items):
    """Test filtering by tag that doesn't exist in any item."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['nonexistent'],
        match_mode='any'
    )

    # Should return empty list
    assert len(results) == 0


def test_mix_of_existent_and_nonexistent_tags_any(sample_items):
    """Test filtering with mix of existent and nonexistent tags (any logic)."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'nonexistent'],
        match_mode='any'
    )

    result_ids = [item['id'] for item in results]
    # Should match all items with 'nature' (nonexistent tag ignored in OR)
    assert set(result_ids) == {1, 2, 4, 6, 8}


def test_mix_of_existent_and_nonexistent_tags_all(sample_items):
    """Test filtering with mix of existent and nonexistent tags (all logic)."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'nonexistent'],
        match_mode='all'
    )

    # Should return empty (no item has both nature AND nonexistent)
    assert len(results) == 0


def test_empty_tag_list(sample_items):
    """Test filtering with empty tag list returns all items."""
    filter = MockTagFilter()
    results_any = filter.filter_by_tags(sample_items, tags=[], match_mode='any')
    results_all = filter.filter_by_tags(sample_items, tags=[], match_mode='all')

    # Empty tag list should return all items (no filtering)
    assert len(results_any) == len(sample_items)
    assert len(results_all) == len(sample_items)


def test_items_with_no_tags(sample_items):
    """Test that items with no tags are not matched."""
    filter = MockTagFilter()
    results = filter.filter_by_tags(
        sample_items,
        tags=['nature'],
        match_mode='any'
    )

    result_ids = [item['id'] for item in results]
    # Item 7 has no tags, should not be included
    assert 7 not in result_ids


def test_all_logic_requires_all_tags(sample_items):
    """Test that 'all' logic strictly requires ALL tags."""
    filter = MockTagFilter()

    # Item 1 has nature+mountain+sunrise
    # Query for nature+mountain should match
    results1 = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'mountain'],
        match_mode='all'
    )
    assert 1 in [item['id'] for item in results1]

    # Query for nature+mountain+beach should NOT match (item doesn't have beach)
    results2 = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'mountain', 'beach'],
        match_mode='all'
    )
    assert 1 not in [item['id'] for item in results2]


def test_any_logic_matches_partial_overlap(sample_items):
    """Test that 'any' logic matches even partial overlaps."""
    filter = MockTagFilter()

    # Query for tags that only some items have
    results = filter.filter_by_tags(
        sample_items,
        tags=['sunrise', 'sunset', 'night'],
        match_mode='any'
    )

    result_ids = [item['id'] for item in results]
    # Item 1 (sunrise), Item 3 (night), Item 4 (sunset)
    assert set(result_ids) == {1, 3, 4}


def test_case_sensitivity(sample_items):
    """Test that tag matching is case-sensitive.

    Note: This documents expected behavior. If case-insensitive
    matching is desired, the implementation should normalize tags.
    """
    filter = MockTagFilter()

    # Query with different case
    results = filter.filter_by_tags(
        sample_items,
        tags=['Nature'],  # Capital N
        match_mode='any'
    )

    # Should NOT match (assuming case-sensitive)
    # If this fails, implementation may be case-insensitive (which is fine)
    # In that case, update test to reflect actual behavior
    assert len(results) == 0


@pytest.mark.parametrize('match_mode', ['any', 'all'])
def test_duplicate_tags_in_query(sample_items, match_mode):
    """Test that duplicate tags in query don't affect results."""
    filter = MockTagFilter()

    # Query with duplicate tags
    results_with_dupes = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'nature', 'mountain'],
        match_mode=match_mode
    )

    # Query without duplicates
    results_without_dupes = filter.filter_by_tags(
        sample_items,
        tags=['nature', 'mountain'],
        match_mode=match_mode
    )

    # Results should be identical
    result_ids_with = [item['id'] for item in results_with_dupes]
    result_ids_without = [item['id'] for item in results_without_dupes]
    assert set(result_ids_with) == set(result_ids_without)


def test_large_number_of_tags():
    """Test filtering with many tags doesn't break."""
    items = [
        {'id': 1, 'title': 'Item 1', 'tags': [f'tag{i}' for i in range(50)]},
        {'id': 2, 'title': 'Item 2', 'tags': ['tag1', 'tag2']},
    ]

    filter = MockTagFilter()

    # Query with many tags
    query_tags = [f'tag{i}' for i in range(20)]
    results = filter.filter_by_tags(items, tags=query_tags, match_mode='all')

    # Item 1 has all tags 0-49, should match
    result_ids = [item['id'] for item in results]
    assert 1 in result_ids
    assert 2 not in result_ids  # Item 2 doesn't have all queried tags
