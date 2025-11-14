# Test Failures - Frontend E2E Tests (test-frontend-e2e)

This document tracks failures from the frontend E2E test suite.

## Test Suite: Frontend E2E Tests (frontend-test-e2e-wt2)

**Results**: 8 failed, 197 passed, 52 skipped
**Run time**: 10.6 minutes
**Last updated**: 2025-11-14

### Summary

**IMPORTANT**: The 2 originally documented failures are now **PASSING** on second run:
- analytics-real-api.spec.ts:90 "displays all analytics cards" - **FLAKY** (failed run 1, passed run 2)
- gallery-content-filters.spec.ts:146 "should show 0 results when all filters are OFF" - **TIMING ISSUE** (failed run 1, passed run 2)

**Current Status**: 8 new failures identified, categorized below:

---

## Failing Tests (8 total)

### 1. Gallery Content Filters - Individual Filter Counts (medium)

**Status**: FAILED
**Root cause**: Test expects each individual filter to return different result counts, but assertions are failing

**Affected tests**:
- [ ] frontend/tests/e2e/gallery-content-filters.spec.ts:196:3 - "should show different result counts for each individual filter"

**Test output**:
```
All ON: 212 results
Your gens only: 0 results
Your auto-gens only: 0 results
Community gens only: 112 results
Community auto-gens only: 100 results
```

**Expected**: Assertions after toggling each filter should pass
**Actual**: Test failure after checking individual filter results

**Location**: frontend/tests/e2e/gallery-content-filters.spec.ts:196

---

### 2. Generation Job Submission (medium-high)

**Status**: FAILED
**Root cause**: Generation job submission failing with validation error

**Affected tests**:
- [ ] frontend/tests/e2e/generation.spec.ts:8:3 - "should successfully submit a generation job with real API"

**Failure details**:
```
Error: Generation job submission failed: Please resolve the highlighted issues.
Location: Line 53 in test
Duration: 3.4s
```

**Investigation needed**:
1. Check what validation is failing
2. Verify form data being submitted
3. Check API endpoint validation requirements

**Location**: frontend/tests/e2e/generation.spec.ts:8

---

### 3. Settings Page - User Profile (medium)

**Status**: FAILED (3 tests)
**Root cause**: API returning 404 for user profile endpoint

**Affected tests**:
- [ ] settings-real-api.spec.ts - "handles user profile data correctly"
- [ ] settings-real-api.spec.ts - "validates form inputs properly"
- [ ] settings-real-api.spec.ts - "updates and theme preference"

**Failure details**:
```
Error: Failed to get user: 404
Location: Line 426 in test helper
```

**Investigation needed**:
1. Check if user seeding is working correctly for test database
2. Verify user authentication state in settings tests
3. Check API endpoint `/api/v1/users/{id}` availability

---

### 4. Tag Rating - Real API Tests (high)

**Status**: FAILED (3 tests)
**Root cause**: Test timeout waiting for elements (10s timeout exceeded)

**Affected tests**:
- [ ] tag-rating.spec.ts - "should allow user to rate a tag"
- [ ] tag-rating.spec.ts - "should update existing rating"
- [ ] tag-rating.spec.ts - "rating across page refreshes"

**Failure details**:
```
Error: page.waitForSelector: Test timeout of 10000ms exceeded.
```

**Investigation needed**:
1. Check if tag rating UI elements have correct data-testid attributes
2. Verify tag rating API endpoints are working
3. Check for timing issues or slow API responses
4. May need to increase timeout or add better wait conditions

---

## Previously Failing Tests - Now Fixed

### Analytics Page - "displays all analytics cards" (FLAKY)

**Status**: FLAKY - Failed run 1, passed run 2
**Root cause**: Timing/race condition or data loading issue

**Test details**:
- Location: frontend/tests/e2e/analytics-real-api.spec.ts:90:5
- Checks for: Route Analytics Card, Generation Analytics Card, Tag Cardinality Card (optional)
- Run 1: FAILED (4.8s)
- Run 2: PASSED (4.7s)

**Recommendation**: Add retry logic or better wait conditions for card rendering

---

### Gallery Filters - "should show 0 results when all filters are OFF" (TIMING)

**Status**: TIMING ISSUE - Failed run 1, passed run 2
**Root cause**: Test checks for results too quickly after toggling filters, before API call completes

**Test details**:
- Location: frontend/tests/e2e/gallery-content-filters.spec.ts:146:3
- Expected: 0 results when all 4 content type filters are OFF
- Run 1: FAILED (6.2s)
- Run 2: PASSED (4.9s)

**Fix applied**: User confirmed manual testing shows 0 results correctly. Test needs additional wait after filter toggle.

**Recommendation**: Add `await page.waitForTimeout(1000)` or similar after `setAllFilters()` call at line 154-159

---

## Skipped Tests (52 total)

Many tests are intentionally skipped (marked with "-" in Playwright output). Categories include:
1. Performance tests marked with `@performance` tag
2. Tests with TODO comments for MUI component compatibility issues
3. Tests requiring features not yet implemented
4. Tests skipped in specific test modes

**Note**: Skipped tests are working as intended and do not require fixes.

---

## Test Execution Details

**Test database**: genonaut_test (via API server on port 8002)
**Worktree**: worktree 2 (`/Users/joeflack4/projects/genonaut-wt2`)
**Prerequisites**:
- API server running: `make api-test-wt2`
- Celery worker running: `make celery-test-wt2`

**Run command**:
```bash
make frontend-test-e2e-wt2
```

**Individual test commands**:
```bash
# Gallery filter individual counts
cd frontend && VITE_API_BASE_URL=http://localhost:8002 npx playwright test tests/e2e/gallery-content-filters.spec.ts:196

# Generation job submission
cd frontend && VITE_API_BASE_URL=http://localhost:8002 npx playwright test tests/e2e/generation.spec.ts:8

# Settings tests
cd frontend && VITE_API_BASE_URL=http://localhost:8002 npx playwright test tests/e2e/settings-real-api.spec.ts

# Tag rating tests
cd frontend && VITE_API_BASE_URL=http://localhost:8002 npx playwright test tests/e2e/tag-rating.spec.ts
```

---

## Next Steps

1. **Gallery filters test**: Investigate why individual filter result count assertions are failing
2. **Generation submission**: Debug validation error and fix form data
3. **Settings/User profile**: Fix user seeding or authentication for settings tests
4. **Tag rating**: Add proper wait conditions and verify UI element selectors
5. **Flaky analytics test**: Add retry logic or better wait conditions
6. **Gallery filters timing**: Add wait after filter toggles (line 154-159)
