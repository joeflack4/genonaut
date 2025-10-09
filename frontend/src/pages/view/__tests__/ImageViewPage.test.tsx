import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ImageViewPage } from '../ImageViewPage'

vi.mock('../../../hooks', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('../../../hooks')
  return {
    ...actual,
    useGalleryItem: vi.fn(),
  }
})

const { useGalleryItem } = await import('../../../hooks')
const mockedUseGalleryItem = vi.mocked(useGalleryItem)

const renderWithRouter = (initialPath = '/view/1', state: Record<string, unknown> = {}) =>
  render(
    <MemoryRouter initialEntries={[{ pathname: initialPath, state }]}>
      <Routes>
        <Route path="/view/:id" element={<ImageViewPage />} />
      </Routes>
    </MemoryRouter>
  )

const baseItem = {
  id: 1,
  title: 'Rendered Artwork',
  description: 'Placeholder content for testing.',
  imageUrl: null,
  pathThumb: '/api/v1/images/1?thumbnail=small',
  pathThumbsAltRes: null,
  contentData: '/image.png',
  contentType: 'image',
  prompt: 'Serene landscape',
  qualityScore: 0.82,
  createdAt: '2024-02-01T00:00:00Z',
  updatedAt: '2024-02-01T00:00:00Z',
  creatorId: 'user-123',
  creatorUsername: 'artist-123',
  tags: ['artistic_medium', 'landscape'],
  itemMetadata: { prompt: 'Serene landscape' },
  sourceType: 'regular' as const,
}

describe('ImageViewPage', () => {
  beforeEach(() => {
    mockedUseGalleryItem.mockReset()
  })

  it('renders item details when data is available', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: baseItem,
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1', { sourceType: 'regular' })

    expect(screen.getByTestId('image-view-title')).toHaveTextContent('Rendered Artwork')
    expect(screen.getByTestId('image-view-image')).toBeInTheDocument()
    expect(screen.getByTestId('image-view-quality')).toHaveTextContent('Rating 82%')
    expect(screen.getByTestId('image-view-tags')).toHaveTextContent('artistic_medium')
    expect(screen.getByTestId('image-view-creator')).toHaveTextContent('By: artist-123')
    expect(screen.getByTestId('image-view-source')).toHaveTextContent('User-generated')
  })

  it('truncates long titles to 70 characters with ellipsis', () => {
    const longTitle = 'A very long title that exceeds the seventy character limit intentionally to verify truncation logic'
    mockedUseGalleryItem.mockReturnValue({
      data: {
        ...baseItem,
        title: longTitle,
      },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    const titleNode = screen.getByTestId('image-view-title')
    expect(titleNode).toHaveTextContent(`${longTitle.slice(0, 70)}...`)
    expect(titleNode).toHaveAttribute('title', longTitle)
  })

  it('falls back to content ID when no image sources are available', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: { ...baseItem, pathThumb: null, pathThumbsAltRes: null, contentData: null, imageUrl: null },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    const image = screen.getByTestId('image-view-image') as HTMLImageElement
    expect(image.getAttribute('src')).toBe('http://localhost:8001/api/v1/images/1')
  })

  it('renders tags section even when no tags are present', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: {
        ...baseItem,
        tags: [],
        itemMetadata: {},
      },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    expect(screen.getByTestId('image-view-tags')).toHaveTextContent('No tags')
  })

  it('uses metadata prompt and tags when top-level fields are missing', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: {
        ...baseItem,
        tags: [],
        prompt: null,
        itemMetadata: {
          prompt: 'Metadata prompt text',
          tags: ['metadata-tag'],
        },
      },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    expect(screen.getByTestId('image-view-prompt')).toHaveTextContent('Metadata prompt text')
    expect(screen.getByTestId('image-view-tags')).toHaveTextContent('metadata-tag')
  })

  it('falls back to prompt field when metadata prompt is absent', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: {
        ...baseItem,
        itemMetadata: {},
        prompt: 'Top-level prompt',
      },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    expect(screen.getByTestId('image-view-prompt')).toHaveTextContent('Top-level prompt')
  })

  it('falls back to content ID image URL when paths are file system locations', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: {
        ...baseItem,
        pathThumb: '/Users/test/thumb.png',
        pathThumbsAltRes: null,
        contentData: '/Users/test/image.png',
        imageUrl: null,
      },
      isLoading: false,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    const image = screen.getByTestId('image-view-image') as HTMLImageElement
    expect(image).toBeInTheDocument()
    expect(image.getAttribute('src')).toBe('http://localhost:8001/api/v1/images/1')
  })

  it('displays loading state while fetching data', () => {
    mockedUseGalleryItem.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any)

    renderWithRouter('/view/1')

    expect(screen.getByTestId('image-view-loading')).toBeInTheDocument()
  })
})
