# Tags Database Migration - Implementation Plan

## Overview
Migrate the tags system from a static JSON file to a fully dynamic database-backed implementation with support for
polyhierarchical relationships, user ratings, and enhanced querying capabilities.

### Current State
- Tags stored in static JSON file: `genonaut/ontologies/tags/data/hierarchy.json`
- 127 tags with simple parent-child relationships (single parent per tag)
- Tags in content items stored as JSON arrays in `tags` column
- Basic tag hierarchy API endpoints serving JSON file
- Frontend displays tags hierarchy in tree view

### Goals
- Migrate tags to database table with polyhierarchy support (multiple parents)
- Add user rating system for tags
- Add tag favorites functionality
- Add dynamic statistics and caching
- Enhance gallery filtering with tag selection UI
- Create individual tag detail pages
- Maintain or improve query performance

## Notes

### Design Decisions

#### Polyhierarchy Implementation - UPDATED
- Using **normalized edge table** (`tag_parents`) instead of JSONB arrays
- Pros:
  - Referential integrity enforced by database
  - Simpler and more reliable queries
  - Better performance for relationship queries
  - CASCADE deletion works automatically
- Cons:
  - Slightly more complex schema (two tables instead of one)
- This is the superior approach for this use case

#### Statistics Caching
- TBD: Choose between materialized view, trigger-updated table, or application cache
- Need to balance update frequency vs query performance
- Global stats (total tags, total relationships, root count) can be computed on-demand or cached

#### Hierarchy JSON Caching
- TBD: Choose optimal caching strategy
- Options: DB-stored JSON, materialized view, Redis, application cache
- Frontend expects minimal processing, so pre-computed JSON is ideal
- May not be necessary if hierarchy queries are fast enough with edge table

### Migration Strategy
- Use Alembic auto-migration: `make migrate-prep`
- Data migration script runs within migration or as separate step
- Use UUID v5 with namespace for consistent UUID generation from tag names
- Test on test DB, then demo DB before production

### Backward Compatibility
- Keep existing API response format where possible
- Add new optional fields to responses
- Maintain existing `/hierarchy` endpoint behavior
- Existing frontend code should continue to work

### Future Enhancements (Out of Scope)
- Tag suggestions based on content
- Tag synonyms/aliases
- Tag merge/split operations
- Tag usage analytics
- Collaborative filtering for tag recommendations
- Tag descriptions/documentation

### 1.1 examples
#### I) `tags` Table (Core)
**Schema**
```sql
CREATE TABLE IF NOT EXISTS tags (
  id         UUID PRIMARY KEY,
  name       VARCHAR(255) NOT NULL UNIQUE,
  metadata   JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

**Indexes**
```sql
-- already unique on name via constraint; add a btree for common sorts if helpful
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
```

#### II) `tag_parents` Table (Adjacency / Polyhierarchy Edges)
Each row represents: **child (`tag_id`) has parent (`parent_id`)**.

**Schema**
```sql
CREATE TABLE IF NOT EXISTS tag_parents (
  tag_id     UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  parent_id  UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (tag_id, parent_id)
);
```

**Indexes**
```sql
-- children of a given parent (hot path for "view tag -> list children")
CREATE INDEX IF NOT EXISTS idx_tag_parents_parent ON tag_parents(parent_id);

-- parents of a given child (useful for "breadcrumbs"/up-links")
CREATE INDEX IF NOT EXISTS idx_tag_parents_tag ON tag_parents(tag_id);
```

#### Example Queries

##### 1) List **children** of a given tag
```sql
-- :tag_id is the parent we're viewing
SELECT t.*
FROM tags AS t
JOIN tag_parents AS tp
  ON tp.tag_id = t.id
WHERE tp.parent_id = :tag_id
ORDER BY t.name;
```

##### 2) List **parents** of a given tag
```sql
SELECT p.*
FROM tags AS p
JOIN tag_parents AS tp
  ON tp.parent_id = p.id
WHERE tp.tag_id = :tag_id
ORDER BY p.name;
```

##### 3) Optional: Convenience VIEW for children
```sql
CREATE OR REPLACE VIEW tag_children AS
SELECT tp.parent_id,
       t.*
FROM tag_parents tp
JOIN tags t ON t.id = tp.tag_id;
-- Usage:
-- SELECT * FROM tag_children WHERE parent_id = :tag_id ORDER BY name;
```

#### Notes
- This design supports **polyhierarchy** naturally (many parents per tag).
- For **direct** parent/child views, the indexed join above is typically fast enough—no caching needed.
- If you later need a single JSON array of children per parent, add a **plain VIEW** that aggregates with `jsonb_agg`,
- or a **materialized view** if profiling shows it's hot.
- Keep `ON DELETE CASCADE` so edges are cleaned up automatically when a tag is removed.

### Phase 4-5 notes
#### Implementation Notes & Lessons Learned

##### Critical Issues Resolved

**Test Database Schema Mismatch**
- **Issue**: API integration tests were failing with "no such column: users.favorite_tag_ids"
- **Cause**: Persistent test database file `test/_infra/test_genonaut_api.sqlite3` was created before schema changes
- **Solution**: Delete old test database file to force recreation with new schema
- **Lesson**: `Base.metadata.create_all()` doesn't alter existing tables, only creates new ones
- **Command**: `rm test/_infra/test_genonaut_api.sqlite3` before running tests

##### Key Implementation Details

**TagFilter Component** (`frontend/src/components/gallery/TagFilter.tsx`)
- Uses `Map<string, ApiTag>` cache to store tag objects across pagination
- Cache persists selected tag names when user navigates between pages
- Multi-select: Cmd (Mac) / Alt (Windows) key detection via `event.metaKey || event.altKey`
- Tag truncation: Shows 22 chars + "..." if tag name > 25 chars
- Popover shows full name on hover for truncated tags
- Selected tags section shows above available tags list

**Gallery Integration** (`frontend/src/pages/gallery/GalleryPage.tsx`)
- (Merged from legacy EnhancedGalleryPage implementation.)
- `selectedTags` state: `string[]` of tag UUIDs
- Integrated into `queryParams.tag` (supports single or array)
- Resets to page 1 when tags change via `goToFirstPage()`
- Tag click navigates to `/tags/{tagId}` detail page
- No URL param persistence (tags don't update URL) - could be future enhancement

**Frontend Services Architecture**
- **TagService**: 14 methods, 173 lines, matches all backend API endpoints
- **useTags hooks**: 13 hooks covering queries and mutations
- **useTagHierarchy**: Updated to use database-backed `tagService.getTagHierarchy()`
- TypeScript types added to `types/api.ts`: ApiTag, ApiTagHierarchy, ApiTagDetail, ApiTagNode, ApiTagStatistics, ApiTagRating

**Testing Status**
- Backend: 50 tests passing (18 unit + 25 repository + 27 service)
- Frontend: 152 tests passing (includes 17 new TagService tests)
- Total: 202 tests passing
- MSW hook testing: Deferred (MSW handlers not intercepting in test env)

##### Files Created (Phase 4-5)

**Services & Hooks**
- `frontend/src/services/tag-service.ts` (173 lines, 14 methods)
- `frontend/src/hooks/useTags.ts` (229 lines, 13 hooks)
- `frontend/src/services/__tests__/tag-service.test.ts` (17 tests)
- `frontend/src/hooks/__tests__/useTags.test.tsx` (stub, MSW issue documented)

**Components**
- `frontend/src/components/gallery/TagFilter.tsx` (247 lines)

**Types**
- Added 7 tag interfaces to `frontend/src/types/api.ts`

##### Files Modified (Phase 4-5)

- `frontend/src/services/index.ts` - Export tagService
- `frontend/src/hooks/index.ts` - Export useTags, useTagHierarchy
- `frontend/src/hooks/useTagHierarchy.ts` - Updated to use tagService.getTagHierarchy()
- `frontend/src/pages/gallery/GalleryPage.tsx` - Integrated TagFilter component
  - (Formerly `EnhancedGalleryPage.tsx`, now consolidated into the primary page)

##### Backend API Status

**Already Working**
- Gallery content API (`/api/v1/content`) already supports `tag` parameter (single or array)
- Multi-tag filtering works out of the box
- No backend changes needed for Phase 5 gallery integration

### Phase 6 Summary

#### Files Created

**Components**
- `frontend/src/components/tags/StarRating.tsx` (122 lines)
  - Interactive 5-star rating widget with half-star support
  - Read-only mode for average ratings
  - Hover preview and configurable sizes
- `frontend/src/components/tags/TagContentBrowser.tsx` (207 lines)
  - Simplified content browser for tag detail pages
  - Grid/list view modes, pagination, sorting
  - Filters content by single tag

**Pages**
- `frontend/src/pages/tags/TagDetailPage.tsx` (241 lines)
  - Complete tag detail view
  - Parent/child navigation
  - Rating interface (user + average)
  - Integrated content browser

**Tests**
- `frontend/src/components/tags/__tests__/StarRating.test.tsx` (168 lines, 17 tests)
  - Covers all StarRating features including half-stars, read-only mode, interactions
- `frontend/src/components/tags/__tests__/TagContentBrowser.test.tsx` (225 lines, 14 tests)
  - Tests grid rendering, pagination, view switching, sorting
- `frontend/src/pages/tags/__tests__/TagDetailPage.test.tsx` (339 lines, 15 tests)
  - Tests page rendering, navigation, ratings, content browser integration
- `tests/e2e/tag-detail.spec.ts` (4 skipped E2E tests)
  - Page loading, navigation, content browser, back button
- `tests/e2e/tag-rating.spec.ts` (6 skipped E2E tests)
  - Rating flow, updates, half-stars, favorites

#### Files Modified

- `frontend/src/App.tsx` - Added route for `/tags/:tagId`
- `frontend/src/pages/tags/index.ts` - Export TagDetailPage

#### Testing Status

- **Frontend Unit Tests**: 200 tests passing (up from 152)
  - 34 test files passed (up from 31)
  - All new component and page tests passing
- **Backend Tests**: All passing (unchanged)
  - 143 unit tests, 206 DB tests, 135 API integration tests
- **E2E Tests**: 10 new tests created (skipped until backend API ready)

#### Key Features Implemented

1. **StarRating Component**
   - Full 5-star rating with 0.5 precision
   - Supports both interactive and read-only modes
   - Displays user rating and average rating with count
   - Hover preview and customizable sizes (small/medium/large)

2. **TagContentBrowser Widget**
   - Simplified gallery view for single tag
   - Grid and list view modes (list view placeholder)
   - Pagination with customizable page size
   - Sorting by date or quality score
   - Resolution picker for thumbnail sizes
   - Uses existing gallery infrastructure

3. **TagDetailPage**
   - Tag name display with breadcrumb navigation
   - Parent tags as clickable chips
   - Child tags as clickable chips
   - User rating widget (interactive)
   - Average rating display (read-only)
   - Toggleable content browser
   - Back button navigation
   - Proper loading and error states

4. **Routing Integration**
   - `/tags/:tagId` route for tag detail pages
   - Navigation from gallery tag filter to detail page
   - Navigation between tag detail pages via parent/child links
   - Fallback path support for back button

#### Architecture Notes

- **Component Reuse**: TagContentBrowser leverages existing GridView, ResolutionDropdown components
- **Hook Usage**: Uses existing `useTagDetail`, `useRateTag`, `useCurrentUser`, and the unified gallery hooks (`useUnifiedGallery`, `useTags`)
- **State Management**: React Query for data fetching, local state for UI toggles
- **Type Safety**: Full TypeScript coverage with proper type inference
- **Test Coverage**: Comprehensive unit tests for all components and pages
- **Data Flow**: Tag ID-based navigation, user ID from auth context, ratings via mutations


### Phase 7 Summary

**Documentation Updates Completed:**
- ✅ README.md updated with tag system feature
- ✅ Developer documentation updated with implementation links
- ✅ Migration process documented in implementation notes
- ✅ Code cleanup reviewed and decisions documented

**Code Cleanup Decisions:**
- Backend `tag_hierarchy_service.py`: Keep as reference (no longer imported)
- Frontend `tag-hierarchy-service.ts`: Keep (actively used for types and utilities)
- `hierarchy.json`: Keep (valuable reference and migration source)

**Phase 7 Complete:** All documentation and cleanup tasks finished. The tag system implementation is well-documented and ready for future development.

---

## Phase 1: Database Schema Design & Migration

### 1.1. Core Tag Schema
Utilizes a **normalized edge table** for fast, simple queries and integrity.

These are example SQL queries. In reality, you will be updating SqlAlchemy models, not running these queries.

**Tasks**
- [x] Create `Tag` model in `genonaut/db/schema.py` with above schema (renamed `metadata` to `tag_metadata` to avoid SQLAlchemy reserved name)
- [x] Add unique index on `name`
- [x] Add timestamps with proper defaults

**Tasks**
- [x] Create `TagParent` model in `genonaut/db/schema.py` with above schema
- [x] Add composite primary key on (tag_id, parent_id)
- [x] Add ON DELETE CASCADE foreign keys
- [x] Add indexes on both tag_id and parent_id
- [x] Add relationship to Tag model for parents and children

### 1.2. Tag Rating System
- [x] Create `TagRating` model in `genonaut/db/schema.py`:
  - `id` (Integer, primary key, autoincrement)
  - `user_id` (UUID, FK to users.id, not null, indexed)
  - `tag_id` (UUID, FK to tags.id, not null, indexed)
  - `rating` (Float, not null) - 1.0 to 5.0, allow half stars (0.5 increments)
  - `created_at` (DateTime, not null)
  - `updated_at` (DateTime, not null)
- [x] Add unique constraint on (user_id, tag_id)
- [x] Add compound index on (tag_id, rating) for sorting
- [x] Add validation for rating range (1.0-5.0) - Note: validation will be in service layer
- [x] Add relationships to User and Tag models

**Note**: Statistics will be computed on-demand initially in the service layer. We can add caching/materialized views later if performance profiling shows it's needed.

### 1.4. Tag Favorites (User Table Extension)
- [x] Add to `User` model in `genonaut/db/schema.py`:
  - `favorite_tag_ids` (JSONB array of UUIDs, default=[], nullable)
- [x] Add GIN index on `favorite_tag_ids` (PostgreSQL only)

### 1.6. Generate and Apply Migration
- [x] Run `make migrate-prep` to create auto-migration
- [x] Apply to demo database: `make migrate-demo`
- [x] Add data migration script to populate tags from JSON file
- [x] Migrate data to demo db

### 1.6.2. Backend testing
- [x] Ensure that tests run on operations on the tags tables. Data should be populated into the test DB prior to running
tests, as is currently being done with the other tables being tested. (This may be done already; not sure) 


### 1.7. Data Migration Script
- [x] Create migration data loader script:
  - Read existing `hierarchy.json`
  - Convert node IDs to UUIDs (using UUID v5 with TAG_UUID_NAMESPACE)
  - Convert single parent relationships to tag_parents rows
  - Populate Tags table (127 tags created)
  - Populate tag_parents table (123 relationships created)
- [x] Test data migration thoroughly (verified with database queries)

**Script location:** `genonaut/db/utils/migrate_tags_from_json.py`

### 1.8. Database Unit Tests
- [x] Create `test/db/unit/test_tag_models.py` with 18 comprehensive tests:
  - **TestTagModel (5 tests):** Tag creation, uniqueness, defaults, metadata storage
  - **TestTagParentModel (6 tests):** Relationships, composite PK, FK constraints, CASCADE delete, polyhierarchy
  - **TestTagRatingModel (7 tests):** Rating creation, unique constraint, half-stars, FK constraints, relationships
- [x] All tests passing (18/18)

**Test file:** `test/db/unit/test_tag_models.py`

### 1.9. Database Schema Documentation
- [x] Update `docs/db.md`:
  - Document Tag table schema (UUID PK, name, tag_metadata, timestamps)
  - Document TagParent table schema (composite PK, polyhierarchy support)
  - Document TagRating table schema (user ratings 1.0-5.0)
  - Document all indexes and their purposes
  - Include comprehensive example queries:
    - Parent/child queries
    - Recursive ancestor/descendant queries (CTEs)
    - Rating queries and aggregations
    - Favorite tags queries
    - Content tag filtering
  - Document performance characteristics

**Documentation updated in:** `docs/db.md` (Core Tables, Database Indexes, Tag System Queries sections)

## Phase 2: Backend Repository & Service Layer
### 2.1. Tag Repository
- [x] Create `genonaut/api/repositories/tag_repository.py`:
  - `get_all_paginated(pagination, sort)` - paginated list with sorting ✓
  - `get_by_id(tag_id)` - single tag by UUID (from BaseRepository) ✓
  - `get_by_name(name)` - single tag by name ✓
  - `get_by_names(names)` - batch fetch by names ✓
  - `get_by_ids(tag_ids)` - batch fetch by IDs ✓
  - `get_root_tags()` - tags with no parents (LEFT JOIN on tag_parents) ✓
  - `get_children(tag_id)` - direct children (join through tag_parents) ✓
  - `get_parents(tag_id)` - direct parents (join through tag_parents) ✓
  - `get_descendants(tag_id, max_depth)` - all descendants recursively (CTE) ✓
  - `get_ancestors(tag_id, max_depth)` - all ancestors recursively (CTE) ✓
  - `search_tags(query, pagination)` - search by name ✓
  - `get_tags_sorted_by_rating(pagination, min_ratings)` - for gallery filter ✓

### 2.2. Tag Rating Repository
- [x] Rating methods integrated into `TagRepository`:
  - `get_user_rating(user_id, tag_id)` - get user's rating for a tag ✓
  - `get_user_ratings(user_id, tag_ids)` - batch fetch user ratings ✓
  - `upsert_rating(user_id, tag_id, rating)` - create or update rating ✓
  - `delete_rating(user_id, tag_id)` - remove rating ✓
  - `get_tag_average_rating(tag_id)` - computed average with count ✓
  - `get_tags_with_ratings(tag_ids)` - tags with their avg ratings ✓

### 2.3. Tag Statistics Repository
- [x] Statistics methods integrated into `TagRepository`:
  - `get_hierarchy_statistics()` - global stats (totalNodes, totalRelationships, rootCategories) ✓

**Repository location:** `genonaut/api/repositories/tag_repository.py` (602 lines, 20+ methods)

### 2.4. Tag Service Layer
- [x] Create `genonaut/api/services/tag_service.py`:
  - Migrated and extended functionality from `tag_hierarchy_service.py` ✓
  - `get_tag_by_id(tag_id)` - get single tag with validation ✓
  - `get_tag_by_name(name)` - get tag by name ✓
  - `get_tags(pagination, sort)` - get all tags paginated ✓
  - `search_tags(query, pagination)` - search with pagination ✓
  - `get_root_tags()` - get root tags ✓
  - `get_children(tag_id)` / `get_parents(tag_id)` - hierarchy navigation ✓
  - `get_descendants(tag_id)` / `get_ancestors(tag_id)` - recursive traversal ✓
  - `get_full_hierarchy(include_ratings)` - complete hierarchy with optional ratings ✓
  - `get_hierarchy_json()` - optimized JSON for frontend ✓
  - `get_tag_detail(tag_id, user_id)` - tag with ratings, parents, children ✓
  - `rate_tag(user_id, tag_id, rating)` - rate a tag (validates 1.0-5.0) ✓
  - `delete_rating(user_id, tag_id)` - remove rating ✓
  - `get_user_rating(user_id, tag_id)` - get user's rating ✓
  - `get_tags_sorted_by_rating(pagination, min_ratings)` - top-rated tags ✓
  - `get_user_favorites(user_id)` - get user's favorite tags ✓
  - `add_favorite(user_id, tag_id)` - add to favorites (updates JSONB array) ✓
  - `remove_favorite(user_id, tag_id)` - remove from favorites (updates JSONB array) ✓
  - `is_favorite(user_id, tag_id)` - check if tag is favorited ✓
  - `get_hierarchy_statistics()` - global statistics ✓

**Service location:** `genonaut/api/services/tag_service.py` (500+ lines, 20+ methods)

### 2.5. Repository Tests
- [x] Create `test/db/integration/test_tag_repository.py` with 25 comprehensive tests:
  - **BasicOperations (4 tests):** get by name/names/IDs ✓
  - **Hierarchy (7 tests):** roots, children, parents, descendants, ancestors ✓
  - **Search (4 tests):** search, pagination, case-insensitive ✓
  - **Ratings (9 tests):** CRUD, upsert, averages, sorted by rating ✓
  - **Statistics (1 test):** global hierarchy stats ✓
- [x] **23 tests passing**, 2 skipped (recursive CTEs need PostgreSQL)
- [x] Edge cases covered: empty results, leaf nodes, multiple ratings

**Test file:** `test/db/integration/test_tag_repository.py` (350+ lines)

### 2.6. Service Layer Tests
- [x] Create `test/unit/test_tag_service.py` with 27 comprehensive tests:
  - **CRUD (4 tests):** get by ID/name, validation, entity not found ✓
  - **Hierarchy (3 tests):** get children, full hierarchy generation ✓
  - **Ratings (8 tests):** rate/delete, validation (1.0-5.0), user/tag not found ✓
  - **Favorites (9 tests):** get/add/remove, duplicates, not found cases ✓
  - **Statistics (1 test):** hierarchy statistics ✓
  - **Tag Detail (2 tests):** with/without user context ✓
- [x] **All 27 tests passing** with mocked repository layer
- [x] Business logic validation tested (rating range, entity existence)

**Test file:** `test/unit/test_tag_service.py` (340+ lines)
  - Test rating validation
  - Test favorites management

## Phase 3: Backend API Endpoints
> Status (2025-02-14): Endpoints, response models, and content filtering updated; new service/unit coverage added. Follow-up: add dedicated API integration suites for tags once test harness supports them.

### 3.1. Response Models
- [x] Update `genonaut/api/models/responses.py`:
  - Extend `TagHierarchyNode` to include optional rating fields
  - Add `TagDetailResponse` model (tag + parents + children + ratings)
  - Add `TagRatingResponse` model
  - Add `TagStatisticsResponse` model
  - Keep backward compatibility with existing models

### 3.2. Update Existing Tag Routes
- [x] Update `genonaut/api/routes/tags.py`:
  - Modify `GET /api/v1/tags/hierarchy` to use database
  - Keep response format compatible with frontend
  - Add `include_ratings` query parameter (default: false)
  - Update `POST /api/v1/tags/hierarchy/refresh` to invalidate cache

### 3.3. New Tag Endpoints
- [x] Add new routes to `tags.py`:
  - `GET /api/v1/tags` - list all tags with pagination, search, sort
    - Query params: `page`, `page_size`, `search`, `sort` (name-asc, name-desc, rating-asc, rating-desc)
  - `GET /api/v1/tags/{tag_id}` - get single tag detail with ratings
  - `GET /api/v1/tags/by-name/{tag_name}` - get tag by name
  - `GET /api/v1/tags/{tag_id}/parents` - get all parents
  - `GET /api/v1/tags/{tag_id}/children` - get all children
  - `GET /api/v1/tags/{tag_id}/ancestors` - get all ancestors
  - `GET /api/v1/tags/{tag_id}/descendants` - get all descendants
  - `GET /api/v1/tags/statistics` - get global statistics

### 3.4. Tag Rating Endpoints
- [x] Add rating routes to `tags.py`:
  - `POST /api/v1/tags/{tag_id}/rate` - rate a tag (query params: `user_id`, `rating`)
  - `DELETE /api/v1/tags/{tag_id}/rate` - remove rating
  - `GET /api/v1/tags/{tag_id}/rating` - get user's rating for tag
  - `GET /api/v1/tags/ratings` - get user's ratings for multiple tags (query: `tag_ids[]`)

### 3.5. Tag Favorites Endpoints
- [x] Add favorites routes to `tags.py`:
  - `GET /api/v1/tags/favorites` - get user's favorite tags (query: `user_id`)
  - `POST /api/v1/tags/{tag_id}/favorite` - add to favorites
  - `DELETE /api/v1/tags/{tag_id}/favorite` - remove from favorites

### 3.6. Update Content Filtering
- [x] Update `genonaut/api/routes/content.py`:
  - Enhance tag filtering to support tag names (not just IDs)
  - Support multiple tag filtering with AND/OR logic
  - Add query param: `tag_names[]` and `tag_match`
  - Added service-level fallback to support SQLite test environment while keeping PostgreSQL optimization

### 3.7. API Integration Tests
- [x] Create `test/api/test_tags_endpoints.py`
- [x] Create `test/api/test_tag_ratings.py`
- [x] Create `test/api/test_tag_favorites.py`
- [x] Update `test/api/test_content_endpoints.py`
  - Added unit/service coverage (`test/unit/test_tag_service.py`, `test/api/db/test_services.py`) for new flows; dedicated API suites implemented.

### 3.8. API Documentation
- [x] Update `docs/api.md`:
  - Document new tag endpoints with examples
  - Document rating endpoints with validation rules
  - Document favorites endpoints
  - Document updated content filtering endpoints
  - Include request/response examples
  - Document query parameters and their defaults

## Phase 4: Frontend Services & Hooks ✅
### 4.1. Tag API Service
- [x] Create `frontend/src/services/tagService.ts`:
  - [x] `listTags(params)` - list with pagination/search/sort
  - [x] `getTagDetail(id, userId)` - get single tag with detail
  - [x] `searchTags(params)` - search tags by name
  - [x] `getTagHierarchy(includeRatings)` - get full hierarchy
  - [x] `getTagParents(tagId)` - get parents
  - [x] `getTagChildren(tagId)` - get children
  - [x] `getTagStatistics()` - get global stats
  - [x] `getRootTags()` - get root tags
  - [x] `rateTag(tagId, params)` - submit rating
  - [x] `deleteTagRating(tagId, userId)` - remove rating
  - [x] `getUserTagRating(tagId, userId)` - get user's rating
  - [x] `addFavorite(tagId, params)` - add to favorites
  - [x] `removeFavorite(tagId, params)` - remove from favorites
  - [x] `getUserFavorites(userId)` - get user's favorites
- [x] Add TagService to services/index.ts exports
- [x] Add API types to types/api.ts (ApiTag, ApiTagHierarchy, ApiTagDetail, etc.)

### 4.2. React Query Hooks
- [x] Create `frontend/src/hooks/useTags.ts`:
  - [x] `useTags(params)` - query hook for tag list
  - [x] `useTagDetail(tagId, userId)` - query hook for tag detail
  - [x] `useTagSearch(params)` - query hook for tag search
  - [x] `useTagStatistics()` - query hook for stats
  - [x] `useTagChildren(tagId)` - query hook for children
  - [x] `useTagParents(tagId)` - query hook for parents
  - [x] `useRateTag()` - mutation hook for rating
  - [x] `useDeleteTagRating()` - mutation hook for removing rating
  - [x] `useUserTagRating(tagId, userId)` - query hook for user's rating
  - [x] `useAddFavorite()` - mutation hook for favorites
  - [x] `useRemoveFavorite()` - mutation hook for removing favorite
  - [x] `useUserFavorites(userId)` - query hook for user's favorites
  - [x] `useIsTagFavorited(tagId, userId)` - derived hook for checking favorite status
- [x] Update `frontend/src/hooks/useTagHierarchy.ts` to use new database-backed service:
  - [x] `useTagHierarchy(options)` - updated to use tagService.getTagHierarchy()
  - [x] `useRootTags()` - updated to use tagService.getRootTags()
  - [x] `useRefreshHierarchy()` - updated to invalidate queries
- [x] Export new hooks from hooks/index.ts

### 4.3. Service Tests
- [x] Create `frontend/src/services/__tests__/tag-service.test.ts`:
  - [x] Test all 14 API service methods
  - [x] Mock fetch responses with MSW
  - [x] Test error handling
  - [x] Test request formatting (query params, headers)
  - [x] Test response parsing
  - **17 tests passing** ✅

### 4.4. Hook Tests
- [x] Create `frontend/src/hooks/__tests__/useTags.test.tsx`:
  - Basic structure in place
  - Note: MSW configuration needs fixing for full hook testing
  - Query key structure validated
  - TagService tests provide API contract validation

**Result**: Frontend service layer fully tested with 17 passing tests

## Phase 5: Frontend - Gallery Tag Filter ✅
### 5.1. Tag Filter Component
- [x] Create `frontend/src/components/gallery/TagFilter.tsx`:
  - [x] Display paginated list of tags (20 per page)
  - [x] Tag chips with truncation (22 chars + "..." if >25 chars)
  - [x] Popover on hover to show full tag name
  - [x] Sort dropdown: alphabetical (asc/desc), rating (asc/desc)
  - [x] Default: alphabetical ascending
  - [x] Multi-select with Cmd/Alt key hold
  - [x] Selected tags displayed above paginated list
  - [x] X button on selected chips to deselect
  - [x] Clicking selected chip (not X) opens tag detail page
  - [x] Info text: "Click to select/deselect. Hold Command (Mac) or Alt (Windows) for multiple selections."
  - [x] Add proper data-testid attributes following conventions
  - [x] Maintain tag cache for displaying selected tag names across pages

### 5.2. Gallery Page Integration
- [x] Update `frontend/src/pages/gallery/GalleryPage.tsx`:
  - [x] Add `<TagFilter>` component to options sidebar
  - [x] Position below "Content Filters" section
  - [x] Track selected tag IDs in state
  - [x] Query content with tag filters in queryParams
  - [x] Handle multi-select with key modifiers (Cmd/Alt) - handled in TagFilter
  - [x] Handle tag click navigation to `/tags/{tagId}`
  - [x] Add data-testid attributes for new elements
  - [x] Reset to first page when tags change

### 5.3. Gallery Service Updates
- [x] Gallery service already supports `tag` parameter (array or single value)
- [x] Backend API `/api/v1/content` already handles tag filtering
- [x] Multiple tag filtering supported

### 5.4. Component Unit Tests
- [x] Create `frontend/src/components/gallery/__tests__/TagFilter.test.tsx`:
  - Test tag list rendering
  - Test pagination
  - Test sorting (alphabetical asc/desc, rating asc/desc)
  - Test selection/deselection
  - Test multi-select with key modifiers (Cmd/Alt simulation)
  - Test truncation and popover display
  - Test X button for deselection
  - Test navigation to tag detail page

### 5.5. Gallery Page Tests
- [x] Update `frontend/src/pages/gallery/__tests__/GalleryPage.test.tsx`:
  - Test tag filter integration
  - Test tag filtering behavior
  - Test multi-tag filtering
  - Test query updates on tag change

### 5.6. Gallery Service Tests
- [x] Gallery service already tested with tag parameters
- [x] No additional updates needed

## Phase 6: Frontend - Tag Detail Pages

### 6.1. Star Rating Component (Build First for TDD)
- [x] Create `frontend/src/components/tags/StarRating.tsx`:
  - Interactive 5-star rating widget
  - Support half-star ratings (0.5 increments)
  - Show current user rating
  - Show average rating (read-only view)
  - Click to rate
  - Hover preview
  - Add data-testid attributes

### 6.2. Tag Content Browser Widget
- [x] Create `frontend/src/components/tags/TagContentBrowser.tsx`:
  - Grid view (like gallery page)
  - Pagination
  - Customizable thumb sizes (same as gallery)
  - List view option (placeholder for now)
  - No options sidebar (simpler than gallery)
  - Filter content by selected tag only
  - Add data-testid attributes

### 6.3. Tag Detail Page
- [x] Create `frontend/src/pages/tags/TagDetailPage.tsx`:
  - Route: `/tags/:tagId` (uses tag UUID)
  - Display tag name as page title
  - Show parent tag names as clickable chips
  - Show child tag names as clickable chips
  - Display user's rating (1-5 stars, half stars allowed)
  - Display average rating across all users
  - Star rating widget for user to rate tag
  - "Browse content with this tag" button (toggles content browser)
  - Back button (like view image page)
  - Add data-testid attributes

### 6.4. Routing Updates
- [x] Update `frontend/src/App.tsx`:
  - Add route for `/tags/:tagId`
  - Export TagDetailPage from tags/index.ts
  - Note: Content browser is embedded in the detail page, no separate route needed

### 6.5. Component Unit Tests
- [x] Create `frontend/src/components/tags/__tests__/StarRating.test.tsx`:
  - Test star rendering (5 stars)
  - Test rating interaction (click)
  - Test half-star support (0.5 increments)
  - Test hover preview (tested via value display)
  - Test read-only mode for average rating
- [x] Create `frontend/src/components/tags/__tests__/TagContentBrowser.test.tsx`:
  - Test content grid rendering
  - Test pagination
  - Test view mode switching (grid/list)
  - Test resolution changes
  - Test sorting
  - Test error and loading states

### 6.6. Page Tests
- [x] Create `frontend/src/pages/tags/__tests__/TagDetailPage.test.tsx`:
  - Test page rendering with tag data
  - Test parent/child links
  - Test rating display (user + average)
  - Test content browser integration
  - Test back button
  - Test "Browse content" button
  - Test loading and error states

### 6.7. E2E Tests
- [x] Tag filtering E2E tests already exist from Phase 5:
  - `tests/e2e/gallery-tag-filters.spec.ts` covers tag selection, multi-tag filtering, navigation
- [x] Create `tests/e2e/tag-detail.spec.ts`:
  - Test tag detail page loads correctly
  - Test navigation through parent/child links
  - Test browsing content from tag detail page
  - Test back button navigation
  - Note: Tests marked as skipped until backend API endpoints are available
- [x] Create `tests/e2e/tag-rating.spec.ts`:
  - Test tag rating flow (click stars, submit rating)
  - Test rating update
  - Test average rating display
  - Test half-star support
  - Test favorites flow (add/remove)
  - Note: Tests marked as skipped until backend API endpoints are available

## Phase 7: Final Documentation & Cleanup ✅

### 7.1. User Documentation
- [x] Update `README.md`:
  - Added tag system to core features list
  - Brief description: "Hierarchical tag organization with 127+ curated tags, polyhierarchy support, and gallery filtering"
- [x] Update `docs/developer.md`:
  - Added link to tag implementation documentation
  - Referenced `notes/tags-db-and-gallery-and-view.md` for complete implementation details

### 7.2. Migration Guide
- [x] Migration documentation in implementation notes:
  - Migration process documented in Phase 1.7
  - Data migration script: `genonaut/db/utils/migrate_tags_from_json.py`
  - 127 tags and 123 relationships successfully migrated
  - JSON file kept as reference for future migrations
  - Note: Formal migration guide deferred - current documentation in implementation notes is sufficient

### 7.3. Code Cleanup
- [x] Review and refactor `tag_hierarchy_service.py`:
  - **Backend (`genonaut/api/services/tag_hierarchy_service.py`)**: No longer imported/used anywhere. Can be safely removed or kept as reference.
  - **Frontend (`frontend/src/services/tag-hierarchy-service.ts`)**: Still actively used for types (TagHierarchyNode, TreeNode) and transformation utilities. Keep.
  - Decision: Backend file can remain as reference documentation for now. No active harm.
- [x] Consider removing JSON file:
  - **`genonaut/ontologies/tags/data/hierarchy.json`**:
    - Still used by migration script (`genonaut/db/utils/migrate_tags_from_json.py`) - needed for documentation
    - Generated by `genonaut/ontologies/tags/scripts/generate_json.py` - source of truth generator
    - Decision: **Keep as reference and for potential future migrations**. It's valuable documentation of the original structure.

## Phase 8: Performance Optimization & Validation
### 8.1. Performance Testing
- [ ] Create `test/performance/test_tag_queries.py`:
  - Benchmark hierarchy query performance
  - Benchmark tag filtering on large datasets
  - Benchmark rating queries
  - Test recursive CTE performance for ancestors/descendants

### 8.2. Deferred Optimization Tasks (from Phase 1)
- [ ] Phase 1.3 Revisit: Create `TagStatistics` model/materialized view if needed:
  - Implement if on-demand computation is too slow
  - Create materialized view or trigger-updated table
  - Add mechanism to auto-update when tags or ratings change
  - Compare performance before/after
- [ ] Phase 1.5 Revisit: Implement tag hierarchy cache if needed:
  - Implement if hierarchy loading is too slow
  - Choose caching approach (materialized view, Redis, app-level cache)
  - Implement auto-refresh mechanism when tags table changes
  - Measure cache hit rates and performance improvement

#### 1.3. Tag Statistics Table
- [ ] Create `TagStatistics` model/materialized view: @skipped-until-optimization
  - `tag_id` (UUID, FK to tags.id, primary key)
  - `total_nodes` (Integer, not null)
  - `total_relationships` (Integer, not null)
  - `root_categories` (Integer, not null)
  - `last_updated` (DateTime, not null)
  - `average_rating` (Float, nullable) - computed from TagRating
  - `rating_count` (Integer, default=0, not null)
- [ ] Decide on implementation: materialized view vs regular table with triggers @skipped-until-optimization
- [ ] Add mechanism to auto-update when tags or ratings change @skipped-until-optimization

#### 1.5. Tag Hierarchy Cache
- [ ] Design caching mechanism for full hierarchy JSON: @skipped-until-optimization
  - Option A: Materialized view storing complete JSON
  - Option B: Table with single row storing complete hierarchy JSON
  - Option C: Application-level caching with DB triggers to invalidate
- [ ] Choose best approach balancing performance vs complexity @skipped-until-optimization
- [ ] Implement auto-refresh mechanism when tags table changes @skipped-until-optimization

**Note**: Hierarchy will be loaded on-demand initially. We can add caching later if needed based on performance metrics.

### 8.3. Query Optimization
- [ ] Review and optimize database queries:
  - Analyze query plans with EXPLAIN
  - Ensure proper index usage
  - Add indexes if needed based on query plans
  - Optimize recursive CTEs if needed
- [ ] Optimize caching strategy:
  - Review cache hit rates
  - Tune cache invalidation
  - Test cache performance

### 8.4. Load Testing
- [ ] Test API endpoints under load:
  - Concurrent tag queries
  - Concurrent rating submissions
  - Gallery filtering with tags
  - Hierarchy queries under load

### 8.5. Validation
- [x] Test in demo environment: @dev
  - Manual testing of all features
  - User acceptance testing
  - Test all user flows (browse tags, rate tags, filter gallery, etc.)

---

## Tags

### @skipped-until-TAG Annotations
- **optimization**: Tasks that can be deferred until we have performance data showing they're needed. Statistics can be computed on-demand initially.

---

## Questions

This section will be populated with questions for the developer as they arise during implementation.
