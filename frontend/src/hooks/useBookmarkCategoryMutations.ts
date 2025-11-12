import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bookmarkCategoriesService } from '../services'
import { bookmarkCategoriesQueryKey } from './useBookmarkCategories'
import type {
  BookmarkCategory,
  BookmarkCategoryCreateRequest,
  BookmarkCategoryUpdateRequest
} from '../types/domain'

interface CreateCategoryArgs {
  userId: string
  data: BookmarkCategoryCreateRequest
}

interface UpdateCategoryArgs {
  categoryId: string
  userId: string
  data: BookmarkCategoryUpdateRequest
}

interface DeleteCategoryArgs {
  categoryId: string
  userId: string
  targetCategoryId?: string | null
  deleteAll?: boolean
}

/**
 * Hook for creating a new bookmark category
 */
export function useCreateCategory() {
  const queryClient = useQueryClient()

  return useMutation<BookmarkCategory, unknown, CreateCategoryArgs>({
    mutationFn: ({ userId, data }) => bookmarkCategoriesService.createCategory(userId, data),
    onSuccess: async (_, variables) => {
      // Invalidate all category queries for this user
      await queryClient.invalidateQueries({
        queryKey: ['bookmark-categories', variables.userId]
      })
    },
  })
}

/**
 * Hook for updating an existing bookmark category
 */
export function useUpdateCategory() {
  const queryClient = useQueryClient()

  return useMutation<BookmarkCategory, unknown, UpdateCategoryArgs>({
    mutationFn: ({ categoryId, userId, data }) =>
      bookmarkCategoriesService.updateCategory(categoryId, userId, data),
    onSuccess: async (_, variables) => {
      // Invalidate all category queries for this user
      await queryClient.invalidateQueries({
        queryKey: ['bookmark-categories', variables.userId]
      })
    },
  })
}

/**
 * Hook for deleting a bookmark category
 */
export function useDeleteCategory() {
  const queryClient = useQueryClient()

  return useMutation<void, unknown, DeleteCategoryArgs>({
    mutationFn: ({ categoryId, userId, targetCategoryId, deleteAll }) =>
      bookmarkCategoriesService.deleteCategory(categoryId, userId, targetCategoryId, deleteAll),
    onSuccess: async (_, variables) => {
      // Invalidate all category queries for this user
      await queryClient.invalidateQueries({
        queryKey: ['bookmark-categories', variables.userId]
      })
    },
  })
}
