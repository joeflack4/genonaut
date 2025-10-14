# Fix: Generation Status Oscillation Bug

## Problem Description

When a user submits a new image generation while a completed generation is already showing in the "Status" area, the application enters an infinite loop state with the following symptoms:

1. **Status oscillates** between "pending" and "completed"
2. **Console errors explode** with hundreds/thousands of rapidly growing log messages
3. **Maximum update depth exceeded** error appears in console
4. **WebSocket connections fail** with "WebSocket is closed before the connection is established" errors

### Key Insight
The issue does NOT occur on the first generation (when Status shows "Progress will display once generation starts."). It ONLY occurs when there is already a generation result showing (completed, failed, or any terminal state) and the user starts a new generation.

### Root Cause Hypothesis
There is a state conflict between the old completed generation and the new pending generation, causing a feedback loop between:
- Parent component (GenerationPage) state
- Child component (GenerationProgress) state
- WebSocket connection lifecycle
- Status updates from multiple sources (WebSocket, polling, parent props)

## Console Error Messages

```
useJobWebSocket.ts:110 WebSocket connected for job 1193942
WebSocket connection to 'ws://<URL>/ws/jobs/1193942' failed: WebSocket is closed before the connection is established.
hook.js:608 Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.
```

## Files Involved

- `frontend/src/pages/generation/GenerationPage.tsx` - Parent component managing generation state
- `frontend/src/components/generation/GenerationProgress.tsx` - Child component displaying status and managing WebSocket
- `frontend/src/hooks/useJobWebSocket.ts` - WebSocket connection management
- `frontend/src/components/generation/GenerationForm.tsx` - Form that initiates generation

## Attempted Fixes (In Order)

### Fix Attempt #1: Stabilize handleStatusUpdate Callback
**File:** `frontend/src/components/generation/GenerationProgress.tsx:169-205`

**What was changed:**
- Made `handleStatusUpdate` callback stable by removing `initialGeneration` from dependencies
- Used a ref (`initialGenerationRef`) to access initialGeneration without triggering re-renders
- Changed dependency array from `[initialGeneration]` to `[]`

**Why:** Thought the callback was being recreated on every render, causing WebSocket to reconnect unnecessarily.

**Result:** Did not fix the issue.

### Fix Attempt #2: Restructure WebSocket Lifecycle Effects
**File:** `frontend/src/components/generation/GenerationProgress.tsx:259-284`

**What was changed:**
- Split WebSocket connection/disconnection into two separate useEffect hooks
- First effect: Connect when job starts (only depends on `initialGeneration.id`)
- Second effect: Disconnect when job reaches terminal state (depends on `currentGeneration.status`)
- Added eslint-disable comments to suppress dependency warnings

**Why:** Thought the WebSocket was disconnecting/reconnecting on every status change, causing the loop.

**Result:** Did not fix the issue.

### Fix Attempt #3: Improve WebSocket Disconnect Cleanup
**File:** `frontend/src/hooks/useJobWebSocket.ts:57-87`

**What was changed:**
- Clear all event handlers (`onopen`, `onmessage`, `onerror`, `onclose`) before closing WebSocket
- Set handlers to `null` to prevent events from firing during cleanup
- Only close if readyState is OPEN or CONNECTING

**Why:** Thought the WebSocket errors during disconnect were contributing to the loop.

**Result:** Reduced console noise but did not fix the oscillation issue.

### Fix Attempt #4: Break Synchronous Update Cycle
**File:** `frontend/src/components/generation/GenerationProgress.tsx:423-440`

**What was changed:**
- Wrapped `onGenerationUpdate` call in `setTimeout(..., 0)`
- Added cleanup to clear timeout

**Why:** Thought synchronous state updates between parent and child were causing the loop.

**Result:** Did not fix the issue.

### Fix Attempt #5: Clear State Before New Generation
**File:** `frontend/src/pages/generation/GenerationPage.tsx:24-32`

**What was changed:**
```typescript
const handleGenerationStart = (generation: ComfyUIGenerationResponse) => {
  // Clear any existing generation state first to prevent state conflicts
  setCurrentGeneration(null)
  // Use setTimeout to ensure the null state is applied before setting new generation
  setTimeout(() => {
    setCurrentGeneration(generation)
    setRefreshHistory(prev => prev + 1)
  }, 0)
}
```

**Why:** Based on user diagnosis that issue only happens when there's already a completed generation showing. Attempted to clear the state before loading new generation.

**Result:** Did not fix the issue.

## FINAL SOLUTION (RESOLVED)

The issue has been **SUCCESSFULLY FIXED** with the following changes:

### Fix #1: Add hasMeaningfulChange Check in Prop Sync Effect
**File:** `frontend/src/components/generation/GenerationProgress.tsx:274-278`

Added a check to prevent accepting parent prop updates when there's no meaningful change. This breaks the circular update loop between parent and child:

```typescript
// Same job - check if there's actually a meaningful change before updating
if (!hasMeaningfulChange(prev, next)) {
  console.log('[Effect:PropSync] No meaningful change from parent, keeping current state')
  return prev  // Return prev to avoid triggering downstream effects
}
```

### Fix #2: Add Key Prop to Force Component Cleanup
**File:** `frontend/src/pages/generation/GenerationPage.tsx:118`

Added a `key` prop based on generation ID to force React to completely unmount and remount the component when switching between generations:

```typescript
<GenerationProgress
  key={currentGeneration.id}  // Forces unmount/remount on ID change
  generation={currentGeneration}
  onGenerationUpdate={handleGenerationUpdate}
  onStatusFinalized={handleGenerationFinalStatus}
  onClear={handleGenerationReset}
/>
```

### Fix #3: Simplified Generation Start Handler
**File:** `frontend/src/pages/generation/GenerationPage.tsx:24-28`

Removed the `null`/`setTimeout` workaround since the `key` prop handles proper cleanup:

```typescript
const handleGenerationStart = (generation: ComfyUIGenerationResponse) => {
  // Key prop on GenerationProgress ensures proper cleanup when ID changes
  setCurrentGeneration(generation)
  setRefreshHistory(prev => prev + 1)
}
```

### Testing
Added comprehensive E2E test: `frontend/tests/e2e/generation-oscillation.spec.ts`

The test verifies:
- No "Maximum update depth exceeded" errors
- No excessive WebSocket reconnections
- Stable status (no oscillation)
- Minimal console errors
- No excessive re-renders

**Test Status:** ✅ All tests passing

### Verification
The issue is no longer reproducible:
1. Generate an image successfully (wait for completion)
2. Generate a second image while the first is still showing in Status
3. ✅ No infinite loop, no console errors, status remains stable

## Previous State

The first five fix attempts were applied but the issue persisted until the final solution above was implemented.

## Next Steps for Debugging

Need to investigate:
1. **State update sequence** - Log every state change in GenerationProgress to see the exact sequence
2. **Effect execution order** - Add detailed logging to all useEffect hooks to see when they fire
3. **Prop changes** - Log when `initialGeneration` prop changes and what triggers it
4. **WebSocket message flow** - Log all WebSocket messages and when they arrive
5. **hasMeaningfulChange logic** - Check if this comparison is working correctly
6. **Persisted state** - Check if `usePersistedState` in GenerationPage is causing issues

### Specific Questions to Answer:
- Why does currentGeneration.status keep changing between pending and completed?
- What is triggering the WebSocket to reconnect repeatedly?
- Is the parent component re-rendering and passing stale props?
- Is there a race condition between clearing state and setting new state?
- Are there multiple sources of truth fighting over the status value?

## Related Code Sections

### GenerationProgress State Management
```typescript
// Line 213-257: Reset local state when new generation comes from parent
useEffect(() => {
  setCurrentGeneration(prev => {
    const next = normalizeGeneration(initialGeneration)

    // If different job ID, always accept
    if (!prev || prev.id !== next.id) {
      startTimeRef.current = Date.now()
      previousStatusRef.current = next.status
      return next
    }

    // Same job - don't accept downgrades from terminal to non-terminal
    if (isTerminal(prev.status) && !isTerminal(next.status)) {
      console.debug('[GenerationProgress] Ignoring parent prop downgrade', {
        previousStatus: prev.status,
        incomingStatus: next.status,
      })
      return prev
    }

    // ... timestamp checks ...

    return next
  })
}, [initialGeneration.id, initialGeneration])
```

### WebSocket Status Update Handler
```typescript
// Line 169-205: Handle WebSocket status updates
const handleStatusUpdate = useCallback((update: JobStatusUpdate) => {
  console.log('WebSocket update received:', update)
  setCurrentGeneration(prev => {
    const nextGeneration = normalizeGeneration({
      ...prev,
      status: update.status,
      ...(update.content_id && { content_id: update.content_id }),
      ...(update.output_paths && { output_paths: update.output_paths }),
      ...(update.error && { error_message: update.error }),
    })

    if (isTerminal(prev.status) && !isTerminal(nextGeneration.status)) {
      console.debug('[GenerationProgress] Ignoring websocket downgrade', {
        previousStatus: prev.status,
        incomingStatus: nextGeneration.status,
      })
      return prev
    }

    return nextGeneration
  })
}, [])
```

### Parent Update Callback
```typescript
// Line 423-440: Notify parent of changes
useEffect(() => {
  if (!onGenerationUpdate) {
    return
  }

  if (!hasMeaningfulChange(lastBroadcastRef.current, currentGeneration)) {
    return
  }

  lastBroadcastRef.current = currentGeneration

  // Use setTimeout to break the synchronous update cycle and prevent infinite loops
  const timeoutId = setTimeout(() => {
    onGenerationUpdate(currentGeneration)
  }, 0)

  return () => clearTimeout(timeoutId)
}, [currentGeneration, onGenerationUpdate])
```

## Hypothesis for MCP Debugging Session

The likely culprit is a **circular state update loop** between:
1. GenerationPage sets new generation ->
2. GenerationProgress receives it and updates local state ->
3. GenerationProgress calls onGenerationUpdate ->
4. GenerationPage updates its state ->
5. GenerationProgress receives updated prop ->
6. Loop continues...

The `hasMeaningfulChange` check is supposed to prevent this, but something is causing it to always return true, allowing the loop to continue.

Alternatively, there might be a **race condition** where:
1. Old WebSocket (for completed job) is still sending updates
2. New WebSocket (for new job) is also sending updates
3. Both are fighting to set the status
4. React is batching these updates in a way that causes oscillation
