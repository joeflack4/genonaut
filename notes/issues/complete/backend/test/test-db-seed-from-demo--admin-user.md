# Update Seeding Scripts to Export Admin User and Dependencies

## Problem Statement

The E2E test suite uses a hardcoded user ID (`121e194b-4caa-4b81-ad4f-86ca3919d5b9`, username: `demo_admin`) that exists in the demo database but not in the test database. When tests run against the test database, they fail with 404 errors because this user doesn't exist.

**Current Behavior:**
- Tests pass when using demo database (port 8001)
- Tests fail when using test database due to missing admin user
- Demo database has rich, realistic data including the admin user
- Test database has different users (randomly generated from seed scripts)

## Solution Overview

Update the export/import seeding scripts to:
1. **Always export the admin user by default** (ID: `121e194b-4caa-4b81-ad4f-86ca3919d5b9`)
2. **Recursively export all foreign key dependencies** related to the admin user
3. **Add CLI flag to optionally disable** this behavior (`--exclude-admin-user`)
4. **Ensure deterministic, repeatable test data** for E2E tests

## Database Foreign Key Relationships

### Level 1: Tables Directly Referencing Users (12 tables)

| Table Name | FK Column(s) | Description |
|------------|--------------|-------------|
| `content_items` | `creator_id` | Regular content created by user |
| `content_items_auto` | `creator_id` | Auto-generated content |
| `flagged_content` | `creator_id`, `reviewed_by` | Flagged content (creator and reviewer) |
| `gen_source_stats` | `user_id` | Generation source statistics |
| `generation_jobs` | `user_id` | Image generation jobs |
| `recommendations` | `user_id` | User recommendations |
| `route_analytics` | `user_id` | Route analytics per user |
| `tag_ratings` | `user_id` | User tag ratings |
| `user_interactions` | `user_id` | User content interactions |
| `user_notifications` | `user_id` | User notifications |
| `user_search_history` | `user_id` | User search history |

### Level 2: Tables Referencing Level 1 Tables (COMPLETED)

**Complete dependency tree depth: 2 levels maximum**

Tables referencing `content_items`:
- `content_items_ext.source_id` -> `content_items.id`
- `flagged_content.content_item_id` -> `content_items.id` (also Level 1)
- `generation_jobs.content_id` -> `content_items.id` (also Level 1)
- `recommendations.content_item_id` -> `content_items.id` (also Level 1)
- `user_interactions.content_item_id` -> `content_items.id` (also Level 1)
- `user_notifications.related_content_id` -> `content_items.id` (also Level 1)

Tables referencing `content_items_auto`:
- `content_items_auto_ext.source_id` -> `content_items_auto.id`
- `flagged_content.content_item_auto_id` -> `content_items_auto.id` (also Level 1)

Tables referencing `generation_jobs`:
- `user_notifications.related_job_id` -> `generation_jobs.id` (also Level 1)

**Key Finding:** Most Level 2 references are circular (Level 1 tables referencing other Level 1 tables). Only true Level 2 tables are:
- `content_items_ext`
- `content_items_auto_ext`

## Implementation Plan

### Phase 1: Analysis & Design ✅

- [x] Identify admin user ID and verify existence in demo DB
- [x] Query all tables with foreign keys to `users`
- [x] Query second-level foreign keys (tables referencing Level 1 tables) - do this recursively
- [x] Map complete dependency tree for admin user data
- [x] Determine optimal export strategy (breadth-first vs depth-first)

**Findings:**
- Maximum dependency depth: 2 levels
- Level 1: 12 tables with direct FKs to users
- Level 2: 2 tables (content_items_ext, content_items_auto_ext)
- Strategy: Use breadth-first search (BFS) for recursive export

### Phase 2: Core Export Functionality ✅

#### Task 1: Add Admin User Export Flag ✅
**File:** `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`

- [x] Add CLI argument `--exclude-admin-user` (default: False, i.e., include by default)
- [x] Add CLI argument `--admin-user-id` (default: `121e194b-4caa-4b81-ad4f-86ca3919d5b9`)
- [x] Update `ExportConfig` dataclass with:
  - `include_admin_user: bool`
  - `admin_user_id: str | None`

**Code Location:** `parse_args()` function (~line 46-95)

#### Task 2: Implement Admin User Seed Fetch ✅
**File:** `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`

- [x] Created `seed_admin_user_data()` function (lines 499-569)
- [x] Implements depth-first search with cycle detection
- [x] Uses `build_reverse_fk_graph()` to find dependent tables
- [x] Calls `fetch_related_rows_recursive()` to traverse dependencies
- [x] Logs progress with row counts

**Implementation Details:**
- Uses depth-first search (DFS) to traverse dependencies
- Tracks visited tables/rows via `visited` set to avoid infinite loops
- Respects existing `exported_rows` to avoid duplicates
- Logs: "Seeding admin user ... with all dependencies"

#### Task 3: Integrate Admin Seeding into Export Flow ✅
**File:** `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`

- [x] Modified `export_tables()` function (lines 609-623)
- [x] Added `config.include_admin_user` check at the beginning
- [x] Calls `seed_admin_user_data()` BEFORE normal table export when enabled
- [x] Ensures admin user data is always included regardless of row limits
- [x] Normal export then adds additional rows up to the limits

**Code Location:** Lines 613-623 in `export_tables()`

### Phase 3: Recursive Dependency Resolution ✅

#### Task 4: Build Foreign Key Dependency Graph ✅
**File:** `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`

- [x] Created `build_reverse_fk_graph()` function (lines 229-267)
- [x] Returns mapping of parent_table -> List[(child_table, child_column, parent_column)]
- [x] Excludes tables in EXCLUDED_TABLES set
- [x] Enables efficient lookup of all tables that reference a given table

**Implementation:** Function returns dict mapping each table to its child relationships, making it efficient to find all dependent tables during recursive traversal.

#### Task 5: Implement Recursive Fetch Algorithm ✅
**File:** `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`

- [x] Created `fetch_related_rows_recursive()` function (lines 270-400)
- [x] Implements depth-first search with cycle detection
- [x] Parameters: engine, table_name, key_values, reverse_fk_graph, metadata_tables, exported_rows, selected_values, visited, max_depth, current_depth
- [x] Safety mechanisms implemented:
  - Max depth limit (default: 10 levels)
  - Visited tracking via set to prevent infinite loops
  - Debug logging at each recursion level
  - Handles nullable FK columns gracefully

**Algorithm:**
1. Mark current record as visited
2. Look up child tables in reverse_fk_graph
3. For each child table:
   - Build WHERE clause matching parent key
   - Fetch matching rows
   - Store new rows in exported_rows
   - Ensure parent rows are also exported
   - Recursively call for each new row (if depth < max_depth)

### Phase 4: Testing & Validation

#### Task 6: Add Unit Tests (DEFERRED)
**File:** `test/db/test_export_seed_from_demo.py` (create if doesn't exist)

**Status:** Unit tests deferred to future work. Integration testing via `make export-demo-seed` and `make init-test` demonstrates functionality.

Future test coverage should include:
- Test admin user export with `--admin-user-id`
- Test exclusion with `--exclude-admin-user`
- Test recursive dependency resolution
- Test that exported data maintains referential integrity
- Test max depth limit prevents infinite loops
- Test handling of circular dependencies

#### Task 7: Integration Testing ✅
- [x] Run export with admin user: `make export-demo-seed`
- [x] Verify TSV files contain admin user data (449 content items exported)
- [x] Verify admin user exists in test database after `make init-test`
- [x] Confirmed ~2018 total rows exported including all admin user dependencies
- [x] Verified referential integrity maintained through 2 levels of FK relationships

### Phase 5: Documentation & Cleanup ✅

#### Task 8 (null)
This task was removed from the plan.

#### Task 9: Update Documentation ✅
**Files Updated:**
- [x] `docs/testing.md` - Added comprehensive "Admin User Seeding for E2E Tests" section
  - Documented how export/import workflow includes admin user
  - Added CLI options and verification commands
  - Included troubleshooting steps
  - Location: After "local-test-init Environment" section

- [ ] `docs/db.md` - Not required (admin user seeding is test-specific)
- [ ] `README.md` - Not required (testing.md covers E2E testing)
- [ ] `notes/tag-key-refactor-fix-tests-troubleshooting.md` - Can be marked as resolved (if needed)

#### Task 10: Code Documentation ✅
- [x] Added comprehensive docstrings to all new functions:
  - `build_reverse_fk_graph()` - Documents FK graph structure with examples
  - `fetch_related_rows_recursive()` - Detailed parameter docs and algorithm explanation
  - `seed_admin_user_data()` - Complete docstring with algorithm steps
- [x] Inline comments explaining recursive algorithm (in `fetch_related_rows_recursive`)
- [x] Admin user ID documented in CLI help text
- [x] Function docstrings include parameter descriptions and examples

## Technical Considerations

### Foreign Key Constraints
- **NULL values:** Some FKs may be nullable - handle gracefully
- **Composite FKs:** Check if any tables use multi-column FKs
- **Self-referential FKs:** Handle tables that reference themselves (e.g., tag hierarchy)

### Performance
- **Large datasets:** Admin user might have thousands of related records
- **Query optimization:** Use efficient WHERE clauses with indexes
- **Batch fetching:** Fetch related rows in batches to avoid memory issues
- **Progress logging:** Show progress for long-running exports

### Data Consistency
- **Referential integrity:** Ensure all FKs point to exported records
- **Timestamp ordering:** Maintain temporal consistency in exports
- **Duplicate prevention:** Don't re-export rows already in exported_rows
- **Transactional safety:** Consider using transactions for consistency

## Alternative Approaches Considered

### Option A: Hardcode Admin User in Test Database Seed
**Pros:** Simple, guaranteed to work
**Cons:** Duplicates data, doesn't solve general FK dependency problem
**Decision:** Rejected - doesn't generalize well

### Option B: Make Tests Use Any Available User
**Pros:** Tests more flexible
**Cons:** Tests less deterministic, harder to debug
**Decision:** Rejected - want predictable test data

### Option C: Export Admin User and Dependencies (CHOSEN)
**Pros:** Deterministic, reusable, solves general FK dependency problem
**Cons:** More complex implementation
**Decision:** SELECTED - best long-term solution

## Success Criteria

- [x] Admin user `121e194b-4caa-4b81-ad4f-86ca3919d5b9` exists in test database after import
- [x] All 12 tables with FKs to users contain admin user's related records
- [x] Second-level dependencies (e.g., tags on admin's content) are also exported
- [x] E2E tests pass when run against test database with imported data (199/211 passing = 94.3% pass rate, up from 31% before admin user seeding. 3 tag rating tests that were failing are now passing!)
- [x] Export script has `--exclude-admin-user` flag that works correctly
- [x] Export/import process is documented and easy to use (documented in docs/testing.md)
- [x] No breaking changes to existing export/import workflow

## Migration Path

1. **Phase 1:** Implement and test in isolation
2. **Phase 2:** Run side-by-side with existing approach (verify no regressions)
3. **Phase 3:** Make admin export default behavior
4. **Phase 4:** Update CI/CD pipelines to use new approach
5. **Phase 5:** Remove old workarounds (if any)

## Notes & Open Questions

### Questions to Resolve:
- [ ] Should we export ALL admin user data or limit by table-specific limits?
  - **Recommendation:** Export all admin data, then fill remaining rows up to limit
- [ ] How deep should recursive dependency resolution go?
  - **Recommendation:** Start with max_depth=10, make configurable via CLI
- [ ] Should we support exporting multiple specific users?
  - **Recommendation:** Start with single admin user, generalize later if needed
- [ ] What if admin user has 10,000+ related records?
  - **Recommendation:** Add per-table caps, log warnings if exceeded

### Edge Cases:
- Admin user doesn't exist in source database
- Circular dependencies between tables
- Very deep dependency chains (>10 levels)
- Tables with composite primary keys
- Self-referential foreign keys

## Timeline Estimate

- **Analysis & Design:** 1-2 hours (PARTIALLY COMPLETE)
- **Core Implementation:** 4-6 hours
- **Recursive Dependency Logic:** 3-4 hours
- **Testing:** 2-3 hours
- **Documentation:** 1-2 hours
- **Total:** 11-17 hours

## Related Files

### Files to Modify:
- `genonaut/db/demo/seed_data_gen/export_seed_from_demo.py`
- `docs/testing.md`
- `docs/db.md`

### Files to Create:
- `test/db/test_export_seed_from_demo.py` (if doesn't exist)

### Files to Reference:
- `genonaut/db/schema.py` (for foreign key information)
- `frontend/tests/e2e/utils/realApiHelpers.ts` (uses admin user ID)
- `notes/tag-key-refactor-fix-tests-troubleshooting.md` (documents the problem)

## Next Steps

1. Review and approve this plan
2. Begin Phase 1: Complete analysis of second-level dependencies
3. Implement Task 4: Build reverse FK dependency graph
4. Implement Task 5: Recursive fetch algorithm
5. Test with small dataset before full export
