# Remove Old Tags UUID[] Field

**Date**: 2025-10-13
**Status**: In Progress
**Goal**: Remove the redundant `tags` UUID[] array columns now that we have the content_tags junction table

## Why Remove?

- Single source of truth (junction table only)
- Eliminates data synchronization concerns
- Saves storage (88M relationships = significant duplicate data)
- Simpler codebase (no dual-write)
- Junction table queries are now fast and optimized

## Task List

### Phase 1: Prepare for Removal
- [ ] Ensure all queries use junction table (not tags array)
- [ ] Remove dual-write code in create_content()
- [ ] Remove dual-write code in update_content()
- [ ] Remove _sync_tags_to_junction_table() helper (no longer needed)
- [ ] Update SQLite tests to populate content_tags junction table
- [ ] Remove old _apply_tag_filter() method (JSONB array approach)

### Phase 2: Database Migration
- [ ] Create migration to drop tags column from content_items
- [ ] Create migration to drop tags column from content_items_auto
- [ ] Apply migrations to test database
- [ ] Apply migrations to demo database

### Phase 3: Verification
- [ ] Run all tests - ensure they pass
- [ ] Test gallery tag filtering manually
- [ ] Test content creation with tags
- [ ] Test content update with tags
- [ ] Verify no code references old tags column

### Phase 4: Documentation
- [ ] Update notes/fix-gallery-tag-query.md
- [ ] Update COMPLETION-REPORT.md
- [ ] Document that tags are now junction-table-only

## SQLite Test Strategy

**Decision**: Populate content_tags in SQLite during test setup

**Approach**: Add a test fixture that:
1. After content is created in tests, sync tags to content_tags
2. Use a helper function that mimics the dual-write behavior
3. Or: Run a backfill script at test setup time

**Implementation**: Create a test utility that syncs tags to junction table for SQLite.

## Files to Modify

1. `genonaut/api/services/content_service.py` - Remove dual-write code
2. `genonaut/db/schema.py` - Update if needed
3. `genonaut/db/migrations/versions/` - New migration files
4. `test/` - Update test fixtures for SQLite
5. Documentation files

## Rollback Plan

If issues arise:
- Migration includes downgrade() to restore tags columns
- Can re-enable dual-write code
- Junction table data remains intact

---

**Status Updates**:
- Created: 2025-10-13 14:00 EDT
- Started: 2025-10-13 14:00 EDT
