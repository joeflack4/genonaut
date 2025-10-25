# Fix Duplicate Tags Issue

## Problem Description

Content items have duplicate tags appearing in the UI, causing React console warnings:
```
Encountered two children with the same key, `pastel`. Keys should be unique...
Encountered two children with the same key, `moody`. Keys should be unique...
```

### Root Cause
The duplicate tags exist in the `item_metadata` JSONB field in `content_items` and `content_items_auto` tables. Example from content item 88136:
```json
"item_metadata": {
    "tags": [
        "anime",
        "pastel",
        "moody",
        ...
        "pastel",  // duplicate
        "moody",   // duplicate
        ...
    ]
}
```

### Current Architecture
- Tags are stored in the normalized `content_tags` junction table (canonical source)
- Legacy `item_metadata.tags` arrays exist from before normalization
- Frontend reads tags from `item_metadata.tags` (legacy behavior)
- No synchronization between `content_tags` and `item_metadata.tags`

## Solution Approach

Implement database triggers to keep `item_metadata.tags` synchronized with `content_tags`:
1. Clean up existing duplicate tags in database
2. Create PostgreSQL triggers to maintain sync on INSERT/DELETE
3. Add frontend deduplication as defensive safeguard
4. Update API to return deduplicated tags

## Technical Notes

### Migration Approach
- **Manual Alembic migration required** (autogenerate doesn't detect triggers)
- Triggers are created via raw SQL in `upgrade()` and `downgrade()`
- When `make init-demo` runs, it calls `alembic upgrade head`, so triggers are created automatically
- No special init code needed - migrations handle everything

### Migration File Structure
```python
def upgrade():
    # 1. Deduplicate existing data
    # 2. Create trigger function
    # 3. Create triggers on content_tags

def downgrade():
    # Drop triggers and function
```

## Implementation Tasks

### Phase 1: Database Cleanup
- [x] Write SQL query to identify all content items with duplicate tags in `item_metadata.tags`
- [x] Create Alembic migration to deduplicate existing `item_metadata.tags` arrays
  - [x] For `content_items` table
  - [x] For `content_items_auto` table
- [x] Test migration on test database
- [x] Run migration on demo database

### Phase 2: Database Triggers
- [x] Create trigger function `sync_content_tags_to_metadata()` in PostgreSQL
  - [x] Handle INSERT: add tag name to `item_metadata.tags` array
  - [x] Handle DELETE: remove tag name from `item_metadata.tags` array
  - [x] Join to `tags` table to get tag name from tag_id
  - [x] Route to correct table (`content_items` or `content_items_auto`) based on `content_source`
  - [x] Use JSONB array operations to add/remove tags
  - [x] Ensure deduplication when adding tags
- [x] Create trigger on `content_tags` table
  - [x] AFTER INSERT trigger
  - [x] AFTER DELETE trigger
  - [x] FOR EACH ROW
- [x] Add trigger creation to Alembic migration
- [x] Test triggers work correctly:
  - [x] Test INSERT adds tag to metadata
  - [x] Test DELETE removes tag from metadata
  - [x] Test duplicate prevention
  - [x] Test both content_items and content_items_auto

### Phase 3: Frontend Deduplication (Defensive)
- [x] Update `getMetadataTags()` in `ImageViewPage.tsx` to deduplicate tags
- [x] Update any other frontend code that reads `item_metadata.tags` (none found - only ImageViewPage accesses it)
- [x] Add deduplication to frontend type transformations (N/A - services pass through itemMetadata as-is)

### Phase 4: API Updates
- [x] Add a field validator to `ContentResponse` model to deduplicate tags in item_metadata

### Phase 5: Testing
- [x] Add unit test for deduplication function
- [x] Add database test for trigger functionality
  - [x] Test INSERT operation
  - [x] Test DELETE operation
  - [x] Test both content sources
  - [x] Test duplicate prevention
  - [x] Test multiple tag operations
- [x] Add E2E test to verify no React warnings on view pages

## Migration Strategy

1. Create single Alembic migration that:
   - Deduplicates existing `item_metadata.tags` arrays
   - Creates trigger function
   - Creates triggers on `content_tags` table

2. Migration should be:
   - Idempotent (safe to run multiple times)
   - Reversible (down migration drops triggers)
   - Well-tested on test database before production

## Notes

- Triggers will only fire for future INSERT/DELETE operations on `content_tags`
- Existing data must be cleaned up separately in migration
- Frontend deduplication provides defense-in-depth
- Consider whether to eventually deprecate `item_metadata.tags` entirely in favor of API-side joins to `content_tags`
