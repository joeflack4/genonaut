import { useState, type ReactElement } from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { TagFilter } from '../TagFilter'

vi.mock('../../../hooks', () => {
  const useTags = vi.fn()
  return { useTags }
})

const { useTags } = await import('../../../hooks')
const mockedUseTags = vi.mocked(useTags)

function createTagsResponse(overrides?: { totalPages?: number; items?: Array<{ id: string; name: string }> }) {
  const items = overrides?.items ?? [
    {
      id: 'tag-1',
      name: 'Landscape',
      metadata: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      average_rating: 4.5,
      rating_count: 12,
    },
    {
      id: 'tag-2',
      name: 'Portrait Photography',
      metadata: {},
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      average_rating: 3.8,
      rating_count: 5,
    },
  ]

  return {
    data: {
      items,
      pagination: {
        page: 1,
        page_size: 20,
        total_count: items.length,
        total_pages: overrides?.totalPages ?? 1,
        has_next: false,
        has_previous: false,
      },
    },
    isLoading: false,
  }
}

type HarnessOptions = {
  initialSelected?: string[]
  onTagsChange?: (tags: string[]) => void
  onTagClick?: (tagId: string) => void
}

function renderTagFilterHarness(options: HarnessOptions = {}) {
  const { initialSelected = [], onTagsChange, onTagClick } = options

  const Harness = (): ReactElement => {
    const [selected, setSelected] = useState<string[]>(initialSelected)

    return (
      <TagFilter
        selectedTags={selected}
        onTagsChange={(next) => {
          setSelected(next)
          onTagsChange?.(next)
        }}
        onTagClick={onTagClick}
      />
    )
  }

  return render(<Harness />)
}

describe('TagFilter', () => {
  beforeEach(() => {
    mockedUseTags.mockReset()
    mockedUseTags.mockReturnValue(createTagsResponse())
  })

  it('renders available tags and displays Selected tags', async () => {
    renderTagFilterHarness()

    expect(screen.getByTestId('tag-filter')).toBeInTheDocument()
    expect(screen.getByTestId('tag-filter-chip-tag-1')).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByTestId('tag-filter-chip-tag-1'))

    await waitFor(() => expect(screen.getByTestId('tag-filter-selected-tag-1')).toBeInTheDocument())
  })

  it('supports multi-select with modifier keys and deselection', async () => {
    const user = userEvent.setup()
    renderTagFilterHarness()

    // Select first tag
    await user.click(screen.getByTestId('tag-filter-chip-tag-1'))

    // Select second tag with meta key for multi-select
    fireEvent.click(screen.getByTestId('tag-filter-chip-tag-2'), { metaKey: true })

    await waitFor(() => {
      expect(screen.getByTestId('tag-filter-selected-tag-1')).toBeInTheDocument()
      expect(screen.getByTestId('tag-filter-selected-tag-2')).toBeInTheDocument()
    })

    // Clicking again should remove from selection
    await user.click(screen.getByTestId('tag-filter-chip-tag-1'))
    await waitFor(() => expect(screen.queryByTestId('tag-filter-selected-tag-1')).not.toBeInTheDocument())
  })

  it('invokes onTagClick when selected tag chip is pressed', async () => {
    const onTagClick = vi.fn()
    renderTagFilterHarness({ initialSelected: ['tag-1'], onTagClick })

    await waitFor(() => expect(screen.getByTestId('tag-filter-selected-tag-1')).toBeInTheDocument())

    await userEvent.click(screen.getByTestId('tag-filter-selected-tag-1'))

    expect(onTagClick).toHaveBeenCalledWith('tag-1')
  })

  it('shows truncated labels and popover for long tag names', async () => {
    mockedUseTags.mockReturnValue(createTagsResponse({
      items: [
        {
          id: 'tag-long',
          name: 'Extremely Long Tag Name That Should Truncate Properly',
          metadata: {},
          created_at: '2024-01-03T00:00:00Z',
          updated_at: '2024-01-03T00:00:00Z',
          average_rating: 4,
          rating_count: 3,
        },
      ],
    }))

    renderTagFilterHarness()

    const chip = screen.getByTestId('tag-filter-chip-tag-long')
    expect(chip.textContent).toMatch(/\.\.\.$/)

    fireEvent.mouseEnter(chip)
    await waitFor(() =>
      expect(
        screen.getByText('Extremely Long Tag Name That Should Truncate Properly')
      ).toBeInTheDocument()
    )
  })

  it('changes sort option and requests new tag data', async () => {
    const user = userEvent.setup()
    renderTagFilterHarness()

    await user.click(screen.getByLabelText(/sort tags/i))
    await user.click(screen.getByText('Rating (High to Low)'))

    await waitFor(() => {
      const lastCall = mockedUseTags.mock.calls.at(-1)?.[0] ?? {}
      expect(lastCall.sort).toBe('rating-desc')
    })
  })

  it('supports pagination when multiple pages are available', async () => {
    // Create enough items to span 2 pages (with pageSize=20, need 21+ items)
    const manyItems = Array.from({ length: 25 }, (_, i) => ({
      id: `tag-${i + 1}`,
      name: `Tag ${i + 1}`,
      metadata: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      average_rating: 4.5,
      rating_count: 12,
    }))

    mockedUseTags.mockReturnValue(createTagsResponse({ totalPages: 2, items: manyItems }))

    renderTagFilterHarness()

    const nextPageButton = screen.getByRole('button', { name: 'Go to page 2' })
    await userEvent.click(nextPageButton)

    await waitFor(() => {
      const lastCall = mockedUseTags.mock.calls.at(-1)?.[0] ?? {}
      expect(lastCall.page).toBe(2)
    })
  })

  it('allows removing Selected tags via delete button', async () => {
    renderTagFilterHarness({ initialSelected: ['tag-1'] })

    await waitFor(() => expect(screen.getByTestId('tag-filter-selected-tag-1')).toBeInTheDocument())

    const deleteButton = screen.getByTestId('tag-filter-selected-tag-1-delete')
    fireEvent.click(deleteButton)

    await waitFor(() => expect(screen.queryByTestId('tag-filter-selected-tag-1')).not.toBeInTheDocument())
  })

  it('provides a clear all button when tags are selected', async () => {
    renderTagFilterHarness({ initialSelected: ['tag-1', 'tag-2'] })

    await waitFor(() => expect(screen.getByTestId('tag-filter-clear-all-button')).toBeInTheDocument())
    await userEvent.click(screen.getByTestId('tag-filter-clear-all-button'))

    await waitFor(() => {
      expect(screen.queryByTestId('tag-filter-selected-tag-1')).not.toBeInTheDocument()
      expect(screen.queryByTestId('tag-filter-selected-tag-2')).not.toBeInTheDocument()
    })
  })

  it('displays placeholder chips for tags not yet loaded', async () => {
    mockedUseTags.mockReturnValue(createTagsResponse({ items: [] }))

    renderTagFilterHarness({ initialSelected: ['missing-tag'] })

    await waitFor(() => {
      const chip = screen.getByTestId('tag-filter-selected-missing-tag')
      expect(chip).toBeInTheDocument()
      expect(chip).toHaveTextContent('missing-tag')
    })
  })
})
