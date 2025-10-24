# Gallery URL Sync Race Condition Analysis

## Problem Statement

When users quickly toggle multiple content filters in the gallery (e.g., clicking "Your gens" followed quickly by "Your auto-gens"), the first toggle re-enables itself incorrectly. This is a race condition in the bidirectional URL synchronization logic.

**Reproduction**: E2E test `gallery-url-params.spec.ts:416` - "updates URL with multiple disabled sources"

**Observable behavior**:
1. User clicks "Your gens" toggle -> unchecks successfully
2. User clicks "Your auto-gens" toggle within ~300ms -> "Your gens" re-checks itself (bug!)

## Current Implementation Overview

The gallery uses bidirectional URL synchronization with these mechanisms:

### Race Prevention Mechanisms (lines 162-168)
```typescript
const isInitializedRef = useRef(false)           // Skip first render
const pendingUrlUpdatesRef = useRef(0)           // Track pending updates
const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
const isProgrammaticUrlUpdateRef = useRef(false) // Block "Sync FROM URL" during updates
```

### Two-Way Sync Pattern

**1. Sync FROM URL** (lines 316-352) - Browser back/forward navigation
- Triggered when `searchParams` changes
- Skips if not initialized or `isProgrammaticUrlUpdateRef` is true
- Reads URL and updates `contentToggles` state

**2. Sync TO URL** (lines 354-431) - User interactions
- Triggered when `contentToggles` state changes
- Uses adaptive debouncing:
  - **0ms** (immediate) if `pendingUrlUpdatesRef.current === 0`
  - **150ms** if `pendingUrlUpdatesRef.current > 0`
- Sets `isProgrammaticUrlUpdateRef = true` during update
- Clears flag after **300ms** via setTimeout

## Root Cause Analysis

### Timeline of the Bug

```
t=0ms:    User clicks toggle 1 ("Your gens")
          - contentToggles.yourGens = false
          - "Sync TO URL" effect fires
          - pendingUrlUpdatesRef = 1
          - performUrlUpdate() executes immediately (no debounce)
          - isProgrammaticUrlUpdateRef = true
          - setSearchParams() queued
          - setTimeout(300ms) to clear flags

t=1ms:    React Router processes URL update
          - searchParams changes to include notGenSource=your-g
          - "Sync FROM URL" effect queued
          - isProgrammaticUrlUpdateRef is true -> effect returns early ✓

t=50ms:   User clicks toggle 2 ("Your auto-gens") [BEFORE 300ms timeout!]
          - contentToggles.yourAutoGens = false
          - "Sync TO URL" effect fires
          - pendingUrlUpdatesRef = 1 (hasn't decremented yet!)
          - shouldDebounce = true
          - pendingUrlUpdatesRef = 2
          - debounceTimerRef set for 150ms
          - setTimeout(300ms) to clear flags (SECOND timeout)

t=200ms:  Debounced performUrlUpdate() executes (150ms after t=50)
          - isProgrammaticUrlUpdateRef = true (set again)
          - setSearchParams() queued with both changes
          - setTimeout(300ms) to clear flags (THIRD timeout)

t=300ms:  FIRST setTimeout fires ⚠️
          - isProgrammaticUrlUpdateRef = false
          - pendingUrlUpdatesRef = 1

t=301ms:  React Router processes URL update from t=200
          - searchParams changes
          - "Sync FROM URL" effect queued
          - isProgrammaticUrlUpdateRef is FALSE! ❌
          - Effect RUNS and reads URL
          - URL might have stale data OR
          - URL update timing causes effect to read intermediate state
          - Effect overwrites contentToggles, re-enabling first toggle!
```

### The Critical Flaw

**Line 407-410**: The setTimeout always fires after 300ms, regardless of whether there are still pending updates being processed.

```typescript
setTimeout(() => {
  isProgrammaticUrlUpdateRef.current = false
  pendingUrlUpdatesRef.current = Math.max(0, pendingUrlUpdatesRef.current - 1)
}, 300)
```

This creates a window where:
- `isProgrammaticUrlUpdateRef` is cleared while URL updates are still propagating through React Router
- "Sync FROM URL" effect runs with the flag disabled
- State gets overwritten with stale or intermediate URL data

## Why Existing Mechanisms Don't Work

### Issue (a): Implementation Bug - Flag Cleared Too Early

The `pendingUrlUpdatesRef` counter exists but is NOT checked before clearing `isProgrammaticUrlUpdateRef`. Each click schedules its own independent 300ms timeout that clears the flag, regardless of whether other updates are pending.

**Evidence**: The counter is decremented but never checked:
```typescript
pendingUrlUpdatesRef.current = Math.max(0, pendingUrlUpdatesRef.current - 1)
```

### Issue (b): Timing is Insufficient

300ms assumes React Router will process the URL update within that window, but:
- React Router batches updates
- Multiple rapid state changes can extend processing time
- Browser/system performance varies
- The debounced second update (150ms) plus React processing can exceed 300ms

### Issue (c): Not Applied Consistently

The flag clearing logic doesn't account for:
- Multiple pending updates (each sets its own timeout)
- Debounced updates that execute later
- React Router's asynchronous update processing

### Issue (d): Architectural - Bidirectional Sync is Fragile

The fundamental problem is maintaining two sources of truth (state and URL) that must stay synchronized. This pattern is inherently race-prone with async updates.

## Recommendations

### Option 1: Fix Flag Management (Quick Fix) ⭐

**Difficulty**: Easy
**Risk**: Low
**Completeness**: Partial (fixes immediate issue but doesn't prevent future similar bugs)

Change the flag clearing logic to only clear when ALL pending updates are processed:

```typescript
setTimeout(() => {
  pendingUrlUpdatesRef.current = Math.max(0, pendingUrlUpdatesRef.current - 1)

  // Only clear flag when no more pending updates
  if (pendingUrlUpdatesRef.current === 0) {
    isProgrammaticUrlUpdateRef.current = false
  }
}, 300)
```

**Pros**:
- Minimal code change
- Preserves existing architecture
- Likely fixes the immediate issue

**Cons**:
- Still relies on 300ms timeout assumption
- Doesn't eliminate race conditions, just reduces window
- Fragile if new interactions are added

---

### Option 2: Increase Timeout + Fix Flag (Conservative) ⭐⭐

**Difficulty**: Easy
**Risk**: Very Low
**Completeness**: Partial

Combine Option 1 with increased timeout:

```typescript
setTimeout(() => {
  pendingUrlUpdatesRef.current = Math.max(0, pendingUrlUpdatesRef.current - 1)

  if (pendingUrlUpdatesRef.current === 0) {
    isProgrammaticUrlUpdateRef.current = false
  }
}, 500)  // Increased from 300ms
```

**Pros**:
- More safety margin for slow systems/React batching
- Very safe change
- Fixes immediate issue

**Cons**:
- URL might be briefly out of sync for longer
- Still fundamentally fragile
- Doesn't scale if more rapid interactions are added

---

### Option 3: Single Source of Truth - URL as Source (Recommended) ⭐⭐⭐

**Difficulty**: Medium
**Risk**: Medium
**Completeness**: Complete

Remove bidirectional sync. Make URL the single source of truth:

1. **User clicks toggle** -> Update URL only via `setSearchParams()`
2. **Single effect**: Sync state FROM URL
3. **Remove**: "Sync TO URL" effect and all flag management

```typescript
// Remove all these refs:
// - isProgrammaticUrlUpdateRef
// - pendingUrlUpdatesRef
// - debounceTimerRef

// Keep only one sync direction:
useEffect(() => {
  const notGenSource = searchParams.get('notGenSource')
  const disabledSources = notGenSource ? notGenSource.split(',') : []

  setContentToggles({
    yourGens: !disabledSources.includes('your-g'),
    yourAutoGens: !disabledSources.includes('your-ag'),
    communityGens: !disabledSources.includes('comm-g'),
    communityAutoGens: !disabledSources.includes('comm-ag'),
  })
}, [searchParams])

// User interactions update URL directly:
const handleToggleChange = (toggleKey: keyof ContentToggles) => () => {
  setSearchParams((params) => {
    // Build new notGenSource from current toggles + change
    // ...
  })
}
```

**Pros**:
- Eliminates race conditions entirely
- Simpler mental model
- React Router handles all batching/timing
- URL is always correct (shareable, bookmark-able)
- Easier to debug and maintain

**Cons**:
- Requires refactoring handler logic
- Need to compute new URL state from current state + change
- More code changes required
- Need thorough testing

---

### Option 4: Debounce All Toggles Together (Hybrid)

**Difficulty**: Medium
**Risk**: Medium
**Completeness**: Moderate

Add a shared debounce for all toggle changes:

```typescript
const toggleDebounceRef = useRef<NodeJS.Timeout | null>(null)

const handleToggleChange = (toggleKey: keyof ContentToggles) => (event) => {
  const checked = event.target.checked

  // Update state immediately for UI responsiveness
  setContentToggles((prev) => ({ ...prev, [toggleKey]: checked }))

  // Debounce the URL update by 200ms
  if (toggleDebounceRef.current) {
    clearTimeout(toggleDebounceRef.current)
  }

  toggleDebounceRef.current = setTimeout(() => {
    // Sync to URL happens here via existing effect
    // Or call URL update directly
  }, 200)
}
```

**Pros**:
- UI feels responsive (immediate toggle)
- URL updates are batched
- Reduces number of URL updates

**Cons**:
- URL temporarily out of sync with UI
- Complex: debounce in handler + effect debounce
- Doesn't fully eliminate race conditions

---

### Option 5: Use URL State Library (Future-Proof)

**Difficulty**: Hard
**Risk**: High (significant refactor)
**Completeness**: Complete

Use a library like `nuqs` or `use-query-params` designed for URL state management:

```typescript
import { useQueryState } from 'nuqs'

const [notGenSource, setNotGenSource] = useQueryState('notGenSource')

// Library handles all sync, debouncing, and race prevention
```

**Pros**:
- Battle-tested solution
- Handles all edge cases
- Cleaner code
- Type-safe

**Cons**:
- New dependency
- Requires learning library API
- Significant refactoring
- Migration effort

## Implementation Tasks

Based on the analysis, **Option 3 (Single Source of Truth - URL)** is recommended for a robust, maintainable solution. However, **Option 1 + 2 combined** provides a quick, low-risk fix.

### Recommended Approach: Quick Fix First, Then Refactor

**Phase 1: Quick Fix** ✅ COMPLETED

- [x] Update flag clearing logic to check `pendingUrlUpdatesRef === 0` before clearing `isProgrammaticUrlUpdateRef`
- [x] Increase timeout from 300ms to 500ms for additional safety margin
- [x] Test with existing E2E tests
- [x] Manually test rapid toggle clicking (3-4 toggles quickly)

**Status**: ✅ Implemented successfully in `GalleryPage.tsx` (lines 410-414)
- All E2E tests pass including the originally failing test
- Unit tests pass (337/337)
- Fix is minimal, low-risk, and preserves existing architecture

**Phase 2: Architectural Refactor** ❌ ATTEMPTED BUT REVERTED

- [x] Attempted to design URL-as-source-of-truth architecture
- [x] Attempted to refactor `handleToggleChange` to update URL directly
- [x] Attempted to remove bidirectional sync

**Status**: ❌ Reverted due to introducing new race conditions
- The refactor replaced one race condition with another
- Reading from `searchParams` in the handler doesn't work because `setSearchParams` is also asynchronous
- State always lags behind URL updates when interactions are rapid
- The bidirectional sync pattern with proper flag management (Phase 1) is actually more robust for this use case

**Conclusion**: Phase 1 fix is sufficient. Phase 2 architectural refactor is not recommended unless fundamental React Router async handling changes.

**Final phase - Testing** ✅ COMPLETED
- [x] Ensure tests pass: `make frontend-test-unit` (337 passed)
- [x] Ensure tests pass: `make frontend-test-e2e` (179 passed, 3 failed tests now pass)

## Additional Observations

1. **Tag filter synchronization** (lines 587-609) uses similar pattern and may have same vulnerability
2. **Search functionality** appears to handle this better by updating URL directly in handlers
3. Consider applying consistent URL sync pattern across all gallery filters

## Testing Recommendations

### For Quick Fix
- Run existing E2E test: `gallery-url-params.spec.ts:416`
- Add E2E test for 3-4 rapid toggles
- Test with network throttling to simulate slower systems

### For Refactor
- Unit tests for handler logic
- E2E tests for all interaction patterns
- Performance tests for rapid clicking
- Browser back/forward navigation tests
- Deep link / URL sharing tests

