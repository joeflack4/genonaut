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
  contentData: null,
  contentType: 'image',
  qualityScore: null,
  createdAt: '2024-01-01T00:00:00.000Z',
  updatedAt: '2024-01-01T00:00:00.000Z',
  creatorId: 'creator-1',
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

    expect(screen.getByTestId('gallery-grid-item-1-image')).toHaveAttribute('src', '/thumbs/primary.png')
  })

  it('falls back to contentData when thumbnail is missing', () => {
    render(
      <ImageGridCell
        item={{ ...baseItem, id: 2, pathThumb: null, contentData: '/images/full.png' }}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
      />
    )

    expect(screen.getByTestId('gallery-grid-item-2-image')).toHaveAttribute('src', '/images/full.png')
  })

  it('displays placeholder icon when no media is available', () => {
    render(
      <ImageGridCell
        item={{ ...baseItem, id: 3, pathThumb: null, contentData: null, imageUrl: null }}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
      />
    )

    expect(screen.getByTestId('gallery-grid-item-3-placeholder')).toBeInTheDocument()
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
