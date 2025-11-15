#!/bin/bash
# Append admin user bookmark data to TSV files

cd "$(dirname "$0")"

echo "Appending admin user bookmark data to TSV files..."

# Generate the data
python3 generate_admin_bookmarks.py > admin_data.txt

# Extract and append bookmark categories (8 lines)
sed -n '/^b8bcf155/,/^$/p' admin_data.txt | head -8 >> bookmark_categories.tsv
echo "Added 8 categories to bookmark_categories.tsv"

# Extract and append bookmarks (25 lines)
sed -n '/^c5dc9a10/,/^$/p' admin_data.txt | head -25 >> bookmarks.tsv
echo "Added 25 bookmarks to bookmarks.tsv"

# Extract and append bookmark category members (33 lines)
sed -n '/^c5dc9a10.*a0077122/,/^$/p' admin_data.txt | head -33 >> bookmark_category_members.tsv
echo "Added 33 bookmark category members to bookmark_category_members.tsv"

# Clean up
rm admin_data.txt

echo ""
echo "Done! Verify the changes:"
echo "wc -l bookmark_categories.tsv     # Should be 17 (1 header + 8 test user + 8 admin user)"
echo "wc -l bookmarks.tsv               # Should be 51 (1 header + 25 test user + 25 admin user)"
echo "wc -l bookmark_category_members.tsv  # Should be 67 (1 header + 33 test user + 33 admin user)"
