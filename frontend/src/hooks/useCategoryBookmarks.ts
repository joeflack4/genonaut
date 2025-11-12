import { useQuery } from '@tanstack/react-query'
import { bookmarkCategoriesService } from '../services'
import type { PaginatedResult, BookmarkWithContent, BookmarkQueryParams } from '../types/domain'

export const categoryBookmarksQueryKey = (
  categoryId: string,
  userId: string,
  params: BookmarkQueryParams = {}
) => ['bookmark-category-bookmarks', categoryId, userId, params]

export function useCategoryBookmarks(
  categoryId: string,
  userId: string,
  params: BookmarkQueryParams = {}
) {
  return useQuery<PaginatedResult<BookmarkWithContent>>({
    queryKey: categoryBookmarksQueryKey(categoryId, userId, params),
    queryFn: () => bookmarkCategoriesService.getCategoryBookmarks(categoryId, userId, params),
    enabled: !!categoryId && !!userId,  // Only run query if both IDs are provided
  })
}
