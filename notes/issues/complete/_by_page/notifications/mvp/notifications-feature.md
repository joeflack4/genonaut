# Notifications Feature Task

## Task Overview
Enhance notifications UX and backend support by adding dedicated list and detail pages, ensuring API routes support these workflows, and confirming seed scripts auto-load static CSVs.

## Phases & Tasks
### Phase 1: Discovery
- [x] Review existing notification UI components and routing.
- [x] Inspect current notification-related API endpoints and database models.
- [x] Audit seed script static CSV loading behavior.

### Phase 2: API & Backend Updates
- [x] Implement or adjust endpoints to list, filter, read, and delete notifications.
- [x] Ensure notification detail retrieval works for individual IDs.
- [x] Add backend tests covering new or changed notification behavior.

### Phase 3: Frontend Notifications List Page
- [x] Create `/notifications` route showing all notifications sorted newest to oldest.
- [x] Add read/unread visual indicators and filter dropdown with multi-select by type.
- [x] Support deletion with confirmation modal/dialog.

### Phase 4: Frontend Notification Detail
- [x] Implement `/notification/[id]` page displaying notification details and marking as read when viewed.
- [x] Update navigation menu and bell dropdown to link to new pages.

### Phase 5: Polish & Validation
- [ ] Run relevant unit/integration tests (backend/frontend) and ensure they pass. @dev-rollup
- [x] Update documentation or notes if workflows change (no additional updates required).

## Tags
- dev-rollup: Because of sandbox environment, Codex cannot run these tests. Ask the dev (user) to do so, and they will provide the results for you to analyze.

## Questions
- None yet.
