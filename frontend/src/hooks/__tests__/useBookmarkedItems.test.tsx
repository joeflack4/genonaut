import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useBookmarkedItems, bookmarkedItemsQueryKey } from '../useBookmarkedItems'

vi.mock('../../services', () => {
  const listBookmarksMock = vi.fn()

  return {
    bookmarksService: {
      listBookmarks: listBookmarksMock,
    },
  }
})

const { bookmarksService } = await import('../../services')
const listBookmarksMock = vi.mocked(bookmarksService.listBookmarks)

describe('useBookmarkedItems', () => {
  beforeEach(() => {
    listBookmarksMock.mockReset()
  })

  describe('Successful data fetching', () => {
    it('should fetch bookmarks for user', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [
          {
            id: 'bookmark-1',
            userId: 'user-123',
            contentId: 1,
            contentSourceType: 'items',
            note: null,
            pinned: false,
            isPublic: false,
            createdAt: '2025-01-01T00:00:00Z',
            updatedAt: '2025-01-01T00:00:00Z',
            content: null,
            userRating: null,
          },
        ],
        total: 1,
        limit: 20,
        skip: 0,
      }

      listBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkedItems('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(listBookmarksMock).toHaveBeenCalledWith('user-123', {})
      expect(result.current.data).toEqual(response)
    })

    it('should transform API response to domain models', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [],
        total: 0,
        limit: 20,
        skip: 0,
      }

      listBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkedItems('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toBeDefined()
      expect(result.current.data?.items).toEqual([])
    })

    it('should set loading state correctly', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [],
        total: 0,
        limit: 20,
        skip: 0,
      }

      listBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkedItems('user-123'), { wrapper })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.isLoading).toBe(false)
    })

    it('should cache results with correct query key', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [],
        total: 0,
        limit: 20,
        skip: 0,
      }

      listBookmarksMock.mockResolvedValue(response)

      const params = { skip: 10, limit: 5, pinned: true }

      const { result } = renderHook(() => useBookmarkedItems('user-123', params), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const cacheData = queryClient.getQueryData(bookmarkedItemsQueryKey('user-123', params))
      expect(cacheData).toEqual(response)
    })
  })

  describe('Query key factory', () => {
    it('should generate correct key with userId and params', () => {
      const key = bookmarkedItemsQueryKey('user-123', { skip: 10, limit: 5 })
      expect(key).toEqual(['bookmarks', 'user-123', { skip: 10, limit: 5 }])
    })

    it('should include all params in key (skip, limit, pinned, etc.)', () => {
      const params = {
        skip: 10,
        limit: 5,
        pinned: true,
        isPublic: false,
        categoryId: 'cat-123',
        sortField: 'created_at' as const,
        sortOrder: 'desc' as const,
      }
      const key = bookmarkedItemsQueryKey('user-123', params)
      expect(key).toEqual(['bookmarks', 'user-123', params])
    })

    it('should create unique keys for different param combinations', () => {
      const key1 = bookmarkedItemsQueryKey('user-123', { pinned: true })
      const key2 = bookmarkedItemsQueryKey('user-123', { pinned: false })

      expect(key1).not.toEqual(key2)
    })
  })

  describe('Enabled condition', () => {
    it('should not run query when userId is empty string', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useBookmarkedItems(''), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(listBookmarksMock).not.toHaveBeenCalled()
    })

    it('should not run query when userId is undefined', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useBookmarkedItems(undefined as unknown as string), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(listBookmarksMock).not.toHaveBeenCalled()
    })

    it('should run query when userId is provided', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [],
        total: 0,
        limit: 20,
        skip: 0,
      }

      listBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkedItems('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(listBookmarksMock).toHaveBeenCalledWith('user-123', {})
    })
  })

  describe('Error handling', () => {
    it('should handle API errors gracefully', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      listBookmarksMock.mockRejectedValue(error)

      const { result } = renderHook(() => useBookmarkedItems('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should set error state', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      listBookmarksMock.mockRejectedValue(new Error('API Error'))

      const { result } = renderHook(() => useBookmarkedItems('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.isSuccess).toBe(false)
      expect(result.current.data).toBeUndefined()
    })
  })
})
