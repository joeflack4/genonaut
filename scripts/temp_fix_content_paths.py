#!/usr/bin/env python3
"""Temporary script to fix content_data paths in content_items table.

Removes /generations/UUID/YYYY/MM/DD/ from paths, keeping just the filename.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path so we can import from genonaut
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_dir = project_root / "env"
load_dotenv(env_dir / ".env.shared")
load_dotenv(env_dir / ".env.local-demo")
load_dotenv(env_dir / ".env")

from genonaut.db.utils.utils import get_database_session
from genonaut.db.schema import ContentItem


def fix_path(path: str) -> str:
    """Remove /generations/UUID/YYYY/MM/DD/ from path.

    Example:
        ~/Documents/ComfyUI/output/generations/121e194b-4caa-4b81-ad4f-86ca3919d5b9/2025/11/09/gen_1194245_gen_job_1194245_00001_.png
        -> ~/Documents/ComfyUI/output/gen_1194245_gen_job_1194245_00001_.png

    Args:
        path: Original path

    Returns:
        Fixed path with generations/UUID/YYYY/MM/DD/ removed
    """
    # Pattern matches: /generations/{UUID}/{YYYY}/{MM}/{DD}/
    # UUID pattern: 8-4-4-4-12 hex digits
    # Date pattern: 4 digits / 2 digits / 2 digits
    pattern = r'/generations/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/\d{4}/\d{2}/\d{2}/'

    # Replace the pattern with just /
    fixed_path = re.sub(pattern, '/', path)

    return fixed_path


def main():
    """Update content_data paths in content_items table."""

    print("=" * 80)
    print("Content Path Fixer - Temporary Script")
    print("=" * 80)
    print()
    print("This script will update content_data paths in the content_items table.")
    print("It removes: /generations/UUID/YYYY/MM/DD/")
    print("Keeping only the base path and filename.")
    print()

    # Get database session (uses demo by default)
    session = get_database_session(environment='demo')

    try:
        # Query all content items with /generations/ in their path
        items = session.query(ContentItem).filter(
            ContentItem.content_data.like('%/generations/%')
        ).all()

        if not items:
            print("No content items found with /generations/ in their paths.")
            return

        print(f"Found {len(items)} content items with paths to fix.\n")

        # Show what will be changed
        changes = []
        for item in items:
            old_path = item.content_data
            new_path = fix_path(old_path)

            if old_path != new_path:
                changes.append((item.id, old_path, new_path))
                print(f"ID {item.id}:")
                print(f"  Before: {old_path}")
                print(f"  After:  {new_path}")
                print()

        if not changes:
            print("No changes needed - all paths are already in the correct format.")
            return

        print(f"\nTotal changes to make: {len(changes)}")
        print()

        # Ask for confirmation
        response = input("Do you want to proceed with these changes? (yes/no): ").strip().lower()

        if response != 'yes':
            print("Aborted - no changes made.")
            return

        # Apply changes
        print("\nApplying changes...")
        for item_id, old_path, new_path in changes:
            item = session.query(ContentItem).filter(ContentItem.id == item_id).first()
            if item:
                item.content_data = new_path
                print(f"  Updated ID {item_id}")

        # Commit changes
        session.commit()
        print(f"\nSuccessfully updated {len(changes)} content items!")

    except Exception as e:
        session.rollback()
        print(f"\nError: {e}")
        print("Changes rolled back - no data was modified.")
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    main()
