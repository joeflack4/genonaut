import { useRef, useCallback } from 'react'

interface CursorCacheEntry {
  cursor: string
  timestamp: number
  filters: string // JSON of active filters
}

/**
 * Hook to manage cursor caching for hybrid page/cursor pagination.
 *
 * Maintains a Map<pageNumber, cursor> to enable cursor-based performance
 * while showing clean page numbers in the URL.
 */
export function usePaginationCursorCache() {
  const cacheRef = useRef<Map<number, CursorCacheEntry>>(new Map())
  const currentFiltersRef = useRef<string>('')

  /**
   * Get cursor for a specific page number.
   * Returns undefined if cursor is not cached, stale, or filters have changed.
   */
  const getCursor = useCallback((pageNum: number): string | undefined => {
    const entry = cacheRef.current.get(pageNum)
    if (!entry) return undefined

    // Check if filters have changed
    if (entry.filters !== currentFiltersRef.current) {
      return undefined
    }

    // Check if cache is stale (> 5 minutes old)
    const isStale = Date.now() - entry.timestamp > 5 * 60 * 1000
    if (isStale) return undefined

    return entry.cursor
  }, [])

  /**
   * Store cursor for a specific page number.
   */
  const setCursor = useCallback((pageNum: number, cursor: string) => {
    cacheRef.current.set(pageNum, {
      cursor,
      timestamp: Date.now(),
      filters: currentFiltersRef.current,
    })
  }, [])

  /**
   * Clear all cached cursors.
   */
  const clearCache = useCallback(() => {
    cacheRef.current.clear()
  }, [])

  /**
   * Update active filters and clear cache if filters have changed.
   * Call this whenever search, sort, tags, or content toggles change.
   */
  const updateFilters = useCallback((filters: Record<string, unknown>) => {
    const newFiltersStr = JSON.stringify(filters)
    if (newFiltersStr !== currentFiltersRef.current) {
      currentFiltersRef.current = newFiltersStr
      clearCache()
      return true // Filters changed
    }
    return false // Filters unchanged
  }, [clearCache])

  /**
   * Get cache statistics for debugging/monitoring.
   */
  const getCacheStats = useCallback(() => {
    return {
      size: cacheRef.current.size,
      pages: Array.from(cacheRef.current.keys()).sort((a, b) => a - b),
    }
  }, [])

  return {
    getCursor,
    setCursor,
    clearCache,
    updateFilters,
    getCacheStats,
  }
}
