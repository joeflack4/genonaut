# Content Deletion Implementation

## Status
- Priority: Medium
- Started: 2025-10-11
- Current Status: Partially implemented - UI complete, backend verification needed

## Overview
This document tracks the implementation of content deletion functionality across the Genonaut application. Deletion should be available in multiple contexts with consistent UX patterns.

## Completed Work

### 1. Individual View Pages (ImageViewPage)
- Location: `frontend/src/pages/view/ImageViewPage.tsx`
- Status: UI complete, functionality stubbed
- Details:
  - Added grey delete icon button next to title
  - Styled with hover effect (grey -> error red)
  - Test ID: `delete-content-button`
  - Currently logs to console only
  - Needs backend endpoint implementation

### 2. Generation History Deletion
- Location: `frontend/src/components/generation/GenerationHistory.tsx`
- Status: Fully implemented, pending backend verification
- Details:
  - Confirmation dialog implemented
  - Loading states handled
  - Error handling in place
  - Refreshes list after deletion
  - Service method added: `deleteGenerationJob(id)`
  - Test IDs: `generation-delete-dialog`, `generation-delete-confirm`, `generation-delete-cancel`
  - Needs backend DELETE endpoint verification

### 3. Notification Deletion
- Location: `frontend/src/pages/notifications/NotificationsPage.tsx`
- Status: Fully working (reference implementation)
- Details:
  - Complete implementation with confirmation
  - Tests passing
  - Can serve as pattern for other deletions

## Remaining Work

### Backend Verification (HIGH PRIORITY)
- [ ] Verify DELETE endpoint exists: `/api/v1/generation-jobs/{id}`
- [ ] Test endpoint manually with curl or API client
- [ ] Document endpoint behavior:
  - What happens to associated content?
  - What happens to image files?
  - Are soft deletes supported?
  - What errors can occur?
- [ ] Update API documentation if needed

### ImageViewPage Delete Implementation
- [ ] Implement confirmation dialog (similar to GenerationHistory)
- [ ] Add delete service method to content/gallery service
- [ ] Wire up to backend DELETE endpoint
- [ ] Add loading/error states
- [ ] Test with real data
- [ ] Add E2E test for deletion flow

### Gallery Page Delete Buttons
- [ ] Add delete buttons to gallery grid items
- [ ] Add delete buttons to gallery list view
- [ ] Implement confirmation dialog
- [ ] Follow same pattern as generation history
- [ ] Test IDs: `gallery-delete-{id}`, `gallery-delete-dialog`, etc.

### Testing
- [ ] Add unit tests for GenerationHistory delete functionality
- [ ] Add E2E tests for generation history deletion
- [ ] Add E2E tests for view page deletion (when implemented)
- [ ] Add E2E tests for gallery deletion (when implemented)
- [ ] Update `content-crud-real-api.spec.ts` to no longer skip when complete

### User Experience Enhancements
- [ ] Add toast notifications for successful deletions
- [ ] Consider undo functionality (optional)
- [ ] Add batch delete capability for multiple items
- [ ] Add keyboard shortcuts (e.g., Delete key)
- [ ] Add confirmation setting (always ask / never ask / ask for important items)

## Technical Notes

### Deletion Pattern
All deletion implementations should follow this pattern:

```typescript
// State
const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null)
const [isDeleting, setIsDeleting] = useState(false)
const [deleteError, setDeleteError] = useState<string | null>(null)

// Request handler
const handleRequestDelete = (id: number) => {
  setPendingDeleteId(id)
  setDeleteError(null)
}

// Confirm handler
const handleConfirmDelete = async () => {
  if (pendingDeleteId === null || isDeleting) return

  setIsDeleting(true)
  setDeleteError(null)

  try {
    await deleteService(pendingDeleteId)
    setPendingDeleteId(null)
    // Refresh data
  } catch (error) {
    setDeleteError(error.message)
  } finally {
    setIsDeleting(false)
  }
}

// Cancel handler
const handleCancelDelete = () => {
  setPendingDeleteId(null)
  setDeleteError(null)
}
```

### Test ID Conventions
- Delete button: `{context}-delete-{id}` or `delete-{entity}-button`
- Dialog: `{context}-delete-dialog`
- Confirm button: `{context}-delete-confirm`
- Cancel button: `{context}-delete-cancel`

### Backend API Requirements

Expected DELETE endpoints:
- `/api/v1/generation-jobs/{id}` - Delete generation job
- `/api/v1/content/{id}` or `/api/v1/images/{id}` - Delete content/image
- `/api/v1/notifications/{id}` - Delete notification (already working)

Expected responses:
- 204 No Content - Successful deletion
- 404 Not Found - Item doesn't exist
- 403 Forbidden - User doesn't have permission
- 409 Conflict - Item cannot be deleted due to dependencies

## Questions for Developer

1. Should deletions be soft deletes (marked as deleted) or hard deletes (removed from database)?
2. What happens to image files on disk when content is deleted?
3. Should there be a "trash" or "recycle bin" feature to recover deleted items?
4. Are there any items that should not be deletable (e.g., last remaining admin user)?
5. Should we implement batch deletion in the UI?
6. Should deletion require additional confirmation for certain item types?

## Related Files

### Frontend
- `frontend/src/pages/view/ImageViewPage.tsx` - Individual view page with delete button
- `frontend/src/components/generation/GenerationHistory.tsx` - Generation history with working delete
- `frontend/src/components/generation/GenerationCard.tsx` - Card component with delete button
- `frontend/src/pages/notifications/NotificationsPage.tsx` - Reference implementation
- `frontend/src/services/generation-job-service.ts` - Service with delete method
- `frontend/src/hooks/useGenerationJobService.ts` - Hook exposing delete method

### Tests
- `frontend/tests/e2e/content-crud-real-api.spec.ts:285` - Currently skipped delete test
- `frontend/src/pages/notifications/__tests__/NotificationsPage.test.tsx` - Working delete test

### Documentation
- `notes/deletions-temp.md` - Detailed implementation plan and progress tracking
