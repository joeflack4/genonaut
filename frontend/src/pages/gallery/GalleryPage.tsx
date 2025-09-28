import { useMemo, useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
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
  tag?: string  // Tag filter from URL
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
    const tag = searchParams.get('tag') || undefined
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

  // Save optionsOpen state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(GALLERY_OPTIONS_OPEN_KEY, JSON.stringify(optionsOpen))
    } catch {
      // Ignore localStorage errors
    }
  }, [optionsOpen])

  // Sync URL parameters with filters state
  useEffect(() => {
    const tag = searchParams.get('tag')
    if (tag !== filters.tag) {
      setFilters(prev => ({ ...prev, tag: tag || undefined, page: 0 }))
    }
  }, [searchParams, filters.tag])

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
    <Box component="section" sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
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
      >
        <Stack spacing={4}>
          <Stack spacing={1}>
            <Typography component="h1" variant="h4" fontWeight={600} gutterBottom>
              Gallery
            </Typography>
          </Stack>
          <Card>
            <CardContent>
              {isLoading ? (
                <Stack spacing={2}>
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Skeleton key={index} variant="rectangular" height={72} />
                  ))}
                </Stack>
              ) : data && data.items.length > 0 ? (
                <List>
                  {data.items.map((item) => (
                    <ListItem key={item.id} alignItems="flex-start" divider>
                      <ListItemText
                        primary={
                          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
                            <Typography variant="h6" component="span">
                              {item.title}
                            </Typography>
                            {item.qualityScore !== null && item.qualityScore !== undefined && (
                              <Chip
                                label={`Quality ${(item.qualityScore * 100).toFixed(0)}%`}
                                color={item.qualityScore > 0.75 ? 'success' : 'default'}
                              />
                            )}
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

          <Box display="flex" justifyContent="flex-end">
            <Pagination
              count={totalPages}
              page={filters.page + 1}
              onChange={handlePageChange}
              color="primary"
              shape="rounded"
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
      >
        <Stack spacing={3} sx={{ height: '100%' }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', display: 'inline' }}>
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
              >
                <InfoOutlinedIcon sx={{ fontSize: 14 }} />
              </IconButton>
            )}
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography component="h2" variant="h6" fontWeight={600}>
              Options
            </Typography>
            <Tooltip title="Hide options" enterDelay={300} arrow>
              <IconButton aria-label="Close options" onClick={() => setOptionsOpen(false)}>
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSearchSubmit}
            aria-label="gallery filters"
          >
            <TextField
              label="Search"
              variant="outlined"
              fullWidth
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />

            {/* Tag Filter Display */}
            {filters.tag && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Filtered by tag:
                </Typography>
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
                />
              </Box>
            )}

            <FormControl fullWidth>
              <InputLabel id="gallery-sort-label">Sort by</InputLabel>
              <Select
                labelId="gallery-sort-label"
                label="Sort by"
                value={filters.sort}
                onChange={handleSortChange}
              >
                {sortOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          <Stack spacing={2}>
            <Typography variant="h6" component="h2">
              Content Types
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Choose which types of content to include in your gallery view.
            </Typography>
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.yourGens}
                    onChange={handleToggleChange('yourGens')}
                  />
                }
                label="Your gens"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.yourAutoGens}
                    onChange={handleToggleChange('yourAutoGens')}
                  />
                }
                label="Your auto-gens"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.communityGens}
                    onChange={handleToggleChange('communityGens')}
                  />
                }
                label="Community gens"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={contentToggles.communityAutoGens}
                    onChange={handleToggleChange('communityAutoGens')}
                  />
                }
                label="Community auto-gens"
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
      >
        {data?.stats && (
          <Stack spacing={1}>
             {/*<Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
               Content Statistics
             </Typography>*/}
            <Typography variant="body2" color="text.secondary">
              Your gens: {data.stats.userRegularCount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your auto-gens: {data.stats.userAutoCount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Community gens: {data.stats.communityRegularCount.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Community auto-gens: {data.stats.communityAutoCount.toLocaleString()}
            </Typography>
          </Stack>
        )}
      </Popover>
    </Box>
  )
}
