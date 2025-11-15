import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BookmarkManagementModal } from '../BookmarkManagementModal'
import type { Bookmark, BookmarkCategory } from '../../../types/domain'

vi.mock('../../../hooks', () => ({
  useBookmarkCategories: vi.fn(),
  useBookmarkMutations: vi.fn(),
}))

vi.mock('../../../services', () => ({
  bookmarksService: {
    getBookmarkCategories: vi.fn(),
  },
}))

const { useBookmarkCategories, useBookmarkMutations } = await import('../../../hooks')
const { bookmarksService } = await import('../../../services')

const useBookmarkCategoriesMock = vi.mocked(useBookmarkCategories)
const useBookmarkMutationsMock = vi.mocked(useBookmarkMutations)
const getBookmarkCategoriesMock = vi.mocked(bookmarksService.getBookmarkCategories)

const mockBookmark: Bookmark = {
  id: 'bookmark-123',
  userId: 'user-123',
  contentId: 1001,
  contentSourceType: 'items',
  note: null,
  pinned: false,
  isPublic: false,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
}

const mockCategories: BookmarkCategory[] = [
  {
    id: 'cat-1',
    userId: 'user-123',
    name: 'Favorites',
    description: null,
    color: null,
    icon: null,
    coverContentId: null,
    coverContentSourceType: null,
    parentId: null,
    sortIndex: null,
    isPublic: false,
    shareToken: null,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-03T00:00:00Z',
  },
  {
    id: 'cat-2',
    userId: 'user-123',
    name: 'Animals',
    description: null,
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
  },
  {
    id: 'cat-3',
    userId: 'user-123',
    name: 'Uncategorized',
    description: null,
    color: null,
    icon: null,
    coverContentId: null,
    coverContentSourceType: null,
    parentId: null,
    sortIndex: null,
    isPublic: false,
    shareToken: null,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
  },
]

const renderModal = (props: {
  open?: boolean
  onClose?: () => void
  bookmark?: Bookmark
  userId?: string
} = {}) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  return render(
    <BookmarkManagementModal
      open={props.open ?? true}
      onClose={props.onClose ?? vi.fn()}
      bookmark={props.bookmark ?? mockBookmark}
      userId={props.userId ?? 'user-123'}
    />,
    { wrapper }
  )
}

describe('BookmarkManagementModal', () => {
  const mockSyncCategories = vi.fn()
  const mockDeleteBookmark = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Default mocks
    useBookmarkCategoriesMock.mockReturnValue({
      data: { items: mockCategories, total: 3, limit: 20, skip: 0 },
      isLoading: false,
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
        mutateAsync: mockDeleteBookmark.mockResolvedValue(undefined),
        isPending: false,
      } as any,
      syncCategories: {
        mutate: vi.fn(),
        mutateAsync: mockSyncCategories.mockResolvedValue({ items: [], total: 0 }),
        isPending: false,
      } as any,
    })

    getBookmarkCategoriesMock.mockResolvedValue(['cat-3']) // Uncategorized by default
  })

  describe('Rendering', () => {
    it('should render all modal elements correctly', async () => {
      renderModal()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /manage bookmark/i })).toBeInTheDocument()
      })

      expect(screen.getByTestId('bookmark-public-toggle')).toBeInTheDocument()
      expect(screen.getByTestId('bookmark-categories-sort-dropdown')).toBeInTheDocument()
      expect(screen.getByTestId('bookmark-categories-sort-order-toggle')).toBeInTheDocument()
      expect(screen.getByTestId('bookmark-categories-dropdown')).toBeInTheDocument()
      expect(screen.getByTestId('bookmark-remove-button')).toBeInTheDocument()
      expect(screen.getByTestId('bookmark-cancel-button')).toBeInTheDocument()
      expect(screen.getByTestId('bookmark-save-button')).toBeInTheDocument()
    })
  })

  describe('Public/Private Toggle', () => {
    it('should toggle public/private state', async () => {
      renderModal()

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-public-toggle')).toBeInTheDocument()
      })

      const toggle = screen.getByTestId('bookmark-public-toggle')
      const input = toggle.querySelector('input[type="checkbox"]') as HTMLInputElement
      expect(input.checked).toBe(false)

      fireEvent.click(input)
      expect(input.checked).toBe(true)

      fireEvent.click(input)
      expect(input.checked).toBe(false)
    })

    it('should show explanatory text about public bookmarks', async () => {
      renderModal()

      await waitFor(() => {
        expect(
          screen.getByText(/public bookmarks have not yet been implemented/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Categories Multi-Select', () => {
    it('should display categories dropdown', async () => {
      renderModal()

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-categories-dropdown')).toBeInTheDocument()
      })
    })

    it('should pre-select bookmark\'s current categories', async () => {
      getBookmarkCategoriesMock.mockResolvedValue(['cat-1', 'cat-2'])
      renderModal()

      await waitFor(() => {
        expect(getBookmarkCategoriesMock).toHaveBeenCalledWith('bookmark-123')
      })

      // Wait for categories to be selected
      await waitFor(() => {
        expect(screen.getByText('Favorites')).toBeInTheDocument()
        expect(screen.getByText('Animals')).toBeInTheDocument()
      })
    })
  })

  describe('Categories Sorting', () => {
    it('should change sort mode between Recent activity and Alphabetical', async () => {
      renderModal()

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-categories-sort-dropdown')).toBeInTheDocument()
      })

      const sortDropdown = screen.getByTestId('bookmark-categories-sort-dropdown')
      const input = sortDropdown.querySelector('input') as HTMLInputElement
      expect(input.value).toBe('updated_at')

      // Change the select value directly (simpler approach for testing)
      fireEvent.change(input, { target: { value: 'name' } })

      await waitFor(() => {
        expect(input.value).toBe('name')
      })
    })

    it('should toggle sort order when clicking sort order button', async () => {
      renderModal()

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-categories-sort-order-toggle')).toBeInTheDocument()
      })

      const sortOrderButton = screen.getByTestId('bookmark-categories-sort-order-toggle')

      // Initial state should be descending
      expect(sortOrderButton).toHaveAttribute('aria-label', 'Sort order: Descending')

      fireEvent.click(sortOrderButton)

      await waitFor(() => {
        expect(sortOrderButton).toHaveAttribute('aria-label', 'Sort order: Ascending')
      })

      fireEvent.click(sortOrderButton)

      await waitFor(() => {
        expect(sortOrderButton).toHaveAttribute('aria-label', 'Sort order: Descending')
      })
    })
  })

  describe('Save Functionality', () => {
    it('should call syncCategories with selected category IDs when saving', async () => {
      getBookmarkCategoriesMock.mockResolvedValue(['cat-3'])
      renderModal()

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-save-button')).toBeInTheDocument()
      })

      const saveButton = screen.getByTestId('bookmark-save-button')
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockSyncCategories).toHaveBeenCalledWith({
          bookmarkId: 'bookmark-123',
          categoryIds: ['cat-3'],
        })
      })
    })

    it('should close modal after successful save', async () => {
      const onClose = vi.fn()
      renderModal({ onClose })

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-save-button')).toBeInTheDocument()
      })

      const saveButton = screen.getByTestId('bookmark-save-button')
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled()
      })
    })
  })

  describe('Remove Functionality', () => {
    it('should call deleteBookmark when remove button is clicked', async () => {
      renderModal()

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-remove-button')).toBeInTheDocument()
      })

      const removeButton = screen.getByTestId('bookmark-remove-button')
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(mockDeleteBookmark).toHaveBeenCalledWith({
          bookmarkId: 'bookmark-123',
          contentId: 1001,
          contentSourceType: 'items',
        })
      })
    })

    it('should close modal after successful removal', async () => {
      const onClose = vi.fn()
      renderModal({ onClose })

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-remove-button')).toBeInTheDocument()
      })

      const removeButton = screen.getByTestId('bookmark-remove-button')
      fireEvent.click(removeButton)

      await waitFor(() => {
        expect(onClose).toHaveBeenCalled()
      })
    })
  })

  describe('Cancel Functionality', () => {
    it('should close modal when cancel button is clicked', async () => {
      const onClose = vi.fn()
      renderModal({ onClose })

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-cancel-button')).toBeInTheDocument()
      })

      const cancelButton = screen.getByTestId('bookmark-cancel-button')
      fireEvent.click(cancelButton)

      expect(onClose).toHaveBeenCalled()
    })
  })
})
