import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bookmarksService } from '../services'
import { bookmarkStatusQueryKey } from './useBookmarkStatus'
import { bookmarkedItemsQueryKey } from './useBookmarkedItems'
import type { Bookmark } from '../types/domain'

/**
 * Hook providing mutations for bookmark operations
 * Automatically invalidates relevant queries on success
 */
export function useBookmarkMutations(userId: string) {
  const queryClient = useQueryClient()

  const createBookmark = useMutation({
    mutationFn: ({
      contentId,
      contentSourceType = 'items',
      options = {},
    }: {
      contentId: number
      contentSourceType?: string
      options?: {
        note?: string
        pinned?: boolean
        isPublic?: boolean
      }
    }) => bookmarksService.createBookmark(userId, contentId, contentSourceType, options),
    onSuccess: (bookmark: Bookmark) => {
      // Invalidate bookmark status queries for this content
      queryClient.invalidateQueries({
        queryKey: bookmarkStatusQueryKey(userId, bookmark.contentId, bookmark.contentSourceType),
      })
      // Invalidate bookmarks list queries
      queryClient.invalidateQueries({
        queryKey: bookmarkedItemsQueryKey(userId),
      })
      // Invalidate and refetch batch bookmark status queries
      queryClient.invalidateQueries({
        queryKey: ['bookmark-status-batch'],
        refetchType: 'active', // Force active queries to refetch immediately
      })
    },
  })

  const deleteBookmark = useMutation({
    mutationFn: ({
      bookmarkId,
      contentId,
      contentSourceType = 'items',
    }: {
      bookmarkId: string
      contentId: number
      contentSourceType?: string
    }) => bookmarksService.deleteBookmark(bookmarkId, userId),
    onSuccess: (_data, variables) => {
      // Invalidate bookmark status queries for this content
      queryClient.invalidateQueries({
        queryKey: bookmarkStatusQueryKey(userId, variables.contentId, variables.contentSourceType),
      })
      // Invalidate bookmarks list queries
      queryClient.invalidateQueries({
        queryKey: bookmarkedItemsQueryKey(userId),
      })
      // Invalidate and refetch batch bookmark status queries
      queryClient.invalidateQueries({
        queryKey: ['bookmark-status-batch'],
        refetchType: 'active', // Force active queries to refetch immediately
      })
    },
  })

  const syncCategories = useMutation({
    mutationFn: ({
      bookmarkId,
      categoryIds,
    }: {
      bookmarkId: string
      categoryIds: string[]
    }) => bookmarksService.syncCategories(bookmarkId, userId, categoryIds),
    onSuccess: () => {
      // Invalidate bookmarks list queries (which may include category info)
      queryClient.invalidateQueries({
        queryKey: bookmarkedItemsQueryKey(userId),
      })
      // Invalidate bookmark categories queries
      queryClient.invalidateQueries({
        queryKey: ['bookmark-categories'],
      })
    },
  })

  return {
    createBookmark,
    deleteBookmark,
    syncCategories,
  }
}
