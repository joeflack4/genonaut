"""API integration tests for tag query combinations against demo database.

These tests verify that the unified content endpoint returns correct results
for various tag filtering combinations. Unlike other tests, these run against
the DEMO database with real data to validate performance and accuracy.

Tests are marked with @pytest.mark.tag_queries and @pytest.mark.longrunning.

Test data reference: test/api/notes/tag_query_test_data.md
"""

import math
import os
import pytest
import requests

# Test user ID from demo database
TEST_USER_ID = "121e194b-4caa-4b81-ad4f-86ca3919d5b9"

# API base URL (defaults to port 8001, can override with API_BASE_URL env var)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")

# Tag IDs from demo database (see test/api/notes/tag_query_test_data.md)
TAG_ANIME = "dfbb88fc-3c31-468f-a2d7-99605206c985"
TAG_4K = "eeed7442-6374-4e2a-b110-f97fcc89df78"

# Five most popular tags
TAG_PASTEL = "94ea732c-067c-4552-8d84-9663ef00e43a"
TAG_MOODY = "45a09394-4710-4380-8d56-b18b8af361a2"
TAG_CRAYON = "3cfa3c68-dac7-4034-ad6c-ab6b7fe639fa"
TAG_FLAT = "edb00348-4517-473c-bb5d-3b3f4ad89be5"
TAG_MINIMALIST_TYPOGRAPHY = "0f5f42ca-6d96-4e56-9896-f331c339c5c1"

# Twenty most popular tags
TWENTY_TAGS = [
    "94ea732c-067c-4552-8d84-9663ef00e43a",  # pastel
    "45a09394-4710-4380-8d56-b18b8af361a2",  # moody
    "3cfa3c68-dac7-4034-ad6c-ab6b7fe639fa",  # crayon
    "edb00348-4517-473c-bb5d-3b3f4ad89be5",  # flat
    "0f5f42ca-6d96-4e56-9896-f331c339c5c1",  # minimalist-typography
    "98e9f2e8-0b69-4537-b417-bc208bd82c70",  # soft-light
    "be35c31c-58cb-4d31-bccc-f41f20b54cba",  # hand-drawn
    "9076888a-3939-4ad7-8763-47fe3276babf",  # vibrant
    "0e62209e-97ad-4ddb-86e0-2494d7a61e41",  # installation
    "0e283364-214b-42a1-82fe-42382ab2043a",  # cinematic
    "ab7b665f-4b93-4285-b79f-ebb765e7c139",  # vector
    "bf2a93fd-79b6-4f84-b072-4e23d9195498",  # glossy
    "e7461eb7-b898-4641-ac39-9675ee7af6ab",  # symmetrical
    "2823e3cd-63fd-4797-bd59-041ef350f386",  # experimental
    "47575f40-d6ec-4946-aabc-bdb8c4fdd09e",  # tilt-shift
    "3d7303d3-9939-4002-9e1c-4b4c50473891",  # gothic
    "44f9e5df-9ace-46eb-a6f7-615b30935c24",  # action
    "069dfa87-481a-4ee2-963c-1d16023fbc17",  # isometric
    "41330e77-f595-41a5-9327-e101b42d2141",  # horror
    "158354e1-5671-4154-9aa1-1cf2c04fbf41",  # thumbnail
]

# Default page size used by frontend
DEFAULT_PAGE_SIZE = 25


def _build_unified_content_url(tags, page=1, page_size=DEFAULT_PAGE_SIZE):
    """Build unified content API URL with tag filters.

    Args:
        tags: List of tag UUIDs to filter by (AND condition)
        page: Page number (default: 1)
        page_size: Items per page (default: 25)

    Returns:
        Full API URL with query parameters
    """
    params = [
        f"page={page}",
        f"page_size={page_size}",
        "content_source_types=user-regular",
        "content_source_types=user-auto",
        "content_source_types=community-regular",
        "content_source_types=community-auto",
        f"user_id={TEST_USER_ID}",
        "sort_field=created_at",
        "sort_order=desc",
    ]

    # Add tag filters
    for tag_id in tags:
        params.append(f"tag={tag_id}")

    query_string = "&".join(params)
    return f"{API_BASE_URL}/api/v1/content/unified?{query_string}"


@pytest.mark.tag_queries
def test_single_tag_anime():
    """Test query with single tag: 'anime'.

    Expected: >= 836,134 content items (from demo database)
    Reference: test/api/notes/tag_query_test_data.md - Test Case 1
    """
    url = _build_unified_content_url([TAG_ANIME])
    response = requests.get(url, timeout=30)

    assert response.status_code == 200, f"API request failed: {response.text}"

    data = response.json()
    items = data.get("items", [])
    pagination = data.get("pagination", {})

    # Verify items are returned
    assert len(items) > 0, "Expected non-empty items list"
    assert len(items) <= DEFAULT_PAGE_SIZE, f"Expected <= {DEFAULT_PAGE_SIZE} items, got {len(items)}"

    # Verify total count (may be -1 if COUNT is skipped for performance)
    total_count = pagination.get("total_count", 0)
    if total_count != -1:
        assert total_count >= 836_000, f"Expected >= 836,000 items, got {total_count:,}"

        # Verify page count matches total count
        expected_pages = math.ceil(total_count / DEFAULT_PAGE_SIZE)
        actual_pages = pagination.get("total_pages", 0)
        assert actual_pages == expected_pages, f"Expected {expected_pages} pages, got {actual_pages}"


@pytest.mark.tag_queries
def test_single_tag_4k():
    """Test query with single tag: '4k'.

    Expected: >= 836,262 content items (from demo database)
    Reference: test/api/notes/tag_query_test_data.md - Test Case 2
    """
    url = _build_unified_content_url([TAG_4K])
    response = requests.get(url, timeout=30)

    assert response.status_code == 200, f"API request failed: {response.text}"

    data = response.json()
    items = data.get("items", [])
    pagination = data.get("pagination", {})

    # Verify items are returned
    assert len(items) > 0, "Expected non-empty items list"
    assert len(items) <= DEFAULT_PAGE_SIZE, f"Expected <= {DEFAULT_PAGE_SIZE} items, got {len(items)}"

    # Verify total count (may be -1 if COUNT is skipped for performance)
    total_count = pagination.get("total_count", 0)
    if total_count != -1:
        assert total_count >= 836_000, f"Expected >= 836,000 items, got {total_count:,}"

        # Verify page count matches total count
        expected_pages = math.ceil(total_count / DEFAULT_PAGE_SIZE)
        actual_pages = pagination.get("total_pages", 0)
        assert actual_pages == expected_pages, f"Expected {expected_pages} pages, got {actual_pages}"


@pytest.mark.tag_queries
def test_two_tags_anime_and_4k():
    """Test query with two tags: 'anime' AND '4k'.

    Expected: >= 742,257 content items (from demo database)
    Reference: test/api/notes/tag_query_test_data.md - Test Case 3
    """
    url = _build_unified_content_url([TAG_ANIME, TAG_4K])
    response = requests.get(url, timeout=30)

    assert response.status_code == 200, f"API request failed: {response.text}"

    data = response.json()
    items = data.get("items", [])
    pagination = data.get("pagination", {})

    # Verify items are returned
    assert len(items) > 0, "Expected non-empty items list"
    assert len(items) <= DEFAULT_PAGE_SIZE, f"Expected <= {DEFAULT_PAGE_SIZE} items, got {len(items)}"

    # Verify total count (may be -1 if COUNT is skipped for performance)
    total_count = pagination.get("total_count", 0)
    if total_count != -1:
        assert total_count >= 726_000, f"Expected >= 726,000 items, got {total_count:,}"

        # Verify page count matches total count
        expected_pages = math.ceil(total_count / DEFAULT_PAGE_SIZE)
        actual_pages = pagination.get("total_pages", 0)
        assert actual_pages == expected_pages, f"Expected {expected_pages} pages, got {actual_pages}"


@pytest.mark.tag_queries
def test_five_tags():
    """Test query with five tags: pastel, moody, crayon, flat, minimalist-typography.

    Expected: >= 662,239 content items (from demo database)
    Reference: test/api/notes/tag_query_test_data.md - Test Case 4
    """
    five_tags = [TAG_PASTEL, TAG_MOODY, TAG_CRAYON, TAG_FLAT, TAG_MINIMALIST_TYPOGRAPHY]
    url = _build_unified_content_url(five_tags)
    response = requests.get(url, timeout=30)

    assert response.status_code == 200, f"API request failed: {response.text}"

    data = response.json()
    items = data.get("items", [])
    pagination = data.get("pagination", {})

    # Verify items are returned
    assert len(items) > 0, "Expected non-empty items list"
    assert len(items) <= DEFAULT_PAGE_SIZE, f"Expected <= {DEFAULT_PAGE_SIZE} items, got {len(items)}"

    # Verify total count (may be -1 if COUNT is skipped for performance)
    total_count = pagination.get("total_count", 0)
    if total_count != -1:
        assert total_count >= 662_000, f"Expected >= 662,000 items, got {total_count:,}"

        # Verify page count matches total count
        expected_pages = math.ceil(total_count / DEFAULT_PAGE_SIZE)
        actual_pages = pagination.get("total_pages", 0)
        assert actual_pages == expected_pages, f"Expected {expected_pages} pages, got {actual_pages}"


@pytest.mark.tag_queries
def test_twenty_tags():
    """Test query with twenty tags (top 20 most popular).

    Expected: >= 565,508 content items (from demo database)
    Reference: test/api/notes/tag_query_test_data.md - Test Case 5
    """
    url = _build_unified_content_url(TWENTY_TAGS)
    response = requests.get(url, timeout=30)

    assert response.status_code == 200, f"API request failed: {response.text}"

    data = response.json()
    items = data.get("items", [])
    pagination = data.get("pagination", {})

    # Verify items are returned
    assert len(items) > 0, "Expected non-empty items list"
    assert len(items) <= DEFAULT_PAGE_SIZE, f"Expected <= {DEFAULT_PAGE_SIZE} items, got {len(items)}"

    # Verify total count (may be -1 if COUNT is skipped for performance)
    total_count = pagination.get("total_count", 0)
    if total_count != -1:
        assert total_count >= 565_000, f"Expected >= 565,000 items, got {total_count:,}"

        # Verify page count matches total count
        expected_pages = math.ceil(total_count / DEFAULT_PAGE_SIZE)
        actual_pages = pagination.get("total_pages", 0)
        assert actual_pages == expected_pages, f"Expected {expected_pages} pages, got {actual_pages}"


@pytest.mark.tag_queries
def test_tag_query_returns_different_results():
    """Test that different tag combinations return different content items.

    This validates that tag filtering is actually working and not just
    returning the same results for all queries.
    """
    # Query 1: anime only
    url1 = _build_unified_content_url([TAG_ANIME], page_size=10)
    response1 = requests.get(url1, timeout=30)
    assert response1.status_code == 200
    items1 = response1.json().get("items", [])
    item_ids1 = {(item["id"], item["source_type"]) for item in items1}

    # Query 2: 4k only
    url2 = _build_unified_content_url([TAG_4K], page_size=10)
    response2 = requests.get(url2, timeout=30)
    assert response2.status_code == 200
    items2 = response2.json().get("items", [])
    item_ids2 = {(item["id"], item["source_type"]) for item in items2}

    # Query 3: anime + 4k
    url3 = _build_unified_content_url([TAG_ANIME, TAG_4K], page_size=10)
    response3 = requests.get(url3, timeout=30)
    assert response3.status_code == 200
    items3 = response3.json().get("items", [])
    item_ids3 = {(item["id"], item["source_type"]) for item in items3}

    # Verify that not all queries return identical results
    # At least one query should have different items than the others
    all_same = (item_ids1 == item_ids2 == item_ids3)
    assert not all_same, (
        "All three tag queries returned identical items. "
        "This suggests tag filtering may not be working correctly."
    )
