# Interactive Tag Cardinality Histogram - Future Enhancement

## Overview
Add interactivity to the tag cardinality histogram on the Analytics page, allowing users to click on histogram bars to see the specific tags within that cardinality range.

## User Story
As a system administrator or developer viewing the tag cardinality histogram, I want to click on a histogram bar to see which specific tags fall within that cardinality bucket, so that I can quickly identify and investigate tags in specific usage ranges.

## Current State
The tag cardinality histogram displays the distribution of tags across cardinality buckets in a log scale, showing how many tags have 1 item, 2-5 items, 6-10 items, etc. The histogram is read-only and does not respond to clicks.

## Proposed Enhancement

### Interaction Design
1. **Hover State**
   - When user hovers over a histogram bar, show cursor change to pointer
   - Highlight the bar with a subtle glow or color change
   - Tooltip shows: "X tags with Y-Z items - Click to view"

2. **Click Behavior**
   - When user clicks a histogram bar, open a modal or expandable panel
   - Display a list of all tags in that cardinality range
   - Show tag name, exact cardinality count, and percentage of total

3. **Tag List Modal**
   - Title: "Tags with [bucket range] items" (e.g., "Tags with 11-25 items")
   - Scrollable list if many tags
   - Columns: Tag Name, Content Count, Percentage, View Details button
   - Search/filter box to filter tags by name
   - Sort by: Name (A-Z), Count (High-Low), Percentage
   - "View Details" navigates to tag detail page
   - Close button or click outside to dismiss

4. **Empty State**
   - If a bucket has no tags, show "No tags in this range" message
   - Bar still visible but grayed out

### Technical Implementation

**Data Structure:**
```typescript
interface CardinalityBucket {
  range: string;           // "1", "2-5", "6-10", etc.
  minCardinality: number;  // 1, 2, 6, etc.
  maxCardinality: number;  // 1, 5, 10, etc.
  count: number;           // Number of tags in this bucket
  tags: TagDetail[];       // Array of tags in this bucket
}

interface TagDetail {
  id: string;
  name: string;
  cardinality: number;
  percentage: number;
}
```

**Component Structure:**
- `TagCardinalityHistogram` (existing) - add onClick handler to bars
- `TagBucketModal` (new) - modal showing tags in clicked bucket
- `TagBucketList` (new) - list component with search/sort

**API Considerations:**
- Current API: `GET /api/v1/tags/popular` returns tags sorted by cardinality
- May need to fetch ALL tags (not just top 100) to bin them correctly
- OR create new endpoint: `GET /api/v1/tags/by-cardinality-range?min=6&max=10`
- Consider pagination for large buckets (100+ tags)

**State Management:**
```typescript
const [selectedBucket, setSelectedBucket] = useState<CardinalityBucket | null>(null);
const [bucketModalOpen, setBucketModalOpen] = useState(false);
```

**Performance Considerations:**
- Lazy load tag details when bucket is clicked (don't fetch all tags upfront)
- Cache bucket data in React Query
- Virtualize list if bucket has 100+ tags
- Debounce search input

### UX Flow

1. User views tag cardinality histogram
2. User hovers over "26-50" bucket bar
3. Tooltip shows: "15 tags with 26-50 items - Click to view"
4. User clicks the bar
5. Modal opens showing list of 15 tags
6. Modal title: "Tags with 26-50 items"
7. User sees:
   - fantasy_art (47 items, 2.3%)
   - digital_painting (43 items, 2.1%)
   - character_design (38 items, 1.9%)
   - etc.
8. User clicks "View Details" on "fantasy_art"
9. Modal closes, navigates to tag detail page

### Accessibility
- Histogram bars should have ARIA labels: "Bar representing X tags with Y-Z items"
- Add keyboard support: Tab to bars, Enter/Space to open modal
- Modal should trap focus while open
- Escape key closes modal
- Screen reader announces: "Modal opened showing tags with [range] items"
- Tag list should be announced as a list with count

### Visual Design
- Modal uses Material UI Dialog component
- Consistent with app's light/dark theme
- Modal width: 600px on desktop, full screen on mobile
- List items have subtle hover state
- Tag names are links (blue, underlined on hover)
- Percentage shown in lighter text color

### Testing Requirements
- Unit test: Click handler triggers modal open
- Unit test: Modal displays correct tags for bucket
- Unit test: Search filters tags correctly
- Unit test: Sort changes tag order
- Integration test: Click bar -> modal opens -> data loads
- E2E test: Full interaction flow with real API
- Accessibility test: Keyboard navigation and screen reader

### API Changes Needed

**Option 1: Fetch all tags and bin client-side**
- Use existing `GET /api/v1/tags/popular?limit=1000`
- Bin tags into buckets on client
- Pros: No API changes needed
- Cons: Could be slow if thousands of tags

**Option 2: New endpoint for bucket data**
- `GET /api/v1/tags/by-cardinality-range?min=26&max=50`
- Returns tags in that specific range
- Pros: Efficient, only fetch what's needed
- Cons: Requires new backend endpoint

**Recommendation:** Start with Option 1, add Option 2 if performance becomes an issue.

### Dependencies
- Material UI Dialog component
- React Query for data fetching
- Parent Analytics page must be implemented first

### Success Metrics
- Histogram bars are clickable and show visual feedback
- Modal opens within 300ms of click
- Tag list loads within 500ms
- Search results appear instantly (<100ms)
- Zero accessibility violations
- Works on mobile and desktop

### Future Enhancements (beyond this task)
- Deep linking: URL param to auto-open specific bucket
- Export bucket data as CSV
- Compare two buckets side-by-side
- Show trend (how bucket has changed over time)
- Filter tags by other criteria (auto vs regular, active vs inactive)

### Estimated Effort
- Frontend component development: 4-6 hours
- API endpoint (if needed): 2-3 hours
- Testing (unit + E2E): 2-3 hours
- Polish and accessibility: 1-2 hours
- **Total: 9-14 hours**

### Priority
**Medium** - Nice-to-have enhancement that improves usability but not critical for initial Analytics page launch.
