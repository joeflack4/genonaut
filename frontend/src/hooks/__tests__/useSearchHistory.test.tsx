/**
 * Unit tests for search history hooks.
 */

import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { vi, beforeEach, afterEach } from 'vitest'
import { createTestQueryClient } from '../../test/query-client'
import {
  useRecentSearches,
  useSearchHistory,
  useAddSearchHistory,
  useDeleteSearchHistory,
  useClearSearchHistory,
} from '../useSearchHistory'
import type { SearchHistoryItem, SearchHistoryPaginatedResponse } from '../../services'

vi.mock('../../services', () => ({
  searchHistoryService: {
    getRecentSearches: vi.fn(),
    getSearchHistory: vi.fn(),
    addSearch: vi.fn(),
    deleteSearchHistoryItem: vi.fn(),
    clearAllHistory: vi.fn(),
  },
}))

const { searchHistoryService } = await import('../../services')

// Clear all mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.clearAllMocks()
})

const mockSearchHistoryItems: SearchHistoryItem[] = [
  {
    id: 1,
    user_id: 'user-123',
    search_query: 'cats playing',
    created_at: '2024-01-01T10:00:00Z',
  },
  {
    id: 2,
    user_id: 'user-123',
    search_query: '"black cat" mystery',
    created_at: '2024-01-01T09:00:00Z',
  },
  {
    id: 3,
    user_id: 'user-123',
    search_query: 'sunset ocean',
    created_at: '2024-01-01T08:00:00Z',
  },
]

const mockPaginatedResponse: SearchHistoryPaginatedResponse = {
  items: mockSearchHistoryItems,
  pagination: {
    page: 1,
    page_size: 20,
    total_count: 3,
    total_pages: 1,
    has_next: false,
    has_previous: false,
  },
}

describe('useRecentSearches', () => {
  const userId = 'user-123'

  it('fetches recent searches successfully', async () => {
    vi.mocked(searchHistoryService.getRecentSearches).mockResolvedValue(mockSearchHistoryItems)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useRecentSearches(userId, 3), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockSearchHistoryItems)
    expect(searchHistoryService.getRecentSearches).toHaveBeenCalledWith(userId, 3)
  })

  it('uses custom limit parameter', async () => {
    vi.mocked(searchHistoryService.getRecentSearches).mockResolvedValue(
      mockSearchHistoryItems.slice(0, 5)
    )

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useRecentSearches(userId, 5), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(searchHistoryService.getRecentSearches).toHaveBeenCalledWith(userId, 5)
  })

  it('does not fetch when userId is empty', () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useRecentSearches('', 3), { wrapper })

    expect(result.current.isFetching).toBe(false)
    expect(searchHistoryService.getRecentSearches).not.toHaveBeenCalled()
  })

  it('handles empty results', async () => {
    vi.mocked(searchHistoryService.getRecentSearches).mockResolvedValue([])

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useRecentSearches(userId, 3), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual([])
  })
})

describe('useSearchHistory', () => {
  const userId = 'user-123'

  it('fetches paginated search history successfully', async () => {
    vi.mocked(searchHistoryService.getSearchHistory).mockResolvedValue(mockPaginatedResponse)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useSearchHistory(userId, 1, 20), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockPaginatedResponse)
    expect(searchHistoryService.getSearchHistory).toHaveBeenCalledWith(userId, 1, 20)
  })

  it('uses custom page and page size', async () => {
    vi.mocked(searchHistoryService.getSearchHistory).mockResolvedValue({
      ...mockPaginatedResponse,
      pagination: { ...mockPaginatedResponse.pagination, page: 2, page_size: 10 },
    })

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useSearchHistory(userId, 2, 10), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(searchHistoryService.getSearchHistory).toHaveBeenCalledWith(userId, 2, 10)
  })

  it('does not fetch when userId is empty', () => {
    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useSearchHistory('', 1, 20), { wrapper })

    expect(result.current.isFetching).toBe(false)
    expect(searchHistoryService.getSearchHistory).not.toHaveBeenCalled()
  })
})

describe('useAddSearchHistory', () => {
  const userId = 'user-123'

  it('adds search to history successfully', async () => {
    const newSearch: SearchHistoryItem = {
      id: 4,
      user_id: userId,
      search_query: 'new search query',
      created_at: new Date().toISOString(),
    }

    vi.mocked(searchHistoryService.addSearch).mockResolvedValue(newSearch)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useAddSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate('new search query')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(searchHistoryService.addSearch).toHaveBeenCalledWith(userId, 'new search query')
    expect(result.current.data).toEqual(newSearch)
  })

  it('invalidates queries on success', async () => {
    const newSearch: SearchHistoryItem = {
      id: 5,
      user_id: userId,
      search_query: 'another search',
      created_at: new Date().toISOString(),
    }

    vi.mocked(searchHistoryService.addSearch).mockResolvedValue(newSearch)

    const queryClient = createTestQueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useAddSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate('another search')

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalled()
  })
})

describe('useDeleteSearchHistory', () => {
  const userId = 'user-123'

  it('deletes search history item successfully', async () => {
    const deleteResponse = {
      success: true,
      message: 'Search history item deleted successfully',
    }

    vi.mocked(searchHistoryService.deleteSearchHistoryItem).mockResolvedValue(deleteResponse)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(searchHistoryService.deleteSearchHistoryItem).toHaveBeenCalledWith(userId, 1)
    expect(result.current.data).toEqual(deleteResponse)
  })

  it('invalidates queries on success', async () => {
    const deleteResponse = {
      success: true,
      message: 'Deleted',
    }

    vi.mocked(searchHistoryService.deleteSearchHistoryItem).mockResolvedValue(deleteResponse)

    const queryClient = createTestQueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate(2)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalled()
  })
})

describe('useClearSearchHistory', () => {
  const userId = 'user-123'

  it('clears all search history successfully', async () => {
    const clearResponse = {
      success: true,
      deleted_count: 10,
      message: 'Cleared 10 search history items',
    }

    vi.mocked(searchHistoryService.clearAllHistory).mockResolvedValue(clearResponse)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useClearSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate()

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(searchHistoryService.clearAllHistory).toHaveBeenCalledWith(userId)
    expect(result.current.data).toEqual(clearResponse)
  })

  it('invalidates queries on success', async () => {
    const clearResponse = {
      success: true,
      deleted_count: 5,
      message: 'Cleared',
    }

    vi.mocked(searchHistoryService.clearAllHistory).mockResolvedValue(clearResponse)

    const queryClient = createTestQueryClient()
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useClearSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate()

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalled()
  })

  it('handles clearing when history is empty', async () => {
    const clearResponse = {
      success: true,
      deleted_count: 0,
      message: 'Cleared 0 items',
    }

    vi.mocked(searchHistoryService.clearAllHistory).mockResolvedValue(clearResponse)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    const { result } = renderHook(() => useClearSearchHistory(userId), { wrapper })

    await waitFor(() => expect(result.current).toBeDefined())

    result.current.mutate()

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.deleted_count).toBe(0)
  })
})
