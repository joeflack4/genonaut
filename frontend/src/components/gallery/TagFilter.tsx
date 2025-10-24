import { useState, useMemo, useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Chip,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Pagination,
  Popover,
  Select,
  Skeleton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import { useTags } from '../../hooks'
import type { ApiTag } from '../../types/api'

interface TagFilterProps {
  selectedTags: string[]
  onTagsChange: (tagIds: string[]) => void
  onTagClick?: (tagId: string) => void
  onNavigateToHierarchy?: () => void
  pageSize?: number
  tagPage?: number
  onTagPageChange?: (page: number) => void
  tagIdToNameMap?: Map<string, string>
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
  onNavigateToHierarchy,
  pageSize = 20,
  tagPage = 1,
  onTagPageChange,
  tagIdToNameMap,
}: TagFilterProps) {
  // Use controlled page if provided, otherwise use internal state
  const [internalPage, setInternalPage] = useState(1)
  const page = onTagPageChange ? tagPage : internalPage
  const setPage = onTagPageChange || setInternalPage

  const [sortOption, setSortOption] = useState<TagSortOption>('name-asc')
  const [popoverAnchor, setPopoverAnchor] = useState<{
    element: HTMLElement
    tagName: string
    isSelected: boolean
  } | null>(null)

  // Cache of all tags we've seen (to display names for Selected tags)
  const [tagCache, setTagCache] = useState<Map<string, ApiTag>>(new Map())

  // Track pending tag changes during multi-select mode
  const [pendingTags, setPendingTags] = useState<string[]>(selectedTags)
  const isMultiSelectActive = useRef(false)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('')

  const apiSort = useMemo(() => sortOption, [sortOption])

  // Fetch tags with pagination and search (backend filtering)
  const { data, isLoading } = useTags({
    page,
    page_size: pageSize,
    sort: apiSort,
    search: debouncedSearchQuery || undefined,
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

  // Debounce search query (1 second delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery)
      setPage(1) // Reset to first page when search changes
    }, 1000)

    return () => clearTimeout(timer)
  }, [searchQuery])

  // Listen for keyup events to commit pending changes
  useEffect(() => {
    const handleKeyUp = (event: KeyboardEvent) => {
      if ((event.key === 'Meta' || event.key === 'Alt') && isMultiSelectActive.current) {
        // Commit the pending tags when modifier key is released
        isMultiSelectActive.current = false
        onTagsChange(pendingTags)
      }
    }

    window.addEventListener('keyup', handleKeyUp)
    return () => window.removeEventListener('keyup', handleKeyUp)
  }, [pendingTags, onTagsChange])

  // Sync pendingTags with selectedTags when not in multi-select mode
  useEffect(() => {
    if (!isMultiSelectActive.current) {
      setPendingTags(selectedTags)
    }
  }, [selectedTags])

  // Handle tag selection with keyboard modifiers
  const handleTagSelect = (tagId: string, event: React.MouseEvent) => {
    // Check if shift key is pressed - if so, navigate to tag page instead
    if (event.shiftKey && onTagClick) {
      event.preventDefault()
      event.stopPropagation()
      onTagClick(tagId)
      return
    }

    const isMultiSelect = event.metaKey || event.altKey // Cmd on Mac, Alt on Windows

    // Determine which list to work with
    const currentTags = isMultiSelectActive.current ? pendingTags : selectedTags

    if (currentTags.includes(tagId)) {
      // Deselect tag
      const newTags = currentTags.filter((id) => id !== tagId)
      if (isMultiSelect) {
        isMultiSelectActive.current = true
        setPendingTags(newTags)
      } else {
        isMultiSelectActive.current = false
        onTagsChange(newTags)
      }
    } else {
      // Select tag - always append
      const newTags = [...currentTags, tagId]
      if (isMultiSelect) {
        isMultiSelectActive.current = true
        setPendingTags(newTags)
      } else {
        isMultiSelectActive.current = false
        onTagsChange(newTags)
      }
    }
  }

  // Handle deselect from selected chips
  const handleDeselectTag = (tagId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    const newTags = displayTags.filter((id) => id !== tagId)
    if (isMultiSelectActive.current) {
      setPendingTags(newTags)
    } else {
      onTagsChange(newTags)
    }
  }

  // Handle selected chip click (navigate to tag detail)
  const handleSelectedChipClick = (tagId: string) => {
    if (onTagClick) {
      onTagClick(tagId)
    }
  }

  // Handle popover
  const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>, tagName: string, isSelected: boolean = false) => {
    // Always show popover for selected tags, or for truncated tags
    if (isSelected || tagName.length > TRUNCATE_THRESHOLD) {
      setPopoverAnchor({ element: event.currentTarget, tagName, isSelected })
    }
  }

  const handlePopoverClose = () => {
    setPopoverAnchor(null)
  }

  // Backend handles filtering and pagination - no client-side logic needed

  // Find selected tag objects for display (use pending tags if in multi-select mode)
  const displayTags = isMultiSelectActive.current ? pendingTags : selectedTags

  const selectedTagObjects = useMemo(() => {
    return displayTags.map((id) => {
      // First check cache
      const cached = tagCache.get(id)
      if (cached) {
        return cached
      }

      // If not in cache, try to get name from tagIdToNameMap (from parent)
      const name = tagIdToNameMap?.get(id) ?? id

      return {
        id,
        name,
        created_at: '',
        updated_at: '',
        metadata: {},
        average_rating: null,
        rating_count: 0,
        slug: name,
        description: '',
        ancestors: [],
        descendants: [],
        is_favorite: false,
      } as ApiTag
    })
  }, [displayTags, tagCache, tagIdToNameMap])

  return (
    <Box data-testid="tag-filter">
      {/* Search tags input with hierarchy nav button */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2, alignItems: 'flex-start' }}>
        <TextField
          fullWidth
          size="small"
          label="Search tags"
          placeholder='Type to filter (or "exact match")'
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          inputProps={{ 'data-testid': 'tag-filter-search-input' }}
          data-testid="tag-filter-search"
        />
        {onNavigateToHierarchy && (
          <Tooltip title="Go to tag hierarchy page" enterDelay={300} arrow>
            <IconButton
              size="small"
              onClick={onNavigateToHierarchy}
              sx={{ mt: 0.5 }}
              data-testid="tag-filter-hierarchy-button"
            >
              <AccountTreeIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Sort dropdown and clear button */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <FormControl size="small" sx={{ flex: displayTags.length > 0 ? '2 1 0%' : '1 1 100%' }}>
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
        {displayTags.length > 0 && (
          <Button
            variant="outlined"
            color="secondary"
            size="small"
            onClick={() => {
              isMultiSelectActive.current = false
              onTagsChange([])
              setPendingTags([])
            }}
            sx={{ flex: '1 1 0%', minWidth: '80px' }}
            data-testid="tag-filter-clear-all-button"
          >
            Clear All
          </Button>
        )}
      </Box>

      {/* Selected tags section */}
      {displayTags.length > 0 && (
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
                onMouseEnter={(e) => handlePopoverOpen(e, tag.name, true)}
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
            {debouncedSearchQuery ? 'No tags match your search' : 'No tags found'}
          </Typography>
        ) : (
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
            {tags.map((tag) => {
              const isSelected = displayTags.includes(tag.id)
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
      {!isLoading && tags.length > 0 && (
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

      {/* Info text */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block', mt: 2 }}
        data-testid="tag-filter-info"
      >
        (1) Click to add tags. (2) Hold Command (Mac) or Alt (Windows) to select multiple before querying. (3) Shift+click to open tag's info page.
      </Typography>

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
        disableAutoFocus
        disableEnforceFocus
        disableRestoreFocus
        sx={{ pointerEvents: 'none' }}
        data-testid="tag-filter-popover"
      >
        <Box sx={{ p: 1, maxWidth: 300 }}>
          {popoverAnchor?.isSelected ? (
            <Typography variant="body2">Click to open tag page</Typography>
          ) : (
            <Typography variant="body2">{popoverAnchor?.tagName}</Typography>
          )}
        </Box>
      </Popover>
    </Box>
  )
}
