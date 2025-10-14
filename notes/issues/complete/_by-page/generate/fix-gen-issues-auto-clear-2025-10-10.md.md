# Fix Auto-Clear Issue on Image Generation Status

## Problem Statement

When a user submits an image generation and it completes successfully:
1. The status widget shows "Completed" with the generated image
2. After approximately 10-11 seconds, the status area completely clears on its own
3. This happens WITHOUT the user clicking the "Clear Details" button
4. The clearing appears to be automatic and unexpected

## User Impact

This creates a poor user experience because:
- Users want to view their completed generations
- The automatic clearing happens while they're still looking at the result
- It feels like the UI is malfunctioning or the job was lost
- There's now a manual "Clear Details" button, so automatic clearing is unnecessary

## Console Logs Observed

The logs show a pattern of WebSocket connection issues around the time of completion:

```
WebSocket connection to 'ws://localhost:8001/ws/jobs/1193934' failed
WebSocket error events
WebSocket disconnected for job 1193934
WebSocket connected for job 1193934
Job status update: {status: 'completed', content_id: 65022}
Reconnecting WebSocket for job 1193934 (attempt 1)...
```

## Root Cause Analysis

### Primary Cause: Auto-Clear Timeout
In `frontend/src/pages/generation/GenerationPage.tsx`, the `handleGenerationFinalStatus` callback had a `setTimeout` that would clear the state after 10 seconds:

```typescript
setTimeout(() => {
  setCurrentGeneration(null)
}, 10000) // Clear after 10 seconds
```

This was added as part of the fix for status oscillation issues to prevent stale localStorage from causing problems. However, it creates the auto-clear behavior the user is experiencing.

### Secondary Issue: WebSocket Reconnection
The WebSocket continues trying to reconnect even after the job completes because:
1. Backend closes the WebSocket when job reaches terminal status
2. Hook's `onclose` handler sees this as unexpected disconnect
3. Auto-reconnect logic kicks in, causing connection attempts
4. This creates console noise but doesn't directly cause the clearing

## Fixes Applied

### Fix 1: Remove Auto-Clear Timeout
**Location**: `frontend/src/pages/generation/GenerationPage.tsx:48-53`

**Before**:
```typescript
const handleGenerationFinalStatus = useCallback((status, generation) => {
  setTimeoutActive(false)
  setCurrentGeneration(generation)
  setRefreshHistory(prev => prev + 1)

  setTimeout(() => {
    setCurrentGeneration(null)
  }, 10000)
}, [setCurrentGeneration])
```

**After**:
```typescript
const handleGenerationFinalStatus = useCallback((status, generation) => {
  setTimeoutActive(false)
  setCurrentGeneration(generation)
  setRefreshHistory(prev => prev + 1)
  // State persists until user manually clicks "Clear Details" button
}, [setCurrentGeneration])
```

**Result**: Completed jobs now stay visible until user manually clears them using the "Clear Details" button.

### Fix 2: Prevent WebSocket Reconnection After Terminal Status
**Location**: `frontend/src/hooks/useJobWebSocket.ts:125-129`

**Change**:
```typescript
// Auto-disconnect on terminal statuses and prevent reconnection
if (data.status === 'completed' || data.status === 'failed') {
  shouldConnectRef.current = false // Prevent auto-reconnect
  setTimeout(() => disconnect(), 1000)
}
```

Added `shouldConnectRef.current = false` to signal that we should not attempt to reconnect when the backend closes the connection for completed/failed jobs.

**Result**: Cleaner console logs, no unnecessary reconnection attempts after job completes.

## Testing Plan

To verify the fix:
1. Start a new image generation
2. Wait for it to complete successfully
3. Verify the completed status and image remain visible
4. Wait 15+ seconds to ensure no auto-clear occurs
5. Manually click "Clear Details" to verify user control works
6. Check console for cleaner WebSocket behavior (fewer reconnection attempts)

## Related Issues

This fix relates to the broader status management improvements made to prevent oscillation between statuses. The key insight is:

- **For oscillation prevention**: We needed to prevent stale localStorage from overwriting fresh state
- **For UX**: We should NOT auto-clear completed jobs - users should control when to clear

The solution is:
- Add guards to reject stale updates (already done)
- Keep completed jobs visible until user clears manually (this fix)
- Don't reconnect WebSocket after terminal status (this fix)
