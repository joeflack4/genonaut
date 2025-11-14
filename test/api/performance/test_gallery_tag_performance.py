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

import os
import pytest
import requests
import time
from typing import Optional


# Demo server configuration (defaults to port 8001, can override with API_BASE_URL env var)
DEMO_SERVER_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8001")
TIMEOUT_SECONDS = 15  # Must complete before this timeout
PERFORMANCE_TARGET_SECONDS = 3  # Should complete within this time
NON_TAG_QUERY_TARGET_SECONDS = 3.5  # Allow margin for system variance (CPU, GC, background services)


def check_server_health() -> tuple[bool, Optional[str]]:
    """Check if the demo server is healthy and ready.

    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        response = requests.get(
            f"{DEMO_SERVER_BASE_URL}/api/v1/health",
            timeout=5
        )

        if response.status_code != 200:
            return False, f"Health endpoint returned {response.status_code}: {response.text}"

        data = response.json()
        if data.get("status") != "healthy":
            return False, f"Server status is '{data.get('status')}', expected 'healthy'"

        db_status = data.get("database", {}).get("status")
        if db_status != "connected":
            return False, f"Database status is '{db_status}', expected 'connected'"

        return True, None

    except requests.ConnectionError:
        return False, f"Could not connect to {DEMO_SERVER_BASE_URL}. Is the server running? (make api-demo)"
    except requests.Timeout:
        return False, "Health check timed out"
    except Exception as e:
        return False, f"Unexpected error during health check: {e}"


def warmup_server():
    """Make a warmup request to eliminate cold start overhead.

    This prevents the first performance test from being unfairly slow due to:
    - Connection pool initialization
    - Database connection establishment
    - Cache warming
    """
    try:
        # Make two quick health check requests
        requests.get(f"{DEMO_SERVER_BASE_URL}/api/v1/health", timeout=5)
        time.sleep(0.1)
        requests.get(f"{DEMO_SERVER_BASE_URL}/api/v1/health", timeout=5)
    except Exception:
        # Warmup failure is not critical
        pass


@pytest.mark.performance
class TestGalleryTagPerformance:
    """Test performance of tag-filtered gallery queries against live demo server."""

    def setup_method(self):
        """Run before each test to ensure server is healthy."""
        is_healthy, error = check_server_health()
        if not is_healthy:
            pytest.skip(f"Server health check failed: {error}")

        # Warm up server to eliminate cold start effects
        warmup_server()

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
            # This should not happen due to setup_method health check
            raise AssertionError(
                f"Lost connection to demo server during test. "
                f"Server may have crashed or restarted.\n"
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
            # This should not happen due to setup_method health check
            raise AssertionError(
                f"Lost connection to demo server during test. "
                f"Server may have crashed or restarted.\n"
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
