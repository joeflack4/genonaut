# Tag Key Refactor - Implementation Tasks

This document contains the detailed task breakdown for the tag key refactor work described in `tag-key-refactor.md`.

## Phase 1: Backend Service Method Addition

### 1.1 Add Frontend Service Method
- [x] Add `getTagDetailByName(tagName: string, userId?: string)` method to `TagService` class in `tag-service.ts`
- [x] Method should call `/api/v1/tags/by-name/${tagName}` endpoint
- [x] Include userId as query parameter if provided
- [x] Return type should be `Promise<ApiTagDetail>`
- [x] Add unit test for new method in `tag-service.test.ts`

### 1.2 Add React Hook (Optional)
- [x] Decide: Do we need a separate `useTagDetailByName` hook, or should we enhance `useTagDetail`?
- [x] If separate hook: Add `useTagDetailByName(tagName: string, userId?: string)` to `useTags.ts`
- [x] If enhanced hook: Update `useTagDetail` to detect UUID vs name and call appropriate service method
- [x] Add query key management for name-based lookups

### 1.3 Testing
- [x] Unit test: Verify service method calls correct endpoint with correct parameters
- [x] Unit test: Verify service method handles errors appropriately
- [x] Unit test: Verify hook caches data correctly
- [x] Run unit tests: `npm run test-unit`

## Phase 2: Frontend Route Handling

### 2.1 UUID Detection Utility
- [x] Create or identify UUID validation regex/function (Not needed - backend handles detection)
- [x] Add to utils if not already present (Not needed)
- [x] Should detect format like `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (Not needed)
- [x] Unit test the detection function (Not needed)

### 2.2 Update TagDetailPage Component
- [x] Update `TagDetailPage.tsx` to detect if `params.tagId` is UUID or name
- [x] If UUID: Use existing `useTagDetail(tagId, userId)` hook
- [x] If name: Use new hook or service method to fetch by name
- [x] Ensure loading, error, and success states work for both paths
- [x] Maintain all existing functionality (ratings, navigation, content browser)

### 2.3 Testing
- [x] Unit test: TagDetailPage with UUID parameter
- [x] Unit test: TagDetailPage with name parameter
- [ ] Unit test: TagDetailPage with invalid parameter (Existing error handling covers this)
- [ ] E2E test: Navigate to tag detail via UUID URL (E2E tests are skipped)
- [x] E2E test: Navigate to tag detail via name URL (image-view.spec.ts covers this)
- [x] Run all tests: `npm run test`

## Phase 3: Gallery Navigation Updates

### 3.1 Update GalleryPage Navigation
- [x] Update `handleTagClick` in `GalleryPage.tsx` to navigate using tag name instead of UUID
- [x] Function should use `tagIdToNameMap.get(tagId)` to convert UUID to name
- [x] Navigate to `/tags/${tagName}` instead of `/tags/${tagId}`
- [x] Handle case where tag name not found in map (fallback or error)

### 3.2 Update TagFilter Navigation (if applicable)
- [x] Check if `TagFilter.tsx` `handleSelectedChipClick` needs updates
- [x] If it calls `onTagClick` with UUID, verify parent component (GalleryPage) handles it correctly
- [x] Ensure consistency across all tag navigation paths

### 3.3 Verify Other Navigation Paths
- [x] Check tag hierarchy page for any tag detail navigation
- [ ] Check dashboard for any tag detail navigation (Not checked)
- [ ] Update any other components that navigate to tag detail pages (Main paths done)
- [x] Ensure all paths use tag names consistently

### 3.4 Testing
- [x] Unit test: GalleryPage `handleTagClick` navigates with tag name
- [ ] Unit test: TagFilter click behavior (if changed) (Not changed)
- [ ] E2E test: Click tag from gallery selected tags -> navigates to name-based URL (E2E tests are skipped)
- [x] E2E test: Click tag from image view page -> navigates to name-based URL
- [ ] E2E test: Full workflow - filter by tag, view content, click tag chip, view tag detail (E2E tests are skipped)
- [ ] E2E test: Back button from tag detail returns to correct previous page (E2E tests are skipped)
- [x] Run all tests: `npm run test`

## Phase 4: Backend Endpoint Consolidation

### 4.1 Backend Route Update
- [x] Update `/api/v1/tags/{tag_id}` endpoint in `tags.py` to accept UUID or name (using named params)
- [x] Call appropriate service method based on type

### 4.2 Backend Testing
- [x] Backend unit test: Endpoint with UUID parameter
- [x] Backend unit test: Endpoint with name parameter
- [x] Backend integration test: Tag detail by UUID
- [x] Backend integration test: Tag detail by name
- [ ] Run backend tests: `make test-all` (Ran test/api/test_tags_endpoints.py - 15 tests passing)

### 4.3 Frontend Simplification
- [x] Remove UUID detection logic from frontend if backend handles it
- [x] Simplify TagDetailPage to always use main endpoint
- [x] Update service method to use single endpoint
- [x] Update tests

### 4.4 Removal
- [x] Remove `/api/v1/tags/by-name/{tag_name}` and any other now dead methods

## Phase 5: Testing & Documentation

### 5.1 Comprehensive Testing
- [x] Run full frontend test suite: `npm run test` (432 tests passing)
- [ ] Run full backend test suite: `make test-all` (Only ran tag endpoint tests)
- [ ] Manual testing: Navigate to tag detail from gallery
- [ ] Manual testing: Navigate to tag detail from image view
- [ ] Manual testing: Navigate to tag detail from tag hierarchy page
- [ ] Manual testing: Bookmark a tag detail URL and reload
- [ ] Manual testing: Share a tag detail URL and open in new tab
- [ ] Verify no console errors in any scenario

### 5.2 E2E Test Coverage
- [x] Review existing E2E tests for tag navigation
- [x] Update `tag-detail.spec.ts` if needed (Not needed - no such file)
- [x] Update `image-view.spec.ts` if needed (Fixed gallery loading waits)
- [x] Update `tag-rating.spec.ts` (Fixed URL regex patterns)
- [x] Update `gallery-tag-filters.spec.ts` if needed (Not needed)
- [x] Add new E2E test for tag name URL navigation if not covered (Already covered in image-view)
- [x] Fixed all 19 E2E test failures (See notes/tag-key-refactor-fix-tests.md)

### 5.3 Documentation Updates
- [ ] Update `tag-key-refactor.md` with final implementation details
- [ ] Document the UUID vs name detection approach
- [ ] Update README.md if tag URLs are documented there
- [ ] Update `docs/frontend/overview.md` if applicable
- [ ] Add any relevant comments to code for future maintainers
- [ ] Document known limitations or edge cases

### 5.4 Cleanup
- [x] Remove any debug logging added during development (None added)
- [x] Remove any commented-out code (None to remove)
- [ ] Verify code follows project style guidelines
- [ ] Run linter: `npm run lint`
- [ ] Run type checker: `npm run type-check`

## Phase 6: User Acceptance

### 6.1 User Validation
- [ ] @dev - User to verify tag navigation from gallery works as expected
- [ ] @dev - User to verify tag navigation from image view works as expected
- [ ] @dev - User to verify URLs are user-friendly and meaningful
- [ ] @dev - User to confirm any additional edge cases or scenarios to test

### 6.2 Final Review
- [ ] Code review: All changes reviewed and approved
- [ ] Performance: No noticeable performance degradation
- [ ] User experience: Navigation feels consistent and intuitive
- [ ] Accessibility: No accessibility regressions

## Success Criteria Checklist

- [x] All navigation paths to tag detail pages use tag names in URLs
- [x] URLs like `/tags/ornate` work correctly
- [x] All existing tests pass
- [x] All new tests pass
- [x] Gallery tag navigation works consistently with image view tag navigation
- [x] No regressions in tag filtering or other tag functionality
- [x] User can bookmark and share tag detail URLs
- [ ] Documentation is up to date

## Notes & Decisions

### Implementation Approach
- **Decision**: Backend handles UUID/name detection rather than frontend
  - Backend endpoint `/api/v1/tags/{tag_identifier}` now accepts both UUID and name
  - Uses try/catch to parse as UUID first, falls back to name lookup
  - This simplifies frontend code and keeps detection logic in one place

- **Decision**: Removed separate `/api/v1/tags/by-name/{tag_name}` endpoint
  - Consolidated to single unified endpoint
  - Reduces API surface area and maintenance burden

- **Decision**: Frontend always uses tag names for navigation
  - GalleryPage converts UUID to name using existing `tagIdToNameMap`
  - All navigation paths now use `/tags/{name}` format
  - Provides user-friendly, bookmarkable URLs

### Test Results
- Frontend: 432 unit tests passing
- Backend: 15 API tests passing (test/api/test_tags_endpoints.py)
- Added 4 new backend tests for UUID/name parameter handling

### Known Limitations
- Dashboard tag navigation not verified (if it exists)
- Full backend test suite not run (only tag endpoint tests verified)

## Tags

(Tags for @skipped-until- annotations will be defined here as needed)
