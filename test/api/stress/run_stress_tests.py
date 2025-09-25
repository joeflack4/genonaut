#!/usr/bin/env python3
"""
Convenience script to run pagination stress tests with different configurations.

This script provides presets for different testing scenarios:
- Development: Quick tests with small datasets
- CI: Medium tests suitable for continuous integration
- Production: Full stress tests with large datasets
"""

import os
import sys
import subprocess
import argparse
from typing import Dict, List


# Test configurations
CONFIGURATIONS = {
    "development": {
        "description": "Quick development tests",
        "dataset_size": 1000,
        "concurrent_requests": 3,
        "max_pages": 5,
        "pytest_args": ["-v", "--tb=short"]
    },
    "ci": {
        "description": "CI/CD pipeline tests",
        "dataset_size": 10000,
        "concurrent_requests": 5,
        "max_pages": 10,
        "pytest_args": ["-v", "--tb=short", "--durations=10"]
    },
    "production": {
        "description": "Full production stress tests",
        "dataset_size": 100000,
        "concurrent_requests": 10,
        "max_pages": 50,
        "pytest_args": ["-v", "-s", "--tb=short", "--durations=20"]
    },
    "custom": {
        "description": "Custom configuration (specify parameters)",
        "dataset_size": None,  # Will be set via command line
        "concurrent_requests": None,
        "max_pages": None,
        "pytest_args": ["-v", "--tb=short"]
    }
}


def run_stress_tests(
    config_name: str,
    custom_dataset_size: int = None,
    custom_concurrent: int = None,
    custom_max_pages: int = None,
    pytest_extra_args: List[str] = None
) -> int:
    """Run stress tests with specified configuration."""

    if config_name not in CONFIGURATIONS:
        print(f"❌ Unknown configuration: {config_name}")
        print(f"Available configurations: {', '.join(CONFIGURATIONS.keys())}")
        return 1

    config = CONFIGURATIONS[config_name].copy()

    # Handle custom configuration
    if config_name == "custom":
        if custom_dataset_size is None:
            print("❌ Custom configuration requires --dataset-size")
            return 1
        config["dataset_size"] = custom_dataset_size
        config["concurrent_requests"] = custom_concurrent or 5
        config["max_pages"] = custom_max_pages or 10

    print(f"🚀 Running {config['description']}")
    print(f"   Dataset Size: {config['dataset_size']:,}")
    print(f"   Concurrent Requests: {config['concurrent_requests']}")
    print(f"   Max Pages: {config['max_pages']}")

    # Set environment variables for the stress tests
    env = os.environ.copy()
    env.update({
        "STRESS_TEST_DATASET_SIZE": str(config["dataset_size"]),
        "STRESS_TEST_CONCURRENT_REQUESTS": str(config["concurrent_requests"]),
        "STRESS_TEST_MAX_PAGES": str(config["max_pages"])
    })

    # Build pytest command
    pytest_cmd = [
        "python", "-m", "pytest",
        "test/api/stress/test_pagination_stress.py",
        "-m", "stress"
    ] + config["pytest_args"]

    if pytest_extra_args:
        pytest_cmd.extend(pytest_extra_args)

    print(f"🔧 Command: {' '.join(pytest_cmd)}")
    print("-" * 80)

    # Run the tests
    try:
        result = subprocess.run(pytest_cmd, env=env, cwd=os.getcwd())
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_benchmark(
    base_url: str = "http://localhost:8002",
    dataset_size: int = 10000,
    concurrent_requests: int = 5,
    output_file: str = None
) -> int:
    """Run the standalone benchmark script."""

    print(f"📊 Running pagination benchmarks...")
    print(f"   Base URL: {base_url}")
    print(f"   Dataset Size: {dataset_size:,}")
    print(f"   Concurrent Requests: {concurrent_requests}")

    benchmark_cmd = [
        "python", "test/api/stress/benchmark_pagination.py",
        "--base-url", base_url,
        "--dataset-size", str(dataset_size),
        "--concurrent-requests", str(concurrent_requests)
    ]

    if output_file:
        benchmark_cmd.extend(["--output", output_file])

    print(f"🔧 Command: {' '.join(benchmark_cmd)}")
    print("-" * 80)

    try:
        result = subprocess.run(benchmark_cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running benchmark: {e}")
        return 1


def main():
    """Main function to handle command line arguments and run tests."""

    parser = argparse.ArgumentParser(
        description="Run pagination stress tests and benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available test configurations:
  development : Quick tests for local development (1K records)
  ci          : Medium tests for CI/CD pipelines (10K records)
  production  : Full stress tests for production validation (100K records)
  custom      : Custom configuration (specify your own parameters)

Examples:
  python run_stress_tests.py --config development
  python run_stress_tests.py --config custom --dataset-size 50000
  python run_stress_tests.py --benchmark --base-url http://localhost:8002
        """
    )

    # Test configuration options
    parser.add_argument(
        "--config", "-c",
        choices=list(CONFIGURATIONS.keys()),
        default="development",
        help="Test configuration preset"
    )

    # Custom configuration options
    parser.add_argument(
        "--dataset-size",
        type=int,
        help="Dataset size for custom configuration"
    )

    parser.add_argument(
        "--concurrent-requests",
        type=int,
        help="Number of concurrent requests for custom configuration"
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum pages to test for custom configuration"
    )

    # Benchmark options
    parser.add_argument(
        "--benchmark", "-b",
        action="store_true",
        help="Run standalone benchmark instead of stress tests"
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8002",
        help="Base URL for benchmark testing"
    )

    parser.add_argument(
        "--benchmark-output",
        help="Output file for benchmark results"
    )

    # Additional pytest arguments
    parser.add_argument(
        "--pytest-args",
        help="Additional arguments to pass to pytest (space-separated)"
    )

    # List configurations
    parser.add_argument(
        "--list-configs", "-l",
        action="store_true",
        help="List available test configurations"
    )

    args = parser.parse_args()

    if args.list_configs:
        print("📋 Available test configurations:")
        for name, config in CONFIGURATIONS.items():
            print(f"\n  {name}:")
            print(f"    Description: {config['description']}")
            if config['dataset_size']:
                print(f"    Dataset Size: {config['dataset_size']:,}")
                print(f"    Concurrent Requests: {config['concurrent_requests']}")
                print(f"    Max Pages: {config['max_pages']}")
        return 0

    pytest_extra_args = []
    if args.pytest_args:
        pytest_extra_args = args.pytest_args.split()

    if args.benchmark:
        # Run benchmark
        return run_benchmark(
            base_url=args.base_url,
            dataset_size=args.dataset_size or 10000,
            concurrent_requests=args.concurrent_requests or 5,
            output_file=args.benchmark_output
        )
    else:
        # Run stress tests
        return run_stress_tests(
            config_name=args.config,
            custom_dataset_size=args.dataset_size,
            custom_concurrent=args.concurrent_requests,
            custom_max_pages=args.max_pages,
            pytest_extra_args=pytest_extra_args
        )


if __name__ == "__main__":
    sys.exit(main())