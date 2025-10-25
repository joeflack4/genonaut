# Test Database Persistence Investigation

## Summary

E2E tests are failing because the test database (`genonaut_test`) likely doesn't have sufficient seed data loaded. Tests are gracefully skipping when data is unavailable, but should be passing with proper data.

## Database Configuration

### Environment Configurations

All environments use **port 8001** for the API, but connect to different databases:

| Environment | Database Name | API Port | Redis DB | Config File |
|------------|---------------|----------|----------|-------------|
| **test** | genonaut_test | 8001 | 3 | config/local-test.json |
| **demo** | genonaut_demo | 8001 | 2 | config/local-demo.json |
| **dev** | genonaut_dev | 8001 | 1 | config/local-dev.json |

### E2E Test Configuration

From `frontend/playwright.config.ts`:
- Frontend runs on: `http://127.0.0.1:4173`
- API endpoint: `http://127.0.0.1:8001`
- **Critical**: E2E tests connect to whatever database is served on port 8001

**Problem**: If you run `make api-demo` (common during development), E2E tests will connect to the **demo** database, not the test database!

## Test Data Availability

### Test Data Files Exist

Located in `test/db/input/rdbms_init/`:

| File | Lines | Purpose |
|------|-------|---------|
| content_items_full.tsv | 1,001 | 1000 content items + header |
| content_item_autos_full.tsv | 1,001 | 1000 auto-generated items |
| generation_jobs_full.tsv | 1,001 | 1000 generation jobs |
| content_items.tsv | 101 | 100 content items (smaller set) |
| users.tsv | 58 | 57 users |
| recommendations.tsv | 1 | Header only (no data) |
| user_interactions.tsv | 1 | Header only (no data) |

**Tags**: Tags are NOT stored as TSV files. They are generated from content using the `seed_tags_from_content.py` script.

### Tag Generation

Tags must be extracted from content after loading:

```bash
# Generate tags from content tags_old JSONB field
python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test --clear-existing
```

This script:
1. Extracts unique tag names from `content_items.tags_old` and `content_items_auto.tags_old` JSONB fields
2. Creates entries in the `tags` table with UUIDs
3. The content items in the TSV files have hundreds of tags in their JSONB data

## Root Cause Analysis

### Why Tests Skip

Tests check for data availability and skip when:
1. **Gallery/Image View Tests**: No content items in gallery results
2. **Tag Rating Tests**: No tags in tag hierarchy tree
3. **Tag Cardinality Tests**: No tag statistics available
4. **Pagination Tests**: Less than 2 pages of data (< 50 items with page_size=25)

### Likely Causes

**Cause 1: Test Database Not Initialized**
```bash
# Check if genonaut_test database exists
psql -l | grep genonaut
```

**Cause 2: Test Database Not Seeded with TSV Data**
- `make init-test` creates the database schema but may not load TSV data
- Need to explicitly load test data

**Cause 3: Tags Not Generated**
- Even if content is loaded, tags table might be empty
- Need to run `seed_tags_from_content.py` for test environment

**Cause 4: E2E Tests Running Against Wrong Database**
- If demo API is running on port 8001, E2E tests use demo database
- Demo database might have different (or no) data

## Solution Paths

### Option 1: Ensure Test Database is Properly Seeded (Recommended)

**Step 1: Initialize test database**
```bash
make init-test
```

**Step 2: Load test data from TSV files**

Currently, there's no `make` target that loads test TSV data into the test database. Need to find or create a script.

Check if there's a loading script:
```bash
# Search for TSV loading functionality
find genonaut test -name "*.py" -type f | xargs grep -l "\.tsv" | grep -i load
```

**Step 3: Generate tags from content**
```bash
python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test --clear-existing
```

**Step 4: Start test API server**
```bash
make api-test
```

**Step 5: Run E2E tests**
```bash
npm --prefix frontend run test:e2e
```

### Option 2: Run E2E Tests Against Demo Database

**Pros:**
- Demo database is regularly maintained and seeded
- Already has comprehensive data
- Easy to set up

**Cons:**
- Tests might modify demo data (though they should rollback)
- Not isolated test environment
- Data changes over time

**Steps:**
1. Ensure demo database is seeded: `make init-demo`
2. Generate tags: `python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target demo --clear-existing`
3. Start demo API: `make api-demo`
4. Run E2E tests (they'll use whatever is on port 8001)

### Option 3: Modify E2E Tests to Use Demo Explicitly

Update `playwright.config.ts` to:
```typescript
env: {
  VITE_API_BASE_URL: 'http://127.0.0.1:8001',
  ENV_TARGET: 'local-demo'  // Explicitly use demo
},
```

## Recommendations

### Short Term (Immediate Fix)

1. **Document which database E2E tests should use** in test documentation
2. **Add a make target** for running E2E tests that:
   - Checks if API server is running on port 8001
   - Warns which database it's connected to
   - Optionally seeds test data if needed

3. **Run tests against demo database for now**:
   ```bash
   # Terminal 1: Start demo API
   make api-demo

   # Terminal 2: Ensure demo has data
   python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target demo --clear-existing

   # Terminal 3: Run E2E tests
   npm --prefix frontend run test:e2e
   ```

### Long Term (Proper Solution)

1. **Create test data seeding infrastructure**:
   - Add `make seed-test-data` target that loads TSV files
   - Add `make test-e2e-setup` that does full test database setup
   - Document the complete E2E test setup process

2. **Add database state verification**:
   - E2E test setup script that checks data availability
   - Warns if insufficient data for tests
   - Option to auto-seed if needed

3. **Consider separate API port for test environment**:
   - Test API on port 8099 (already configured but not used)
   - Demo API on port 8001
   - Prevents confusion about which database E2E tests use

4. **Add test data persistence strategy**:
   - Document whether test database should persist between runs
   - Or if it should be recreated fresh each time
   - CI/CD implications

## Missing Pieces

### Need to Find/Create

1. **TSV loading script** for test database
   - Might exist but not documented
   - May need to create one
   - Should load from `test/db/input/rdbms_init/*.tsv`

2. **Make target for full E2E setup**:
   ```makefile
   test-e2e-setup:
       @echo "Setting up E2E test environment..."
       make init-test
       # Load TSV data (script needed)
       python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target test --clear-existing
       @echo "Test database ready for E2E tests"
   ```

3. **Documentation**:
   - Update `docs/testing.md` with E2E database setup
   - Add section to frontend test README
   - Include in CI/CD setup docs

## Current Test Behavior

Tests now **skip gracefully** when data is unavailable:
- ✓ "No gallery results available in test database"
- ✓ "No tags available in test database"
- ✓ "Not enough data for pagination test - need at least 2 pages"
- ✓ "Tag cardinality card not available - may need data"

This is **correct behavior** for real API tests that depend on database state. However, with proper seeding, these tests should **pass** instead of skip.

## Action Items

- [ ] Verify which database is currently being used by E2E tests
- [ ] Find or create TSV data loading script
- [ ] Create `make test-e2e-setup` target
- [ ] Document E2E database requirements in testing.md
- [ ] Decide on test vs demo database for E2E tests
- [ ] Add data verification to E2E test setup
- [ ] Consider separate API port for test environment
- [ ] Update CI/CD to include test database seeding

## Quick Fix for User

**Immediate steps to get E2E tests passing:**

```bash
# 1. Make sure demo database exists and is seeded
make init-demo

# 2. Generate tags from content (this is usually the missing piece!)
python -m genonaut.db.demo.seed_data_gen.seed_tags_from_content --env-target demo --clear-existing

# 3. Start demo API (in background or separate terminal)
make api-demo &

# 4. Wait a few seconds for API to start
sleep 5

# 5. Run E2E tests
npm --prefix frontend run test:e2e
```

If this works, it confirms the issue is missing data, not the test code itself.
