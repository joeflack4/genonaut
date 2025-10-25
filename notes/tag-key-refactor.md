# Tag Key Refactor - Use Tag Names as Frontend Identifiers

## Problem Statement

Currently, there is an inconsistency in how tag pages are accessed in the frontend:

1. **ImageViewPage** (recently updated) navigates to tag detail pages using tag names:
   - Example: `/tags/ornate`
   - Code: `navigate(/tags/${tag})` where `tag` is the tag name string

2. **GalleryPage** navigates to tag detail pages using tag UUIDs:
   - Example: `/tags/e25615e8-a502-41f7-a638-b8d11bdf7f70`
   - Code: `navigate(/tags/${tagId})` where `tagId` is a UUID string
   - Location: GalleryPage.tsx:616 (`handleTagClick` function)

3. **TagDetailPage** expects a UUID in the route parameter:
   - It receives `params.tagId` and passes it directly to `useTagDetail(tagId, userId)`
   - The hook calls `/api/v1/tags/${tagId}` which expects a UUID
   - Location: TagDetailPage.tsx:52-55

This creates a broken user experience:
- From image view page: clicking "ornate" tag -> navigates to `/tags/ornate` -> fails (404 or error)
- From gallery sidebar: clicking "ornate" tag -> navigates to `/tags/{uuid}` -> works

## Current Architecture

### Frontend
- **Gallery URL params**: Uses tag names in URL (`?tags=ornate,landscape`)
- **Gallery internal state**: Uses tag UUIDs in `selectedTags` array
- **Gallery mapping**: Maintains bidirectional maps `tagNameToIdMap` and `tagIdToNameMap`
- **TagFilter component**: Works with tag UUIDs internally
- **Navigation**: Inconsistent - some places use names, some use UUIDs

### Backend
The backend **already supports both approaches**:
- `/api/v1/tags/{tag_id}` - Get tag detail by UUID (tags.py:410)
- `/api/v1/tags/by-name/{tag_name}` - Get tag detail by name (tags.py:442)

Tag names are:
- Unique (enforced by database constraint)
- Indexed in the database
- Therefore just as efficient as UUIDs for lookups

### Frontend Service Layer
- `tag-service.ts` has `getTagDetail(tagId: string, userId?: string)` which calls the UUID endpoint
- Does NOT have a method for the by-name endpoint
- All other tag endpoints use UUIDs

## Desired Solution

Make tag names the universal identifier for tag detail pages in the frontend. This provides:
- **User-friendly URLs**: `/tags/ornate` instead of `/tags/e25615e8-a502-41f7-a638-b8d11bdf7f70`
- **Consistency**: All navigation to tag pages uses the same format
- **Bookmarkable URLs**: Users can share meaningful tag URLs
- **SEO-friendly**: If the app becomes public, tag names are better for search engines

UUIDs would only be used:
- Internally in API calls where the backend doesn't support name-based lookup
- As React keys for rendering lists
- In internal state where appropriate

## Implementation Approach

### Phase 1: Backend Service Method Addition
Add a `getTagDetailByName` method to the frontend tag service to wrap the existing backend endpoint.

### Phase 2: Frontend Route Handling
Update TagDetailPage to:
1. Detect if the route parameter is a UUID or a name
2. Call the appropriate service method based on the parameter type

This provides backward compatibility during the transition.

### Phase 3: Gallery Navigation Updates
Update GalleryPage's `handleTagClick` to navigate using tag names instead of UUIDs.

### Phase 4: Unified Endpoint (Optional Backend Enhancement)
Consider updating the backend's main tag detail endpoint to accept either UUID or name, eliminating the need for detection logic in the frontend. This would involve:
- Modifying `/api/v1/tags/{tag_id}` to detect parameter type
- Deprecating the `/api/v1/tags/by-name/{tag_name}` endpoint (or keeping it for explicit name lookups)

This is optional and could be deferred to a later iteration.

### Phase 5: Testing & Documentation
- Update unit tests for affected components
- Add E2E tests for tag navigation from multiple entry points
- Update documentation

## Implementation Phases (Detailed in tasks document)

See `tag-key-refactor-tasks.md` for the detailed task breakdown.

## Questions & Concerns

### Q1: UUID Detection Strategy
**Question**: Should we use a regex to detect UUIDs vs names, or should we check format more strictly?

**Current thinking**: Use a UUID regex pattern. If it matches UUID format, treat as UUID. Otherwise, treat as name. 
This provides good backward compatibility.

**Alternative**: Always treat route parameter as name, and update all existing links immediately. More breaking but cleaner.

**User input needed**: Which approach do you prefer?

Answer: if you're talking about the frontend, change it to only accept names. If you're talking about the backend, I 
think we should not use regex either. We should have explicit params for GET by UUID or name. 

### Q2: Backward Compatibility
**Question**: Do we need to support old UUID-based URLs indefinitely, or can we break them after a transition period?

**Current thinking**: Support both during transition (Phases 1-3), then optionally deprecate UUID URLs in a future release.

**User input needed**: What's your preference for backward compatibility?

Answer: You can break them now. We're not in production yet, and we also have a good test suite, including new tests you
are making. All that combined with manual testing--we'll be fine.

### Q3: Other Tag Endpoints
**Question**: Should we update OTHER tag-related frontend code to use names where possible, or just focus on the tag detail page for now?

**Current thinking**: Focus on tag detail navigation first (this document's scope), then consider broader refactoring later if needed.

**User input needed**: Confirm scope is acceptable.

Answer: All areas in the frontend should use tag names instead of UUIDs now as I mentioned in the original prompt.

### Q4: Backend Endpoint Consolidation
**Question**: Should we proceed with Phase 4 (unified backend endpoint) as part of this refactor, or defer it?

**Current thinking**: Defer to a separate task. The by-name endpoint already exists and works. We can consolidate later if desired.

**User input needed**: Confirm whether Phase 4 should be included in this work or deferred.

Answer: By unified endpoint, it sounds like you're talking about `/api/v1/tags/{tag_id}`. I updated Phase 4. I do want 
you to do it, and you should do it right after phase 3. And I updated it, changing and removing some subtasks. So 
re-read it and follow my new plan. 

## Success Criteria

1. Users can navigate to tag detail pages from any location using tag names
2. URLs like `/tags/ornate` work correctly
3. All existing tests pass (or are updated appropriately)
4. Gallery tag navigation works consistently with image view tag navigation
5. No regressions in tag filtering or other tag-related functionality

## Files Affected

### Frontend
- `frontend/src/services/tag-service.ts` - Add getTagDetailByName method
- `frontend/src/hooks/useTags.ts` - Potentially add useTagDetailByName hook
- `frontend/src/pages/tags/TagDetailPage.tsx` - Update to detect and handle both UUID and name params
- `frontend/src/pages/gallery/GalleryPage.tsx` - Update handleTagClick to use tag names
- `frontend/src/components/gallery/TagFilter.tsx` - Update handleSelectedChipClick if needed
- `frontend/src/pages/view/ImageViewPage.tsx` - Already uses names (no change needed)

### Tests
- `frontend/src/pages/tags/__tests__/TagDetailPage.test.tsx` - Update unit tests
- `frontend/tests/e2e/tag-detail.spec.ts` - Update E2E tests
- `frontend/tests/e2e/image-view.spec.ts` - Verify tag navigation works
- `frontend/tests/e2e/gallery-tag-filters.spec.ts` - Update if affected
- `frontend/src/services/__tests__/tag-service.test.ts` - Add tests for new method

### Backend (Optional - Phase 4)
- `genonaut/api/routes/tags.py` - Potentially consolidate endpoints

### Documentation
- Update relevant docs if tag URL format is documented anywhere
- Update this document with final decisions and outcomes

## Tags

(Tags for @skipped-until- annotations will be added here as needed during implementation)

## Timeline Estimate

- Phase 1: 30 minutes (service method + hook)
- Phase 2: 1 hour (route handling + detection logic)
- Phase 3: 30 minutes (gallery navigation update)
- Phase 4: 1-2 hours (optional backend work - deferred)
- Phase 5: 1-2 hours (testing + documentation)

**Total**: 3-4 hours (excluding Phase 4)

## References

- Backend tag routes: `genonaut/api/routes/tags.py`
- Frontend tag service: `frontend/src/services/tag-service.ts`
- Gallery page: `frontend/src/pages/gallery/GalleryPage.tsx`
- Tag detail page: `frontend/src/pages/tags/TagDetailPage.tsx`
- Image view page: `frontend/src/pages/view/ImageViewPage.tsx`
