# Notifications Unread Enhancements

## Task Overview
Add the ability for users to mark notifications as unread from the detail view, including backend support and UI integration.

## Phases & Tasks
### Phase 1: Analysis
- [x] Identify backend changes required to mark notifications as unread.
- [x] Determine UI updates needed on notification detail page.

### Phase 2: Backend Implementation
- [x] Add repository/service support plus API endpoint for marking notifications unread.
- [x] Add unit tests covering the new unread pathway.

### Phase 3: Frontend Implementation
- [x] Add "Mark as unread" control beside "All notifications" button on detail page.
- [x] Wire new control to API and update local state/query cache accordingly.
- [x] Ensure dropdown/list reflects unread status after action.

### Phase 4: Validation
- [ ] Run targeted backend and frontend tests (or coordinate reruns externally).
- [ ] Verify console is clean when using new action.

## Tags
- dev-rollup: Frontend unit tests run by dev outside sandbox; share results for follow-up.

## Questions
- None yet.
