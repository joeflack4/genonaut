import type { EnhancedPaginatedResult, PaginationParams } from '../types/domain'

export interface CachedPage<T> {
  data: T[]
  pagination: {
    page: number
    pageSize: number
    totalCount: number
    totalPages: number
    hasNext: boolean
    hasPrevious: boolean
    nextCursor?: string | null
    prevCursor?: string | null
  }
  timestamp: number
  stale: boolean
  loading: boolean
  queryKey: string
}

export interface CacheEvictionPolicy {
  maxCacheSize: number
  maxAge: number // in milliseconds
  staleTolerance: number // in milliseconds
}

export interface PrefetchStrategy {
  enabled: boolean
  pagesAhead: number
  pagesBehind: number
  delay: number // in milliseconds
  bandwidthAware: boolean
}

export interface PaginationCacheOptions {
  maxCacheSize?: number
  maxAge?: number // 15 minutes default
  staleTolerance?: number // 5 minutes default
  prefetchStrategy?: Partial<PrefetchStrategy>
}

/**
 * Advanced pagination cache with LRU eviction, prefetching, and bandwidth awareness
 */
export class PaginationCache<T> {
  private pages = new Map<string, CachedPage<T>>()
  private accessOrder = new Map<string, number>() // LRU tracking
  private prefetchQueue: string[] = []
  private loadingKeys = new Set<string>()
  private accessCounter = 0

  private readonly evictionPolicy: CacheEvictionPolicy
  private readonly prefetchStrategy: PrefetchStrategy

  constructor(options: PaginationCacheOptions = {}) {
    this.evictionPolicy = {
      maxCacheSize: options.maxCacheSize ?? 10,
      maxAge: options.maxAge ?? 15 * 60 * 1000, // 15 minutes
      staleTolerance: options.staleTolerance ?? 5 * 60 * 1000 // 5 minutes
    }

    this.prefetchStrategy = {
      enabled: options.prefetchStrategy?.enabled ?? true,
      pagesAhead: options.prefetchStrategy?.pagesAhead ?? 2,
      pagesBehind: options.prefetchStrategy?.pagesBehind ?? 1,
      delay: options.prefetchStrategy?.delay ?? 500,
      bandwidthAware: options.prefetchStrategy?.bandwidthAware ?? true
    }
  }

  /**
   * Generate a cache key from pagination parameters
   */
  private generateCacheKey(params: PaginationParams, queryBase?: string): string {
    const baseKey = queryBase || 'default'
    const sortKey = params.sortField && params.sortOrder
      ? `${params.sortField}-${params.sortOrder}`
      : 'default-sort'

    if (params.cursor) {
      return `${baseKey}-cursor-${params.cursor}-${params.pageSize}-${sortKey}`
    }

    return `${baseKey}-page-${params.page}-${params.pageSize}-${sortKey}`
  }

  /**
   * Set a page in the cache
   */
  set(
    params: PaginationParams,
    result: EnhancedPaginatedResult<T>,
    queryBase?: string
  ): void {
    const key = this.generateCacheKey(params, queryBase)

    const cachedPage: CachedPage<T> = {
      data: result.items,
      pagination: result.pagination,
      timestamp: Date.now(),
      stale: false,
      loading: false,
      queryKey: key
    }

    this.pages.set(key, cachedPage)
    this.updateAccessOrder(key)
    this.loadingKeys.delete(key)

    // Trigger cleanup if needed
    this.cleanup()

    // Schedule prefetch if enabled
    if (this.prefetchStrategy.enabled) {
      this.schedulePrefetch(params, result, queryBase)
    }
  }

  /**
   * Get a page from the cache
   */
  get(params: PaginationParams, queryBase?: string): CachedPage<T> | null {
    const key = this.generateCacheKey(params, queryBase)
    const cached = this.pages.get(key)

    if (!cached) return null

    // Update access order for LRU
    this.updateAccessOrder(key)

    // Check if data is stale
    const age = Date.now() - cached.timestamp
    const isStale = age > this.evictionPolicy.staleTolerance

    if (isStale && !cached.stale) {
      cached.stale = true
    }

    return cached
  }

  /**
   * Check if a page is currently loading
   */
  isLoading(params: PaginationParams, queryBase?: string): boolean {
    const key = this.generateCacheKey(params, queryBase)
    return this.loadingKeys.has(key)
  }

  /**
   * Mark a page as loading
   */
  setLoading(params: PaginationParams, queryBase?: string): void {
    const key = this.generateCacheKey(params, queryBase)
    this.loadingKeys.add(key)

    // Create placeholder entry if it doesn't exist
    if (!this.pages.has(key)) {
      this.pages.set(key, {
        data: [],
        pagination: {
          page: params.page ?? 1,
          pageSize: params.pageSize ?? 50,
          totalCount: 0,
          totalPages: 0,
          hasNext: false,
          hasPrevious: false
        },
        timestamp: Date.now(),
        stale: false,
        loading: true,
        queryKey: key
      })
    } else {
      const cached = this.pages.get(key)!
      cached.loading = true
    }
  }

  /**
   * Remove a page from the cache
   */
  delete(params: PaginationParams, queryBase?: string): boolean {
    const key = this.generateCacheKey(params, queryBase)
    this.accessOrder.delete(key)
    this.loadingKeys.delete(key)
    return this.pages.delete(key)
  }

  /**
   * Clear all cached data
   */
  clear(): void {
    this.pages.clear()
    this.accessOrder.clear()
    this.prefetchQueue.length = 0
    this.loadingKeys.clear()
    this.accessCounter = 0
  }

  /**
   * Invalidate cache entries matching a pattern
   */
  invalidate(pattern: string | RegExp): number {
    let count = 0

    for (const [key, page] of this.pages.entries()) {
      const matches = typeof pattern === 'string'
        ? key.includes(pattern)
        : pattern.test(key)

      if (matches) {
        page.stale = true
        count++
      }
    }

    return count
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    size: number
    maxSize: number
    hitRate: number
    staleCount: number
    loadingCount: number
    oldestEntry: number | null
    newestEntry: number | null
  } {
    const now = Date.now()
    let staleCount = 0
    let oldestTimestamp: number | null = null
    let newestTimestamp: number | null = null

    for (const page of this.pages.values()) {
      if (page.stale) staleCount++

      if (!oldestTimestamp || page.timestamp < oldestTimestamp) {
        oldestTimestamp = page.timestamp
      }

      if (!newestTimestamp || page.timestamp > newestTimestamp) {
        newestTimestamp = page.timestamp
      }
    }

    return {
      size: this.pages.size,
      maxSize: this.evictionPolicy.maxCacheSize,
      hitRate: 0, // TODO: Implement hit rate tracking if needed
      staleCount,
      loadingCount: this.loadingKeys.size,
      oldestEntry: oldestTimestamp ? now - oldestTimestamp : null,
      newestEntry: newestTimestamp ? now - newestTimestamp : null
    }
  }

  /**
   * Get all prefetch candidates for a given page
   */
  getPrefetchCandidates(
    params: PaginationParams,
    currentResult: EnhancedPaginatedResult<T>,
    queryBase?: string
  ): PaginationParams[] {
    const candidates: PaginationParams[] = []
    const { pagination } = currentResult

    // Prefetch ahead (next pages)
    for (let i = 1; i <= this.prefetchStrategy.pagesAhead; i++) {
      const nextPage = pagination.page + i
      if (nextPage <= pagination.totalPages) {
        candidates.push({
          ...params,
          page: nextPage,
          cursor: undefined // Use page-based for predictable prefetch
        })
      }
    }

    // Prefetch behind (previous pages)
    for (let i = 1; i <= this.prefetchStrategy.pagesBehind; i++) {
      const prevPage = pagination.page - i
      if (prevPage >= 1) {
        candidates.push({
          ...params,
          page: prevPage,
          cursor: undefined
        })
      }
    }

    // Add cursor-based prefetch if available
    if (pagination.nextCursor) {
      candidates.push({
        ...params,
        page: pagination.page + 1,
        cursor: pagination.nextCursor
      })
    }

    if (pagination.prevCursor) {
      candidates.push({
        ...params,
        page: pagination.page - 1,
        cursor: pagination.prevCursor
      })
    }

    // Filter out already cached or loading pages
    return candidates.filter(candidate => {
      const key = this.generateCacheKey(candidate, queryBase)
      return !this.pages.has(key) && !this.loadingKeys.has(key)
    })
  }

  /**
   * Update access order for LRU
   */
  private updateAccessOrder(key: string): void {
    this.accessOrder.set(key, ++this.accessCounter)
  }

  /**
   * Schedule prefetch for adjacent pages
   */
  private schedulePrefetch(
    params: PaginationParams,
    result: EnhancedPaginatedResult<T>,
    queryBase?: string
  ): void {
    if (!this.prefetchStrategy.enabled) return

    const candidates = this.getPrefetchCandidates(params, result, queryBase)

    // Add to prefetch queue
    candidates.forEach(candidate => {
      const key = this.generateCacheKey(candidate, queryBase)
      if (!this.prefetchQueue.includes(key)) {
        this.prefetchQueue.push(key)
      }
    })
  }

  /**
   * Cleanup expired and excess entries
   */
  private cleanup(): void {
    const now = Date.now()

    // Remove expired entries
    for (const [key, page] of this.pages.entries()) {
      const age = now - page.timestamp
      if (age > this.evictionPolicy.maxAge) {
        this.pages.delete(key)
        this.accessOrder.delete(key)
        this.loadingKeys.delete(key)
      }
    }

    // LRU eviction if over maxCacheSize
    while (this.pages.size > this.evictionPolicy.maxCacheSize) {
      const lruKey = this.getLRUKey()
      if (lruKey) {
        this.pages.delete(lruKey)
        this.accessOrder.delete(lruKey)
        this.loadingKeys.delete(lruKey)
      } else {
        break // Safety break
      }
    }
  }

  /**
   * Get the least recently used key
   */
  private getLRUKey(): string | null {
    let lruKey: string | null = null
    let minAccess = Infinity

    for (const [key, accessTime] of this.accessOrder.entries()) {
      if (accessTime < minAccess) {
        minAccess = accessTime
        lruKey = key
      }
    }

    return lruKey
  }
}