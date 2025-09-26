import { useState, useEffect, useRef, useCallback } from 'react'

interface CacheEntry<T> {
  data: T
  timestamp: number
  loading: boolean
  error: string | null
}

interface QueryCacheOptions {
  ttl?: number // Time to live in milliseconds
  staleWhileRevalidate?: boolean // Return stale data while fetching fresh data
  backgroundRefresh?: boolean // Refresh data in background
  retryOnError?: boolean // Retry failed requests
  maxRetries?: number // Maximum retry attempts
}

class QueryCache {
  private cache = new Map<string, CacheEntry<unknown>>()
  private pendingRequests = new Map<string, Promise<unknown>>()
  private refreshTimers = new Map<string, NodeJS.Timeout>()

  get<T>(key: string): CacheEntry<T> | undefined {
    return this.cache.get(key) as CacheEntry<T> | undefined
  }

  set<T>(key: string, data: T, options: QueryCacheOptions = {}) {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      loading: false,
      error: null,
    }

    this.cache.set(key, entry)

    // Set up background refresh if enabled
    if (options.backgroundRefresh && options.ttl) {
      this.scheduleBackgroundRefresh(key, options.ttl)
    }
  }

  setLoading(key: string, loading: boolean) {
    const entry = this.cache.get(key)
    if (entry) {
      entry.loading = loading
      this.cache.set(key, entry)
    } else {
      this.cache.set(key, {
        data: null,
        timestamp: Date.now(),
        loading,
        error: null,
      })
    }
  }

  setError(key: string, error: string) {
    const entry = this.cache.get(key) || {
      data: null,
      timestamp: Date.now(),
      loading: false,
      error: null,
    }
    entry.error = error
    entry.loading = false
    this.cache.set(key, entry)
  }

  isStale(key: string, ttl: number): boolean {
    const entry = this.cache.get(key)
    if (!entry) return true
    return Date.now() - entry.timestamp > ttl
  }

  invalidate(key: string) {
    this.cache.delete(key)
    this.pendingRequests.delete(key)
    const timer = this.refreshTimers.get(key)
    if (timer) {
      clearTimeout(timer)
      this.refreshTimers.delete(key)
    }
  }

  invalidatePattern(pattern: string) {
    const regex = new RegExp(pattern)
    const keysToDelete: string[] = []

    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        keysToDelete.push(key)
      }
    }

    keysToDelete.forEach(key => this.invalidate(key))
  }

  setPendingRequest(key: string, promise: Promise<unknown>) {
    this.pendingRequests.set(key, promise)
    promise.finally(() => {
      this.pendingRequests.delete(key)
    })
  }

  getPendingRequest(key: string): Promise<unknown> | undefined {
    return this.pendingRequests.get(key)
  }

  private scheduleBackgroundRefresh(key: string, ttl: number) {
    const existingTimer = this.refreshTimers.get(key)
    if (existingTimer) {
      clearTimeout(existingTimer)
    }

    const timer = setTimeout(() => {
      // Trigger background refresh event
      window.dispatchEvent(new CustomEvent('queryCache:backgroundRefresh', { detail: { key } }))
      this.refreshTimers.delete(key)
    }, ttl)

    this.refreshTimers.set(key, timer)
  }

  clear() {
    this.cache.clear()
    this.pendingRequests.clear()
    this.refreshTimers.forEach(timer => clearTimeout(timer))
    this.refreshTimers.clear()
  }

  getStats() {
    return {
      cacheSize: this.cache.size,
      pendingRequests: this.pendingRequests.size,
      scheduledRefreshes: this.refreshTimers.size,
    }
  }
}

// Global cache instance
const globalQueryCache = new QueryCache()

export function useQueryCache<T>(
  key: string,
  queryFn: () => Promise<T>,
  options: QueryCacheOptions = {}
) {
  const {
    ttl = 5 * 60 * 1000, // 5 minutes default
    staleWhileRevalidate = true,
    retryOnError = true,
    maxRetries = 3,
  } = options

  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const retryCountRef = useRef(0)
  const isMountedRef = useRef(true)

  // Function to execute the query
  const executeQuery = useCallback(async (isBackgroundRefresh = false) => {
    // Check if there's already a pending request for this key
    const pendingRequest = globalQueryCache.getPendingRequest(key)
    if (pendingRequest && !isBackgroundRefresh) {
      try {
        const result = await pendingRequest
        if (isMountedRef.current) {
          setData(result as T)
          setLoading(false)
          setError(null)
        }
        return result
      } catch (err) {
        if (isMountedRef.current) {
          setError(err instanceof Error ? err.message : 'Query failed')
          setLoading(false)
        }
        throw err
      }
    }

    // Set loading state if not background refresh
    if (!isBackgroundRefresh && isMountedRef.current) {
      setLoading(true)
      setError(null)
    }

    globalQueryCache.setLoading(key, !isBackgroundRefresh)

    try {
      // Create and store the promise
      const queryPromise = queryFn()
      globalQueryCache.setPendingRequest(key, queryPromise)

      const result = await queryPromise

      // Update cache and state
      globalQueryCache.set(key, result, options)

      if (isMountedRef.current) {
        setData(result)
        setLoading(false)
        setError(null)
      }

      retryCountRef.current = 0
      return result

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Query failed'
      globalQueryCache.setError(key, errorMessage)

      if (isMountedRef.current) {
        setError(errorMessage)
        setLoading(false)
      }

      // Retry logic
      if (retryOnError && retryCountRef.current < maxRetries) {
        retryCountRef.current++
        const delay = Math.min(1000 * Math.pow(2, retryCountRef.current - 1), 10000)

        setTimeout(() => {
          if (isMountedRef.current) {
            executeQuery(isBackgroundRefresh)
          }
        }, delay)
      }

      throw err
    }
  }, [key, queryFn, options, retryOnError, maxRetries])

  // Function to manually refetch data
  const refetch = useCallback(() => {
    return executeQuery(false)
  }, [executeQuery])

  // Function to invalidate cache for this key
  const invalidate = useCallback(() => {
    globalQueryCache.invalidate(key)
    if (isMountedRef.current) {
      setData(null)
      setError(null)
    }
  }, [key])

  // Initial data fetch and cache check
  useEffect(() => {
    isMountedRef.current = true

    const cachedEntry = globalQueryCache.get<T>(key)

    if (cachedEntry && !cachedEntry.loading) {
      // We have cached data
      setData(cachedEntry.data)
      setError(cachedEntry.error)
      setLoading(false)

      // Check if data is stale
      const isStale = globalQueryCache.isStale(key, ttl)

      if (isStale) {
        if (staleWhileRevalidate && cachedEntry.data && !cachedEntry.error) {
          // Return stale data immediately, fetch fresh data in background
          executeQuery(true)
        } else {
          // Data is stale and we don't have good data, fetch fresh
          executeQuery(false)
        }
      }
    } else {
      // No cached data, fetch fresh
      executeQuery(false)
    }

    return () => {
      isMountedRef.current = false
    }
  }, [key, executeQuery, ttl, staleWhileRevalidate])

  // Listen for background refresh events
  useEffect(() => {
    const handleBackgroundRefresh = (event: CustomEvent) => {
      if (event.detail.key === key && isMountedRef.current) {
        executeQuery(true)
      }
    }

    window.addEventListener('queryCache:backgroundRefresh', handleBackgroundRefresh as EventListener)

    return () => {
      window.removeEventListener('queryCache:backgroundRefresh', handleBackgroundRefresh as EventListener)
    }
  }, [key, executeQuery])

  return {
    data,
    loading,
    error,
    refetch,
    invalidate,
    isStale: data ? globalQueryCache.isStale(key, ttl) : false,
  }
}

// Utility hook for invalidating multiple cache entries
export function useCacheInvalidation() {
  const invalidateKey = useCallback((key: string) => {
    globalQueryCache.invalidate(key)
  }, [])

  const invalidatePattern = useCallback((pattern: string) => {
    globalQueryCache.invalidatePattern(pattern)
  }, [])

  const clearCache = useCallback(() => {
    globalQueryCache.clear()
  }, [])

  const getCacheStats = useCallback(() => {
    return globalQueryCache.getStats()
  }, [])

  return {
    invalidateKey,
    invalidatePattern,
    clearCache,
    getCacheStats,
  }
}

// Hook for prefetching data
export function usePrefetch() {
  const prefetch = useCallback(async <T>(
    key: string,
    queryFn: () => Promise<T>,
    options: QueryCacheOptions = {}
  ) => {
    const cachedEntry = globalQueryCache.get<T>(key)
    const isStale = cachedEntry ? globalQueryCache.isStale(key, options.ttl || 5 * 60 * 1000) : true

    if (!cachedEntry || isStale) {
      try {
        globalQueryCache.setLoading(key, true)
        const result = await queryFn()
        globalQueryCache.set(key, result, options)
        return result
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Prefetch failed'
        globalQueryCache.setError(key, errorMessage)
        throw err
      }
    }

    return cachedEntry.data
  }, [])

  return { prefetch }
}