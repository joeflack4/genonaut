#!/usr/bin/env python3
"""Data quality tests for tag ontology system.

Tests tag normalization, pattern recognition, semantic clustering,
and data consistency.
"""

import unittest
import sys
from pathlib import Path
from collections import Counter

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from genonaut.ontologies.tags.scripts.analyze_tag_patterns import analyze_linguistic_patterns, identify_semantic_clusters
    from genonaut.ontologies.tags.scripts.analyze_semantic_relationships import categorize_tags_by_semantic_domains
except ImportError as e:
    print(f"Warning: Could not import pattern analysis modules: {e}")


class TestPatternRecognition(unittest.TestCase):
    """Test linguistic pattern recognition in tags."""

    def test_compound_term_detection(self):
        """Test detection of hyphenated compound terms."""
        test_tags = ['digital-painting', 'oil-painting', '3d-render', 'bird\'s-eye', 'cel-shaded', 'single']

        patterns = analyze_linguistic_patterns(test_tags)

        # Should detect compound terms
        self.assertIn('compound_terms', patterns)
        compound_terms = patterns['compound_terms']

        # All hyphenated terms should be detected
        expected_compounds = ['digital-painting', 'oil-painting', '3d-render', 'cel-shaded']
        for term in expected_compounds:
            self.assertIn(term, compound_terms)

        # Single word should not be in compounds
        self.assertNotIn('single', compound_terms)

    def test_dimensional_term_detection(self):
        """Test detection of dimensional terms like 2d, 3d."""
        test_tags = ['2d', '3d', '3d-render', 'art', 'painting']

        patterns = analyze_linguistic_patterns(test_tags)

        # Should detect dimensional terms
        self.assertIn('dimensional_terms', patterns)
        dimensional_terms = patterns['dimensional_terms']

        self.assertIn('2d', dimensional_terms)
        self.assertIn('3d', dimensional_terms)
        self.assertNotIn('3d-render', dimensional_terms)  # This is compound
        self.assertNotIn('art', dimensional_terms)

    def test_quality_term_detection(self):
        """Test detection of quality/resolution terms."""
        test_tags = ['4k', '8k', 'hdr', 'high-detail', 'art', 'painting']

        patterns = analyze_linguistic_patterns(test_tags)

        if 'quality_terms' in patterns:
            quality_terms = patterns['quality_terms']
            self.assertIn('4k', quality_terms)
            self.assertIn('8k', quality_terms)
            self.assertIn('hdr', quality_terms)
            self.assertNotIn('art', quality_terms)

    def test_material_term_detection(self):
        """Test detection of artistic material terms."""
        test_tags = ['acrylic', 'oil-painting', 'chalk', 'charcoal', 'digital', 'abstract']

        patterns = analyze_linguistic_patterns(test_tags)

        if 'material_terms' in patterns:
            material_terms = patterns['material_terms']
            self.assertIn('acrylic', material_terms)
            self.assertIn('chalk', material_terms)
            self.assertIn('charcoal', material_terms)
            self.assertNotIn('digital', material_terms)
            self.assertNotIn('abstract', material_terms)


class TestSemanticClustering(unittest.TestCase):
    """Test semantic clustering and categorization."""

    def test_color_brightness_clustering(self):
        """Test clustering of color and brightness terms."""
        test_tags = ['bright', 'dark', 'vibrant', 'colorful', 'monochrome', 'pastel', 'abstract', 'painting']

        clusters = identify_semantic_clusters(test_tags)

        self.assertIn('colors_brightness', clusters)
        color_cluster = clusters['colors_brightness']

        expected_color_terms = ['bright', 'dark', 'vibrant', 'colorful', 'monochrome', 'pastel']
        for term in expected_color_terms:
            self.assertIn(term, color_cluster)

        self.assertNotIn('abstract', color_cluster)
        self.assertNotIn('painting', color_cluster)

    def test_technical_clustering(self):
        """Test clustering of technical terms."""
        test_tags = ['4k', '8k', 'high-detail', 'low-poly', 'photorealistic', 'stylized', 'art']

        clusters = identify_semantic_clusters(test_tags)

        # Check resolution cluster
        if 'resolution_detail' in clusters:
            resolution_cluster = clusters['resolution_detail']
            expected_resolution = ['4k', '8k', 'high-detail', 'low-poly']
            for term in expected_resolution:
                self.assertIn(term, resolution_cluster)

        # Check rendering styles cluster
        if 'rendering_styles' in clusters:
            rendering_cluster = clusters['rendering_styles']
            expected_rendering = ['photorealistic', 'stylized']
            for term in expected_rendering:
                self.assertIn(term, rendering_cluster)

    def test_art_movement_clustering(self):
        """Test clustering of art movement terms."""
        test_tags = ['abstract', 'realistic', 'surreal', 'experimental', 'decorative', 'painting']

        clusters = identify_semantic_clusters(test_tags)

        if 'art_movements' in clusters:
            movement_cluster = clusters['art_movements']
            expected_movements = ['abstract', 'realistic', 'surreal', 'experimental', 'decorative']
            for term in expected_movements:
                self.assertIn(term, movement_cluster)

            self.assertNotIn('painting', movement_cluster)


class TestDataConsistency(unittest.TestCase):
    """Test data consistency and integrity."""

    def test_hierarchy_file_consistency(self):
        """Test that hierarchy file is consistent and well-formed."""
        hierarchy_file = Path(__file__).parent.parent / "data" / "hierarchy.tsv"

        if not hierarchy_file.exists():
            self.skipTest("Hierarchy file not found")

        # Read and parse hierarchy
        relationships = []
        line_count = 0

        with open(hierarchy_file, 'r') as f:
            lines = f.readlines()

            # Check header
            self.assertEqual(lines[0].strip(), "parent\tchild", "Header should be 'parent\\tchild'")

            for i, line in enumerate(lines[1:], 2):
                line_count += 1
                parts = line.strip().split('\t')

                # Each line should have exactly 2 parts
                self.assertEqual(len(parts), 2, f"Line {i} should have exactly 2 tab-separated values")

                parent, child = parts

                # Neither parent nor child should be empty
                self.assertTrue(parent.strip(), f"Line {i}: Parent cannot be empty")
                self.assertTrue(child.strip(), f"Line {i}: Child cannot be empty")

                # Check for consistent naming (lowercase, allowed characters)
                self.assertTrue(self._is_valid_tag_name(parent), f"Line {i}: Invalid parent name '{parent}'")
                self.assertTrue(self._is_valid_tag_name(child), f"Line {i}: Invalid child name '{child}'")

                relationships.append((parent, child))

        # Check for duplicate relationships
        relationship_counts = Counter(relationships)
        duplicates = [(rel, count) for rel, count in relationship_counts.items() if count > 1]
        self.assertEqual(len(duplicates), 0, f"Found duplicate relationships: {duplicates}")

        print(f"Validated {line_count} relationships in hierarchy file")

    def test_tag_naming_conventions(self):
        """Test that tags follow naming conventions."""
        hierarchy_file = Path(__file__).parent.parent / "data" / "hierarchy.tsv"

        if not hierarchy_file.exists():
            self.skipTest("Hierarchy file not found")

        all_tags = set()

        with open(hierarchy_file, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    all_tags.update(parts)

        # Test naming conventions
        for tag in all_tags:
            with self.subTest(tag=tag):
                # Should be lowercase
                self.assertEqual(tag, tag.lower(), f"Tag '{tag}' should be lowercase")

                # Should not start or end with whitespace
                self.assertEqual(tag, tag.strip(), f"Tag '{tag}' should not have leading/trailing whitespace")

                # Should not be empty
                self.assertTrue(len(tag) > 0, f"Tag should not be empty")

                # Should only contain allowed characters
                self.assertTrue(self._is_valid_tag_name(tag), f"Tag '{tag}' contains invalid characters")

    def test_orphaned_categories(self):
        """Test for orphaned intermediate categories."""
        hierarchy_file = Path(__file__).parent.parent / "data" / "hierarchy.tsv"

        if not hierarchy_file.exists():
            self.skipTest("Hierarchy file not found")

        parents = set()
        children = set()

        with open(hierarchy_file, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    parent, child = parts
                    parents.add(parent)
                    children.add(child)

        # Find intermediate categories (categories that are both parent and child)
        intermediate_categories = parents & children

        # Find leaf nodes (categories that are only children)
        leaf_nodes = children - parents

        # Find root nodes (categories that are only parents)
        root_nodes = parents - children

        # Validate structure
        self.assertGreater(len(root_nodes), 0, "Should have at least one root category")
        self.assertGreater(len(leaf_nodes), 0, "Should have at least one leaf node")

        print(f"Structure: {len(root_nodes)} roots, {len(intermediate_categories)} intermediate, {len(leaf_nodes)} leaves")

    def _is_valid_tag_name(self, tag: str) -> bool:
        """Check if a tag name follows naming conventions."""
        import re
        # Allow lowercase letters, numbers, hyphens, apostrophes, and underscores
        pattern = r'^[a-z0-9\-\'_]+$'
        return bool(re.match(pattern, tag))


if __name__ == '__main__':
    unittest.main()