# Frontend MVP Action Plan

## 0. Preparation
- [x] Review `docs/api.md` to map concrete endpoints for user profile, content catalog, and recommendations required for the MVP.
- [x] Capture any clarifications from stakeholders and sync updates back into `scratchpads/frontend.md`.

## 1. Project Scaffolding & Tooling
- [x] Write a failing Vitest smoke test for `App` that expects the branded shell layout and initial route to render.
- [x] Scaffold a Vite React+TypeScript app in `frontend/` with ESLint, Prettier, Testing Library, React Router, React Query, Material UI, and Vitest configured.
- [x] Implement the minimal app shell (providers, baseline layout) to satisfy the smoke test.
- [x] Configure npm scripts (lint, test, type-check, e2e) and integrate equivalent Make targets.

## 2. API Client & Types
- [x] Define OpenAPI generator config and write a failing service-layer test (MSW) for `UserService.getCurrentUser` hitting `/api/v1/users/{id}`.
- [x] Generate the API client/types and implement the shared `ApiClient` plus domain services to pass the test.
- [x] Create React Query hooks (`useCurrentUser`, `useContentList`, `useRecommendations`) with unit tests mocking the services.

## 3. State Management & Theming
- [x] Write failing tests for a theme context that defaults to dark mode and persists toggle state.
- [x] Implement the theme provider, wire it into MUI, and ensure tests pass.
- [x] Write failing tests for the layout components (header with user name, sidebar navigation, responsive container).
- [x] Implement the layout components with Material UI to satisfy layout tests.

## 4. Dashboard Page
- [x] Write failing unit tests verifying the dashboard requests `/api/v1/users/{id}/stats` and recent content data.
- [x] Implement dashboard widgets/cards (summary metrics, recent content) to satisfy tests.
- [x] Add a Playwright scenario that stubs API responses and validates dashboard rendering.

## 5. Content Management Page
- [x] Write failing tests for the content list hook covering pagination and filtering parameters.
- [x] Implement the content table/grid with filter controls to meet test expectations.
- [x] Add a Playwright test for browsing, filtering, and viewing a content item.

## 6. Recommendations Page
- [x] Write failing unit tests for fetching `/api/v1/users/{id}/recommendations` and marking items served.
- [x] Implement the recommendations list with action handlers to satisfy tests.
- [x] Add a Playwright flow validating recommendation display and mark-as-served interaction.

## 7. Settings Page
- [x] Write failing tests for the settings form (pre-populated user data, updating preferences, dark mode toggle integration).
- [x] Implement the settings page with form controls and Mutation hooks to pass tests.
- [x] Add a Playwright test toggling theme and confirming persistence across reload.

## 8. Auth Placeholder Pages
- [x] Write failing tests ensuring login and signup routes render and redirect authenticated users to the dashboard.
- [x] Implement placeholder login/signup pages and simple guard logic to satisfy tests.

## 9. Documentation & Knowledge Share
- [x] Draft `docs/frontend/overview.md` detailing architecture, conventions, and local commands.
- [x] Update `scratchpads/frontend.md` with clarifications and implementation decisions as they solidify.
- [x] Update `README.md` to link frontend setup and key npm scripts.

## 10. Wrap-up & Verification
- [x] Run lint, type-check, unit tests, and Playwright suites; note results for hand-off.
- [ ] Document open issues or deferred enhancements for post-MVP follow-up.
