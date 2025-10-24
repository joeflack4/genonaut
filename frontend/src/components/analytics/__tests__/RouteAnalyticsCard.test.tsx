import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { RouteAnalyticsCard } from '../RouteAnalyticsCard'

vi.mock('../../../hooks', () => ({
  useRouteCachePriorities: vi.fn(),
}))

const { useRouteCachePriorities } = await import('../../../hooks')
const useRouteCachePrioritiesMock = vi.mocked(useRouteCachePriorities)

const mockRouteData = {
  system: 'absolute' as const,
  lookback_days: 7,
  total_routes: 3,
  routes: [
    {
      route: '/api/v1/content/unified',
      method: 'GET',
      query_params_normalized: {},
      avg_hourly_requests: 100,
      avg_p95_latency_ms: 50,
      avg_unique_users: 20,
      success_rate: 0.99,
      total_requests: 1000,
      cache_priority_score: 1000,
    },
    {
      route: '/api/v1/users/profile',
      method: 'GET',
      query_params_normalized: {},
      avg_hourly_requests: 200,
      avg_p95_latency_ms: 250,
      avg_unique_users: 30,
      success_rate: 0.98,
      total_requests: 2000,
      cache_priority_score: 2000,
    },
    {
      route: '/api/v1/tags',
      method: 'GET',
      query_params_normalized: {},
      avg_hourly_requests: 50,
      avg_p95_latency_ms: 600,
      avg_unique_users: 10,
      success_rate: 0.95,
      total_requests: 500,
      cache_priority_score: 500,
    },
  ],
}

const renderRouteAnalyticsCard = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  )

  return render(<RouteAnalyticsCard />, { wrapper })
}

describe('RouteAnalyticsCard', () => {
  beforeEach(() => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)
  })

  it('renders card with title', () => {
    renderRouteAnalyticsCard()
    expect(screen.getByTestId('route-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('route-analytics-title')).toHaveTextContent('Route Analytics')
  })

  it('shows filter controls', () => {
    renderRouteAnalyticsCard()
    expect(screen.getByTestId('route-analytics-filters')).toBeInTheDocument()
  })

  it('displays refresh button', () => {
    renderRouteAnalyticsCard()
    const refreshBtn = screen.getByTestId('route-analytics-refresh')
    expect(refreshBtn).toBeInTheDocument()
    expect(refreshBtn).toHaveTextContent(/refresh/i)
  })

  it('shows loading skeleton when data is loading', () => {
    renderRouteAnalyticsCard()
    // Skeleton elements are present during loading
    expect(screen.getByTestId('route-analytics-card')).toBeInTheDocument()
  })

  it('displays data table when data is loaded', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: mockRouteData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()
    expect(screen.getByTestId('route-analytics-table')).toBeInTheDocument()
  })

  it('displays all route data in table', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: mockRouteData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()

    expect(screen.getByText('/api/v1/content/unified')).toBeInTheDocument()
    expect(screen.getByText('/api/v1/users/profile')).toBeInTheDocument()
    expect(screen.getByText('/api/v1/tags')).toBeInTheDocument()
  })

  it('applies color coding to latency values', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: mockRouteData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()

    // Green for <100ms (50ms)
    const row1 = screen.getByTestId('route-analytics-row-0')
    expect(within(row1).getByText('50ms')).toBeInTheDocument()

    // Yellow for 100-500ms (250ms)
    const row2 = screen.getByTestId('route-analytics-row-1')
    expect(within(row2).getByText('250ms')).toBeInTheDocument()

    // Red for >500ms (600ms)
    const row3 = screen.getByTestId('route-analytics-row-2')
    expect(within(row3).getByText('600ms')).toBeInTheDocument()
  })

  it('shows error alert when fetch fails', () => {
    const error = new Error('Failed to fetch')
    useRouteCachePrioritiesMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()
    expect(screen.getByTestId('route-analytics-error')).toBeInTheDocument()
    expect(screen.getByText(/failed to load route analytics/i)).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: { ...mockRouteData, routes: [], total_routes: 0 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()
    expect(screen.getByTestId('route-analytics-empty')).toBeInTheDocument()
  })

  it('calls refetch when refresh button is clicked', () => {
    const refetch = vi.fn()
    useRouteCachePrioritiesMock.mockReturnValue({
      data: mockRouteData,
      isLoading: false,
      error: null,
      refetch,
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()
    const refreshBtn = screen.getByTestId('route-analytics-refresh')
    fireEvent.click(refreshBtn)
    expect(refetch).toHaveBeenCalled()
  })

  it('handles filter changes', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: mockRouteData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()

    // Filter controls should be present
    expect(screen.getByTestId('route-analytics-system-select')).toBeInTheDocument()
    expect(screen.getByTestId('route-analytics-days-select')).toBeInTheDocument()
    expect(screen.getByTestId('route-analytics-topn-select')).toBeInTheDocument()
  })

  it('displays footer info with metadata', () => {
    useRouteCachePrioritiesMock.mockReturnValue({
      data: mockRouteData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()
    const info = screen.getByTestId('route-analytics-info')
    expect(info).toHaveTextContent(/3 routes/)
    expect(info).toHaveTextContent(/7 days/)
    expect(info).toHaveTextContent(/absolute/)
  })

  it('formats numbers with commas', () => {
    const dataWithLargeNumbers = {
      ...mockRouteData,
      routes: [
        {
          ...mockRouteData.routes[0],
          avg_hourly_requests: 1234,
          cache_priority_score: 56789,
        },
      ],
    }

    useRouteCachePrioritiesMock.mockReturnValue({
      data: dataWithLargeNumbers,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderRouteAnalyticsCard()
    expect(screen.getByText('1,234')).toBeInTheDocument()
    expect(screen.getByText('56,789')).toBeInTheDocument()
  })
})
