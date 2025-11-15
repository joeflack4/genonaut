import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useBookmarkStatus, bookmarkStatusQueryKey } from '../useBookmarkStatus'
import type { Bookmark } from '../../types/domain'

vi.mock('../../services', () => {
  const checkBookmarkStatusMock = vi.fn()

  return {
    bookmarksService: {
      checkBookmarkStatus: checkBookmarkStatusMock,
    },
  }
})

const { bookmarksService } = await import('../../services')
const checkBookmarkStatusMock = vi.mocked(bookmarksService.checkBookmarkStatus)

describe('useBookmarkStatus', () => {
  beforeEach(() => {
    checkBookmarkStatusMock.mockReset()
  })

  describe('When bookmarked', () => {
    it('should return correct status when bookmarked', async () => {
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

      checkBookmarkStatusMock.mockResolvedValue(bookmark)

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', 1001, 'items'),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusMock).toHaveBeenCalledWith('user-123', 1001, 'items')
      expect(result.current.isBookmarked).toBe(true)
      expect(result.current.bookmark).toEqual(bookmark)
      expect(result.current.data).toEqual(bookmark)
    })
  })

  describe('When not bookmarked', () => {
    it('should return correct status when not bookmarked', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusMock.mockResolvedValue(null)

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', 1001, 'items'),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusMock).toHaveBeenCalledWith('user-123', 1001, 'items')
      expect(result.current.isBookmarked).toBe(false)
      expect(result.current.bookmark).toBeUndefined()
      expect(result.current.data).toBeNull()
    })
  })

  describe('Loading state', () => {
    it('should set loading state correctly', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusMock.mockResolvedValue(null)

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', 1001, 'items'),
        { wrapper }
      )

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('Query key factory', () => {
    it('should generate correct key with userId, contentId, and contentSourceType', () => {
      const key = bookmarkStatusQueryKey('user-123', 1001, 'items')
      expect(key).toEqual(['bookmark-status', 'user-123', 1001, 'items'])
    })

    it('should use default contentSourceType if not provided', () => {
      const key = bookmarkStatusQueryKey('user-123', 1001)
      expect(key).toEqual(['bookmark-status', 'user-123', 1001, 'items'])
    })
  })

  describe('Enabled condition', () => {
    it('should not run query when userId is undefined', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(
        () => useBookmarkStatus(undefined, 1001, 'items'),
        { wrapper }
      )

      expect(result.current.isPending).toBe(true)
      expect(checkBookmarkStatusMock).not.toHaveBeenCalled()
    })

    it('should not run query when contentId is undefined', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', undefined, 'items'),
        { wrapper }
      )

      expect(result.current.isPending).toBe(true)
      expect(checkBookmarkStatusMock).not.toHaveBeenCalled()
    })

    it('should run query when both userId and contentId are provided', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      checkBookmarkStatusMock.mockResolvedValue(null)

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', 1001, 'items'),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(checkBookmarkStatusMock).toHaveBeenCalledWith('user-123', 1001, 'items')
    })
  })

  describe('Error handling', () => {
    it('should handle API errors gracefully', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      checkBookmarkStatusMock.mockRejectedValue(error)

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', 1001, 'items'),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
      expect(result.current.isBookmarked).toBe(false)
      expect(result.current.bookmark).toBeUndefined()
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

      checkBookmarkStatusMock.mockResolvedValue(bookmark)

      const { result } = renderHook(
        () => useBookmarkStatus('user-123', 1001, 'items'),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      const cacheData = queryClient.getQueryData(
        bookmarkStatusQueryKey('user-123', 1001, 'items')
      )
      expect(cacheData).toEqual(bookmark)
    })
  })
})
