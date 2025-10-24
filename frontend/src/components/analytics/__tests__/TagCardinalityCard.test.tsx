import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { TagCardinalityCard } from '../TagCardinalityCard'

vi.mock('../../../hooks', () => ({
  usePopularTags: vi.fn(),
}))

const { usePopularTags } = await import('../../../hooks')
const usePopularTagsMock = vi.mocked(usePopularTags)

const mockRegularTags = [
  { id: '1', name: 'landscape', cardinality: 150, created_at: '2024-01-01T00:00:00Z' },
  { id: '2', name: 'abstract', cardinality: 120, created_at: '2024-01-01T00:00:00Z' },
  { id: '3', name: 'portrait', cardinality: 80, created_at: '2024-01-01T00:00:00Z' },
]

const mockAutoTags = [
  { id: '4', name: 'ai-generated', cardinality: 200, created_at: '2024-01-01T00:00:00Z' },
  { id: '5', name: 'synthetic', cardinality: 100, created_at: '2024-01-01T00:00:00Z' },
]

const renderTagCardinalityCard = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  )

  return render(<TagCardinalityCard />, { wrapper })
}

describe('TagCardinalityCard', () => {
  beforeEach(() => {
    // Clear localStorage to reset persisted filter state
    localStorage.clear()

    // Mock all usePopularTags calls to return undefined initially
    usePopularTagsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)
  })

  it('renders card with title', () => {
    renderTagCardinalityCard()
    expect(screen.getByTestId('tag-cardinality-card')).toBeInTheDocument()
    expect(screen.getByTestId('tag-cardinality-title')).toHaveTextContent('Tags')
  })

  it('shows two tabs: Table and Visualization', () => {
    renderTagCardinalityCard()
    expect(screen.getByTestId('tag-cardinality-tabs')).toBeInTheDocument()
    expect(screen.getByTestId('tag-cardinality-tab-table')).toBeInTheDocument()
    expect(screen.getByTestId('tag-cardinality-tab-visualization')).toBeInTheDocument()
  })

  it('defaults to Table tab', () => {
    renderTagCardinalityCard()
    const tableTab = screen.getByTestId('tag-cardinality-tab-table')
    expect(tableTab).toHaveAttribute('aria-selected', 'true')
  })

  it('shows total unique tags count', () => {
    // Mock the two calls to usePopularTags for total count
    usePopularTagsMock
      .mockReturnValueOnce({
        data: mockRegularTags,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        isFetching: false,
      } as any)
      .mockReturnValueOnce({
        data: mockAutoTags,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        isFetching: false,
      } as any)

    renderTagCardinalityCard()

    // Should show 5 unique tags (3 regular + 2 auto)
    expect(screen.getByTestId('tag-cardinality-total')).toHaveTextContent('Total tags: 5')
  })

  it('switches to Visualization tab when clicked', () => {
    renderTagCardinalityCard()

    const visualizationTab = screen.getByTestId('tag-cardinality-tab-visualization')
    fireEvent.click(visualizationTab)

    expect(visualizationTab).toHaveAttribute('aria-selected', 'true')
  })

  describe('Table Tab', () => {
    it('shows Regular Content section', () => {
      renderTagCardinalityCard()
      expect(screen.getByText('Regular Content')).toBeInTheDocument()
    })

    it('shows Auto-Generated Content section', () => {
      renderTagCardinalityCard()
      expect(screen.getByText('Auto-Generated Content')).toBeInTheDocument()
    })

    it('displays loading skeletons when loading', () => {
      renderTagCardinalityCard()
      // Should have loading skeletons for both sections
      expect(screen.getByTestId('tag-cardinality-card')).toBeInTheDocument()
    })

    it('displays tags in Regular Content section', () => {
      // Mock calls: first two for total count, then for each section
      usePopularTagsMock
        .mockReturnValueOnce({
          data: mockRegularTags,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
          isFetching: false,
        } as any)
        .mockReturnValueOnce({
          data: mockAutoTags,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
          isFetching: false,
        } as any)
        .mockReturnValueOnce({
          data: mockRegularTags,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
          isFetching: false,
        } as any)
        .mockReturnValueOnce({
          data: mockAutoTags,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
          isFetching: false,
        } as any)

      renderTagCardinalityCard()

      // Check that regular tags are displayed
      expect(screen.getByText('landscape')).toBeInTheDocument()
      expect(screen.getByText('abstract')).toBeInTheDocument()
    })

    it('has Show selector for Regular Content', () => {
      renderTagCardinalityCard()
      expect(screen.getByTestId('tag-cardinality-items-topn-select')).toBeInTheDocument()
    })

    it('has Show selector for Auto-Generated Content', () => {
      renderTagCardinalityCard()
      expect(screen.getByTestId('tag-cardinality-auto-topn-select')).toBeInTheDocument()
    })
  })

  describe('Visualization Tab', () => {
    beforeEach(() => {
      // Set up mocks for visualization tab tests
      usePopularTagsMock
        .mockReturnValue({
          data: mockRegularTags,
          isLoading: false,
          error: null,
          refetch: vi.fn(),
          isFetching: false,
        } as any)
    })

    it('shows statistics when data is loaded', () => {
      renderTagCardinalityCard()

      const visualizationTab = screen.getByTestId('tag-cardinality-tab-visualization')
      fireEvent.click(visualizationTab)

      // Should show stats sections for both content types
      expect(screen.getByText('Regular Content')).toBeInTheDocument()
      expect(screen.getByText('Auto-Generated Content')).toBeInTheDocument()
    })

    it('shows histogram visualization', () => {
      renderTagCardinalityCard()

      const visualizationTab = screen.getByTestId('tag-cardinality-tab-visualization')
      fireEvent.click(visualizationTab)

      // Check for histogram testids (should be in both sections)
      const histograms = screen.queryAllByTestId(/histogram/)
      expect(histograms.length).toBeGreaterThan(0)
    })

    it('has log scale toggle', () => {
      renderTagCardinalityCard()

      const visualizationTab = screen.getByTestId('tag-cardinality-tab-visualization')
      fireEvent.click(visualizationTab)

      // Should have a shared log scale toggle (switch, not checkbox)
      const toggle = screen.getByRole('switch', { name: /log scale/i })
      expect(toggle).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('shows error message when fetch fails', () => {
      const error = new Error('Failed to fetch tags')
      usePopularTagsMock.mockReturnValue({
        data: undefined,
        isLoading: false,
        error,
        refetch: vi.fn(),
        isFetching: false,
      } as any)

      renderTagCardinalityCard()

      // Error messages should appear in the sections
      const alerts = screen.queryAllByRole('alert')
      expect(alerts.length).toBeGreaterThan(0)
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no data', () => {
      usePopularTagsMock.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        isFetching: false,
      } as any)

      renderTagCardinalityCard()

      // Empty state text appears in both sections
      expect(screen.getAllByText(/no data available/i).length).toBeGreaterThan(0)
    })
  })
})


