#!/usr/bin/env python3
"""Core functionality tests for tag ontology system.

Tests database connectivity, tag extraction, hierarchy validation,
and basic data integrity.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from genonaut.ontologies.tags.scripts.query_tags import extract_tags_from_json_column, main as query_main
    from genonaut.ontologies.tags.scripts.generate_hierarchy import validate_hierarchy
    from genonaut.ontologies.tags.scripts.curate_final_hierarchy import validate_hierarchy_completeness
except ImportError as e:
    print(f"Warning: Could not import ontology modules: {e}")


class TestDatabaseConnectivity(unittest.TestCase):
    """Test database connection and tag extraction."""

    def test_extract_tags_from_json_column(self):
        """Test tag extraction from JSON column data."""
        # Test valid JSON array
        tags = extract_tags_from_json_column(['art', 'Digital', '  painting  ', 'MODERN'])
        expected = {'art', 'digital', 'painting', 'modern'}
        self.assertEqual(tags, expected)

        # Test empty and invalid inputs
        self.assertEqual(extract_tags_from_json_column([]), set())
        self.assertEqual(extract_tags_from_json_column(None), set())
        self.assertEqual(extract_tags_from_json_column(['', '  ', None]), set())

    @patch('genonaut.ontologies.tags.scripts.query_tags.get_database_session')
    def test_database_query_mock(self, mock_session):
        """Test database query with mocked session."""
        # Mock database session and content items
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Mock content items with tags
        mock_item = MagicMock()
        mock_item.tags = ['art', 'digital', 'painting']
        mock_session_instance.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_item]

        # This would test the actual query logic if we extracted it to a testable function
        # For now, we verify the mock setup works
        session = mock_session()
        items = session.query().filter().limit().all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].tags, ['art', 'digital', 'painting'])


class TestHierarchyValidation(unittest.TestCase):
    """Test hierarchy TSV validation and integrity."""

    def test_validate_hierarchy_format(self):
        """Test TSV format validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            f.write("parent\tchild\n")
            f.write("art\tpainting\n")
            f.write("art\tsculpture\n")
            f.write("painting\toil-painting\n")
            temp_path = f.name

        try:
            errors = validate_hierarchy(Path(temp_path))
            self.assertIsInstance(errors, list)
            # Should have no errors for valid format
            format_errors = [e for e in errors if 'format' in e.lower()]
            self.assertEqual(len(format_errors), 0)
        finally:
            os.unlink(temp_path)

    def test_validate_hierarchy_duplicates(self):
        """Test duplicate relationship detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            f.write("parent\tchild\n")
            f.write("art\tpainting\n")
            f.write("art\tpainting\n")  # Duplicate
            temp_path = f.name

        try:
            errors = validate_hierarchy(Path(temp_path))
            duplicate_errors = [e for e in errors if 'duplicate' in e.lower()]
            self.assertGreater(len(duplicate_errors), 0)
        finally:
            os.unlink(temp_path)

    def test_validate_hierarchy_completeness(self):
        """Test hierarchy completeness validation."""
        # Test complete coverage
        hierarchy = [('art', 'painting'), ('art', 'sculpture'), ('painting', 'oil')]
        all_tags = ['painting', 'sculpture', 'oil']

        validation = validate_hierarchy_completeness(hierarchy, all_tags)

        self.assertEqual(validation['coverage_percent'], 100.0)
        self.assertEqual(len(validation['missing_tags']), 0)
        self.assertEqual(validation['unique_children'], 3)

        # Test incomplete coverage
        incomplete_hierarchy = [('art', 'painting')]
        all_tags = ['painting', 'sculpture', 'oil']

        validation = validate_hierarchy_completeness(incomplete_hierarchy, all_tags)

        self.assertLess(validation['coverage_percent'], 100.0)
        self.assertEqual(len(validation['missing_tags']), 2)
        self.assertIn('sculpture', validation['missing_tags'])
        self.assertIn('oil', validation['missing_tags'])


class TestTagNormalization(unittest.TestCase):
    """Test tag normalization and data quality."""

    def test_tag_normalization(self):
        """Test tag normalization to lowercase and whitespace removal."""
        test_cases = [
            ('Art', 'art'),
            ('  PAINTING  ', 'painting'),
            ('Digital-Art', 'digital-art'),
            ('3D', '3d'),
            ('sci-fi', 'sci-fi'),
        ]

        for input_tag, expected in test_cases:
            # Test the normalization logic from extract_tags_from_json_column
            tags = extract_tags_from_json_column([input_tag])
            self.assertEqual(tags, {expected})

    def test_special_characters(self):
        """Test handling of special characters in tags."""
        special_tags = ['bird\'s-eye', 'high-detail', '3d-render', 'cel-shaded']

        for tag in special_tags:
            tags = extract_tags_from_json_column([tag])
            self.assertEqual(len(tags), 1)
            extracted_tag = list(tags)[0]
            # Should preserve hyphens and apostrophes but normalize case
            self.assertEqual(extracted_tag, tag.lower().strip())


class TestHierarchyStructure(unittest.TestCase):
    """Test hierarchy structure and organization."""

    def test_root_categories_validation(self):
        """Test that required root categories exist."""
        expected_roots = ['visual_aesthetics', 'technical_execution', 'artistic_medium', 'content_classification']

        # Read actual hierarchy file
        hierarchy_file = Path(__file__).parent.parent / "data" / "hierarchy.tsv"

        if hierarchy_file.exists():
            parents = set()
            children = set()

            with open(hierarchy_file, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        parents.add(parts[0])
                        children.add(parts[1])

            # Root categories should be parents but not children
            actual_roots = parents - children

            for expected_root in expected_roots:
                self.assertIn(expected_root, parents, f"Root category '{expected_root}' should exist as a parent")

    def test_hierarchy_depth(self):
        """Test that hierarchy doesn't exceed reasonable depth."""
        hierarchy_file = Path(__file__).parent.parent / "data" / "hierarchy.tsv"

        if hierarchy_file.exists():
            # Build adjacency list
            children_map = {}
            with open(hierarchy_file, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        parent, child = parts
                        if parent not in children_map:
                            children_map[parent] = []
                        children_map[parent].append(child)

            # Calculate max depth using DFS
            def max_depth(node, current_depth=0):
                if node not in children_map:
                    return current_depth
                return max(current_depth, max(max_depth(child, current_depth + 1)
                                            for child in children_map[node]))

            # Find roots (nodes that are not children)
            all_children = set()
            all_parents = set()
            for parent, children_list in children_map.items():
                all_parents.add(parent)
                all_children.update(children_list)

            roots = all_parents - all_children

            # Test that max depth is reasonable (should be <= 4 levels)
            for root in roots:
                depth = max_depth(root)
                self.assertLessEqual(depth, 4, f"Hierarchy depth for root '{root}' exceeds 4 levels")


if __name__ == '__main__':
    unittest.main()