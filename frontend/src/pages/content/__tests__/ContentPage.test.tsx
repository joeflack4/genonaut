import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, vi } from 'vitest'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { ContentPage } from '../ContentPage'

vi.mock('../../../hooks', () => {
  const useContentList = vi.fn()

  return {
    useContentList,
  }
})

const { useContentList } = await import('../../../hooks')
const mockedUseContentList = vi.mocked(useContentList)

const renderContentPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>{children}</ThemeModeProvider>
    </QueryClientProvider>
  )

  return render(<ContentPage />, { wrapper })
}

describe('ContentPage', () => {
  beforeEach(() => {
    mockedUseContentList.mockReset()
    mockedUseContentList.mockReturnValue({
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
          },
        ],
        total: 1,
        limit: 10,
        skip: 0,
      },
      isLoading: false,
    })
  })

  it('renders content list and triggers search filter', () => {
    renderContentPage()

    expect(mockedUseContentList).toHaveBeenCalledWith({ limit: 10, skip: 0, search: '', sort: 'recent' })
    expect(screen.getByText('Neon Cityscape')).toBeInTheDocument()

    const searchInput = screen.getByLabelText(/search content/i)
    const filterForm = screen.getByRole('form', { name: /content filters/i })

    fireEvent.change(searchInput, { target: { value: 'portrait' } })
    fireEvent.submit(filterForm)

    const calls = mockedUseContentList.mock.calls
    const lastCallArgs = calls[calls.length - 1][0]
    expect(lastCallArgs).toMatchObject({ search: 'portrait' })
  })
})
