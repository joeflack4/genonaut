import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { Box } from '@mui/material'

interface VirtualScrollListProps<T> {
  items: T[]
  itemHeight: number
  containerHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  overscan?: number
  className?: string
  onScroll?: (scrollTop: number) => void
}

export function VirtualScrollList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className,
  onScroll,
}: VirtualScrollListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Calculate visible range
  const visibleRange = useMemo(() => {
    const visibleStart = Math.floor(scrollTop / itemHeight)
    const visibleEnd = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight)
    )

    // Add overscan items
    const start = Math.max(0, visibleStart - overscan)
    const end = Math.min(items.length - 1, visibleEnd + overscan)

    return { start, end }
  }, [scrollTop, itemHeight, containerHeight, items.length, overscan])

  // Get visible items
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end + 1)
  }, [items, visibleRange])

  // Handle scroll events
  const handleScroll = useCallback((e: Event) => {
    const target = e.target as HTMLDivElement
    const newScrollTop = target.scrollTop
    setScrollTop(newScrollTop)
    onScroll?.(newScrollTop)
  }, [onScroll])

  // Set up scroll listener
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll)
    }
  }, [handleScroll])

  // Total height of all items
  const totalHeight = items.length * itemHeight

  return (
    <Box
      ref={scrollContainerRef}
      sx={{
        height: containerHeight,
        overflow: 'auto',
        position: 'relative',
      }}
      className={className}
    >
      {/* Spacer to maintain scroll height */}
      <Box sx={{ height: totalHeight, position: 'relative' }}>
        {/* Render visible items */}
        <Box
          sx={{
            position: 'absolute',
            top: visibleRange.start * itemHeight,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) => {
            const actualIndex = visibleRange.start + index
            return (
              <Box
                key={actualIndex}
                sx={{
                  height: itemHeight,
                  overflow: 'hidden',
                }}
              >
                {renderItem(item, actualIndex)}
              </Box>
            )
          })}
        </Box>
      </Box>
    </Box>
  )
}

// Hook for dynamic item heights (more complex virtualization)
interface VariableVirtualScrollListProps<T> {
  items: T[]
  estimatedItemHeight: number
  containerHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  getItemHeight?: (index: number) => number
  overscan?: number
  className?: string
  onScroll?: (scrollTop: number) => void
}

export function VariableVirtualScrollList<T>({
  items,
  estimatedItemHeight,
  containerHeight,
  renderItem,
  getItemHeight,
  overscan = 3,
  className,
  onScroll,
}: VariableVirtualScrollListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  const [itemHeights, setItemHeights] = useState<number[]>([])
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<(HTMLDivElement | null)[]>([])

  // Initialize item heights with estimates
  useEffect(() => {
    if (itemHeights.length !== items.length) {
      const newHeights = new Array(items.length).fill(estimatedItemHeight)
      setItemHeights(newHeights)
    }
  }, [items.length, estimatedItemHeight, itemHeights.length])

  // Calculate cumulative heights for positioning
  const cumulativeHeights = useMemo(() => {
    const heights = [0]
    for (let i = 0; i < itemHeights.length; i++) {
      const height = getItemHeight?.(i) || itemHeights[i] || estimatedItemHeight
      heights.push(heights[i] + height)
    }
    return heights
  }, [itemHeights, getItemHeight, estimatedItemHeight])

  // Find visible range using binary search
  const visibleRange = useMemo(() => {
    if (cumulativeHeights.length <= 1) return { start: 0, end: 0 }

    // Binary search for start
    let start = 0
    let end = cumulativeHeights.length - 1
    while (start < end) {
      const mid = Math.floor((start + end) / 2)
      if (cumulativeHeights[mid] < scrollTop) {
        start = mid + 1
      } else {
        end = mid
      }
    }
    const visibleStart = Math.max(0, start - 1)

    // Binary search for end
    const scrollBottom = scrollTop + containerHeight
    start = visibleStart
    end = cumulativeHeights.length - 1
    while (start < end) {
      const mid = Math.floor((start + end + 1) / 2)
      if (cumulativeHeights[mid] <= scrollBottom) {
        start = mid
      } else {
        end = mid - 1
      }
    }
    const visibleEnd = Math.min(items.length - 1, start)

    return {
      start: Math.max(0, visibleStart - overscan),
      end: Math.min(items.length - 1, visibleEnd + overscan),
    }
  }, [scrollTop, containerHeight, cumulativeHeights, items.length, overscan])

  // Get visible items
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end + 1)
  }, [items, visibleRange])

  // Handle scroll events
  const handleScroll = useCallback((e: Event) => {
    const target = e.target as HTMLDivElement
    const newScrollTop = target.scrollTop
    setScrollTop(newScrollTop)
    onScroll?.(newScrollTop)
  }, [onScroll])

  // Set up scroll listener
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll)
    }
  }, [handleScroll])

  // Measure actual item heights after render
  useEffect(() => {
    const newHeights = [...itemHeights]
    let hasChanges = false

    visibleItems.forEach((_, index) => {
      const actualIndex = visibleRange.start + index
      const ref = itemRefs.current[actualIndex]
      if (ref) {
        const actualHeight = ref.getBoundingClientRect().height
        if (Math.abs(actualHeight - newHeights[actualIndex]) > 1) {
          newHeights[actualIndex] = actualHeight
          hasChanges = true
        }
      }
    })

    if (hasChanges) {
      setItemHeights(newHeights)
    }
  }, [visibleItems, visibleRange, itemHeights])

  const totalHeight = cumulativeHeights[cumulativeHeights.length - 1] || 0

  return (
    <Box
      ref={scrollContainerRef}
      sx={{
        height: containerHeight,
        overflow: 'auto',
        position: 'relative',
      }}
      className={className}
    >
      <Box sx={{ height: totalHeight, position: 'relative' }}>
        <Box
          sx={{
            position: 'absolute',
            top: cumulativeHeights[visibleRange.start] || 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) => {
            const actualIndex = visibleRange.start + index
            return (
              <Box
                key={actualIndex}
                ref={(el: HTMLDivElement | null) => {
                  itemRefs.current[actualIndex] = el
                }}
                sx={{
                  overflow: 'hidden',
                }}
              >
                {renderItem(item, actualIndex)}
              </Box>
            )
          })}
        </Box>
      </Box>
    </Box>
  )
}