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

### Phase: Final 1: Documentation
- [ ] 9.1 Document API endpoints in docs/api.md
- [ ] 9.2 Document database schema in docs/db.md
- [ ] 9.3 Update README.md with bookmarks feature overview
- [ ] 9.4 Add JSDoc/docstrings for new functions and components
- [ ] 9.5 Add code comments for complex logic (RLS, composite FKs, etc.)

### Phase: Final 2: Final Testing & Polish
- [ ] 10.1 Run full backend test suite (make test-all)
- [ ] 10.2 Run full frontend test suite (make frontend-test)
- [ ] 10.3 Manual browser testing of all features
- [ ] 10.4 Performance testing for large bookmark collections
- [ ] 10.5 Test edge cases (max hierarchy depth, name collisions, etc.)
- [ ] 10.6 Security review (ensure user_id constraints work, test RLS)
- [ ] 10.7 Accessibility review (keyboard navigation, screen readers)
- [ ] 10.8 Address any remaining TODOs or skipped tests

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
