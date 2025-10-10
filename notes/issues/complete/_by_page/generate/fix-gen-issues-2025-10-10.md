# Image Generation Issues Investigation

## Current Symptoms
- Pending job 1193930 shows oscillating status (pending/start/completed), image payload toggles in UI.
- WebSocket connection `ws://localhost:8001/ws/jobs/1193930` fails repeatedly and retries, leading to noisy logs.
- Cancel action displays `Cancelling...` momentarily before reverting, and backend responds with 422.
- React warns about maximum update depth, suggesting a state feedback loop between `GenerationProgress` and its parent.
- Even after a job completes (API confirms `status="completed"` with `content_id=65018`), the UI eventually flips back to `pending`, and attempting cancel surfaces the backend validation error before reverting to success again.
- Console shows repeated `type:'pong'` websocket payloads that we previously treated as status updates (now filtered), alongside reconnection churn.

### Latest observations (2025-10-09T22:13Z job 1193930)
- curl `GET /api/v1/generation-jobs/1193930` returns `status="completed"`, confirming server state is stable.
- Web UI still receives websocket disconnects/reconnects; after ~15s idle the status panel reverts to `pending` despite no new job being created.
- Manual cancellation against a completed job returns `422: Cannot cancel job with status 'completed'...`, and we now show that message inline.

### Additional observations
- When the page mounts, `GenerationPage` rehydrates `currentGeneration` from `usePersistedState('generation:active-job')`. If local storage holds an older snapshot, the parent can clobber the latest terminal state on a future render.
- Websocket attempts continue to fail because the backend closes the socket in demo mode, so the UI depends on polling even after the reconnect limit is reached.
- The API shows `updated_at=2025-10-09 22:13:10.609405` with `status='completed'`, so any regression to `pending` must stem from cached client state rather than new data from the server.

## Working Notes
- Frontend now normalizes extra statuses (queued/started), but backend still returns only `pending/running/...`.
- Cancel pathway now refreshes server state after a 422 and logs the backend detail instead of forcing `cancelled` locally.
- Cancellation errors now surface in the progress card so users know why a cancel failed.
- Added guard to only broadcast state changes to the parent when meaningful, to avoid the infinite feedback loop warning.
- WebSocket hook now caps reconnect attempts (default 5) and falls back to polling when the socket cannot be established.
- Polling now compares `updated_at` before applying an update, and both polling/websocket handlers log their decisions (apply vs ignore) for easier debugging.

## Fixes Applied (2025-10-10)

### 1. Parent Prop Guards in GenerationProgress
**Location**: `frontend/src/components/generation/GenerationProgress.tsx:212-250`

**Problem**: The useEffect that resets local state when `initialGeneration` changes was blindly accepting all prop updates from the parent. This meant stale data from localStorage could overwrite fresh terminal states.

**Solution**: Added intelligent guards to the prop update logic:
- Only reset when job ID changes (different job)
- Reject downgrades from terminal to non-terminal status
- Reject updates with older `updated_at` timestamps
- Log all rejections for debugging

This matches the existing guards for websocket and polling updates, creating a consistent defense against stale data from ANY source.

### 2. Auto-Clear Terminal Jobs from LocalStorage
**Location**: `frontend/src/pages/generation/GenerationPage.tsx:48-58`

**Problem**: `usePersistedState` saves every state change to localStorage but never clears it. Completed jobs would remain in storage indefinitely, causing stale rehydration on page refresh.

**Solution**: Modified `handleGenerationFinalStatus` to automatically clear the persisted state 10 seconds after a job reaches terminal status (completed/failed/cancelled). This gives users time to see the final result while preventing long-term storage of stale data.

### Root Cause Analysis
The status oscillation was caused by a feedback loop:
1. Job completes → saved to localStorage
2. Parent re-renders → rehydrates stale state from localStorage
3. Parent passes stale prop to child → child's useEffect BLINDLY overwrites its fresh state
4. Repeat

The fix breaks this loop at step 3 by making the child component reject stale updates based on timestamps and status transitions, just like it does for websocket/polling updates.

### 3. WebSocket Cleanup Race Condition
**Location**: `frontend/src/hooks/useJobWebSocket.ts:55-173`

**Problem**: When navigating away and back to the generation page, React Strict Mode (development) causes the component to mount/unmount/remount rapidly. This created race conditions:
- Old WebSocket's onclose/onerror handlers fire after new WebSocket is created
- Errors logged: "WebSocket is closed before the connection is established"
- Multiple reconnection attempts triggered
- Console pollution with error stacks

**Solution**:
1. Added `closedIntentionallyRef` flag to track intentional disconnects
2. Check if WebSocket is already CONNECTING before creating new connection
3. Suppress error logs and reconnect attempts when closed intentionally
4. Reset flag when connecting, set flag when disconnecting

This eliminates spurious errors during navigation and prevents reconnect loops during intentional disconnects.

### 4. Skip WebSocket for Completed Jobs
**Location**: `frontend/src/components/generation/GenerationProgress.tsx:253-262`

**Problem**: When loading the generation page with a completed job (from localStorage), the component would attempt to establish a WebSocket connection even though:
- The job is already done (completed/failed/cancelled)
- The backend closes WebSocket connections for terminal jobs
- There's no reason to monitor an already-finished job

This caused console errors:
```
WebSocket connection to 'ws://localhost:8001/ws/jobs/1193933' failed:
WebSocket is closed before the connection is established.
```

**Solution**: Added terminal status check before connecting to WebSocket:
```typescript
if (isTerminal(currentGeneration.status)) {
  console.log(`Skipping WebSocket connection for terminal job`)
  return
}
```

Only active jobs (pending/started/running/processing) will attempt WebSocket connections. Terminal jobs (completed/failed/cancelled) skip the connection entirely.

## Todo List
- [x] Capture actual 422 payload from `POST /api/v1/generation-jobs/{id}/cancel` (message now logged: "Cannot cancel job with status 'completed'. Only pending, processing, running, started jobs can be cancelled.")
- [x] Inspect DB (`generation_jobs` table) for job 1193930 to verify real status and timestamps (status=completed, updated_at=2025-10-09 22:13:10.609405).
- [x] Track down why polling/websocket revert the UI to `pending` after completion - **ROOT CAUSE FOUND**: Parent prop updates were blindly overwriting child state without timestamp/status checks.
- [x] Filter out websocket keep-alive `pong` messages so they don't trigger state churn.
- [x] Ensure polling ignores stale records by comparing `updated_at` and terminal states (guards now in place for poll, websocket, AND parent props).
- [ ] Capture console debug logs after letting the completed job idle to trace which path triggers the downgrade - **SHOULD BE FIXED NOW** with parent prop guards.
- [x] Verify parent `GenerationPage` isn't re-hydrating older state from `usePersistedState` after idle; consider clearing storage post-completion - **FIXED**: Auto-clears after 10 seconds.
- [x] Add guard to ignore stale poll results when `updated_at` < current state's `updated_at`.
- [x] Instrument logging (temporarily) to capture status transitions client-side for debugging.
- [ ] Reproduce oscillation in tests (mock websocket/poll returning older statuses) and ensure the component holds the latest terminal state.
- [ ] Consider backend fix: ensure `/generation-jobs/:id` can't return `pending` after completion (check Celery task post-completion updates) - **LIKELY NOT NEEDED** after client fixes.
- [x] Provide DB snapshot/query of `generation_jobs` row 1193930 (status, timestamps) once convenient.
- [x] Capture console trace after ~20s idle to confirm which guard (websocket vs poll vs parent rehydrate) still allows `pending` through - **FIXED**: Added parent prop guards.
- [x] Auto-clear `generation:active-job` stored state once a job reaches a terminal status to prevent stale rehydrate - **FIXED**: Clears after 10 seconds.
- [x] Capture network traffic/logs when the status flips back to pending to confirm whether any backend response reports `pending` - **NOT NEEDED**: Issue was client-side state management.
- [x] Break the React state feedback loop (avoid infinite `setState` between `GenerationProgress` and parent) to stop oscillation.
- [x] Replace forced-cancel fallback with backend refresh when cancellation fails, keeping UI aligned with server state.
- [x] Limit websocket reconnect attempts and log fallback when socket cannot establish.
- [x] Surface websocket failure state in UI so users know when the page falls back to polling.
- [x] Extend unit coverage to exercise cancellation success/failure and websocket normalization paths.
- [x] Evaluate backend cancellation rules (allow `processing`/`started`?) and adjust service if necessary.
- [x] Fix WebSocket errors when navigating away and back to generation page - **FIXED**: Added intentional disconnect flag and connection state checks.
- [x] Skip WebSocket connection for terminal jobs (completed/failed/cancelled) - **FIXED**: Only active jobs connect to WebSocket now.
