# E2E Testing: Network-Aware Wait Pattern

## Problem Statement

E2E tests that interact with UI controls triggering API requests often suffer from flakiness and timeouts when using arbitrary `waitForTimeout()` delays. This is especially problematic when:

- Multiple UI controls are toggled/clicked in rapid succession
- Each action triggers an API request to update data
- Tests need to verify the final state after all actions complete

**Common symptoms:**
- Tests fail intermittently with timeout errors
- Increasing timeout values doesn't solve the root problem
- Tests that pass locally fail in CI/CD
- Same test alternates between passing and failing

## Root Cause Analysis

### Why Arbitrary Timeouts Fail

When multiple UI actions trigger API requests rapidly, modern frontend frameworks (like React Query) optimize network traffic by:

1. **Request Cancellation**: Intermediate API requests are canceled when newer requests supersede them
2. **Request Batching**: Multiple rapid state changes may trigger a single final API request
3. **Debouncing**: Framework may delay API calls until user stops interacting

**Example scenario:**
```typescript
// User toggles 4 filters in rapid succession
await toggle1.click()  // API request #1 started
await toggle2.click()  // API request #1 CANCELED, #2 started
await toggle3.click()  // API request #2 CANCELED, #3 started
await toggle4.click()  // API request #3 CANCELED, #4 started
// Only request #4 actually completes!
```

If your test waits for request #1, #2, or #3 to complete, it will timeout because those requests were canceled.

### The Flawed Pattern (BEFORE)

```typescript
// PROBLEMATIC: Waiting for individual API responses
async function setAllFilters(page, filters) {
  await toggleFilter(page, 'filter1', filters.value1)
  // Wait for THIS specific request - but it might be canceled!
  await page.waitForTimeout(500)  // Arbitrary guess

  await toggleFilter(page, 'filter2', filters.value2)
  await page.waitForTimeout(500)  // Another guess

  await toggleFilter(page, 'filter3', filters.value3)
  await page.waitForTimeout(500)  // Still guessing!

  await toggleFilter(page, 'filter4', filters.value4)
  await page.waitForTimeout(500)  // Final guess
}

// Helper that waits for individual responses
async function toggleFilter(page, name, checked) {
  const toggle = page.getByRole('switch', { name })
  const isChecked = await toggle.isChecked()

  if (isChecked !== checked) {
    // Try to wait for API response
    await performActionAndWaitForApi(
      page,
      async () => await toggle.click(),
      '/api/v1/endpoint'
    )
  }
}
```

**Problems:**
1. Arbitrary `waitForTimeout()` values are unreliable
2. Intermediate API requests may be canceled - wait never completes
3. Tests timeout waiting for responses that will never come
4. Increasing timeout values just makes tests slower without fixing the root issue

## The Solution: Batched API Wait Pattern

### Core Concept

Instead of waiting for each individual action's API response, wait for the **FINAL** API response after **ALL** actions complete.

**Key steps:**
1. **Check** if any actions will trigger state changes (to avoid waiting when nothing will happen)
2. **Set up** API response wait **BEFORE** performing any actions
3. **Perform** ALL actions without individual waits
4. **Wait** for the FINAL API response after all actions complete

### The Correct Pattern (AFTER)

```typescript
// CORRECT: Wait for the final batched API response
async function setAllFilters(page, filters) {
  // 1. Check if ANY filters will actually change state
  const labelMap = {
    'filter1': 'Filter 1',
    'filter2': 'Filter 2',
    'filter3': 'Filter 3',
    'filter4': 'Filter 4'
  }

  const toggle1 = page.getByRole('switch', { name: labelMap['filter1'] })
  const toggle2 = page.getByRole('switch', { name: labelMap['filter2'] })
  const toggle3 = page.getByRole('switch', { name: labelMap['filter3'] })
  const toggle4 = page.getByRole('switch', { name: labelMap['filter4'] })

  const willChange =
    (await toggle1.isChecked()) !== filters.value1 ||
    (await toggle2.isChecked()) !== filters.value2 ||
    (await toggle3.isChecked()) !== filters.value3 ||
    (await toggle4.isChecked()) !== filters.value4

  // 2. Set up API response wait BEFORE any clicks (if changes will occur)
  let responsePromise
  if (willChange) {
    responsePromise = waitForApiResponse(page, '/api/v1/endpoint', { timeout: 30000 })
  }

  // 3. Perform ALL clicks without individual waits
  await toggleFilterNoWait(page, 'filter1', filters.value1)
  await toggleFilterNoWait(page, 'filter2', filters.value2)
  await toggleFilterNoWait(page, 'filter3', filters.value3)
  await toggleFilterNoWait(page, 'filter4', filters.value4)

  // 4. Wait for the FINAL API response after all clicks
  if (willChange && responsePromise) {
    await responsePromise
  }
}

// Helper that does NOT wait for API response
async function toggleFilterNoWait(page, filterName, checked) {
  const labelMap = { /* ... */ }
  const label = labelMap[filterName]
  const toggle = page.getByRole('switch', { name: label })

  const isChecked = await toggle.isChecked()
  if (isChecked !== checked) {
    await toggle.click()  // Just click, don't wait
  } else {
    console.log(`Filter ${filterName} already ${checked ? 'ON' : 'OFF'}, skipping`)
  }
}
```

**Benefits:**
1. No arbitrary timeouts - waits for actual network activity
2. Handles request cancellation/batching correctly
3. Only waits when state actually changes (performance optimization)
4. Tests run faster and more reliably

## When to Use This Pattern

### Ideal Use Cases

Use the Batched API Wait Pattern when:

1. **Multiple rapid actions** - Toggling multiple switches, clicking multiple buttons in sequence
2. **Each action triggers API** - Each UI interaction makes a network request
3. **Single endpoint** - All actions hit the same API endpoint
4. **Final state matters** - You care about the end result, not intermediate states

### Example Scenarios

**Good candidates:**
- Setting multiple filter toggles (gallery filters, search filters)
- Rapid-fire form field updates (settings forms, preferences)
- Batch operations (selecting multiple items, bulk actions)
- Sequential navigation steps (multi-step forms, wizards)

**Not suitable for:**
- Single isolated actions (one button click, one toggle)
- Different API endpoints for each action
- Actions with side effects you need to verify individually
- Situations where intermediate states must be validated

## Implementation Guide

### Step 1: Add Network-Aware Helpers

Ensure your test utilities include these helpers (see `frontend/tests/e2e/utils/realApiHelpers.ts`):

```typescript
/**
 * Wait for a specific API endpoint to respond
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  options: {
    method?: string
    status?: number
    timeout?: number
  } = {}
): Promise<any> {
  const { method, status = 200, timeout = 30000 } = options

  const pattern = typeof urlPattern === 'string'
    ? (url: string) => url.includes(urlPattern)
    : (url: string) => urlPattern.test(url)

  return page.waitForResponse(
    response => {
      const matchesUrl = pattern(response.url())
      const matchesMethod = !method || response.request().method() === method
      const matchesStatus = response.status() === status
      return matchesUrl && matchesMethod && matchesStatus
    },
    { timeout }
  )
}

/**
 * Execute an action and wait for the resulting API call to complete
 * Use this for SINGLE actions, not batched operations
 */
export async function performActionAndWaitForApi(
  page: Page,
  action: () => Promise<void>,
  urlPattern: string | RegExp,
  options: {
    method?: string
    status?: number
    timeout?: number
  } = {}
): Promise<void> {
  const responsePromise = waitForApiResponse(page, urlPattern, options)
  await action()
  await responsePromise
}
```

### Step 2: Identify the API Endpoint

Use browser DevTools Network tab to identify which API endpoint is called:

1. Open your app in a browser
2. Open DevTools > Network tab
3. Perform the actions you want to test
4. Note the API endpoint URL pattern (e.g., `/api/v1/content/unified`, `/api/v1/users/profile`)

### Step 3: Refactor Your Test

Apply the pattern following the template above:

1. Check if any actions will change state
2. Set up response wait BEFORE actions
3. Perform all actions
4. Wait for final response

### Step 4: Test and Validate

Run your test multiple times to ensure it's stable:

```bash
# Run the test 10 times to check for flakiness
for i in {1..10}; do
  echo "Run $i:"
  npx playwright test path/to/test.spec.ts
done
```

## Real-World Example: Gallery Filters

**Context:** Gallery page with 4 content type filter toggles. Each toggle triggers an API call to `/api/v1/content/unified` to fetch filtered results.

### Before (FLAKY - 0/3 tests passing)

```typescript
async function setAllFilters(page, filters) {
  const optionsDrawer = page.locator('[data-testid="gallery-options-drawer"]')
  // ... drawer opening logic ...

  // Toggle each filter with individual waits
  await toggleFilter(page, 'your-gens', filters.yourGens)
  await toggleFilter(page, 'your-autogens', filters.yourAutoGens)
  await toggleFilter(page, 'community-gens', filters.communityGens)
  await toggleFilter(page, 'community-autogens', filters.communityAutoGens)

  // Arbitrary timeout hoping all requests finished
  await page.waitForTimeout(500)  // PROBLEMATIC!
}

async function toggleFilter(page, filterName, checked) {
  const toggle = page.getByRole('switch', { name: labelMap[filterName] })
  const isChecked = await toggle.isChecked()

  if (isChecked !== checked) {
    // Wait for THIS request - but it might get canceled!
    await performActionAndWaitForApi(
      page,
      async () => await toggle.click(),
      '/api/v1/content/unified'
    )  // TIMEOUT! Request was canceled by next toggle
  }
}
```

**Result:** Tests timeout after 30s waiting for canceled API requests.

### After (STABLE - 7/7 tests passing in 32.7s)

```typescript
async function setAllFilters(page, filters) {
  const optionsDrawer = page.locator('[data-testid="gallery-options-drawer"]')
  // ... drawer opening logic ...

  // 1. Check if ANY toggles will actually change state
  const yourGensToggle = page.getByRole('switch', { name: 'Your gens' })
  const yourAutoGensToggle = page.getByRole('switch', { name: 'Your auto-gens' })
  const communityGensToggle = page.getByRole('switch', { name: 'Community gens' })
  const communityAutoGensToggle = page.getByRole('switch', { name: 'Community auto-gens' })

  const willChange =
    (await yourGensToggle.isChecked()) !== filters.yourGens ||
    (await yourAutoGensToggle.isChecked()) !== filters.yourAutoGens ||
    (await communityGensToggle.isChecked()) !== filters.communityGens ||
    (await communityAutoGensToggle.isChecked()) !== filters.communityAutoGens

  // 2. Set up API response wait BEFORE toggling (if any will change)
  let responsePromise
  if (willChange) {
    responsePromise = waitForApiResponse(page, '/api/v1/content/unified', { timeout: 30000 })
  }

  // 3. Toggle each filter WITHOUT waiting for individual responses
  await toggleFilterNoWait(page, 'your-gens', filters.yourGens)
  await toggleFilterNoWait(page, 'your-autogens', filters.yourAutoGens)
  await toggleFilterNoWait(page, 'community-gens', filters.communityGens)
  await toggleFilterNoWait(page, 'community-autogens', filters.communityAutoGens)

  // 4. Wait for the FINAL API response after all toggles
  if (willChange && responsePromise) {
    await responsePromise
  }
}

async function toggleFilterNoWait(page, filterName, checked) {
  const labelMap = {
    'your-gens': 'Your gens',
    'your-autogens': 'Your auto-gens',
    'community-gens': 'Community gens',
    'community-autogens': 'Community auto-gens'
  }

  const label = labelMap[filterName]
  const toggle = page.getByRole('switch', { name: label })

  const isChecked = await toggle.isChecked()
  if (isChecked !== checked) {
    await toggle.click()  // Just click, don't wait
  } else {
    console.log(`Filter ${filterName} already ${checked ? 'ON' : 'OFF'}, skipping`)
  }
}
```

**Result:** All 7 tests pass consistently. Tests complete 3x faster.

## Troubleshooting

### Test still times out

**Check:**
1. Is the API endpoint pattern correct? Use DevTools Network tab to verify.
2. Are there intermediate redirects? Some frameworks redirect before the final API call.
3. Is the response status code what you expect? Default is 200, but some APIs return 201 or 204.

**Solutions:**
- Adjust the `urlPattern` to be more specific or use a RegExp
- Increase timeout: `{ timeout: 60000 }` for slow APIs
- Specify expected method: `{ method: 'POST' }` if not GET
- Check response status: `{ status: 201 }` for created resources

### Test passes but is slow

**Check:**
1. Are you checking state changes before setting up the wait? (Optimization)
2. Are you using the right timeout value?

**Solutions:**
- Always check `if (willChange)` before setting up wait
- Use shorter timeouts for fast APIs: `{ timeout: 10000 }`
- Profile with `console.time()` to identify slow operations

### Test fails with "no such element"

**Check:**
1. Did you wait for the page to load before interacting?
2. Are you using correct selectors?

**Solutions:**
- Use `waitForPageLoad()` helper before test logic
- Verify selectors with `page.locator().first().waitFor()`
- Check `data-testid` attributes are present in the DOM

## Related Patterns

### Single Action Pattern

For single isolated actions, use `performActionAndWaitForApi()`:

```typescript
// Single button click that triggers API
await performActionAndWaitForApi(
  page,
  async () => await saveButton.click(),
  '/api/v1/save',
  { method: 'POST', status: 201 }
)
```

### Form Submission Pattern

For form submissions, wait for the submission API response:

```typescript
const responsePromise = waitForApiResponse(page, '/api/v1/forms/submit', {
  method: 'POST',
  status: 201
})

await page.fill('[name="email"]', 'test@example.com')
await page.fill('[name="password"]', 'password123')
await submitButton.click()

await responsePromise
```

### Navigation Pattern

For navigation with API calls on new page:

```typescript
const responsePromise = waitForApiResponse(page, '/api/v1/dashboard')
await page.goto('/dashboard')
await responsePromise
```

## References

- Playwright `waitForResponse()` documentation: https://playwright.dev/docs/api/class-page#page-wait-for-response
- Real-world implementation: `frontend/tests/e2e/gallery-content-filters.spec.ts`
- Helper utilities: `frontend/tests/e2e/utils/realApiHelpers.ts`
- Test failure analysis: `notes/test-fails-4-test-frontend-e2e.md`
