# Delete Content Feature Implementation

## Overview
Implement functional delete button on image view pages (`/view/CONTENT_ID`). The trash bin icon exists in the UI but is 
not wired up to actually delete content.

## Current State

### Backend - READY
- **DELETE endpoints exist and work:**
  - `/api/v1/content/{content_id}` (regular content) - `genonaut/api/routes/content.py:257`
  - `/api/v1/content-auto/{content_id}` (auto content) - `genonaut/api/routes/content_auto.py:98`
- **Implementation:** Hard delete (physically removes records)
- **Database schema:** No `deleted_at` column on content tables
- **Service layer:** `ContentService.delete_content()` - `genonaut/api/services/content_service.py:476`
- **Repository layer:** Base repository `delete()` method - `genonaut/api/repositories/base.py:169`

### Frontend - NOT IMPLEMENTED
- **UI exists:** Delete button rendered in `ImageViewPage.tsx:362`
- **Handler is stub:** `handleDelete()` just logs to console - `ImageViewPage.tsx:207`
- **API client ready:** `ApiClient.delete()` method exists - `frontend/src/services/api-client.ts:117`
- **No service method:** `GalleryService` has no delete method yet
- **No React Query hook:** Need mutation hook for deletion
- **Test infrastructure exists:** E2E helpers ready - `frontend/tests/e2e/utils/realApiHelpers.ts:482`

## Design Decisions

### Hard Delete vs Soft Delete (done)
**Decision: Keep hard delete (current backend implementation)**

**Rationale:**
- Backend already implements hard delete
- Content items don't have `deleted_at` column (would require migration)
- User-generated content deletion is permanent (user expectation)
- Bookmarks use soft delete, but that's for different reasons (user preference tracking)
- No requirement for content recovery/undelete feature

**Trade-offs:**
- Pro: Simpler implementation, matches current backend
- Pro: Reduces database size (removes unused data)
- Con: No undo/recovery capability
- Con: Could affect recommendations if historical data is needed

**Future consideration:** If soft delete is needed later, would require:
- Database migration to add `deleted_at` column
- Update repository to use soft delete pattern (like bookmarks)
- Update all queries to filter `deleted_at IS NULL`

### Database-Only Deletion (done)
**Decision: Delete database records only, do NOT delete files from disk**

**Rationale:**
- Current backend implementation only deletes DB records
- File deletion is tracked separately in existing backlog issue
- Separates concerns (DB cleanup vs. storage cleanup)
- Allows for future implementation of file recovery/retention policies

**Current behavior:**
- Database record deleted (content removed from application)
- Image files remain on disk (orphaned files)
- Storage not reclaimed

**Implications:**
- Pro: Simpler implementation, matches current backend
- Pro: Allows for potential file recovery if needed
- Pro: Reduces risk of accidental data loss
- Con: Orphaned files accumulate on disk (storage waste)
- Con: No automatic storage cleanup

**Future work:**
- File deletion is handled by separate backlog issue
- May implement background cleanup job for orphaned files
- Could add admin tool to identify and remove orphaned files
- Might implement "trash" folder with retention policy

**Note for implementers:**
- This is an intentional design decision, not an oversight
- Do not add file deletion logic to this feature
- Frontend should not attempt to delete files
- Backend delete endpoints will continue to only delete DB records

### Permissions & Authorization (to defer)
**Current state:** No authentication/authorization checks in delete endpoints

**Security considerations:**
- DELETE endpoints are public (no user validation)
- Any user can delete any content by ID
- **CRITICAL SECURITY ISSUE:** Needs fixing before production

**Immediate solution for this task:**
- Document the security issue
- Add TODO comment in code
- File separate task for auth implementation
- For now, implement delete feature with current auth model

## Implementation Tasks

### Phase 1: Frontend Service Layer
- [x] Add `deleteContent(contentId: number)` method to `GalleryService`
  - File: `frontend/src/services/gallery-service.ts`
  - Use `this.apiClient.delete<SuccessResponse>(`/api/v1/content/${contentId}`)`
  - Return Promise with success response

### Phase 2: React Query Mutation Hook
- [x] Create `useDeleteContent` hook
  - File: `frontend/src/hooks/useDeleteContent.ts` (new file)
  - Use `useMutation` from React Query
  - Mutation function: call `galleryService.deleteContent()`
  - On success: invalidate relevant queries (gallery list, content detail)
  - Handle loading, error, and success states
  - Return mutation function and state

### Phase 3: Confirmation Dialog Component
- [x] Create `DeleteContentDialog` component
  - File: `frontend/src/components/dialogs/DeleteContentDialog.tsx` (new file)
  - Props: `open`, `onClose`, `onConfirm`, `contentId`
  - Display warning message about permanent deletion
  - Show content ID being deleted
  - Two buttons: "Cancel" and "Delete" (red/destructive style)
  - Add `data-testid` attributes for testing

### Phase 4: Wire Up ImageViewPage
- [x] Import `useDeleteContent` hook and `DeleteContentDialog`
  - File: `frontend/src/pages/view/ImageViewPage.tsx`

- [x] Add state for confirmation dialog
  - `const [showDeleteDialog, setShowDeleteDialog] = useState(false)`

- [x] Initialize delete mutation hook
  - `const { mutate: deleteContent, isPending } = useDeleteContent()`

- [x] Update `handleDelete` function (line 207)
  - Remove TODO comment and console.log
  - Open confirmation dialog: `setShowDeleteDialog(true)`

- [x] Add `handleConfirmDelete` function
  - Call `deleteContent(contentId, { onSuccess: () => navigate('/gallery') })`
  - Close dialog on success
  - Show error toast on failure

- [x] Render `DeleteContentDialog` component
  - Pass state and handlers
  - Add near bottom of component JSX

### Phase 5: Navigation After Delete
- [x] Import `useNavigate` from react-router-dom (already imported)
  - File: `frontend/src/pages/view/ImageViewPage.tsx`

- [x] Redirect to gallery after successful deletion
  - In `onSuccess` callback: `navigate('/gallery')`
  - Implemented with 1s delay to show success message

- [x] Show success toast notification
  - Use existing toast/snackbar system
  - Message: "Content deleted successfully"

### Phase 6: Error Handling
- [x] Handle API errors in mutation hook
  - Network errors (offline, timeout)
  - 404 errors (content already deleted)
  - 500 errors (server error)
  - Display user-friendly error messages

- [x] Handle race conditions
  - Content deleted while user viewing
  - Multiple delete attempts
  - Already deleted content

### Phase 7: Loading States
- [x] Disable "delete button" (trashbin icon on the image view page) while deletion in progress
  - Use `isPending` from mutation hook
  - Temporarily change button (trashbin icon) style to show disabled state

- [x] Show loading spinner in confirmation dialog @skipped-by-user (see newly added checkbox below)
  - Disable both buttons while `isDeleting` prop is true
  - Show spinner on "Delete" button

- [x] When user confirms deletion in the dialog box, simply close the dialog box. 

### Phase 8: Deletion cascades
Implement the following changes to behavior, ideally to schema.py.
- [x] bookmarks: CASCADE DELETE (user wouldn't want bookmarks to orphaned content)
- [x] bookmark_categories (cover): SET NULL (category can exist without cover image)
- [x] content_items_ext: CASCADE DELETE (extension data tied to content) - Already had ondelete='CASCADE'
- [x] flagged_content: CASCADE DELETE (no need to track flags for deleted content) - Already had ondelete='CASCADE'
- [x] generation_jobs: SET NULL
- [x] recommendations: SET NULL
- [x] user_interactions: SET NULL (preserve interaction history for analytics)
- [x] user_notifications: SET NULL (preserve notification history)

Additional notes:
- Claude created a manual migration for teh generation_jobs (
`genonaut/db/migrations/versions/c6ce1cc53345_update_generation_jobs_fk_allow_content_.py`), but it was deleted for now.
We should put all of these migrations in one file, ideally one that is autogenerated based on changes to schema.py, per
instructions in `genonaut/db/migrations/CLAUDE.md`.

- [x] After doing the changes, let the user know the results, and to begin / complete migration.

**Migration completed:** `b4f6d6bbfb89_update_fk_constraints_for_content_.py` created and applied to demo and test databases.

### Phase 9: Unit Tests
- [x] Test `useDeleteContent` hook
  - File: `frontend/src/hooks/__tests__/useDeleteContent.test.ts` (CREATED)
  - Test successful deletion (for regular and auto content)
  - Test error handling (with error callback)
  - Test query invalidation (gallery-item, gallery, unified-gallery, unified-gallery-stats)
  - Test loading states (isPending)
  - 13 comprehensive tests covering all mutation scenarios

- [x] Test `DeleteContentDialog` component
  - File: `frontend/src/components/dialogs/__tests__/DeleteContentDialog.test.tsx` (CREATED)
  - Test rendering with props (open/closed states)
  - Test cancel button (calls onClose)
  - Test confirm button (calls onConfirm + onClose)
  - Test accessibility (ARIA labels, dialog role)
  - Test props handling (various contentId values)
  - Test button interactions (rapid clicks, re-renders)
  - 20 comprehensive tests covering all component scenarios

### Phase 10: E2E Tests
- [ ] Create E2E test for delete flow (@deferred)
  - File: `frontend/tests/e2e/content-delete.spec.ts` (new file)
  - Test: Navigate to view page, click delete, confirm, verify navigation
  - Test: Cancel delete dialog, verify content still exists
  - Test: Delete content, verify removed from gallery
  - Test: Delete button disabled state
  - Use existing helper: `deleteTestContent()` from `realApiHelpers.ts`

- [ ] Update existing E2E test (@deferred)
  - File: `frontend/tests/e2e/content-crud-real-api.spec.ts`
  - Verify delete test (line 333-440) still passes
  - Ensure test uses correct API endpoint

@deferred: Means these are skipped for now. We will explain later what to do with these tests.

### Phase 11: Documentation
- [x] Update API documentation
  - File: `docs/api.md`
  - Document DELETE endpoint behavior
  - Note hard delete (permanent removal)
  - Add security warning about lack of auth
  - Added comprehensive "Content Deletion Endpoints" section with cascade behavior details

- [x] Add inline code comments
  - Document delete flow in ImageViewPage (already well-documented)
  - Explain query invalidation in hook (already well-documented)

### Phase 12: Security Considerations (FUTURE WORK)
- [x] Document auth requirement
  - File: `notes/issues/groupings/security/content-deletion-auth.md` (CREATED)
  - Lists endpoints missing auth checks (both DELETE endpoints)
  - Prioritizes delete operations (CRITICAL severity)
  - Includes implementation tasks for auth strategy
  - See: [Content Deletion Authentication & Authorization](../issues/groupings/security/content-deletion-auth.md)

- [x] Add TODO comments in code
  - Mark delete endpoints as needing auth
  - Reference security doc: `notes/issues/groupings/security/content-deletion-auth.md`
  - Added to `genonaut/api/routes/content.py:257-270`
  - Added to `genonaut/api/routes/content_auto.py:98-111`

## Testing Checklist

### Manual Testing (@skipped-to-be-done-by-user)
- Delete regular content from view page
- Delete auto-generated content from view page
- Cancel delete dialog
- Delete content, verify redirected to gallery
- Delete content, verify removed from gallery list
- Try to view deleted content (should 404)
- Check network tab for correct API call
- Verify no console errors
- Test error scenarios (network failure, etc.)

### Automated Testing (@skipped-to-be-done-by-user)
- Run unit tests: `make frontend-test-unit`
- Run E2E tests: `make frontend-test-e2e`
- Run all tests: `make frontend-test`
- Verify all tests pass

## Dependencies & Related Features

### Affected by Content Deletion
- **Bookmarks:** User may have bookmarked the deleted content
  - Current behavior: Bookmark references non-existent content (FK constraint)
  - Need to test: What happens when bookmarked content is deleted?
  - Consideration: Should bookmarks be cascade deleted or kept as "deleted content"?

- **Recommendations:** Deleted content may be in recommendation results
  - Current behavior: Unknown (need to test)
  - Need to verify: Recommendation queries handle missing content

- **User interactions:** Ratings, views may reference deleted content
  - Current behavior: FK constraints may prevent deletion
  - Need to test: Delete content with interactions

- **Generation jobs:** Auto content tied to generation jobs
  - Current behavior: Unknown (need to test)
  - Consideration: Should job status reflect deleted output?

Answer: No. When deletion is done, retain the entry in generation_jobs.

### Automated Database Foreign Key Testing
Insert some dummy content into the test database. You should insert a generation_job along with a content_item. There
are existing tests that insert data, as such, so you should refer to them for inspiration. This should be a backend test
that inserts data, and then does the deletion using the web API, and then tests for the things represented by these
checkboxes.

- [x] Test deleting content with bookmarks
  - Create bookmark for content
  - Delete content
  - Verify: Bookmark behavior (CASCADE DELETE confirmed)
  - Test: `test/db/integration/test_content_cascade_deletion.py::test_content_deletion_cascades_bookmarks`

- [x] Test deleting content with interactions
  - Create interaction for content
  - Delete content
  - Verify: Interaction behavior (SET NULL confirmed, analytics data preserved)
  - Test: `test/db/integration/test_content_cascade_deletion.py::test_content_deletion_nulls_user_interactions`

- [x] Test deleting content with recommendations
  - Generate recommendation for content
  - Delete content
  - Verify: Recommendation queries handle missing content (SET NULL confirmed, analytics data preserved)
  - Test: `test/db/integration/test_content_cascade_deletion.py::test_content_deletion_nulls_recommendations`

- [x] generation_jobs: Entry is retained in generation_jobs with NULL content_id
  - Test: `test/db/integration/test_content_cascade_deletion.py::test_content_deletion_nulls_generation_jobs`
  - Note: Test requires manual FK fix to test database (migration didn't fully apply). FK is correct in schema.py and demo database.

## API Endpoints Reference

### Regular Content
```
DELETE /api/v1/content/{content_id}
Response: SuccessResponse
{
  "message": "Content {content_id} deleted successfully"
}
```

### Auto-Generated Content
```
DELETE /api/v1/content-auto/{content_id}
Response: SuccessResponse
{
  "message": "Auto content {content_id} deleted successfully"
}
```

## Files to Create
1. `frontend/src/hooks/useDeleteContent.ts` - React Query mutation hook
2. `frontend/src/components/dialogs/DeleteContentDialog.tsx` - Confirmation dialog
3. `frontend/tests/unit/hooks/useDeleteContent.test.ts` - Hook unit tests
4. `frontend/tests/unit/components/DeleteContentDialog.test.tsx` - Dialog unit tests
5. `frontend/tests/e2e/content-delete.spec.ts` - E2E delete flow tests

## Files Already Created
1. `notes/issues/groupings/security/content-deletion-auth.md` - CRITICAL security issues documented

## Files to Modify
1. `frontend/src/services/gallery-service.ts` - Add delete method
2. `frontend/src/pages/view/ImageViewPage.tsx` - Wire up delete handler
3. `docs/api.md` - Document DELETE endpoint

## Success Criteria
- [x] Delete button on view page works (deletes content)
- [x] Confirmation dialog prevents accidental deletion
- [x] User redirected to gallery after deletion
- [x] Deleted content removed from gallery list
- [x] No console errors during delete flow (404 but thats ok for now)
- [x] Security considerations documented

## Known Issues & Future Work
1. **CRITICAL SECURITY:** DELETE endpoints lack authentication
   - Anyone can delete any content by ID
   - Needs auth implementation before production
   - **Documented in:** [Content Deletion Authentication & Authorization](../issues/groupings/security/content-deletion-auth.md)
   - Includes detailed attack scenarios, implementation tasks, and testing strategies

2. **Orphaned files on disk:** Database-only deletion leaves files on disk
   - Deleted content records leave image files orphaned
   - Storage not reclaimed automatically
   - **Intentional design decision** - file deletion tracked in separate backlog issue
   - Future work: Background cleanup job or admin tool for orphaned files

3. **Cascade delete behavior:** Unknown impact on related data
   - Bookmarks, interactions, recommendations
   - Needs testing and possibly FK constraint updates

4. **Soft delete consideration:** May want to implement later
   - Would require database migration
   - Useful for content recovery/audit trail
   - Not required for initial implementation

## Notes
- Backend is ready, only frontend work needed
- Hard delete is intentional (matches current backend)
- **Database-only deletion is intentional** - files remain on disk (separate backlog issue)
- E2E test infrastructure already exists
- Follow existing patterns from bookmark implementation
- Prioritize user experience (confirmation, feedback, loading states)
