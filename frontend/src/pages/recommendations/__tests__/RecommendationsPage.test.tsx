import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { RecommendationsPage } from '../RecommendationsPage'

vi.mock('../../../hooks', () => {
  const useRecommendations = vi.fn()
  const useServeRecommendation = vi.fn()

  return {
    useRecommendations,
    useServeRecommendation,
    useCurrentUser: () => ({ data: { id: 1, name: 'Admin' }, isLoading: false }),
  }
})

const hooks = await import('../../../hooks')
const mockedUseRecommendations = vi.mocked(hooks.useRecommendations)
const mockedUseServeRecommendation = vi.mocked(hooks.useServeRecommendation)

const renderRecommendationsPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>{children}</ThemeModeProvider>
    </QueryClientProvider>
  )

  return render(<RecommendationsPage />, { wrapper })
}

describe('RecommendationsPage', () => {
  const mutateAsyncMock = vi.fn()

  beforeEach(() => {
    mockedUseRecommendations.mockReset()
    mockedUseServeRecommendation.mockReset()
    mutateAsyncMock.mockReset()

    mockedUseRecommendations.mockReturnValue({
      data: [
        {
          id: 7,
          userId: 1,
          contentId: 42,
          algorithm: 'collaborative',
          score: 0.82,
          servedAt: null,
          createdAt: '2024-01-10T00:00:00Z',
        },
      ],
      isLoading: false,
    })

    mockedUseServeRecommendation.mockReturnValue({ mutateAsync: mutateAsyncMock })
  })

  it('renders recommendations and marks as served', async () => {
    renderRecommendationsPage()

    expect(screen.getByText('collaborative')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /mark as served/i }))

    expect(mutateAsyncMock).toHaveBeenCalledWith(7)
  })
})
