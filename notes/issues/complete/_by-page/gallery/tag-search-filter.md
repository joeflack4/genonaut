# Tag Search Filter Feature

## Task Description
Add a client-side tag search filter to the "Filter by tags" section in the gallery page options sidebar.

### Requirements
1. Add a "Search tags" text input widget beneath the "Sort Tags" dropdown
2. Client-side filtering only - no server queries
3. 1-second debounce after user stops typing before applying filter
4. Support two search modes:
   - **Word-based search** (default): Match tags where any word starts with any search query word
   - **Exact match search**: If query is wrapped in quotes (e.g. "anime art"), match anywhere in tag name
5. Case-insensitive matching
6. Update pagination to reflect filtered results
7. If search is empty/inactive, show all tags as normal

### Word-Based Search Logic
For query "anime art":
- Split query into words: ["anime", "art"]
- Split each tag name into words (handle hyphens as single words)
- Match if any tag word starts with any query word

Examples that MATCH "anime art":
- "anime" (word "anime" starts with "anime")
- "art" (word "art" starts with "art")
- "art styles" (word "art" starts with "art")
- "styled like anime" (word "anime" starts with "anime")
- "anime-style" (word "anime-style" starts with "anime")

Examples that DON'T match:
- "fart" (word "fart" doesn't start with "art")

### Exact Match Search Logic
For query '"anime art"' (with quotes):
- Strip quotes
- Match if tag name contains the exact string anywhere
- Case-insensitive

### Technical Implementation
- Add TextField component in TagFilter.tsx
- Implement debounced search with 1-second delay
- Filter tags array before rendering
- Update pagination to use filtered tag count
- Add data-testid attributes for testing

## Implementation Checklist

### Phase 1: Core Functionality
- [x] Add search input TextField to TagFilter component
- [x] Implement debounce hook/utility (1 second delay)
- [x] Implement word-based search filtering logic
- [x] Implement exact match (quoted) search filtering logic
- [x] Update tag list rendering to use filtered results
- [x] Update pagination to reflect filtered tag count
- [x] Add appropriate data-testid attributes

### Phase 2: Testing
- [x] Create E2E tests for tag search functionality
- [x] Test word-based search with various queries
- [x] Test exact match (quoted) search
- [x] Test pagination updates with filtered results
- [x] Test debounce behavior
- [x] Test case-insensitive matching
- [x] Test empty/cleared search returns to normal state

### Phase 3: Verification
- [x] Manual testing in browser
- [x] Run E2E test suite (10/10 tests passing)
- [x] Verify no regressions in existing tag filter functionality (7/7 tests passing)

## Questions/Notes
- Using demo database tags for test cases (has 106+ tags including "anime", "art", "3D", etc.)
- Will need to handle the quotes detection carefully (check if first and last char are quotes)
- Debounce should be implemented cleanly, perhaps with useMemo/useEffect

## Implementation Summary

### Files Modified
1. `/Users/joeflack4/projects/genonaut/frontend/src/components/gallery/TagFilter.tsx`
   - Added TextField import from MUI
   - Added search state: `searchQuery` and `debouncedSearchQuery`
   - Added 1-second debounce effect using setTimeout
   - Implemented word-based filtering logic (splits on whitespace and hyphens)
   - Implemented exact match filtering (detects quotes)
   - Added client-side pagination for filtered results
   - Updated rendering to use `paginatedTags` and `filteredTotalPages`
   - Added data-testid attributes for testing

### Files Created
1. `/Users/joeflack4/projects/genonaut/frontend/tests/e2e/gallery-tag-search.spec.ts`
   - 10 comprehensive E2E tests
   - Tests cover: word-based search, exact match, pagination, debounce, case-insensitivity, clear search
   - All tests passing (10/10)

### Test Results
- **E2E Tests:**
  - New tests: 10/10 passing (gallery-tag-search.spec.ts)
  - Regression tests: 7/7 passing (gallery-tag-filters.spec.ts)
  - Total E2E: 17/17 tests passing
- **Unit Tests:**
  - All 217 tests passing (fixed 5 broken tests)
  - Fixed tests: TagFilter pagination, GalleryPage search input, TagDetailPage back button (2x), DashboardPage grid view

### Feature Behavior
- Search input appears below "Sort Tags" dropdown
- 1-second debounce prevents excessive filtering during typing
- Word-based search: splits query into words, matches if any tag word starts with any query word
- Exact match: wrap query in quotes (e.g. "anime art") to match substring anywhere in tag name
- Case-insensitive matching
- Pagination updates to reflect filtered tag count
- Empty search shows all tags
- Shows helpful message "No tags match your search" when no results
