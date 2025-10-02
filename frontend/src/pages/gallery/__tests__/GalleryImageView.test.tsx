import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { GalleryImageView } from '../GalleryImageView'

vi.mock('../../../hooks', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../../hooks')
  return {
    ...actual,
    useGalleryItem: vi.fn(),
  }
})

const { useGalleryItem } = await import('../../../hooks')
const mockedUseGalleryItem = vi.mocked(useGalleryItem)

const renderWithRouter = (initialPath = '/gallery/1') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/gallery/:id" element={<GalleryImageView />} />
      </Routes>
    </MemoryRouter>
  )

const baseItem = {
  id: 1,
  title: 'Mock Artwork',
  description: 'Placeholder content for testing.',
  imageUrl: null,
  pathThumb: '/thumb.png',
  contentData: '/image.png',
  contentType: 'image',
  qualityScore: 0.82,
  createdAt: '2024-02-01T00:00:00Z',
  updatedAt: '2024-02-01T00:00:00Z',
  creatorId: 'user-123',
  tags: ['artistic_medium', 'landscape'],
  itemMetadata: { prompt: 'Serene landscape' },
  sourceType: 'regular' as const,
}

describe('GalleryImageView', () => {
  beforeEach(() => {
    mockedUseGalleryItem.mockReset()
  })

  it('renders gallery item details when data is available', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: baseItem,
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter()

    expect(screen.getByTestId('gallery-detail-title')).toHaveTextContent('Mock Artwork')
    expect(screen.getByTestId('gallery-detail-image')).toBeInTheDocument()
    expect(screen.getByTestId('gallery-detail-quality')).toHaveTextContent('Quality 82%')
    expect(screen.getByTestId('gallery-detail-prompt')).toHaveTextContent('Serene landscape')
    expect(screen.getByTestId('gallery-detail-tags')).toHaveTextContent('artistic_medium')
  })

  it('shows placeholder when no image sources are available', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: { ...baseItem, pathThumb: null, contentData: null, imageUrl: null },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter()

    expect(screen.getByTestId('gallery-detail-placeholder')).toBeInTheDocument()
  })

  it('displays loading state while fetching data', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any)

    renderWithRouter()

    expect(screen.getByTestId('gallery-detail-loading')).toBeInTheDocument()
  })
})
