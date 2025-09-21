# Frontend Overview

The Genonaut frontend lives in the `frontend/` directory and is implemented with React, TypeScript, and Vite. The UI is structured around Material UI components, React Router for navigation, and React Query for all data fetching and caching. The backend API is consumed through a thin service layer that wraps the shared `ApiClient` helper.

## Project layout

```
frontend/
├── src/
│   ├── app/                # App shell, providers, routing helpers
│   ├── components/         # Layout primitives and reusable pieces
│   ├── hooks/              # React Query hooks for data access
│   ├── pages/              # Top-level routed views
│   ├── services/           # API client + domain service classes
│   ├── types/              # API and domain typings
│   └── test/               # Test utilities (MSW server, query client)
├── public/
├── docs/frontend/          # Frontend documentation
└── tests/                  # (reserved for Playwright when enabled)
```

## Key libraries

- **Routing** – `react-router-dom@7`
- **Styling** – Material UI with the custom `ThemeModeProvider`
- **Data fetching** – `@tanstack/react-query`
- **HTTP abstraction** – `fetch` via `ApiClient`, services map API payloads to domain types
- **Testing** – Vitest + Testing Library + MSW for unit/integration tests, plus Playwright for E2E.

## Core concepts

- **Providers** – `AppProviders` wires QueryClient + ThemeMode contexts. `ThemeModeProvider` persists the palette and exposes `useThemeMode`.
- **Services** – `ApiClient` centralises HTTP behaviour (base URL, error handling). `UserService`, `GalleryService`, and `RecommendationService` expose typed operations against the backend.
- **Hooks** – `useCurrentUser`, `useContentList`, `useUserStats`, `useRecommendations`, and mutation hooks encapsulate React Query usage. All hooks have unit tests.
- **Pages** –
  - **Dashboard** shows user stats and recent content cards.
  - **Gallery** provides search/sort filters with pagination.
  - **Recommendations** lists current suggestions with “mark as served”.
  - **Settings** updates profile fields and exposes the theme toggle.
  - **Auth placeholders** (login/signup) guard authenticated users and explain the stubbed state.

## Available scripts

```
npm run dev           # Vite dev server at http://localhost:5173
npm run build         # Type checking + production build
npm run lint          # ESLint (flat-config)
npm run test-unit      # Vitest in CI mode (unit tests only)
npm run test          # All tests (unit + e2e)
npm run test:watch    # Vitest watch mode
npm run test:coverage # Vitest with V8 coverage
npm run test:e2e      # Playwright end-to-end tests
npm run test:e2e:headed # Playwright tests with browser UI
npm run test:e2e:ui   # Playwright debug UI mode
npm run type-check    # tsc --noEmit
npm run openapi:types # Generates types from OPENAPI_SCHEMA_URL (defaults to local API)
```

The top-level `Makefile` includes matching helpers (`make frontend-dev`, `make frontend-test`, etc.) so you can stay in the usual workflow.

## Testing workflow

1. Unit + integration tests run with `npm run test-unit`. All tests (unit + e2e) run with `npm run test`.
2. ESLint (`npm run lint`) executes against `src/**/*.{ts,tsx}`.
3. Playwright end-to-end specs live under `tests/e2e/` and run with `npm run test:e2e` (headed/UI variants available).

## Environment

- Configure the API base URL with `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).
- Theme preference persists to `localStorage` under `theme-mode`.
- The OpenAPI generator script honours `OPENAPI_SCHEMA_URL` and `OPENAPI_OUTPUT` env vars for custom schemas.

## Next steps

- Integrate with real authentication once the backend is ready.
- Hook the Playwright E2E suite into CI and grow coverage alongside new flows.
- Expand services/hooks as new backend endpoints land.
