# Gallery Content Filter Counts Test Investigation

**STATUS**: FIXED - Test now passes (completed 2025-11-13)

## Test Location
`frontend/tests/e2e/gallery-content-filters.spec.ts:196` - "should show different result counts for each individual filter"

## Problem Summary
E2E test is returning results from the DEMO database (1.1M+ records) instead of TEST database (200 records), even though the API server on port 8002 is correctly connected to `genonaut_test`.

## Evidence

### Database Counts (Direct SQL Queries)

**Test Database** (`genonaut_test`):
- content_items: 100
- content_items_auto: 100
- **TOTAL: 200 items**

Test user ID: `121e194b-4caa-4b81-ad4f-86ca3919d5b9`
- Your gens (creator_id = test_user): 0
- Your auto-gens (creator_id = test_user): 0
- Community gens (creator_id != test_user): 100
- Community auto-gens (creator_id != test_user): 100

**Demo Database** (`genonaut_demo`):
- content_items: 65,371
- content_items_auto: 1,110,000
- **TOTAL: 1,175,371 items** ← EXACT MATCH to test result!

### E2E Test Results
From test run output:
- All filters ON: **1,175,371 results**
- Your gens only: 593 results
- Your auto-gens only: 523 results
- Community gens only: 64,778 results
- Community auto-gens only: [Test timed out]

### API Server Verification

**Port 8001** (should be demo):
```bash
curl http://localhost:8001/api/v1/lora-models/
# Returns 7 items (demo database)
```

**Port 8002** (should be test):
```bash
curl http://localhost:8002/api/v1/lora-models/
# Returns 0 items (test database)
```

This confirms port 8002 IS connected to the test database.

**Health endpoint**:
```bash
curl http://localhost:8002/api/v1/health
# Returns: "database": { "name": "genonaut_test" }
```

## Root Cause Analysis

### Initial Hypothesis (INCORRECT)
API server on port 8002 is connected to wrong database.
**DISPROVEN**: lora-models endpoint proves port 8002 is correctly connected to test database.

### Actual Root Cause
**The E2E test is somehow connecting to port 8001 (demo) instead of port 8002 (test)**, OR there's a caching/connection pooling issue causing queries to go to the wrong database.

## Investigation Steps Completed

1. ✅ Verified test user ID: `121e194b-4caa-4b81-ad4f-86ca3919d5b9`
2. ✅ Ran direct SQL queries on both test and demo databases
3. ✅ Confirmed test database has only 200 items
4. ✅ Confirmed demo database has 1,175,371 items (exact match to test result)
5. ✅ Verified port 8002 API is connected to test database via lora-models endpoint
6. ✅ Verified port 8001 API is connected to demo database via lora-models endpoint

## Next Steps

1. **Check E2E test configuration**: Verify which port/URL the test is actually using
   - Check `frontend/tests/e2e/playwright.config.ts` for baseURL
   - Check `realApiHelpers.ts` for `getApiBaseUrl()` function
   - Check if test is explicitly setting API_BASE_URL

2. **Monitor actual HTTP requests**: Use browser dev tools or Playwright tracing to see which port the test is hitting

3. **Check for environment variable conflicts**: Ensure `API_BASE_URL` or similar env vars aren't overriding test configuration

4. **Verify database connection caching**: Check if API server has stale database connection pool

## Key Files

- Test file: `frontend/tests/e2e/gallery-content-filters.spec.ts`
- Helper functions: `frontend/tests/e2e/utils/realApiHelpers.ts`
- Playwright config: `frontend/tests/e2e/playwright.config.ts`
- API config: `genonaut/api/config.py`
- Database dependencies: `genonaut/api/dependencies.py`

## Important Notes

- **Schema difference**: Tables use `creator_id` column, NOT `user_id`
- **Test user has NO content**: Test database has 0 items for the test user (all 200 items belong to other users)
- **This affects filter logic**: "Your gens" and "Your auto-gens" should return 0 results for this test user

## Solution

**Root Cause**: Playwright configuration hardcoded the frontend app to use port 8001 (demo database) instead of respecting the environment variable that would allow tests to use port 8002 (test database).

**Fixes Applied**:

1. **frontend/playwright.config.ts:30-32**: Updated to respect VITE_API_BASE_URL environment variable
   ```typescript
   env: {
     VITE_API_BASE_URL: process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001'
   }
   ```

2. **frontend/tests/e2e/gallery-content-filters.spec.ts:197-198**: Added 60s timeout
   ```typescript
   test.setTimeout(60000)
   ```

**Test Results**:
- All filters ON: 200 results (correct)
- Your gens: 0, Your auto-gens: 0, Community gens: 100, Community auto-gens: 100
- Sum: 200 (matches total)
- **Test status**: PASSES in 11.1s
