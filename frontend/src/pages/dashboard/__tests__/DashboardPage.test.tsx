import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { UiSettingsProvider } from '../../../app/providers/ui'
import { DashboardPage } from '../DashboardPage'

vi.mock('../../../hooks', () => {
  const useCurrentUser = vi.fn()
  const useContentStats = vi.fn()
  const useContentList = vi.fn()

  return {
    useCurrentUser,
    useContentStats,
    useContentList,
  }
})

const hooks = await import('../../../hooks')
const mockedUseCurrentUser = vi.mocked(hooks.useCurrentUser)
const mockedUseContentStats = vi.mocked(hooks.useContentStats)
const mockedUseContentList = vi.mocked(hooks.useContentList)

const renderDashboard = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>{children}</ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )

  return render(<DashboardPage />, { wrapper })
}

describe('DashboardPage', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
    mockedUseContentStats.mockReset()
    mockedUseContentList.mockReset()

    mockedUseCurrentUser.mockReturnValue({
      data: { id: 1, name: 'Admin' },
      isLoading: false,
    })

    mockedUseContentStats.mockReturnValue({
      data: {
        userContentCount: 1,
        totalContentCount: 3,
      },
      isLoading: false,
    })

    mockedUseContentList
      .mockReturnValueOnce({
        data: {
          items: [
            {
              id: 1,
              title: 'User Content Item',
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
      .mockReturnValueOnce({
        data: {
          items: [
            {
              id: 2,
              title: 'Surreal Landscape',
              description: null,
              imageUrl: null,
              qualityScore: 0.9,
              createdAt: '2024-01-10T00:00:00Z',
              updatedAt: '2024-01-10T00:00:00Z',
            },
          ],
          total: 3,
          limit: 5,
          skip: 0,
        },
        isLoading: false,
      })
  })

  it('displays content stats and recent content', () => {
    renderDashboard()

    expect(mockedUseContentStats).toHaveBeenCalledWith(1)
    expect(mockedUseContentList).toHaveBeenCalledWith({ limit: 5, sort: 'recent', creator_id: 1 })
    expect(mockedUseContentList).toHaveBeenCalledWith({ limit: 5, sort: 'recent' })
    expect(screen.getByText('1')).toBeInTheDocument() // User content count
    expect(screen.getByText('3')).toBeInTheDocument() // Total content count
    expect(screen.getByText('Your works')).toBeInTheDocument()
    expect(screen.getByText('Community works')).toBeInTheDocument()
    expect(screen.getByText('Your recent works')).toBeInTheDocument()
    expect(screen.getByText('Community recent works')).toBeInTheDocument()
    expect(screen.getByText('User Content Item')).toBeInTheDocument() // User's recent content
    expect(screen.getByText('Surreal Landscape')).toBeInTheDocument() // Community recent content
  })
})
