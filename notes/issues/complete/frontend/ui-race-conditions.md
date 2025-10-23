# UI race conditions
## The general problem

**Bidirectional state-URL synchronization race conditions** occur when:
1. User action updates local state (e.g., toggle clicks)
2. State change triggers URL parameter update (to keep URL in sync)
3. URL parameter change triggers "sync from URL" effect
4. "Sync from URL" effect reads the URL that may not be fully updated yet, or reads it during rapid successive state changes
5. This causes the effect to "correct" the state back to an older value, undoing the user's action

This is particularly problematic when:
- Users perform rapid successive actions (multiple toggle clicks within ~1 second)
- The application needs bidirectional sync (state → URL and URL → state for browser back/forward)
- State updates and URL updates happen in separate React effect cycles

**Key insight**: The race occurs because we have TWO useEffects watching each other:
- Effect A: watches `contentToggles` state → updates URL
- Effect B: watches `searchParams` (URL) → updates `contentToggles` state
- When Effect A updates URL, it triggers Effect B, which may see stale/intermediate state

## Real examples
### Toggle URL Parameters - Multiple Sources (Race Condition)
This is a Playwright E2E test failure.
**Problem**: When clicking multiple toggles rapidly, the first toggle gets re-checked after clicking the second toggle.

**Root Cause**: The `useEffect` (lines 307-329 in GalleryPage.tsx) syncs toggles FROM URL, creating a race condition with rapid state changes. The `handleToggleChange` function uses `contentToggles` from closure which becomes stale.

**Fix Plan**:
- [x] Update `handleToggleChange` in `frontend/src/pages/gallery/GalleryPage.tsx:472-503` to use functional setState
- [x] Implement adaptive debouncing with programmatic update flag (see below for full solution)
- [x] Un-skip the test in `frontend/tests/e2e/gallery-url-params.spec.ts`
- [x] Verify all seven toggle URL parameter tests pass

## Solution(s)

### Approach 1: Adaptive Debouncing (RECOMMENDED)
**Concept**: Only debounce when there are pending URL updates; execute immediately otherwise.

**Pros**:
- Best UX: Immediate response for single actions, protection for rapid actions
- No perceived delay for normal usage
- Naturally batches rapid updates

**Cons**:
- Slightly more complex than fixed debouncing
- Need to track pending URL update state

**Implementation**:
- Track pending URL updates in a ref (counter or Set of update IDs)
- Before updating URL, check if any updates are pending
- If pending: debounce by ~150ms
- If not pending: execute immediately
- Decrement counter / remove from Set when update completes

### Approach 2: Simple Fixed Debouncing
**Concept**: Always debounce the "sync TO URL" effect by a fixed duration (100-150ms).

**Pros**:
- Very simple to implement
- Proven pattern, hard to mess up
- Works reliably for all cases

**Cons**:
- Always adds a small delay (even for single clicks)
- URL bar updates slightly after user action

**Implementation**:
- Wrap the "sync contentToggles TO URL" useEffect body in a setTimeout
- Return cleanup function that clears the timeout
- Use 100-150ms delay

### Approach 3: Update Source Tracking (Lock/Flag Pattern)
**Concept**: Use a ref to track when WE are updating the URL, and skip "sync FROM URL" during those updates.

**Pros**:
- No artificial delays
- Directly addresses the root cause (preventing circular updates)

**Cons**:
- Tricky timing: need to set/clear the flag at the right moments
- Can be fragile if not implemented carefully
- Async timing issues between state updates and URL updates

**Implementation**:
- Add `isUpdatingFromStateRef` ref
- Set ref to `true` before calling `setSearchParams` in "sync TO URL" effect
- In "sync FROM URL" effect, check ref and return early if `true`
- Clear ref after URL update completes (tricky: need to wait for next render cycle)

### Approach 4: Separate Update Queues
**Concept**: Queue URL updates and process them sequentially with proper state reconciliation.

**Pros**:
- Guarantees update order
- Can handle complex multi-field updates

**Cons**:
- Most complex solution
- Overkill for this problem
- Need to manage queue state

**Implementation**: (Not recommended for this use case)

---

## Chosen Solution: Adaptive Debouncing + Programmatic Update Flag

We implemented Approach 1 (Adaptive Debouncing) combined with Approach 3 (Update Source Tracking) for the most robust solution.

### Implementation Checklist

#### Phase 1: Setup tracking infrastructure
- [x] Add `pendingUrlUpdatesRef` useRef to track number of pending URL updates
- [x] Add `debounceTimerRef` useRef to track debounce timeout
- [x] Add `isProgrammaticUrlUpdateRef` useRef to track programmatic URL updates
- [x] Implemented inline in GalleryPage.tsx (no separate hook needed)

#### Phase 2: Modify "sync TO URL" effect
- [x] Implement adaptive debounce logic inline in useEffect
- [x] Increment `pendingUrlUpdatesRef.current` before scheduling or executing update
- [x] Decrement `pendingUrlUpdatesRef.current` after update completes (300ms delay)
- [x] Set debounce delay to 150ms for rapid successive updates
- [x] Set `isProgrammaticUrlUpdateRef` flag to prevent "Sync FROM URL" interference

#### Phase 3: Modify "sync FROM URL" effect
- [x] Add check for `isProgrammaticUrlUpdateRef.current` to skip during programmatic updates
- [x] This prevents circular updates and race conditions

#### Phase 4: Testing
- [x] All 7 tests pass in `npm run test:e2e -- tests/e2e/gallery-url-params.spec.ts`
- [x] Single toggle clicks update URL immediately (adaptive behavior)
- [x] Rapid multiple toggle clicks are batched with debouncing
- [x] Browser back/forward navigation works correctly

#### Phase 5: Cleanup
- [x] Add comprehensive code comments explaining the mechanism
- [x] Update this document with final implementation notes

---

## Final Implementation Notes (2025-10-23)

### What We Implemented

Combined two approaches for maximum robustness:

1. **Adaptive Debouncing**: Tracks pending URL updates with a ref counter
   - First update executes immediately (best UX)
   - Subsequent rapid updates (within 300ms) are debounced by 150ms
   - Batches rapid successive clicks automatically

2. **Programmatic Update Flag**: Prevents "Sync FROM URL" effect from interfering
   - Set to `true` when updating URL programmatically
   - "Sync FROM URL" effect checks this flag and skips if true
   - Cleared after 300ms to allow legitimate URL changes (browser back/forward)

### Key Implementation Details

**File**: `frontend/src/pages/gallery/GalleryPage.tsx`

**Refs added** (lines 162-168):
- `isInitializedRef` - Skip first render
- `pendingUrlUpdatesRef` - Counter for pending URL updates
- `debounceTimerRef` - Timeout handle for debouncing
- `isProgrammaticUrlUpdateRef` - Flag to prevent circular updates

**"Sync TO URL" effect** (lines 354-425):
- Check if any updates are pending (`pendingUrlUpdatesRef.current > 0`)
- If pending, debounce by 150ms; if not, execute immediately
- Increment counter BEFORE scheduling/executing
- Set programmatic flag before calling `setSearchParams`
- Clear flag and decrement counter after 300ms

**"Sync FROM URL" effect** (lines 317-352):
- Added check: `if (isProgrammaticUrlUpdateRef.current) return`
- Prevents effect from running during programmatic URL updates
- Still works for browser back/forward navigation (flag is cleared after 300ms)

### Why 300ms?

The 300ms timeout was chosen through testing:
- 100ms was too short for React to process all state updates
- 200ms was borderline
- 300ms provides reliable coverage while still being imperceptible to users
- Allows rapid clicks (within ~500ms) to be handled correctly

### Test Results

All 7 E2E tests pass:
1. Initializes toggles from URL with multiple disabled sources
2. Initializes all toggles ON when notGenSource is absent
3. Initializes single toggle OFF from URL
4. Updates URL when toggle is turned OFF
5. Removes URL param when last disabled toggle is turned ON
6. **Updates URL with multiple disabled sources** (previously failing, now fixed)
7. Maintains URL params when using browser back button

### Performance Characteristics

- Single clicks: Immediate URL update (0ms delay)
- Rapid clicks (<300ms apart): Debounced with 150ms delay, batched
- Normal usage: No perceptible delay
- Edge case (extreme rapid clicking): Gracefully batches all updates
