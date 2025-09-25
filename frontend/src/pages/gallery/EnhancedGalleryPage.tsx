import { useMemo, useState, useEffect } from 'react'
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
  ListItemText,
  MenuItem,
  Pagination,
  Select,
  Skeleton,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
  Alert,
  LinearProgress,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import CachedIcon from '@mui/icons-material/Cached'
import SpeedIcon from '@mui/icons-material/Speed'
import { useEnhancedGalleryList, useCurrentUser } from '../../hooks'
import { ADMIN_USER_ID } from '../../constants/config'

const DEFAULT_PAGE_SIZE = 20 // Increased from 10 for better performance
const PANEL_WIDTH = 360
const DEFAULT_USER_ID = ADMIN_USER_ID
const GALLERY_OPTIONS_OPEN_KEY = 'enhanced-gallery-options-open'

type SortOption = 'created_at' | 'quality_score'
type SortOrder = 'asc' | 'desc'

interface FiltersState {
  search: string
  sortField: SortOption
  sortOrder: SortOrder
  contentType?: string
  publicOnly?: boolean
}

interface ContentToggles {
  showYourContent: boolean
  showPublicContent: boolean
  showPrivateContent: boolean
}

const sortOptions: Array<{ value: SortOption; label: string }> = [
  { value: 'created_at', label: 'Creation Date' },
  { value: 'quality_score', label: 'Quality Score' },
]

const contentTypeOptions: Array<{ value: string; label: string }> = [
  { value: 'text', label: 'Text' },
  { value: 'image', label: 'Image' },
  { value: 'video', label: 'Video' },
  { value: 'audio', label: 'Audio' },
]

export function EnhancedGalleryPage() {
  const [searchInput, setSearchInput] = useState('')
  const [filters, setFilters] = useState<FiltersState>({
    search: '',
    sortField: 'created_at',
    sortOrder: 'desc'
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

  const [contentToggles, setContentToggles] = useState<ContentToggles>({
    showYourContent: true,
    showPublicContent: true,
    showPrivateContent: false,
  })

  const { data: currentUser } = useCurrentUser()
  const userId = currentUser?.id ?? DEFAULT_USER_ID

  // Save optionsOpen state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(GALLERY_OPTIONS_OPEN_KEY, JSON.stringify(optionsOpen))
    } catch {
      // Ignore localStorage errors
    }
  }, [optionsOpen])

  // Build query parameters for the enhanced pagination API
  const queryParams = useMemo(() => {
    const params: any = {
      sortField: filters.sortField,
      sortOrder: filters.sortOrder,
      pageSize: DEFAULT_PAGE_SIZE,
    }

    if (filters.search) {
      params.searchTerm = filters.search
    }

    if (filters.contentType) {
      params.contentType = filters.contentType
    }

    // Determine content filtering based on toggles
    if (contentToggles.showYourContent && !contentToggles.showPublicContent) {
      // Only your content
      params.creatorId = userId
    } else if (!contentToggles.showYourContent && contentToggles.showPublicContent) {
      // Only public content (from others)
      params.publicOnly = true
      // Note: We'll need to filter out user's content in a more sophisticated way
    } else if (contentToggles.showPublicContent && !contentToggles.showPrivateContent) {
      // Only public content (including user's own public content)
      params.publicOnly = true
    } else if (!contentToggles.showPrivateContent) {
      // Public content only, but allow all users
      params.publicOnly = true
    }

    return params
  }, [filters, contentToggles, userId])

  // Use the enhanced gallery hook with pre-fetching and caching
  const {
    items,
    pagination,
    isLoading,
    isError,
    error,
    isFetching,
    currentPage,
    pageSize,
    goToPage,
    goToNextPage,
    goToPreviousPage,
    goToFirstPage,
    goToLastPage,
    canGoNext,
    canGoPrevious,
    pageNumbers: _pageNumbers,
    prefetchStatus,
    invalidate,
  } = useEnhancedGalleryList({
    filters: queryParams,
    initialPageSize: DEFAULT_PAGE_SIZE,
    enablePrefetch: true,
    prefetchPages: 2, // Prefetch 2 pages ahead
    prefetchDelay: 300, // Prefetch after 300ms
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFilters((prev) => ({ ...prev, search: searchInput.trim() }))
    goToFirstPage() // Reset to first page on search
  }

  const handleSortFieldChange = (event: SelectChangeEvent<SortOption>) => {
    setFilters((prev) => ({ ...prev, sortField: event.target.value as SortOption }))
    goToFirstPage()
  }

  const handleSortOrderChange = (event: SelectChangeEvent<SortOrder>) => {
    setFilters((prev) => ({ ...prev, sortOrder: event.target.value as SortOrder }))
    goToFirstPage()
  }

  const handleContentTypeChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value === 'all' ? undefined : event.target.value
    setFilters((prev) => ({ ...prev, contentType: value }))
    goToFirstPage()
  }

  const handleToggleChange = (toggleKey: keyof ContentToggles) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setContentToggles((prev) => ({
      ...prev,
      [toggleKey]: event.target.checked,
    }))
    goToFirstPage() // Reset to first page when toggling content types
  }

  const handleRefresh = () => {
    invalidate()
  }

  return (
    <Box component="section" sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
      {!optionsOpen && (
        <Tooltip title="Options" enterDelay={300} arrow>
          <IconButton
            aria-label="Options"
            onClick={() => setOptionsOpen(true)}
            sx={{
              position: 'fixed',
              top: (theme) => theme.spacing(10),
              right: (theme) => theme.spacing(2),
              zIndex: (theme) => theme.zIndex.drawer + 1,
              bgcolor: 'background.paper',
              boxShadow: 1,
            }}
          >
            <SettingsOutlinedIcon />
          </IconButton>
        </Tooltip>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <Stack spacing={4}>
          {/* Performance Indicators */}
          {(isFetching || prefetchStatus.isNextPagePrefetched) && (
            <Alert severity="info" sx={{ alignItems: 'center' }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                {isFetching && <LinearProgress sx={{ minWidth: 100, flexGrow: 1 }} />}
                <Typography variant="caption">
                  {isFetching && 'Loading...'}
                  {prefetchStatus.isNextPagePrefetched && (
                    <Stack direction="row" alignItems="center" spacing={0.5}>
                      <CachedIcon fontSize="small" />
                      <span>Next page cached</span>
                    </Stack>
                  )}
                </Typography>
              </Stack>
            </Alert>
          )}

          {/* Error State */}
          {isError && error && (
            <Alert severity="error" action={
              <IconButton size="small" onClick={handleRefresh}>
                <CachedIcon />
              </IconButton>
            }>
              Failed to load gallery: {error.message}
            </Alert>
          )}

          {/* Pagination Info */}
          {pagination && (
            <Card variant="outlined">
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" color="text.secondary">
                    Page {pagination.page} of {pagination.totalPages} • {pagination.totalCount} total items
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <SpeedIcon fontSize="small" color="primary" />
                    <Typography variant="caption" color="primary">
                      Enhanced with pre-fetching
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Content List */}
          <Card>
            <CardContent>
              {isLoading ? (
                <Stack spacing={2}>
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton key={index} variant="rectangular" height={72} />
                  ))}
                </Stack>
              ) : items && items.length > 0 ? (
                <List>
                  {items.map((item) => (
                    <ListItem key={item.id} alignItems="flex-start" divider>
                      <ListItemText
                        primary={
                          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
                            <Typography variant="h6" component="span">
                              {item.title}
                            </Typography>
                            <Stack direction="row" spacing={1}>
                              {item.qualityScore !== null && item.qualityScore !== undefined && (
                                <Chip
                                  label={`Quality ${(item.qualityScore * 100).toFixed(0)}%`}
                                  color={item.qualityScore > 0.75 ? 'success' : 'default'}
                                  size="small"
                                />
                              )}
                              {item.creatorId === userId && (
                                <Chip label="Your Content" size="small" color="primary" />
                              )}
                            </Stack>
                          </Stack>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mt: 1 }}>
                            {item.description && (
                              <Typography variant="body2" color="text.secondary" component="span">
                                {item.description}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary" component="span">
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
                <Typography variant="body2" color="text.secondary">
                  No gallery items found. Try adjusting your filters.
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Enhanced Pagination */}
          {pagination && pagination.totalPages > 1 && (
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Stack direction="row" spacing={1}>
                <Tooltip title="First Page">
                  <span>
                    <IconButton onClick={goToFirstPage} disabled={!canGoPrevious} size="small">
                      ⏮
                    </IconButton>
                  </span>
                </Tooltip>
                <Tooltip title="Previous Page">
                  <span>
                    <IconButton onClick={goToPreviousPage} disabled={!canGoPrevious} size="small">
                      ⏸
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>

              <Pagination
                count={pagination.totalPages}
                page={currentPage}
                onChange={(_, page) => goToPage(page)}
                color="primary"
                shape="rounded"
                showFirstButton
                showLastButton
              />

              <Stack direction="row" spacing={1}>
                <Tooltip title="Next Page">
                  <span>
                    <IconButton onClick={goToNextPage} disabled={!canGoNext} size="small">
                      ⏯
                    </IconButton>
                  </span>
                </Tooltip>
                <Tooltip title="Last Page">
                  <span>
                    <IconButton onClick={() => goToLastPage()} disabled={!canGoNext} size="small">
                      ⏭
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>
            </Box>
          )}
        </Stack>
      </Box>

      {/* Enhanced Options Drawer */}
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
      >
        <Stack spacing={3} sx={{ height: '100%' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography component="h1" variant="h5" fontWeight={600}>
              Enhanced Gallery
            </Typography>
            <Tooltip title="Hide options" enterDelay={300} arrow>
              <IconButton aria-label="Close options" onClick={() => setOptionsOpen(false)}>
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Search and Sorting */}
          <Stack component="form" spacing={2} onSubmit={handleSearchSubmit} aria-label="gallery filters">
            <TextField
              label="Search"
              variant="outlined"
              fullWidth
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search by title or description..."
            />

            <FormControl fullWidth>
              <InputLabel id="gallery-sort-field-label">Sort by</InputLabel>
              <Select
                labelId="gallery-sort-field-label"
                label="Sort by"
                value={filters.sortField}
                onChange={handleSortFieldChange}
              >
                {sortOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="gallery-sort-order-label">Sort order</InputLabel>
              <Select
                labelId="gallery-sort-order-label"
                label="Sort order"
                value={filters.sortOrder}
                onChange={handleSortOrderChange}
              >
                <MenuItem value="desc">Descending</MenuItem>
                <MenuItem value="asc">Ascending</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="content-type-label">Content Type</InputLabel>
              <Select
                labelId="content-type-label"
                label="Content Type"
                value={filters.contentType || 'all'}
                onChange={handleContentTypeChange}
              >
                <MenuItem value="all">All Types</MenuItem>
                {contentTypeOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          {/* Content Filters */}
          <Stack spacing={2}>
            <Typography variant="h6" component="h2">
              Content Filters
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Choose which content to display. Enhanced pagination automatically handles filtering server-side.
            </Typography>
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.showYourContent}
                    onChange={handleToggleChange('showYourContent')}
                  />
                }
                label="Your content"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.showPublicContent}
                    onChange={handleToggleChange('showPublicContent')}
                  />
                }
                label="Public content"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.showPrivateContent}
                    onChange={handleToggleChange('showPrivateContent')}
                  />
                }
                label="Private content"
              />
            </Stack>
          </Stack>

          {/* Performance Info */}
          <Stack spacing={1}>
            <Typography variant="h6" component="h2">
              Performance
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Enhanced pagination with server-side filtering and automatic pre-fetching.
            </Typography>
            <Stack spacing={0.5}>
              <Typography variant="caption">
                Page Size: {pageSize} items
              </Typography>
              {pagination && (
                <>
                  <Typography variant="caption">
                    Total: {pagination.totalCount} items across {pagination.totalPages} pages
                  </Typography>
                  <Typography variant="caption" color="primary">
                    {prefetchStatus.isNextPagePrefetched ? '✓ Next page cached' : '◦ Next page loading...'}
                  </Typography>
                  <Typography variant="caption" color="secondary">
                    {prefetchStatus.isPreviousPagePrefetched ? '✓ Previous page cached' : '◦ Previous page available'}
                  </Typography>
                </>
              )}
            </Stack>
          </Stack>
        </Stack>
      </Drawer>
    </Box>
  )
}