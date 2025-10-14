import React, { type ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ThemeModeProvider } from '../../../app/providers/theme'
import { GalleryPage } from '../GalleryPage'

// Mock config constants
vi.mock('../../../constants/config', () => ({
  ADMIN_USER_ID: 'test-admin-id',
}))

vi.mock('../../../hooks', () => {
  const useUnifiedGallery = vi.fn()
  const useCurrentUser = vi.fn()
  const useTags = vi.fn()

  return {
    useUnifiedGallery,
    useCurrentUser,
    useTags,
  }
})

const { useUnifiedGallery, useCurrentUser, useTags } = await import('../../../hooks')
const mockedUseUnifiedGallery = vi.mocked(useUnifiedGallery)
const mockedUseCurrentUser = vi.mocked(useCurrentUser)
const mockedUseTags = vi.mocked(useTags)

const renderGalleryPage = (initialEntries: string[] = ['/gallery']) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <ThemeModeProvider>
          <Routes>
            <Route path="/gallery" element={children} />
          </Routes>
        </ThemeModeProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )

  return render(<GalleryPage />, { wrapper })
}

describe('GalleryPage', () => {
  beforeEach(() => {
    localStorage.clear()
    mockedUseCurrentUser.mockReset()
    mockedUseUnifiedGallery.mockReset()
    mockedUseTags.mockReset()

    mockedUseCurrentUser.mockReturnValue({
      data: { id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9', name: 'Admin' },
      isLoading: false,
    })

    mockedUseUnifiedGallery.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            title: 'Neon Cityscape',
            description: 'Futuristic skyline',
            imageUrl: null,
            pathThumb: null,
            pathThumbsAltRes: null,
            contentData: null,
            contentType: 'image',
            prompt: 'City skyline',
            qualityScore: 0.87,
            createdAt: '2024-01-05T00:00:00Z',
            updatedAt: '2024-01-05T00:00:00Z',
            creatorId: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            creatorUsername: 'Admin',
            tags: ['cyberpunk'],
            itemMetadata: { prompt: 'City skyline' },
            sourceType: 'regular',
          },
        ],
        total: 1,
        limit: 20,
        skip: 0,
        stats: {
          userRegularCount: 1,
          userAutoCount: 0,
          communityRegularCount: 0,
          communityAutoCount: 0,
        },
      },
      isLoading: false,
    })

    mockedUseTags.mockReturnValue({
      data: {
        items: [
          {
            id: 'tag-1',
            name: 'Landscape',
            metadata: {},
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            average_rating: 4.2,
            rating_count: 10,
          },
        ],
        pagination: {
          page: 1,
          page_size: 20,
          total_count: 1,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        },
      },
      isLoading: false,
    })
  })

  it('renders gallery list and tag filter', () => {
    renderGalleryPage()

    expect(screen.getByText('Neon Cityscape')).toBeInTheDocument()
    expect(screen.getByTestId('tag-filter')).toBeInTheDocument()

    const searchInput = screen.getByTestId('gallery-search-input')
    const filterForm = screen.getByRole('form', { name: /gallery filters/i })

    fireEvent.change(searchInput, { target: { value: 'portrait' } })
    fireEvent.submit(filterForm)
  })

  it('toggles the options panel', async () => {
    const user = userEvent.setup()
    renderGalleryPage()

    // Wait for the page to render first
    await waitFor(() => expect(screen.getByTestId('gallery-options-drawer')).toBeInTheDocument(), { timeout: 10000 })

    await user.click(screen.getByLabelText(/close options/i))
    await waitFor(() => expect(screen.getByTestId('gallery-options-drawer')).toHaveAttribute('data-open', 'false'), { timeout: 10000 })

    await user.click(screen.getByTestId('gallery-options-toggle-button'))
    await waitFor(() => expect(screen.getByTestId('gallery-options-drawer')).toHaveAttribute('data-open', 'true'), { timeout: 10000 })
  })

  it('syncs tags from query parameters', async () => {
    renderGalleryPage(['/gallery?tag=tag-1&tag=tag-2'])

    await waitFor(() => {
      expect(screen.getByTestId('tag-filter-selected-tag-1')).toBeInTheDocument()
      expect(screen.getByTestId('tag-filter-selected-tag-2')).toBeInTheDocument()
    })

    const lastCallParams = mockedUseUnifiedGallery.mock.calls.at(-1)?.[0]
    expect(lastCallParams?.tag).toEqual(['tag-1', 'tag-2'])
  })

  it('updates tag filters when selecting and removing tags', async () => {
    const user = userEvent.setup()
    renderGalleryPage()

    await user.click(screen.getByTestId('tag-filter-chip-tag-1'))

    await waitFor(() => expect(screen.getByTestId('tag-filter-selected-tag-1')).toBeInTheDocument())

    let lastCallParams = mockedUseUnifiedGallery.mock.calls.at(-1)?.[0]
    expect(lastCallParams?.tag).toEqual(['tag-1'])

    // Remove via chip delete button
    const deleteButton = screen.getByTestId('tag-filter-selected-tag-1-delete')
    fireEvent.click(deleteButton)

    await waitFor(() => expect(screen.queryByTestId('tag-filter-selected-tag-1')).not.toBeInTheDocument())
    lastCallParams = mockedUseUnifiedGallery.mock.calls.at(-1)?.[0]
    expect(lastCallParams?.tag).toBeUndefined()
  })

  it('clears all tags when clear button is pressed', async () => {
    const user = userEvent.setup()
    renderGalleryPage(['/gallery?tag=tag-1&tag=tag-2'])

    await waitFor(() => expect(screen.getByTestId('tag-filter-clear-all-button')).toBeInTheDocument())
    await user.click(screen.getByTestId('tag-filter-clear-all-button'))

    await waitFor(() => expect(screen.queryByTestId('tag-filter-selected-tag-1')).not.toBeInTheDocument())
    const lastCallParams = mockedUseUnifiedGallery.mock.calls.at(-1)?.[0]
    expect(lastCallParams?.tag).toBeUndefined()
  })
})
