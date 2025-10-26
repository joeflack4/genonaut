# Analytics Frontend - Specification

## Overview
Create a new frontend page to visualize system analytics data including route performance, generation metrics, and tag cardinality statistics. This page will provide developers and administrators with insights into system usage, performance patterns, and content distribution.

## User Story
As a system administrator or developer, I want to view comprehensive analytics about the application's performance and usage patterns so that I can make informed decisions about caching, optimization, and capacity planning.

## Scope
This feature adds a new "Analytics" page under the Settings area that displays:
1. Route analytics (API endpoint performance and cache priorities)
2. Generation analytics (image generation statistics and patterns)
3. Tag cardinality (content distribution across tags with histogram visualization)

## Requirements

### Navigation & Access
1. **Sidebar Integration**
   - Add "Analytics" as a sub-option under "Settings" in the sidebar
   - Only visible when Settings page is selected
   - Indented to show hierarchical relationship
   - Can be toggled on/off in Settings like other sidebar pages

2. **Route Structure**
   - Primary route: `/settings/analytics`
   - Follows existing pattern like `/settings/search-history`
   - Accessible via sidebar navigation
   - Can also be reached from Settings page via link

### Page Layout
The Analytics page will consist of a title, subtitle, and three main card sections:

```
Analytics
[subtitle explaining the purpose]

[Route Analytics Card]
  - Top routes by cache priority
  - Performance metrics table
  - Absolute vs Relative system toggle

[Generation Analytics Card]
  - Generation statistics overview
  - Success/failure rates
  - Performance trends
  - User activity patterns

[Tag Cardinality Card]
  - Tag usage statistics
  - Histogram visualization (log scale)
  - Distribution metrics
```

### Section 1: Route Analytics

**Purpose:** Display API endpoint performance metrics and identify routes that would benefit from caching.

**Data Source:** `GET /api/v1/analytics/routes/cache-priorities`

**UI Components:**
- System selector: Toggle between "Absolute" (production) and "Relative" (development) ranking
- Time range selector: 7, 14, 30, 90 days
- Top N selector: 5, 10, 20, 50 routes
- Data table with columns:
  - Rank (1, 2, 3...)
  - Method (GET, POST, etc.)
  - Route path
  - Avg Requests/Hour
  - P95 Latency (ms)
  - Unique Users
  - Priority Score
  - Success Rate (%)

**Features:**
- Sortable columns
- Color coding for high/medium/low priority
- Tooltips explaining metrics
- Refresh button to fetch latest data
- Loading skeleton during data fetch
- Error state with retry option

**Visual Design:**
- Use DataGrid or Table component from Material UI
- Highlight top 3 routes with subtle background colors
- Show latency with color gradient (green < 100ms, yellow 100-500ms, red > 500ms)
- Compact view on mobile with horizontal scroll

### Section 2: Generation Analytics

**Purpose:** Display image generation system performance and usage patterns.

**Data Source:** `GET /api/v1/analytics/generation/overview`

**UI Components:**

**Overview Cards (4 cards in a row):**
1. Total Generations
2. Success Rate (%)
3. Average Duration (seconds)
4. Active Users (last 24h)

**Detailed Stats:**
- Time-series chart showing generations over time
- Success vs Failure breakdown (pie or donut chart)
- Peak usage hours (bar chart)
- Top models by usage (bar chart)
- Average queue wait time trend

**Features:**
- Time range selector: 1 day, 7 days, 30 days
- Manual refresh button (no auto-refresh as per requirements)
- Expandable sections for detailed metrics

**Visual Design:**
- Use Card components with bold numbers
- Charts using a charting library (Recharts, Chart.js, or MUI X Charts)
- Consistent color scheme (success = green, failure = red, neutral = blue)
- Responsive grid layout that stacks on mobile

### Section 3: Tag Cardinality

**Purpose:** Visualize content distribution across tags and identify popular vs rare tags.

**Data Source:** `GET /api/v1/tags/popular?limit=100&min_cardinality=1`

**UI Components:**

**Statistics Summary:**
- Total tags in system
- Tags with content (cardinality > 0)
- Most popular tag (name + count)
- Median cardinality
- 90th percentile cardinality

**Histogram Visualization:**
- X-axis: Cardinality (log scale)
  - Buckets: 1, 2-5, 6-10, 11-25, 26-50, 51-100, 101-250, 251-500, 501-1000, 1000+
- Y-axis: Number of tags (linear scale)
- Bar chart with hover tooltips showing exact counts
- Color gradient from light to dark based on tag count

**Popular Tags Table:**
- Top 20 tags by cardinality
- Columns: Rank, Tag Name, Content Count, Percentage of Total
- Click to navigate to tag detail page

**Features:**
- Toggle between linear and log scale for histogram
- Filter by content source: All, Regular Content, Auto-Generated
- Min cardinality slider to filter rare tags

**Visual Design:**
- Use a charting library for histogram (Recharts recommended)
- Material UI Table for popular tags
- Log scale toggle as a switch with explanatory tooltip
- Color palette that works in both light and dark modes
- Responsive design that adapts chart size on mobile

## Technical Implementation Notes

### Backend APIs Already Available
- `/api/v1/analytics/routes/cache-priorities` - Route performance analytics
- `/api/v1/analytics/generation/overview` - Generation statistics (to be confirmed)
- `/api/v1/tags/popular` - Tag cardinality data

### Frontend Technologies
- React + TypeScript
- Material UI for components
- React Query for data fetching
- React Router for navigation
- Recharts or similar for visualizations

### Data Refresh Strategy
- Initial load on page mount
- Manual refresh button for all sections
- Data refreshes only on page reload or manual refresh (no auto-refresh)
- Use React Query's automatic caching and refetching
- Show last updated timestamp
- Persist user filter preferences (time range, system type, etc.) in localStorage

### Accessibility
- All charts must have text alternatives
- Keyboard navigation for all interactive elements
- ARIA labels for data visualizations
- Proper heading hierarchy (h1, h2, h3)
- Color contrast meeting WCAG AA standards
- Screen reader friendly data tables

### Performance Considerations
- Lazy load chart libraries (code splitting)
- Paginate or virtualize long lists
- Debounce filter inputs
- Show loading skeletons during data fetch
- Error boundaries for chart rendering failures
- Memoize expensive computations

### Testing Requirements
- Unit tests for all components
- Integration tests for data fetching hooks
- E2E tests for navigation and key user flows
- Snapshot tests for chart rendering
- Accessibility tests with jest-axe
- Mock API responses in tests

## User Experience Flow

### First Visit
1. User navigates to Settings page
2. Sees "Analytics" option in sidebar (indented under Settings)
3. Clicks Analytics
4. Page loads with all three sections showing loading skeletons
5. Data loads progressively (route analytics first, then others)
6. User explores different time ranges and filters

### Subsequent Visits
1. React Query cache may have recent data
2. User sees cached data immediately
3. Fresh data loads in background
4. Page updates smoothly when new data arrives

### Error Handling
1. If API fails, show error message with retry button
2. Show partial data if some endpoints succeed
3. Clear error messages explaining what went wrong
4. Option to view more details in console (for developers)

## Design Decisions

### Why Tab vs Separate Page?
**Decision:** Separate page under Settings, not tabs on Settings page.
**Rationale:**
- Analytics is substantial enough to warrant its own page
- Follows existing pattern (SearchHistoryPage)
- Easier to deep link and bookmark
- Cleaner separation of concerns
- Can add more analytics pages in future as sub-pages

### Why Hierarchical Sidebar Navigation?
**Decision:** Show as indented sub-item when Settings is active.
**Rationale:**
- Indicates parent-child relationship
- Reduces sidebar clutter
- Similar to file tree navigation patterns
- Makes it clear Analytics is settings-related

### Why Log Scale for Histogram?
**Decision:** Use log scale by default with toggle.
**Rationale:**
- Tag cardinality typically follows power law distribution
- Most tags have 1-10 items, few tags have 100+
- Log scale shows distribution more clearly
- Toggle allows users to compare both views

### Why Three Separate Sections?
**Decision:** Keep route, generation, and tag analytics separate but on same page.
**Rationale:**
- Related but distinct data sources
- Different audiences (devs vs admins)
- Easier to scan and navigate
- Can be expanded independently
- Allows for different refresh rates

## Future Enhancements (Out of Scope)
The following features have been moved to separate specification documents for future implementation:
- **Interactive histogram** - Click bars to see tags in that range (see `analytics-frontend-tags-histogram.md`)
- **Data export** - Export analytics data as CSV/JSON (see `analytics-frontend-export.md`)
- **Performance alerts** - Automated alerting for degradation (see `perf-regress-alerts.md`)

Other potential future enhancements:
- Real-time WebSocket updates for generation stats
- Drill-down views for specific routes or tags
- Historical trend analysis (weekly/monthly comparisons)
- Customizable dashboard with draggable widgets
- Comparison mode (compare two time periods)
- User-specific analytics for individual users

## Implementation Decisions

### 1. Generation Analytics Auto-Refresh
**Decision:** No auto-refresh. Data refreshes only on page reload or manual refresh button click.
**Rationale:** Reduces unnecessary API calls and simplifies implementation.

### 2. User Filter Preferences Persistence
**Decision:** Yes, persist in localStorage.
**Rationale:** Improves UX by remembering user preferences across sessions (time range, system type, content source filters).

### 3. Interactive Histogram
**Decision:** Moved to future enhancement (see `analytics-frontend-tags-histogram.md`).
**Rationale:** Adds complexity; focus on core functionality first.

### 4. Data Export Options
**Decision:** Moved to future enhancement (see `analytics-frontend-export.md`).
**Rationale:** CSV/JSON export is valuable but not critical for initial launch.

### 5. Performance Regression Alerts
**Decision:** Moved to future enhancement (see `perf-regress-alerts.md`).
**Rationale:** Requires significant backend work; separate project.


## Success Metrics
- Page loads successfully without errors
- All visualizations render correctly in light and dark mode
- Data refreshes when user changes filters
- Page is responsive on mobile devices
- No accessibility violations
- All tests pass (unit, integration, E2E)
- Loading time < 2 seconds for initial page load
- Charts render in < 500ms after data loads

## Dependencies
- Backend analytics endpoints must be functional
- Tag cardinality stats must be refreshed regularly (daily Celery job)
- Route analytics table must have data (requires traffic)
- Generation events must be tracked (requires generations)

## Deliverables
1. ✅ New `AnalyticsPage.tsx` component
2. ✅ Supporting sub-components for each section
3. ✅ React Query hooks for data fetching
4. ✅ Unit tests for components and hooks (service tests complete, component tests in progress)
5. ⏳ E2E tests for navigation and interactions (navigation tests updated, analytics-specific E2E pending)
6. ✅ Updated routing configuration
7. ⏭️ Updated sidebar navigation in AppLayout (deferred - using Settings page link instead)
8. ✅ Documentation in code (JSDoc comments)
9. ✅ Update to this spec document with implementation notes

## Implementation Notes

### Completed (As of 2025-10-24)

**Phase 1 - Foundation:**
- ✅ All API endpoints verified and tested with various query parameters
- ✅ Comprehensive TypeScript types created in `src/types/analytics.ts`
- ✅ Analytics service layer implemented with error handling
- ✅ React Query hooks created with appropriate cache configuration
- ✅ Unit tests written for service methods (12 tests passing)

**Phase 2 - Routing & Navigation:**
- ✅ Route `/settings/analytics` added to App.tsx
- ✅ Route added to E2E test suite (navigation.spec.ts)
- ✅ Analytics card added to Settings page with navigation link
- ✅ Unit tests updated for SettingsPage
- ⏭️ Hierarchical sidebar navigation deferred (using flat Settings page link instead)

**Phase 3 - Core Page Structure:**
- ✅ AnalyticsPage component created with header, refresh button, and last updated timestamp
- ✅ Three card sections (Route, Generation, Tag Cardinality) integrated
- ✅ Global refresh functionality implemented
- ✅ Unit tests created for AnalyticsPage (10 tests passing)

**Phase 4 - Route Analytics Section:**
- ✅ RouteAnalyticsCard component fully implemented
- ✅ System selector (Absolute vs Relative), time range, and top N filters
- ✅ Sortable data table with color-coded latency indicators
- ✅ Loading, error, and empty states handled
- ✅ Filter persistence via localStorage
- ✅ Unit tests created (13 tests passing)

**Phase 5 - Generation Analytics Section:**
- ✅ GenerationAnalyticsCard component fully implemented
- ✅ Four overview metric cards (Total, Success Rate, Avg Duration, Unique Users)
- ✅ Detailed statistics panel with P50/P95/P99 durations
- ✅ Time range filtering with manual refresh
- ✅ Color-coded success rate (green ≥90%, yellow <90%)
- ✅ Unit tests created (17 tests passing)

**Phase 6 - Tag Cardinality Section:**
- ✅ TagCardinalityCard component fully implemented
- ✅ Statistics summary (total tags, most popular, median, P90)
- ✅ Histogram visualization with Recharts (log/linear scale toggle)
- ✅ Popular tags table (top 20) with clickable links to tag detail pages
- ✅ Content source filtering (All, Regular, Auto-Generated)
- ✅ Filter persistence via localStorage
- ⏳ Unit tests partially created (component structure evolved, tests need updating)

### Deviations from Original Spec

1. **Sidebar Navigation**: Hierarchical sidebar navigation was deferred. Analytics page is accessible via a prominent card on the Settings page instead. This provides equivalent functionality with simpler implementation.

2. **No Auto-Refresh**: As specified, data only refreshes on manual refresh button click or page reload. This prevents unnecessary API calls and gives users control.

3. **Filter Persistence**: All filter preferences (time ranges, system types, content source) are persisted in localStorage using a custom `usePersistedState` hook. This improves UX by remembering user preferences across sessions.

### Technical Implementation Details

**Performance Optimizations:**
- Expensive computations (histogram binning, statistics calculations) use React's `useMemo` hook
- React Query provides intelligent caching (5-10 minute staleTime for analytics data)
- Filter state persisted to localStorage to avoid recalculation

**Data Refresh Strategy:**
- Manual refresh button on each card
- Global "Refresh All" button in page header that invalidates all analytics queries
- Last updated timestamp displayed at page level

**Error Handling:**
- All cards show user-friendly error alerts when API calls fail
- Empty states with helpful messages when no data available
- Loading skeletons for better perceived performance

**Responsive Design:**
- Cards stack vertically on mobile
- Tables use horizontal scroll on small screens
- Metric cards adapt from 4x1 grid (desktop) to 2x2 grid (mobile)

### Pending Work

**Phase 7 - Polish & Optimization:**
- ⏳ Lazy loading charting library (Recharts)
- ⏳ Code splitting for AnalyticsPage
- ⏳ React.memo for chart components
- ⏳ Debounce filter inputs

**Phase 8 - Testing & QA:**
- ⏳ Complete unit test coverage (>90% target)
- ⏳ E2E tests for analytics page interactions
- ⏳ Tag cardinality component tests need updating for new structure

**Phase 9 - Final Integration:**
- ⏳ Full test suite verification
- ⏳ Linting and type-check
- ⏳ Final documentation review
