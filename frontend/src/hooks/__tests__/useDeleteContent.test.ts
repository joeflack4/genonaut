/**
 * Unit tests for useDeleteContent hook
 * Tests successful deletion, error handling, and query invalidation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useDeleteContent } from '../useDeleteContent'
import { galleryService } from '../../services'
import type { ReactNode } from 'react'
import React from 'react'

// Mock the gallery service
vi.mock('../../services', () => ({
  galleryService: {
    deleteContent: vi.fn(),
  },
}))

describe('useDeleteContent', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    // Create a new QueryClient for each test to ensure isolation
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
        mutations: {
          retry: false,
        },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('Successful deletion', () => {
    it('should call deleteContent service with correct parameters for regular content', async () => {
      const mockResponse = { message: 'Content 123 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      // Trigger mutation
      result.current.mutate({ contentId: 123 })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(galleryService.deleteContent).toHaveBeenCalledWith(123, {})
    })

    it('should call deleteContent service with sourceType for auto content', async () => {
      const mockResponse = { message: 'Auto content 456 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      // Trigger mutation with sourceType
      result.current.mutate({ contentId: 456, sourceType: 'auto' })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(galleryService.deleteContent).toHaveBeenCalledWith(456, { sourceType: 'auto' })
    })

    it('should return success response data', async () => {
      const mockResponse = { message: 'Content 789 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 789 })

      await waitFor(() => {
        expect(result.current.data).toEqual(mockResponse)
      })
    })
  })

  describe('Error handling', () => {
    it('should handle deletion errors', async () => {
      const mockError = new Error('Content with id 999 not found')
      vi.mocked(galleryService.deleteContent).mockRejectedValueOnce(mockError)

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 999 })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(mockError)
    })

    it('should call onError callback when deletion fails', async () => {
      const mockError = new Error('Network error')
      vi.mocked(galleryService.deleteContent).mockRejectedValueOnce(mockError)

      const onError = vi.fn()
      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 111 }, { onError })

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(mockError, { contentId: 111 }, undefined)
      })
    })
  })

  describe('Query invalidation', () => {
    it('should invalidate gallery-item query on success', async () => {
      const mockResponse = { message: 'Content 123 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      // Spy on query invalidation
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 123 })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Verify specific gallery item query was invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['gallery-item', 123],
      })
    })

    it('should invalidate all gallery queries on success', async () => {
      const mockResponse = { message: 'Content 456 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 456 })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Verify all gallery list queries were invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['gallery'],
      })
    })

    it('should invalidate unified gallery queries on success', async () => {
      const mockResponse = { message: 'Content 789 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 789 })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Verify unified gallery queries were invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['unified-gallery'],
      })
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['unified-gallery-stats'],
      })
    })

    it('should call onSuccess callback after invalidation', async () => {
      const mockResponse = { message: 'Content 222 deleted successfully' }
      vi.mocked(galleryService.deleteContent).mockResolvedValueOnce(mockResponse)

      const onSuccess = vi.fn()
      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 222 }, { onSuccess })

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(
          mockResponse,
          { contentId: 222 },
          undefined
        )
      })
    })
  })

  describe('Loading state', () => {
    it('should set isPending to true while deletion is in progress', async () => {
      let resolveDelete: (value: unknown) => void
      const deletePromise = new Promise((resolve) => {
        resolveDelete = resolve
      })
      vi.mocked(galleryService.deleteContent).mockReturnValueOnce(deletePromise as Promise<never>)

      const { result } = renderHook(() => useDeleteContent(), { wrapper })

      result.current.mutate({ contentId: 333 })

      // Check that isPending is true immediately after mutation
      expect(result.current.isPending).toBe(true)

      // Resolve the promise
      resolveDelete!({ message: 'Success' })

      await waitFor(() => {
        expect(result.current.isPending).toBe(false)
      })
    })
  })
})
