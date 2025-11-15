import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BookmarkButton } from '../BookmarkButton'
import type { Bookmark } from '../../../types/domain'

vi.mock('../../../hooks', () => ({
  useBookmarkStatus: vi.fn(),
  useBookmarkMutations: vi.fn(),
  useBookmarkCategories: vi.fn(),
}))

const { useBookmarkStatus, useBookmarkMutations, useBookmarkCategories } = await import('../../../hooks')
const useBookmarkStatusMock = vi.mocked(useBookmarkStatus)
const useBookmarkMutationsMock = vi.mocked(useBookmarkMutations)
const useBookmarkCategoriesMock = vi.mocked(useBookmarkCategories)

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

const renderBookmarkButton = (props: {
  contentId?: number
  contentSourceType?: string
  userId?: string
  size?: 'small' | 'medium' | 'large'
  showLabel?: boolean
  onBookmarkClick?: (bookmark: { id: string; isBookmarked: boolean }) => void
} = {}) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  return render(
    <BookmarkButton
      contentId={props.contentId ?? 1001}
      contentSourceType={props.contentSourceType ?? 'items'}
      userId={props.userId ?? 'user-123'}
      size={props.size}
      showLabel={props.showLabel}
      onBookmarkClick={props.onBookmarkClick}
    />,
    { wrapper }
  )
}

describe('BookmarkButton', () => {
  const mockCreateBookmark = vi.fn()
  const mockDeleteBookmark = vi.fn()
  const mockSyncCategories = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock implementations
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
        mutate: mockCreateBookmark,
        mutateAsync: vi.fn().mockResolvedValue(mockBookmark),
        isPending: false,
        isSuccess: false,
        isError: false,
      } as any,
      deleteBookmark: {
        mutate: mockDeleteBookmark,
        mutateAsync: vi.fn(),
        isPending: false,
        isSuccess: false,
        isError: false,
      } as any,
      syncCategories: {
        mutate: mockSyncCategories,
        mutateAsync: vi.fn(),
        isPending: false,
        isSuccess: false,
        isError: false,
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

  describe('Rendering - Not Bookmarked', () => {
    it('should render BookmarkBorderIcon when not bookmarked', () => {
      renderBookmarkButton()
      expect(screen.getByTestId('bookmark-icon-outline')).toBeInTheDocument()
      expect(screen.queryByTestId('bookmark-icon-filled')).not.toBeInTheDocument()
    })

    it('should show "Add bookmark" tooltip when not bookmarked', () => {
      renderBookmarkButton()
      const button = screen.getByRole('button', { name: /add bookmark/i })
      expect(button).toBeInTheDocument()
    })
  })

  describe('Rendering - Bookmarked', () => {
    beforeEach(() => {
      useBookmarkStatusMock.mockReturnValue({
        isBookmarked: true,
        bookmark: mockBookmark,
        isLoading: false,
        data: mockBookmark,
        isSuccess: true,
        isError: false,
        error: null,
      } as any)
    })

    it('should render BookmarkIcon when bookmarked', () => {
      renderBookmarkButton()
      expect(screen.getByTestId('bookmark-icon-filled')).toBeInTheDocument()
      expect(screen.queryByTestId('bookmark-icon-outline')).not.toBeInTheDocument()
    })

    it('should show "Manage bookmark" tooltip when bookmarked', () => {
      renderBookmarkButton()
      const button = screen.getByRole('button', { name: /manage bookmark/i })
      expect(button).toBeInTheDocument()
    })
  })

  describe('Click Behavior - Not Bookmarked', () => {
    it('should create bookmark when clicking while not bookmarked', async () => {
      const mockMutateAsync = vi.fn().mockResolvedValue(mockBookmark)
      useBookmarkMutationsMock.mockReturnValue({
        createBookmark: {
          mutate: mockCreateBookmark,
          mutateAsync: mockMutateAsync,
          isPending: false,
          isSuccess: false,
          isError: false,
        } as any,
        deleteBookmark: {
          mutate: mockDeleteBookmark,
          mutateAsync: vi.fn(),
          isPending: false,
          isSuccess: false,
          isError: false,
        } as any,
        syncCategories: {
          mutate: mockSyncCategories,
          mutateAsync: vi.fn(),
          isPending: false,
          isSuccess: false,
          isError: false,
        } as any,
      })

      renderBookmarkButton({ contentId: 1001, contentSourceType: 'items', userId: 'user-123' })

      const button = screen.getByRole('button', { name: /add bookmark/i })
      fireEvent.click(button)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          contentId: 1001,
          contentSourceType: 'items',
        })
      })
    })

    it('should call onBookmarkClick callback after creating bookmark', async () => {
      const onBookmarkClick = vi.fn()
      const mockMutateAsync = vi.fn().mockResolvedValue(mockBookmark)

      useBookmarkMutationsMock.mockReturnValue({
        createBookmark: {
          mutate: mockCreateBookmark,
          mutateAsync: mockMutateAsync,
          isPending: false,
          isSuccess: false,
          isError: false,
        } as any,
        deleteBookmark: {
          mutate: mockDeleteBookmark,
          mutateAsync: vi.fn(),
          isPending: false,
          isSuccess: false,
          isError: false,
        } as any,
        syncCategories: {
          mutate: mockSyncCategories,
          mutateAsync: vi.fn(),
          isPending: false,
          isSuccess: false,
          isError: false,
        } as any,
      })

      renderBookmarkButton({ onBookmarkClick })

      const button = screen.getByRole('button', { name: /add bookmark/i })
      fireEvent.click(button)

      await waitFor(() => {
        expect(onBookmarkClick).toHaveBeenCalledWith({
          id: 'bookmark-123',
          isBookmarked: true,
        })
      })
    })
  })

  describe('Click Behavior - Bookmarked', () => {
    beforeEach(() => {
      useBookmarkStatusMock.mockReturnValue({
        isBookmarked: true,
        bookmark: mockBookmark,
        isLoading: false,
        data: mockBookmark,
        isSuccess: true,
        isError: false,
        error: null,
      } as any)
    })

    it('should open modal when clicking while bookmarked', async () => {
      renderBookmarkButton()

      const button = screen.getByRole('button', { name: /manage bookmark/i })
      fireEvent.click(button)

      await waitFor(() => {
        // Modal should be rendered (it will have heading "Manage Bookmark")
        expect(screen.getByRole('heading', { name: /manage bookmark/i })).toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    it('should show CircularProgress when isLoading is true', () => {
      useBookmarkStatusMock.mockReturnValue({
        isBookmarked: false,
        bookmark: undefined,
        isLoading: true,
        data: null,
        isSuccess: false,
        isError: false,
        error: null,
      } as any)

      renderBookmarkButton()

      expect(screen.getByRole('progressbar')).toBeInTheDocument()
      expect(screen.queryByTestId('bookmark-icon-outline')).not.toBeInTheDocument()
      expect(screen.queryByTestId('bookmark-icon-filled')).not.toBeInTheDocument()
    })

    it('should disable button when loading', () => {
      useBookmarkStatusMock.mockReturnValue({
        isBookmarked: false,
        bookmark: undefined,
        isLoading: true,
        data: null,
        isSuccess: false,
        isError: false,
        error: null,
      } as any)

      renderBookmarkButton()

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })
  })
})
