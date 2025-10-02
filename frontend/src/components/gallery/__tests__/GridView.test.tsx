import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { GridView } from '../GridView'
import { DEFAULT_THUMBNAIL_RESOLUTION } from '../../../constants/gallery'
import type { GalleryItem } from '../../../types/domain'

const createGalleryItem = (overrides: Partial<GalleryItem> = {}): GalleryItem => ({
  id: overrides.id ?? 1,
  title: overrides.title ?? 'Sample Item',
  description: overrides.description ?? null,
  imageUrl: overrides.imageUrl ?? null,
  pathThumb: overrides.pathThumb ?? '/static/thumb.png',
  contentData: overrides.contentData ?? null,
  contentType: overrides.contentType ?? 'image',
  qualityScore: overrides.qualityScore ?? null,
  createdAt: overrides.createdAt ?? '2024-01-01T00:00:00.000Z',
  updatedAt: overrides.updatedAt ?? '2024-01-01T00:00:00.000Z',
  creatorId: overrides.creatorId ?? 'creator-1',
  tags: overrides.tags ?? [],
  itemMetadata: overrides.itemMetadata ?? null,
  sourceType: overrides.sourceType ?? 'regular',
})

describe('GridView', () => {
  it('renders grid items and triggers click handler', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()
    const items = [createGalleryItem({ id: 101, title: 'Gallery Entry' })]

    render(
      <GridView
        items={items}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
        onItemClick={handleClick}
        dataTestId="grid-under-test"
      />
    )

    expect(screen.getByTestId('grid-under-test')).toBeInTheDocument()
    expect(screen.getByTestId('gallery-grid-item-101-title')).toHaveTextContent('Gallery Entry')

    await user.click(screen.getByTestId('gallery-grid-item-101'))
    expect(handleClick).toHaveBeenCalledWith(items[0])
  })

  it('renders loading skeleton placeholders when loading', () => {
    render(
      <GridView
        items={[]}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
        isLoading
        loadingPlaceholderCount={3}
        dataTestId="grid-loading"
      />
    )

    const skeletons = screen.getAllByTestId(/gallery-grid-skeleton-/)
    expect(skeletons).toHaveLength(3)
    expect(screen.queryByTestId('gallery-grid-empty')).not.toBeInTheDocument()
  })

  it('renders empty state message when there are no items', () => {
    render(
      <GridView
        items={[]}
        resolution={DEFAULT_THUMBNAIL_RESOLUTION}
        emptyMessage="No results"
        dataTestId="grid-empty"
      />
    )

    expect(screen.getByTestId('gallery-grid-empty')).toHaveTextContent('No results')
  })
})
