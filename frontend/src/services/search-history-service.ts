/**
 * Service for managing user search history.
 */

import { apiClient } from './api-client'

export interface SearchHistoryRecord {
  id: number
  user_id: string
  search_query: string
  created_at: string
}

export interface SearchHistoryItem {
  search_query: string
  search_count: number
  last_searched_at: string
  user_id: string
}

export interface SearchHistoryListResponse {
  items: SearchHistoryRecord[]
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
  addSearch: async (userId: string, searchQuery: string): Promise<SearchHistoryRecord> => {
    return apiClient.post<SearchHistoryRecord>(
      `/api/v1/users/${userId}/search-history`,
      { search_query: searchQuery }
    )
  },

  /**
   * Get user's most recent unique search queries (aggregated).
   * Returns the most recent unique searches sorted by last_searched_at descending.
   */
  getRecentSearches: async (userId: string, limit: number = 5): Promise<SearchHistoryItem[]> => {
    const response = await apiClient.get<SearchHistoryPaginatedResponse>(
      `/api/v1/users/${userId}/search-history?page=1&page_size=${limit}`
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
   * Delete all instances of a specific search query from user's history.
   */
  deleteSearchHistoryItem: async (userId: string, searchQuery: string): Promise<DeleteResponse> => {
    return apiClient.delete<DeleteResponse>(
      `/api/v1/users/${userId}/search-history/by-query`,
      { search_query: searchQuery }
    )
  },

  /**
   * Clear all search history for a user.
   */
  clearAllHistory: async (userId: string): Promise<ClearHistoryResponse> => {
    return apiClient.delete<ClearHistoryResponse>(`/api/v1/users/${userId}/search-history/clear`)
  },
}
