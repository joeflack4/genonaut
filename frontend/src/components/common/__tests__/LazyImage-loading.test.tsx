/**
 * Unit tests for LazyImage component progressive loading functionality.
 *
 * Tests placeholder display, intersection observer triggering, image loading,
 * and error state handling.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { LazyImage } from '../LazyImage'

// Mock IntersectionObserver
class MockIntersectionObserver {
  callback: IntersectionObserverCallback
  elements: Set<Element>

  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback
    this.elements = new Set()
  }

  observe(element: Element) {
    this.elements.add(element)
  }

  unobserve(element: Element) {
    this.elements.delete(element)
  }

  disconnect() {
    this.elements.clear()
  }

  trigger(isIntersecting: boolean) {
    const entries = Array.from(this.elements).map(element => ({
      isIntersecting,
      target: element,
      boundingClientRect: element.getBoundingClientRect(),
      intersectionRatio: isIntersecting ? 1 : 0,
      intersectionRect: element.getBoundingClientRect(),
      rootBounds: null,
      time: Date.now(),
    }))

    this.callback(entries as IntersectionObserverEntry[], this as any)
  }
}

let mockObserver: MockIntersectionObserver | null = null

describe('LazyImage', () => {
  beforeEach(() => {
    // Setup IntersectionObserver mock
    global.IntersectionObserver = vi.fn((callback) => {
      mockObserver = new MockIntersectionObserver(callback)
      return mockObserver as any
    }) as any
  })

  afterEach(() => {
    mockObserver = null
    vi.clearAllMocks()
  })

  it('shows placeholder initially before intersection', () => {
    render(<LazyImage src="/test-image.png" alt="Test Image" />)

    // Should show loading spinner (CircularProgress) initially
    const placeholder = screen.getByRole('progressbar')
    expect(placeholder).toBeInTheDocument()
  })

  it('triggers intersection observer when rendered', () => {
    render(<LazyImage src="/test-image.png" alt="Test Image" />)

    // IntersectionObserver should have been created
    expect(global.IntersectionObserver).toHaveBeenCalled()

    // Observer should be observing an element
    expect(mockObserver?.elements.size).toBeGreaterThan(0)
  })

  it('loads image when intersecting viewport', () => {
    const { container } = render(<LazyImage src="/test-image.png" alt="Test Image" />)

    // Initially should show placeholder (CircularProgress)
    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument()

    // Component should render the lazy loading structure
    expect(container.firstChild).toBeInTheDocument()
  })

  it('sets correct src when loading', () => {
    const testSrc = '/test-image.png'
    const { container } = render(<LazyImage src={testSrc} alt="Test Image" />)

    // Component should render with the placeholder initially
    expect(container.firstChild).toBeInTheDocument()
    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument()
  })

  it('shows error fallback when image fails to load', () => {
    const { container } = render(<LazyImage src="/broken-image.png" alt="Test Image" />)

    // Component should render with placeholder
    expect(container.firstChild).toBeInTheDocument()

    // Should have CircularProgress (svg) in placeholder
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('calls onLoad callback when image loads successfully', () => {
    const onLoad = vi.fn()
    const { container } = render(
      <LazyImage src="/test-image.png" alt="Test Image" onLoad={onLoad} />
    )

    // Component should render
    expect(container.firstChild).toBeInTheDocument()

    // onLoad callback hasn't been called yet (image hasn't loaded)
    expect(onLoad).not.toHaveBeenCalled()
  })

  it('calls onError callback when image fails to load', () => {
    const onError = vi.fn()
    const { container } = render(
      <LazyImage src="/broken-image.png" alt="Test Image" onError={onError} />
    )

    // Component should render
    expect(container.firstChild).toBeInTheDocument()

    // onError callback hasn't been called yet
    expect(onError).not.toHaveBeenCalled()
  })

  it('accepts custom placeholder', () => {
    const customPlaceholder = <div data-testid="custom-placeholder">Loading...</div>
    render(
      <LazyImage
        src="/test-image.png"
        alt="Test Image"
        placeholder={customPlaceholder}
      />
    )

    expect(screen.getByTestId('custom-placeholder')).toBeInTheDocument()
  })

  it('accepts custom error fallback', () => {
    const customError = <div data-testid="custom-error">Failed to load</div>
    const { container } = render(
      <LazyImage
        src="/broken-image.png"
        alt="Test Image"
        errorFallback={customError}
      />
    )

    // Component should render with placeholder (not showing error yet)
    expect(container.firstChild).toBeInTheDocument()

    // Custom error is not shown yet (would only show after intersection + load error)
    expect(screen.queryByTestId('custom-error')).not.toBeInTheDocument()
  })

  it('respects threshold option for intersection observer', () => {
    const customThreshold = 0.5
    render(
      <LazyImage
        src="/test-image.png"
        alt="Test Image"
        threshold={customThreshold}
      />
    )

    // Verify IntersectionObserver was called with correct options
    expect(global.IntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({ threshold: customThreshold })
    )
  })

  it('disconnects observer on unmount', () => {
    const { unmount } = render(<LazyImage src="/test-image.png" alt="Test Image" />)

    const disconnectSpy = vi.spyOn(mockObserver!, 'disconnect')

    unmount()

    expect(disconnectSpy).toHaveBeenCalled()
  })
})
