/**
 * Service for managing user search history.
 */

import { apiClient } from './api-client'

export interface SearchHistoryItem {
  id: number
  user_id: string
  search_query: string
  created_at: string
}

export interface SearchHistoryListResponse {
  items: SearchHistoryItem[]
}

export interface PaginationMetadata {
  page: number
  page_size: number
  total_count: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface SearchHistoryPaginatedResponse {
  items: SearchHistoryItem[]
  pagination: PaginationMetadata
}

export interface DeleteResponse {
  success: boolean
  message: string
}

export interface ClearHistoryResponse {
  success: boolean
  deleted_count: number
  message: string
}

export const searchHistoryService = {
  /**
   * Add a search query to user's history.
   */
  addSearch: async (userId: string, searchQuery: string): Promise<SearchHistoryItem> => {
    return apiClient.post<SearchHistoryItem>(
      `/api/v1/users/${userId}/search-history`,
      { search_query: searchQuery }
    )
  },

  /**
   * Get user's most recent search queries.
   */
  getRecentSearches: async (userId: string, limit: number = 3): Promise<SearchHistoryItem[]> => {
    const response = await apiClient.get<SearchHistoryListResponse>(
      `/api/v1/users/${userId}/search-history/recent?limit=${limit}`
    )
    return response.items
  },

  /**
   * Get user's search history with pagination.
   */
  getSearchHistory: async (
    userId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<SearchHistoryPaginatedResponse> => {
    return apiClient.get<SearchHistoryPaginatedResponse>(
      `/api/v1/users/${userId}/search-history?page=${page}&page_size=${pageSize}`
    )
  },

  /**
   * Delete a specific search history entry.
   */
  deleteSearchHistoryItem: async (userId: string, historyId: number): Promise<DeleteResponse> => {
    return apiClient.delete<DeleteResponse>(
      `/api/v1/users/${userId}/search-history/${historyId}`
    )
  },

  /**
   * Clear all search history for a user.
   */
  clearAllHistory: async (userId: string): Promise<ClearHistoryResponse> => {
    return apiClient.delete<ClearHistoryResponse>(`/api/v1/users/${userId}/search-history`)
  },
}
