import { useState, useMemo, useEffect } from 'react'
import {
  Box,
  Button,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Pagination,
  Popover,
  Select,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { useTags } from '../../hooks'
import type { ApiTag } from '../../types/api'

interface TagFilterProps {
  selectedTags: string[]
  onTagsChange: (tagIds: string[]) => void
  onTagClick?: (tagId: string) => void
  pageSize?: number
}

type TagSortOption = 'name-asc' | 'name-desc' | 'rating-asc' | 'rating-desc'

const TRUNCATE_LENGTH = 22
const TRUNCATE_THRESHOLD = 25

const sortOptions: Array<{ value: TagSortOption; label: string }> = [
  { value: 'name-asc', label: 'Name (A-Z)' },
  { value: 'name-desc', label: 'Name (Z-A)' },
  { value: 'rating-asc', label: 'Rating (Low to High)' },
  { value: 'rating-desc', label: 'Rating (High to Low)' },
]

function truncateTagName(name: string): string {
  if (name.length <= TRUNCATE_THRESHOLD) {
    return name
  }
  return name.substring(0, TRUNCATE_LENGTH) + '...'
}

export function TagFilter({
  selectedTags,
  onTagsChange,
  onTagClick,
  pageSize = 20,
}: TagFilterProps) {
  const [page, setPage] = useState(1)
  const [sortOption, setSortOption] = useState<TagSortOption>('name-asc')
  const [popoverAnchor, setPopoverAnchor] = useState<{
    element: HTMLElement
    tagName: string
  } | null>(null)

  // Cache of all tags we've seen (to display names for Selected tags)
  const [tagCache, setTagCache] = useState<Map<string, ApiTag>>(new Map())

  const apiSort = useMemo(() => sortOption, [sortOption])

  // Fetch tags with pagination
  const { data, isLoading } = useTags({
    page,
    page_size: pageSize,
    sort: apiSort,
  })

  const tags = data?.items || []
  const totalPages = data?.pagination?.total_pages || 1

  // Update tag cache whenever new tags are fetched
  useEffect(() => {
    if (tags.length > 0) {
      setTagCache(prev => {
        const newCache = new Map(prev)
        tags.forEach(tag => newCache.set(tag.id, tag))
        return newCache
      })
    }
  }, [tags])

  // Handle tag selection with keyboard modifiers
  const handleTagSelect = (tagId: string, event: React.MouseEvent) => {
    const isMultiSelect = event.metaKey || event.altKey // Cmd on Mac, Alt on Windows

    if (selectedTags.includes(tagId)) {
      // Deselect tag
      onTagsChange(selectedTags.filter((id) => id !== tagId))
    } else {
      // Select tag
      if (isMultiSelect) {
        onTagsChange([...selectedTags, tagId])
      } else {
        onTagsChange([tagId])
      }
    }
  }

  // Handle deselect from selected chips
  const handleDeselectTag = (tagId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    onTagsChange(selectedTags.filter((id) => id !== tagId))
  }

  // Handle selected chip click (navigate to tag detail)
  const handleSelectedChipClick = (tagId: string) => {
    if (onTagClick) {
      onTagClick(tagId)
    }
  }

  // Handle popover
  const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>, tagName: string) => {
    if (tagName.length > TRUNCATE_THRESHOLD) {
      setPopoverAnchor({ element: event.currentTarget, tagName })
    }
  }

  const handlePopoverClose = () => {
    setPopoverAnchor(null)
  }

  // Find selected tag objects for display
  const selectedTagObjects = useMemo(() => {
    return selectedTags.map((id) => {
      const cached = tagCache.get(id)
      if (cached) {
        return cached
      }

      return {
        id,
        name: id,
        created_at: '',
        updated_at: '',
        metadata: {},
        average_rating: null,
        rating_count: 0,
        slug: id,
        description: '',
        ancestors: [],
        descendants: [],
        is_favorite: false,
      } as ApiTag
    })
  }, [selectedTags, tagCache])

  return (
    <Box data-testid="tag-filter">
      {/* Sort dropdown */}
      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
        <InputLabel id="tag-sort-label">Sort Tags</InputLabel>
        <Select
          labelId="tag-sort-label"
          value={sortOption}
          label="Sort Tags"
          onChange={(e) => {
            setSortOption(e.target.value as TagSortOption)
            setPage(1) // Reset to first page on sort change
          }}
          data-testid="tag-filter-sort"
        >
          {sortOptions.map((option) => (
            <MenuItem key={option.value} value={option.value} data-testid={`tag-sort-${option.value}`}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Info text */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block', mb: 2 }}
        data-testid="tag-filter-info"
      >
        Click to select/deselect. Hold Command (Mac) or Alt (Windows) for multiple selections.
      </Typography>

      {/* Selected tags section */}
      {selectedTags.length > 0 && (
        <Box sx={{ mb: 2 }} data-testid="tag-filter-selected">
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Selected tags:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
            {selectedTagObjects.map((tag) => (
              <Chip
                key={tag.id}
                label={truncateTagName(tag.name)}
                onClick={() => handleSelectedChipClick(tag.id)}
                onDelete={(e) => handleDeselectTag(tag.id, e as React.MouseEvent)}
                deleteIcon={<CloseIcon data-testid={`tag-filter-selected-${tag.id}-delete`} />}
                color="primary"
                size="small"
                sx={{ cursor: 'pointer' }}
                data-testid={`tag-filter-selected-${tag.id}`}
                onMouseEnter={(e) => handlePopoverOpen(e, tag.name)}
                onMouseLeave={handlePopoverClose}
              />
            ))}
          </Stack>
        </Box>
      )}

      {/* Available tags list */}
      <Box data-testid="tag-filter-list">
        {isLoading ? (
          <Stack spacing={1}>
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton
                key={`tag-skeleton-${index}`}
                variant="rectangular"
                height={32}
                sx={{ borderRadius: 2 }}
                data-testid={`tag-filter-skeleton-${index}`}
              />
            ))}
          </Stack>
        ) : tags.length === 0 ? (
          <Typography
            variant="body2"
            color="text.secondary"
            data-testid="tag-filter-empty"
          >
            No tags found
          </Typography>
        ) : (
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
            {tags.map((tag) => {
              const isSelected = selectedTags.includes(tag.id)
              return (
                <Chip
                  key={tag.id}
                  label={truncateTagName(tag.name)}
                  onClick={(e) => handleTagSelect(tag.id, e)}
                  color={isSelected ? 'primary' : 'default'}
                  variant={isSelected ? 'filled' : 'outlined'}
                  size="small"
                  sx={{ cursor: 'pointer' }}
                  data-testid={`tag-filter-chip-${tag.id}`}
                  onMouseEnter={(e) => handlePopoverOpen(e, tag.name)}
                  onMouseLeave={handlePopoverClose}
                />
              )
            })}
          </Stack>
        )}
      </Box>

      {/* Pagination */}
      {!isLoading && totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, newPage) => setPage(newPage)}
            color="primary"
            size="small"
            data-testid="tag-filter-pagination"
          />
        </Box>
      )}

      {selectedTags.length > 0 && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            color="secondary"
            size="small"
            onClick={() => onTagsChange([])}
            data-testid="tag-filter-clear-all-button"
          >
            Clear All Tags
          </Button>
        </Box>
      )}

      {/* Popover for full tag names */}
      <Popover
        open={Boolean(popoverAnchor)}
        anchorEl={popoverAnchor?.element}
        onClose={handlePopoverClose}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        disableRestoreFocus
        sx={{ pointerEvents: 'none' }}
        data-testid="tag-filter-popover"
      >
        <Box sx={{ p: 1, maxWidth: 300 }}>
          <Typography variant="body2">{popoverAnchor?.tagName}</Typography>
        </Box>
      </Popover>
    </Box>
  )
}
