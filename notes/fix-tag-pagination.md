# Fix Tag Pagination Issue

**Date Created**: 2025-10-21
**Status**: Not Started
**Related Work**: Performance optimization work in `notes/perf-updates-non-db--sqlalchemy.md`

## Problem Statement

The tags widget in the gallery options sidebar is only showing 1 page of tags (~25 tags) when there are 100+ tags available in the database. Users need to be able to browse all available tags to select them for filtering content.

### Observed Behavior
- Tag widget shows only ~25 tags
- No pagination controls visible or functional
- Unable to browse/select tags beyond the first page
- This prevents users from testing tag query combinations with less common tags

### Expected Behavior
- All 100+ tags should be browsable
- Pagination controls should allow navigating through all tag pages
- Users should be able to select any tag from the full tag list

## Background Context

This issue was discovered during performance optimization work on tag query filtering. While fixing COUNT query performance for multi-tag queries, we deferred this frontend pagination issue to focus on the backend query optimization first.

**Related fixes completed:**
- Optimized COUNT queries for multi-tag filtering (2-7s vs 12-17s, 5.2x faster)
- Implemented CTE GROUP BY strategy in `genonaut/api/services/content_query_strategies.py:352-388`
- Created comprehensive test suite in `test/api/test_tag_query_combinations.py`
- All 6 tag query combination tests passing

## Task Checklist

### Phase 1: Investigation
- [ ] Identify the tags endpoint being called by the frontend
  - Check API endpoint path and parameters
  - Verify current pagination parameters (page, page_size, etc.)
  - Document current API response structure
- [ ] Check tags endpoint implementation
  - Review endpoint code in `genonaut/api/routes/tags.py`
  - Verify pagination logic is implemented
  - Check if pagination metadata is returned correctly
- [ ] Examine frontend tag widget component
  - Identify React component responsible for tag selection
  - Check if pagination controls are implemented
  - Verify if component is handling pagination metadata from API
- [ ] Test tags endpoint directly via API
  - Query `/api/v1/tags` with different page parameters
  - Verify total count and total pages are correct
  - Confirm pagination actually returns different results per page

### Phase 2: Root Cause Analysis
- [ ] Determine if issue is backend or frontend
  - Backend: API not implementing pagination correctly
  - Frontend: Component not handling pagination controls
  - Integration: Mismatch between API contract and frontend expectations
- [ ] Document the root cause with evidence
  - Include API responses showing the issue
  - Include frontend component code showing the issue
  - Note any error messages in browser console

### Phase 3: Backend Fix (if applicable)
- [ ] Implement or fix pagination in tags endpoint
  - Ensure endpoint accepts `page` and `page_size` parameters
  - Return correct pagination metadata (total_count, total_pages, current_page)
  - Test with various page parameters
- [ ] Add/update API tests for tag pagination
  - Test requesting different pages
  - Test page_size limits
  - Verify total_count accuracy
- [ ] Document changes in `docs/api.md`

### Phase 4: Frontend Fix (if applicable)
- [ ] Add pagination controls to tag widget
  - Implement page navigation (previous/next buttons)
  - Show current page / total pages
  - Handle page changes by calling API with new page parameter
- [ ] Update component to handle pagination metadata
  - Parse total_pages from API response
  - Track current page in component state
  - Disable prev/next buttons appropriately at boundaries
- [ ] Add loading states during page transitions
- [ ] Add E2E tests for tag pagination
  - Test navigating between tag pages
  - Test selecting tags from different pages
  - Verify tag selection works across pagination

### Phase 5: Verification
- [ ] Manual testing in browser
  - Navigate to http://localhost:5173/gallery
  - Open tag selection widget in sidebar
  - Verify all 100+ tags are browsable via pagination
  - Test selecting tags from different pages
  - Verify selected tags filter content correctly
- [ ] Run relevant test suites
  - Backend API tests: `make test-api`
  - Frontend unit tests: `make frontend-test-unit`
  - Frontend E2E tests: `make frontend-test-e2e`
- [ ] Performance testing
  - Verify tag pagination doesn't add significant latency
  - Check that page loads are <500ms

### Phase 6: Documentation
- [ ] Update API documentation if endpoint changed
- [ ] Add comments to frontend component explaining pagination logic
- [ ] Update `CHANGELOG.md` or release notes if applicable

## Files Likely to Need Changes

**Backend:**
- `genonaut/api/routes/tags.py` - Tags API endpoint
- `genonaut/api/repositories/tag_repository.py` - Tag data access layer
- `test/api/test_tags_endpoints.py` - API tests

**Frontend:**
- `frontend/src/components/...` - Tag selection widget component (exact path TBD)
- `frontend/src/services/tag-service.ts` - Tag API client (if exists)
- `frontend/tests/e2e/...` - E2E tests for tag selection

**Documentation:**
- `docs/api.md` - API endpoint documentation

## Success Criteria

- [ ] Tag widget shows pagination controls (e.g., "Page 1 of 5")
- [ ] Users can navigate through all pages of tags
- [ ] All 100+ tags are accessible for selection
- [ ] Selected tags from any page filter content correctly
- [ ] Pagination is performant (<500ms page loads)
- [ ] Tests verify pagination works correctly
- [ ] No regressions in existing tag functionality

## Notes

- Defer this work until tag query COUNT optimization is complete (COMPLETED)
- Consider using cursor-based pagination if offset pagination becomes a performance issue
- May want to add search/filter functionality to tag widget in addition to pagination
- Could consider infinite scroll as an alternative to traditional pagination
