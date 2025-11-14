#!/usr/bin/env python3
"""Directly append admin user bookmark data to TSV files."""

import csv
import uuid
from typing import Dict

# User IDs
TEST_USER_ID = 'a04237b8-f14e-4fed-9427-576c780d6e2a'  # aandersen
ADMIN_USER_ID = '121e194b-4caa-4b81-ad4f-86ca3919d5b9'  # admin

def append_data():
    # Maps old category/bookmark UUIDs to new ones for admin user
    category_id_map: Dict[str, str] = {}
    bookmark_id_map: Dict[str, str] = {}

    # Read and append bookmark_categories.tsv
    print("Appending to bookmark_categories.tsv...")
    with open('bookmark_categories.tsv', 'r+', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)

        # Generate new rows for admin user
        new_rows = []
        for row in rows:
            if row['user_id'] == TEST_USER_ID:
                old_id = row['id']
                new_id = str(uuid.uuid4())
                category_id_map[old_id] = new_id

                new_row = row.copy()
                new_row['id'] = new_id
                new_row['user_id'] = ADMIN_USER_ID

                # Update parent_id if it exists
                if row.get('parent_id') and row['parent_id'].strip():
                    new_row['parent_id'] = category_id_map.get(row['parent_id'], row['parent_id'])

                new_rows.append(new_row)

        # Append new rows
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames, delimiter='\t')
        for new_row in new_rows:
            writer.writerow(new_row)

    print(f"Added {len(new_rows)} categories")

    # Read and append bookmarks.tsv
    print("Appending to bookmarks.tsv...")
    with open('bookmarks.tsv', 'r+', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)

        new_rows = []
        for row in rows:
            if row['user_id'] == TEST_USER_ID:
                old_id = row['id']
                new_id = str(uuid.uuid4())
                bookmark_id_map[old_id] = new_id

                new_row = row.copy()
                new_row['id'] = new_id
                new_row['user_id'] = ADMIN_USER_ID
                new_rows.append(new_row)

        writer = csv.DictWriter(f, fieldnames=reader.fieldnames, delimiter='\t')
        for new_row in new_rows:
            writer.writerow(new_row)

    print(f"Added {len(new_rows)} bookmarks")

    # Read and append bookmark_category_members.tsv
    print("Appending to bookmark_category_members.tsv...")
    with open('bookmark_category_members.tsv', 'r+', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)

        new_rows = []
        for row in rows:
            if row['user_id'] == TEST_USER_ID:
                new_row = row.copy()
                new_row['bookmark_id'] = bookmark_id_map.get(row['bookmark_id'], row['bookmark_id'])
                new_row['category_id'] = category_id_map.get(row['category_id'], row['category_id'])
                new_row['user_id'] = ADMIN_USER_ID
                new_rows.append(new_row)

        writer = csv.DictWriter(f, fieldnames=reader.fieldnames, delimiter='\t')
        for new_row in new_rows:
            writer.writerow(new_row)

    print(f"Added {len(new_rows)} bookmark category members")
    print()
    print("Done! Data appended successfully.")

if __name__ == '__main__':
    append_data()
