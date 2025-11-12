# Bookmarks Implementation Guide

Based on Grid Components Analysis - Quick Reference for Bookmarks Feature

## Reuse vs New Components Decision Matrix

| Component/Layer | Reuse? | Reason |
|---|---|---|
| **GridView** | YES - Direct reuse | Generic grid container, already used by Gallery & Dashboard |
| **ImageGridCell** | YES - Direct reuse | Generic cell renderer, works with any GalleryItem |
| **ResolutionDropdown** | YES - Direct reuse | Generic resolution selector |
| **View Mode Toggle** | YES - Use same pattern | Same localStorage-based persistence pattern |
| **useGalleryList hook** | NO - Create similar | Bookmarks need different API endpoint |
| **GalleryService** | NO - Create similar | Bookmarks need separate service layer |

## File Structure to Create

```
frontend/src/
├── services/
│   └── bookmarks-service.ts          [NEW] Service class for bookmark API calls
├── hooks/
│   └── useBookmarkedItems.ts         [NEW] React Query hook for fetching bookmarks
├── pages/bookmarks/
│   ├── BookmarksPage.tsx             [NEW] Main page component
│   └── __tests__/
│       ├── BookmarksPage.test.tsx    [NEW] Unit tests
│       └── BookmarksPage.integration.test.tsx [NEW] E2E tests (optional)
└── constants/ (optional)
    └── bookmarks.ts                  [OPTIONAL] Bookmarks-specific constants
```

## Expected Implementation Timeline

- **Services Layer**: 30-45 min
- **Hooks**: 15-20 min
- **Page Component**: 45-60 min (leveraging existing patterns)
- **Tests**: 45-60 min
- **Total**: ~3-4 hours

## Code Patterns to Follow

### 1. Bookmarks Service Pattern
```typescript
// File: services/bookmarks-service.ts

export interface BookmarkedItem {
  id: number
  content_id: number
  bookmarked_at: string
  // ... other fields
}

export type ListBookmarksParams = {
  skip?: number
  limit?: number
  search?: string
  sort?: 'recent' | 'most-bookmarked'
  creator_id?: string
  tag?: string | string[]
}

export class BookmarksService {
  private readonly api: ApiClient

  async listBookmarks(params: ListBookmarksParams = {}): Promise<PaginatedResult<GalleryItem>> {
    // 1. Build URLSearchParams
    // 2. Call API: GET /api/v1/bookmarks?...
    // 3. Transform API response to GalleryItem[] (add bookmarked_at if needed)
    // 4. Return { items, total, limit, skip }
  }

  async addBookmark(contentId: number): Promise<void> {
    // POST /api/v1/bookmarks { content_id: contentId }
  }

  async removeBookmark(contentId: number): Promise<void> {
    // DELETE /api/v1/bookmarks/{contentId}
  }

  async isBookmarked(contentId: number): Promise<boolean> {
    // GET /api/v1/bookmarks/{contentId}
  }

  private transformBookmark(item: ApiContentItem): GalleryItem {
    // Same transformation as GalleryService.transformGalleryItem()
  }
}
```

### 2. Bookmarks Hook Pattern
```typescript
// File: hooks/useBookmarkedItems.ts

export const bookmarkedItemsQueryKey = (params: ListBookmarksParams = {}) => 
  ['bookmarks', params]

export function useBookmarkedItems(params: ListBookmarksParams = {}) {
  return useQuery<PaginatedResult<GalleryItem>>({
    queryKey: bookmarkedItemsQueryKey(params),
    queryFn: () => bookmarksService.listBookmarks(params),
  })
}

export function useAddBookmark() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (contentId: number) => bookmarksService.addBookmark(contentId),
    onSuccess: () => {
      // Invalidate bookmarks cache
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
    }
  })
}

export function useRemoveBookmark() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (contentId: number) => bookmarksService.removeBookmark(contentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
    }
  })
}
```

### 3. Bookmarks Page Pattern
```typescript
// File: pages/bookmarks/BookmarksPage.tsx
// Pattern follows Dashboard/Gallery very closely

export function BookmarksPage() {
  const [viewMode, setViewMode] = useState<ViewMode>(() =>
    loadViewMode('bookmarks-view-mode', DEFAULT_VIEW_MODE)
  )

  const isGridView = viewMode.startsWith('grid-')
  const [filters, setFilters] = useState({ ... })

  const { data: bookmarks, isLoading } = useBookmarkedItems({
    skip: filters.skip,
    limit: filters.limit,
    sort: filters.sort,
    search: filters.search,
  })

  return (
    <Stack spacing={4}>
      {/* Header with view toggle & resolution dropdown */}
      <Box>
        <Typography variant="h4">My Bookmarks</Typography>
        <Stack direction="row" spacing={1}>
          {/* View toggle buttons */}
          {isGridView && <ResolutionDropdown ... />}
        </Stack>
      </Box>

      {/* Filter section (optional) */}
      <Card>
        <CardContent>
          {/* Search, sort, etc. */}
        </CardContent>
      </Card>

      {/* Grid/List view - USE EXISTING COMPONENTS */}
      <Card>
        <CardContent>
          {isGridView ? (
            <GridView
              items={bookmarks?.items ?? []}
              resolution={currentResolution}
              isLoading={isLoading}
              onItemClick={navigateToDetail}
              dataTestId="bookmarks-grid-view"
            />
          ) : (
            <List>
              {bookmarks?.items.map(item => (
                <ListItem key={item.id}>
                  {/* Same pattern as Gallery/Dashboard */}
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Pagination or Virtual scroll (optional) */}
    </Stack>
  )
}
```

## Data Transform Example

Since bookmarks API will likely return a different structure, transform to GalleryItem:

```typescript
private transformBookmark(apiItem: ApiBookmark): GalleryItem {
  // API might return: { content_id, content: {...}, bookmarked_at }
  // Transform to: GalleryItem (used by GridView)
  
  const contentItem = apiItem.content || {}
  return {
    id: contentItem.id,
    title: contentItem.title,
    description: contentItem.description ?? null,
    imageUrl: contentItem.image_url ?? null,
    pathThumb: contentItem.path_thumb ?? null,
    pathThumbsAltRes: contentItem.path_thumbs_alt_res ?? null,
    contentData: contentItem.content_data ?? null,
    contentType: contentItem.content_type,
    prompt: contentItem.prompt ?? null,
    qualityScore: contentItem.quality_score,
    createdAt: apiItem.bookmarked_at || contentItem.created_at,
    updatedAt: contentItem.updated_at,
    creatorId: contentItem.creator_id,
    creatorUsername: contentItem.creator_username ?? null,
    tags: contentItem.tags ?? [],
    itemMetadata: contentItem.item_metadata ?? null,
    sourceType: contentItem.source_type ?? 'regular',
  }
}
```

## Integration Points

### 1. Gallery Page - Add Bookmark Button
```typescript
// In ImageGridCell or a wrapper component
const { mutate: addBookmark } = useAddBookmark()

<IconButton 
  onClick={() => addBookmark(item.id)}
  size="small"
>
  <BookmarkIcon />
</IconButton>
```

### 2. Navbar/Routing
Add bookmark icon in navbar linking to `/bookmarks`

### 3. Bookmark Badge (Optional)
Show bookmark count in gallery items:
```typescript
const { data: isBookmarked } = useCheckBookmarkStatus(item.id)
{isBookmarked && <BookmarkBadge />}
```

## Testing Strategy

### Unit Tests
```typescript
// bookmarks-service.test.ts
describe('BookmarksService', () => {
  it('transforms API response to GalleryItem[]')
  it('handles pagination correctly')
  it('filters by search term')
  it('sorts by recent/most-bookmarked')
})

// useBookmarkedItems.test.ts
describe('useBookmarkedItems', () => {
  it('fetches bookmarks with correct params')
  it('returns loading state during fetch')
  it('handles API errors gracefully')
})
```

### E2E Tests
```typescript
// BookmarksPage.integration.test.ts
describe('BookmarksPage', () => {
  it('displays bookmarked items in grid view')
  it('toggles between list and grid view')
  it('changes resolution and persists to localStorage')
  it('searches bookmarks')
  it('removes bookmark from list')
})
```

## Key Things to Remember

1. **Reuse GridView & ImageGridCell** - Don't reinvent the wheel
2. **Follow existing patterns** - Look at Gallery/Dashboard for view mode, pagination, etc.
3. **Transform to GalleryItem** - All grid items must be GalleryItem interface
4. **localStorage persistence** - Store view mode with key `bookmarks-view-mode`
5. **Add data-testids** - Every section needs testid for E2E tests
6. **Lazy load if needed** - Optional: add stats/counts with lazy loading like Gallery
7. **Handle empty state** - Show meaningful message when no bookmarks

## Quick Start Checklist

- [ ] Create bookmarks-service.ts with listBookmarks(), addBookmark(), removeBookmark()
- [ ] Create useBookmarkedItems.ts hook (and useAddBookmark, useRemoveBookmark mutations)
- [ ] Create BookmarksPage.tsx following Dashboard pattern
- [ ] Copy view mode toggle & resolution dropdown logic from Gallery
- [ ] Use GridView and ImageGridCell directly (no new grid components)
- [ ] Add tests for service and hook
- [ ] Add E2E test for page
- [ ] Add route in routing config
- [ ] Add navbar link/icon to bookmarks page
- [ ] Test with browser: grid view, list view, resolution changes, search/filter

