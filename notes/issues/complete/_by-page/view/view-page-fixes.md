## Context
If I am in the dashboard, I can click an image, and it will load a "view" page, at the route: /dashboard/ID.

Similarly, if I am in the gallery, I can click an image, and it will load a "view" page, at the route: /gallery/ID.

However, the desired behavior is that both entry points open a unified route: `/view/ID`.

When an image successfully generates in the "Image Generation" page, it correctly displays the image and messaging on the right. However, clicking the image currently routes to the dashboard where the image is missing, and navigating away and back clears the generation status/results.

## Phased Checklist

### Phase 1 - Planning and Alignment
- [x] Review prior fixes related to image rendering (see `notes/gen-img-success-fixes1.md`).
- [x] Confirm existing routes and components used for dashboard (`DashboardImageView`), gallery (`GalleryImageView`), and routing entries in `frontend/src/App.tsx`.
- [x] Identify dependencies or shared utilities impacted by routing changes (e.g. `useGalleryItem`, `getImageUrl*` helpers, navigation handlers in dashboard/gallery pages).

### Phase 2 - Unified View Routing (`/view/:id`)
- [x] Update router configuration to introduce `/view/:id` and add legacy redirects for `/dashboard/:id` and `/gallery/:id`.
- [x] Refactor dashboard entry points to link to `/view/:id` with routing state for fallback context.
- [x] Refactor gallery entry points to link to `/view/:id` with routing state for fallback context.
- [x] Ensure deep linking (direct navigation to `/view/:id`) renders correctly via new shared view component.
- [x] Update relevant tests (frontend unit) and mocks to reflect the new route (`ImageViewPage`).

### Phase 3 - Image Generation Flow Improvements
- [x] Update the generation success view to link to `/view/:contentId` with appropriate routing state.
- [x] Persist generation status/results when navigating away and back via `usePersistedState` and generation updates.
- [x] Add/adjust tests covering the new persistence behavior and link target (`GenerationProgress` unit tests).

### Phase 4 - Verification and Documentation
- [x] Run targeted unit tests for updated areas (frontend routes/components, generation flow).
- [x] Execute broader regression checks if needed (tsc `--noEmit`).
- [x] Update documentation (`docs/frontend/overview.md`) describing the unified view route.
- [x] Capture manual verification notes in this document if additional follow-up is required.

### Manual Verification Notes
- Validate in browser: dashboard tile click -> `/view/:id` renders image
- Validate gallery item click -> `/view/:id`
- Confirm generation success click opens `/view/:id` and returning preserves status panel

## Tags
- `skipped-example`: Placeholder for documenting skipped tasks if needed.

## Questions
- None at this time.

## SOP Reference
1. Create a multi-phased checklist of checkbox tasks below to address these problems.
2. Read and follow this document as the SOP for completing these tasks: `notes/routines/iteration.md`.
