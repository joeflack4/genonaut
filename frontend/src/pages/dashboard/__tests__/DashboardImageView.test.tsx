import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardImageView } from '../DashboardImageView'

vi.mock('../../../hooks', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../../hooks')
  return {
    ...actual,
    useGalleryItem: vi.fn(),
  }
})

const { useGalleryItem } = await import('../../../hooks')
const mockedUseGalleryItem = vi.mocked(useGalleryItem)

const renderWithRouter = (initialPath = '/dashboard/1') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/dashboard/:id" element={<DashboardImageView />} />
      </Routes>
    </MemoryRouter>
  )

const baseItem = {
  id: 1,
  title: 'Dashboard Item',
  description: 'Recent dashboard content.',
  imageUrl: null,
  pathThumb: '/thumb.png',
  contentData: '/image.png',
  contentType: 'image',
  qualityScore: 0.76,
  createdAt: '2024-02-01T00:00:00Z',
  updatedAt: '2024-02-01T00:00:00Z',
  creatorId: 'user-456',
  tags: ['dashboard', 'featured'],
  itemMetadata: { prompt: 'Featured content' },
  sourceType: 'regular' as const,
}

describe('DashboardImageView', () => {
  beforeEach(() => {
    mockedUseGalleryItem.mockReset()
  })

  it('renders dashboard item details when data is available', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: baseItem,
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter()

    expect(screen.getByTestId('dashboard-detail-title')).toHaveTextContent('Dashboard Item')
    expect(screen.getByTestId('dashboard-detail-image')).toBeInTheDocument()
    expect(screen.getByTestId('dashboard-detail-quality')).toHaveTextContent('Quality 76%')
    expect(screen.getByTestId('dashboard-detail-tags')).toHaveTextContent('dashboard')
  })

  it('shows placeholder when no image sources are available', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: { ...baseItem, pathThumb: null, contentData: null, imageUrl: null },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter()

    expect(screen.getByTestId('dashboard-detail-placeholder')).toBeInTheDocument()
  })

  it('displays loading state while fetching data', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any)

    renderWithRouter()

    expect(screen.getByTestId('dashboard-detail-loading')).toBeInTheDocument()
  })
})
