import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import { useCreateCategory, useUpdateCategory, useDeleteCategory } from '../useBookmarkCategoryMutations'

vi.mock('../../services', () => {
  const createCategoryMock = vi.fn()
  const updateCategoryMock = vi.fn()
  const deleteCategoryMock = vi.fn()

  return {
    bookmarkCategoriesService: {
      createCategory: createCategoryMock,
      updateCategory: updateCategoryMock,
      deleteCategory: deleteCategoryMock,
    },
  }
})

const { bookmarkCategoriesService } = await import('../../services')
const createCategoryMock = vi.mocked(bookmarkCategoriesService.createCategory)
const updateCategoryMock = vi.mocked(bookmarkCategoriesService.updateCategory)
const deleteCategoryMock = vi.mocked(bookmarkCategoriesService.deleteCategory)

describe('useCreateCategory', () => {
  beforeEach(() => {
    createCategoryMock.mockReset()
  })

  describe('Successful creation', () => {
    it('should call service with correct data', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const newCategory = {
        id: 'new-cat-123',
        userId: 'user-123',
        name: 'New Category',
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
      }

      createCategoryMock.mockResolvedValue(newCategory)

      const { result } = renderHook(() => useCreateCategory(), { wrapper })

      const data = {
        name: 'New Category',
        isPublic: false,
      }

      result.current.mutate({ userId: 'user-123', data })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(createCategoryMock).toHaveBeenCalledWith('user-123', data)
    })

    it('should invalidate bookmark-categories queries', async () => {
      const queryClient = createTestQueryClient()
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const newCategory = {
        id: 'new-cat-123',
        userId: 'user-123',
        name: 'New Category',
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
      }

      createCategoryMock.mockResolvedValue(newCategory)

      const { result } = renderHook(() => useCreateCategory(), { wrapper })

      const data = {
        name: 'New Category',
        isPublic: false,
      }

      result.current.mutate({ userId: 'user-123', data })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['bookmark-categories', 'user-123']
      })
    })

    it('should return created category', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const newCategory = {
        id: 'new-cat-123',
        userId: 'user-123',
        name: 'New Category',
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
      }

      createCategoryMock.mockResolvedValue(newCategory)

      const { result } = renderHook(() => useCreateCategory(), { wrapper })

      const data = {
        name: 'New Category',
        isPublic: false,
      }

      result.current.mutate({ userId: 'user-123', data })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(newCategory)
    })
  })

  describe('Error handling', () => {
    it('should handle validation errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Validation error: name is required')
      createCategoryMock.mockRejectedValue(error)

      const { result } = renderHook(() => useCreateCategory(), { wrapper })

      const data = {
        name: '',
        isPublic: false,
      }

      result.current.mutate({ userId: 'user-123', data })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should handle network errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Network error')
      createCategoryMock.mockRejectedValue(error)

      const { result } = renderHook(() => useCreateCategory(), { wrapper })

      const data = {
        name: 'New Category',
        isPublic: false,
      }

      result.current.mutate({ userId: 'user-123', data })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })
})

describe('useUpdateCategory', () => {
  beforeEach(() => {
    updateCategoryMock.mockReset()
  })

  describe('Successful update', () => {
    it('should call service with categoryId, userId, and data', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const updatedCategory = {
        id: 'cat-123',
        userId: 'user-123',
        name: 'Updated Category',
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
      }

      updateCategoryMock.mockResolvedValue(updatedCategory)

      const { result } = renderHook(() => useUpdateCategory(), { wrapper })

      const data = {
        name: 'Updated Category',
      }

      result.current.mutate({ categoryId: 'cat-123', userId: 'user-123', data })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(updateCategoryMock).toHaveBeenCalledWith('cat-123', 'user-123', data)
    })

    it('should invalidate bookmark-categories queries', async () => {
      const queryClient = createTestQueryClient()
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const updatedCategory = {
        id: 'cat-123',
        userId: 'user-123',
        name: 'Updated Category',
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
      }

      updateCategoryMock.mockResolvedValue(updatedCategory)

      const { result } = renderHook(() => useUpdateCategory(), { wrapper })

      const data = {
        name: 'Updated Category',
      }

      result.current.mutate({ categoryId: 'cat-123', userId: 'user-123', data })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['bookmark-categories', 'user-123']
      })
    })

    it('should return updated category', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const updatedCategory = {
        id: 'cat-123',
        userId: 'user-123',
        name: 'Updated Category',
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
      }

      updateCategoryMock.mockResolvedValue(updatedCategory)

      const { result } = renderHook(() => useUpdateCategory(), { wrapper })

      const data = {
        name: 'Updated Category',
      }

      result.current.mutate({ categoryId: 'cat-123', userId: 'user-123', data })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(updatedCategory)
    })
  })

  describe('Error handling', () => {
    it('should handle 404 errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Category not found')
      updateCategoryMock.mockRejectedValue(error)

      const { result } = renderHook(() => useUpdateCategory(), { wrapper })

      const data = {
        name: 'Updated Category',
      }

      result.current.mutate({ categoryId: 'cat-999', userId: 'user-123', data })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })

    it('should handle validation errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Validation error: name too long')
      updateCategoryMock.mockRejectedValue(error)

      const { result } = renderHook(() => useUpdateCategory(), { wrapper })

      const data = {
        name: 'A'.repeat(200),
      }

      result.current.mutate({ categoryId: 'cat-123', userId: 'user-123', data })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })
})

describe('useDeleteCategory', () => {
  beforeEach(() => {
    deleteCategoryMock.mockReset()
  })

  describe('Successful deletion', () => {
    it('should call service with categoryId and userId', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      deleteCategoryMock.mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteCategory(), { wrapper })

      result.current.mutate({ categoryId: 'cat-123', userId: 'user-123' })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(deleteCategoryMock).toHaveBeenCalledWith('cat-123', 'user-123', undefined, undefined)
    })

    it('should invalidate bookmark-categories queries', async () => {
      const queryClient = createTestQueryClient()
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      deleteCategoryMock.mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteCategory(), { wrapper })

      result.current.mutate({ categoryId: 'cat-123', userId: 'user-123' })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: ['bookmark-categories', 'user-123']
      })
    })
  })

  describe('Error handling', () => {
    it('should handle 404 errors', async () => {
      const queryClient = createTestQueryClient()
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      )

      const error = new Error('Category not found')
      deleteCategoryMock.mockRejectedValue(error)

      const { result } = renderHook(() => useDeleteCategory(), { wrapper })

      result.current.mutate({ categoryId: 'cat-999', userId: 'user-123' })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toEqual(error)
    })
  })
})
