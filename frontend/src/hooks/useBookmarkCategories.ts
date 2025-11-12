import { useQuery } from '@tanstack/react-query'
import { bookmarkCategoriesService } from '../services'
import type { PaginatedResult, BookmarkCategory, BookmarkCategoryQueryParams } from '../types/domain'

export const bookmarkCategoriesQueryKey = (userId: string, params: BookmarkCategoryQueryParams = {}) => [
  'bookmark-categories',
  userId,
  params
]

export function useBookmarkCategories(userId: string, params: BookmarkCategoryQueryParams = {}) {
  return useQuery<PaginatedResult<BookmarkCategory>>({
    queryKey: bookmarkCategoriesQueryKey(userId, params),
    queryFn: () => bookmarkCategoriesService.listCategories(userId, params),
    enabled: !!userId,  // Only run query if userId is provided
  })
}
