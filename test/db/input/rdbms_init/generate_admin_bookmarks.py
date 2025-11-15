#!/usr/bin/env python3
"""
Generate duplicate bookmark data for admin user.

This script reads existing bookmark data for test user (aandersen) and creates
duplicate data for the admin user with new UUIDs while maintaining relationships.
"""

import csv
import uuid
from typing import Dict

# User IDs
TEST_USER_ID = 'a04237b8-f14e-4fed-9427-576c780d6e2a'  # aandersen
ADMIN_USER_ID = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'  # admin

def main():
    # Maps old category/bookmark UUIDs to new ones for admin user
    category_id_map: Dict[str, str] = {}
    bookmark_id_map: Dict[str, str] = {}

    print("Generating duplicate bookmark data for admin user...")
    print(f"Source user: {TEST_USER_ID}")
    print(f"Target user: {ADMIN_USER_ID}")
    print()

    # Process bookmark_categories.tsv
    print("=" * 80)
    print("BOOKMARK CATEGORIES (bookmark_categories.tsv)")
    print("=" * 80)
    print("Append the following lines to bookmark_categories.tsv:")
    print()

    with open('bookmark_categories.tsv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['user_id'] == TEST_USER_ID:
                old_id = row['id']
                new_id = str(uuid.uuid4())
                category_id_map[old_id] = new_id

                # Update fields
                row['id'] = new_id
                row['user_id'] = ADMIN_USER_ID

                # Update parent_id if it exists (maintain parent-child relationship)
                if row.get('parent_id') and row['parent_id'].strip():
                    row['parent_id'] = category_id_map.get(row['parent_id'], row['parent_id'])

                # Print TSV line
                print('\t'.join([
                    row['id'],
                    row['user_id'],
                    row['name'],
                    row['description'],
                    row['color_hex'],
                    row['icon'],
                    row['cover_content_id'],
                    row['cover_content_source_type'],
                    row['parent_id'],
                    row['sort_index'],
                    row['is_public'],
                    row['share_token'],
                    row['created_at'],
                    row['updated_at']
                ]))

    print()
    print()

    # Process bookmarks.tsv
    print("=" * 80)
    print("BOOKMARKS (bookmarks.tsv)")
    print("=" * 80)
    print("Append the following lines to bookmarks.tsv:")
    print()

    with open('bookmarks.tsv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['user_id'] == TEST_USER_ID:
                old_id = row['id']
                new_id = str(uuid.uuid4())
                bookmark_id_map[old_id] = new_id

                # Update fields
                row['id'] = new_id
                row['user_id'] = ADMIN_USER_ID

                # Print TSV line
                print('\t'.join([
                    row['id'],
                    row['user_id'],
                    row['content_id'],
                    row['content_source_type'],
                    row['note'],
                    row['pinned'],
                    row['is_public'],
                    row['created_at'],
                    row['updated_at'],
                    row['deleted_at']
                ]))

    print()
    print()

    # Process bookmark_category_members.tsv
    print("=" * 80)
    print("BOOKMARK CATEGORY MEMBERS (bookmark_category_members.tsv)")
    print("=" * 80)
    print("Append the following lines to bookmark_category_members.tsv:")
    print()

    with open('bookmark_category_members.tsv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['user_id'] == TEST_USER_ID:
                # Map old IDs to new IDs
                row['bookmark_id'] = bookmark_id_map.get(row['bookmark_id'], row['bookmark_id'])
                row['category_id'] = category_id_map.get(row['category_id'], row['category_id'])
                row['user_id'] = ADMIN_USER_ID

                # Print TSV line
                print('\t'.join([
                    row['bookmark_id'],
                    row['category_id'],
                    row['user_id'],
                    row['position'],
                    row['added_at']
                ]))

    print()
    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print()
    print(f"Generated {len(category_id_map)} bookmark categories")
    print(f"Generated {len(bookmark_id_map)} bookmarks")
    print()
    print("Copy the output above and append to the respective TSV files.")

if __name__ == '__main__':
    main()
