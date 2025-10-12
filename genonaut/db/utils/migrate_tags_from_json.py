"""Migrate tags from hierarchy.json to database.

This script loads tags from the static JSON file and populates the database
with tags and their parent-child relationships.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from genonaut.db.schema import Tag, TagParent


# UUID namespace for generating consistent tag UUIDs from tag names
TAG_UUID_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # URL namespace


def generate_tag_uuid(tag_name: str) -> uuid.UUID:
    """Generate a consistent UUID for a tag based on its name.

    Uses UUID v5 with a consistent namespace to ensure the same tag name
    always generates the same UUID.

    Args:
        tag_name: The tag name (id from JSON file)

    Returns:
        UUID for the tag
    """
    return uuid.uuid5(TAG_UUID_NAMESPACE, tag_name)


def load_hierarchy_json(json_path: Optional[Path] = None) -> Dict:
    """Load tag hierarchy from JSON file.

    Args:
        json_path: Path to hierarchy.json file. If None, uses default location.

    Returns:
        Dictionary with hierarchy data

    Raises:
        FileNotFoundError: If hierarchy file doesn't exist
        ValueError: If JSON is invalid
    """
    if json_path is None:
        # Default path relative to this file
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        json_path = project_root / "genonaut" / "ontologies" / "tags" / "data" / "hierarchy.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Hierarchy file not found: {json_path}")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in hierarchy file: {e}")


def migrate_tags(session: Session, hierarchy_data: Dict, verbose: bool = True) -> Tuple[int, int]:
    """Migrate tags from hierarchy data to database.

    Args:
        session: SQLAlchemy session
        hierarchy_data: Hierarchy data from JSON
        verbose: Whether to print progress messages

    Returns:
        Tuple of (tags_created, relationships_created)
    """
    nodes = hierarchy_data.get("nodes", [])

    if verbose:
        print(f"Processing {len(nodes)} tags...")

    # First pass: Create all tags
    tag_map: Dict[str, uuid.UUID] = {}  # Map tag_id (name) to UUID
    tags_created = 0

    for node in nodes:
        tag_id = node.get("id")
        tag_name = node.get("name")

        if not tag_id or not tag_name:
            if verbose:
                print(f"Warning: Skipping invalid node: {node}")
            continue

        # Generate consistent UUID for this tag
        tag_uuid = generate_tag_uuid(tag_id)
        tag_map[tag_id] = tag_uuid

        # Check if tag already exists
        existing_tag = session.query(Tag).filter(Tag.id == tag_uuid).first()
        if existing_tag:
            if verbose:
                print(f"  Tag '{tag_name}' already exists, skipping...")
            continue

        # Create tag
        tag = Tag(
            id=tag_uuid,
            name=tag_name,
            tag_metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(tag)
        tags_created += 1

        if verbose and tags_created % 20 == 0:
            print(f"  Created {tags_created} tags...")

    # Commit tags
    session.commit()

    if verbose:
        print(f"Created {tags_created} tags")

    # Second pass: Create parent-child relationships
    relationships_created = 0

    for node in nodes:
        tag_id = node.get("id")
        parent_id = node.get("parent")

        if not tag_id:
            continue

        # Skip if no parent (root node)
        if parent_id is None:
            continue

        # Get UUIDs for child and parent
        child_uuid = tag_map.get(tag_id)
        parent_uuid = tag_map.get(parent_id)

        if not child_uuid or not parent_uuid:
            if verbose:
                print(f"Warning: Could not find UUID for tag_id={tag_id} or parent_id={parent_id}")
            continue

        # Check if relationship already exists
        existing_rel = session.query(TagParent).filter(
            TagParent.tag_id == child_uuid,
            TagParent.parent_id == parent_uuid
        ).first()

        if existing_rel:
            continue

        # Create relationship
        tag_parent = TagParent(
            tag_id=child_uuid,
            parent_id=parent_uuid
        )
        session.add(tag_parent)
        relationships_created += 1

    # Commit relationships
    session.commit()

    if verbose:
        print(f"Created {relationships_created} parent-child relationships")

    return tags_created, relationships_created


def main(database_url: str, json_path: Optional[str] = None, verbose: bool = True):
    """Main function to run the migration.

    Args:
        database_url: Database connection URL
        json_path: Optional path to hierarchy.json
        verbose: Whether to print progress messages
    """
    if verbose:
        print("=" * 60)
        print("Tag Migration: JSON to Database")
        print("=" * 60)

    # Load hierarchy data
    json_file_path = Path(json_path) if json_path else None
    hierarchy_data = load_hierarchy_json(json_file_path)

    if verbose:
        metadata = hierarchy_data.get("metadata", {})
        print(f"Loaded hierarchy with {metadata.get('totalNodes', 0)} nodes")
        print(f"  Root categories: {metadata.get('rootCategories', 0)}")
        print(f"  Total relationships: {metadata.get('totalRelationships', 0)}")
        print()

    # Create database engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Run migration
        tags_created, rels_created = migrate_tags(session, hierarchy_data, verbose)

        if verbose:
            print()
            print("=" * 60)
            print("Migration completed successfully!")
            print(f"  Tags created: {tags_created}")
            print(f"  Relationships created: {rels_created}")
            print("=" * 60)

        return tags_created, rels_created

    except Exception as e:
        session.rollback()
        if verbose:
            print(f"\nError during migration: {e}")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Migrate tags from JSON to database")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="Database connection URL (default: from DATABASE_URL env var)"
    )
    parser.add_argument(
        "--json-path",
        help="Path to hierarchy.json file (default: genonaut/ontologies/tags/data/hierarchy.json)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    if not args.database_url:
        print("Error: DATABASE_URL environment variable not set and --database-url not provided")
        exit(1)

    main(args.database_url, args.json_path, verbose=not args.quiet)
