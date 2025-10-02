import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { UiSettingsProvider } from '../../../app/providers/ui'
import { DashboardPage } from '../DashboardPage'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../../../hooks', () => {
  const useCurrentUser = vi.fn()
  const useGalleryStats = vi.fn()
  const useGalleryList = vi.fn()
  const useGalleryAutoList = vi.fn()

  return {
    useCurrentUser,
    useGalleryStats,
    useGalleryList,
    useGalleryAutoList,
  }
})

const hooks = await import('../../../hooks')
const mockedUseCurrentUser = vi.mocked(hooks.useCurrentUser)
const mockedUseGalleryStats = vi.mocked(hooks.useGalleryStats)
const mockedUseGalleryList = vi.mocked(hooks.useGalleryList)
const mockedUseGalleryAutoList = vi.mocked(hooks.useGalleryAutoList)

const renderDashboard = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <UiSettingsProvider>
        <ThemeModeProvider>
          <MemoryRouter>{children}</MemoryRouter>
        </ThemeModeProvider>
      </UiSettingsProvider>
    </QueryClientProvider>
  )

  return render(<DashboardPage />, { wrapper })
}

describe('DashboardPage', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
    mockedUseGalleryStats.mockReset()
    mockedUseGalleryList.mockReset()
    mockedUseGalleryAutoList.mockReset()

    mockedUseCurrentUser.mockReturnValue({
      data: { id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9', name: 'Admin' },
      isLoading: false,
    })

    mockedUseGalleryStats.mockReturnValue({
      data: {
        userGalleryCount: 1,
        userAutoGalleryCount: 2,
        totalGalleryCount: 3,
        totalAutoGalleryCount: 4,
      },
      isLoading: false,
    })

    const userGalleryResponse = {
      items: [
        {
          id: 1,
          title: 'User Content Item',
          description: null,
          imageUrl: null,
          pathThumb: null,
          contentData: null,
          contentType: 'image',
          qualityScore: 0.9,
          createdAt: '2024-01-10T00:00:00Z',
          updatedAt: '2024-01-10T00:00:00Z',
          creatorId: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
          tags: [],
          itemMetadata: null,
          sourceType: 'regular' as const,
        },
      ],
      total: 1,
      limit: 5,
      skip: 0,
    }

    const communityGalleryResponse = {
      items: [
        {
          id: 2,
          title: 'Surreal Landscape',
          description: null,
          imageUrl: null,
          pathThumb: null,
          contentData: null,
          contentType: 'image',
          qualityScore: 0.9,
          createdAt: '2024-01-10T00:00:00Z',
          updatedAt: '2024-01-10T00:00:00Z',
          creatorId: 'different-user-id',
          tags: [],
          itemMetadata: null,
          sourceType: 'regular' as const,
        },
      ],
      total: 3,
      limit: 20,
      skip: 0,
    }

    const userAutoResponse = {
      items: [
        {
          id: 3,
          title: 'User Auto-Gen Item',
          description: null,
          imageUrl: null,
          pathThumb: null,
          contentData: null,
          contentType: 'image',
          qualityScore: 0.8,
          createdAt: '2024-01-10T00:00:00Z',
          updatedAt: '2024-01-10T00:00:00Z',
          creatorId: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
          tags: [],
          itemMetadata: null,
          sourceType: 'auto' as const,
        },
      ],
      total: 1,
      limit: 5,
      skip: 0,
    }

    const communityAutoResponse = {
      items: [
        {
          id: 4,
          title: 'Community Auto-Gen Item',
          description: null,
          imageUrl: null,
          pathThumb: null,
          contentData: null,
          contentType: 'image',
          qualityScore: 0.85,
          createdAt: '2024-01-10T00:00:00Z',
          updatedAt: '2024-01-10T00:00:00Z',
          creatorId: 'different-user-id',
          tags: [],
          itemMetadata: null,
          sourceType: 'auto' as const,
        },
      ],
      total: 2,
      limit: 20,
      skip: 0,
    }

    mockedUseGalleryList.mockImplementation((params: any) => ({
      data: params?.creator_id ? userGalleryResponse : communityGalleryResponse,
      isLoading: false,
    }))

    mockedUseGalleryAutoList.mockImplementation((params: any) => ({
      data: params?.creator_id ? userAutoResponse : communityAutoResponse,
      isLoading: false,
    }))
  })

  it('displays gallery stats and recent content', () => {
    renderDashboard()

    expect(screen.getByTestId('dashboard-page-root')).toBeInTheDocument()
    expect(screen.getByTestId('dashboard-stat-grid')).toBeInTheDocument()
    expect(screen.getByTestId('dashboard-user-recent-list')).toBeInTheDocument()

    expect(mockedUseGalleryStats).toHaveBeenCalledWith('121e194b-4caa-4b81-ad4f-86ca3919d5b9')
    expect(mockedUseGalleryList).toHaveBeenCalledWith({ limit: 5, sort: 'recent', creator_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9' })
    expect(mockedUseGalleryAutoList).toHaveBeenCalledWith({ limit: 5, sort: 'recent', creator_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9' })
    expect(mockedUseGalleryList).toHaveBeenCalledWith({ limit: 20, sort: 'recent' })
    expect(mockedUseGalleryAutoList).toHaveBeenCalledWith({ limit: 20, sort: 'recent' })
    expect(screen.getByText('1')).toBeInTheDocument() // User gallery count
    expect(screen.getByText('2')).toBeInTheDocument() // User auto gallery count
    expect(screen.getByText('3')).toBeInTheDocument() // Total gallery count
    expect(screen.getByText('4')).toBeInTheDocument() // Total auto gallery count
    expect(screen.getByText('Your gens')).toBeInTheDocument()
    expect(screen.getByText('Your auto-gens')).toBeInTheDocument()
    expect(screen.getByText('Community gens')).toBeInTheDocument()
    expect(screen.getByText('Community auto-gens')).toBeInTheDocument()
    expect(screen.getByText('Your recent gens')).toBeInTheDocument()
    expect(screen.getByText('Your recent auto-gens')).toBeInTheDocument()
    expect(screen.getByText('Community recent gens')).toBeInTheDocument()
    expect(screen.getByText('Community recent auto-gens')).toBeInTheDocument()
    expect(screen.getByText('User Content Item')).toBeInTheDocument() // User's recent gallery item
    expect(screen.getByText('User Auto-Gen Item')).toBeInTheDocument() // User's recent auto-gen
    expect(screen.getByText('Surreal Landscape')).toBeInTheDocument() // Community recent content
    expect(screen.getByText('Community Auto-Gen Item')).toBeInTheDocument() // Community recent auto-gen
  })

  it('switches to grid view when toggled', async () => {
    const user = userEvent.setup()
    renderDashboard()

    await user.click(screen.getByTestId('dashboard-view-toggle-grid'))

    expect(screen.getByTestId('dashboard-user-recent-grid')).toBeInTheDocument()
    expect(screen.getByTestId('dashboard-community-recent-grid')).toBeInTheDocument()
  })
})
