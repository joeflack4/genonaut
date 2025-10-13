"""Integration test for gallery tag query performance against live demo server.

This test validates that the canonical tag query completes within acceptable time limits.
It tests against the running demo server on port 8001.

IMPORTANT: This test expects the demo server to ALREADY BE RUNNING on port 8001.
It does NOT start its own test server. Start the demo server with: make api-demo

These tests are marked with @pytest.mark.performance and @pytest.mark.manual,
so they will NOT run during regular test suite execution.

Run manually with:
    pytest test/api/integration/test_gallery_tag_performance.py -v -s -m performance
"""

import pytest
import requests
import time
from typing import Dict, Any


# Demo server configuration
DEMO_SERVER_BASE_URL = "http://localhost:8001"
TIMEOUT_SECONDS = 15  # Must complete before this timeout
PERFORMANCE_TARGET_SECONDS = 3  # Should complete within this time
NON_TAG_QUERY_TARGET_SECONDS = 2.0


@pytest.mark.performance
class TestGalleryTagPerformance:
    """Test performance of tag-filtered gallery queries."""

    def test_canonical_tag_query_performance(self):
        """Test that canonical tag query completes within 3 seconds.

        This is the canonical query that was timing out:
        - All content_source_types selected (user-regular, user-auto, community-regular, community-auto)
        - Single tag filter (anime tag: dfbb88fc-3c31-468f-a2d7-99605206c985)
        - User ID filter
        - Sort by created_at DESC
        - Page 1, page_size 25
        """
        # Canonical query parameters
        params = {
            "page": 1,
            "page_size": 25,
            "content_source_types": [
                "user-regular",
                "user-auto",
                "community-regular",
                "community-auto"
            ],
            "user_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9",
            "sort_field": "created_at",
            "sort_order": "desc",
            "tag": "dfbb88fc-3c31-468f-a2d7-99605206c985"  # anime tag
        }

        # Make the request and measure time
        start_time = time.time()

        try:
            response = requests.get(
                f"{DEMO_SERVER_BASE_URL}/api/v1/content/unified",
                params=params,
                timeout=TIMEOUT_SECONDS
            )

            elapsed_time = time.time() - start_time

            # Check response is successful
            assert response.status_code == 200, (
                f"Expected 200 OK, got {response.status_code}: {response.text}"
            )

            # Check response has expected structure
            data = response.json()
            assert "items" in data, "Response should have 'items' field"
            assert "pagination" in data, "Response should have 'pagination' field"

            # Check performance target
            assert elapsed_time < PERFORMANCE_TARGET_SECONDS, (
                f"Query took {elapsed_time:.2f}s, which exceeds target of "
                f"{PERFORMANCE_TARGET_SECONDS}s"
            )

            # Success - query completed within target time

        except requests.Timeout:
            elapsed_time = time.time() - start_time
            pytest.fail(
                f"Query timed out after {elapsed_time:.2f}s "
                f"(timeout set to {TIMEOUT_SECONDS}s)"
            )
        except requests.ConnectionError as e:
            pytest.fail(
                f"Could not connect to demo server at {DEMO_SERVER_BASE_URL}. "
                f"Ensure the server is running with: make start-api\n"
                f"Error: {e}"
            )

    def test_canonical_query_without_tag_is_fast(self):
        """Baseline test: same query without tag filter should be fast.

        This helps identify if the issue is specifically with tag filtering.
        """
        params = {
            "page": 1,
            "page_size": 25,
            "content_source_types": [
                "user-regular",
                "user-auto",
                "community-regular",
                "community-auto"
            ],
            "user_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9",
            "sort_field": "created_at",
            "sort_order": "desc"
            # No tag filter
        }

        start_time = time.time()

        try:
            response = requests.get(
                f"{DEMO_SERVER_BASE_URL}/api/v1/content/unified",
                params=params,
                timeout=TIMEOUT_SECONDS
            )

            elapsed_time = time.time() - start_time

            assert response.status_code == 200
            assert elapsed_time < NON_TAG_QUERY_TARGET_SECONDS, (
                f"Non-tag query should be very fast, but took {elapsed_time:.2f}s"
            )

        except requests.ConnectionError as e:
            pytest.fail(
                f"Could not connect to demo server at {DEMO_SERVER_BASE_URL}. "
                f"Ensure the server is running with: make start-api\n"
                f"Error: {e}"
            )

    def test_tag_query_with_multiple_tags(self):
        """Test tag query with multiple tags using 'any' matching.

        This tests a more complex scenario with multiple tag filters.
        """
        params = {
            "page": 1,
            "page_size": 25,
            "content_source_types": [
                "user-regular",
                "user-auto",
                "community-regular",
                "community-auto"
            ],
            "user_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9",
            "sort_field": "created_at",
            "sort_order": "desc",
            "tag": [
                "dfbb88fc-3c31-468f-a2d7-99605206c985",  # anime
                # Add more tags if needed
            ],
            "tag_match": "any"
        }

        start_time = time.time()

        try:
            response = requests.get(
                f"{DEMO_SERVER_BASE_URL}/api/v1/content/unified",
                params=params,
                timeout=TIMEOUT_SECONDS
            )

            elapsed_time = time.time() - start_time

            assert response.status_code == 200
            assert elapsed_time < PERFORMANCE_TARGET_SECONDS, (
                f"Multi-tag query took {elapsed_time:.2f}s, exceeds target"
            )

        except requests.ConnectionError as e:
            pytest.fail(
                f"Could not connect to demo server at {DEMO_SERVER_BASE_URL}. "
                f"Ensure the server is running with: make start-api\n"
                f"Error: {e}"
            )


@pytest.mark.performance
class TestManualGalleryPerformance:
    """Manual performance tests that can be run selectively.

    These tests are designed to run against the live demo server on port 8001.
    They do NOT start their own test server - they expect the demo server to already be running.
    """

    def test_measure_query_performance_detailed(self):
        """Detailed performance measurement with timing breakdown.

        Run this manually to get detailed performance metrics:
        pytest test/api/integration/test_gallery_tag_performance.py::TestManualGalleryPerformance::test_measure_query_performance_detailed -v -s

        Prerequisites:
        - Demo server must be running on port 8001
        - Start with: make api-demo
        """
        params = {
            "page": 1,
            "page_size": 25,
            "content_source_types": [
                "user-regular",
                "user-auto",
                "community-regular",
                "community-auto"
            ],
            "user_id": "121e194b-4caa-4b81-ad4f-86ca3919d5b9",
            "sort_field": "created_at",
            "sort_order": "desc",
            "tag": "dfbb88fc-3c31-468f-a2d7-99605206c985"
        }

        print("\n" + "="*80)
        print("DETAILED PERFORMANCE MEASUREMENT")
        print("="*80)

        # Make multiple requests to get average
        num_runs = 5
        times = []

        for i in range(num_runs):
            start = time.time()
            response = requests.get(
                f"{DEMO_SERVER_BASE_URL}/api/v1/content/unified",
                params=params,
                timeout=TIMEOUT_SECONDS
            )
            elapsed = time.time() - start
            times.append(elapsed)

            print(f"Run {i+1}: {elapsed:.3f}s (status: {response.status_code})")

        print("\n" + "-"*80)
        print(f"Average: {sum(times)/len(times):.3f}s")
        print(f"Min: {min(times):.3f}s")
        print(f"Max: {max(times):.3f}s")
        print("="*80)
