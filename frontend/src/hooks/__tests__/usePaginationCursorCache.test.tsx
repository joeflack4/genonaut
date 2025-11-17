import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { usePaginationCursorCache } from '../usePaginationCursorCache'

describe('usePaginationCursorCache', () => {
  beforeEach(() => {
    // Clear any existing cache between tests
    localStorage.clear()
  })

  describe('basic functionality', () => {
    it('initializes with empty cache', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      expect(result.current.getCursor(1)).toBeUndefined()
      expect(result.current.getCursor(2)).toBeUndefined()
    })

    it('stores and retrieves cursors', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, 'cursor-for-page-2')
        result.current.setCursor(3, 'cursor-for-page-3')
      })

      expect(result.current.getCursor(2)).toBe('cursor-for-page-2')
      expect(result.current.getCursor(3)).toBe('cursor-for-page-3')
      expect(result.current.getCursor(1)).toBeUndefined()
    })

    it('clears cache', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, 'cursor-for-page-2')
        result.current.setCursor(3, 'cursor-for-page-3')
      })

      expect(result.current.getCursor(2)).toBe('cursor-for-page-2')

      act(() => {
        result.current.clearCache()
      })

      expect(result.current.getCursor(2)).toBeUndefined()
      expect(result.current.getCursor(3)).toBeUndefined()
    })
  })

  describe('filter updates', () => {
    it('clears cache when filters change', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      const initialFilters = { search: 'cat', sort: 'recent' }
      const newFilters = { search: 'dog', sort: 'recent' }

      act(() => {
        result.current.updateFilters(initialFilters)
        result.current.setCursor(2, 'cursor-for-page-2')
      })

      expect(result.current.getCursor(2)).toBe('cursor-for-page-2')

      act(() => {
        result.current.updateFilters(newFilters)
      })

      expect(result.current.getCursor(2)).toBeUndefined()
    })

    it('preserves cache when filters remain the same', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      const filters = { search: 'cat', sort: 'recent' }

      act(() => {
        result.current.updateFilters(filters)
        result.current.setCursor(2, 'cursor-for-page-2')
      })

      expect(result.current.getCursor(2)).toBe('cursor-for-page-2')

      act(() => {
        result.current.updateFilters(filters) // Same filters
      })

      expect(result.current.getCursor(2)).toBe('cursor-for-page-2')
    })

    it('handles complex filter objects', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      const filters1 = {
        search: 'test',
        contentTypes: ['regular', 'auto'],
        tags: ['landscape', 'nature'],
        userId: '123',
      }

      const filters2 = {
        search: 'test',
        contentTypes: ['regular', 'auto'],
        tags: ['landscape', 'nature'],
        userId: '456', // Different user ID
      }

      act(() => {
        result.current.updateFilters(filters1)
        result.current.setCursor(2, 'cursor-page-2')
      })

      expect(result.current.getCursor(2)).toBe('cursor-page-2')

      act(() => {
        result.current.updateFilters(filters2)
      })

      expect(result.current.getCursor(2)).toBeUndefined()
    })
  })

  describe('instance behavior', () => {
    it('does not persist cursors across hook instances', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, 'cursor-for-page-2')
        result.current.setCursor(3, 'cursor-for-page-3')
      })

      // Create a new hook instance (simulating component remount)
      const { result: newResult } = renderHook(() => usePaginationCursorCache())

      // New instance starts with empty cache
      expect(newResult.current.getCursor(2)).toBeUndefined()
      expect(newResult.current.getCursor(3)).toBeUndefined()
    })

    it('maintains separate cache for each hook instance', () => {
      const { result: result1 } = renderHook(() => usePaginationCursorCache())
      const { result: result2 } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result1.current.setCursor(2, 'cursor-instance-1')
        result2.current.setCursor(2, 'cursor-instance-2')
      })

      expect(result1.current.getCursor(2)).toBe('cursor-instance-1')
      expect(result2.current.getCursor(2)).toBe('cursor-instance-2')
    })

    it('cache stats reflect current instance state', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, 'cursor-2')
        result.current.setCursor(3, 'cursor-3')
        result.current.setCursor(5, 'cursor-5')
      })

      const stats = result.current.getCacheStats()
      expect(stats.size).toBe(3)
      expect(stats.pages).toEqual([2, 3, 5])
    })
  })

  describe('edge cases', () => {
    it('handles invalid page numbers gracefully', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, 'cursor')
      })

      expect(result.current.getCursor(0)).toBeUndefined()
      expect(result.current.getCursor(-1)).toBeUndefined()
      expect(result.current.getCursor(NaN)).toBeUndefined()
    })

    it('overwrites existing cursor for same page', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, 'first-cursor')
      })

      expect(result.current.getCursor(2)).toBe('first-cursor')

      act(() => {
        result.current.setCursor(2, 'updated-cursor')
      })

      expect(result.current.getCursor(2)).toBe('updated-cursor')
    })

    it('handles empty cursor values', () => {
      const { result } = renderHook(() => usePaginationCursorCache())

      act(() => {
        result.current.setCursor(2, '')
      })

      expect(result.current.getCursor(2)).toBe('')

      act(() => {
        result.current.setCursor(3, 'valid-cursor')
        result.current.setCursor(3, '')
      })

      expect(result.current.getCursor(3)).toBe('')
    })
  })
})