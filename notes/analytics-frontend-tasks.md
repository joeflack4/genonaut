# Analytics Frontend - Implementation Tasks

## Overview
This document tracks the implementation of the Analytics frontend page as specified in `analytics-frontend.md`. Tasks 
are organized by phase with clear acceptance criteria and dependencies.

## Phase 1: Foundation & Setup

### 1.1 Backend API Verification
- [ ] Verify `/api/v1/analytics/routes/cache-priorities` endpoint works
- [ ] Verify `/api/v1/tags/popular` endpoint works
- [ ] Check if `/api/v1/analytics/generation/overview` exists (or needs to be created)
- [ ] Document API response schemas for TypeScript types
- [ ] Test all endpoints with various query parameters
- [ ] Verify error responses and edge cases

### 1.2 TypeScript Types & Interfaces
- [ ] Create `frontend/src/types/analytics.ts` with:
  - `RouteAnalytics` interface
  - `RouteCachePriority` interface
  - `GenerationAnalytics` interface
  - `TagCardinalityStats` interface
  - Query parameter types
  - Filter state types
- [ ] Add JSDoc comments to all types
- [ ] Export all types for use in components

### 1.3 API Service Layer
- [ ] Create `frontend/src/services/AnalyticsService.ts` with methods:
  - `getRouteCachePriorities(params)`
  - `getGenerationOverview(params)`
  - `getTagCardinality(params)`
- [ ] Add error handling and retries
- [ ] Add request timeout configuration
- [ ] Write unit tests for service methods

### 1.4 React Query Hooks
- [ ] Create `frontend/src/hooks/useRouteCachePriorities.ts`
- [ ] Create `frontend/src/hooks/useGenerationAnalytics.ts`
- [ ] Create `frontend/src/hooks/useTagCardinality.ts`
- [ ] Configure appropriate staleTime and cacheTime
- [ ] Add refetch on window focus for generation stats
- [ ] Write unit tests for hooks with MSW mocking

## Phase 2: Routing & Navigation

### 2.1 Update Routing Configuration
- [ ] Add route `{ path: 'settings/analytics', element: <AnalyticsPage /> }` to App.tsx
- [ ] Import AnalyticsPage component
- [ ] Test route navigation works
- [ ] Add route to route table in tests

### 2.2 Update Sidebar Navigation
- [ ] Add "Analytics" to `navItems` in AppLayout.tsx (as settings sub-item)
- [ ] Implement hierarchical navigation display logic:
  - Show indented when Settings is active
  - Hide when Settings is not active or page is toggled off
- [ ] Add BarChartIcon or InsightsIcon for Analytics
- [ ] Add data-testid for Analytics nav item
- [ ] Update unit tests for AppLayout
- [ ] Test navigation in E2E tests

### 2.3 Update Settings Page
- [ ] Add "Analytics" card to SettingsPage.tsx
- [ ] Include link button to navigate to `/settings/analytics`
- [ ] Add description text explaining analytics purpose
- [ ] Add to sidebar pages toggle list (like search-history)
- [ ] Update data-testids
- [ ] Update unit tests for SettingsPage

## Phase 3: Core Page Structure

### 3.1 Create AnalyticsPage Component
- [ ] Create `frontend/src/pages/settings/AnalyticsPage.tsx`
- [ ] Add page root with data-testid="analytics-page-root"
- [ ] Add title "Analytics" (h1)
- [ ] Add subtitle description
- [ ] Create three card placeholders:
  - Route Analytics Card
  - Generation Analytics Card
  - Tag Cardinality Card
- [ ] Add basic layout with Material UI Stack/Grid
- [ ] Ensure responsive design (stack on mobile, columns on desktop)
- [ ] Add loading skeletons for all sections
- [ ] Add error boundaries

### 3.2 Page-Level State Management
- [ ] Create shared filter state (time range selection if needed)
- [ ] Add "Last Updated" timestamp display
- [ ] Add global refresh button for all sections
- [ ] Implement refresh logic that refetches all queries
- [ ] Add loading state coordination

### 3.3 Basic Component Tests
- [ ] Create `frontend/src/pages/settings/__tests__/AnalyticsPage.test.tsx`
- [ ] Test page renders without crashing
- [ ] Test title and subtitle display
- [ ] Test three card sections are present
- [ ] Test loading states
- [ ] Test error states
- [ ] Add snapshot test

## Phase 4: Route Analytics Section

### 4.1 Create RouteAnalyticsCard Component
- [ ] Create `frontend/src/components/analytics/RouteAnalyticsCard.tsx`
- [ ] Add card with title "Route Analytics"
- [ ] Add system selector (Absolute vs Relative)
- [ ] Add time range selector (7, 14, 30, 90 days)
- [ ] Add top N selector (5, 10, 20, 50)
- [ ] Add refresh button
- [ ] Store filter state in component state
- [ ] Add data-testids for all controls

### 4.2 Route Analytics Data Table
- [ ] Add Material UI Table or DataGrid component
- [ ] Define columns: Rank, Method, Route, Req/Hr, P95 Latency, Users, Priority, Success Rate
- [ ] Implement sortable columns
- [ ] Add color coding for latency:
  - Green: < 100ms
  - Yellow: 100-500ms
  - Red: > 500ms
- [ ] Highlight top 3 routes with subtle background
- [ ] Add tooltips for metric explanations
- [ ] Make responsive (horizontal scroll on mobile)

### 4.3 Route Analytics Data Integration
- [ ] Connect to useRouteCachePriorities hook
- [ ] Pass filter parameters from card state
- [ ] Handle loading state (skeleton table)
- [ ] Handle error state (error message + retry)
- [ ] Handle empty state (no data message)
- [ ] Format numbers appropriately (commas, decimals)
- [ ] Add last updated timestamp

### 4.4 Route Analytics Tests
- [ ] Create `__tests__/RouteAnalyticsCard.test.tsx`
- [ ] Test filter controls work
- [ ] Test data loads and displays
- [ ] Test sorting columns
- [ ] Test color coding logic
- [ ] Test error and empty states
- [ ] Test refresh button
- [ ] Add MSW handlers for API mocking

## Phase 5: Generation Analytics Section

### 5.1 Create GenerationAnalyticsCard Component
- [ ] Create `frontend/src/components/analytics/GenerationAnalyticsCard.tsx`
- [ ] Add card with title "Generation Analytics"
- [ ] Add time range selector
- [ ] Add auto-refresh toggle
- [ ] Add refresh button
- [ ] Store filter state

### 5.2 Overview Stats Cards
- [ ] Create 4 mini cards in a grid:
  - Total Generations (number)
  - Success Rate (percentage)
  - Average Duration (seconds)
  - Active Users (number)
- [ ] Use Card with bold numbers and icons
- [ ] Add subtle color coding (green for good metrics)
- [ ] Add loading skeletons
- [ ] Make responsive (2x2 grid on mobile, 4x1 on desktop)

### 5.3 Detailed Charts (if generation API exists)
- [ ] Install charting library (Recharts or MUI X Charts)
- [ ] Add time-series line chart (generations over time)
- [ ] Add pie/donut chart (success vs failure)
- [ ] Add bar chart (peak usage hours)
- [ ] Add bar chart (top models)
- [ ] Configure chart colors and tooltips
- [ ] Make charts responsive
- [ ] Add chart loading states

### 5.4 Generation Analytics Data Integration
- [ ] Connect to useGenerationAnalytics hook
- [ ] Pass filter parameters
- [ ] Handle loading, error, empty states
- [ ] Format data for charts
- [ ] Add last updated timestamp
- [ ] Add manual refresh button

### 5.5 Generation Analytics Tests
- [ ] Create `__tests__/GenerationAnalyticsCard.test.tsx`
- [ ] Test overview cards render correctly
- [ ] Test charts render with data
- [ ] Test manual refresh button works
- [ ] Test time range filtering
- [ ] Test error and empty states
- [ ] Mock chart library if needed

## Phase 6: Tag Cardinality Section

### 6.1 Create TagCardinalityCard Component
- [ ] Create `frontend/src/components/analytics/TagCardinalityCard.tsx`
- [ ] Add card with title "Tag Cardinality"
- [ ] Add content source filter (All, Regular, Auto-Generated)
- [ ] Add min cardinality slider
- [ ] Add log scale toggle
- [ ] Add refresh button
- [ ] Store filter state

### 6.2 Statistics Summary
- [ ] Add stats section with key metrics:
  - Total tags
  - Tags with content
  - Most popular tag
  - Median cardinality
  - 90th percentile cardinality
- [ ] Use Grid layout for stats
- [ ] Add icons for visual interest
- [ ] Calculate stats from API data
- [ ] Add loading skeletons

### 6.3 Histogram Visualization
- [ ] Install Recharts (if not already installed)
- [ ] Create histogram component
- [ ] Define cardinality buckets (log scale):
  - 1, 2-5, 6-10, 11-25, 26-50, 51-100, 101-250, 251-500, 501-1000, 1000+
- [ ] Bin tag data into buckets
- [ ] Create bar chart with Recharts
- [ ] Add tooltips showing exact counts
- [ ] Implement log/linear scale toggle
- [ ] Add color gradient for bars
- [ ] Make chart responsive

### 6.4 Popular Tags Table
- [ ] Add Material UI Table
- [ ] Define columns: Rank, Tag Name, Content Count, Percentage
- [ ] Show top 20 tags by default
- [ ] Make tag names clickable (navigate to tag detail page)
- [ ] Add sorting capability
- [ ] Calculate percentage of total
- [ ] Add loading skeleton
- [ ] Make responsive

### 6.5 Tag Cardinality Data Integration
- [ ] Connect to useTagCardinality hook
- [ ] Fetch tag data with appropriate limit
- [ ] Apply filters (content source, min cardinality)
- [ ] Process data for histogram binning
- [ ] Process data for popular tags table
- [ ] Handle loading, error, empty states
- [ ] Add last updated timestamp
- [ ] Persist filter preferences in localStorage

### 6.6 Tag Cardinality Tests
- [ ] Create `__tests__/TagCardinalityCard.test.tsx`
- [ ] Test statistics calculation
- [ ] Test histogram renders
- [ ] Test log scale toggle
- [ ] Test filters work (content source, min cardinality)
- [ ] Test popular tags table
- [ ] Test tag name links navigate correctly
- [ ] Test error and empty states
- [ ] Test filter persistence in localStorage

## Phase 7: Polish & Optimization

### 7.1 Accessibility
- [ ] Add ARIA labels to all interactive elements
- [ ] Ensure proper heading hierarchy (h1, h2, h3)
- [ ] Add text alternatives for charts
- [ ] Test keyboard navigation
- [ ] Test with screen reader
- [ ] Run jest-axe accessibility tests
- [ ] Fix any violations found
- [ ] Check color contrast in both themes

### 7.2 Performance Optimization
- [ ] Lazy load charting library with React.lazy()
- [ ] Add code splitting for AnalyticsPage
- [ ] Memoize expensive computations (histogram binning)
- [ ] Use React.memo for chart components
- [ ] Debounce filter inputs (500ms)
- [ ] Virtualize long lists if needed
- [ ] Optimize bundle size
- [ ] Check performance with React DevTools Profiler

### 7.3 Error Handling & Edge Cases
- [ ] Test with no data scenarios
- [ ] Test with API timeout
- [ ] Test with malformed API responses
- [ ] Test with very large datasets
- [ ] Test with slow network (throttling)
- [ ] Add error boundaries for chart failures
- [ ] Add retry logic for failed requests
- [ ] Show user-friendly error messages

### 7.4 Visual Polish
- [ ] Ensure consistent spacing using theme spacing
- [ ] Use consistent colors from theme palette
- [ ] Add subtle animations (fade in, slide in)
- [ ] Test in both light and dark modes
- [ ] Test on various screen sizes
- [ ] Add loading transitions
- [ ] Polish typography (sizes, weights)
- [ ] Add helpful empty states with illustrations/icons

### 7.5 Documentation
- [ ] Add JSDoc comments to all components
- [ ] Document props interfaces
- [ ] Add usage examples in comments
- [ ] Update `analytics-frontend.md` with implementation notes
- [ ] Document any deviations from spec
- [ ] Add comments explaining complex logic (histogram binning)
- [ ] Document data refresh strategies

## Phase 8: Testing & Quality Assurance

### 8.1 Unit Tests
- [ ] Ensure >90% coverage for all components
- [ ] Test all filter interactions
- [ ] Test data transformations
- [ ] Test error handling
- [ ] Test loading states
- [ ] Add snapshot tests for static content
- [ ] Run: `make frontend-test-unit`

### 8.2 Integration Tests
- [ ] Test data fetching with MSW
- [ ] Test React Query cache behavior
- [ ] Test component integration (page + cards)
- [ ] Test navigation flow
- [ ] Test error recovery

### 8.3 E2E Tests
- [ ] Create `frontend/tests/e2e/analytics.spec.ts`
- [ ] Test navigation to Analytics page:
  - From sidebar
  - From Settings page
- [ ] Test route analytics section:
  - Filter changes
  - Data loads and displays
  - Sort columns
  - Filter persistence across page reloads
- [ ] Test generation analytics section:
  - Manual refresh button
  - Time range selection
- [ ] Test tag cardinality section:
  - Histogram renders
  - Log scale toggle
  - Tag navigation
  - Filter persistence
- [ ] Test responsive behavior on mobile viewport
- [ ] Test error states and retry
- [ ] Run: `make frontend-test-e2e`

### 8.4 Cross-Browser & Device Testing
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test on mobile device (iOS)
- [ ] Test on mobile device (Android)
- [ ] Test on tablet
- [ ] Fix any browser-specific issues

### 8.5 Performance Testing
- [ ] Measure initial page load time (target: <2s)
- [ ] Measure chart render time (target: <500ms)
- [ ] Measure filter response time (should feel instant)
- [ ] Check bundle size impact
- [ ] Run Lighthouse audit
- [ ] Optimize if performance targets not met
- [ ] Consider adding @performance tag if adding performance-specific tests

## Phase 9: Final Integration & Cleanup

### 9.1 Final Testing Round
- [ ] Run all backend tests: `make test-all`
- [ ] Run all frontend unit tests: `make frontend-test-unit`
- [ ] Run all frontend E2E tests: `make frontend-test-e2e`
- [ ] Fix any failing tests
- [ ] Verify no console errors or warnings
- [ ] Check for TypeScript errors: `npm run type-check`
- [ ] Run linter: `npm run lint` and fix issues

### 9.2 Documentation Updates
- [ ] Update `README.md` if new commands added
- [ ] Update `docs/frontend/overview.md` if needed
- [ ] Ensure all code has JSDoc comments
- [ ] Mark analytics-frontend.md as implemented
- [ ] Add screenshots to spec document
- [ ] Document any known limitations

### 9.3 Code Review Checklist
- [ ] All code follows style guide
- [ ] All data-testids follow naming convention
- [ ] No hardcoded values (use theme/config)
- [ ] Error messages are user-friendly
- [ ] Loading states are implemented
- [ ] Components are properly typed
- [ ] No console.log statements left in code
- [ ] No commented-out code
- [ ] Proper use of React hooks (dependencies)

### 9.4 Deployment Readiness
- [ ] Feature works with real API endpoints
- [ ] Feature works with empty database (no data)
- [ ] Feature works with large datasets
- [ ] No breaking changes to existing features
- [ ] All tests pass in CI pipeline (if applicable)
- [ ] Performance is acceptable
- [ ] Accessibility standards met

## Tags
(This section explains any @skipped-until-TAG annotations)

## Skipped Tests
(If any tests are skipped, document them here with reasons)

## Questions
(Document any questions that arise during implementation)

## Notes
- The generation analytics section depends on the generation analytics API existing. If it doesn't exist yet, we may need to create it first or stub out that section.
- Histogram binning logic for tag cardinality should be well-tested as it's the most complex calculation.
- No auto-refresh - data refreshes only on page reload or manual refresh button click.
- User filter preferences (time range, system type, content source) should be persisted in localStorage.
- Interactive histogram (click bars), data export, and performance alerts have been moved to separate future enhancement documents.

## Completion Criteria
This feature is complete when:
- [ ] 1. All checkboxes above are checked or marked as skipped with good reason
- [ ] 2. All tests pass (unit, integration, E2E)
- [ ] 3. No accessibility violations
- [ ] 4. Performance targets met
- [ ] 5. Code review completed
- [ ] 6. Feature deployed to demo environment
- [ ] 7. User can successfully navigate to Analytics page and view all three sections
- [ ] 8. All data displays correctly with real API data
- [ ] 9. All filters and interactions work as expected
- [ ] 10. Page is responsive on all device sizes
