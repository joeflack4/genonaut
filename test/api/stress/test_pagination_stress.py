"""
Stress tests for pagination performance with large datasets.

These tests simulate scenarios with millions of rows to validate:
- Response time performance under load
- Memory usage patterns
- Database query optimization
- Pagination stability with concurrent requests
"""

import asyncio
import time
import gc
import psutil
import pytest
import uuid
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock

from sqlalchemy import text, func
from sqlalchemy.orm import Session

from genonaut.api.models.requests import PaginationRequest
from genonaut.api.models.responses import PaginatedResponse
from genonaut.api.repositories.base import BaseRepository
from genonaut.api.repositories.content_repository import ContentRepository
from genonaut.db.schema import ContentItem, User

# Test configuration
STRESS_TEST_PAGE_SIZE = 50
LARGE_DATASET_SIZE = 100000  # Simulate 100K rows (can be scaled up)
CONCURRENT_REQUESTS = 10
MAX_RESPONSE_TIME_MS = 200  # Maximum acceptable response time
MAX_MEMORY_USAGE_MB = 300   # Maximum acceptable memory usage per worker (increased for large datasets)


class PerformanceMetrics:
    """Helper class to track performance metrics during stress tests."""

    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start_timing(self):
        """Start timing a request."""
        self.start_time = time.time()

    def stop_timing(self):
        """Stop timing and record response time."""
        if self.start_time:
            self.end_time = time.time()
            response_time = (self.end_time - self.start_time) * 1000  # Convert to ms
            self.response_times.append(response_time)

    def record_memory_usage(self):
        """Record current memory usage."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)

    def record_error(self, error: str):
        """Record an error that occurred during testing."""
        self.errors.append(error)

    @property
    def avg_response_time(self) -> float:
        """Average response time in milliseconds."""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0

    @property
    def max_response_time(self) -> float:
        """Maximum response time in milliseconds."""
        return max(self.response_times) if self.response_times else 0

    @property
    def avg_memory_usage(self) -> float:
        """Average memory usage in MB."""
        return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0

    @property
    def max_memory_usage(self) -> float:
        """Maximum memory usage in MB."""
        return max(self.memory_usage) if self.memory_usage else 0


class StressTester:
    """Main class for conducting pagination stress tests."""

    def __init__(self, session: Session):
        self.session = session
        self.content_repository = ContentRepository(session)
        self.metrics = PerformanceMetrics()

    def setup_large_dataset(self, size: int = LARGE_DATASET_SIZE) -> str:
        """
        Create a large dataset for stress testing.
        Returns the creator_id used for the test data.
        """
        print(f"Setting up large dataset with {size} records...")

        # Create a test user with proper UUID
        test_user_id = uuid.uuid4()
        test_user = User(
            id=test_user_id,
            email="stress@test.com",
            username="stresstest"
        )
        self.session.add(test_user)
        self.session.commit()

        # Batch insert content items
        batch_size = 1000
        creator_id = test_user.id

        for i in range(0, size, batch_size):
            batch_items = []
            batch_end = min(i + batch_size, size)

            for j in range(i, batch_end):
                item = ContentItem(
                    title=f"Stress Test Item {j:06d}",
                    content_data=f"Generated content item for stress testing - Item #{j}",
                    creator_id=creator_id,
                    prompt="Test prompt",
                    quality_score=0.5 + (j % 100) / 200,  # Vary quality scores
                    content_type="text",
                    is_private=(j % 3 == 0)  # Mix of public/private content
                )
                batch_items.append(item)

            self.session.bulk_save_objects(batch_items)

            # Commit in batches and provide progress feedback
            if (i // batch_size) % 10 == 0:
                self.session.commit()
                print(f"Created {min(i + batch_size, size)} / {size} records...")

        self.session.commit()
        print(f"Dataset setup complete: {size} records created")
        return creator_id

    def cleanup_large_dataset(self, creator_id):
        """Remove the large dataset after testing."""
        print("Cleaning up large dataset...")

        # Delete content items
        self.session.query(ContentItem).filter(
            ContentItem.creator_id == creator_id
        ).delete()

        # Delete test user
        self.session.query(User).filter(User.id == creator_id).delete()

        self.session.commit()
        print("Dataset cleanup complete")

    def test_single_page_performance(self, page: int = 1) -> Dict[str, Any]:
        """Test performance of a single page request."""
        self.metrics.start_timing()
        self.metrics.record_memory_usage()

        try:
            pagination = PaginationRequest(
                page=page,
                page_size=STRESS_TEST_PAGE_SIZE
            )

            result = self.content_repository.get_paginated(pagination)

            self.metrics.stop_timing()
            self.metrics.record_memory_usage()

            return {
                "success": True,
                "item_count": len(result.items),
                "total_count": result.pagination.total_count,
                "has_next": result.pagination.has_next,
                "response_time_ms": self.metrics.response_times[-1] if self.metrics.response_times else 0,
                "memory_mb": self.metrics.memory_usage[-1] if self.metrics.memory_usage else 0
            }

        except Exception as e:
            self.metrics.record_error(str(e))
            return {"success": False, "error": str(e)}

    def test_deep_pagination_performance(self, max_pages: int = 100) -> Dict[str, Any]:
        """Test performance when paginating deep into large datasets."""
        print(f"Testing deep pagination performance (up to page {max_pages})...")

        results = []

        # Test pages at different depths
        test_pages = [1, 10, 25, 50, max_pages]

        for page in test_pages:
            print(f"Testing page {page}...")
            result = self.test_single_page_performance(page)
            results.append({
                "page": page,
                **result
            })

        return {
            "deep_pagination_results": results,
            "avg_response_time": self.metrics.avg_response_time,
            "max_response_time": self.metrics.max_response_time,
            "performance_degradation": self._calculate_performance_degradation(results)
        }

    def _calculate_performance_degradation(self, results: List[Dict]) -> Dict[str, float]:
        """Calculate performance degradation across page depths."""
        successful_results = [r for r in results if r.get("success")]

        if len(successful_results) < 2:
            return {"degradation_factor": 0, "first_page_time": 0, "last_page_time": 0}

        first_time = successful_results[0].get("response_time_ms", 0)
        last_time = successful_results[-1].get("response_time_ms", 0)

        degradation_factor = last_time / first_time if first_time > 0 else 0

        return {
            "degradation_factor": degradation_factor,
            "first_page_time": first_time,
            "last_page_time": last_time
        }

    def test_concurrent_pagination_requests(self, num_requests: int = CONCURRENT_REQUESTS) -> Dict[str, Any]:
        """Test pagination performance under concurrent load."""
        print(f"Testing concurrent pagination with {num_requests} simultaneous requests...")

        def make_request(page: int) -> Dict[str, Any]:
            """Make a single pagination request."""
            start_time = time.time()
            try:
                pagination = PaginationRequest(
                    page=page,
                    page_size=STRESS_TEST_PAGE_SIZE
                )

                result = self.content_repository.get_paginated(pagination)

                response_time = (time.time() - start_time) * 1000

                return {
                    "success": True,
                    "page": page,
                    "response_time_ms": response_time,
                    "item_count": len(result.items)
                }

            except Exception as e:
                return {
                    "success": False,
                    "page": page,
                    "error": str(e),
                    "response_time_ms": (time.time() - start_time) * 1000
                }

        # Execute concurrent requests
        concurrent_results = []

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            # Submit requests for different pages
            futures = {
                executor.submit(make_request, page): page
                for page in range(1, num_requests + 1)
            }

            for future in as_completed(futures):
                result = future.result()
                concurrent_results.append(result)

        # Analyze concurrent performance
        successful_requests = [r for r in concurrent_results if r["success"]]
        failed_requests = [r for r in concurrent_results if not r["success"]]

        avg_concurrent_time = (
            sum(r["response_time_ms"] for r in successful_requests) / len(successful_requests)
            if successful_requests else 0
        )

        return {
            "total_requests": num_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "avg_response_time_ms": avg_concurrent_time,
            "max_response_time_ms": max((r["response_time_ms"] for r in successful_requests), default=0),
            "success_rate": len(successful_requests) / num_requests if num_requests > 0 else 0,
            "errors": [r["error"] for r in failed_requests]
        }

    def test_cursor_pagination_performance(self) -> Dict[str, Any]:
        """Test cursor-based pagination performance."""
        print("Testing cursor-based pagination performance...")

        cursor_results = []
        current_cursor = None
        pages_tested = 0
        max_pages = 20  # Test first 20 pages with cursor pagination

        try:
            while pages_tested < max_pages:
                self.metrics.start_timing()

                pagination = PaginationRequest(
                    page_size=STRESS_TEST_PAGE_SIZE,
                    cursor=current_cursor
                )

                result = self.content_repository.get_paginated(pagination)

                self.metrics.stop_timing()
                self.metrics.record_memory_usage()

                cursor_results.append({
                    "page": pages_tested + 1,
                    "cursor": current_cursor,
                    "next_cursor": result.pagination.next_cursor,
                    "item_count": len(result.items),
                    "response_time_ms": self.metrics.response_times[-1] if self.metrics.response_times else 0
                })

                # Move to next cursor
                current_cursor = result.pagination.next_cursor
                pages_tested += 1

                # Break if no more pages
                if not result.pagination.has_next or not current_cursor:
                    break

        except Exception as e:
            self.metrics.record_error(str(e))
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "pages_tested": pages_tested,
            "cursor_results": cursor_results,
            "avg_response_time": self.metrics.avg_response_time,
            "consistent_performance": self._analyze_cursor_consistency(cursor_results)
        }

    def _analyze_cursor_consistency(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze if cursor pagination maintains consistent performance."""
        response_times = [r["response_time_ms"] for r in results]

        if len(response_times) < 2:
            return {"consistent": True, "variance": 0}

        avg_time = sum(response_times) / len(response_times)
        variance = sum((t - avg_time) ** 2 for t in response_times) / len(response_times)
        coefficient_of_variation = (variance ** 0.5) / avg_time if avg_time > 0 else 0

        # Consider consistent if coefficient of variation is less than 20%
        is_consistent = coefficient_of_variation < 0.2

        return {
            "consistent": is_consistent,
            "variance": variance,
            "coefficient_of_variation": coefficient_of_variation,
            "avg_response_time": avg_time
        }

    def test_memory_usage_stability(self, pages_to_test: int = 50) -> Dict[str, Any]:
        """Test that memory usage remains stable during extended pagination."""
        print(f"Testing memory usage stability across {pages_to_test} pages...")

        memory_readings = []
        initial_memory = None

        for page in range(1, pages_to_test + 1):
            # Force garbage collection before measurement
            gc.collect()

            # Record memory before request
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024

            if initial_memory is None:
                initial_memory = memory_before

            # Make pagination request
            try:
                pagination = PaginationRequest(
                    page=page,
                    page_size=STRESS_TEST_PAGE_SIZE
                )

                result = self.content_repository.get_paginated(pagination)

                # Record memory after request
                memory_after = process.memory_info().rss / 1024 / 1024

                memory_readings.append({
                    "page": page,
                    "memory_before_mb": memory_before,
                    "memory_after_mb": memory_after,
                    "memory_delta_mb": memory_after - memory_before,
                    "item_count": len(result.items)
                })

            except Exception as e:
                self.metrics.record_error(f"Page {page}: {str(e)}")

        # Analyze memory stability
        if not memory_readings:
            return {"success": False, "error": "No successful memory readings"}

        final_memory = memory_readings[-1]["memory_after_mb"]
        memory_growth = final_memory - initial_memory
        avg_memory = sum(r["memory_after_mb"] for r in memory_readings) / len(memory_readings)

        # Check for memory leaks (growth > 50MB indicates potential issue)
        has_memory_leak = memory_growth > 50

        return {
            "success": True,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": memory_growth,
            "avg_memory_mb": avg_memory,
            "has_potential_leak": has_memory_leak,
            "readings": memory_readings,
            "pages_tested": len(memory_readings)
        }


@pytest.mark.stress
@pytest.mark.longrunning
class TestPaginationStress:
    """Stress test class for pagination performance validation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, large_db_session):
        """Setup and teardown for stress tests."""
        self.stress_tester = StressTester(large_db_session)
        self.creator_id = None

        yield

        # Cleanup after tests
        if self.creator_id:
            try:
                self.stress_tester.cleanup_large_dataset(self.creator_id)
            except Exception as e:
                print(f"Cleanup warning: {e}")

    def test_pagination_with_large_dataset(self, large_db_session):
        """Test pagination performance with a large dataset."""
        # Setup large dataset
        self.creator_id = self.stress_tester.setup_large_dataset(LARGE_DATASET_SIZE)

        # Test single page performance
        result = self.stress_tester.test_single_page_performance()

        assert result["success"], f"Single page test failed: {result.get('error')}"
        assert result["response_time_ms"] < MAX_RESPONSE_TIME_MS, (
            f"Response time {result['response_time_ms']}ms exceeds limit {MAX_RESPONSE_TIME_MS}ms"
        )
        assert result["memory_mb"] < MAX_MEMORY_USAGE_MB, (
            f"Memory usage {result['memory_mb']}MB exceeds limit {MAX_MEMORY_USAGE_MB}MB"
        )

        print(f"✓ Single page performance: {result['response_time_ms']:.2f}ms, {result['memory_mb']:.2f}MB")

    def test_deep_pagination_performance(self, large_db_session):
        """Test that deep pagination maintains acceptable performance."""
        # Setup large dataset
        self.creator_id = self.stress_tester.setup_large_dataset(LARGE_DATASET_SIZE)

        # Test deep pagination
        result = self.stress_tester.test_deep_pagination_performance(50)

        assert result["max_response_time"] < MAX_RESPONSE_TIME_MS * 2, (
            f"Max deep pagination time {result['max_response_time']}ms exceeds limit"
        )

        # Performance should not degrade more than 3x from first to last page
        degradation = result["performance_degradation"]
        assert degradation["degradation_factor"] < 3.0, (
            f"Performance degraded by {degradation['degradation_factor']}x, exceeds 3x limit"
        )

        print(f"✓ Deep pagination performance: avg {result['avg_response_time']:.2f}ms, "
              f"degradation {degradation['degradation_factor']:.2f}x")

    @pytest.mark.skip(reason="Data scaling tests - Performance/stress testing (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_concurrent_pagination_load(self, large_db_session):
        """Test pagination performance under concurrent load."""
        # Setup large dataset
        self.creator_id = self.stress_tester.setup_large_dataset(LARGE_DATASET_SIZE)

        # Test concurrent requests
        result = self.stress_tester.test_concurrent_pagination_requests(CONCURRENT_REQUESTS)

        assert result["success_rate"] >= 0.9, (
            f"Success rate {result['success_rate']} below 90%"
        )
        assert result["avg_response_time_ms"] < MAX_RESPONSE_TIME_MS * 2, (
            f"Concurrent avg response time {result['avg_response_time_ms']}ms exceeds limit"
        )

        print(f"✓ Concurrent load performance: {result['successful_requests']}/{result['total_requests']} "
              f"success, avg {result['avg_response_time_ms']:.2f}ms")

    @pytest.mark.skip(reason="Data scaling tests - Performance/stress testing and cursor navigation (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_cursor_pagination_performance(self, large_db_session):
        """Test cursor-based pagination performance and consistency."""
        # Setup large dataset
        self.creator_id = self.stress_tester.setup_large_dataset(LARGE_DATASET_SIZE)

        # Test cursor pagination
        result = self.stress_tester.test_cursor_pagination_performance()

        assert result["success"], f"Cursor pagination failed: {result.get('error')}"
        assert result["avg_response_time"] < MAX_RESPONSE_TIME_MS, (
            f"Cursor pagination avg time {result['avg_response_time']}ms exceeds limit"
        )

        consistency = result["consistent_performance"]
        assert consistency["consistent"], (
            f"Cursor pagination performance inconsistent: CV={consistency['coefficient_of_variation']:.3f}"
        )

        print(f"✓ Cursor pagination performance: avg {result['avg_response_time']:.2f}ms, "
              f"CV={consistency['coefficient_of_variation']:.3f}")

    @pytest.mark.skip(reason="Data scaling tests - Performance/stress testing (see notes/issues/by_priority/low/data-scaling-tests.md)")
    def test_memory_usage_stability(self, large_db_session):
        """Test that memory usage remains stable during extended pagination."""
        # Setup large dataset
        self.creator_id = self.stress_tester.setup_large_dataset(LARGE_DATASET_SIZE)

        # Test memory stability
        result = self.stress_tester.test_memory_usage_stability(30)

        assert result["success"], f"Memory stability test failed: {result.get('error')}"
        assert not result["has_potential_leak"], (
            f"Potential memory leak detected: growth {result['memory_growth_mb']:.2f}MB"
        )
        assert result["avg_memory_mb"] < MAX_MEMORY_USAGE_MB, (
            f"Average memory usage {result['avg_memory_mb']:.2f}MB exceeds limit {MAX_MEMORY_USAGE_MB}MB"
        )

        print(f"✓ Memory stability: growth {result['memory_growth_mb']:.2f}MB, "
              f"avg {result['avg_memory_mb']:.2f}MB")


@pytest.mark.stress
@pytest.mark.longrunning
@pytest.mark.skip(reason="Data scaling tests - Performance/stress testing (see notes/issues/by_priority/low/data-scaling-tests.md)")
def test_pagination_performance_benchmarks(large_db_session):
    """Comprehensive benchmark test for pagination performance."""
    print("\n" + "="*80)
    print("PAGINATION PERFORMANCE STRESS TEST SUITE")
    print("="*80)

    stress_tester = StressTester(db_session)

    try:
        # Setup large dataset
        print(f"\n1. Setting up test dataset ({LARGE_DATASET_SIZE:,} records)...")
        creator_id = stress_tester.setup_large_dataset(LARGE_DATASET_SIZE)

        # Test suite results
        results = {}

        # Test 1: Single page performance
        print("\n2. Testing single page performance...")
        results["single_page"] = stress_tester.test_single_page_performance()

        # Test 2: Deep pagination
        print("\n3. Testing deep pagination performance...")
        results["deep_pagination"] = stress_tester.test_deep_pagination_performance(20)

        # Test 3: Concurrent load
        print("\n4. Testing concurrent pagination load...")
        results["concurrent_load"] = stress_tester.test_concurrent_pagination_requests(5)

        # Test 4: Cursor pagination
        print("\n5. Testing cursor pagination performance...")
        results["cursor_pagination"] = stress_tester.test_cursor_pagination_performance()

        # Test 5: Memory stability
        print("\n6. Testing memory usage stability...")
        results["memory_stability"] = stress_tester.test_memory_usage_stability(20)

        # Print comprehensive results
        print("\n" + "="*80)
        print("STRESS TEST RESULTS SUMMARY")
        print("="*80)

        # Single page results
        sp = results["single_page"]
        print(f"Single Page Performance: {sp['response_time_ms']:.2f}ms, {sp['memory_mb']:.2f}MB")

        # Deep pagination results
        dp = results["deep_pagination"]
        print(f"Deep Pagination Performance: avg {dp['avg_response_time']:.2f}ms, "
              f"degradation {dp['performance_degradation']['degradation_factor']:.2f}x")

        # Concurrent load results
        cl = results["concurrent_load"]
        print(f"Concurrent Load Performance: {cl['success_rate']*100:.1f}% success rate, "
              f"avg {cl['avg_response_time_ms']:.2f}ms")

        # Cursor pagination results
        cp = results["cursor_pagination"]
        if cp["success"]:
            consistency = cp["consistent_performance"]
            print(f"Cursor Pagination Performance: avg {cp['avg_response_time']:.2f}ms, "
                  f"consistent: {consistency['consistent']}")

        # Memory stability results
        ms = results["memory_stability"]
        if ms["success"]:
            print(f"Memory Stability: growth {ms['memory_growth_mb']:.2f}MB, "
                  f"leak detected: {ms['has_potential_leak']}")

        print("\n" + "="*80)

        # Overall performance validation
        all_tests_passed = (
            sp["success"] and
            sp["response_time_ms"] < MAX_RESPONSE_TIME_MS and
            dp["performance_degradation"]["degradation_factor"] < 3.0 and
            cl["success_rate"] >= 0.8 and
            cp.get("success", False) and
            ms.get("success", False) and
            not ms.get("has_potential_leak", True)
        )

        if all_tests_passed:
            print("✅ ALL STRESS TESTS PASSED - System ready for production scale!")
        else:
            print("❌ Some stress tests failed - System needs optimization before production")

        assert all_tests_passed, "Pagination stress tests failed - check performance metrics"

    finally:
        # Cleanup
        print("\n7. Cleaning up test dataset...")
        try:
            stress_tester.cleanup_large_dataset(creator_id)
            print("✓ Cleanup completed successfully")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    """Run stress tests directly for development/debugging."""
    # This allows running stress tests independently
    pytest.main([__file__, "-v", "-s", "--tb=short"])