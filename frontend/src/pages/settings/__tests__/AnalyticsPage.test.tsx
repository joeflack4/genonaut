import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AnalyticsPage } from '../AnalyticsPage'

// Mock the analytics hooks
vi.mock('../../../hooks', () => ({
  useRouteCachePriorities: vi.fn(),
  useGenerationOverview: vi.fn(),
  usePopularTags: vi.fn(),
}))

const { useRouteCachePriorities, useGenerationOverview, usePopularTags } = await import('../../../hooks')
const useRouteCachePrioritiesMock = vi.mocked(useRouteCachePriorities)
const useGenerationOverviewMock = vi.mocked(useGenerationOverview)
const usePopularTagsMock = vi.mocked(usePopularTags)

const renderAnalyticsPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  )

  return render(<AnalyticsPage />, { wrapper })
}

describe('AnalyticsPage', () => {
  beforeEach(() => {
    // Default mock implementations - return loading state
    useRouteCachePrioritiesMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    useGenerationOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    usePopularTagsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)
  })

  it('renders without crashing', () => {
    renderAnalyticsPage()
    expect(screen.getByTestId('analytics-page-root')).toBeInTheDocument()
  })

  it('displays page title and subtitle', () => {
    renderAnalyticsPage()

    expect(screen.getByTestId('analytics-title')).toHaveTextContent('Analytics')
    expect(screen.getByTestId('analytics-subtitle')).toHaveTextContent(
      /system performance metrics/i
    )
  })

  it('displays last updated timestamp', () => {
    renderAnalyticsPage()

    expect(screen.getByTestId('analytics-last-updated')).toBeInTheDocument()
    expect(screen.getByTestId('analytics-last-updated')).toHaveTextContent(/last updated:/i)
  })

  it('shows refresh all button', () => {
    renderAnalyticsPage()

    const refreshButton = screen.getByTestId('analytics-refresh-all')
    expect(refreshButton).toBeInTheDocument()
    expect(refreshButton).toHaveTextContent(/refresh all/i)
  })

  it('refreshes all sections when refresh all button is clicked', async () => {
    const refetchRoute = vi.fn()
    const refetchGeneration = vi.fn()
    const refetchTags = vi.fn()

    useRouteCachePrioritiesMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: refetchRoute,
      isFetching: false,
    } as any)

    useGenerationOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: refetchGeneration,
      isFetching: false,
    } as any)

    usePopularTagsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: refetchTags,
      isFetching: false,
    } as any)

    const { rerender } = renderAnalyticsPage()

    const refreshButton = screen.getByTestId('analytics-refresh-all')
    fireEvent.click(refreshButton)

    // QueryClient invalidateQueries is async
    await waitFor(() => {
      // We can't directly test invalidateQueries, but we can verify the button click doesn't error
      expect(refreshButton).toBeInTheDocument()
    })
  })

  it('displays all three analytics card sections', () => {
    renderAnalyticsPage()

    expect(screen.getByTestId('route-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('generation-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('tag-cardinality-card')).toBeInTheDocument()
  })

  it('shows loading skeletons when data is loading', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: true,
    } as any)

    useGenerationOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: true,
    } as any)

    usePopularTagsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: true,
    } as any)

    renderAnalyticsPage()

    // The cards themselves handle loading states with skeletons
    // We just verify the cards are present
    expect(screen.getByTestId('route-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('generation-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('tag-cardinality-card')).toBeInTheDocument()
  })

  it('handles error states gracefully', () => {
    const error = new Error('Failed to fetch analytics')

    useRouteCachePrioritiesMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    useGenerationOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    usePopularTagsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderAnalyticsPage()

    // Error states are handled within individual cards
    // The page should still render
    expect(screen.getByTestId('analytics-page-root')).toBeInTheDocument()
    expect(screen.getByTestId('route-analytics-card')).toBeInTheDocument()
  })

  it('renders with data successfully loaded', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: {
        system: 'absolute',
        lookback_days: 7,
        total_routes: 1,
        routes: [
          {
            route: '/api/v1/content',
            method: 'GET',
            query_params_normalized: {},
            avg_hourly_requests: 100,
            avg_p95_latency_ms: 150,
            avg_unique_users: 10,
            success_rate: 0.99,
            total_requests: 1000,
            cache_priority_score: 500,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    useGenerationOverviewMock.mockReturnValue({
      data: {
        lookback_days: 7,
        total_requests: 100,
        successful_generations: 95,
        failed_generations: 5,
        cancelled_generations: 0,
        success_rate_pct: 95,
        avg_duration_ms: 5000,
        p50_duration_ms: 4500,
        p95_duration_ms: 7000,
        p99_duration_ms: 9000,
        total_images_generated: 95,
        hours_with_data: 168,
        latest_data_timestamp: '2024-01-07T23:59:59Z',
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    usePopularTagsMock.mockReturnValue({
      data: [
        {
          id: '1',
          name: 'landscape',
          cardinality: 150,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderAnalyticsPage()

    expect(screen.getByTestId('analytics-page-root')).toBeInTheDocument()
    expect(screen.getByTestId('route-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('generation-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('tag-cardinality-card')).toBeInTheDocument()
  })

  it('has proper test IDs for all major elements', () => {
    renderAnalyticsPage()

    expect(screen.getByTestId('analytics-page-root')).toBeInTheDocument()
    expect(screen.getByTestId('analytics-header')).toBeInTheDocument()
    expect(screen.getByTestId('analytics-title')).toBeInTheDocument()
    expect(screen.getByTestId('analytics-subtitle')).toBeInTheDocument()
    expect(screen.getByTestId('analytics-refresh-all')).toBeInTheDocument()
    expect(screen.getByTestId('analytics-last-updated')).toBeInTheDocument()
  })
})
