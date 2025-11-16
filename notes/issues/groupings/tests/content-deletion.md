# Content Deletion - Deferred Tests

**Feature:** Delete content functionality (Image View Page delete button)
**Status:** Deferred
**Related:** `notes/active/delete-content.md`

## Overview

This document tracks test coverage that was deferred during the initial implementation of the content deletion feature. The feature is functionally complete with:
- Unit tests for hook and dialog component (33 tests total)
- Database FK cascade tests (4 tests)
- Manual testing performed by user

The following E2E and integration tests were identified as valuable but deferred to avoid blocking feature delivery.

## Deferred E2E Tests

### E2E Test Suite: Content Delete Flow
**File:** `frontend/tests/e2e/content-delete.spec.ts` (to be created)
**Priority:** Medium
**Estimated effort:** 2-3 hours

- [ ] Test: Navigate to view page, click delete button, confirm in dialog
  - Verify navigation back to gallery after successful deletion
  - Check that success message is displayed
  - Verify content is no longer visible in gallery

- [ ] Test: Cancel delete dialog
  - Click delete button to open dialog
  - Click cancel button
  - Verify dialog closes without deleting content
  - Verify content still exists and is viewable

- [ ] Test: Delete content and verify removal from gallery list
  - Start from gallery page with known content
  - Navigate to content view page
  - Delete the content
  - Verify it's removed from the gallery pagination

- [ ] Test: Delete button disabled state during deletion
  - Click delete and confirm
  - Verify button shows loading/disabled state
  - Verify button re-enables after operation completes (or shows error)

- [ ] Test: Delete auto-generated content (different endpoint)
  - Navigate to auto-generated content view page
  - Perform deletion
  - Verify correct API endpoint is called (`/api/v1/content-auto/{id}`)

**Implementation notes:**
- Use existing helper: `deleteTestContent()` from `realApiHelpers.ts`
- May need to extend helper to support both regular and auto content
- Tests should use real API (not mocked) to verify full integration

### E2E Test: Update Existing Delete Test
**File:** `frontend/tests/e2e/content-crud-real-api.spec.ts`
**Priority:** Low
**Estimated effort:** 30 minutes

- [ ] Verify existing delete test (lines 333-440) still passes after changes
- [ ] Ensure test uses correct API endpoint format
- [ ] Update test if delete flow changed (e.g., now shows confirmation dialog)
- [ ] Verify test covers both regular and auto content if applicable

**Context:** There may already be a delete test in the CRUD suite. Need to verify it's compatible with the new delete dialog flow.

## Additional Test Coverage (Not Yet Planned)

These tests were not in the original implementation plan but would provide valuable coverage:

### Integration Tests

- [ ] **Frontend-Backend Integration: Error Scenarios**
  - Test 404 when trying to delete non-existent content
  - Test network failure during deletion
  - Test partial failure (DB deletion succeeds but response fails)
  - Verify error messages are user-friendly

- [ ] **Frontend-Backend Integration: Concurrent Operations**
  - Test deleting content while another user is viewing it
  - Test rapid deletion of multiple items
  - Test deletion while gallery is loading/refreshing

### API Endpoint Tests

- [ ] **Backend: DELETE /api/v1/content/{id} Edge Cases**
  - Test deleting content that doesn't exist (404)
  - Test deleting content with invalid ID format
  - Test deleting content with very large ID numbers
  - Test concurrent deletion requests for same content

- [ ] **Backend: DELETE /api/v1/content-auto/{id} Edge Cases**
  - Same edge cases as regular content
  - Verify correct table (content_items_auto) is targeted

### Cascade Behavior Verification Tests

- [ ] **Integration: Verify FK Cascades in Real Scenarios**
  - Create content with bookmarks, then delete -> verify bookmarks removed
  - Create content with interactions, then delete -> verify interactions nulled
  - Create content with generation job, then delete -> verify job preserved with null content_id
  - Create content with recommendations, then delete -> verify recommendations nulled

- [ ] **Backend: Cascade Test for All 8 FK Relationships**
  - Expand beyond the 4 current FK tests to cover:
    - content_items_ext (already CASCADE, but no explicit test)
    - flagged_content (already CASCADE, but no explicit test)
    - bookmark_categories cover images (SET NULL test)

### Security & Authorization Tests (Blocked by Auth Implementation)

- [ ] **API: Authentication Required**
  - Test unauthenticated deletion request returns 401
  - Test authenticated but unauthorized deletion returns 403

- [ ] **API: Authorization - Owner Check**
  - Test user can delete their own content
  - Test user cannot delete another user's content
  - Test admin can delete any content

- [ ] **Frontend: UI Reflects Permissions**
  - Delete button hidden for content user doesn't own
  - Delete button visible for owned content
  - Delete button visible for admins

**Note:** These security tests are blocked until authentication is implemented. See `notes/issues/groupings/security/content-deletion-auth.md`.

### Accessibility Tests

- [ ] **Dialog Accessibility**
  - Test keyboard navigation (Tab, Enter, Escape)
  - Test screen reader announces dialog content correctly
  - Test focus management (focus trap, return focus after close)
  - Test ARIA labels are correct and descriptive

- [ ] **Delete Button Accessibility**
  - Test keyboard activation (Space, Enter)
  - Test disabled state is announced to screen readers
  - Test tooltip/label is accessible

### Performance Tests

- [ ] **Deletion Performance Under Load**
  - Test deletion of content with 1000+ bookmarks
  - Test deletion with complex FK relationships
  - Verify query invalidation doesn't cause excessive re-fetches
  - Test cascade deletion performance with large datasets

### File System Tests

- [ ] **Orphaned Files**
  - Verify files are NOT deleted from disk (documented behavior)
  - Create test for manual file cleanup process
  - Test identifying orphaned files after deletion
  - Consider adding automated cleanup job (future feature)

## Test Organization

**Unit Tests:** ✅ Complete (33 tests)
- `frontend/src/hooks/__tests__/useDeleteContent.test.ts` (13 tests)
- `frontend/src/components/dialogs/__tests__/DeleteContentDialog.test.tsx` (20 tests)

**Database Tests:** ✅ Mostly Complete (4 tests)
- `test/db/integration/test_content_cascade_deletion.py` (4 FK cascade tests)
- Missing: Explicit tests for content_items_ext and flagged_content cascades

**E2E Tests:** ⏸️ Deferred (tracked in this document)

**Integration Tests:** ⏸️ Not yet planned (tracked in this document)

**Security Tests:** ⏸️ Blocked by auth implementation

## Priority Recommendations

**High Priority (Do Next):**
1. E2E delete flow test suite (main user journey coverage)
2. API edge case tests (ensure robust error handling)

**Medium Priority:**
3. Frontend-backend integration error scenarios
4. Update existing CRUD E2E test

**Low Priority:**
5. Accessibility tests (important but feature is functional)
6. Performance tests (optimize after baseline is established)

**Blocked:**
- All security/authorization tests (waiting on auth implementation)

## Implementation Strategy

When ready to implement these tests:

1. Start with the E2E delete flow suite (highest ROI for test coverage)
2. Run existing E2E CRUD test to see if updates are needed
3. Add API edge case tests to improve error handling
4. Consider accessibility and performance tests for polish

## Related Documentation

- Feature implementation: `notes/active/delete-content.md`
- Security requirements: `notes/issues/groupings/security/content-deletion-auth.md`
- FK migration issue: `notes/issues/by_priority/low/generation-jobs-fk-migration-issue.md`
- API documentation: `docs/api.md#content-deletion-endpoints`
- Testing guide: `docs/testing.md`
