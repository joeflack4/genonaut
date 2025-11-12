import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useCategoryBookmarks, categoryBookmarksQueryKey } from '../useCategoryBookmarks'

vi.mock('../../services', () => {
  const getCategoryBookmarksMock = vi.fn()

  return {
    bookmarkCategoriesService: {
      getCategoryBookmarks: getCategoryBookmarksMock,
    },
  }
})

const { bookmarkCategoriesService } = await import('../../services')
const getCategoryBookmarksMock = vi.mocked(bookmarkCategoriesService.getCategoryBookmarks)

describe('useCategoryBookmarks', () => {
  beforeEach(() => {
    getCategoryBookmarksMock.mockReset()
  })

  describe('Successful data fetching', () => {
    it('should fetch bookmarks for category', async () => {
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

      getCategoryBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(getCategoryBookmarksMock).toHaveBeenCalledWith('cat-123', 'user-123', {})
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

      getCategoryBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123'), { wrapper })

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

      getCategoryBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123'), { wrapper })

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

      getCategoryBookmarksMock.mockResolvedValue(response)

      const params = { skip: 10, limit: 5 }

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123', params), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const cacheData = queryClient.getQueryData(categoryBookmarksQueryKey('cat-123', 'user-123', params))
      expect(cacheData).toEqual(response)
    })
  })

  describe('Query key factory', () => {
    it('should generate correct key with categoryId, userId, and params', () => {
      const key = categoryBookmarksQueryKey('cat-123', 'user-123', { skip: 10, limit: 5 })
      expect(key).toEqual(['bookmark-category-bookmarks', 'cat-123', 'user-123', { skip: 10, limit: 5 }])
    })

    it('should include all params in key', () => {
      const params = {
        skip: 10,
        limit: 5,
        sortField: 'created_at' as const,
        sortOrder: 'desc' as const,
      }
      const key = categoryBookmarksQueryKey('cat-123', 'user-123', params)
      expect(key).toEqual(['bookmark-category-bookmarks', 'cat-123', 'user-123', params])
    })

    it('should create unique keys for different param combinations', () => {
      const key1 = categoryBookmarksQueryKey('cat-123', 'user-123', { skip: 0 })
      const key2 = categoryBookmarksQueryKey('cat-123', 'user-123', { skip: 10 })

      expect(key1).not.toEqual(key2)
    })
  })

  describe('Enabled condition', () => {
    it('should not run query when categoryId is empty string', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useCategoryBookmarks('', 'user-123'), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(getCategoryBookmarksMock).not.toHaveBeenCalled()
    })

    it('should not run query when userId is empty string', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', ''), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(getCategoryBookmarksMock).not.toHaveBeenCalled()
    })

    it('should not run query when both IDs are empty', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useCategoryBookmarks('', ''), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(getCategoryBookmarksMock).not.toHaveBeenCalled()
    })

    it('should run query when both categoryId AND userId are provided', async () => {
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

      getCategoryBookmarksMock.mockResolvedValue(response)

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(getCategoryBookmarksMock).toHaveBeenCalledWith('cat-123', 'user-123', {})
    })
  })

  describe('Error handling', () => {
    it('should handle API errors gracefully', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      getCategoryBookmarksMock.mockRejectedValue(error)

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should set error state', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      getCategoryBookmarksMock.mockRejectedValue(new Error('API Error'))

      const { result } = renderHook(() => useCategoryBookmarks('cat-123', 'user-123'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.isSuccess).toBe(false)
      expect(result.current.data).toBeUndefined()
    })
  })
})
