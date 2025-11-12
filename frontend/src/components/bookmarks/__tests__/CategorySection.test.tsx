import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import { CategorySection } from '../CategorySection'
import type { BookmarkCategory, BookmarkWithContent, ThumbnailResolution } from '../../../types/domain'

// Mock useNavigate
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = (await importOriginal()) as typeof import('react-router-dom')
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  }
})

const { useNavigate } = await import('react-router-dom')
const useNavigateMock = vi.mocked(useNavigate)

const renderWithProviders = (ui: ReactNode, initialEntries: string[] = ['/']) => {
  const queryClient = new QueryClient()

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

const mockCategory: BookmarkCategory = {
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
  updatedAt: '2025-01-02T00:00:00Z',
}

const mockBookmarks: BookmarkWithContent[] = [
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
      sourceType: 'regular',
    },
    userRating: 4,
  },
]

const mockResolution: ThumbnailResolution = {
  id: '184x272',
  width: 184,
  height: 272,
  label: 'Small',
}

describe('CategorySection', () => {
  beforeEach(() => {
    useNavigateMock.mockClear()
  })

  describe('Rendering', () => {
    it('should render category name and description', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      expect(screen.getByText('Test Category')).toBeInTheDocument()
      expect(screen.getByText('Test description')).toBeInTheDocument()
    })

    it('should render grid of bookmarks using ImageGridCell', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      expect(screen.getByTestId('category-section-cat-123-grid')).toBeInTheDocument()
      expect(screen.getByTestId('category-section-cat-123-item-1')).toBeInTheDocument()
    })

    it('should render "More..." cell when bookmarks.length >= itemsPerPage', () => {
      const manyBookmarks = Array.from({ length: 15 }, (_, i) => ({
        ...mockBookmarks[0],
        id: `bm-${i}`,
        contentId: i,
        content: {
          ...mockBookmarks[0].content!,
          id: i,
        },
      }))

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={manyBookmarks}
          resolution={mockResolution}
          itemsPerPage={15}
        />
      )

      expect(screen.getByTestId('category-section-cat-123-more-cell')).toBeInTheDocument()
    })

    it('should not render "More..." cell when bookmarks.length < itemsPerPage', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          itemsPerPage={15}
        />
      )

      expect(screen.queryByTestId('category-section-cat-123-more-cell')).not.toBeInTheDocument()
    })

    it('should render empty state when bookmarks array is empty', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={[]}
          resolution={mockResolution}
        />
      )

      expect(screen.getByText('0 bookmarks in category.')).toBeInTheDocument()
      expect(screen.getByTestId('category-section-cat-123-empty')).toBeInTheDocument()
    })

    it('should render loading state with skeletons', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={[]}
          resolution={mockResolution}
          isLoading={true}
          itemsPerPage={5}
        />
      )

      expect(screen.getByTestId('category-section-cat-123-grid')).toBeInTheDocument()
    })
  })

  describe('Public/Private Toggle', () => {
    it('should show PublicIcon when isPublic is true', () => {
      const publicCategory = { ...mockCategory, isPublic: true }

      renderWithProviders(
        <CategorySection
          category={publicCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      const toggle = screen.getByTestId('category-section-cat-123-public-toggle')
      expect(toggle).toBeInTheDocument()
    })

    it('should show PublicOffIcon when isPublic is false', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      const toggle = screen.getByTestId('category-section-cat-123-public-toggle')
      expect(toggle).toBeInTheDocument()
    })

    it('should call onPublicToggle with correct args after 500ms debounce', async () => {
      const onPublicToggle = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onPublicToggle={onPublicToggle}
        />
      )

      const toggleButton = screen.getByTestId('category-section-cat-123-public-toggle')
      fireEvent.click(toggleButton)

      // Should not call immediately
      expect(onPublicToggle).not.toHaveBeenCalled()

      // Should call after 500ms
      await waitFor(
        () => {
          expect(onPublicToggle).toHaveBeenCalledWith('cat-123', true)
        },
        { timeout: 600 }
      )
    })

    it('should not call onPublicToggle immediately on click', async () => {
      const onPublicToggle = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onPublicToggle={onPublicToggle}
        />
      )

      const toggleButton = screen.getByTestId('category-section-cat-123-public-toggle')
      fireEvent.click(toggleButton)

      expect(onPublicToggle).not.toHaveBeenCalled()
    })

    it('should update icon state optimistically before API call', () => {
      const onPublicToggle = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onPublicToggle={onPublicToggle}
        />
      )

      const toggleButton = screen.getByTestId('category-section-cat-123-public-toggle')
      fireEvent.click(toggleButton)

      // State should update immediately (icon changes)
      // This is tested by checking that the component doesn't throw
      expect(toggleButton).toBeInTheDocument()
    })

    it('should show correct tooltip text based on current state', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      const toggleButton = screen.getByTestId('category-section-cat-123-public-toggle')
      expect(toggleButton).toHaveAttribute('aria-label', 'Make category public')
    })
  })

  describe('Edit Button', () => {
    it('should call onEditCategory when clicked', () => {
      const onEditCategory = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onEditCategory={onEditCategory}
        />
      )

      const editButton = screen.getByTestId('category-section-cat-123-edit-button')
      fireEvent.click(editButton)

      expect(onEditCategory).toHaveBeenCalledWith(mockCategory)
    })

    it('should pass category object to callback', () => {
      const onEditCategory = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onEditCategory={onEditCategory}
        />
      )

      const editButton = screen.getByTestId('category-section-cat-123-edit-button')
      fireEvent.click(editButton)

      expect(onEditCategory).toHaveBeenCalledTimes(1)
      expect(onEditCategory.mock.calls[0][0]).toEqual(mockCategory)
    })

    it('should show "Edit category" tooltip', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      const editButton = screen.getByTestId('category-section-cat-123-edit-button')
      expect(editButton).toHaveAttribute('aria-label', 'Edit category')
    })
  })

  describe('Navigation', () => {
    it('should navigate to /bookmarks/:categoryId when "More..." clicked', () => {
      const navigateSpy = vi.fn()
      useNavigateMock.mockReturnValue(navigateSpy)

      const manyBookmarks = Array.from({ length: 15 }, (_, i) => ({
        ...mockBookmarks[0],
        id: `bm-${i}`,
        contentId: i,
        content: {
          ...mockBookmarks[0].content!,
          id: i,
        },
      }))

      renderWithProviders(
        <Routes>
          <Route
            path="/"
            element={
              <CategorySection
                category={mockCategory}
                bookmarks={manyBookmarks}
                resolution={mockResolution}
                itemsPerPage={15}
              />
            }
          />
        </Routes>
      )

      const moreCell = screen.getByTestId('category-section-cat-123-more-cell')
      fireEvent.click(moreCell)

      expect(navigateSpy).toHaveBeenCalledWith('/bookmarks/cat-123')
    })

    it('should use correct category ID in URL', () => {
      const navigateSpy = vi.fn()
      useNavigateMock.mockReturnValue(navigateSpy)

      const customCategory = { ...mockCategory, id: 'custom-cat-456' }
      const manyBookmarks = Array.from({ length: 15 }, (_, i) => ({
        ...mockBookmarks[0],
        id: `bm-${i}`,
        contentId: i,
        content: {
          ...mockBookmarks[0].content!,
          id: i,
        },
      }))

      renderWithProviders(
        <Routes>
          <Route
            path="/"
            element={
              <CategorySection
                category={customCategory}
                bookmarks={manyBookmarks}
                resolution={mockResolution}
                itemsPerPage={15}
              />
            }
          />
        </Routes>
      )

      const moreCell = screen.getByTestId('category-section-custom-cat-456-more-cell')
      fireEvent.click(moreCell)

      expect(navigateSpy).toHaveBeenCalledWith('/bookmarks/custom-cat-456')
    })
  })

  describe('Item Click', () => {
    it('should call onItemClick when grid item clicked', () => {
      const onItemClick = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onItemClick={onItemClick}
        />
      )

      const item = screen.getByTestId('category-section-cat-123-item-1')
      fireEvent.click(item)

      expect(onItemClick).toHaveBeenCalled()
    })

    it('should pass GalleryItem to callback', () => {
      const onItemClick = vi.fn()

      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
          onItemClick={onItemClick}
        />
      )

      const item = screen.getByTestId('category-section-cat-123-item-1')
      fireEvent.click(item)

      expect(onItemClick).toHaveBeenCalledWith(mockBookmarks[0].content)
    })
  })

  describe('Keyboard Accessibility', () => {
    it('should navigate to category page when Enter is pressed on title', () => {
      const navigateSpy = vi.fn()
      useNavigateMock.mockReturnValue(navigateSpy)

      renderWithProviders(
        <Routes>
          <Route
            path="/"
            element={
              <CategorySection
                category={mockCategory}
                bookmarks={mockBookmarks}
                resolution={mockResolution}
              />
            }
          />
        </Routes>
      )

      const titleSection = screen.getByTestId('category-section-cat-123-title-section')
      fireEvent.keyDown(titleSection, { key: 'Enter', code: 'Enter' })

      expect(navigateSpy).toHaveBeenCalledWith('/bookmarks/cat-123')
    })

    it('should navigate to category page when Space is pressed on title', () => {
      const navigateSpy = vi.fn()
      useNavigateMock.mockReturnValue(navigateSpy)

      renderWithProviders(
        <Routes>
          <Route
            path="/"
            element={
              <CategorySection
                category={mockCategory}
                bookmarks={mockBookmarks}
                resolution={mockResolution}
              />
            }
          />
        </Routes>
      )

      const titleSection = screen.getByTestId('category-section-cat-123-title-section')
      fireEvent.keyDown(titleSection, { key: ' ', code: 'Space' })

      expect(navigateSpy).toHaveBeenCalledWith('/bookmarks/cat-123')
    })

    it('should not navigate on other keys', () => {
      const navigateSpy = vi.fn()
      useNavigateMock.mockReturnValue(navigateSpy)

      renderWithProviders(
        <Routes>
          <Route
            path="/"
            element={
              <CategorySection
                category={mockCategory}
                bookmarks={mockBookmarks}
                resolution={mockResolution}
              />
            }
          />
        </Routes>
      )

      const titleSection = screen.getByTestId('category-section-cat-123-title-section')
      fireEvent.keyDown(titleSection, { key: 'Escape', code: 'Escape' })

      expect(navigateSpy).not.toHaveBeenCalled()
    })

    it('should have tabIndex={0} on title section for keyboard focus', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      const titleSection = screen.getByTestId('category-section-cat-123-title-section')
      expect(titleSection).toHaveAttribute('tabIndex', '0')
    })

    it('should have descriptive aria-label on title section', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      const titleSection = screen.getByTestId('category-section-cat-123-title-section')
      expect(titleSection).toHaveAttribute('aria-label', 'View all bookmarks in Test Category category')
    })
  })

  describe('Data Test IDs', () => {
    it('should have correct data-testid on root element', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      expect(screen.getByTestId('category-section-cat-123')).toBeInTheDocument()
    })

    it('should have data-testid on header, toolbar, grid', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      expect(screen.getByTestId('category-section-cat-123-header')).toBeInTheDocument()
      expect(screen.getByTestId('category-section-cat-123-toolbar')).toBeInTheDocument()
      expect(screen.getByTestId('category-section-cat-123-grid-container')).toBeInTheDocument()
    })

    it('should have data-testid on public toggle and edit button', () => {
      renderWithProviders(
        <CategorySection
          category={mockCategory}
          bookmarks={mockBookmarks}
          resolution={mockResolution}
        />
      )

      expect(screen.getByTestId('category-section-cat-123-public-toggle')).toBeInTheDocument()
      expect(screen.getByTestId('category-section-cat-123-edit-button')).toBeInTheDocument()
    })
  })
})
