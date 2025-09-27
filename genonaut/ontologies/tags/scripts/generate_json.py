#!/usr/bin/env python3
"""Convert TSV hierarchy to JSON format for frontend consumption.

This script reads the hierarchy.tsv file and converts it to a flat JSON format
optimized for performance with the react-accessible-treeview library.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def load_tsv_hierarchy(tsv_path: Path) -> List[Dict[str, Optional[str]]]:
    """Load hierarchy from TSV file and convert to flat node list.

    Args:
        tsv_path: Path to the TSV file

    Returns:
        List of node dictionaries with id, name, and parent fields

    Raises:
        FileNotFoundError: If TSV file doesn't exist
        ValueError: If TSV format is invalid
    """
    if not tsv_path.exists():
        raise FileNotFoundError(f"TSV file not found: {tsv_path}")

    parents_seen = set()
    children_seen = set()
    relationships = set()  # Track unique parent-child pairs
    child_to_parent = {}  # Track final parent for each child

    with open(tsv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("TSV file is empty")

    # Skip header line
    if lines[0].strip().lower().startswith('parent'):
        lines = lines[1:]

    duplicate_relationships = []
    conflicting_parents = {}

    for line_num, line in enumerate(lines, 2):  # Line 2 since we skip header
        line = line.strip()
        if not line:
            continue

        parts = line.split('\t')
        if len(parts) != 2:
            raise ValueError(f"Invalid TSV format on line {line_num}: expected 2 columns, got {len(parts)}")

        parent, child = parts
        parent = parent.strip()
        child = child.strip()

        if not parent or not child:
            raise ValueError(f"Empty parent or child on line {line_num}")

        relationship = (parent, child)

        # Track duplicate relationships
        if relationship in relationships:
            duplicate_relationships.append(f"Line {line_num}: {parent} -> {child}")
            continue

        relationships.add(relationship)
        parents_seen.add(parent)
        children_seen.add(child)

        # Check for conflicting parent assignments
        if child in child_to_parent and child_to_parent[child] != parent:
            if child not in conflicting_parents:
                conflicting_parents[child] = []
            conflicting_parents[child].append((parent, line_num))
        else:
            child_to_parent[child] = parent

    # Report issues but continue processing
    if duplicate_relationships:
        print(f"⚠️  Found {len(duplicate_relationships)} duplicate relationships (skipped):")
        for dup in duplicate_relationships[:5]:  # Show first 5
            print(f"    {dup}")
        if len(duplicate_relationships) > 5:
            print(f"    ... and {len(duplicate_relationships) - 5} more")

    if conflicting_parents:
        print(f"⚠️  Found {len(conflicting_parents)} nodes with conflicting parents:")
        for child, parents in conflicting_parents.items():
            print(f"    {child}: using '{child_to_parent[child]}', conflicting with {[p[0] for p in parents]}")

    # Create node list from unique relationships
    nodes = []

    # Add child nodes
    for child, parent in child_to_parent.items():
        nodes.append({
            "id": child,
            "name": format_tag_name(child),
            "parent": parent
        })

    # Add root nodes (parents that are not children of anything)
    root_nodes = parents_seen - children_seen
    for root in sorted(root_nodes):
        nodes.append({
            "id": root,
            "name": format_tag_name(root),
            "parent": None
        })

    # Sort nodes: roots first, then by parent, then by name
    def sort_key(node):
        if node["parent"] is None:
            return (0, node["name"])
        else:
            return (1, node["parent"], node["name"])

    nodes.sort(key=sort_key)

    return nodes


def format_tag_name(tag_id: str) -> str:
    """Convert tag ID to human-readable name.

    Args:
        tag_id: Tag identifier (e.g., 'art_movements', 'digital_techniques')

    Returns:
        Formatted name (e.g., 'Art Movements', 'Digital Techniques')
    """
    # Replace underscores with spaces and title case
    return tag_id.replace('_', ' ').replace('-', ' ').title()


def generate_hierarchy_json(nodes: List[Dict], output_path: Path) -> Dict:
    """Generate complete hierarchy JSON structure.

    Args:
        nodes: List of node dictionaries
        output_path: Path where JSON will be saved

    Returns:
        Complete JSON structure with nodes and metadata
    """
    # Calculate statistics
    total_nodes = len(nodes)
    total_relationships = len([n for n in nodes if n["parent"] is not None])
    root_count = len([n for n in nodes if n["parent"] is None])

    # Create complete structure
    hierarchy_data = {
        "nodes": nodes,
        "metadata": {
            "totalNodes": total_nodes,
            "totalRelationships": total_relationships,
            "rootCategories": root_count,
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "format": "flat_array",
            "version": "1.0"
        }
    }

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(hierarchy_data, f, indent=2, ensure_ascii=False)

    return hierarchy_data


def validate_hierarchy_integrity(nodes: List[Dict]) -> List[str]:
    """Validate hierarchy for consistency and integrity.

    Args:
        nodes: List of node dictionaries

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    node_ids = {node["id"] for node in nodes}

    # Check for orphaned references
    for node in nodes:
        if node["parent"] is not None and node["parent"] not in node_ids:
            errors.append(f"Node '{node['id']}' references non-existent parent '{node['parent']}'")

    # Check for duplicate IDs
    id_counts = {}
    for node in nodes:
        node_id = node["id"]
        id_counts[node_id] = id_counts.get(node_id, 0) + 1

    for node_id, count in id_counts.items():
        if count > 1:
            errors.append(f"Duplicate node ID: '{node_id}' appears {count} times")

    # Check for circular dependencies (basic check)
    def has_circular_dependency(node_id: str, visited: set) -> bool:
        if node_id in visited:
            return True

        visited.add(node_id)

        # Find node
        node = next((n for n in nodes if n["id"] == node_id), None)
        if not node or node["parent"] is None:
            return False

        return has_circular_dependency(node["parent"], visited.copy())

    for node in nodes:
        if node["parent"] is not None:
            if has_circular_dependency(node["id"], set()):
                errors.append(f"Circular dependency detected for node '{node['id']}'")

    return errors


def main():
    """Main function to convert TSV to JSON."""
    # Set up paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    tsv_path = data_dir / "hierarchy.tsv"
    json_path = data_dir / "hierarchy.json"

    try:
        print(f"Loading hierarchy from {tsv_path}...")
        nodes = load_tsv_hierarchy(tsv_path)
        print(f"Loaded {len(nodes)} nodes")

        print("Validating hierarchy integrity...")
        errors = validate_hierarchy_integrity(nodes)
        if errors:
            print("❌ Validation errors found:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)

        print("✅ Validation passed")

        print(f"Generating JSON at {json_path}...")
        hierarchy_data = generate_hierarchy_json(nodes, json_path)

        # Print summary
        metadata = hierarchy_data["metadata"]
        print(f"✅ JSON generated successfully!")
        print(f"  - Total nodes: {metadata['totalNodes']}")
        print(f"  - Relationships: {metadata['totalRelationships']}")
        print(f"  - Root categories: {metadata['rootCategories']}")
        print(f"  - Output file: {json_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()