# Bookmarks Phase 7 & 8 Test Plan

## Overview
This document outlines the unit tests needed for Phase 7 (Services & Hooks) and Phase 8 (Components). Tests should be written using Vitest + Testing Library following existing patterns in the codebase.

## Phase 7: Services & Hooks Tests

### 7.13 Service Transformation Logic Tests

#### File: `src/services/__tests__/bookmarks-service.test.ts`

**Test Suite: BookmarksService**

1. **transformBookmarkWithContent()**
   - Should transform API bookmark to domain model
   - Should handle null content
   - Should handle null user_rating
   - Should transform content fields correctly (snake_case to camelCase)
   - Should set default values for missing optional fields

2. **transformContentItem()**
   - Should transform API content item to GalleryItem
   - Should handle null description, imageUrl, pathThumb
   - Should default pathThumbsAltRes to null
   - Should handle missing updatedAt (use createdAt as fallback)
   - Should set creatorUsername to null (not in response)
   - Should set sourceType to 'regular'

**Mock Data:**
```typescript
const mockApiBookmarkWithContent = {
  id: 'bookmark-uuid',
  user_id: 'user-uuid',
  content_id: 123,
  content_source_type: 'items',
  note: 'Test note',
  pinned: true,
  is_public: false,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z',
  content: {
    id: 123,
    title: 'Test Image',
    description: 'Test description',
    image_url: '/path/to/image.jpg',
    path_thumb: '/path/to/thumb.jpg',
    path_thumbs_alt_res: { '184x272': '/path/184x272.jpg' },
    content_data: 'data',
    content_type: 'image',
    prompt: 'test prompt',
    quality_score: 0.85,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
    creator_id: 'creator-uuid',
    tags: ['tag1', 'tag2']
  },
  user_rating: 4
}
```

#### File: `src/services/__tests__/bookmark-categories-service.test.ts`

**Test Suite: BookmarkCategoriesService**

1. **transformCategory()**
   - Should transform API category to domain model
   - Should handle null description, color, icon
   - Should handle null coverContentId, coverContentSourceType
   - Should handle null parentId, sortIndex, shareToken
   - Should transform all fields correctly (snake_case to camelCase)

2. **createCategory() request transformation**
   - Should transform domain model to API request format
   - Should handle undefined optional fields
   - Should convert camelCase to snake_case

3. **updateCategory() request transformation**
   - Should transform partial update to API format
   - Should only include provided fields
   - Should handle undefined sortIndex

**Mock Data:**
```typescript
const mockApiCategory = {
  id: 'category-uuid',
  user_id: 'user-uuid',
  name: 'My Category',
  description: 'Category description',
  color: '#FF5733',
  icon: 'bookmark',
  cover_content_id: 456,
  cover_content_source_type: 'items',
  parent_id: 'parent-uuid',
  sort_index: 1,
  is_public: true,
  share_token: 'share-uuid',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-02T00:00:00Z'
}
```

### 7.14 Hook Tests with Mocked API

Follow pattern from existing hook tests (e.g., `useGalleryList.test.tsx`).

#### File: `src/hooks/__tests__/useBookmarkedItems.test.tsx`

**Test Suite: useBookmarkedItems**

1. **Successful data fetching**
   - Should fetch bookmarks for user
   - Should transform API response to domain models
   - Should set loading state correctly
   - Should cache results with correct query key

2. **Query key factory**
   - Should generate correct key with userId and params
   - Should include all params in key (skip, limit, pinned, etc.)
   - Should create unique keys for different param combinations

3. **Enabled condition**
   - Should not run query when userId is empty string
   - Should not run query when userId is undefined
   - Should run query when userId is provided

4. **Error handling**
   - Should handle API errors gracefully
   - Should set error state

**Mock Setup:**
```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { bookmarksService } from '../../services'

// Mock the service
vi.mock('../../services', () => ({
  bookmarksService: {
    listBookmarks: vi.fn()
  }
}))
```

#### File: `src/hooks/__tests__/useBookmarkCategories.test.tsx`

**Test Suite: useBookmarkCategories**

Same structure as useBookmarkedItems:
1. Successful data fetching
2. Query key factory
3. Enabled condition
4. Error handling

#### File: `src/hooks/__tests__/useCategoryBookmarks.test.tsx`

**Test Suite: useCategoryBookmarks**

Same structure, but test that both categoryId AND userId must be provided.

#### File: `src/hooks/__tests__/useBookmarkCategoryMutations.test.tsx`

**Test Suite: useCreateCategory**

1. **Successful creation**
   - Should call service with correct data
   - Should invalidate bookmark-categories queries
   - Should return created category

2. **Error handling**
   - Should handle validation errors
   - Should handle network errors

**Test Suite: useUpdateCategory**

1. **Successful update**
   - Should call service with categoryId, userId, and data
   - Should invalidate bookmark-categories queries
   - Should return updated category

2. **Error handling**
   - Should handle 404 errors
   - Should handle validation errors

**Test Suite: useDeleteCategory**

1. **Successful deletion**
   - Should call service with categoryId and userId
   - Should invalidate bookmark-categories queries

2. **Error handling**
   - Should handle 404 errors

**Mock Setup:**
```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { bookmarkCategoriesService } from '../../services'

vi.mock('../../services', () => ({
  bookmarkCategoriesService: {
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    deleteCategory: vi.fn()
  }
}))
```

---

## Phase 8: Component Tests

### 8.11 CategorySection Component Tests

#### File: `src/components/bookmarks/__tests__/CategorySection.test.tsx`

**Test Suite: CategorySection**

1. **Rendering**
   - Should render category name and description
   - Should render grid of bookmarks using ImageGridCell
   - Should render "More..." cell when bookmarks.length >= itemsPerPage
   - Should not render "More..." cell when bookmarks.length < itemsPerPage
   - Should render empty state when bookmarks array is empty
   - Should render loading state with skeletons

2. **Public/Private Toggle**
   - Should show PublicIcon when isPublic is true
   - Should show PublicOffIcon when isPublic is false
   - Should call onPublicToggle with correct args after 500ms debounce
   - Should not call onPublicToggle immediately on click
   - Should update icon state optimistically before API call
   - Should show correct tooltip text based on current state

3. **Edit Button**
   - Should call onEditCategory when clicked
   - Should pass category object to callback
   - Should show "Edit category" tooltip

4. **Navigation**
   - Should navigate to /bookmarks/:categoryId when "More..." clicked
   - Should use correct category ID in URL

5. **Item Click**
   - Should call onItemClick when grid item clicked
   - Should pass GalleryItem to callback

6. **Data Test IDs**
   - Should have correct data-testid on root element
   - Should have data-testid on header, toolbar, grid
   - Should have data-testid on public toggle and edit button

**Mock Data:**
```typescript
const mockCategory = {
  id: 'cat-123',
  userId: 'user-123',
  name: 'Test Category',
  description: 'Test description',
  color: null,
  icon: null,
  coverContentId: null,
  coverContentSourceType: null,
  parentId: null,
  sortIndex: null,
  isPublic: false,
  shareToken: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-02T00:00:00Z'
}

const mockBookmarks = [
  {
    id: 'bm-1',
    userId: 'user-123',
    contentId: 1,
    contentSourceType: 'items',
    note: null,
    pinned: false,
    isPublic: false,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-02T00:00:00Z',
    content: {
      id: 1,
      title: 'Image 1',
      description: null,
      imageUrl: '/image1.jpg',
      pathThumb: '/thumb1.jpg',
      pathThumbsAltRes: null,
      contentData: null,
      contentType: 'image',
      prompt: null,
      qualityScore: 0.8,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
      creatorId: 'creator-1',
      creatorUsername: null,
      tags: [],
      itemMetadata: null,
      sourceType: 'regular'
    },
    userRating: 4
  }
  // ... more bookmarks
]

const mockResolution = {
  id: '184x272',
  width: 184,
  height: 272,
  label: 'Small'
}
```

**Test Pattern:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { CategorySection } from '../CategorySection'

describe('CategorySection', () => {
  it('should render category name and description', () => {
    render(
      <BrowserRouter>
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      </BrowserRouter>
    )

    expect(screen.getByText('Test Category')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
  })

  it('should debounce public toggle by 500ms', async () => {
    const onPublicToggle = vi.fn()

    render(
      <BrowserRouter>
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onPublicToggle={onPublicToggle}
        />
      </BrowserRouter>
    )

    const toggleButton = screen.getByTestId('category-section-cat-123-public-toggle')
    fireEvent.click(toggleButton)

    // Should not call immediately
    expect(onPublicToggle).not.toHaveBeenCalled()

    // Should call after 500ms
    await waitFor(() => {
      expect(onPublicToggle).toHaveBeenCalledWith('cat-123', true)
    }, { timeout: 600 })
  })
})
```

### 8.12 CategoryFormModal Component Tests

#### File: `src/components/bookmarks/__tests__/CategoryFormModal.test.tsx`

**Test Suite: CategoryFormModal**

1. **Create Mode**
   - Should render "Create Category" title
   - Should have empty form fields
   - Should default isPublic to false
   - Should default parentId to empty
   - Should show "Create" button text

2. **Edit Mode**
   - Should render "Edit Category" title
   - Should pre-fill form with category data
   - Should show "Save" button text
   - Should update form when category prop changes

3. **Form Validation - Name**
   - Should show error when name is empty
   - Should show error when name is < 2 characters
   - Should show error when name is > 100 characters
   - Should not show error for valid name (2-100 chars)

4. **Form Validation - Description**
   - Should show error when description is > 500 characters
   - Should not show error for empty description (optional)
   - Should not show error for valid description

5. **Parent Dropdown**
   - Should show "None (Top Level)" as first option
   - Should list all available categories
   - Should filter out current category in edit mode
   - Should handle empty categories array

6. **Public Toggle**
   - Should toggle isPublic state
   - Should show explanatory text
   - Should be disabled when isSubmitting

7. **Form Submission**
   - Should call onSubmit with trimmed data
   - Should not call onSubmit if validation fails
   - Should convert empty strings to undefined for optional fields
   - Should disable form during submission

8. **Close Behavior**
   - Should call onClose when Cancel clicked
   - Should call onClose when dialog backdrop clicked
   - Should not close when isSubmitting is true
   - Should reset form when reopened in create mode

9. **Data Test IDs**
   - Should have data-testid on all form fields
   - Should have data-testid on buttons
   - Should have data-testid on parent options

**Mock Data:**
```typescript
const mockCategory = {
  id: 'cat-123',
  userId: 'user-123',
  name: 'Existing Category',
  description: 'Existing description',
  color: null,
  icon: null,
  coverContentId: null,
  coverContentSourceType: null,
  parentId: 'parent-123',
  sortIndex: null,
  isPublic: true,
  shareToken: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-02T00:00:00Z'
}

const mockCategories = [
  {
    id: 'parent-123',
    name: 'Parent Category',
    // ... other fields
  },
  {
    id: 'cat-123',
    name: 'Existing Category',
    // ... other fields (should be filtered out in edit mode)
  }
]
```

**Test Pattern:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CategoryFormModal } from '../CategoryFormModal'

describe('CategoryFormModal', () => {
  it('should validate name is required', async () => {
    const onSubmit = vi.fn()

    render(
      <CategoryFormModal
        open={true}
        onClose={vi.fn()}
        onSubmit={onSubmit}
        mode="create"
      />
    )

    const submitButton = screen.getByTestId('category-form-modal-submit-button')
    fireEvent.click(submitButton)

    expect(await screen.findByText('Category name is required')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should trim whitespace from name on submit', async () => {
    const onSubmit = vi.fn()

    render(
      <CategoryFormModal
        open={true}
        onClose={vi.fn()}
        onSubmit={onSubmit}
        mode="create"
      />
    )

    const nameInput = screen.getByTestId('category-form-modal-name-input')
    await userEvent.type(nameInput, '  Test Category  ')

    const submitButton = screen.getByTestId('category-form-modal-submit-button')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'Test Category',
        description: undefined,
        isPublic: false,
        parentId: undefined
      })
    })
  })
})
```

---

## Testing Commands

```bash
# Run all tests
npm run test

# Run specific test file
npm run test bookmarks-service.test.ts

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Notes

1. **Follow existing patterns**: Look at `useGalleryList.test.tsx` and `GridView.test.tsx` for reference
2. **Mock external dependencies**: Services should be mocked in hook tests
3. **Use Testing Library queries**: Prefer `getByRole`, `getByLabelText`, `getByTestId` in that order
4. **Test user interactions**: Use `userEvent` for realistic user interactions (typing, clicking)
5. **Test accessibility**: Ensure ARIA labels and roles are correct
6. **Debounce testing**: Use `waitFor` with appropriate timeout for debounced functions
7. **Router context**: Wrap components in `<BrowserRouter>` when they use navigation

## Deferred to Phase 11

- E2E tests with Playwright
- Integration tests with real API server
- Visual regression tests

## Database seeding
This is a critical first step before running tests. See more information in: `bookmarks-tasks.md`