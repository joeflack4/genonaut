import { useQuery } from '@tanstack/react-query'
import { bookmarksService } from '../services'
import type { PaginatedResult, BookmarkWithContent, BookmarkQueryParams } from '../types/domain'

export const bookmarkedItemsQueryKey = (userId: string, params: BookmarkQueryParams = {}) => [
  'bookmarks',
  userId,
  params
]

export function useBookmarkedItems(userId: string, params: BookmarkQueryParams = {}) {
  return useQuery<PaginatedResult<BookmarkWithContent>>({
    queryKey: bookmarkedItemsQueryKey(userId, params),
    queryFn: () => bookmarksService.listBookmarks(userId, params),
    enabled: !!userId,  // Only run query if userId is provided
  })
}
