# Content Deletion Features

## Task Description

This document outlines the implementation of content deletion functionality across multiple areas of the Genonaut application. Currently, deletion functionality exists in some places but needs to be implemented or fixed in others.

### Current State

**Implemented:**
- Notification deletion: Fully working with confirmation dialog
  - Location: `NotificationsPage.tsx`
  - Features: Delete button, confirmation dialog, API integration
  - Test: `NotificationsPage.test.tsx` has passing tests

**Partially Implemented:**
- History page (generation history) deletion: UI exists but doesn't work
  - Location: `GenerationHistory.tsx` line 100-103
  - Current behavior: Just console.logs, no actual deletion
  - Component: `GenerationCard.tsx` has delete button with `data-testid="delete-generation"`

**Not Implemented:**
- Individual view pages: No delete button visible
  - Location: `ImageViewPage.tsx`
  - User request: Add grey trashbin icon in row 1 beneath image, to the far right of title
  - Note: Doesn't have to actually work yet, just needs to be visible

**Tests:**
- `content-crud-real-api.spec.ts:285` - "deletes content with confirmation"
  - Currently skipped because delete functionality not found in gallery UI
  - This test should remain skipped for now

### Goals

1. Add visual delete button to individual view pages (doesn't need to work yet)
2. Implement working deletion for generation history
3. Document the implementation plan for future work
4. Ensure tests are properly skipped or passing

## Implementation Plan

### Phase 1: Visual Updates to View Pages

- [x] Add delete icon button to ImageViewPage.tsx
  - [x] Import DeleteIcon from @mui/icons-material
  - [x] Add IconButton in appropriate location (row 1, far right of title)
  - [x] Style as grey trashbin icon
  - [x] Add data-testid="delete-content-button"
  - [x] Add tooltip "Delete Content"
  - [x] Wire up to stub handler (console.log for now)
  - [x] Verify UI placement matches requirements

### Phase 2: Implement Generation History Deletion

- [x] Update GenerationHistory.tsx
  - [x] Replace console.log in handleDeleteGeneration with confirmation dialog
  - [x] Add state for confirmation dialog (similar to notifications)
  - [x] Implement deleteGenerationJob service call
  - [x] Add loading/error states
  - [x] Refresh list after successful deletion
  - [x] Add proper error handling

- [x] Update generation-job-service.ts
  - [x] Add deleteGenerationJob function if not exists
  - [x] Implement DELETE endpoint call
  - [x] Handle response and errors
  - [x] Add TypeScript types

- [ ] Backend verification
  - [ ] Verify DELETE endpoint exists in backend API @dev
  - [ ] Test endpoint manually if needed @dev
  - [ ] Document any issues found

### Phase 3: Testing

- [x] Review content-crud-real-api.spec.ts
  - [x] Verify test is still appropriately skipped
  - [x] Skip message is already clear: 'Delete functionality not found in UI'

- [ ] Add or update tests for generation history deletion
  - [ ] Unit tests for GenerationHistory component @skipped-until-backend-ready
  - [ ] E2E tests for deletion flow (if applicable) @skipped-until-backend-ready
  - [ ] Test confirmation dialog
  - [ ] Test successful deletion
  - [ ] Test error handling

- [x] Verify notification deletion tests still pass
  - [x] Run NotificationsPage.test.tsx
  - [x] Deletion test passing (3/4 tests pass, 1 unrelated failure)

### Phase 4: Documentation and Cleanup

- [x] Update component documentation
  - [x] Code already includes comments explaining TODO items
  - [x] Deletion flow documented in deleting-content.md

- [ ] Update notes/unskip-tests-e2e.md if applicable
  - [ ] Not needed - test status unchanged

- [x] Create notes/issues/by_priority/medium/deleting-content.md
  - [x] Document full deletion implementation plan
  - [x] List all locations needing deletion
  - [x] Document API endpoints needed
  - [x] Add checklist for future work
  - [x] Document questions for developer

- [ ] Update README.md if needed
  - [ ] Not needed - no user-facing features changed yet (buttons visible but not functional)

## Tags

- `@dev`: Requires developer action or input before proceeding
- `@skipped-until-backend-ready`: Blocked until backend DELETE endpoint is verified and tested

## Questions

Questions for the developer will be documented here as they arise.

## Technical Notes

### Deletion Patterns

The application should follow consistent patterns for deletion:

1. **User Confirmation**: All deletions should require confirmation via dialog
2. **Loading States**: Show loading indicator during deletion
3. **Error Handling**: Display user-friendly error messages
4. **Optimistic Updates**: Consider removing from UI immediately, rollback on error
5. **Toast Notifications**: Show success/error toast after deletion

### Component Locations

- **View Pages**: `/Users/joeflack4/projects/genonaut/frontend/src/pages/view/ImageViewPage.tsx`
- **Generation History**: `/Users/joeflack4/projects/genonaut/frontend/src/components/generation/GenerationHistory.tsx`
- **Generation Card**: `/Users/joeflack4/projects/genonaut/frontend/src/components/generation/GenerationCard.tsx`
- **Notifications**: `/Users/joeflack4/projects/genonaut/frontend/src/pages/notifications/NotificationsPage.tsx`

### Data TestIDs

Following project conventions:
- Delete buttons: `{page-or-component}-delete-{id}` or `delete-{entity}-button`
- Confirmation dialogs: `{page-or-component}-delete-dialog`
- Confirm buttons: `{page-or-component}-delete-confirm`
- Cancel buttons: `{page-or-component}-delete-cancel`

### Example: Notification Deletion (Reference Implementation)

The notifications page has a complete deletion implementation that can serve as a reference:

```typescript
// State
const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null)

// Mutation
const deleteMutation = useMutation({
  mutationFn: (notificationId: number) => deleteNotification(notificationId, userId),
  onSuccess: () => {
    setPendingDeleteId(null)
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }
})

// Handlers
const handleRequestDelete = (event: React.MouseEvent, notificationId: number) => {
  event.stopPropagation()
  setPendingDeleteId(notificationId)
}

const handleConfirmDelete = async () => {
  if (pendingDeleteId === null || deleteMutation.isPending) return
  try {
    await deleteMutation.mutateAsync(pendingDeleteId)
  } catch (error) {
    console.error('Failed to delete notification:', error)
  }
}
```
