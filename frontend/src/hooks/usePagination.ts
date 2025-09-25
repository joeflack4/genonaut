import { useState, useCallback, useMemo } from 'react'
import type { PaginationParams, PaginationMeta } from '../types/domain'

export interface UsePaginationOptions {
  initialPage?: number
  initialPageSize?: number
  enablePrefetch?: boolean
  maxCacheSize?: number
}

export interface UsePaginationResult {
  // Current state
  currentPage: number
  pageSize: number
  cursor?: string | null
  sortField?: string
  sortOrder?: 'asc' | 'desc'

  // Navigation methods
  goToPage: (page: number) => void
  goToNextPage: () => void
  goToPreviousPage: () => void
  goToFirstPage: () => void
  goToLastPage: (totalPages: number) => void

  // Cursor navigation methods
  goToNextCursor: (nextCursor: string) => void
  goToPreviousCursor: (prevCursor: string) => void

  // Configuration methods
  setPageSize: (size: number) => void
  setSorting: (field: string, order: 'asc' | 'desc') => void
  resetPagination: () => void

  // Current pagination parameters
  paginationParams: PaginationParams

  // Helper methods
  canGoNext: (meta?: PaginationMeta) => boolean
  canGoPrevious: (meta?: PaginationMeta) => boolean
  getPageNumbers: (meta?: PaginationMeta) => number[]
}

export function usePagination(options: UsePaginationOptions = {}): UsePaginationResult {
  const {
    initialPage = 1,
    initialPageSize = 50,
    enablePrefetch: _enablePrefetch = true,
    maxCacheSize: _maxCacheSize = 10
  } = options

  // State management
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [cursor, setCursor] = useState<string | null>(null)
  const [sortField, setSortField] = useState<string | undefined>(undefined)
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Navigation methods
  const goToPage = useCallback((page: number) => {
    setCurrentPage(page)
    setCursor(null) // Clear cursor when using page-based navigation
  }, [])

  const goToNextPage = useCallback(() => {
    setCurrentPage(prev => prev + 1)
    setCursor(null)
  }, [])

  const goToPreviousPage = useCallback(() => {
    setCurrentPage(prev => Math.max(1, prev - 1))
    setCursor(null)
  }, [])

  const goToFirstPage = useCallback(() => {
    setCurrentPage(1)
    setCursor(null)
  }, [])

  const goToLastPage = useCallback((totalPages: number) => {
    setCurrentPage(totalPages)
    setCursor(null)
  }, [])

  // Cursor navigation methods
  const goToNextCursor = useCallback((nextCursor: string) => {
    setCursor(nextCursor)
    setCurrentPage(prev => prev + 1) // Update page number for UI consistency
  }, [])

  const goToPreviousCursor = useCallback((prevCursor: string) => {
    setCursor(prevCursor)
    setCurrentPage(prev => Math.max(1, prev - 1))
  }, [])

  // Configuration methods
  const handleSetPageSize = useCallback((size: number) => {
    setPageSize(size)
    setCurrentPage(1) // Reset to first page when changing page size
    setCursor(null)
  }, [])

  const setSorting = useCallback((field: string, order: 'asc' | 'desc') => {
    setSortField(field)
    setSortOrder(order)
    setCurrentPage(1) // Reset to first page when changing sorting
    setCursor(null)
  }, [])

  const resetPagination = useCallback(() => {
    setCurrentPage(initialPage)
    setPageSize(initialPageSize)
    setCursor(null)
    setSortField(undefined)
    setSortOrder('desc')
  }, [initialPage, initialPageSize])

  // Current pagination parameters
  const paginationParams = useMemo((): PaginationParams => ({
    page: currentPage,
    pageSize,
    cursor: cursor || undefined,
    sortField,
    sortOrder
  }), [currentPage, pageSize, cursor, sortField, sortOrder])

  // Helper methods
  const canGoNext = useCallback((meta?: PaginationMeta): boolean => {
    if (!meta) return false
    return meta.hasNext || Boolean(meta.nextCursor)
  }, [])

  const canGoPrevious = useCallback((meta?: PaginationMeta): boolean => {
    if (!meta) return currentPage > 1
    return meta.hasPrevious || Boolean(meta.prevCursor) || currentPage > 1
  }, [currentPage])

  const getPageNumbers = useCallback((meta?: PaginationMeta): number[] => {
    if (!meta) return [1]

    const { totalPages } = meta
    const current = currentPage
    const delta = 2 // Number of pages to show on each side of current page

    let start = Math.max(1, current - delta)
    let end = Math.min(totalPages, current + delta)

    // Adjust if we're near the beginning or end
    if (end - start < 2 * delta) {
      if (start === 1) {
        end = Math.min(totalPages, start + 2 * delta)
      } else if (end === totalPages) {
        start = Math.max(1, end - 2 * delta)
      }
    }

    const pages: number[] = []
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    return pages
  }, [currentPage])

  return {
    // Current state
    currentPage,
    pageSize,
    cursor,
    sortField,
    sortOrder,

    // Navigation methods
    goToPage,
    goToNextPage,
    goToPreviousPage,
    goToFirstPage,
    goToLastPage,

    // Cursor navigation methods
    goToNextCursor,
    goToPreviousCursor,

    // Configuration methods
    setPageSize: handleSetPageSize,
    setSorting,
    resetPagination,

    // Current pagination parameters
    paginationParams,

    // Helper methods
    canGoNext,
    canGoPrevious,
    getPageNumbers
  }
}