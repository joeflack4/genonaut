import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useBookmarkMutations } from '../useBookmarkMutations'
import { bookmarkStatusQueryKey } from '../useBookmarkStatus'
import { bookmarkedItemsQueryKey } from '../useBookmarkedItems'
import type { Bookmark } from '../../types/domain'

vi.mock('../../services', () => {
  const createBookmarkMock = vi.fn()
  const deleteBookmarkMock = vi.fn()
  const syncCategoriesMock = vi.fn()

  return {
    bookmarksService: {
      createBookmark: createBookmarkMock,
      deleteBookmark: deleteBookmarkMock,
      syncCategories: syncCategoriesMock,
    },
  }
})

const { bookmarksService } = await import('../../services')
const createBookmarkMock = vi.mocked(bookmarksService.createBookmark)
const deleteBookmarkMock = vi.mocked(bookmarksService.deleteBookmark)
const syncCategoriesMock = vi.mocked(bookmarksService.syncCategories)

describe('useBookmarkMutations', () => {
  beforeEach(() => {
    createBookmarkMock.mockReset()
    deleteBookmarkMock.mockReset()
    syncCategoriesMock.mockReset()
  })

  describe('createBookmark mutation', () => {
    it('should create bookmark and update cache', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const newBookmark: Bookmark = {
        id: 'bookmark-1',
        userId: 'user-123',
        contentId: 1001,
        contentSourceType: 'items',
        note: null,
        pinned: false,
        isPublic: false,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      }

      createBookmarkMock.mockResolvedValue(newBookmark)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      // Spy on invalidateQueries
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

      result.current.createBookmark.mutate({
        contentId: 1001,
        contentSourceType: 'items',
      })

      await waitFor(() => expect(result.current.createBookmark.isSuccess).toBe(true))

      expect(createBookmarkMock).toHaveBeenCalledWith('user-123', 1001, 'items', {})
      expect(result.current.createBookmark.data).toEqual(newBookmark)

      // Verify cache invalidation
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: bookmarkStatusQueryKey('user-123', 1001, 'items'),
      })
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: bookmarkedItemsQueryKey('user-123'),
      })
    })

    it('should create bookmark with options', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const newBookmark: Bookmark = {
        id: 'bookmark-1',
        userId: 'user-123',
        contentId: 1001,
        contentSourceType: 'items',
        note: 'Great image!',
        pinned: true,
        isPublic: false,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      }

      createBookmarkMock.mockResolvedValue(newBookmark)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      result.current.createBookmark.mutate({
        contentId: 1001,
        contentSourceType: 'items',
        options: {
          note: 'Great image!',
          pinned: true,
          isPublic: false,
        },
      })

      await waitFor(() => expect(result.current.createBookmark.isSuccess).toBe(true))

      expect(createBookmarkMock).toHaveBeenCalledWith('user-123', 1001, 'items', {
        note: 'Great image!',
        pinned: true,
        isPublic: false,
      })
    })

    it('should handle createBookmark errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Failed to create bookmark')
      createBookmarkMock.mockRejectedValue(error)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      result.current.createBookmark.mutate({
        contentId: 1001,
        contentSourceType: 'items',
      })

      await waitFor(() => expect(result.current.createBookmark.isError).toBe(true))

      expect(result.current.createBookmark.error).toEqual(error)
    })
  })

  describe('deleteBookmark mutation', () => {
    it('should delete bookmark and update cache', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      deleteBookmarkMock.mockResolvedValue(undefined)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      // Spy on invalidateQueries
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

      result.current.deleteBookmark.mutate({
        bookmarkId: 'bookmark-1',
        contentId: 1001,
        contentSourceType: 'items',
      })

      await waitFor(() => expect(result.current.deleteBookmark.isSuccess).toBe(true))

      expect(deleteBookmarkMock).toHaveBeenCalledWith('bookmark-1', 'user-123')

      // Verify cache invalidation
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: bookmarkStatusQueryKey('user-123', 1001, 'items'),
      })
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: bookmarkedItemsQueryKey('user-123'),
      })
    })

    it('should handle deleteBookmark errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Failed to delete bookmark')
      deleteBookmarkMock.mockRejectedValue(error)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      result.current.deleteBookmark.mutate({
        bookmarkId: 'bookmark-1',
        contentId: 1001,
        contentSourceType: 'items',
      })

      await waitFor(() => expect(result.current.deleteBookmark.isError).toBe(true))

      expect(result.current.deleteBookmark.error).toEqual(error)
    })
  })

  describe('syncCategories mutation', () => {
    it('should sync categories and update cache', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [
          {
            bookmarkId: 'bookmark-1',
            categoryId: 'cat-1',
            userId: 'user-123',
            position: null,
            addedAt: '2025-01-01T00:00:00Z',
          },
        ],
        total: 1,
      }

      syncCategoriesMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      // Spy on invalidateQueries
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

      result.current.syncCategories.mutate({
        bookmarkId: 'bookmark-1',
        categoryIds: ['cat-1'],
      })

      await waitFor(() => expect(result.current.syncCategories.isSuccess).toBe(true))

      expect(syncCategoriesMock).toHaveBeenCalledWith('bookmark-1', 'user-123', ['cat-1'])

      // Verify cache invalidation
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: bookmarkedItemsQueryKey('user-123'),
      })
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['bookmark-categories'],
      })
    })

    it('should sync multiple categories', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const response = {
        items: [
          {
            bookmarkId: 'bookmark-1',
            categoryId: 'cat-1',
            userId: 'user-123',
            position: null,
            addedAt: '2025-01-01T00:00:00Z',
          },
          {
            bookmarkId: 'bookmark-1',
            categoryId: 'cat-2',
            userId: 'user-123',
            position: null,
            addedAt: '2025-01-01T00:00:00Z',
          },
        ],
        total: 2,
      }

      syncCategoriesMock.mockResolvedValue(response)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      result.current.syncCategories.mutate({
        bookmarkId: 'bookmark-1',
        categoryIds: ['cat-1', 'cat-2'],
      })

      await waitFor(() => expect(result.current.syncCategories.isSuccess).toBe(true))

      expect(syncCategoriesMock).toHaveBeenCalledWith('bookmark-1', 'user-123', ['cat-1', 'cat-2'])
      expect(result.current.syncCategories.data).toEqual(response)
    })

    it('should handle syncCategories errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Failed to sync categories')
      syncCategoriesMock.mockRejectedValue(error)

      const { result } = renderHook(() => useBookmarkMutations('user-123'), { wrapper })

      result.current.syncCategories.mutate({
        bookmarkId: 'bookmark-1',
        categoryIds: ['cat-1'],
      })

      await waitFor(() => expect(result.current.syncCategories.isError).toBe(true))

      expect(result.current.syncCategories.error).toEqual(error)
    })
  })
})
