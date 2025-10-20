# Frontend Development Guide

This file provides guidance to Claude Code when working with frontend code in this repository.

## Project Overview
React + TypeScript + Vite frontend with Material UI, React Router, and React Query for data fetching.

## Environment Setup
**IMPORTANT**: Before starting frontend work:
```bash
cd frontend
npm install
```

## Code Style & Architecture
- Use TypeScript with strict typing for all function parameters
- Follow React best practices with hooks and functional components
- Use React Query for all data fetching and caching
- Prefer pure functions and avoid side effects where possible
- Instrument UI markup with stable `data-testid` attributes so components are easy to reference in reviews, automated tests, and debugging tools. See **Data Test IDs** below for conventions.

## Key Libraries & Patterns
- **Routing**: `react-router-dom@7`
- **Styling**: Material UI with custom `ThemeModeProvider`
- **Data Fetching**: `@tanstack/react-query` via service hooks
- **HTTP Client**: `ApiClient` + domain services (`UserService`, `GalleryService`, etc.)
- **Testing**: Vitest + Testing Library + MSW for mocking

## Testing Strategy
Follow comprehensive testing approach:
```bash
# Unit tests (fastest)
npm run test-unit
make frontend-test-unit

# All tests (unit + e2e)
npm run test
make frontend-test

# E2E tests only (Playwright)
npm run test:e2e
make frontend-test-e2e

# Development
npm run test:watch        # Auto-run tests on changes
npm run test:coverage     # Coverage reporting
```

## Development Workflow
```bash
# Development server
npm run dev               # http://localhost:5173
make frontend-dev

# Code quality
npm run lint              # ESLint checks
npm run type-check        # TypeScript validation
npm run build             # Production build
```

## Testing Requirements
- **Unit Tests**: >90% coverage for components, hooks, services
- **E2E Tests**: Cover critical user journeys
- Write tests during development, not after
- Mock external dependencies in unit tests
- Use MSW for API mocking in tests

## Key Directories
```
frontend/src/
├── app/          # App shell, providers, routing
├── components/   # Reusable UI components
├── hooks/        # React Query hooks for data access
├── pages/        # Top-level routed views
├── services/     # API client + domain services
├── types/        # TypeScript definitions
└── test/         # Test utilities (MSW, query client)
```

## Code Quality Standards
- Use TypeScript for all new code
- Add comprehensive component tests for UI components
- Include hook tests for custom hooks
- Follow Material UI design patterns
- Ensure responsive design principles
- Verify new `data-testid` hooks are covered by unit/E2E tests where practical, and update existing tests when markup changes.

## Data Test IDs
- Every routed page, major layout container, toolbar, card/list section, loading/empty state, and interactive control should expose a unique `data-testid`.
- Use a consistent `page-or-component-element` pattern (e.g. `dashboard-page-root`, `tags-page-refresh`, `app-layout-search-form`). For collections, interpolate context (`gallery-result-item-${item.id}`).
- When using Material UI, set IDs via the appropriate props (e.g. `inputProps={{ 'data-testid': 'search-input' }}`, `slotProps={{ paper: { 'data-testid': '...' } }}`).
- Ensure skeleton/loading and empty states have their own IDs so tests can assert transitions.
- Update existing tests (Vitest + Playwright) to assert against the new IDs whenever markup changes. Example snippets from `notes/el-ids.md`:
  ```tsx
  <Box data-testid="page-root" sx={{ p: 3 }}>
    <List data-testid="gallery-results-list">
      {items.map((item) => (
        <ListItem key={item.id} data-testid={`gallery-result-item-${item.id}`} />
      ))}
    </List>
  </Box>

  <TextField
    label="Search"
    inputProps={{ 'data-testid': 'search-input' }}
    FormHelperTextProps={{ 'data-testid': 'search-help' }}
  />
  ```
- Treat `data-testid` coverage as part of the definition of done for UI work; new sections without IDs should be considered incomplete.

## Documentation Requirements
- Update component documentation for significant changes
- Add JSDoc comments for complex functions
- Consider updating `docs/frontend/overview.md` for architectural changes
- Document new testing patterns or utilities
