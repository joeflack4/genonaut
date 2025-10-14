# Frontend E2E Test Categorization

This document categorizes all Playwright E2E tests by whether they are performance-related tests (expecting things to 
happen within specific time constraints) or purely sanity/functionality tests.

## Performance-Related Tests

These tests include explicit time expectations, timeout thresholds, or measure response times:

### 1. **performance.spec.ts** - ENTIRELY PERFORMANCE
- All tests measure performance metrics with explicit thresholds:
  - `generation page load performance` - expects load < 3000ms
  - `generation history component rendering performance` - expects render < 500ms
  - `virtual scrolling performance with large lists` - expects scroll time < 500ms (100ms x 5)
  - `lazy image loading performance` - expects image load < 2000ms
  - `search and filter interaction performance` - expects interaction < 400ms (200ms x 2)
  - `generation form interaction performance` - expects input < 200ms, dropdown < 200ms
  - `pagination performance` - expects navigation < 500ms
  - `generation details modal performance` - expects modal open/close < 200ms
  - `memory usage during component lifecycle` - expects memory increase < 50%
  - `bundle size and loading performance` - expects bundle < 12MB, reasonable load time

### 2. **search-filtering-real-api.spec.ts** - Line 516
- `filter performance with large datasets` - expects filter response time < 5000ms





### 3. **navigation.spec.ts** - Lines 5, 9, 30, 44, 72
- Uses explicit 5000ms timeouts for navigation operations
- While not measuring performance per se, these are timeout constraints

### 4. **generation-oscillation.spec.ts** - Lines 273-274
- `should not oscillate when generating multiple images sequentially` - waits 5000ms to ensure no oscillation occurs
- This is checking that a bug (oscillation) doesn't happen within a time window

### 5. **error-handling.spec.ts** - Line 320
- `handles timeout errors gracefully` - tests timeout warning display after deliberate delay


## Sanity/Functionality Tests

These tests verify correct behavior, UI state, data integrity, and user workflows without time-based assertions:

### Basic Navigation & UI
- **navigation.spec.ts** - All except timeout configs (verifies routes, navigation, keyboard nav)
- **accessibility.spec.ts** - All tests (keyboard nav, focus, ARIA, labels)
- **theme.spec.ts** - All tests (theme toggle and persistence)
- **loading-errors.spec.ts** - All tests (console errors, loading states, error handling, offline)

### Dashboard
- **dashboard.spec.ts** - All tests (displays stats and content)
- **dashboard-interactions.spec.ts** - All tests (view toggles, interactions, grid sizing)
- **dashboard-real-api.spec.ts** - All tests (stats accuracy, content sections, navigation)

### Gallery
- **gallery.spec.ts** - All tests (pagination display, content toggles, totals matching)
- **gallery-interactions.spec.ts** - All tests (view switching, detail views, filters, pagination)
- **gallery-real-api.spec.ts** - All tests (pagination, navigation)
- **gallery-real-api-improved.spec.ts** - All tests (pagination, deep pagination, filtering)
- **gallery-content-filters.spec.ts** - All tests (filter combinations and states)
- **gallery-tag-filters.spec.ts** - All tests (tag display, removal, navigation)
- **gallery-tag-search.spec.ts** - All tests (tag search functionality)

### Generation
- **generation.spec.ts** - All tests (form display, validation, parameters)
- **generation-interactions.spec.ts** - All tests (tab switching, progress display)
- **generation-failure-feedback.spec.ts** - All tests (error message persistence)

### Tags
- **tags-interactions.spec.ts** - All tests (toggle modes, refresh, tree interactions, search)
- **tag-hierarchy.spec.ts** - All tests (tree display, selection, navigation, empty states)
- **tag-hierarchy-debug.spec.ts** - Debug test (network monitoring, not really a test)
- **tag-detail.spec.ts** - All tests (SKIPPED - awaiting backend)
- **tag-rating.spec.ts** - All tests (SKIPPED - awaiting backend)

### Recommendations
- **recommendations-interactions.spec.ts** - All tests (display, marking served, status)
- **recommendations-real-api.spec.ts** - All tests (marking served, display, interactions, state)

### Settings & Auth
- **settings-interactions.spec.ts** - All tests (profile updates, toggles, validation)
- **settings-real-api.spec.ts** - All tests (profile persistence, data loading, validation)
- **auth-real-api.spec.ts** - All tests (redirects, authentication state, logout)

### Content & CRUD
- **content-crud-real-api.spec.ts** - All tests (create, view, edit, delete operations)

### Forms & Input
- **forms.spec.ts** - All tests (focus states, validation, accordions, number inputs)

### Statistics & Data
- **statistics-real-api.spec.ts** - All tests (totals matching, breakdowns, edge cases, number formatting)

### Error Handling
- **error-handling.spec.ts** - All except line 320 (validation, loading states, form preservation, accessibility)


## Ambiguous/Hybrid Tests

These tests have some performance aspects but primarily test functionality:

### 1. **navigation.spec.ts**
**Why ambiguous**: Uses 5000ms timeouts extensively for navigation
- These are protective timeouts (preventing infinite waits) rather than performance assertions
- Not measuring if navigation is "fast enough", just preventing test hangs
- **Lean towards**: SANITY - timeouts are for test stability, not performance requirements

### 2. **generation-oscillation.spec.ts**
**Why ambiguous**: Waits 5000ms to detect oscillation bug
- The 5s wait is checking that a bug (infinite loop) does NOT occur
- It's testing stability over time, not speed
- The bug manifested as rapid oscillations within seconds
- **Lean towards**: SANITY - it's a regression test for a specific bug, time is incidental

### 3. **search-filtering-real-api.spec.ts** - Line 516 test
**Why ambiguous**: Only ONE test in the file measures performance
- `filter performance with large datasets` expects < 5000ms response
- All other tests in the file are pure sanity checks
- **Categorization**: File is MIXED - mostly sanity, one performance test


## Summary Statistics

- **Pure Performance Test Files**: 1 (performance.spec.ts)
- **Pure Sanity Test Files**: 33
- **Mixed Files**: 1 (search-filtering-real-api.spec.ts has 1 perf test among sanity tests)
- **Skipped/Placeholder Files**: 3 (auth.spec.ts, settings.spec.ts, recommendations.spec.ts - empty with comments)

**Total Performance Test Cases**: ~13 tests
**Total Sanity Test Cases**: ~200+ tests (rough estimate based on file contents)

**Ratio**: Approximately 94% sanity tests, 6% performance tests


## Notes

1. **Timeouts vs Performance Tests**:
   - Many tests use `setTimeout` or `waitForTimeout` for synchronization
   - These are NOT performance tests - they're giving the UI time to update
   - Only tests with explicit performance assertions (expect(time).toBeLessThan(X)) count as performance tests

2. **Real API vs Mock Tests**:
   - The use of real API doesn't make a test performance-related
   - Real API tests are primarily for integration/sanity checking
   - Only 1 real API test explicitly measures performance (search-filtering line 516)

3. **Skipped Tests**:
   - Several test files have all tests marked as `.skip()` awaiting implementation
   - These are counted as sanity tests based on their intended purpose

4. **Debug Tests**:
   - `tag-hierarchy-debug.spec.ts` is a diagnostic tool, not a real test
   - Included in sanity category as it verifies page loads without crashing
