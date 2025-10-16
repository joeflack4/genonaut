/**
 * Hook for fetching user search history.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  searchHistoryService,
  type SearchHistoryItem,
  type SearchHistoryPaginatedResponse,
} from '../services'

// Query keys
export const searchHistoryQueryKeys = {
  all: (userId: string) => ['searchHistory', userId] as const,
  recent: (userId: string, limit: number) => ['searchHistory', userId, 'recent', limit] as const,
  paginated: (userId: string, page: number, pageSize: number) =>
    ['searchHistory', userId, 'paginated', page, pageSize] as const,
}

/**
 * Hook to fetch recent search history (for dropdown).
 */
export function useRecentSearches(userId: string, limit: number = 3) {
  return useQuery<SearchHistoryItem[]>({
    queryKey: searchHistoryQueryKeys.recent(userId, limit),
    queryFn: () => searchHistoryService.getRecentSearches(userId, limit),
    enabled: !!userId,
  })
}

/**
 * Hook to fetch paginated search history (for dedicated page).
 */
export function useSearchHistory(userId: string, page: number = 1, pageSize: number = 20) {
  return useQuery<SearchHistoryPaginatedResponse>({
    queryKey: searchHistoryQueryKeys.paginated(userId, page, pageSize),
    queryFn: () => searchHistoryService.getSearchHistory(userId, page, pageSize),
    enabled: !!userId,
  })
}

/**
 * Hook to add search to history.
 */
export function useAddSearchHistory(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (searchQuery: string) => searchHistoryService.addSearch(userId, searchQuery),
    onSuccess: () => {
      // Invalidate all search history queries for this user
      queryClient.invalidateQueries({ queryKey: searchHistoryQueryKeys.all(userId) })
    },
  })
}

/**
 * Hook to delete a search history item.
 */
export function useDeleteSearchHistory(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (historyId: number) =>
      searchHistoryService.deleteSearchHistoryItem(userId, historyId),
    onSuccess: () => {
      // Invalidate all search history queries for this user
      queryClient.invalidateQueries({ queryKey: searchHistoryQueryKeys.all(userId) })
    },
  })
}

/**
 * Hook to clear all search history.
 */
export function useClearSearchHistory(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => searchHistoryService.clearAllHistory(userId),
    onSuccess: () => {
      // Invalidate all search history queries for this user
      queryClient.invalidateQueries({ queryKey: searchHistoryQueryKeys.all(userId) })
    },
  })
}
