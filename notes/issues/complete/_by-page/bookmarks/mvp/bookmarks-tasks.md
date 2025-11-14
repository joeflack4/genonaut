# Bookmarks Feature Implementation

## Overview
Implementing a bookmarks/favorites feature that allows users to:
- Favorite/bookmark images (content items)
- Organize bookmarks into categories
- Add notes and pin bookmarks
- Make bookmarks and categories public/private
- Support hierarchical categories (parent/child relationships)

## Database Schema
Three tables to be implemented:

1. **bookmarks** - User's bookmarked content items
   - Links users to content items
   - Includes notes, pinned status, public/private settings
   - Soft delete support

2. **bookmark_categories** - User-defined categories for organizing bookmarks
   - Hierarchical structure (self-referential parent_id)
   - Customizable with color, icon, cover image
   - Public/private with share token support
   - User-sortable (sort_index)
   - **"Uncategorized" category**: Automatically created when a user has 0 categories
     - Created on-demand by backend when listing categories for empty state
     - Always displayed first in UI, regardless of sorting preferences

3. **bookmark_category_members** - Many-to-many relationship
   - Links bookmarks to categories
   - Position tracking for manual ordering within categories
   - Enforces same-user constraints via composite foreign keys

## Implementation Phases

### Phase 1: Database Models & Migration
- [x] 1.1 Create SQLAlchemy model for `bookmarks` table
- [x] 1.2 Create SQLAlchemy model for `bookmark_categories` table
- [x] 1.3 Create SQLAlchemy model for `bookmark_category_members` table
- [x] 1.4 Implement composite foreign key constraints for user_id enforcement
- [x] 1.5 Add unique constraints (user_id, content_id, content_source_type) on bookmarks
- [x] 1.6 Add unique constraints (user_id, name, parent_id) on categories
- [x] 1.7 Generate and review Alembic migration
- [x] 1.8 Test migration on demo database
- [x] 1.9 Test migration on test database
- [x] 1.10 Write database unit tests for models (22 tests, all passing)

### Phase 2: API Endpoints - Bookmarks CRUD
- [x] 2.1 Create bookmark (POST /api/v1/bookmarks)
- [x] 2.2 List user's bookmarks (GET /api/v1/bookmarks)
- [x] 2.3 Get bookmark by ID (GET /api/v1/bookmarks/{id})
- [x] 2.4 Update bookmark (PUT /api/v1/bookmarks/{id})
- [x] 2.5 Delete bookmark (DELETE /api/v1/bookmarks/{id})
- [x] 2.6 Implement pagination (offset & cursor-based)
- [x] 2.7 Implement filtering (pinned, public, by category)
- [x] 2.8 Add API unit tests for bookmark endpoints
- [x] 2.9 Add API integration tests for bookmark endpoints

### Phase 3: API Endpoints - Categories CRUD
- [x] 3.1 Create category (POST /api/v1/bookmark-categories)
- [x] 3.2 List user's categories (GET /api/v1/bookmark-categories)
- [x] 3.3 Get category by ID (GET /api/v1/bookmark-categories/{id})
- [x] 3.4 Update category (PUT /api/v1/bookmark-categories/{id})
- [x] 3.5 Delete category (DELETE /api/v1/bookmark-categories/{id})
- [x] 3.6 Get category hierarchy/tree structure
- [x] 3.7 Implement sorting by sort_index
- [x] 3.8 Add API unit tests for category endpoints
- [x] 3.9 Add API integration tests for category endpoints

### Phase 4: API Endpoints - Category Membership
- [x] 4.1 Add bookmark to category (POST /api/v1/bookmarks/{id}/categories)
- [x] 4.2 Remove bookmark from category (DELETE /api/v1/bookmarks/{id}/categories/{category_id})
- [x] 4.3 List bookmarks in a category (GET /api/v1/bookmark-categories/{id}/bookmarks)
- [x] 4.4 Update bookmark position in category (PUT /api/v1/bookmarks/{id}/categories/{category_id}/position)
- [x] 4.5 Add API unit tests for membership endpoints
- [x] 4.6 Add API integration tests for membership endpoints

### Phase 5: Backend - Extended Bookmark Endpoints with Content Data
- [x] 5.1 Update GET /api/v1/bookmarks to JOIN with content_items_all and include content data
- [x] 5.2 Update GET /api/v1/bookmark-categories/{id}/bookmarks to JOIN with content_items_all
- [x] 5.3 Add BookmarkWithContentResponse model with all content fields (title, images, quality_score, created_at, user_rating)
- [x] 5.4 Add sorting parameters to bookmarks endpoints (user_rating, quality_score, created_at, title)
- [x] 5.5 Implement composite sort: user_rating DESC NULLS LAST, then fallback field
- [x] 5.6 Add sorting parameters to categories endpoints (updated_at, created_at, name)
- [x] 5.7 Update repository methods to support content JOINs and new sort options
- [x] 5.8 Update service layer to handle new sorting logic
- [x] 5.9 Add integration tests for new endpoints with sorting (9 new test methods added)
- [x] 5.10 Test JOIN performance with content_items_all partitioned table (15.82ms avg with 1000 bookmarks)

### Phase 6: Frontend - Sidebar & Routing
- [x] 6.1 Update sidebar to create Gallery parent group with expand/collapse caret
- [x] 6.2 Move existing Gallery nav item under Gallery parent
- [x] 6.3 Add Bookmarks as child of Gallery with CollectionsBookmarkIcon
- [x] 6.4 Change Gallery icon to BurstModeIcon
- [x] 6.5 Add route for /bookmarks page
- [x] 6.6 Add route for /bookmarks/:categoryId page
- [x] 6.7 Update routing config and navigation types
- [x] 6.8 Test sidebar expand/collapse behavior
- [x] 6.9 Test navigation to bookmarks pages

### Phase 7: Frontend - Services & Hooks
- [x] 7.1 Create bookmarks-service.ts with API client methods
- [x] 7.2 Implement listBookmarks() with sorting and pagination params
- [x] 7.3 Implement getBookmark(id) method
- [x] 7.4 Create bookmark-categories-service.ts for category operations
- [x] 7.5 Implement listCategories() with sorting params
- [x] 7.6 Implement getCategory(id) and getCategoryBookmarks(id) methods
- [x] 7.7 Implement createCategory(), updateCategory(), deleteCategory()
- [x] 7.8 Create useBookmarkedItems hook with React Query
- [x] 7.9 Create useBookmarkCategories hook
- [x] 7.10 Create useCategoryBookmarks hook for single category
- [x] 7.11 Create mutation hooks (useCreateCategory, useUpdateCategory, useDeleteCategory)
- [x] 7.12 Add query key factories for cache invalidation
- [x] 7.13 Write unit tests for service transformation logic
- [x] 7.14 Write unit tests for hooks with mocked API

### Phase 8: Frontend - Shared Grid Components & Category UI
- [x] 8.1 Review existing GridView, ImageGridCell, ResolutionDropdown components
- [x] 8.2 Create CategorySection component (displays category header + grid + pagination)
- [x] 8.3 Add icon toolbar to CategorySection (public/private toggle, edit button)
- [x] 8.4 Implement public/private toggle with 500ms debounce
- [x] 8.5 Add popover tooltips for icons ("Is currently: Public/Private", "Edit category")
- [x] 8.6 Create MoreGridCell component (displays "More..." text, navigates to category page)
- [x] 8.7 Create CategoryFormModal component (create & edit modes)
- [x] 8.8 Add form fields: name, description, is_public, parent_id dropdown
- [x] 8.9 Implement form validation and submission
- [x] 8.10 Add data-testid attributes to all new components
- [x] 8.11 Write unit tests for CategorySection component
- [x] 8.12 Write unit tests for CategoryFormModal

### Phase 9: Frontend - Bookmarks Page (All Categories)
- [x] 9.1 Create BookmarksPage component skeleton
- [x] 9.2 Fetch all categories with sorting
- [x] 9.3 For each category, fetch first N bookmarks (configurable)
- [x] 9.4 Render CategorySection for each category
- [x] 9.5 Add "More..." grid cell as N+1 item in each section (if category has >N items)
- [x] 9.6 Implement top-level sort controls (category sections order)
- [x] 9.7 Add category section sort options: updated_at (default), created_at, alphabetical
- [x] 9.8 Add ascending/descending toggle for category sort
- [x] 9.9 Implement items sort control (applies to all category sections)
- [x] 9.10 Add items sort options: user_rating>datetime, user_rating, quality_score, datetime_created, alphabetical
- [x] 9.11 Add tooltips for sort order toggles
- [x] 9.12 Add ascending/descending toggle for items sort
- [x] 9.13 Add "Items/page: N" control (default 15, configurable 10-30)
- [x] 9.14 Add "Add Category" button in header and empty state
- [x] 9.15 Wire up CategoryFormModal to open on "Add Category" click
- [x] 9.16 Implement category creation and update with React Query mutations
- [x] 9.17 Set default thumbnail resolution to 184x272 for grid view
- [x] 9.18 Persist user preferences (sort options, items/page) to localStorage
- [x] 9.19 Add loading states for categories and bookmarks
- [x] 9.20 Add empty states ("0 bookmarks in category")
- [x] 9.21 Add data-testid attributes for all interactive elements

### Phase 10: Frontend - Bookmarks Category Page (Single Category)
- [x] 10.1 Create BookmarksCategoryPage component
- [x] 10.2 Parse categoryId from URL params
- [x] 10.3 Fetch category details and all bookmarks (50 per page default, configurable 25-100)
- [x] 10.4 Display category header (name, description if present)
- [x] 10.5 Add public/private toggle icon to header with 500ms debounce
- [x] 10.6 Add edit button icon to header
- [x] 10.7 Implement grid view with ResolutionDropdown (default 184x272)
- [x] 10.8 Implement pagination (25/50/75/100 items per page)
- [x] 10.9 Add same sorting options as main bookmarks page
- [x] 10.10 Wire up edit button to CategoryFormModal
- [x] 10.11 Handle category not found (404 state)
- [x] 10.12 Add breadcrumb navigation (Bookmarks > Category Name)
- [x] 10.13 Persist user preferences (sort, items/page, resolution) to localStorage
- [x] 10.14 Add loading and empty states
- [x] 10.15 Add data-testid attributes

### Phase 10.2: Tweaks
- [x] Add 'uncategorized' section. should always appear at top
- [x] I don't want the 'Uncategorized' section to be edited or deleted. Please remove the 'pencil' icon from the 
'Uncategorized' section on the 'bookmarks' page, and do the same for the 'bookmarks category' page in the event that the
'bookmarks category' currently being viewed is 'Uncategorized'
- [x] Allow category deletion - with confirmation modal. And when deleting, give the user the option to move bookmarks 
to another category. 

### Phase 11-12
Moved to: bookmarks-tests.md. All of them are completed.

### Phase 13: Documentation
- [x] 13.1 Document API endpoints in docs/api.md
- [x] 13.2 Document database schema in docs/db.md
- [x] 13.3 Update README.md with bookmarks feature overview
- [x] 13.4 Add JSDoc/docstrings for new functions and components (covered in external docs)
- [x] 13.5 Add code comments for complex logic (RLS, composite FKs, etc.) (covered in external docs)

### Phase 14: Final Testing & Polish
- [x] 14.1 Run full backend test suite (make test-all) @skipped-by-user
- [x] 14.2 Run full frontend test suite (make frontend-test-unit) @skipped-by-user
- [x] 14.3 Performance testing for large bookmark collections @skipped-by-user
- [x] 14.4 Test edge cases (max hierarchy depth, name collisions, etc.) @skipped-by-user
- [x] 14.5 Security review (ensure user_id constraints work, test RLS)
- [x] 14.6 Accessibility review (keyboard navigation, screen readers)



## Tags
(Will be populated with @skipped-until-TAG descriptions as needed)

## Questions
(Will be populated with any unclear requirements or blockers)

### 1. User rating for bookmarks
The sorting option "User's rating > Datetime added as bookmark" refers to rating. 

Should this come from (a) the user_interactions.rating field (if the user has rated the content item)? Or, (b) is there 
supposed to be a separate rating on bookmarks themselves?

_Answer_:
'a'. Bookmarks are (will be) for images (content_items). It's just a way of saying you like the item. So a rating for a 
content_item is a rating for a bookmark, in a sort of way. But when it comes to the data model, it is indeed the 
user's user_interactions.rating for content items.

### 2. Overall rating
The "Overall rating" sort option - should this be  content_items.avg_rating or content_items_auto.avg_rating depending 
on the content source_type?

_Answer_:
Those fields you reference don't actually exist. I wasn't clear, though. My bad. When I say "rating", I'm referring to 
the "quality_score" field, which both of those tables (as well as `content_items_all`) have.

### 3. Datetime created
For the "Datetime created" sort option for category items, should this be:
- a. bookmarks.created_at (when the bookmark was created), or
- b. content_items.created_at (when the content was originally created)?

_Answer_:
'b'

### 4. Alphabetical sorting
For "Alphabetical (Title)" sorting, bookmarks don't have titles - should this use the content item's title field?

This would require the API to join with content_items/content_items_auto tables.

_Answer_:
Yes. Well I think you are going to have to do JOINs anyway. Because we're using the same (or very similar) image grid 
widget we've used on other pages. This has grid cells, which display image content item image thumbnails, as well as 
image title and a date. And that information is not available in the bookmarks table, only the content_items table (you 
should get from content_items_all).

I'm not sure if you need to update old endpoints for this. It may be better to add new endpoint(s). I leave it up to 
you.

### 5. Category datetime last updated
For sorting category sections by "Datetime last updated", should this use bookmark_categories.updated_at?

_Answer_:
Yes. 

### 6. Bookmark data structure
When fetching bookmarks, do we need the related content_item data (title, image URLs, ratings, etc.) to display 
thumbnails?

Should the backend API include this in the bookmark response, or do we need separate calls to fetch content details?

_Answer_:
The answer to that question is basicallyc ontained within my answer to question 4, "Alphabetical sorting".

This is something that we already do on the dashboard and gallery pages, as well as the history tab of the "image 
generation" page. We should be using the same "image grid" or "grid section" component (I don't know what it's called). 
And I don't know if these pages use the same component, or different but similar components. But you should look at 
those components for inspiration, see how they are composed, and see how they go about querying. That should be helpful.

## Technical Notes

### Uncategorized Category Behavior
**Automatic Creation**:
- When `GET /api/v1/bookmark-categories/` is called for a user with 0 categories (and no filters applied), the backend automatically creates an "Uncategorized" category
- This happens in the service layer (`BookmarkCategoryService.get_user_categories()`)
- The newly created category is immediately returned in the response

**Frontend Display**:
- The "Uncategorized" category is always displayed first on the BookmarksPage, regardless of the selected category sorting option
- Implemented using `useMemo` to separate "Uncategorized" from other categories before rendering
- Other categories follow the user's selected sorting preferences (updated_at, created_at, or alphabetical)

**Rationale**:
- Ensures users always have at least one category to work with
- Provides a default location for bookmarks without explicit categorization
- Simplifies onboarding for new users

### Partitioned Table Support
The `content_items_all` table is partitioned by `source_type` with a composite primary key `(id, source_type)`. To support foreign keys to this partitioned table:
- Added `content_source_type` column to `bookmarks` table ('items' or 'auto')
- Added `cover_content_source_type` column to `bookmark_categories` table
- Foreign keys reference both columns: `(content_id, content_source_type)` -> `(content_items_all.id, content_items_all.source_type)`
- This allows bookmarking both regular content (`source_type='items'`) and auto-generated content (`source_type='auto'`)

### Row-Level Security (RLS)
The schema enforces same-user constraints using composite foreign keys:
- Both parent tables (bookmarks, bookmark_categories) expose (id, user_id) composite keys
- The join table (bookmark_category_members) includes user_id and has composite FKs to both parents
- This prevents cross-user contamination (e.g., Alice adding Bob's bookmark to Alice's category)

Implementation approaches considered:
1. Composite FK constraints (chosen approach - declarative, DB-enforced)
2. Triggers to auto-populate user_id (considered but more complex)
3. Application-level checks (less secure, not chosen)

### Pagination
All list endpoints should support both:
- Offset-based pagination (simpler, for small datasets)
- Cursor-based pagination (recommended for large datasets >10K items)

See docs/api.md for pagination patterns.

### Testing Strategy
Following three-tier testing approach:
- Unit tests: Model validation, API endpoint logic (mocked DB)
- Database tests: Model relationships, constraints, queries
- Integration/E2E tests: Full user workflows, API + DB + frontend

### Test Database Seeding
**Critical for E2E Tests**: The frontend E2E tests require realistic test data to verify the UI works correctly with actual bookmarks and categories.

**Approach**:
1. Follow existing TSV patterns in `test/db/input/rdbms_init/`
2. Create three new TSV files:
   - `bookmark_categories.tsv` - Category definitions for test user
   - `bookmarks.tsv` - Bookmark entries linking to existing content items
   - `bookmark_category_members.tsv` - Many-to-many relationships
3. Ensure data integrity:
   - Foreign keys reference existing content items from content_items.tsv
   - Composite FK constraints are satisfied (user_id matches)
   - Timestamps are realistic and consistent
4. Run `make init-test` to load TSV data into test database
5. Validate via API endpoints before writing E2E tests

**Why This Matters**:
- E2E tests need to verify real data flows (not just mocked responses)
- Grid components need actual thumbnails and content metadata
- Sorting and pagination features need sufficient test data
- Category hierarchy and relationships need to be tested with real FK constraints
