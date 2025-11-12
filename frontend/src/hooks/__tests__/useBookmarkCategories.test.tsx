import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useBookmarkCategories, bookmarkCategoriesQueryKey } from '../useBookmarkCategories'

vi.mock('../../services', () => {
  const listCategoriesMock = vi.fn()

  return {
    bookmarkCategoriesService: {
      listCategories: listCategoriesMock,
    },
  }
})

const { bookmarkCategoriesService } = await import('../../services')
const listCategoriesMock = vi.mocked(bookmarkCategoriesService.listCategories)

describe('useBookmarkCategories', () => {
  beforeEach(() => {
    listCategoriesMock.mockReset()
  })

  describe('Successful data fetching', () => {
    it('should fetch categories for user', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [
          {
            id: 'cat-1',
            userId: 'user-123',
            name: 'Test Category',
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
        ],
        total: 1,
        limit: 20,
        skip: 0,
      }

      listCategoriesMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkCategories('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(listCategoriesMock).toHaveBeenCalledWith('user-123', {})
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

      listCategoriesMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkCategories('user-123'), { wrapper })

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

      listCategoriesMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkCategories('user-123'), { wrapper })

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

      listCategoriesMock.mockResolvedValue(response)

      const params = { skip: 10, limit: 5, isPublic: true }

      const { result } = renderHook(() => useBookmarkCategories('user-123', params), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const cacheData = queryClient.getQueryData(bookmarkCategoriesQueryKey('user-123', params))
      expect(cacheData).toEqual(response)
    })
  })

  describe('Query key factory', () => {
    it('should generate correct key with userId and params', () => {
      const key = bookmarkCategoriesQueryKey('user-123', { skip: 10, limit: 5 })
      expect(key).toEqual(['bookmark-categories', 'user-123', { skip: 10, limit: 5 }])
    })

    it('should include all params in key (skip, limit, isPublic, etc.)', () => {
      const params = {
        skip: 10,
        limit: 5,
        isPublic: true,
        parentId: 'parent-123',
        sortField: 'name' as const,
        sortOrder: 'asc' as const,
      }
      const key = bookmarkCategoriesQueryKey('user-123', params)
      expect(key).toEqual(['bookmark-categories', 'user-123', params])
    })

    it('should create unique keys for different param combinations', () => {
      const key1 = bookmarkCategoriesQueryKey('user-123', { isPublic: true })
      const key2 = bookmarkCategoriesQueryKey('user-123', { isPublic: false })

      expect(key1).not.toEqual(key2)
    })
  })

  describe('Enabled condition', () => {
    it('should not run query when userId is empty string', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useBookmarkCategories(''), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(listCategoriesMock).not.toHaveBeenCalled()
    })

    it('should not run query when userId is undefined', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(() => useBookmarkCategories(undefined as unknown as string), { wrapper })

      expect(result.current.isPending).toBe(true)
      expect(listCategoriesMock).not.toHaveBeenCalled()
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

      listCategoriesMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkCategories('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(listCategoriesMock).toHaveBeenCalledWith('user-123', {})
    })
  })

  describe('Error handling', () => {
    it('should handle API errors gracefully', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      listCategoriesMock.mockRejectedValue(error)

      const { result } = renderHook(() => useBookmarkCategories('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should set error state', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      listCategoriesMock.mockRejectedValue(new Error('API Error'))

      const { result } = renderHook(() => useBookmarkCategories('user-123'), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.isSuccess).toBe(false)
      expect(result.current.data).toBeUndefined()
    })
  })
})
