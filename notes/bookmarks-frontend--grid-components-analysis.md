# Grid and Section Components Analysis

## Executive Summary
The codebase has well-structured, reusable grid components that are shared across multiple pages (Dashboard, Gallery, Generation History). The architecture follows a clear pattern of:
- Data fetching hooks (useGalleryList, useUnifiedGallery)
- Grid container (GridView)
- Grid cell (ImageGridCell)
- Shared utility components (ResolutionDropdown)

**Recommendation for Bookmarks**: Leverage existing GridView and ImageGridCell components with a new useBookmarkedItems hook. Minimal new component creation needed.

---

## Component File Paths

### Core Grid Components
- `/Users/joeflack4/projects/genonaut/frontend/src/components/gallery/GridView.tsx`
- `/Users/joeflack4/projects/genonaut/frontend/src/components/gallery/ImageGridCell.tsx`
- `/Users/joeflack4/projects/genonaut/frontend/src/components/gallery/ResolutionDropdown.tsx`
- `/Users/joeflack4/projects/genonaut/frontend/src/components/gallery/index.ts` (exports)

### Page Components Using Grids
- `/Users/joeflack4/projects/genonaut/frontend/src/pages/dashboard/DashboardPage.tsx`
- `/Users/joeflack4/projects/genonaut/frontend/src/pages/gallery/GalleryPage.tsx`
- `/Users/joeflack4/projects/genonaut/frontend/src/components/generation/GenerationHistory.tsx` (tab component)

### Data Hooks
- `/Users/joeflack4/projects/genonaut/frontend/src/hooks/useGalleryList.ts`
- `/Users/joeflack4/projects/genonaut/frontend/src/hooks/useUnifiedGallery.ts`
- `/Users/joeflack4/projects/genonaut/frontend/src/hooks/useGalleryAutoList.ts`

### Services
- `/Users/joeflack4/projects/genonaut/frontend/src/services/gallery-service.ts`
- `/Users/joeflack4/projects/genonaut/frontend/src/services/unified-gallery-service.ts`

### Types & Constants
- `/Users/joeflack4/projects/genonaut/frontend/src/types/domain.ts`
- `/Users/joeflack4/projects/genonaut/frontend/src/constants/gallery.ts`

---

## Component Composition & Architecture

### 1. GridView Component
**File**: `GridView.tsx`
**Purpose**: Responsive grid container for displaying collections of items

**Props**:
```typescript
interface GridViewProps {
  items: GalleryItem[]
  resolution: ThumbnailResolution
  isLoading?: boolean
  onItemClick?: (item: GalleryItem) => void
  emptyMessage?: string
  loadingPlaceholderCount?: number
  dataTestId?: string
}
```

**Key Features**:
- Responsive auto-fill grid layout
- Skeleton loading states with customizable count
- Empty state handling
- Uses `ImageGridCell` for each item
- Aspect ratio maintained via padding-top percentage trick

**Usage Pattern** (from Dashboard):
```typescript
<GalleryGridView
  items={userRecentGallery?.items ?? []}
  resolution={currentResolution}
  isLoading={userRecentGalleryLoading}
  onItemClick={navigateToDetail}
  loadingPlaceholderCount={3}
  dataTestId="dashboard-user-recent-grid"
  emptyMessage="No recent gens available."
/>
```

---

### 2. ImageGridCell Component
**File**: `ImageGridCell.tsx`
**Purpose**: Individual grid cell displaying a gallery item with image and metadata

**Props**:
```typescript
interface ImageGridCellProps {
  item: GalleryItem
  resolution: ThumbnailResolution
  onClick?: (item: GalleryItem) => void
  dataTestId?: string
}
```

**Key Features**:
- ButtonBase wrapper for clickability and accessibility
- Image loading with fallback placeholder (InsertPhotoIcon)
- Error handling for failed image loads
- Shows title and creation date
- Hover effects (translateY, shadow)
- Multiple data-testid attributes for detailed testing

**Data Displayed**:
```
- item.title (caption)
- item.createdAt (localized date)
- item thumbnail image (from various sources)
```

**Image Resolution Support**:
- Primary: `item.pathThumbsAltRes[resolution.id]`
- Fallback: `item.pathThumb`
- Last resort: `item.imageUrl`

---

### 3. ResolutionDropdown Component
**File**: `ResolutionDropdown.tsx`
**Purpose**: Dropdown menu for selecting thumbnail grid resolution

**Props**:
```typescript
interface ResolutionDropdownProps {
  currentResolution: ThumbnailResolutionId
  onResolutionChange: (resolution: ThumbnailResolutionId) => void
  dataTestId?: string
  disabled?: boolean
}
```

**Available Resolutions** (from constants/gallery.ts):
```
512x768, 460x691, 410x614, 358x538, 307x461, 
256x384 (default), 232x344, 200x304, 184x272, 152x232
```

---

## Data Flow Architecture

### Dashboard Page
**Sections** (4 Cards, each with grid + list view):
1. "Your recent gens" - Regular user content (limit: 5)
2. "Your recent auto-gens" - Auto-generated content (limit: 5)
3. "Community recent gens" - Community content (limit: 5, excludes user's own)
4. "Community recent auto-gens" - Community auto content (limit: 5)

**Data Fetching**:
```typescript
// Hook usage example
const { data: userRecentGallery, isLoading: userRecentGalleryLoading } = useGalleryList({
  limit: 5,
  sort: 'recent',
  creator_id: userId,
})
```

**View Mode Persistence**:
- Stored in localStorage with key: `'dashboard-view-mode'`
- Format: `'list'` or `'grid-{resolutionId}'`
- Default: `'grid-256x384'`

---

### Gallery Page
**Single unified view with advanced filtering**:
- Search (by prompt & title)
- Sort (recent, top-rated)
- Content toggles (your gens, your auto-gens, community, community auto)
- Tag filtering
- Pagination or virtual scrolling

**Data Fetching**:
```typescript
const { data: unifiedData, isLoading } = useUnifiedGallery({
  page: filters.page + 1,
  pageSize: useVirtualScrolling ? 100 : 25,
  cursor: filters.cursor,
  contentSourceTypes: ['user-regular', 'community-auto', ...],
  userId,
  searchTerm: filters.search,
  sortField: 'created_at' | 'quality_score',
  sortOrder: 'desc',
  tag: selectedTags,
  includeStats: false,  // Lazy load stats
})
```

**View Mode Persistence**:
- Stored in localStorage with key: `'gallery-view-mode'`
- Default: `'grid-256x384'`

**URL Parameter Sync**:
- Search: `?search=term`
- Cursor: `?cursor=value`
- Tags: `?tags=tag1,tag2`
- Content toggles: `?notGenSource=your-g,comm-ag`

---

### Generation History (Tab Component)
**Purpose**: Standalone component showing user's generation jobs

**Data Fetching**:
```typescript
const response = await listGenerationJobs({
  skip: (page - 1) * pageSize,
  limit: pageSize,
  user_id: userId,
  status: statusFilter,  // Optional: pending, running, completed, failed, cancelled
})
```

**Display**:
- Uses `GenerationCard` component (similar to ImageGridCell)
- Responsive grid with auto-fill
- Supports virtual scrolling toggle
- Status badge on each card
- Delete functionality with confirmation dialog

---

## API Endpoints & Data Structures

### Gallery Service Endpoints
**Base**: `/api/v1/content`

#### List Gallery
```
GET /api/v1/content?skip=0&limit=25&search=term&sort=recent&creator_id=uuid&tag=tag_id
```

**Response** (PaginatedResult):
```typescript
{
  items: GalleryItem[],
  total: number,
  limit: number,
  skip: number
}
```

#### Enhanced Pagination
```
GET /api/v1/content/enhanced?page=1&page_size=25&cursor=value&...
```

**Response** (EnhancedPaginatedResult):
```typescript
{
  items: GalleryItem[],
  pagination: {
    page: number,
    page_size: number,
    total_count: number,
    total_pages: number,
    has_next: boolean,
    has_previous: boolean,
    next_cursor: string | null,
    prev_cursor: string | null
  }
}
```

### GalleryItem Data Structure
```typescript
interface GalleryItem {
  id: number
  title: string
  description: string | null
  imageUrl: string | null
  pathThumb: string | null
  pathThumbsAltRes: Record<string, string> | null  // {resolutionId: path}
  contentData: string | null
  contentType: string
  prompt: string | null
  qualityScore: number | null
  createdAt: string
  updatedAt: string
  creatorId: string  // UUID
  creatorUsername: string | null
  tags: string[]
  itemMetadata: Record<string, unknown> | null
  sourceType: 'regular' | 'auto'
}
```

### Unified Gallery Service
**Endpoint**: `/api/v1/content/unified` (implied via service)

**Parameters**:
- `page`, `page_size`, `cursor`: Pagination
- `content_source_types`: ['user-regular', 'user-auto', 'community-regular', 'community-auto']
- `user_id`: For user-specific filtering
- `search_term`: Full-text search
- `sort_field`: 'created_at' or 'quality_score'
- `sort_order`: 'asc' or 'desc'
- `tag`: Single tag ID or array of tag IDs
- `include_stats`: Boolean (adds 20-800ms overhead)

---

## Thumbnail & Grid Rendering Approach

### Responsive Grid Layout
```css
display: grid;
gap: 2;  /* MUI spacing: 16px */
gridTemplateColumns: repeat(auto-fill, minmax({width}px, 1fr));
alignItems: flex-start;
```

### Aspect Ratio Maintenance
**Technique**: Padding-bottom percentage hack (padding-top in this codebase)

```typescript
const aspectRatioPercentage = (resolution.height / resolution.width) * 100
// Example: 384/256 * 100 = 150%

<Box sx={{ pt: `${aspectRatioPercentage}%`, position: 'relative' }}>
  <img sx={{ position: 'absolute', inset: 0 }} />
</Box>
```

### Virtual Scrolling
- **Gallery**: Optional feature, controlled by localStorage flag
- **Generation History**: Supports virtual scrolling toggle
- **Implementation**: Custom `VirtualScrollList` component
- **Row grouping**: Items grouped by `itemsPerRow` (calculated from viewport width)
- **Row height**: Calculated as `resolution.width * aspectRatio + metadata_space + gap`

---

## Reusability Patterns

### Pattern 1: Custom Hook for Data Fetching
**Concept**: Each data source has a dedicated hook

```typescript
// useGalleryList.ts
export function useGalleryList(params: GalleryListParams = {}) {
  return useQuery<PaginatedResult<GalleryItem>>({
    queryKey: galleryListQueryKey(params),
    queryFn: () => galleryService.listGallery(params),
  })
}

// useGalleryAutoList.ts
export function useGalleryAutoList(params: GalleryListParams = {}) {
  // Similar pattern for auto-generated content
}
```

### Pattern 2: Service Layer with Transform
**Concept**: API responses (camelCase/snake_case) transformed to domain model

```typescript
private transformGalleryItem(item: ApiContentItem, sourceType): GalleryItem {
  return {
    id: item.id,
    title: item.title,
    imageUrl: item.image_url ?? null,  // Transform snake_case to camelCase
    pathThumb: item.path_thumb ?? null,
    // ...
    sourceType,
  }
}
```

### Pattern 3: View Mode Persistence
**Concept**: View preferences (list vs grid, resolution) persisted to localStorage

```typescript
const [viewMode, setViewMode] = useState<ViewMode>(() =>
  loadViewMode(DASHBOARD_VIEW_MODE_STORAGE_KEY, DEFAULT_VIEW_MODE)
)

const updateViewMode = (mode: ViewMode) => {
  setViewMode(mode)
  persistViewMode(DASHBOARD_VIEW_MODE_STORAGE_KEY, mode)
}
```

### Pattern 4: Conditional Grid vs List
**Concept**: Same data displayed in two different formats based on view mode

```typescript
{isGridView ? (
  <GalleryGridView
    items={items}
    resolution={currentResolution}
    isLoading={isLoading}
    onItemClick={navigateToDetail}
  />
) : (
  <List>
    {items.map(item => (
      <ListItem key={item.id} onClick={() => navigateToDetail(item)}>
        <ListItemText primary={item.title} />
      </ListItem>
    ))}
  </List>
)}
```

---

## Key Observations

### Strengths
1. **DRY Principle**: GridView and ImageGridCell are reused across 3+ pages
2. **Flexible Props**: Components accept callbacks for custom click handling
3. **Loading States**: Skeleton loaders matching content dimensions
4. **Accessibility**: Proper ARIA labels, semantic HTML (ButtonBase)
5. **Testing**: Comprehensive data-testid attributes for E2E testing
6. **Persistence**: View preferences stored in localStorage
7. **Responsive**: Grid adapts to viewport with `auto-fill` + `minmax()`

### Areas for Enhancement
1. **Gallery Statistics**: Lazy-loaded to avoid performance overhead
2. **Image Resolution Management**: pathThumbsAltRes keyed by resolution.id
3. **Error Handling**: Image load failures gracefully fallback to placeholder
4. **Performance**: Cursor-based pagination for large datasets (>10K items)

---

## Recommendations for Bookmarks Feature

### Architecture
1. **Create Bookmarks Service** (`/src/services/bookmarks-service.ts`)
   - Add `listBookmarkedItems(params)` method
   - Transform API responses to GalleryItem format
   - Handle both API caching and local state

2. **Create Bookmarks Hook** (`/src/hooks/useBookmarkedItems.ts`)
   - Use React Query with `useQuery`
   - Similar pattern to `useGalleryList`
   - Support pagination/cursor

3. **Reuse Existing Components**
   - Use `GridView` for grid display (NO NEW COMPONENT)
   - Use `ImageGridCell` for individual items (NO NEW COMPONENT)
   - Use `ResolutionDropdown` for resolution selection (NO NEW COMPONENT)
   - Use view mode pattern for list/grid toggle

4. **Create Bookmarks Page** (`/src/pages/bookmarks/BookmarksPage.tsx`)
   - Follow Dashboard/Gallery pattern
   - Include view mode toggle
   - Include resolution dropdown
   - Optional: Add filter/sort controls

### Code Structure
```
/src/services/bookmarks-service.ts          (NEW)
/src/hooks/useBookmarkedItems.ts             (NEW)
/src/pages/bookmarks/BookmarksPage.tsx       (NEW)
/src/pages/bookmarks/__tests__/...           (NEW)
/src/components/bookmarks/                   (OPTIONAL - if custom UI needed)
```

### Estimated Components to Create
- **Services**: 1 (bookmarks-service.ts)
- **Hooks**: 1 (useBookmarkedItems.ts)
- **Pages**: 1 (BookmarksPage.tsx)
- **Components**: 0 (reuse GridView, ImageGridCell, ResolutionDropdown)
- **Types**: Extend existing GalleryItem if needed for bookmark-specific fields

### Key Implementation Details
1. Transform bookmarked items to GalleryItem format for compatibility
2. Use same pagination pattern as Gallery (offset or cursor-based)
3. Store view mode in localStorage: `'bookmarks-view-mode'`
4. Support filtering: by creator, date range, tags
5. Optional: Add bookmark badge/icon to items in Gallery page
6. Optional: Add unbookmark action (delete from bookmarks)

---

## Testing Coverage

### Existing Component Tests
- `GridView.test.tsx` - Grid rendering, loading, empty states
- `ImageGridCell.test.tsx` - Image loading, error handling, click events
- `ResolutionDropdown.test.tsx` - Dropdown interaction, selection

### Recommended for Bookmarks
- Unit tests for bookmarks-service
- Unit tests for useBookmarkedItems hook
- E2E tests for BookmarksPage (add to bookmarks, view grid, change resolution)
- Integration tests for bookmark API calls

