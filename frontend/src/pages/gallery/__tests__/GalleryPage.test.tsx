import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { GalleryPage } from '../GalleryPage'

vi.mock('../../../hooks', () => {
  const useGalleryList = vi.fn()
  const useGalleryAutoList = vi.fn()
  const useCurrentUser = vi.fn()

  return {
    useGalleryList,
    useGalleryAutoList,
    useCurrentUser,
  }
})

const { useGalleryList, useGalleryAutoList, useCurrentUser } = await import('../../../hooks')
const mockedUseGalleryList = vi.mocked(useGalleryList)
const mockedUseGalleryAutoList = vi.mocked(useGalleryAutoList)
const mockedUseCurrentUser = vi.mocked(useCurrentUser)

const renderGalleryPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>{children}</ThemeModeProvider>
    </QueryClientProvider>
  )

  return render(<GalleryPage />, { wrapper })
}

describe('GalleryPage', () => {
  beforeEach(() => {
    mockedUseCurrentUser.mockReset()
    mockedUseGalleryList.mockReset()
    mockedUseGalleryAutoList.mockReset()

    mockedUseCurrentUser.mockReturnValue({
      data: { id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9', name: 'Admin' },
      isLoading: false,
    })

    mockedUseGalleryList.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            title: 'Neon Cityscape',
            description: 'Futuristic skyline',
            imageUrl: null,
            qualityScore: 0.87,
            createdAt: '2024-01-05T00:00:00Z',
            updatedAt: '2024-01-05T00:00:00Z',
            creatorId: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
          },
        ],
        total: 1,
        limit: 20,
        skip: 0,
      },
      isLoading: false,
    })

    mockedUseGalleryAutoList.mockReturnValue({
      data: {
        items: [],
        total: 0,
        limit: 20,
        skip: 0,
      },
      isLoading: false,
    })
  })

  it('renders gallery list and triggers search filter', () => {
    renderGalleryPage()

    // Gallery page calls multiple hooks with different parameters
    expect(mockedUseGalleryList).toHaveBeenCalledWith({
      limit: 20,
      skip: 0,
      search: '',
      sort: 'recent',
      creator_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9'
    })
    expect(mockedUseGalleryList).toHaveBeenCalledWith({
      limit: 20,
      skip: 0,
      search: '',
      sort: 'recent'
    })
    expect(screen.getByText('Neon Cityscape')).toBeInTheDocument()

    const searchInput = screen.getByLabelText(/search/i)
    const filterForm = screen.getByRole('form', { name: /gallery filters/i })

    fireEvent.change(searchInput, { target: { value: 'portrait' } })
    fireEvent.submit(filterForm)

    const calls = mockedUseGalleryList.mock.calls
    const lastCallArgs = calls[calls.length - 1][0]
    expect(lastCallArgs).toMatchObject({ search: 'portrait' })
  })

  it('toggles the options panel', async () => {
    const user = userEvent.setup()
    renderGalleryPage()

    await user.click(screen.getByLabelText(/close options/i))
    expect(screen.getByTestId('SettingsOutlinedIcon')).toBeInTheDocument()

    const optionButtons = screen.getAllByRole('button', { name: /options/i })
    await user.click(optionButtons[0])

    expect(screen.queryByTestId('SettingsOutlinedIcon')).not.toBeInTheDocument()
  })
})
