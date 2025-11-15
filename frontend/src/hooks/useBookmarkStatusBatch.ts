import { useQuery } from '@tanstack/react-query'
import { bookmarksService } from '../services'
import type { Bookmark } from '../types/domain'

/**
 * Content item reference for batch bookmark status check
 */
export interface ContentItemReference {
  contentId: number
  contentSourceType: string
}

/**
 * Bookmark status for a single content item
 */
export interface BookmarkStatus {
  isBookmarked: boolean
  bookmark: Bookmark | undefined
}

/**
 * Query key for batch bookmark status check
 */
export const bookmarkStatusBatchQueryKey = (
  userId: string,
  contentItems: ContentItemReference[]
) => [
  'bookmark-status-batch',
  userId,
  contentItems.map(item => `${item.contentId}-${item.contentSourceType}`).join(',')
]

/**
 * Hook to check bookmark status for multiple content items in a single batch request
 *
 * This hook is optimized for grid/list views where you need to check many items at once.
 * For single item checks (e.g., detail pages), use useBookmarkStatus instead.
 *
 * @param userId - User ID to check bookmarks for
 * @param contentItems - Array of content items to check
 * @returns Map of 'contentId-sourceType' to bookmark status
 */
export function useBookmarkStatusBatch(
  userId: string | undefined,
  contentItems: ContentItemReference[]
) {
  const query = useQuery<Record<string, Bookmark | null>>({
    queryKey: bookmarkStatusBatchQueryKey(userId!, contentItems),
    queryFn: () => bookmarksService.checkBookmarkStatusBatch(userId!, contentItems),
    enabled: !!userId && contentItems.length > 0,
    staleTime: 30000, // Consider data fresh for 30 seconds
  })

  // Helper function to get status for a specific content item
  const getBookmarkStatus = (contentId: number, contentSourceType: string): BookmarkStatus => {
    const key = `${contentId}-${contentSourceType}`
    const bookmark = query.data?.[key] ?? null

    return {
      isBookmarked: bookmark !== null,
      bookmark: bookmark ?? undefined,
    }
  }

  return {
    ...query,
    bookmarkStatuses: query.data ?? {},
    getBookmarkStatus,
  }
}
