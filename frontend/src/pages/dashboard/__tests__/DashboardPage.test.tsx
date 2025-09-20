import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { DashboardPage } from '../DashboardPage'

vi.mock('../../../hooks', () => {
  const useCurrentUser = vi.fn()
  const useUserStats = vi.fn()
  const useContentList = vi.fn()

  return {
    useCurrentUser,
    useUserStats,
    useContentList,
  }
})

const hooks = await import('../../../hooks')
const mockedUseCurrentUser = vi.mocked(hooks.useCurrentUser)
const mockedUseUserStats = vi.mocked(hooks.useUserStats)
const mockedUseContentList = vi.mocked(hooks.useContentList)

const renderDashboard = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>{children}</ThemeModeProvider>
    </QueryClientProvider>
  )

  return render(<DashboardPage />, { wrapper })
}

describe('DashboardPage', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
    mockedUseUserStats.mockReset()
    mockedUseContentList.mockReset()

    mockedUseCurrentUser.mockReturnValue({
      data: { id: 1, name: 'Admin' },
      isLoading: false,
    })

    mockedUseUserStats.mockReturnValue({
      data: {
        totalRecommendations: 12,
        servedRecommendations: 5,
        generatedContent: 7,
        lastActiveAt: '2024-01-12T10:00:00Z',
      },
      isLoading: false,
    })

    mockedUseContentList.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            title: 'Surreal Landscape',
            description: null,
            imageUrl: null,
            qualityScore: 0.9,
            createdAt: '2024-01-10T00:00:00Z',
            updatedAt: '2024-01-10T00:00:00Z',
          },
        ],
        total: 1,
        limit: 5,
        skip: 0,
      },
      isLoading: false,
    })
  })

  it('displays user stats and recent content', () => {
    renderDashboard()

    expect(mockedUseContentList).toHaveBeenCalledWith({ limit: 5, sort: 'recent' })
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('Total Recommendations')).toBeInTheDocument()
    expect(screen.getByText('Surreal Landscape')).toBeInTheDocument()
  })
})
