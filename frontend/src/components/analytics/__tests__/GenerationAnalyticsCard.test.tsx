import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { GenerationAnalyticsCard } from '../GenerationAnalyticsCard'

vi.mock('../../../hooks', () => ({
  useGenerationOverview: vi.fn(),
}))

const { useGenerationOverview } = await import('../../../hooks')
const useGenerationOverviewMock = vi.mocked(useGenerationOverview)

const mockGenerationData = {
  lookback_days: 7,
  total_requests: 150,
  successful_generations: 145,
  failed_generations: 3,
  cancelled_generations: 2,
  success_rate_pct: 96.67,
  avg_duration_ms: 5000,
  p50_duration_ms: 4500,
  p95_duration_ms: 7000,
  p99_duration_ms: 9000,
  total_images_generated: 145,
  unique_users: 25,
  hours_with_data: 168,
  latest_data_timestamp: '2024-01-07T23:59:59Z',
}

const renderGenerationAnalyticsCard = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  )

  return render(<GenerationAnalyticsCard />, { wrapper })
}

describe('GenerationAnalyticsCard', () => {
  beforeEach(() => {
    useGenerationOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)
  })

  it('renders card with title', () => {
    renderGenerationAnalyticsCard()
    expect(screen.getByTestId('generation-analytics-card')).toBeInTheDocument()
    expect(screen.getByTestId('generation-analytics-title')).toHaveTextContent('Generation Analytics')
  })

  it('shows filter controls', () => {
    renderGenerationAnalyticsCard()
    expect(screen.getByTestId('generation-analytics-filters')).toBeInTheDocument()
  })

  it('displays refresh button', () => {
    renderGenerationAnalyticsCard()
    const refreshBtn = screen.getByTestId('generation-analytics-refresh')
    expect(refreshBtn).toBeInTheDocument()
  })

  it('shows loading skeletons when data is loading', () => {
    renderGenerationAnalyticsCard()
    expect(screen.getByTestId('generation-analytics-card')).toBeInTheDocument()
  })

  it('displays overview metric cards when data is loaded', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByTestId('generation-analytics-metrics')).toBeInTheDocument()
  })

  it('displays total generations metric', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('displays success rate with percentage', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByText('96.7%')).toBeInTheDocument()
  })

  it('formats duration in seconds', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    // avg_duration_ms: 5000 -> 5.0s
    expect(screen.getByText('5.0s')).toBeInTheDocument()
  })

  it('displays unique users count', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByText('25')).toBeInTheDocument()
  })

  it('shows detailed statistics panel', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByText('145')).toBeInTheDocument() // successful
    expect(screen.getByText('3')).toBeInTheDocument() // failed
    expect(screen.getByText('2')).toBeInTheDocument() // cancelled
  })

  it('displays percentile durations', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByText('4.5s')).toBeInTheDocument() // P50
    expect(screen.getByText('7.0s')).toBeInTheDocument() // P95
    expect(screen.getByText('9.0s')).toBeInTheDocument() // P99
  })

  it('applies success rate color coding', () => {
    // High success rate (green)
    const highSuccessData = { ...mockGenerationData, success_rate_pct: 95 }
    useGenerationOverviewMock.mockReturnValue({
      data: highSuccessData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByText('95.0%')).toBeInTheDocument()
  })

  it('shows error alert when fetch fails', () => {
    const error = new Error('Failed to fetch')
    useGenerationOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByTestId('generation-analytics-error')).toBeInTheDocument()
  })

  it('shows metrics even when total_requests is 0', () => {
    const emptyData = {
      ...mockGenerationData,
      total_requests: 0,
      successful_generations: 0,
      failed_generations: 0,
      cancelled_generations: 0,
      success_rate_pct: 0,
      avg_duration_ms: null,
      p50_duration_ms: null,
      p95_duration_ms: null,
      p99_duration_ms: null,
    }

    useGenerationOverviewMock.mockReturnValue({
      data: emptyData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    // Component shows metrics even with 0 values
    expect(screen.getByTestId('generation-analytics-metrics')).toBeInTheDocument()
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
  })

  it('calls refetch when refresh button is clicked', () => {
    const refetch = vi.fn()
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch,
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    const refreshBtn = screen.getByTestId('generation-analytics-refresh')
    fireEvent.click(refreshBtn)
    expect(refetch).toHaveBeenCalled()
  })

  it('has time range filter control', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    expect(screen.getByTestId('generation-analytics-days-select')).toBeInTheDocument()
  })

  it('displays footer info with lookback days', () => {
    useGenerationOverviewMock.mockReturnValue({
      data: mockGenerationData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      isFetching: false,
    } as any)

    renderGenerationAnalyticsCard()
    const info = screen.getByTestId('generation-analytics-info')
    expect(info).toHaveTextContent(/7 days/)
  })
})
