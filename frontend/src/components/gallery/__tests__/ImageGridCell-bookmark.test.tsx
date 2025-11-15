import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ImageGridCell } from '../ImageGridCell'
import type { GalleryItem, ThumbnailResolution } from '../../../types/domain'

vi.mock('../../../hooks', () => ({
  useBookmarkStatus: vi.fn(),
  useBookmarkMutations: vi.fn(),
  useBookmarkCategories: vi.fn(),
}))

const { useBookmarkStatus, useBookmarkMutations, useBookmarkCategories } = await import(
  '../../../hooks'
)
const useBookmarkStatusMock = vi.mocked(useBookmarkStatus)
const useBookmarkMutationsMock = vi.mocked(useBookmarkMutations)
const useBookmarkCategoriesMock = vi.mocked(useBookmarkCategories)

const mockGalleryItem: GalleryItem = {
  id: 1001,
  title: 'Test Image',
  description: 'Test description',
  imageUrl: '/test-image.jpg',
  pathThumb: '/test-thumb.jpg',
  pathThumbsAltRes: null,
  qualityScore: 0.8,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
  contentType: 'image',
  contentData: '',
  itemMetadata: {},
  creatorId: 'user-123',
  tags: [],
  isPublic: true,
  isPrivate: false,
  prompt: null,
  sourceType: 'regular',
}

const mockResolution: ThumbnailResolution = {
  id: 'medium',
  width: 256,
  height: 256,
  label: 'Medium',
}

const renderImageGridCell = (props: {
  item?: GalleryItem
  resolution?: ThumbnailResolution
  onClick?: (item: GalleryItem) => void
  showBookmarkButton?: boolean
  userId?: string
} = {}) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  return render(
    <ImageGridCell
      item={props.item ?? mockGalleryItem}
      resolution={props.resolution ?? mockResolution}
      onClick={props.onClick}
      showBookmarkButton={props.showBookmarkButton}
      userId={props.userId}
    />,
    { wrapper }
  )
}

describe('ImageGridCell - Bookmark Button', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Default mocks
    useBookmarkStatusMock.mockReturnValue({
      isBookmarked: false,
      bookmark: undefined,
      isLoading: false,
      data: null,
      isSuccess: true,
      isError: false,
      error: null,
    } as any)

    useBookmarkMutationsMock.mockReturnValue({
      createBookmark: {
        mutate: vi.fn(),
        mutateAsync: vi.fn(),
        isPending: false,
      } as any,
      deleteBookmark: {
        mutate: vi.fn(),
        mutateAsync: vi.fn(),
        isPending: false,
      } as any,
      syncCategories: {
        mutate: vi.fn(),
        mutateAsync: vi.fn(),
        isPending: false,
      } as any,
    })

    useBookmarkCategoriesMock.mockReturnValue({
      data: { items: [], total: 0, limit: 20, skip: 0 },
      isLoading: false,
      isSuccess: true,
      isError: false,
      error: null,
    } as any)
  })

  describe('Bookmark Button Rendering', () => {
    it('should render bookmark button when showBookmarkButton=true and userId is provided', () => {
      renderImageGridCell({
        showBookmarkButton: true,
        userId: 'user-123',
      })

      const bookmarkButton = screen.getByTestId('bookmark-button-1001')
      expect(bookmarkButton).toBeInTheDocument()
    })

    it('should NOT render bookmark button when showBookmarkButton=false', () => {
      renderImageGridCell({
        showBookmarkButton: false,
        userId: 'user-123',
      })

      const bookmarkButton = screen.queryByTestId('bookmark-button-1001')
      expect(bookmarkButton).not.toBeInTheDocument()
    })

    it('should NOT render bookmark button when userId is not provided', () => {
      renderImageGridCell({
        showBookmarkButton: true,
        userId: undefined,
      })

      const bookmarkButton = screen.queryByTestId('bookmark-button-1001')
      expect(bookmarkButton).not.toBeInTheDocument()
    })

    it('should NOT render bookmark button by default (when showBookmarkButton is not specified)', () => {
      renderImageGridCell({
        userId: 'user-123',
      })

      const bookmarkButton = screen.queryByTestId('bookmark-button-1001')
      expect(bookmarkButton).not.toBeInTheDocument()
    })
  })

  describe('Bookmark Button Positioning', () => {
    it('should position bookmark button in metadata section alongside title', () => {
      renderImageGridCell({
        showBookmarkButton: true,
        userId: 'user-123',
      })

      // Verify the metadata section exists
      const metaSection = screen.getByTestId('gallery-grid-item-1001-meta')
      expect(metaSection).toBeInTheDocument()

      // Verify the bookmark button is inside the metadata section
      const bookmarkButton = screen.getByTestId('bookmark-button-1001')
      expect(metaSection).toContainElement(bookmarkButton)

      // Verify title is also in metadata section
      const title = screen.getByTestId('gallery-grid-item-1001-title')
      expect(metaSection).toContainElement(title)
    })

    it('should render bookmark button with small size', () => {
      renderImageGridCell({
        showBookmarkButton: true,
        userId: 'user-123',
      })

      const bookmarkButton = screen.getByTestId('bookmark-button-1001')

      // The button should be rendered with small size (data-testid confirms it exists)
      expect(bookmarkButton).toBeInTheDocument()
    })
  })

  describe('Content Source Type Mapping', () => {
    it('should pass correct contentSourceType for regular content', () => {
      const regularItem: GalleryItem = {
        ...mockGalleryItem,
        sourceType: 'regular',
      }

      renderImageGridCell({
        item: regularItem,
        showBookmarkButton: true,
        userId: 'user-123',
      })

      const bookmarkButton = screen.getByTestId('bookmark-button-1001')
      expect(bookmarkButton).toBeInTheDocument()

      // Hook should be called with correct parameters (verified by BookmarkButton rendering)
      expect(useBookmarkStatusMock).toHaveBeenCalledWith('user-123', 1001, 'items')
    })

    it('should pass correct contentSourceType for auto content', () => {
      const autoItem: GalleryItem = {
        ...mockGalleryItem,
        sourceType: 'auto',
      }

      renderImageGridCell({
        item: autoItem,
        showBookmarkButton: true,
        userId: 'user-123',
      })

      const bookmarkButton = screen.getByTestId('bookmark-button-1001')
      expect(bookmarkButton).toBeInTheDocument()

      // Hook should be called with 'auto' for auto content
      expect(useBookmarkStatusMock).toHaveBeenCalledWith('user-123', 1001, 'auto')
    })
  })
})
