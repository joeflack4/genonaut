import { useQuery } from '@tanstack/react-query'
import { bookmarksService } from '../services'
import type { Bookmark } from '../types/domain'

/**
 * Query key for bookmark status check
 */
export const bookmarkStatusQueryKey = (
  userId: string,
  contentId: number,
  contentSourceType: string = 'items'
) => ['bookmark-status', userId, contentId, contentSourceType]

/**
 * Hook to check if a content item is bookmarked by the user
 * Returns the bookmark if it exists, undefined if not bookmarked, or null while loading
 */
export function useBookmarkStatus(
  userId: string | undefined,
  contentId: number | undefined,
  contentSourceType: string = 'items'
) {
  const query = useQuery<Bookmark | null>({
    queryKey: bookmarkStatusQueryKey(userId!, contentId!, contentSourceType),
    queryFn: () =>
      bookmarksService.checkBookmarkStatus(userId!, contentId!, contentSourceType),
    enabled: !!userId && contentId !== undefined,
    staleTime: 30000, // Consider data fresh for 30 seconds
  })

  return {
    ...query,
    isBookmarked: query.data !== null && query.data !== undefined,
    bookmark: query.data ?? undefined,
  }
}
