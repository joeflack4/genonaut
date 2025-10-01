import { useMemo, useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { SelectChangeEvent } from '@mui/material/Select'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Drawer,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Pagination,
  Popover,
  Select,
  Skeleton,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { useUnifiedGallery, useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'

const PAGE_SIZE = 10
const PANEL_WIDTH = 360
const DEFAULT_USER_ID = ADMIN_USER_ID
const GALLERY_OPTIONS_OPEN_KEY = 'gallery-options-open'

type SortOption = 'recent' | 'top-rated'

interface FiltersState {
  search: string
  sort: SortOption
  page: number
  tag?: string | string[]  // Tag filter from URL - single or multiple tags
}

interface ContentToggles {
  yourGens: boolean
  yourAutoGens: boolean
  communityGens: boolean
  communityAutoGens: boolean
}

const sortOptions: Array<{ value: SortOption; label: string }> = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'top-rated', label: 'Top Rated' },
]

export function GalleryPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchInput, setSearchInput] = useState('')

  // Initialize filters from URL parameters
  const [filters, setFilters] = useState<FiltersState>(() => {
    // Handle multiple tag parameters from URL
    const tags = searchParams.getAll('tag')
    const tag = tags.length === 0 ? undefined : tags.length === 1 ? tags[0] : tags
    return {
      search: '',
      sort: 'recent' as SortOption,
      page: 0,
      tag
    }
  })

  // Initialize optionsOpen state from localStorage
  const [optionsOpen, setOptionsOpen] = useState(() => {
    try {
      const stored = localStorage.getItem(GALLERY_OPTIONS_OPEN_KEY)
      return stored !== null ? JSON.parse(stored) : true
    } catch {
      return true
    }
  })

  // Popover state for stats
  const [statsAnchorEl, setStatsAnchorEl] = useState<HTMLElement | null>(null)
  const [contentToggles, setContentToggles] = useState<ContentToggles>({
    yourGens: true,
    yourAutoGens: true,
    communityGens: true,
    communityAutoGens: true,
  })

  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  // Update filters when URL parameters change
  useEffect(() => {
    const tags = searchParams.getAll('tag')
    const tag = tags.length === 0 ? undefined : tags.length === 1 ? tags[0] : tags
    setFilters(prev => ({ ...prev, tag, page: 0 }))
  }, [searchParams])

  // Save optionsOpen state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(GALLERY_OPTIONS_OPEN_KEY, JSON.stringify(optionsOpen))
    } catch {
      // Ignore localStorage errors
    }
  }, [optionsOpen])


  // Determine content types based on toggles
  const contentTypes = useMemo(() => {
    const types = []
    if (contentToggles.yourGens || contentToggles.communityGens) {
      types.push('regular')
    }
    if (contentToggles.yourAutoGens || contentToggles.communityAutoGens) {
      types.push('auto')
    }
    return types
  }, [contentToggles])

  // Determine creator filter
  const creatorFilter = useMemo(() => {
    const userContent = contentToggles.yourGens || contentToggles.yourAutoGens
    const communityContent = contentToggles.communityGens || contentToggles.communityAutoGens

    if (userContent && communityContent) {
      return 'all'
    } else if (userContent) {
      return 'user'
    } else if (communityContent) {
      return 'community'
    }
    return 'all'
  }, [contentToggles])

  // Use unified gallery API
  const { data: unifiedData, isLoading } = useUnifiedGallery({
    page: filters.page + 1, // Convert from 0-based to 1-based
    pageSize: PAGE_SIZE,
    contentTypes,
    creatorFilter,
    userId,
    searchTerm: filters.search || undefined,
    sortField: filters.sort === 'recent' ? 'created_at' : 'quality_score',
    sortOrder: 'desc',
    tag: filters.tag, // Pass tag filter(s) to API
  })

  const data = unifiedData

  const totalPages = useMemo(() => {
    if (!data?.total) {
      return 1
    }

    return Math.max(1, Math.ceil(data.total / PAGE_SIZE))
  }, [data])

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFilters((prev) => ({ ...prev, search: searchInput.trim(), page: 0 }))
  }

  const handleSortChange = (event: SelectChangeEvent<SortOption>) => {
    setFilters((prev) => ({ ...prev, sort: event.target.value as SortOption, page: 0 }))
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, page: number) => {
    setFilters((prev) => ({ ...prev, page: page - 1 }))
  }

  const handleToggleChange = (toggleKey: keyof ContentToggles) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setContentToggles((prev) => ({
      ...prev,
      [toggleKey]: event.target.checked,
    }))
    // Reset page when toggling content types
    setFilters((prev) => ({ ...prev, page: 0 }))
  }

  return (
    <Box
      component="section"
      sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}
      data-testid="gallery-page-root"
    >
      {!optionsOpen && (
        <Tooltip title="Options" enterDelay={300} arrow>
          <IconButton
            aria-label="Options"
            onClick={() => setOptionsOpen(true)}
            sx={{
              position: 'fixed',
              top: (theme) => theme.spacing(10), // Increased from 2 to 10 to be below navbar
              right: (theme) => theme.spacing(2),
              zIndex: (theme) => theme.zIndex.drawer + 1,
              bgcolor: 'background.paper',
              boxShadow: 1,
            }}
            data-testid="gallery-options-open-button"
          >
            <SettingsOutlinedIcon />
          </IconButton>
        </Tooltip>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
        }}
        data-testid="gallery-content-wrapper"
      >
        <Stack spacing={4} data-testid="gallery-content-stack">
          <Stack spacing={1} data-testid="gallery-header">
            <Typography
              component="h1"
              variant="h4"
              fontWeight={600}
              gutterBottom
              data-testid="gallery-title"
            >
              Gallery
            </Typography>
          </Stack>
          <Card data-testid="gallery-results-card">
            <CardContent>
              {isLoading ? (
                <Stack spacing={2} data-testid="gallery-results-loading">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton
                      key={index}
                      variant="rectangular"
                      height={72}
                      data-testid={`gallery-results-skeleton-${index}`}
                    />
                  ))}
                </Stack>
              ) : data && data.items.length > 0 ? (
                <List data-testid="gallery-results-list">
                  {data.items.map((item) => (
                    <ListItem
                      key={item.id}
                      alignItems="flex-start"
                      divider
                      data-testid={`gallery-result-item-${item.id}`}
                    >
                      <ListItemText
                        primary={
                          <Stack
                            direction="row"
                            justifyContent="space-between"
                            alignItems="center"
                            spacing={2}
                            data-testid={`gallery-result-item-${item.id}-header`}
                          >
                            <Typography variant="h6" component="span" data-testid={`gallery-result-item-${item.id}-title`}>
                              {item.title}
                            </Typography>
                            {item.qualityScore !== null && item.qualityScore !== undefined && (
                              <Chip
                                label={`Quality ${(item.qualityScore * 100).toFixed(0)}%`}
                                color={item.qualityScore > 0.75 ? 'success' : 'default'}
                                data-testid={`gallery-result-item-${item.id}-quality`}
                              />
                            )}
                          </Stack>
                        }
                        secondary={
                          <Box
                            sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mt: 1 }}
                            data-testid={`gallery-result-item-${item.id}-meta`}
                          >
                            {item.description && (
                              <Typography
                                variant="body2"
                                color="text.secondary"
                                component="span"
                                data-testid={`gallery-result-item-${item.id}-description`}
                              >
                                {item.description}
                              </Typography>
                            )}
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              component="span"
                              data-testid={`gallery-result-item-${item.id}-created`}
                            >
                              Created {new Date(item.createdAt).toLocaleString()}
                            </Typography>
                          </Box>
                        }
                        primaryTypographyProps={{ component: 'span' }}
                        secondaryTypographyProps={{ component: 'span' }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" data-testid="gallery-results-empty">
                  No gallery items found. Try adjusting your filters.
                </Typography>
              )}
            </CardContent>
          </Card>

          <Box display="flex" justifyContent="flex-end" data-testid="gallery-pagination">
            <Pagination
              count={totalPages}
              page={filters.page + 1}
              onChange={handlePageChange}
              color="primary"
              shape="rounded"
              data-testid="gallery-pagination-control"
            />
          </Box>
        </Stack>
      </Box>

      <Drawer
        anchor="right"
        variant="persistent"
        open={optionsOpen}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: PANEL_WIDTH },
            boxSizing: 'border-box',
            p: 3,
            gap: 3,
            position: 'fixed',
            zIndex: (theme) => theme.zIndex.drawer,
          },
        }}
        data-testid="gallery-options-drawer"
      >
        <Stack spacing={3} sx={{ height: '100%' }} data-testid="gallery-options-stack">
          <Box sx={{ textAlign: 'center' }} data-testid="gallery-options-summary">
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontStyle: 'italic', display: 'inline' }}
              data-testid="gallery-options-summary-text"
            >
              {totalPages.toLocaleString()} pages showing {data?.total?.toLocaleString() || 0} results matching filters.
            </Typography>
            {data?.stats && (
              <IconButton
                size="small"
                sx={{
                  ml: 0.5,
                  p: 0.25,
                  color: 'text.secondary'
                }}
                onMouseEnter={(event) => setStatsAnchorEl(event.currentTarget)}
                onMouseLeave={() => setStatsAnchorEl(null)}
                data-testid="gallery-options-stats-info-button"
              >
                <InfoOutlinedIcon sx={{ fontSize: 14 }} />
              </IconButton>
            )}
          </Box>
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            data-testid="gallery-options-header"
          >
            <Typography component="h2" variant="h6" fontWeight={600} data-testid="gallery-options-title">
              Options
            </Typography>
            <Tooltip title="Hide options" enterDelay={300} arrow>
              <IconButton
                aria-label="Close options"
                onClick={() => setOptionsOpen(false)}
                data-testid="gallery-options-close-button"
              >
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSearchSubmit}
            aria-label="gallery filters"
            data-testid="gallery-filter-form"
          >
            <TextField
              label="Search"
              variant="outlined"
              fullWidth
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              inputProps={{ 'data-testid': 'gallery-search-input' }}
            />

            {/* Tag Filter Display */}
            {filters.tag && (
              <Box
                sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}
                data-testid="gallery-tag-filter"
              >
                <Typography variant="body2" color="text.secondary" data-testid="gallery-tag-filter-label">
                  Filtered by {Array.isArray(filters.tag) ? 'tags' : 'tag'}:
                </Typography>
                {Array.isArray(filters.tag) ? (
                  // Multiple tags
                  filters.tag.map((tag, index) => (
                    <Chip
                      key={tag}
                      label={tag}
                      variant="outlined"
                      color="primary"
                      onDelete={() => {
                        const remainingTags = filters.tag.filter(t => t !== tag);
                        if (remainingTags.length === 0) {
                          // Remove all tags if this was the last one
                          setFilters(prev => ({ ...prev, tag: undefined, page: 0 }));
                          setSearchParams(params => {
                            const newParams = new URLSearchParams(params);
                            newParams.delete('tag');
                            return newParams;
                          });
                        } else {
                          // Update with remaining tags
                          setFilters(prev => ({ ...prev, tag: remainingTags.length === 1 ? remainingTags[0] : remainingTags, page: 0 }));
                          setSearchParams(params => {
                            const newParams = new URLSearchParams(params);
                            newParams.delete('tag');
                            remainingTags.forEach(t => newParams.append('tag', t));
                            return newParams;
                          });
                        }
                      }}
                      sx={{ maxWidth: 200 }}
                      data-testid={`gallery-tag-chip-${index}`}
                    />
                  ))
                ) : (
                  // Single tag
                  <Chip
                    label={filters.tag}
                    variant="outlined"
                    color="primary"
                    onDelete={() => {
                      setFilters(prev => ({ ...prev, tag: undefined, page: 0 }));
                      setSearchParams(params => {
                        const newParams = new URLSearchParams(params);
                        newParams.delete('tag');
                        return newParams;
                      });
                    }}
                    sx={{ maxWidth: 200 }}
                    data-testid="gallery-tag-chip-single"
                  />
                )}
                {/* Clear All Tags Button */}
                {filters.tag && (
                  <Button
                    variant="outlined"
                    size="small"
                    color="secondary"
                    onClick={() => {
                      setFilters(prev => ({ ...prev, tag: undefined, page: 0 }));
                      setSearchParams(params => {
                        const newParams = new URLSearchParams(params);
                        newParams.delete('tag');
                        return newParams;
                      });
                    }}
                    sx={{ ml: 1 }}
                    data-testid="gallery-clear-tags-button"
                  >
                    Clear All Tags
                  </Button>
                )}
              </Box>
            )}

            <FormControl fullWidth>
              <InputLabel id="gallery-sort-label">Sort by</InputLabel>
              <Select
                labelId="gallery-sort-label"
                label="Sort by"
                value={filters.sort}
                onChange={handleSortChange}
                data-testid="gallery-sort-select"
              >
                {sortOptions.map((option) => (
                  <MenuItem
                    key={option.value}
                    value={option.value}
                    data-testid={`gallery-sort-option-${option.value}`}
                  >
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          <Stack spacing={2} data-testid="gallery-content-toggles">
            <Typography variant="h6" component="h2" data-testid="gallery-content-toggles-title">
              Content Types
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="gallery-content-toggles-description">
              Choose which types of content to include in your gallery view.
            </Typography>
            <Stack spacing={1} data-testid="gallery-content-toggles-switches">
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.yourGens}
                    onChange={handleToggleChange('yourGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-your-gens' }}
                  />
                }
                label="Your gens"
                data-testid="gallery-toggle-your-gens-label"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.yourAutoGens}
                    onChange={handleToggleChange('yourAutoGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-your-autogens' }}
                  />
                }
                label="Your auto-gens"
                data-testid="gallery-toggle-your-autogens-label"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.communityGens}
                    onChange={handleToggleChange('communityGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-community-gens' }}
                  />
                }
                label="Community gens"
                data-testid="gallery-toggle-community-gens-label"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.communityAutoGens}
                    onChange={handleToggleChange('communityAutoGens')}
                    inputProps={{ 'data-testid': 'gallery-toggle-community-autogens' }}
                  />
                }
                label="Community auto-gens"
                data-testid="gallery-toggle-community-autogens-label"
              />
            </Stack>
          </Stack>
        </Stack>
      </Drawer>

      {/* Stats Popover */}
      <Popover
        open={Boolean(statsAnchorEl)}
        anchorEl={statsAnchorEl}
        onClose={() => setStatsAnchorEl(null)}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
        disableRestoreFocus
        sx={{
          pointerEvents: 'none',
        }}
        slotProps={{
          paper: {
            sx: {
              p: 1.5,
              pointerEvents: 'auto',
            },
          },
        }}
        onMouseEnter={() => setStatsAnchorEl(statsAnchorEl)}
        onMouseLeave={() => setStatsAnchorEl(null)}
        data-testid="gallery-stats-popover"
      >
        {data?.stats && (
          <Stack spacing={1} data-testid="gallery-stats-list">
             {/*<Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
               Content Statistics
             </Typography>*/}
            <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-user-regular">
              Your gens: {data.stats.userRegularCount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-user-auto">
              Your auto-gens: {data.stats.userAutoCount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-community-regular">
              Community gens: {data.stats.communityRegularCount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="gallery-stats-community-auto">
              Community auto-gens: {data.stats.communityAutoCount.toLocaleString()}
            </Typography>
          </Stack>
        )}
      </Popover>
    </Box>
  )
}
