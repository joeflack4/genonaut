# SQLite References Audit - 2025-10-22

## Summary
Comprehensive search for SQLite references in the codebase after discovering that the Playwright real API config was still using SQLite despite the project migrating to PostgreSQL for all test databases.

## Background
- Git history shows branch `wt2-fix-sqlite-tests` (commits d6fa624, b08f22c) that migrated from SQLite to PostgreSQL for tests
- All config files (`config/local-dev.json`, `config/local-demo.json`, `config/local-test.json`) are configured for PostgreSQL
- However, some files still referenced SQLite

## Findings

### Critical Issues (MUST FIX)

#### 1. Frontend Playwright Real API Config
**File**: `frontend/playwright-real-api.config.ts`
**Lines**: 28, 35
**Issue**: Playwright config still references SQLite database in comments and environment variables
```typescript
// Line 28: Comment says "Test API server with SQLite database"
// Line 35: DATABASE_URL: 'sqlite:///tests/e2e/output/playwright_test.db'
```
**Impact**: HIGH - This config is outdated and conflicts with the actual test-api-server.js implementation (which now uses PostgreSQL)
**Fix**: Remove SQLite references, update to reflect PostgreSQL usage

#### 2. Frontend E2E Test Comment
**File**: `frontend/tests/e2e/gallery-real-api.spec.ts`
**Line**: 54
**Issue**: Old comment says "Started a real API server with SQLite database"
```typescript
// 1. Started a real API server with SQLite database
```
**Impact**: MEDIUM - Misleading documentation in test file
**Fix**: Update comment to say "PostgreSQL test database"

### Cleanup References (OK to keep)

#### 3. Gitignore
**File**: `.gitignore`
**Line**: 80
**Content**: `test/_infra/test_genonaut_api.sqlite3`
**Status**: OK - Cleanup reference for legacy files

#### 4. Makefile
**File**: `Makefile`
**Line**: 507
**Content**: `find . -type f -name "*.sqlite" -delete`
**Status**: OK - Generic cleanup command

### Backend Compatibility Code (OK to keep)

#### 5. Content Service SQLite Fallback
**File**: `genonaut/api/services/content_service.py`
**Lines**: 60-62, 1080-1081
**Purpose**: Fallback code for non-PostgreSQL backends (SQLite compatibility layer)
```python
# Line 60-62: Check dialect and defer tag filtering for non-PostgreSQL
if dialect_name and dialect_name != "postgresql":
    # Defer tag filtering to Python post-processing

# Line 1080-1081: SQLite detection for pagination logic
is_sqlite = session.bind and session.bind.dialect.name != "postgresql"
if use_junction_table_filter and tag_uuids and not is_sqlite:
```
**Status**: OK - This is defensive programming for compatibility, not an indication of active SQLite test usage

### Notes Files (Documentation/Historical)

#### 6. Tag Query Performance Notes
**File**: `notes/issues/by_priority/medium_high/fix-gallery-tag-query-and-performance--notes.md`
**Lines**: 43, 53, 90, 104, 958
**Purpose**: Documents SQLite compatibility considerations during tag migration
**Status**: OK - Historical documentation

#### 7. Database Init Tests Notes
**File**: `notes/db-init-tests.md`
**Lines**: 75, 209
**Purpose**: References PostgreSQL vs SQLite differences and TODO to test both
**Status**: OK - Documentation, TODO can be ignored (we use PostgreSQL for all tests now)

#### 8. Fix Tests Notes
**File**: `notes/fix-tests-2025-10-22.md`
**Lines**: 11, 82, 85, 86, 90, 130
**Purpose**: Documents the SQLite to PostgreSQL migration I just completed
**Status**: OK - Accurate documentation of fixes

### Separate Projects (Not Main Test Database)

#### 9. md_manager Library
**Files**:
- `libs/md_manager/CLAUDE.md` (line 25)
- `libs/md_manager/AGENTS.md` (line 25)
- `libs/md_manager/.gitignore` (lines 51-52)
- `libs/md_manager/notes/*.md`

**Purpose**: The md_manager library is a separate CLI tool that uses SQLite for its own data storage (markdown file tracking)
**Status**: OK - This is NOT related to the main Genonaut test database. The md_manager library legitimately uses SQLite for its own purposes.

## Tests Currently Using SQLite

**NONE** - All tests now use PostgreSQL test databases:
- Unit tests: Use PostgreSQL test database (`genonaut_test` from `config/local-test.json`)
- Database tests: Use PostgreSQL test database
- API integration tests: Use PostgreSQL test database
- Frontend E2E tests: Use PostgreSQL test database (via `test-api-server.js` with ENV_TARGET='local-test')

## How SQLite References Appeared

Based on git history:
1. Originally, the project used SQLite for test databases
2. Branch `wt2-fix-sqlite-tests` (commits d6fa624, b08f22c around Oct 20, 2025) migrated tests from SQLite to PostgreSQL
3. The migration fixed backend tests and updated most frontend code
4. However, `frontend/playwright-real-api.config.ts` was missed in the migration
5. The config file's SQLite `DATABASE_URL` override was being IGNORED by the Node.js test-api-server.js script (which reads from .env files instead)
6. This created a silent disconnect: config said SQLite, but actual implementation used PostgreSQL

## Action Items

- [x] Create this documentation file
- [x] Fix `frontend/playwright-real-api.config.ts` - Remove SQLite DATABASE_URL, update comments
- [x] Fix `frontend/tests/e2e/gallery-real-api.spec.ts` line 54 comment
- [x] Update `genonaut/api/services/content_service.py` comment to reflect PostgreSQL-only tests
- [x] Update `notes/fix-tests-2025-10-22.md` with these additional fixes

## Conclusion

**No tests are currently using SQLite.** The SQLite references found were:
1. Outdated config/comments in Playwright files (need fixing)
2. Cleanup references in .gitignore/Makefile (harmless)
3. Defensive compatibility code in backend (intentional)
4. Historical documentation in notes files (accurate)
5. Separate md_manager library using SQLite for its own purposes (unrelated)

The critical issue was that `frontend/playwright-real-api.config.ts` had stale SQLite configuration that was being ignored by the actual implementation.
