import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { ImageGridCell } from '../ImageGridCell'
import { DEFAULT_THUMBNAIL_RESOLUTION } from '../../../constants/gallery'
import type { GalleryItem } from '../../../types/domain'

const baseItem: GalleryItem = {
  id: 1,
  title: 'Thumbnail Item',
  description: null,
  imageUrl: null,
  pathThumb: '/thumbs/primary.png',
  pathThumbsAltRes: null,
  contentData: null,
  contentType: 'image',
  prompt: null,
  qualityScore: null,
  createdAt: '2024-01-01T00:00:00.000Z',
  updatedAt: '2024-01-01T00:00:00.000Z',
  creatorId: 'creator-1',
  creatorUsername: 'creator-1',
  tags: [],
  itemMetadata: null,
  sourceType: 'regular',
}

describe('ImageGridCell', () => {
  it('renders thumbnail image when path is available', () => {
    render(
      <ImageGridCell
        item={baseItem}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
      />
    )

    expect(screen.getByTestId('gallery-grid-item-1-image').getAttribute('src')).toContain('/api/v1/images/1')
  })

  it('falls back to contentData when thumbnail is missing', () => {
    render(
      <ImageGridCell
        item={{ ...baseItem, id: 2, pathThumb: null, contentData: '/Users/test/image.png' }}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
      />
    )

    expect(screen.getByTestId('gallery-grid-item-2-image').getAttribute('src')).toContain('/api/v1/images/2')
  })

  it('prefers resolution-specific thumbnails when available', () => {
    render(
      <ImageGridCell
        item={{
          ...baseItem,
          id: 5,
          pathThumb: '/fallback.png',
          pathThumbsAltRes: { [DEFAULT_THUMBNAIL_RESOLUTION.id]: 'https://cdn.example.com/thumb.png' },
        }}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
      />
    )

    expect(screen.getByTestId('gallery-grid-item-5-image')).toHaveAttribute('src', 'https://cdn.example.com/thumb.png')
  })

  it('falls back to content ID when no media paths are available', () => {
    render(
      <ImageGridCell
        item={{ ...baseItem, id: 3, pathThumb: null, pathThumbsAltRes: null, contentData: null, imageUrl: null }}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
      />
    )

    expect(screen.getByTestId('gallery-grid-item-3-image').getAttribute('src')).toContain('/api/v1/images/3')
  })

  it('invokes onClick handler when provided', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()
    render(
      <ImageGridCell
        item={{ ...baseItem, id: 4 }}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
        onClick={handleClick}
      />
    )

    await user.click(screen.getByTestId('gallery-grid-item-4'))
    expect(handleClick).toHaveBeenCalledWith(expect.objectContaining({ id: 4 }))
  })
})
