import { useMemo, useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import type { SelectChangeEvent } from '@mui/material/Select'
import {
  Box,
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
  ListItemButton,
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
import ViewListIcon from '@mui/icons-material/ViewList'
import GridViewIcon from '@mui/icons-material/GridView'
import { useUnifiedGallery, useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'
import type { GalleryItem, ThumbnailResolutionId, ViewMode } from '../../types/domain'
import {
  DEFAULT_GRID_VIEW_MODE,
  DEFAULT_THUMBNAIL_RESOLUTION,
  DEFAULT_THUMBNAIL_RESOLUTION_ID,
  DEFAULT_VIEW_MODE,
  GALLERY_VIEW_MODE_STORAGE_KEY,
  THUMBNAIL_RESOLUTION_OPTIONS,
} from '../../constants/gallery'
import { loadViewMode, persistViewMode } from '../../utils/viewModeStorage'
import { GridView as GalleryGridView, ResolutionDropdown } from '../../components/gallery'
import { TagFilter } from '../../components/gallery/TagFilter'

const PAGE_SIZE = 25
const PANEL_WIDTH = 360
const DEFAULT_USER_ID = ADMIN_USER_ID
const GALLERY_OPTIONS_OPEN_KEY = 'gallery-options-open'

type SortOption = 'recent' | 'top-rated'

interface FiltersState {
  search: string
  sort: SortOption
  page: number
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

function arraysEqualIgnoreOrder(a: string[], b: string[]): boolean {
  if (a.length !== b.length) {
    return false
  }
  const sortedA = [...a].sort()
  const sortedB = [...b].sort()
  return sortedA.every((value, index) => value === sortedB[index])
}

export function GalleryPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchInput, setSearchInput] = useState('')

  // Initialize filters from URL parameters
  const [filters, setFilters] = useState<FiltersState>(() => {
    return {
      search: '',
      sort: 'recent' as SortOption,
      page: 0,
    }
  })

  const [selectedTags, setSelectedTags] = useState<string[]>(() => searchParams.getAll('tag'))

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

  const [viewMode, setViewMode] = useState<ViewMode>(() =>
    loadViewMode(GALLERY_VIEW_MODE_STORAGE_KEY, DEFAULT_VIEW_MODE)
  )

  const navigate = useNavigate()

  const isGridView = viewMode.startsWith('grid-')

  const currentGridResolutionId = useMemo<ThumbnailResolutionId>(() => {
    if (isGridView) {
      const resolutionId = viewMode.slice(5) as ThumbnailResolutionId
      const exists = THUMBNAIL_RESOLUTION_OPTIONS.some((option) => option.id === resolutionId)
      if (exists) {
        return resolutionId
      }
    }
    return DEFAULT_THUMBNAIL_RESOLUTION_ID
  }, [isGridView, viewMode])

  const currentResolution = useMemo(
    () =>
      THUMBNAIL_RESOLUTION_OPTIONS.find((option) => option.id === currentGridResolutionId)
      ?? DEFAULT_THUMBNAIL_RESOLUTION,
    [currentGridResolutionId]
  )

  const updateViewMode = (mode: ViewMode) => {
    setViewMode(mode)
    persistViewMode(GALLERY_VIEW_MODE_STORAGE_KEY, mode)
  }

  const handleSelectListView = () => {
    updateViewMode('list')
  }

  const handleSelectGridView = () => {
    const nextMode = isGridView ? viewMode : DEFAULT_GRID_VIEW_MODE
    updateViewMode(nextMode)
  }

  const handleResolutionChange = (resolutionId: ThumbnailResolutionId) => {
    const nextMode: ViewMode = `grid-${resolutionId}`
    updateViewMode(nextMode)
  }

  const navigateToDetail = (item: GalleryItem) => {
    navigate(`/view/${item.id}`, {
      state: {
        sourceType: item.sourceType,
        from: 'gallery',
        fallbackPath: '/gallery',
      },
    })
  }

  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  // Sync Selected tags with URL parameters (supports navigation/back links)
  useEffect(() => {
    const tagsFromParams = searchParams.getAll('tag')
    if (!arraysEqualIgnoreOrder(tagsFromParams, selectedTags)) {
      setSelectedTags(tagsFromParams)
      setFilters((prev) => ({ ...prev, page: 0 }))
    }
  }, [searchParams, selectedTags])

  // Save optionsOpen state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(GALLERY_OPTIONS_OPEN_KEY, JSON.stringify(optionsOpen))
    } catch {
      // Ignore localStorage errors
    }
  }, [optionsOpen])


  // NEW: Build content source types array directly from toggles
  const contentSourceTypes = useMemo(() => {
    const types: string[] = []
    if (contentToggles.yourGens) types.push('user-regular')
    if (contentToggles.yourAutoGens) types.push('user-auto')
    if (contentToggles.communityGens) types.push('community-regular')
    if (contentToggles.communityAutoGens) types.push('community-auto')
    return types
  }, [contentToggles])

  // Use unified gallery API with new content source types
  const tagFilterParam = selectedTags.length === 0 ? undefined : selectedTags

  const { data: unifiedData, isLoading } = useUnifiedGallery({
    page: filters.page + 1, // Convert from 0-based to 1-based
    pageSize: PAGE_SIZE,
    contentSourceTypes,  // NEW: Use specific combinations instead of contentTypes + creatorFilter
    userId,
    searchTerm: filters.search || undefined,
    sortField: filters.sort === 'recent' ? 'created_at' : 'quality_score',
    sortOrder: 'desc',
    tag: tagFilterParam,
  })

  const data = unifiedData
  const items = data?.items ?? []

  // Track if critical data has loaded for E2E tests
  const isAppReady = !isLoading && data !== undefined

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

  const handleTagFilterChange = (tags: string[]) => {
    setSelectedTags(tags)
    setFilters((prev) => ({ ...prev, page: 0 }))
    setSearchParams((params) => {
      const newParams = new URLSearchParams(params)
      newParams.delete('tag')
      tags.forEach((tagId) => newParams.append('tag', tagId))
      return newParams
    })
  }

  const handleTagClick = (tagId: string) => {
    navigate(`/tags/${tagId}`)
  }

  return (
    <Box
      component="section"
      sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}
      data-testid="gallery-page-root"
      data-app-ready={isAppReady ? '1' : '0'}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
        }}
        data-testid="gallery-content-wrapper"
      >
        <Stack spacing={4} data-testid="gallery-content-stack">
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', sm: 'center' }}
            spacing={2}
            data-testid="gallery-header"
          >
            <Box data-testid="gallery-header-title">
              <Typography
                component="h1"
                variant="h4"
                fontWeight={600}
                gutterBottom
                data-testid="gallery-title"
              >
                Gallery
              </Typography>
            </Box>
            <Stack direction="row" spacing={1} alignItems="center" data-testid="gallery-view-toggle-group">
              <Tooltip title="List view" enterDelay={300} arrow>
                <IconButton
                  aria-label="Switch to list view"
                  color={isGridView ? 'default' : 'primary'}
                  onClick={handleSelectListView}
                  data-testid="gallery-view-toggle-list"
                  aria-pressed={!isGridView}
                >
                  <ViewListIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Grid view" enterDelay={300} arrow>
                <IconButton
                  aria-label="Switch to grid view"
                  color={isGridView ? 'primary' : 'default'}
                  onClick={handleSelectGridView}
                  data-testid="gallery-view-toggle-grid"
                  aria-pressed={isGridView}
                >
                  <GridViewIcon />
                </IconButton>
              </Tooltip>
              {isGridView && (
                <ResolutionDropdown
                  currentResolution={currentGridResolutionId}
                  onResolutionChange={handleResolutionChange}
                  dataTestId="gallery-resolution-dropdown"
                />
              )}
              <Tooltip title={optionsOpen ? 'Hide options panel' : 'Show options panel'} enterDelay={300} arrow>
                <IconButton
                  aria-label={optionsOpen ? 'Hide options panel' : 'Show options panel'}
                  color={optionsOpen ? 'primary' : 'default'}
                  onClick={() => setOptionsOpen((prev) => !prev)}
                  data-testid="gallery-options-toggle-button"
                >
                  <SettingsOutlinedIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>
          <Card data-testid="gallery-results-card">
            <CardContent>
              {isGridView ? (
                <GalleryGridView
                  items={items}
                  resolution={currentResolution}
                  isLoading={isLoading}
                  onItemClick={navigateToDetail}
                  emptyMessage="No gallery items found. Try adjusting your filters."
                  dataTestId="gallery-grid-view"
                />
              ) : isLoading ? (
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
              ) : items.length > 0 ? (
                <List data-testid="gallery-results-list">
                  {items.map((item) => (
                    <ListItem
                      key={item.id}
                      disablePadding
                      alignItems="flex-start"
                      divider
                      data-testid={`gallery-result-item-${item.id}`}
                    >
                      <ListItemButton
                        onClick={() => navigateToDetail(item)}
                        data-testid={`gallery-result-item-${item.id}-button`}
                        alignItems="flex-start"
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
                      </ListItemButton>
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

          <Box display="flex" justifyContent="flex-start" data-testid="gallery-pagination">
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
        data-open={optionsOpen ? 'true' : 'false'}
      >
        <Stack spacing={3} sx={{ height: '100%', pb: 4 }} data-testid="gallery-options-stack">
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
          <Box sx={{ textAlign: 'center' }} data-testid="gallery-options-summary">
            {!isLoading && (
              <>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontStyle: 'italic', display: 'inline' }}
                  data-testid="gallery-options-summary-text"
                >
                  {(data?.total ?? 0) === 0
                    ? '0 results matching filters.'
                    : `${totalPages.toLocaleString()} pages showing ${data?.total?.toLocaleString() || 0} results matching filters.`}
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
              </>
            )}
          </Box>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSearchSubmit}
            aria-label="gallery filters"
            data-testid="gallery-filter-form"
          >
            <TextField
              label="Search (by prompt & title)"
              variant="outlined"
              fullWidth
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              inputProps={{ 'data-testid': 'gallery-search-input' }}
            />

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
              Filter by gen source
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

          <Stack spacing={2} data-testid="gallery-tag-filter-section">
            <Typography variant="h6" component="h2" data-testid="gallery-tag-filter-title">
              Filter by tags
            </Typography>
            <TagFilter
              selectedTags={selectedTags}
              onTagsChange={handleTagFilterChange}
              onTagClick={handleTagClick}
            />
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
