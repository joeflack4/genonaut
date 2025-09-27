#!/usr/bin/env python3
"""Query all tags from the database to analyze for ontology creation.

This script connects to the Genonaut database and extracts all unique tags
from both content_items and content_items_auto tables for ontology analysis.
"""

import json
from collections import Counter
from typing import Set, List
import sys
from pathlib import Path

# Add the project root to the path so we can import genonaut modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from genonaut.db.utils.utils import get_database_session
from genonaut.db.schema import ContentItem, ContentItemAuto


def extract_tags_from_json_column(tags_column) -> Set[str]:
    """Extract individual tags from a JSON column containing a list of tags."""
    tags = set()
    if tags_column and isinstance(tags_column, list):
        for tag in tags_column:
            if isinstance(tag, str) and tag.strip():
                # Clean and normalize tags
                cleaned_tag = tag.strip().lower()
                tags.add(cleaned_tag)
    return tags


def main():
    """Query and analyze all tags from the database."""
    print("Connecting to demo database...")

    # Get database session for demo environment (which has the real diverse data)
    session = get_database_session(environment='demo')

    try:
        # Query all content items with tags (limit for initial analysis)
        print("Querying content_items table...")
        content_items = session.query(ContentItem).filter(ContentItem.tags != None).limit(1000).all()
        print(f"Found {len(content_items)} content items (limited to 1000 for analysis)")

        print("Querying content_items_auto table...")
        auto_content_items = session.query(ContentItemAuto).filter(ContentItemAuto.tags != None).limit(1000).all()
        print(f"Found {len(auto_content_items)} auto content items (limited to 1000 for analysis)")

        # Extract all unique tags
        all_tags = set()
        tag_counts = Counter()

        print(f"Processing {len(content_items)} content items...")
        for item in content_items:
            item_tags = extract_tags_from_json_column(item.tags)
            all_tags.update(item_tags)
            for tag in item_tags:
                tag_counts[tag] += 1

        print(f"Processing {len(auto_content_items)} auto content items...")
        for item in auto_content_items:
            item_tags = extract_tags_from_json_column(item.tags)
            all_tags.update(item_tags)
            for tag in item_tags:
                tag_counts[tag] += 1

        # Sort tags alphabetically for easier analysis
        sorted_tags = sorted(list(all_tags))

        print(f"\nFound {len(sorted_tags)} unique tags across {len(content_items) + len(auto_content_items)} content items\n")

        # Print summary statistics
        print("=== TAG STATISTICS ===")
        print(f"Total unique tags: {len(sorted_tags)}")
        print(f"Total tag instances: {sum(tag_counts.values())}")

        if tag_counts:
            most_common = tag_counts.most_common(10)
            print(f"\nMost common tags:")
            for tag, count in most_common:
                print(f"  {tag}: {count}")

        # Write all tags to a file for analysis
        output_file = project_root / "tags_analysis.txt"
        with open(output_file, 'w') as f:
            f.write("=== ALL UNIQUE TAGS (ALPHABETICAL) ===\n\n")
            for tag in sorted_tags:
                f.write(f"{tag}\n")

            f.write(f"\n\n=== TAG FREQUENCY ANALYSIS ===\n\n")
            for tag, count in tag_counts.most_common():
                f.write(f"{tag}: {count}\n")

        print(f"\nDetailed analysis written to: {output_file}")

        # Also print first 20 tags for immediate viewing
        print(f"\nFirst 20 tags (alphabetical):")
        for i, tag in enumerate(sorted_tags[:20]):
            print(f"  {tag}")

        if len(sorted_tags) > 20:
            print(f"  ... and {len(sorted_tags) - 20} more")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())