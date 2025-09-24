import { describe, it, expect, beforeEach, vi } from 'vitest'
import { PaginationCache } from '../paginationCache'
import type { EnhancedPaginatedResult, PaginationParams } from '../../types/domain'

interface TestItem {
  id: number
  title: string
}

describe('PaginationCache', () => {
  let cache: PaginationCache<TestItem>
  let mockData: EnhancedPaginatedResult<TestItem>
  let params: PaginationParams

  beforeEach(() => {
    cache = new PaginationCache<TestItem>({
      maxCacheSize: 5,
      maxAge: 60000, // 1 minute for testing
      staleTolerance: 30000 // 30 seconds
    })

    mockData = {
      items: [
        { id: 1, title: 'Item 1' },
        { id: 2, title: 'Item 2' }
      ],
      pagination: {
        page: 1,
        pageSize: 2,
        totalCount: 10,
        totalPages: 5,
        hasNext: true,
        hasPrevious: false,
        nextCursor: 'cursor-2',
        prevCursor: null
      }
    }

    params = {
      page: 1,
      pageSize: 2,
      sortField: 'created_at',
      sortOrder: 'desc'
    }
  })

  describe('basic cache operations', () => {
    it('should store and retrieve cached pages', () => {
      // Store data
      cache.set(params, mockData, 'test-query')

      // Retrieve data
      const cached = cache.get(params, 'test-query')

      expect(cached).toBeDefined()
      expect(cached!.data).toEqual(mockData.items)
      expect(cached!.pagination).toEqual(mockData.pagination)
      expect(cached!.loading).toBe(false)
      expect(cached!.stale).toBe(false)
    })

    it('should return null for cache misses', () => {
      const otherParams = { ...params, page: 2 }
      const cached = cache.get(otherParams, 'test-query')

      expect(cached).toBeNull()
    })

    it('should generate different cache keys for different parameters', () => {
      const params1 = { page: 1, pageSize: 10 }
      const params2 = { page: 2, pageSize: 10 }
      const params3 = { page: 1, pageSize: 20 }

      cache.set(params1, mockData, 'test')
      cache.set(params2, mockData, 'test')
      cache.set(params3, mockData, 'test')

      expect(cache.get(params1, 'test')).toBeDefined()
      expect(cache.get(params2, 'test')).toBeDefined()
      expect(cache.get(params3, 'test')).toBeDefined()
    })

    it('should handle cursor-based cache keys differently', () => {
      const pageParams = { page: 2, pageSize: 10 }
      const cursorParams = { page: 2, pageSize: 10, cursor: 'abc123' }

      cache.set(pageParams, mockData, 'test')
      cache.set(cursorParams, mockData, 'test')

      expect(cache.get(pageParams, 'test')).toBeDefined()
      expect(cache.get(cursorParams, 'test')).toBeDefined()

      // They should be different entries
      const pageEntry = cache.get(pageParams, 'test')
      const cursorEntry = cache.get(cursorParams, 'test')
      expect(pageEntry!.queryKey).not.toBe(cursorEntry!.queryKey)
    })
  })

  describe('loading state management', () => {
    it('should track loading state', () => {
      expect(cache.isLoading(params, 'test')).toBe(false)

      cache.setLoading(params, 'test')
      expect(cache.isLoading(params, 'test')).toBe(true)

      cache.set(params, mockData, 'test')
      expect(cache.isLoading(params, 'test')).toBe(false)
    })

    it('should create placeholder entries when setting loading', () => {
      cache.setLoading(params, 'test')

      const cached = cache.get(params, 'test')
      expect(cached).toBeDefined()
      expect(cached!.loading).toBe(true)
      expect(cached!.data).toEqual([])
    })
  })

  describe('LRU eviction', () => {
    it('should evict least recently used entries when maxCacheSize is exceeded', () => {
      // Fill cache to max capacity (5)
      for (let i = 1; i <= 5; i++) {
        const testParams = { ...params, page: i }
        cache.set(testParams, mockData, 'test')
      }

      // All 5 should be cached
      for (let i = 1; i <= 5; i++) {
        const testParams = { ...params, page: i }
        expect(cache.get(testParams, 'test')).toBeDefined()
      }

      // Access page 2 to make it more recently used
      cache.get({ ...params, page: 2 }, 'test')

      // Add a 6th entry, should evict page 1 (least recently used)
      cache.set({ ...params, page: 6 }, mockData, 'test')

      expect(cache.get({ ...params, page: 1 }, 'test')).toBeNull() // Evicted
      expect(cache.get({ ...params, page: 2 }, 'test')).toBeDefined() // Recently accessed
      expect(cache.get({ ...params, page: 6 }, 'test')).toBeDefined() // Newly added
    })
  })

  describe('staleness management', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should mark entries as stale after staleTolerance period', () => {
      cache.set(params, mockData, 'test')

      // Initially not stale
      const fresh = cache.get(params, 'test')
      expect(fresh!.stale).toBe(false)

      // Advance time past staleTolerance (30 seconds)
      vi.advanceTimersByTime(31000)

      // Should now be marked as stale
      const stale = cache.get(params, 'test')
      expect(stale!.stale).toBe(true)
    })

    it('should remove entries older than maxAge', () => {
      cache.set(params, mockData, 'test')

      // Initially present
      expect(cache.get(params, 'test')).toBeDefined()

      // Advance time past maxAge (1 minute)
      vi.advanceTimersByTime(61000)

      // Add another entry to trigger cleanup
      cache.set({ ...params, page: 2 }, mockData, 'test')

      // Original entry should be removed
      expect(cache.get(params, 'test')).toBeNull()
    })
  })

  describe('prefetch candidates', () => {
    it('should identify pages to prefetch ahead', () => {
      const candidates = cache.getPrefetchCandidates(params, mockData, 'test')

      // Should include next pages (default 2 ahead, 1 behind)
      const expectedPages = [2, 3] // Pages ahead
      const actualPages = candidates
        .filter(c => !c.cursor)
        .map(c => c.page)
        .filter(p => p !== undefined && p > params.page!)

      expect(actualPages).toEqual(expect.arrayContaining(expectedPages))
    })

    it('should include cursor-based prefetch when available', () => {
      const candidates = cache.getPrefetchCandidates(params, mockData, 'test')

      const cursorCandidate = candidates.find(c => c.cursor === 'cursor-2')
      expect(cursorCandidate).toBeDefined()
      expect(cursorCandidate!.page).toBe(2)
    })

    it('should exclude already cached pages from candidates', () => {
      // Cache page 2
      cache.set({ ...params, page: 2 }, mockData, 'test')

      const candidates = cache.getPrefetchCandidates(params, mockData, 'test')
      const page2Candidate = candidates.find(c => c.page === 2 && !c.cursor)

      expect(page2Candidate).toBeUndefined()
    })
  })

  describe('cache invalidation', () => {
    it('should invalidate entries matching string pattern', () => {
      cache.set(params, mockData, 'users-query')
      cache.set(params, mockData, 'posts-query')

      const invalidatedCount = cache.invalidate('users')

      expect(invalidatedCount).toBe(1)
      expect(cache.get(params, 'users-query')!.stale).toBe(true)
      expect(cache.get(params, 'posts-query')!.stale).toBe(false)
    })

    it('should invalidate entries matching regex pattern', () => {
      cache.set({ ...params, page: 1 }, mockData, 'test')
      cache.set({ ...params, page: 2 }, mockData, 'test')

      const invalidatedCount = cache.invalidate(/page-[12]/)

      expect(invalidatedCount).toBe(2)
    })
  })

  describe('cache statistics', () => {
    it('should provide accurate cache statistics', () => {
      // Add some entries
      cache.set({ ...params, page: 1 }, mockData, 'test')
      cache.setLoading({ ...params, page: 2 }, 'test')

      const stats = cache.getStats()

      expect(stats.size).toBe(2) // 1 cached + 1 loading placeholder
      expect(stats.loadingCount).toBe(1)
      expect(stats.staleCount).toBe(0)
      expect(stats.maxSize).toBe(5)
    })
  })

  describe('cache clearing', () => {
    it('should clear all cached data', () => {
      cache.set({ ...params, page: 1 }, mockData, 'test')
      cache.set({ ...params, page: 2 }, mockData, 'test')
      cache.setLoading({ ...params, page: 3 }, 'test')

      expect(cache.getStats().size).toBe(3)

      cache.clear()

      expect(cache.getStats().size).toBe(0)
      expect(cache.getStats().loadingCount).toBe(0)
      expect(cache.get({ ...params, page: 1 }, 'test')).toBeNull()
    })
  })
})