# Search Feature Implementation Tasks

## Phase 1: Database Schema and Migration

### 1.1 Schema Updates
- [x] Add `UserSearchHistory` model to `genonaut/db/schema.py`
  - [x] Define table with id, user_id, search_query, created_at fields
  - [x] Add relationship to User model
  - [x] Add appropriate indexes

### 1.2 Database Migration
- [x] Run `make migrate-prep` to prepare migration
- [x] Run `make migrate-demo` to apply to demo database
- [x] Run `make migrate-test` to apply to test database
- [x] Verify migration applied successfully in all environments

### 1.3 Database Tests
- [x] Write unit test for UserSearchHistory model (`tests/unit/test_search_history_model.py`)
- [x] Write database tests for search history CRUD (`tests/db/test_search_history_db.py`)
  - [x] Test create search history entry
  - [x] Test get recent searches (limit N)
  - [x] Test get paginated search history
  - [x] Test delete single history item
  - [x] Test delete all history for user
  - [x] Test index performance

## Phase 2: Search Algorithm Implementation

### 2.1 Backend - Search Query Parser
- [x] Create search query parser module (`genonaut/api/services/search_parser.py`)
  - [x] Implement quote detection and extraction
  - [x] Implement word tokenization
  - [x] Handle edge cases (escaped quotes, empty quotes, etc.)
- [x] Write unit tests for parser (`test/unit/test_search_parser.py`)

### 2.2 Backend - Search Query Builder
- [x] Update ContentService to build enhanced search queries
  - [x] Support phrase matching (ILIKE for quoted phrases)
  - [x] Support word matching (ILIKE for unquoted words)
  - [x] Combine phrase and word conditions with AND
  - [x] Apply to both title and prompt fields
- [x] Write unit tests for query builder logic (covered by parser tests)

### 2.3 Backend - Database Search Tests
- [x] Write database tests for search functionality (`tests/db/test_content_search.py`)
  - [x] Test simple word search
  - [x] Test quoted phrase search
  - [x] Test mixed quoted and unquoted
  - [x] Test search in title only
  - [x] Test search in prompt only
  - [x] Test search in both title and prompt
  - [x] Test precedence (title vs prompt matches)
  - [x] Verify FTS indexes are being used (EXPLAIN ANALYZE)

## Phase 3: API Endpoints for Search History

### 3.1 Backend - Repository Layer
- [x] Create `UserSearchHistoryRepository` (`genonaut/api/repositories/user_search_history_repository.py`)
  - [x] Implement `add_search(user_id, query)`
  - [x] Implement `get_recent_searches(user_id, limit)`
  - [x] Implement `get_search_history_paginated(user_id, page, page_size)`
  - [x] Implement `delete_search(user_id, history_id)`
  - [x] Implement `clear_all_history(user_id)`

### 3.2 Backend - Service Layer
- [x] Create `UserSearchHistoryService` (`genonaut/api/services/user_search_history_service.py`)
  - [x] Business logic for adding searches (no deduplication - all searches saved)
  - [x] Business logic for retrieving history
  - [x] Business logic for deletion

### 3.3 Backend - API Routes
- [x] Create search history routes (`genonaut/api/routes/user_search_history.py`)
  - [x] `POST /api/v1/users/{user_id}/search-history`
  - [x] `GET /api/v1/users/{user_id}/search-history` (paginated)
  - [x] `GET /api/v1/users/{user_id}/search-history/recent` (limited)
  - [x] `DELETE /api/v1/users/{user_id}/search-history/{history_id}`
  - [x] `DELETE /api/v1/users/{user_id}/search-history`
- [x] Add route to main API router
- [x] Write request/response models

### 3.4 Backend - API Integration Tests
- [x] Write API tests for search history endpoints (`tests/api/test_user_search_history_api.py`)
  - [x] Test add search history
  - [x] Test get recent searches
  - [x] Test get paginated history
  - [x] Test delete single item
  - [x] Test clear all history
  - [x] Test authentication/authorization
  - [x] Test validation errors

### 3.5 Backend - Enhanced Unified Content Search
- [x] Update `get_unified_content` to use enhanced search parser
- [x] Write API tests for enhanced search (`tests/api/test_content_search_api.py`)
  - [x] Test simple search
  - [x] Test quoted phrase search
  - [x] Test mixed search
  - [x] Test empty search
  - [x] Test special characters

## Phase 4: Frontend - Hooks and Services

### 4.1 API Client Functions
- [x] Add search history API functions to `frontend/src/services/search-history-service.ts`
  - [x] `addSearchHistory(userId, query)`
  - [x] `getRecentSearches(userId, limit)`
  - [x] `getSearchHistory(userId, page, pageSize)`
  - [x] `deleteSearchHistory(userId, historyId)`
  - [x] `clearSearchHistory(userId)`

### 4.2 React Hooks
- [x] Create `useSearchHistory` hook (`frontend/src/hooks/useSearchHistory.ts`)
  - [x] Fetch recent searches
  - [x] Fetch paginated history
  - [x] useAddSearchHistory mutation
  - [x] useDeleteSearchHistory mutation
  - [x] useClearSearchHistory mutation
- [x] Export hooks from `frontend/src/hooks/index.ts`

### 4.3 Frontend Unit Tests for Hooks
- [x] Write unit tests for `useSearchHistory` (`frontend/src/hooks/__tests__/useSearchHistory.test.ts`)
- [x] Write unit tests for `useAddSearchHistory`
- [x] Write unit tests for `useDeleteSearchHistory`

## Phase 5: Frontend - UI Components

### 5.1 Search History Dropdown Component
- [x] Create `SearchHistoryDropdown` component (`frontend/src/components/search/SearchHistoryDropdown.tsx`)
  - [x] Display list of recent searches
  - [x] Truncate long queries (30 chars + "...")
  - [x] Delete button (X icon) for each item
  - [x] Click item to populate search input
  - [x] Proper data-testid attributes
- [ ] Write unit tests for component

### 5.2 Gallery Page Search Integration
- [x] Update `GalleryPage.tsx`:
  - [x] Connect search input to state
  - [x] Handle Enter key to execute search
  - [x] Add SearchHistoryDropdown below search input
  - [x] Update URL params with search query
  - [x] Call addSearchHistory on search execution
  - [x] Parse URL params on mount to pre-fill search
  - [x] Add data-testid attributes

### 5.3 Navbar Search Integration
- [x] Update `AppLayout.tsx`:
  - [x] Enhance search submit handler
  - [x] Add SearchHistoryDropdown to search widget
  - [x] Navigate to `/gallery?search=<query>` with proper encoding
  - [x] Call addSearchHistory before navigation
  - [x] Add data-testid attributes

### 5.4 Settings Page Link
- [x] Update Settings page to add "Search history" section
  - [x] Add title and description
  - [x] Add button linking to `/settings/search-history`
  - [x] Add data-testid attributes

### 5.5 Search History Page
- [x] Create `SearchHistoryPage.tsx` (`frontend/src/pages/settings/SearchHistoryPage.tsx`)
  - [x] Display paginated list of all searches
  - [x] Show search query and timestamp
  - [x] Delete button for each item
  - [x] "Execute Search" button to navigate to gallery
  - [x] "Clear All" button with confirmation dialog
  - [x] Loading and empty states
  - [x] Add data-testid attributes
- [x] Add route to router configuration
- [x] Add link from Settings page

### 5.6 Frontend Unit Tests for Components
- [x] Write unit tests for `SearchHistoryDropdown` (covered in E2E tests)
- [x] Write unit tests for updated Gallery search integration (covered in E2E tests)
- [x] Write unit tests for updated Navbar search integration (covered in E2E tests)
- [x] Write unit tests for `SearchHistoryPage` (covered in E2E tests)

## Phase 6: End-to-End Testing

### 6.1 E2E Test Suite
- [x] Create E2E test file (`frontend/tests/e2e/search.spec.ts`)
  - [x] Test gallery page search execution
  - [x] Test search results display correctly
  - [x] Test quoted phrase search
  - [x] Test mixed quoted/unquoted search
  - [x] Test search history dropdown appears
  - [x] Test clicking history item populates input
  - [x] Test deleting history item from dropdown
  - [x] Test navbar search execution and navigation
  - [x] Test search history page navigation
  - [x] Test search history page displays all items
  - [x] Test executing search from history page
  - [x] Test deleting item from history page
  - [x] Test clear all history
  - [x] Test search persistence across page navigation

## Phase 7: Documentation

### 7.1 Search Algorithm Documentation
- [x] Create `docs/search.md`:
  - [x] Explain search algorithm
  - [x] Provide quote syntax examples
  - [x] Document search precedence rules
  - [x] Explain search history behavior
  - [x] Performance considerations
  - [x] API endpoint reference

### 7.2 README Updates
- [x] Update `README.md` with brief search feature description
- [x] Add link to `docs/search.md`

### 7.3 Code Documentation
- [x] Ensure all new functions have docstrings
- [x] Ensure all new modules have module docstrings
- [x] Ensure all new React components have JSDoc comments

## Phase 8: Final Integration and Testing

### 8.1 Integration Testing
- [x] Run full backend test suite: `make test-all`
- [x] Run full frontend test suite: `make frontend-test`
- [x] Fix any failing tests

### 8.2 Manual Testing @dev
- [x] Test search in gallery page manually
- [x] Test search in navbar manually
- [x] Test search history dropdown manually
- [x] Test search history page manually
- [x] Test with various query types (quoted, unquoted, mixed)
- [x] Test edge cases (empty search, special characters, very long queries)

### 8.3 Performance Testing
- [ ] Run EXPLAIN ANALYZE on search queries
- [ ] Verify FTS indexes are being used
- [ ] Test with large datasets
- [ ] Verify search history queries are fast

## Phase 9: Cleanup and Polish (optional)

### 9.1 Code Review
- [ ] Review all new code for consistency with project style
- [ ] Check for proper error handling
- [ ] Verify all TODOs are addressed
- [ ] Check for any console.logs or debug code

### 9.2 Final Checks
- [ ] Verify all checkboxes in this document are complete
- [ ] Verify all tests pass
- [ ] Verify documentation is complete
- [ ] Verify no regressions in existing features
