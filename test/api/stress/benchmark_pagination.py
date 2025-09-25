#!/usr/bin/env python3
"""
Performance benchmarking script for pagination endpoints.

This script provides standalone benchmarking capabilities for:
- API endpoint response times
- Database query performance
- Memory usage patterns
- Concurrent request handling

Usage:
    python benchmark_pagination.py --dataset-size 50000 --concurrent-requests 10
"""

import argparse
import asyncio
import json
import sys
import time
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import psutil
from tabulate import tabulate

# Configuration
DEFAULT_BASE_URL = "http://localhost:8002"
DEFAULT_DATASET_SIZE = 10000
DEFAULT_CONCURRENT_REQUESTS = 5
DEFAULT_PAGE_SIZE = 50


@dataclass
class BenchmarkResult:
    """Data class to store benchmark results."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    requests_per_second: float
    avg_memory_usage_mb: float
    errors: List[str]
    additional_metrics: Dict[str, Any]


class PaginationBenchmarker:
    """Main benchmarking class for pagination performance."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a single HTTP request and measure performance."""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params or {})

            end_time = time.time()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024

            response_time_ms = (end_time - start_time) * 1000
            memory_usage_mb = (memory_before + memory_after) / 2

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "memory_usage_mb": memory_usage_mb,
                    "content_length": len(response.content),
                    "item_count": len(data.get("items", [])),
                    "total_count": data.get("pagination", {}).get("total_count", 0)
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "memory_usage_mb": memory_usage_mb,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }

        except Exception as e:
            end_time = time.time()
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024

            return {
                "success": False,
                "response_time_ms": (end_time - start_time) * 1000,
                "memory_usage_mb": (memory_before + memory_after) / 2,
                "error": str(e)
            }

    def benchmark_single_endpoint(
        self,
        endpoint: str,
        params_list: List[Dict[str, Any]],
        test_name: str
    ) -> BenchmarkResult:
        """Benchmark a single endpoint with multiple parameter sets."""
        print(f"Benchmarking {test_name}...")

        results = []

        for i, params in enumerate(params_list):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(params_list)} requests")

            result = self.make_request(endpoint, params)
            results.append(result)

        return self._analyze_results(test_name, results)

    def benchmark_concurrent_requests(
        self,
        endpoint: str,
        params: Dict[str, Any],
        num_concurrent: int,
        test_name: str
    ) -> BenchmarkResult:
        """Benchmark concurrent requests to the same endpoint."""
        print(f"Benchmarking {test_name} with {num_concurrent} concurrent requests...")

        def make_concurrent_request():
            return self.make_request(endpoint, params)

        results = []

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_concurrent_request) for _ in range(num_concurrent)]

            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 5 == 0:
                    print(f"  Progress: {i + 1}/{num_concurrent} requests completed")

                result = future.result()
                results.append(result)

        return self._analyze_results(test_name, results)

    def benchmark_pagination_depth(
        self,
        endpoint: str,
        base_params: Dict[str, Any],
        max_pages: int,
        test_name: str
    ) -> BenchmarkResult:
        """Benchmark pagination performance at different page depths."""
        print(f"Benchmarking {test_name} across {max_pages} pages...")

        results = []

        for page in range(1, max_pages + 1):
            params = {**base_params, "page": page}
            result = self.make_request(endpoint, params)
            results.append(result)

            if page % 10 == 0:
                print(f"  Progress: page {page}/{max_pages}")

        return self._analyze_results(test_name, results)

    def _analyze_results(self, test_name: str, results: List[Dict[str, Any]]) -> BenchmarkResult:
        """Analyze benchmark results and return summary statistics."""
        successful_results = [r for r in results if r.get("success")]
        failed_results = [r for r in results if not r.get("success")]

        if not results:
            return BenchmarkResult(
                test_name=test_name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0,
                median_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                max_response_time_ms=0,
                min_response_time_ms=0,
                requests_per_second=0,
                avg_memory_usage_mb=0,
                errors=[],
                additional_metrics={}
            )

        # Response time statistics
        response_times = [r["response_time_ms"] for r in successful_results]
        memory_usage = [r["memory_usage_mb"] for r in results]

        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            requests_per_second = 1000 / avg_response_time if avg_response_time > 0 else 0
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = requests_per_second = 0

        avg_memory = statistics.mean(memory_usage) if memory_usage else 0

        errors = [r.get("error", "") for r in failed_results if r.get("error")]

        # Additional metrics
        additional_metrics = {}
        if successful_results:
            # Content size statistics
            content_sizes = [r.get("content_length", 0) for r in successful_results]
            if content_sizes:
                additional_metrics["avg_content_size_bytes"] = statistics.mean(content_sizes)

            # Item count statistics
            item_counts = [r.get("item_count", 0) for r in successful_results]
            if item_counts:
                additional_metrics["avg_items_per_page"] = statistics.mean(item_counts)

            # Total count (if available)
            total_counts = [r.get("total_count", 0) for r in successful_results if r.get("total_count")]
            if total_counts:
                additional_metrics["dataset_total_count"] = total_counts[0]

        return BenchmarkResult(
            test_name=test_name,
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time_ms=avg_response_time,
            median_response_time_ms=median_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            requests_per_second=requests_per_second,
            avg_memory_usage_mb=avg_memory,
            errors=errors[:5],  # Limit to first 5 errors
            additional_metrics=additional_metrics
        )

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


def print_benchmark_results(results: List[BenchmarkResult]):
    """Print benchmark results in a formatted table."""
    print("\n" + "="*120)
    print("PAGINATION BENCHMARKING RESULTS")
    print("="*120)

    # Summary table
    table_data = []
    for result in results:
        success_rate = result.successful_requests / result.total_requests * 100 if result.total_requests > 0 else 0
        table_data.append([
            result.test_name[:30],
            result.total_requests,
            f"{success_rate:.1f}%",
            f"{result.avg_response_time_ms:.2f}ms",
            f"{result.p95_response_time_ms:.2f}ms",
            f"{result.requests_per_second:.1f}",
            f"{result.avg_memory_usage_mb:.1f}MB"
        ])

    headers = ["Test Name", "Requests", "Success %", "Avg Time", "P95 Time", "Req/Sec", "Avg Memory"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Detailed results for each test
    for result in results:
        if result.failed_requests > 0 or result.errors:
            print(f"\n📊 Detailed Results: {result.test_name}")
            print(f"  Total Requests: {result.total_requests}")
            print(f"  Successful: {result.successful_requests}")
            print(f"  Failed: {result.failed_requests}")

            if result.errors:
                print(f"  Sample Errors:")
                for error in result.errors[:3]:
                    print(f"    - {error}")

            if result.additional_metrics:
                print(f"  Additional Metrics:")
                for key, value in result.additional_metrics.items():
                    if isinstance(value, float):
                        print(f"    - {key}: {value:.2f}")
                    else:
                        print(f"    - {key}: {value}")


def main():
    """Main benchmarking function."""
    parser = argparse.ArgumentParser(description="Pagination API Benchmarking Tool")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for API")
    parser.add_argument("--dataset-size", type=int, default=DEFAULT_DATASET_SIZE,
                       help="Expected dataset size for testing")
    parser.add_argument("--concurrent-requests", type=int, default=DEFAULT_CONCURRENT_REQUESTS,
                       help="Number of concurrent requests for load testing")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE,
                       help="Page size for pagination requests")
    parser.add_argument("--max-pages", type=int, default=20,
                       help="Maximum pages to test for deep pagination")
    parser.add_argument("--output", help="Output file for JSON results")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    if not args.quiet:
        print("Starting pagination benchmarking...")
        print(f"Base URL: {args.base_url}")
        print(f"Dataset Size: {args.dataset_size:,}")
        print(f"Concurrent Requests: {args.concurrent_requests}")
        print(f"Page Size: {args.page_size}")

    benchmarker = PaginationBenchmarker(args.base_url)

    # Test scenarios
    results = []

    # 1. Basic pagination performance
    basic_params = [{"page": 1, "page_size": args.page_size}]
    results.append(benchmarker.benchmark_single_endpoint(
        "/api/v1/content/enhanced",
        basic_params,
        "Basic Pagination"
    ))

    # 2. Deep pagination performance
    results.append(benchmarker.benchmark_pagination_depth(
        "/api/v1/content/enhanced",
        {"page_size": args.page_size},
        min(args.max_pages, args.dataset_size // args.page_size),
        "Deep Pagination"
    ))

    # 3. Concurrent request performance
    results.append(benchmarker.benchmark_concurrent_requests(
        "/api/v1/content/enhanced",
        {"page": 1, "page_size": args.page_size},
        args.concurrent_requests,
        "Concurrent Load"
    ))

    # 4. Different page sizes
    page_size_params = [
        {"page": 1, "page_size": 10},
        {"page": 1, "page_size": 50},
        {"page": 1, "page_size": 100},
        {"page": 1, "page_size": 200}
    ]
    results.append(benchmarker.benchmark_single_endpoint(
        "/api/v1/content/enhanced",
        page_size_params,
        "Variable Page Sizes"
    ))

    # 5. Search performance
    search_params = [
        {"page": 1, "page_size": args.page_size, "search_term": "test"},
        {"page": 1, "page_size": args.page_size, "search_term": "content"},
        {"page": 1, "page_size": args.page_size, "search_term": "item"}
    ]
    results.append(benchmarker.benchmark_single_endpoint(
        "/api/v1/content/enhanced",
        search_params,
        "Search Performance"
    ))

    # 6. Sorting performance
    sort_params = [
        {"page": 1, "page_size": args.page_size, "sort_field": "created_at", "sort_order": "desc"},
        {"page": 1, "page_size": args.page_size, "sort_field": "quality_score", "sort_order": "desc"},
        {"page": 1, "page_size": args.page_size, "sort_field": "created_at", "sort_order": "asc"}
    ]
    results.append(benchmarker.benchmark_single_endpoint(
        "/api/v1/content/enhanced",
        sort_params,
        "Sorting Performance"
    ))

    # Print results
    print_benchmark_results(results)

    # Save results to file if specified
    if args.output:
        output_data = {
            "benchmark_config": {
                "base_url": args.base_url,
                "dataset_size": args.dataset_size,
                "concurrent_requests": args.concurrent_requests,
                "page_size": args.page_size,
                "max_pages": args.max_pages,
                "timestamp": time.time()
            },
            "results": [asdict(result) for result in results]
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n📁 Results saved to: {args.output}")

    # Performance validation
    critical_failures = []

    for result in results:
        if result.avg_response_time_ms > 500:  # 500ms threshold
            critical_failures.append(f"{result.test_name}: avg response time {result.avg_response_time_ms:.2f}ms")

        if result.successful_requests / result.total_requests < 0.95:  # 95% success rate threshold
            success_rate = result.successful_requests / result.total_requests * 100
            critical_failures.append(f"{result.test_name}: success rate {success_rate:.1f}%")

    if critical_failures:
        print("\n❌ PERFORMANCE ISSUES DETECTED:")
        for failure in critical_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("\n✅ ALL BENCHMARKS PASSED - Performance within acceptable limits")


if __name__ == "__main__":
    main()