"""Performance test for gallery tag query against live demo server.

This test validates that the canonical tag query completes within acceptable time limits.
It tests against the running demo server on port 8001.

IMPORTANT: This test expects the demo server to ALREADY BE RUNNING on port 8001.
It does NOT start its own test server. Start the demo server with: make api-demo

These tests are marked with @pytest.mark.performance and @pytest.mark.manual,
so they will NOT run during regular test suite execution.

Run manually with:
    pytest test/api/performance/ -v -s -m performance
"""

import pytest
import requests
import time


# Demo server configuration
DEMO_SERVER_BASE_URL = "http://localhost:8001"
TIMEOUT_SECONDS = 15  # Must complete before this timeout
PERFORMANCE_TARGET_SECONDS = 3  # Should complete within this time
NON_TAG_QUERY_TARGET_SECONDS = 2.0


@pytest.mark.performance
class TestGalleryTagPerformance:
    """Test performance of tag-filtered gallery queries against live demo server."""

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
            raise AssertionError(
                f"Query timed out after {elapsed_time:.2f}s "
                f"(timeout set to {TIMEOUT_SECONDS}s)"
            )
        except requests.ConnectionError as e:
            raise AssertionError(
                f"Could not connect to demo server at {DEMO_SERVER_BASE_URL}. "
                f"Ensure the server is running with: make api-demo\n"
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
            raise AssertionError(
                f"Could not connect to demo server at {DEMO_SERVER_BASE_URL}. "
                f"Ensure the server is running with: make api-demo\n"
                f"Error: {e}"
            )

    def test_measure_query_performance_detailed(self):
        """Detailed performance measurement with timing breakdown.

        Run this to get detailed performance metrics across multiple runs.
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
        successful = 0

        for i in range(num_runs):
            start = time.time()
            try:
                response = requests.get(
                    f"{DEMO_SERVER_BASE_URL}/api/v1/content/unified",
                    params=params,
                    timeout=TIMEOUT_SECONDS
                )
                elapsed = time.time() - start
                times.append(elapsed)
                successful += 1

                print(f"Run {i+1}: {elapsed:.3f}s (status: {response.status_code})")
            except Exception as e:
                elapsed = time.time() - start
                print(f"Run {i+1}: {elapsed:.3f}s (FAILED: {e})")

        if times:
            print("\n" + "-"*80)
            print(f"Successful runs: {successful}/{num_runs}")
            print(f"Average: {sum(times)/len(times):.3f}s")
            print(f"Min: {min(times):.3f}s")
            print(f"Max: {max(times):.3f}s")
            print("="*80)

            # Assert at least some runs were successful and within target
            assert successful > 0, "No successful runs"
            assert sum(times)/len(times) < PERFORMANCE_TARGET_SECONDS, (
                f"Average time {sum(times)/len(times):.2f}s exceeds target {PERFORMANCE_TARGET_SECONDS}s"
            )
