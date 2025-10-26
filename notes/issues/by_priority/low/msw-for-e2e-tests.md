# MSW (Mock Service Worker) for E2E Tests

## Overview

Mock Service Worker (MSW) is a library that intercepts network requests at the network level and returns mock responses. Unlike traditional mocking approaches that stub API client functions, MSW works by registering a Service Worker (in browsers) or intercepting Node.js http/https modules, making it transparent to the application code.

**Key Benefit:** E2E tests can verify complete user workflows and frontend behavior without depending on real backend API timing, state, or availability.

## How MSW Works

MSW intercepts HTTP requests before they reach the network:

```
Your Test → Browser/Node → [MSW Intercepts] → Mock Response
                              ↓
                           (Real network call never happens)
```

The application code and React Query hooks work exactly as they would with a real API - they just receive instant, predictable responses instead of waiting for actual backend processing.

## When to Use MSW vs Real API

### Use MSW for E2E Tests When:

1. **Testing UI behavior and user workflows** - Not testing API correctness
2. **Need predictable timing** - Async operations complete instantly
3. **Need specific edge cases** - Easy to simulate errors, empty states, large datasets
4. **Tests are flaky due to timing** - React Query + slow API responses cause timeouts
5. **Want isolated frontend testing** - Backend doesn't need to be running
6. **Testing loading/error states** - Can delay responses or return errors on demand

### Use Real API for E2E Tests When:

1. **Integration testing** - Verifying frontend + backend work together correctly
2. **Testing real data flows** - Database → API → Frontend
3. **Performance testing** - Measuring actual response times
4. **End-to-end validation** - Smoke tests before deployment
5. **Backend has complex logic** - Need to verify real backend behavior affects frontend correctly

### Hybrid Approach (Recommended):

- **MSW tests (majority):** Fast, reliable tests for all UI interactions and workflows
- **Real API tests (subset):** Small number of critical path integration tests
- **Manual testing:** Final verification before releases

**Ratio suggestion:** 80% MSW tests, 15% Real API tests, 5% manual verification

## How MSW Would Solve the Analytics Test Failures

### Problem: Analytics Tests Timing Out

The 6 skipped analytics tests failed because:
1. React Query data loading takes unpredictable time (3-18+ seconds)
2. MUI Select menus render options asynchronously
3. Generation analytics has cascading query dependencies
4. No way to know when data is "ready" for interaction

### MSW Solution: Instant, Predictable Responses

```typescript
// tests/e2e/setup/msw-handlers.ts
import { http, HttpResponse } from 'msw'

export const analyticsHandlers = [
  // Route analytics - returns instantly
  http.get('/api/v1/analytics/routes', () => {
    return HttpResponse.json({
      routes: [
        { route: '/api/v1/content', total_queries: 1000, avg_response_ms: 150 },
        { route: '/api/v1/tags', total_queries: 500, avg_response_ms: 80 },
      ]
    })
  }),

  // Generation analytics - returns instantly
  http.get('/api/v1/analytics/generation', () => {
    return HttpResponse.json({
      total_generations: 42,
      success_rate: 0.95,
      avg_duration_seconds: 12.5,
      unique_users: 8
    })
  }),

  // Can simulate loading delay if needed
  http.get('/api/v1/analytics/slow-endpoint', async () => {
    await delay(2000) // Simulate 2s delay
    return HttpResponse.json({ data: 'loaded' })
  }),

  // Can simulate errors
  http.get('/api/v1/analytics/error-endpoint', () => {
    return HttpResponse.json(
      { error: 'Service unavailable' },
      { status: 503 }
    )
  })
]
```

```typescript
// tests/e2e/analytics-real-api.spec.ts (converted to MSW)
import { test, expect } from '@playwright/test'
import { setupMSW } from './setup/msw-setup'

test.describe('Analytics Page (MSW)', () => {
  setupMSW() // Enables MSW for all tests in this describe block

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings/analytics')
    // No need for long waits - data loads instantly!
    // waitForPageLoad is enough
  })

  test('changes time range filter', async ({ page }) => {
    // Open select - works immediately because data is already loaded
    await page.getByTestId('route-analytics-days-select').locator('..').click()

    // Click option - works immediately, no timeout needed
    await page.getByRole('option', { name: /last 7 days/i }).click()

    // Verify - data updates instantly
    const selectParent = page.getByTestId('route-analytics-days-select').locator('..')
    await expect(selectParent).toContainText('Last 7 Days')
  })

  test('displays generation metrics', async ({ page }) => {
    // All elements render immediately with mock data
    await expect(page.getByTestId('generation-analytics-stats')).toBeVisible()
    await expect(page.getByTestId('gen-stat-total-generations')).toContainText('42')
    await expect(page.getByTestId('gen-stat-success-rate')).toContainText('95.0%')
  })
})
```

**What Changed:**
- No long timeouts needed (3s, 10s, 15s) - everything is instant
- No unpredictable timing - MSW responses are synchronous
- Tests run 10-20x faster (seconds instead of minutes)
- 100% reliable - no flaky failures from timing issues

### Why This Works

1. **React Query receives data immediately** - No waiting for backend processing
2. **Components render without delays** - All data available synchronously
3. **MUI Select menus work reliably** - Data already loaded when menu opens
4. **No cascading query dependencies** - All queries resolve instantly in parallel

## Applicability to Other E2E Tests

### Currently Skipped Tests That Would Benefit

#### 1. Gallery Pagination Tests (Already Skipped)
**Reference:** `notes/issues/groupings/tests/tests-skipped-troublesome-patterns.md`

**Current Problem:**
- Mock API patterns don't match correctly
- Complex URL query parameters (`?page=1&page_size=10&content_types=regular,auto&...`)
- React Query caching interferes with pagination state

**MSW Solution:**
```typescript
http.get('/api/v1/content/unified', ({ request }) => {
  const url = new URL(request.url)
  const page = parseInt(url.searchParams.get('page') || '1')
  const pageSize = parseInt(url.searchParams.get('page_size') || '10')

  return HttpResponse.json({
    items: generateMockItems(page, pageSize),
    pagination: {
      page,
      page_size: pageSize,
      total_count: 10000,
      total_pages: 1000
    }
  })
})
```

**Benefits:**
- Pattern matching is simple and explicit
- Can generate any page of data instantly
- No React Query caching issues (fresh responses each time)
- Can test deep pagination (page 50000) without performance impact

#### 2. Tag Rating Tests
**Reference:** `frontend/tests/e2e/tag-rating.spec.ts`

**How MSW Helps:**
```typescript
http.post('/api/v1/tags/:tagId/rating', async ({ request, params }) => {
  const body = await request.json()
  return HttpResponse.json({
    tag_id: params.tagId,
    rating: body.rating,
    user_id: 'test-user-123'
  })
})
```

**Benefits:**
- Instant rating updates (no waiting for DB write)
- Can test optimistic UI updates
- Can simulate rating conflicts or errors
- No need for admin user in test database

#### 3. Image View Navigation
**Reference:** `notes/issues/groupings/tests/tests-skipped-troublesome-patterns.md`

**Current Problem:**
- Navigation between images flaky
- Tag chip clicks don't trigger navigation reliably

**MSW Solution:**
- Mock image data with predictable IDs and tag relationships
- Navigation works instantly without waiting for API
- Can test edge cases (last image, first image, no tags)

### Future Tests That Should Use MSW

#### 1. Generation Job Workflow Tests
```typescript
http.post('/api/v1/generation/jobs', () => {
  return HttpResponse.json({
    job_id: 'job-123',
    status: 'queued'
  })
})

http.get('/api/v1/generation/jobs/:jobId', ({ params }) => {
  // Can simulate job progression
  return HttpResponse.json({
    job_id: params.jobId,
    status: 'completed',
    result_url: '/api/v1/content/456'
  })
})
```

**Benefits:**
- No need to wait for actual Celery job processing
- Can test job status transitions instantly
- Can simulate errors, cancellations, timeouts
- Tests run in seconds instead of minutes

#### 2. Recommendation System Tests
```typescript
http.get('/api/v1/recommendations', () => {
  return HttpResponse.json({
    recommendations: generateMockRecommendations(10),
    algorithm: 'collaborative_filtering',
    confidence: 0.87
  })
})
```

**Benefits:**
- No need for complex recommendation algorithm setup
- Can test different recommendation scenarios
- Can test empty recommendations, low confidence, etc.

#### 3. Search and Filtering Tests
```typescript
http.get('/api/v1/content/search', ({ request }) => {
  const url = new URL(request.url)
  const query = url.searchParams.get('q')

  return HttpResponse.json({
    results: mockSearchResults.filter(item =>
      item.title.includes(query)
    ),
    facets: { /* ... */ }
  })
})
```

**Benefits:**
- Instant search results
- Can test complex filter combinations
- Can simulate slow searches or no results
- No Elasticsearch/database needed

## Implementation Approach

### Phase 1: Convert Failing Analytics Tests (Immediate)

1. Install MSW: `npm install -D msw@latest`
2. Create MSW setup file: `frontend/tests/e2e/setup/msw-setup.ts`
3. Create analytics handlers: `frontend/tests/e2e/setup/handlers/analytics.ts`
4. Convert 6 skipped analytics tests to use MSW
5. Verify all tests pass reliably

**Estimated Effort:** 4-6 hours

### Phase 2: Convert Existing Flaky Tests (Short-term)

1. Convert gallery pagination tests to MSW
2. Convert image view navigation tests to MSW
3. Keep a small subset of "real API" integration tests

**Estimated Effort:** 8-12 hours

### Phase 3: MSW as Default for New Tests (Long-term)

1. Document MSW patterns in `docs/testing.md`
2. Create reusable handler generators
3. Build mock data fixtures library
4. Make MSW the default for all new E2E tests

**Estimated Effort:** Ongoing as new tests are added

## Comparison: MSW vs Other Approaches

| Approach | Speed | Reliability | Setup Complexity | Integration Testing |
|----------|-------|-------------|------------------|---------------------|
| Real API | Slow (minutes) | Flaky (timing) | Low | Excellent |
| MSW (Playwright) | Fast (seconds) | Very Reliable | Medium | None |
| Component Tests (Vitest) | Very Fast (ms) | Excellent | Low | None |
| Mock API Patterns (Current) | Fast | Poor (pattern matching) | High | None |

**Recommendation:** Use MSW for most E2E tests, keep 10-15% Real API tests for critical integration paths.

## Example: Complete MSW Setup for Playwright

```typescript
// tests/e2e/setup/msw-setup.ts
import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export function setupMSW() {
  let worker: ReturnType<typeof setupWorker>

  test.beforeAll(async ({ page }) => {
    // Initialize MSW in the browser context
    await page.addInitScript(() => {
      // MSW setup code injected into page
    })

    worker = setupWorker(...handlers)
    await worker.start({ onUnhandledRequest: 'bypass' })
  })

  test.afterAll(async () => {
    await worker.stop()
  })

  test.afterEach(async () => {
    worker.resetHandlers()
  })
}
```

```typescript
// tests/e2e/setup/handlers/index.ts
import { analyticsHandlers } from './analytics'
import { contentHandlers } from './content'
import { tagHandlers } from './tags'

export const handlers = [
  ...analyticsHandlers,
  ...contentHandlers,
  ...tagHandlers,
]
```

## Conclusion

MSW is **highly recommended** for most E2E tests in this project because:

1. **Solves Current Problems:** Would have prevented all 6 analytics test failures
2. **Improves Speed:** 10-20x faster tests (seconds vs minutes)
3. **Increases Reliability:** Eliminates timing-based flakes
4. **Better Developer Experience:** Tests run locally without backend setup
5. **Enables Edge Case Testing:** Easy to test errors, empty states, large datasets
6. **Still Tests Real Behavior:** User interactions and UI logic are tested authentically

**Recommendation:** Start with Phase 1 (convert analytics tests) to prove value, then expand to Phase 2 and 3.

**See Also:**
- MSW Documentation: https://mswjs.io/
- Playwright + MSW Guide: https://mswjs.io/docs/integrations/browser
- Related Issues: `notes/issues/groupings/tests/tests.md` (Analytics E2E Tests section)
