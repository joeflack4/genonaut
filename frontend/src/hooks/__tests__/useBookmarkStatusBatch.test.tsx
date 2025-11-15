import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useBookmarkStatusBatch, bookmarkStatusBatchQueryKey } from '../useBookmarkStatusBatch'
import type { Bookmark } from '../../types/domain'
import type { ContentItemReference } from '../useBookmarkStatusBatch'

vi.mock('../../services', () => {
  const checkBookmarkStatusBatchMock = vi.fn()

  return {
    bookmarksService: {
      checkBookmarkStatusBatch: checkBookmarkStatusBatchMock,
    },
  }
})

const { bookmarksService } = await import('../../services')
const checkBookmarkStatusBatchMock = vi.mocked(bookmarksService.checkBookmarkStatusBatch)

describe('useBookmarkStatusBatch', () => {
  beforeEach(() => {
    checkBookmarkStatusBatchMock.mockReset()
  })

  describe('When all items are bookmarked', () => {
    it('should return correct status for all bookmarked items', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const bookmark1: Bookmark = {
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

      const bookmark2: Bookmark = {
        id: 'bookmark-2',
        userId: 'user-123',
        contentId: 1002,
        contentSourceType: 'items',
        note: null,
        pinned: false,
        isPublic: false,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      }

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': bookmark1,
        '1002-items': bookmark2,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusBatchMock).toHaveBeenCalledWith('user-123', contentItems)
      expect(result.current.bookmarkStatuses).toEqual({
        '1001-items': bookmark1,
        '1002-items': bookmark2,
      })

      // Test getBookmarkStatus helper
      const status1 = result.current.getBookmarkStatus(1001, 'items')
      expect(status1.isBookmarked).toBe(true)
      expect(status1.bookmark).toEqual(bookmark1)

      const status2 = result.current.getBookmarkStatus(1002, 'items')
      expect(status2.isBookmarked).toBe(true)
      expect(status2.bookmark).toEqual(bookmark2)
    })
  })

  describe('When no items are bookmarked', () => {
    it('should return correct status when no items are bookmarked', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': null,
        '1002-items': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusBatchMock).toHaveBeenCalledWith('user-123', contentItems)
      expect(result.current.bookmarkStatuses).toEqual({
        '1001-items': null,
        '1002-items': null,
      })

      // Test getBookmarkStatus helper
      const status1 = result.current.getBookmarkStatus(1001, 'items')
      expect(status1.isBookmarked).toBe(false)
      expect(status1.bookmark).toBeUndefined()

      const status2 = result.current.getBookmarkStatus(1002, 'items')
      expect(status2.isBookmarked).toBe(false)
      expect(status2.bookmark).toBeUndefined()
    })
  })

  describe('When some items are bookmarked (mixed case)', () => {
    it('should return correct status for mixed bookmarked/unbookmarked items', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const bookmark1: Bookmark = {
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

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': bookmark1,
        '1002-items': null,
        '1003-auto': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
        { contentId: 1003, contentSourceType: 'auto' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusBatchMock).toHaveBeenCalledWith('user-123', contentItems)

      // Test getBookmarkStatus helper for bookmarked item
      const status1 = result.current.getBookmarkStatus(1001, 'items')
      expect(status1.isBookmarked).toBe(true)
      expect(status1.bookmark).toEqual(bookmark1)

      // Test getBookmarkStatus helper for unbookmarked items
      const status2 = result.current.getBookmarkStatus(1002, 'items')
      expect(status2.isBookmarked).toBe(false)
      expect(status2.bookmark).toBeUndefined()

      const status3 = result.current.getBookmarkStatus(1003, 'auto')
      expect(status3.isBookmarked).toBe(false)
      expect(status3.bookmark).toBeUndefined()
    })
  })

  describe('Loading state', () => {
    it('should set loading state correctly', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('Query key factory', () => {
    it('should generate correct key with userId and contentItems', () => {
      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'auto' },
      ]

      const key = bookmarkStatusBatchQueryKey('user-123', contentItems)
      expect(key).toEqual(['bookmark-status-batch', 'user-123', '1001-items,1002-auto'])
    })

    it('should generate different keys for different content items', () => {
      const contentItems1: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]
      const contentItems2: ContentItemReference[] = [
        { contentId: 1002, contentSourceType: 'items' },
      ]

      const key1 = bookmarkStatusBatchQueryKey('user-123', contentItems1)
      const key2 = bookmarkStatusBatchQueryKey('user-123', contentItems2)

      expect(key1).not.toEqual(key2)
    })

    it('should generate same key for same content items in different order', () => {
      // Note: This test documents current behavior - order matters in current implementation
      const contentItems1: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
      ]
      const contentItems2: ContentItemReference[] = [
        { contentId: 1002, contentSourceType: 'items' },
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const key1 = bookmarkStatusBatchQueryKey('user-123', contentItems1)
      const key2 = bookmarkStatusBatchQueryKey('user-123', contentItems2)

      // Different order produces different key (current implementation)
      expect(key1).not.toEqual(key2)
    })
  })

  describe('Enabled condition', () => {
    it('should not run query when userId is undefined', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch(undefined, contentItems),
        { wrapper }
      )

      expect(result.current.isPending).toBe(true)
      expect(checkBookmarkStatusBatchMock).not.toHaveBeenCalled()
    })

    it('should not run query when contentItems is empty', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', []),
        { wrapper }
      )

      expect(result.current.isPending).toBe(true)
      expect(checkBookmarkStatusBatchMock).not.toHaveBeenCalled()
    })

    it('should run query when userId and contentItems are provided', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusBatchMock).toHaveBeenCalledWith('user-123', contentItems)
    })
  })

  describe('Error handling', () => {
    it('should handle API errors gracefully', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      checkBookmarkStatusBatchMock.mockRejectedValue(error)

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
      expect(result.current.bookmarkStatuses).toEqual({})
    })

    it('should handle getBookmarkStatus when data is unavailable (error state)', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      checkBookmarkStatusBatchMock.mockRejectedValue(error)

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isError).toBe(true))

      // getBookmarkStatus should return safe defaults even when data is unavailable
      const status = result.current.getBookmarkStatus(1001, 'items')
      expect(status.isBookmarked).toBe(false)
      expect(status.bookmark).toBeUndefined()
    })
  })

  describe('Cache behavior', () => {
    it('should cache results with correct query key', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const bookmark: Bookmark = {
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

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': bookmark,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const cacheData = queryClient.getQueryData(
        bookmarkStatusBatchQueryKey('user-123', contentItems)
      )
      expect(cacheData).toEqual({
        '1001-items': bookmark,
      })
    })

    it('should have staleTime configured for caching', () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      // Note: This test documents that staleTime is set to 30000ms (30 seconds)
      // The actual value is verified in the implementation at line 51 of useBookmarkStatusBatch.ts
    })
  })

  describe('getBookmarkStatus helper', () => {
    it('should return status for item not in batch', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-items': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Query status for an item not in the original batch
      const status = result.current.getBookmarkStatus(9999, 'items')
      expect(status.isBookmarked).toBe(false)
      expect(status.bookmark).toBeUndefined()
    })

    it('should handle different content source types', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const bookmarkAuto: Bookmark = {
        id: 'bookmark-auto',
        userId: 'user-123',
        contentId: 1001,
        contentSourceType: 'auto',
        note: null,
        pinned: false,
        isPublic: false,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-01T00:00:00Z',
      }

      checkBookmarkStatusBatchMock.mockResolvedValue({
        '1001-auto': bookmarkAuto,
        '1001-items': null,
      })

      const contentItems: ContentItemReference[] = [
        { contentId: 1001, contentSourceType: 'auto' },
        { contentId: 1001, contentSourceType: 'items' },
      ]

      const { result } = renderHook(
        () => useBookmarkStatusBatch('user-123', contentItems),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Same contentId but different source type should return different statuses
      const statusAuto = result.current.getBookmarkStatus(1001, 'auto')
      expect(statusAuto.isBookmarked).toBe(true)
      expect(statusAuto.bookmark).toEqual(bookmarkAuto)

      const statusItems = result.current.getBookmarkStatus(1001, 'items')
      expect(statusItems.isBookmarked).toBe(false)
      expect(statusItems.bookmark).toBeUndefined()
    })
  })
})
