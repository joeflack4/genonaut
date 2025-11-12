# Grid Component Architecture Diagram

## High-Level Component Hierarchy

```
Pages (Dashboard, Gallery, Bookmarks)
    |
    +-- Header with View Toggle & Resolution Dropdown
    |
    +-- Card / Container
        |
        +-- GridView (if grid mode)
        |   |
        |   +-- ImageGridCell (for each item)
        |   |   |
        |   |   +-- ButtonBase (clickable wrapper)
        |   |   +-- Image (with fallback)
        |   |   +-- Title + Date (metadata)
        |   |
        |   +-- Skeleton loaders (while loading)
        |   +-- Empty state message
        |
        +-- List (if list mode)
            |
            +-- ListItem (for each item)
                |
                +-- ListItemButton
                +-- ListItemText
```

## Data Flow Diagram

```
User Action (click item)
    |
    v
Page Component State
(viewMode, filters, resolution)
    |
    v
Custom Hook (useGalleryList, useBookmarkedItems)
(React Query with caching)
    |
    v
Service Layer (galleryService, bookmarksService)
(API client, response transformation)
    |
    v
API Endpoint (/api/v1/content, /api/v1/bookmarks)
    |
    v
Database (content_items, bookmarks)


Response Flow (Reverse):
Database
    |
    v
API Response (snake_case JSON)
    |
    v
Service Transform (to camelCase GalleryItem)
    |
    v
Hook Returns (cached PaginatedResult<GalleryItem>)
    |
    v
Page receives items[] + loading state
    |
    v
Page passes to GridView component
    |
    v
GridView renders ImageGridCell for each item
    |
    v
User sees grid of images + metadata
```

## Component Reuse Matrix for Bookmarks

```
Existing Components (REUSE)        ->  Bookmarks Feature
====================================================

GridView                           ->  Bookmarks grid layout
ImageGridCell                      ->  Bookmark item cards
ResolutionDropdown                 ->  Resolution selector
View Mode Toggle Pattern           ->  Grid/List toggle
localStorage persistence pattern   ->  Store bookmarks view mode

    |
    v

NEW COMPONENTS (CREATE)
====================================================

BookmarksService                   ->  API interaction
useBookmarkedItems Hook            ->  Data fetching
BookmarksPage                      ->  Page container
useAddBookmark Mutation             ->  Add bookmark mutation
useRemoveBookmark Mutation          ->  Remove bookmark mutation
```

## Composition Comparison

### Dashboard Page Structure
```
DashboardPage
  |
  +-- Header (Title + View Toggle + Resolution)
  |
  +-- Stat Cards Grid (4 cards)
  |   +-- Card 1: "Your recent gens"
  |   +-- Card 2: "Your recent auto-gens"
  |   +-- Card 3: "Community recent gens"
  |   +-- Card 4: "Community recent auto-gens"
  |
  Each Card contains:
  |
  +-- {isGridView ? (
  |     <GridView items={data} ... />
  |   ) : (
  |     <List items={data} ... />
  |   )}
```

### Gallery Page Structure
```
GalleryPage
  |
  +-- Header (Title + View Toggle + Resolution + Options Icon)
  |
  +-- Results Card
  |   |
  |   +-- {useVirtualScrolling ? (
  |   |     <VirtualScrollList ... />
  |   |   ) : (
  |   |     <GridView items={data} ... />
  |   |   )}
  |
  +-- Pagination (if not virtual scrolling)
  |
  +-- Options Drawer (persistent sidebar)
      |
      +-- Search
      +-- Sort dropdown
      +-- Content toggles
      +-- Tag filter
      +-- Virtual scrolling toggle
```

### Bookmarks Page Structure (RECOMMENDED)
```
BookmarksPage
  |
  +-- Header (Title + View Toggle + Resolution)
  |
  +-- Filters Card (optional)
  |   +-- Search
  |   +-- Sort dropdown
  |   +-- Filter by creator/tags (optional)
  |
  +-- Results Card
      |
      +-- <GridView items={bookmarks} ... />
      |   or
      +-- <List items={bookmarks} ... />
  |
  +-- Pagination
```

## Data Transformation Pipeline

### Gallery Item Transformation
```
API Response (ApiContentItem)
{
  id: 123,
  title: "My Image",
  image_url: "https://...",
  path_thumb: "/thumbs/123.jpg",
  path_thumbs_alt_res: {
    "512x768": "/thumbs/123_512x768.jpg",
    "256x384": "/thumbs/123_256x384.jpg"
  },
  created_at: "2024-11-11T10:00:00Z",
  creator_id: "uuid-123",
  ...snake_case_fields
}
    |
    v (transformGalleryItem)
Domain Model (GalleryItem)
{
  id: 123,
  title: "My Image",
  imageUrl: "https://...",
  pathThumb: "/thumbs/123.jpg",
  pathThumbsAltRes: {...},
  createdAt: "2024-11-11T10:00:00Z",
  creatorId: "uuid-123",
  ...camelCase_fields
}
    |
    v (Grid/List consumption)
UI Component Display
```

## State Management Pattern

### View Mode Storage
```
localStorage Key: "gallery-view-mode" | "dashboard-view-mode" | "bookmarks-view-mode"
localStorage Value: "list" | "grid-512x768" | "grid-256x384" | ...

Loading (Component Mount):
  |
  +-- Read from localStorage
  +-- Parse value
  +-- Set initial state: "grid-256x384"
  |
  v

User Interaction (clicks Grid/List button or Resolution):
  |
  +-- Update React state
  +-- Persist to localStorage
  +-- Component re-renders with new view mode
  |
  v

Refresh Page:
  |
  +-- Component mounts
  +-- Reads from localStorage
  +-- Same view mode restored
```

### Filter State Pattern
```
GalleryPage Filters:
{
  search: string (from URL ?search=term)
  sort: 'recent' | 'top-rated'
  page: number
  cursor: string | undefined
}

User changes search/sort/filters:
  |
  v
setState(filters)
  |
  v
React Query query key changes
  |
  v
useUnifiedGallery hook re-runs
  |
  v
API called with new params
  |
  v
Results updated on page
```

## Performance Patterns

### Skeleton Loading
```
GridView Component:
  |
  +-- isLoading = true
      |
      +-- Render 6 (or N) skeleton items
      +-- Each skeleton maintains aspect ratio
      +-- Creates perception of fast loading
      |
      v
  |
  +-- isLoading = false
      |
      +-- Replace skeletons with actual ImageGridCell components
```

### Lazy Stats Loading (Gallery Page)
```
Gallery Page Initial Load:
  |
  +-- Query 1: useUnifiedGallery (includeStats: false)
      |
      +-- Returns items quickly (~200ms)
      +-- No stats overhead
  |
  v

User hovers stats button:
  |
  +-- Query 2: useUnifiedGallery (includeStats: true)
      |
      +-- Loads stats in background (~800ms)
      +-- User already seeing results
      +-- Stats appear when ready (Popper)
```

### Virtual Scrolling (Optional)
```
Gallery Page with Virtual Scrolling:
  |
  +-- Items grouped into rows (itemsPerRow = 4)
  +-- Only visible rows rendered to DOM
  +-- Off-screen rows not rendered (huge performance gain)
  +-- Overscan = 2 (render 2 extra rows for smooth scrolling)
  |
  v

Container Height Calculation:
  |
  +-- rowHeight = (resolution.width * aspectRatio) + metadata_space + gap
  +-- totalHeight = rowHeight * numberOfRows
  +-- VirtualScrollList handles rendering
```

## API Response Shapes

### Paginated Result
```typescript
interface PaginatedResult<T> {
  items: T[]              // Array of items
  total: number           // Total count in database
  limit: number           // Items per page requested
  skip: number            // Offset used
}

Example:
{
  items: [GalleryItem, GalleryItem, ...],
  total: 1423,
  limit: 25,
  skip: 0
}
```

### Enhanced Paginated Result (with cursor)
```typescript
interface EnhancedPaginatedResult<T> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total_count: number
    total_pages: number
    has_next: boolean
    has_previous: boolean
    next_cursor: string | null    // For next page query
    prev_cursor: string | null    // For previous page query
  }
}

Example:
{
  items: [...],
  pagination: {
    page: 1,
    page_size: 25,
    total_count: 1423,
    total_pages: 57,
    has_next: true,
    has_previous: false,
    next_cursor: "eyJpZCI6IDU3NDMsICJzb3J0X2tleS..."
  }
}
```

## Resolution Sizing

```typescript
Available Resolutions (from constants/gallery.ts):

512x768   (scale: 1.0)    - Largest, fullest detail
460x691   (scale: 0.9)
410x614   (scale: 0.8)
358x538   (scale: 0.7)
307x461   (scale: 0.6)
256x384   (scale: 0.5)    - DEFAULT
232x344   (scale: 0.45)
200x304   (scale: 0.39)
184x272   (scale: 0.36)
152x232   (scale: 0.3)    - Smallest, compact view

Selected resolution determines:
  |
  +-- Grid cell width (CSS minmax in auto-fill)
  +-- Image aspect ratio maintained
  +-- Number of items per row (responsive)
  +-- Thumbnail image source (pathThumbsAltRes[resolutionId])
```

## Testing Hierarchy

```
Unit Tests (GridView, ImageGridCell, ResolutionDropdown)
  |
  +-- Component rendering
  +-- Props validation
  +-- Event handlers
  +-- Loading states
  +-- Empty states
  v

Hook Tests (useGalleryList, useBookmarkedItems)
  |
  +-- Query key generation
  +-- API call parameters
  +-- Response transformation
  +-- Error handling
  v

Page Tests (GalleryPage, BookmarksPage)
  |
  +-- View mode persistence
  +-- Filter handling
  +-- Grid/List toggle
  +-- Resolution changes
  +-- Pagination
  v

E2E Tests (Playwright)
  |
  +-- User workflows
  +-- Navigation
  +-- Search/filter functionality
  +-- Grid display
  +-- Responsive layout
```

