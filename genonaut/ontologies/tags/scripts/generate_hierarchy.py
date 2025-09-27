#!/usr/bin/env python3
"""Generate tag hierarchy TSV from database analysis.

This script analyzes the tags extracted from the database and creates
a hierarchical structure in TSV format (parent-child relationships).
"""

import sys
from pathlib import Path
from typing import Dict, Set, Tuple, List
import re
from collections import Counter

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_tag_patterns(tags: List[str]) -> Dict[str, List[str]]:
    """Analyze tags and suggest hierarchical relationships based on patterns.

    Args:
        tags: List of all tags to analyze

    Returns:
        Dictionary mapping parent categories to lists of children
    """
    patterns = {
        'software_category': [],
        'test_type': [],
        'development': [],
        'technical': []
    }

    # Define patterns for automatic categorization
    software_keywords = ['api', 'sdk', 'library', 'framework', 'service']
    test_keywords = ['test', 'testing', 'integration', 'unit', 'e2e', 'selenium']
    dev_keywords = ['dev', 'development', 'debug', 'staging', 'prod', 'production']

    for tag in tags:
        tag_lower = tag.lower()

        # Check for software-related terms
        if any(keyword in tag_lower for keyword in software_keywords):
            patterns['software_category'].append(tag)

        # Check for test-related terms
        elif any(keyword in tag_lower for keyword in test_keywords):
            patterns['test_type'].append(tag)

        # Check for development-related terms
        elif any(keyword in tag_lower for keyword in dev_keywords):
            patterns['development'].append(tag)

        else:
            patterns['technical'].append(tag)

    # Remove empty categories
    return {k: v for k, v in patterns.items() if v}


def create_hierarchy_tsv(tag_patterns: Dict[str, List[str]], output_path: Path) -> None:
    """Create a TSV file with parent-child relationships.

    Args:
        tag_patterns: Dictionary mapping categories to tag lists
        output_path: Path where to write the TSV file
    """

    with open(output_path, 'w') as f:
        f.write("parent\tchild\n")

        for parent, children in tag_patterns.items():
            for child in children:
                f.write(f"{parent}\t{child}\n")

        # Add some specific sub-relationships based on current tags
        # This would be customized based on actual tag analysis
        if 'test' in [child for children in tag_patterns.values() for child in children]:
            if 'integration' in [child for children in tag_patterns.values() for child in children]:
                f.write("test\tintegration\n")


def validate_hierarchy(tsv_path: Path) -> List[str]:
    """Validate the hierarchy TSV for consistency issues.

    Args:
        tsv_path: Path to the TSV file to validate

    Returns:
        List of validation errors/warnings
    """
    errors = []
    parent_child_pairs = set()
    all_parents = set()
    all_children = set()

    with open(tsv_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip header

        for i, line in enumerate(lines, 2):
            parts = line.strip().split('\t')
            if len(parts) != 2:
                errors.append(f"Line {i}: Invalid format - expected 2 columns, got {len(parts)}")
                continue

            parent, child = parts

            if (parent, child) in parent_child_pairs:
                errors.append(f"Line {i}: Duplicate relationship - {parent} -> {child}")

            parent_child_pairs.add((parent, child))
            all_parents.add(parent)
            all_children.add(child)

    # Check for potential cycles (simplified check)
    for child in all_children:
        if child in all_parents:
            # This child is also a parent - check if it could create a cycle
            # For now, just warn about it
            errors.append(f"Warning: '{child}' is both a parent and child - verify no cycles exist")

    return errors


def main():
    """Main function to generate hierarchy from current tag analysis."""

    # Read the current tag analysis
    data_dir = Path(__file__).parent.parent / "data"
    analysis_file = data_dir / "tags_analysis.txt"

    if not analysis_file.exists():
        print(f"Error: Analysis file not found at {analysis_file}")
        print("Please run query_tags.py first to generate the analysis.")
        return 1

    # Extract tags from analysis file
    tags = []
    with open(analysis_file, 'r') as f:
        lines = f.readlines()

        # Find the section with all tags
        in_tags_section = False
        for line in lines:
            if "ALL UNIQUE TAGS" in line:
                in_tags_section = True
                continue
            elif "TAG FREQUENCY ANALYSIS" in line:
                in_tags_section = False
                break
            elif in_tags_section and line.strip():
                tags.append(line.strip())

    if not tags:
        print("No tags found in analysis file.")
        return 1

    print(f"Analyzing {len(tags)} tags for hierarchical relationships...")

    # Analyze patterns and create hierarchy
    tag_patterns = analyze_tag_patterns(tags)

    print("Detected categories:")
    for category, tag_list in tag_patterns.items():
        print(f"  {category}: {', '.join(tag_list)}")

    # Create the TSV file
    hierarchy_file = data_dir / "hierarchy.tsv"
    create_hierarchy_tsv(tag_patterns, hierarchy_file)

    print(f"\nHierarchy TSV created at: {hierarchy_file}")

    # Validate the hierarchy
    errors = validate_hierarchy(hierarchy_file)
    if errors:
        print("\nValidation issues:")
        for error in errors:
            print(f"  {error}")
    else:
        print("\nHierarchy validation passed!")

    return 0


if __name__ == "__main__":
    sys.exit(main())