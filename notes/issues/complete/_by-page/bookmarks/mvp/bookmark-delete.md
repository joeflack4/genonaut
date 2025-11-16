# Bookmark Hard Delete Implementation

## Problem
When a bookmark is deleted (soft-deleted), users cannot re-bookmark the same content because the database unique constraint `uq_bookmark_user_content` still sees the soft-deleted record.

**Error**: `POST /api/v1/bookmarks 422 (Unprocessable Entity)` - "Bookmark already exists for this content item"

**Root Cause**:
- Soft-delete sets `deleted_at` timestamp but doesn't remove the row
- Unique constraint `UNIQUE(user_id, content_id, content_source_type)` blocks duplicate bookmarks even if one is soft-deleted
- Application code filters `WHERE deleted_at IS NULL` but database constraint doesn't

## Solution
Implement hard deletion for bookmarks. Bookmarks are lightweight data that users can easily recreate, so there's no need for soft-delete.

## Implementation Checklist

### Backend Code Changes
- [x] Add `delete()` method to `BookmarkRepository` in `genonaut/api/repositories/bookmark_repository.py`
  - Should actually delete the row from database
  - Should handle foreign key cascade (bookmark_category_members should cascade delete)
  - Should raise EntityNotFoundError if bookmark not found
  - Should wrap in try/except for DatabaseError

- [x] Update `BookmarkService.delete_bookmark()` in `genonaut/api/services/bookmark_service.py`
  - Change from `self.bookmark_repo.soft_delete(bookmark_id)` to `self.bookmark_repo.delete(bookmark_id)`

- [x] Verify cascade behavior for `BookmarkCategoryMember` records
  - Check schema.py for FK constraint with `ondelete='CASCADE'`
  - Ensure deleting a bookmark also deletes its category memberships
  - Added `passive_deletes=True` to Bookmark.category_memberships relationship

### Testing
- [ ] Write unit test for `BookmarkRepository.delete()`
  - Test successful deletion
  - Test EntityNotFoundError for non-existent bookmark

- [x] Write integration test for delete -> recreate flow (MANUAL VERIFICATION COMPLETED)
  - Create bookmark
  - Delete bookmark
  - Re-create same bookmark (should succeed)
  - Verify bookmark exists and is functional
  - **Result**: Successfully deleted and re-bookmarked content ID 3000127 with no errors

- [ ] Run existing bookmark tests to ensure no regressions
  - `make test-db` - Database tests
  - `make test-api` - API integration tests
  - Frontend E2E tests if applicable

### Database Migration (Optional - Future Task)
Note: Can be done later in a separate migration
- [ ] Create migration to remove `deleted_at` column from bookmarks table
- [ ] Update Bookmark model in schema.py to remove `deleted_at` field
- [ ] Remove `idx_bookmarks_user_not_deleted` partial index (no longer needed)
- [ ] Update all queries that filter on `deleted_at IS NULL`

### Documentation
- [ ] Update docstrings for modified methods
- [ ] Add note in this file about what was changed

## Files Modified

### Repository Layer
- `genonaut/api/repositories/bookmark_repository.py`
  - Line ~279: `soft_delete()` - Keep for backward compatibility or remove
  - New: `delete()` method for hard deletion

### Service Layer
- `genonaut/api/services/bookmark_service.py`
  - Line ~288: Update `delete_bookmark()` to call `delete()` instead of `soft_delete()`

### Schema (Future)
- `genonaut/db/schema.py`
  - Line 1462: `deleted_at` column (remove in future migration)
  - Line 1501-1502: Partial index on deleted_at (remove in future migration)

### Tests
- New test file or existing test files for bookmark repository/service

## Verification Steps

After implementation:
1. Start API server: `make api-demo-restart`
2. Navigate to http://localhost:5173/gallery
3. Click bookmark icon on an image
4. Open bookmark dialog, click red trash icon to delete
5. Click bookmark icon again - should successfully re-bookmark
6. Verify bookmark appears in /bookmarks page
7. No console errors

## Notes
- Soft-delete pattern is useful for audit trails and data recovery, but bookmarks are user preferences that don't require this
- Hard deletion simplifies the code and eliminates the unique constraint issue
- The `deleted_at` column and related code can be removed in a future cleanup migration
- Foreign key cascade should handle bookmark_category_members automatically

## Implementation Summary (Completed 2025-11-16)

### Changes Made

1. **BookmarkRepository** (`genonaut/api/repositories/bookmark_repository.py`)
   - Added new `delete()` method that performs hard deletion using `self.db.delete(bookmark)`
   - Kept `soft_delete()` method marked as DEPRECATED for backward compatibility
   - The delete method properly handles exceptions and rolls back on errors

2. **BookmarkService** (`genonaut/api/services/bookmark_service.py`)
   - Updated `delete_bookmark()` to call `self.bookmark_repo.delete()` instead of `soft_delete()`
   - Updated docstring to reflect hard deletion behavior

3. **Schema** (`genonaut/db/schema.py`)
   - Added `passive_deletes=True` to `Bookmark.category_memberships` relationship
   - This tells SQLAlchemy to rely on database CASCADE constraints instead of trying to null out FK columns
   - Fixes SQLAlchemy error: "tried to blank-out primary key column 'bookmark_category_members.bookmark_id'"

### Testing Results
- **Manual test passed**: Successfully deleted bookmark for content ID 3000127 and immediately re-bookmarked it
- No console errors or 422 status codes
- Database CASCADE properly deletes associated `bookmark_category_members` records

### What This Fixes
- Users can now delete a bookmark and immediately re-bookmark the same content without getting a 422 error
- Soft-deleted records no longer block the unique constraint `uq_bookmark_user_content`
- Cleaner database - deleted bookmarks are actually removed instead of accumulating with `deleted_at` timestamps
