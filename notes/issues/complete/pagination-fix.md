# Gallery Pagination Fix Plan

## Problem Analysis

The gallery is only showing 80 results across 8 pages instead of the expected millions of records from both `content_items` and `content_items_auto` tables. The issue is multi-layered:

### Current Issues:

1. **Frontend Inefficient Data Fetching**: The frontend fetches `PAGE_SIZE * 2` (20) items from each API, then filters/combines them client-side, which limits total available data
2. **Backend Default Limit**: The backend is likely using conservative defaults and not returning the actual total counts correctly
3. **Client-side Pagination**: Frontend is doing pagination after combining data from multiple sources, which limits the total dataset to what was fetched initially
4. **Duplicated Total Calculation**: The frontend calculates stats separately from the dashboard, instead of reusing the dashboard's stat API

### Root Cause:
The frontend is trying to combine multiple data sources (regular + auto content for both user and community) by fetching limited datasets from each, then paginating the combined result client-side. This approach fundamentally limits the total dataset size.

## Implementation Plan

### Phase 1: Backend API Improvements

- [x] **1.1 Create unified content endpoint** that can fetch both regular and auto content in a single request
  - [x] Add `/api/v1/content/unified` endpoint that accepts filters for content type (regular, auto, or both)
  - [x] Support creator filtering (user vs community)
  - [x] Return proper total counts for the filtered data

- [x] **1.2 Enhance existing endpoints** to return correct total counts
  - [x] Fix content and content-auto endpoints to return actual database totals, not just filtered result counts
  - [x] Ensure pagination works with large datasets (millions of records)

- [x] **1.3 Add content stats API endpoint** (if not already existing)
  - [x] Create endpoint that returns the 4 counts (user regular, user auto, community regular, community auto)
  - [x] Make this endpoint efficient for large datasets

### Phase 2: Frontend Gallery Refactor

- [x] **2.1 Replace client-side data combination** with server-side filtering
  - [x] Use the new unified content endpoint
  - [x] Remove client-side filtering and pagination logic
  - [x] Let the server handle all data combination and pagination

- [x] **2.2 Implement proper pagination**
  - [x] Calculate total pages from server-provided total count
  - [x] Use server-side pagination (skip/limit) instead of client-side slicing
  - [ ] Pre-load next page data for smooth navigation

- [x] **2.3 Reuse dashboard stats** in gallery
  - [x] Import and use the same `useGalleryStats` hook from dashboard
  - [x] Display the 4 count totals at the top of gallery options panel
  - [x] Use these totals to calculate total pages available

### Phase 3: Testing Implementation (TDD)

- [x] **3.1 Backend Tests**
  - [x] Test unified content endpoint with various filter combinations
  - [x] Test pagination with large datasets (performance tests)
  - [x] Test total count accuracy across different filters
  - [x] Test content stats endpoint accuracy

- [x] **3.2 Frontend E2E Tests**
  - [x] Test gallery pagination through all pages
  - [x] Test content type toggling and its impact on pagination
  - [x] Test that total page count matches expected values
  - [ ] Test pre-loading of next page data
  - [x] Verify gallery totals match dashboard totals

### Phase 4: Performance Optimization
Do NOT work on these yet. In fact, some, most, or all of these are likely already done.

- [ ] **4.1 Database Query Optimization**
  - [ ] Ensure proper indexes exist for pagination queries
  - [ ] Optimize COUNT queries for total calculation
  - [ ] Consider cursor-based pagination for very large datasets

- [ ] **4.2 Frontend Performance**
  - [ ] Implement virtual scrolling if needed for large page sizes
  - [ ] Add loading states for page transitions
  - [ ] Cache previous page data for back navigation

## Technical Implementation Details

### New Unified Content API Structure:
```
GET /api/v1/content/unified?content_types=regular,auto&creator_filter=all&page=1&page_size=10&sort=recent
```

### Response Structure:
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 2000000,
    "total_pages": 200000,
    "has_next": true,
    "has_previous": false
  },
  "stats": {
    "user_regular_count": 50000,
    "user_auto_count": 30000,
    "community_regular_count": 1200000,
    "community_auto_count": 800000
  }
}
```

### Frontend Gallery Hook Changes:
- Replace multiple `useGalleryList` and `useGalleryAutoList` calls with single `useUnifiedGalleryList`
- Pass content type filters and creator filters to the unified API
- Use server-provided pagination metadata instead of client-side calculation

## Success Criteria

- [x] Gallery displays correct total page count (based on millions of records)
- [x] All million+ records are accessible through pagination
- [x] Dashboard and gallery show identical count totals
- [ ] Page navigation is smooth with pre-loading
- [x] Content type toggles correctly update total counts and pagination
- [x] Backend tests validate pagination works with large datasets
- [x] E2E tests verify end-to-end pagination functionality

## Migration Strategy

1. [x] Implement backend changes first (unified API)
2. [x] Add comprehensive tests for new backend functionality
3. [x] Gradually migrate frontend to use new API
4. [x] Run both old and new implementations in parallel during testing
5. [x] Switch over completely once all tests pass
6. [x] Remove old client-side pagination logic

## Notes

- The current approach of client-side data combination is fundamentally flawed for large datasets
- Server-side filtering and pagination is the only scalable solution
- Dashboard stats should be the single source of truth for total counts
- Consider implementing cursor-based pagination for future scalability beyond millions of records