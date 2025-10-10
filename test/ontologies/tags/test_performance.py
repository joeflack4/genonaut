#!/usr/bin/env python3
"""Performance tests for tag ontology system.

Tests performance with large datasets, memory usage,
and execution time constraints.
"""

import unittest
import sys
import time
import psutil
import os
import pytest
from pathlib import Path
import tempfile
from unittest import mock

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.ontology_perf
class TestLargeDatasetHandling(unittest.TestCase):
    """Test performance with large datasets."""

    def test_large_tag_extraction_performance(self):
        """Test tag extraction with large number of tags."""
        try:
            from genonaut.ontologies.tags.scripts.query_tags import extract_tags_from_json_column
        except ImportError:
            self.skipTest("Could not import tag extraction function")

        # Create a large set of tags
        large_tag_set = []
        for i in range(1000):
            large_tag_set.extend([
                f'tag_{i}',
                f'category_{i}',
                f'style_{i}',
                f'technique_{i}'
            ])

        start_time = time.time()

        # Extract tags (simulating database result)
        result = extract_tags_from_json_column(large_tag_set)

        execution_time = time.time() - start_time

        # Should complete reasonably quickly (< 1 second for 4000 tags)
        self.assertLess(execution_time, 1.0, f"Tag extraction took {execution_time:.3f}s, should be < 1s")

        # Should handle all tags
        self.assertEqual(len(result), 4000)

    def test_hierarchy_validation_performance(self):
        """Test hierarchy validation with large hierarchy."""
        try:
            from genonaut.ontologies.tags.scripts.generate_hierarchy import validate_hierarchy
        except ImportError:
            self.skipTest("Could not import validation function")

        # Create large hierarchy file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            f.write("parent\tchild\n")

            # Create a deep, wide hierarchy
            for i in range(100):
                f.write(f"root_{i}\tmiddle_{i}\n")
                for j in range(10):
                    f.write(f"middle_{i}\tleaf_{i}_{j}\n")

            temp_path = f.name

        try:
            start_time = time.time()

            errors = validate_hierarchy(Path(temp_path))

            execution_time = time.time() - start_time

            # Should complete reasonably quickly (< 2 seconds for 1100 relationships)
            self.assertLess(execution_time, 2.0, f"Validation took {execution_time:.3f}s, should be < 2s")

            # Should return error list
            self.assertIsInstance(errors, list)

        finally:
            os.unlink(temp_path)

    def test_pattern_analysis_performance(self):
        """Test pattern analysis with many tags."""
        try:
            from genonaut.ontologies.tags.scripts.analyze_tag_patterns import analyze_linguistic_patterns
        except ImportError:
            self.skipTest("Could not import pattern analysis function")

        # Create large tag set with various patterns
        large_tag_set = []
        for i in range(500):
            large_tag_set.extend([
                f'compound-term-{i}',
                f'single{i}',
                f'{i}d',  # dimensional
                f'{i}k',  # quality
                f'style_{i}',
                f'material_{i}'
            ])

        start_time = time.time()

        patterns = analyze_linguistic_patterns(large_tag_set)

        execution_time = time.time() - start_time

        # Should complete reasonably quickly
        self.assertLess(execution_time, 5.0, f"Pattern analysis took {execution_time:.3f}s, should be < 5s")

        # Should detect patterns
        self.assertIsInstance(patterns, dict)
        self.assertGreater(len(patterns), 0)


@pytest.mark.ontology_perf
class TestMemoryUsage(unittest.TestCase):
    """Test memory usage and efficiency."""

    def setUp(self):
        """Set up memory monitoring."""
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss

    def test_tag_processing_memory_usage(self):
        """Test memory usage during tag processing."""
        try:
            from genonaut.ontologies.tags.scripts.query_tags import extract_tags_from_json_column
        except ImportError:
            self.skipTest("Could not import tag extraction function")

        # Process progressively larger tag sets and monitor memory
        memory_usage = []

        for size in [100, 500, 1000, 2000]:
            # Create tag set
            tag_set = [f'tag_{i}' for i in range(size)]

            # Monitor memory before processing
            memory_before = self.process.memory_info().rss

            # Process tags
            result = extract_tags_from_json_column(tag_set)

            # Monitor memory after processing
            memory_after = self.process.memory_info().rss
            memory_increase = memory_after - memory_before

            memory_usage.append((size, memory_increase))

            # Clean up
            del result
            del tag_set

        # Memory usage should grow roughly linearly, not exponentially
        if len(memory_usage) >= 3:
            # Check that memory usage doesn't grow exponentially
            # Allow for some variation but detect major leaks
            positive_usages = [usage[1] for usage in memory_usage if usage[1] > 0]

            if len(positive_usages) >= 2:
                max_usage = max(positive_usages)
                min_usage = min(positive_usages)

                growth_factor = max_usage / min_usage
                # Memory shouldn't grow by more than 100x for reasonable input increases
                self.assertLess(growth_factor, 100,
                              f"Memory usage grew by {growth_factor:.1f}x, indicating possible memory leak")
            # If all memory changes are 0 or negative, that's actually good (no growth)

    def test_hierarchy_generation_memory_efficiency(self):
        """Test memory efficiency of hierarchy generation."""
        initial_memory = self.process.memory_info().rss

        try:
            from genonaut.ontologies.tags.scripts.curate_final_hierarchy import create_curated_hierarchy
        except ImportError:
            self.skipTest("Could not import hierarchy generation function")

        # Generate hierarchy
        hierarchy = create_curated_hierarchy()

        peak_memory = self.process.memory_info().rss
        memory_increase = peak_memory - initial_memory

        # Should not use excessive memory (< 50MB for reasonable hierarchy)
        memory_increase_mb = memory_increase / (1024 * 1024)
        self.assertLess(memory_increase_mb, 50,
                       f"Hierarchy generation used {memory_increase_mb:.1f}MB, should be < 50MB")

        # Clean up
        del hierarchy


@pytest.mark.ontology_perf
class TestExecutionTime(unittest.TestCase):
    """Test execution time constraints."""

    def test_query_execution_time(self):
        """Test that database queries complete within reasonable time."""
        # Mock database session to simulate query time
        with mock.patch('genonaut.ontologies.tags.scripts.query_tags.get_database_session') as mock_session:
            mock_session_instance = mock.MagicMock()
            mock_session.return_value = mock_session_instance

            # Mock content items
            mock_items = []
            for i in range(100):
                mock_item = mock.MagicMock()
                mock_item.tags = [f'tag_{i}', f'category_{i%10}']
                mock_items.append(mock_item)

            mock_session_instance.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_items

            try:
                from genonaut.ontologies.tags.scripts.query_tags import extract_tags_from_json_column

                start_time = time.time()

                # Process mock data
                all_tags = set()
                for item in mock_items:
                    tags = extract_tags_from_json_column(item.tags)
                    all_tags.update(tags)

                execution_time = time.time() - start_time

                # Should complete quickly
                self.assertLess(execution_time, 0.5, f"Query processing took {execution_time:.3f}s, should be < 0.5s")

            except ImportError:
                self.skipTest("Could not import query functions")

    def test_validation_speed(self):
        """Test validation speed with various hierarchy sizes."""
        try:
            from genonaut.ontologies.tags.scripts.generate_hierarchy import validate_hierarchy
        except ImportError:
            self.skipTest("Could not import validation function")

        execution_times = []

        for size in [10, 50, 100, 200]:
            # Create hierarchy of given size
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
                f.write("parent\tchild\n")
                for i in range(size):
                    f.write(f"parent_{i}\tchild_{i}\n")
                temp_path = f.name

            try:
                start_time = time.time()
                errors = validate_hierarchy(Path(temp_path))
                execution_time = time.time() - start_time

                execution_times.append((size, execution_time))

                # Individual validation should be fast
                self.assertLess(execution_time, 1.0,
                              f"Validation of {size} relationships took {execution_time:.3f}s, should be < 1s")

            finally:
                os.unlink(temp_path)

        # Validate that execution time scales reasonably
        if len(execution_times) >= 2:
            # Should not have exponential growth
            last_ratio = execution_times[-1][1] / max(execution_times[0][1], 0.001)
            size_ratio = execution_times[-1][0] / execution_times[0][0]

            # Time ratio should not exceed size ratio by too much
            self.assertLess(last_ratio / size_ratio, 5,
                          "Validation time appears to scale worse than linearly")


@pytest.mark.ontology_perf
class TestConcurrentAccess(unittest.TestCase):
    """Test concurrent access and thread safety."""

    def test_file_read_safety(self):
        """Test that multiple concurrent reads are safe."""
        import threading
        import random

        hierarchy_file = Path(__file__).parent.parent / "data" / "hierarchy.tsv"

        if not hierarchy_file.exists():
            self.skipTest("Hierarchy file not found")

        results = []
        errors = []

        def read_hierarchy():
            """Read hierarchy file."""
            try:
                time.sleep(random.uniform(0, 0.1))  # Random delay
                with open(hierarchy_file, 'r') as f:
                    lines = f.readlines()
                    results.append(len(lines))
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=read_hierarchy)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)

        # All reads should succeed
        self.assertEqual(len(errors), 0, f"Concurrent read errors: {errors}")
        self.assertEqual(len(results), 5, "Not all reads completed")

        # All reads should return the same result
        self.assertEqual(len(set(results)), 1, "Concurrent reads returned different results")


if __name__ == '__main__':
    # Only run performance tests if psutil is available
    try:
        import psutil
        unittest.main()
    except ImportError:
        print("Warning: psutil not available, skipping performance tests")
        # Run basic tests without memory monitoring
        suite = unittest.TestSuite()
        suite.addTest(TestLargeDatasetHandling('test_large_tag_extraction_performance'))
        suite.addTest(TestExecutionTime('test_query_execution_time'))
        runner = unittest.TextTestRunner()
        runner.run(suite)
