import { useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query'
import { useEffect, useCallback, useMemo } from 'react'
import { usePagination, type UsePaginationOptions } from './usePagination'
import type {
  EnhancedPaginatedResult,
  PaginationParams,
  PaginationMeta
} from '../types/domain'

export interface UsePaginatedQueryOptions<TData, TError = Error> extends UsePaginationOptions {
  // Query configuration
  queryKey: (params: PaginationParams) => readonly unknown[]
  queryFn: (params: PaginationParams) => Promise<EnhancedPaginatedResult<TData>>

  // React Query options
  enabled?: boolean
  staleTime?: number
  gcTime?: number // Previously cacheTime

  // Pre-fetching configuration
  enablePrefetch?: boolean
  prefetchPages?: number // Number of pages to prefetch ahead
  prefetchDelay?: number // Delay in ms before prefetching

  // Error handling
  onError?: (error: TError) => void

  // Success callback
  onSuccess?: (data: EnhancedPaginatedResult<TData>) => void
}

export interface UsePaginatedQueryResult<TData> {
  // Query state
  data?: EnhancedPaginatedResult<TData>
  items: TData[]
  pagination?: PaginationMeta
  isLoading: boolean
  isError: boolean
  error: Error | null
  isFetching: boolean
  isSuccess: boolean

  // Pagination controls
  currentPage: number
  pageSize: number
  goToPage: (page: number) => void
  goToNextPage: () => void
  goToPreviousPage: () => void
  goToFirstPage: () => void
  goToLastPage: () => void
  setPageSize: (size: number) => void
  setSorting: (field: string, order: 'asc' | 'desc') => void
  resetPagination: () => void

  // Cursor navigation
  goToNextCursor: (cursor: string) => void
  goToPreviousCursor: (cursor: string) => void

  // Helper methods
  canGoNext: boolean
  canGoPrevious: boolean
  pageNumbers: number[]

  // Pre-fetching state
  prefetchStatus: {
    isNextPagePrefetched: boolean
    isPreviousPagePrefetched: boolean
  }

  // Manual actions
  refetch: () => Promise<unknown>
  invalidate: () => Promise<void>
}

export function usePaginatedQuery<TData, TError = Error>(
  options: UsePaginatedQueryOptions<TData, TError>
): UsePaginatedQueryResult<TData> {
  const {
    queryKey,
    queryFn,
    enabled = true,
    staleTime = 5 * 60 * 1000, // 5 minutes
    gcTime = 10 * 60 * 1000, // 10 minutes
    enablePrefetch = true,
    prefetchPages = 1,
    prefetchDelay = 500,
    onError,
    onSuccess,
    ...paginationOptions
  } = options

  const queryClient = useQueryClient()

  // Use the pagination hook for state management
  const pagination = usePagination(paginationOptions)
  const { paginationParams } = pagination

  // Main query
  const query = useQuery<EnhancedPaginatedResult<TData>, TError>({
    queryKey: queryKey(paginationParams),
    queryFn: () => queryFn(paginationParams),
    enabled,
    staleTime,
    gcTime,
  } as UseQueryOptions<EnhancedPaginatedResult<TData>, TError>)

  // Handle success callback
  useEffect(() => {
    if (query.isSuccess && query.data && onSuccess) {
      onSuccess(query.data)
    }
  }, [query.isSuccess, query.data, onSuccess])

  // Handle error callback
  useEffect(() => {
    if (query.isError && query.error && onError) {
      onError(query.error)
    }
  }, [query.isError, query.error, onError])

  // Pre-fetching logic
  const prefetchNextPages = useCallback(async () => {
    if (!enablePrefetch || !query.data?.pagination.hasNext) return

    const currentMeta = query.data.pagination

    // Prefetch next pages using page-based navigation
    for (let i = 1; i <= prefetchPages; i++) {
      const nextPage = currentMeta.page + i
      if (nextPage <= currentMeta.totalPages) {
        const nextParams: PaginationParams = {
          ...paginationParams,
          page: nextPage,
          cursor: undefined // Use page-based for prefetch
        }

        queryClient.prefetchQuery({
          queryKey: queryKey(nextParams),
          queryFn: () => queryFn(nextParams),
          staleTime,
        })
      }
    }

    // Prefetch using cursor if available
    if (currentMeta.nextCursor) {
      const cursorParams: PaginationParams = {
        ...paginationParams,
        cursor: currentMeta.nextCursor,
        page: currentMeta.page + 1
      }

      queryClient.prefetchQuery({
        queryKey: queryKey(cursorParams),
        queryFn: () => queryFn(cursorParams),
        staleTime,
      })
    }
  }, [
    enablePrefetch,
    query.data?.pagination,
    prefetchPages,
    paginationParams,
    queryKey,
    queryFn,
    queryClient,
    staleTime
  ])

  // Trigger prefetch when data changes
  useEffect(() => {
    if (!query.data || !enablePrefetch) return

    const timeoutId = setTimeout(prefetchNextPages, prefetchDelay)
    return () => clearTimeout(timeoutId)
  }, [prefetchNextPages, prefetchDelay, enablePrefetch, query.data])

  // Check prefetch status
  const prefetchStatus = useMemo(() => {
    if (!query.data?.pagination) {
      return {
        isNextPagePrefetched: false,
        isPreviousPagePrefetched: false
      }
    }

    const { pagination: meta } = query.data

    // Check if next page is prefetched
    const nextPageParams: PaginationParams = {
      ...paginationParams,
      page: meta.page + 1,
      cursor: undefined
    }
    const isNextPagePrefetched = queryClient.getQueryData(queryKey(nextPageParams)) !== undefined

    // Check if previous page is prefetched
    const prevPageParams: PaginationParams = {
      ...paginationParams,
      page: Math.max(1, meta.page - 1),
      cursor: undefined
    }
    const isPreviousPagePrefetched = queryClient.getQueryData(queryKey(prevPageParams)) !== undefined

    return {
      isNextPagePrefetched,
      isPreviousPagePrefetched
    }
  }, [query.data?.pagination, paginationParams, queryKey, queryClient])

  // Manual actions
  const invalidate = useCallback(async () => {
    await queryClient.invalidateQueries({
      queryKey: queryKey(paginationParams)
    })
  }, [queryClient, queryKey, paginationParams])

  // Helper computed values
  const canGoNext = pagination.canGoNext(query.data?.pagination)
  const canGoPrevious = pagination.canGoPrevious(query.data?.pagination)
  const pageNumbers = pagination.getPageNumbers(query.data?.pagination)

  return {
    // Query state
    data: query.data,
    items: query.data?.items ?? [],
    pagination: query.data?.pagination,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isFetching: query.isFetching,
    isSuccess: query.isSuccess,

    // Pagination controls
    currentPage: pagination.currentPage,
    pageSize: pagination.pageSize,
    goToPage: pagination.goToPage,
    goToNextPage: pagination.goToNextPage,
    goToPreviousPage: pagination.goToPreviousPage,
    goToFirstPage: pagination.goToFirstPage,
    goToLastPage: () => {
      if (query.data?.pagination) {
        pagination.goToLastPage(query.data.pagination.totalPages)
      }
    },
    setPageSize: pagination.setPageSize,
    setSorting: pagination.setSorting,
    resetPagination: pagination.resetPagination,

    // Cursor navigation
    goToNextCursor: pagination.goToNextCursor,
    goToPreviousCursor: pagination.goToPreviousCursor,

    // Helper methods
    canGoNext,
    canGoPrevious,
    pageNumbers,

    // Pre-fetching state
    prefetchStatus,

    // Manual actions
    refetch: query.refetch,
    invalidate
  }
}