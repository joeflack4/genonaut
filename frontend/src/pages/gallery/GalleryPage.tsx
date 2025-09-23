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
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import { useGalleryList, useGalleryAutoList, useCurrentUser } from '../../hooks'
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
}

interface ContentToggles {
  yourWorks: boolean
  yourAutoGens: boolean
  communityWorks: boolean
  communityAutoGens: boolean
}

const sortOptions: Array<{ value: SortOption; label: string }> = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'top-rated', label: 'Top Rated' },
]

export function GalleryPage() {
  const [searchInput, setSearchInput] = useState('')
  const [filters, setFilters] = useState<FiltersState>({ search: '', sort: 'recent', page: 0 })

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
    yourWorks: true,
    yourAutoGens: true,
    communityWorks: true,
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

  const queryParams = useMemo(
    () => ({
      limit: PAGE_SIZE * 2, // Get more items to account for filtering
      skip: 0, // We'll handle pagination after combining results
      search: filters.search,
      sort: filters.sort,
    }),
    [filters.search, filters.sort]
  )

  // Fetch data from different sources based on toggles
  const { data: yourWorksData, isLoading: yourWorksLoading } = useGalleryList({
    ...queryParams,
    creator_id: userId,
  })

  const { data: yourAutoGensData, isLoading: yourAutoGensLoading } = useGalleryAutoList({
    ...queryParams,
    creator_id: userId,
  })

  const { data: allWorksData, isLoading: allWorksLoading } = useGalleryList(queryParams)

  const { data: allAutoGensData, isLoading: allAutoGensLoading } = useGalleryAutoList(queryParams)

  // Combine and filter data based on toggles
  const combinedData = useMemo(() => {
    const items = []

    // Add your works if toggle is on
    if (contentToggles.yourWorks && yourWorksData?.items) {
      items.push(...yourWorksData.items)
    }

    // Add your auto-gens if toggle is on
    if (contentToggles.yourAutoGens && yourAutoGensData?.items) {
      items.push(...yourAutoGensData.items)
    }

    // Add community works if toggle is on (exclude user's own content)
    if (contentToggles.communityWorks && allWorksData?.items) {
      const communityWorks = allWorksData.items.filter(item => item.creatorId !== userId)
      items.push(...communityWorks)
    }

    // Add community auto-gens if toggle is on (exclude user's own content)
    if (contentToggles.communityAutoGens && allAutoGensData?.items) {
      const communityAutoGens = allAutoGensData.items.filter(item => item.creatorId !== userId)
      items.push(...communityAutoGens)
    }

    // Remove duplicates and sort
    const uniqueItems = items.filter((item, index, self) =>
      index === self.findIndex(i => i.id === item.id)
    )

    // Sort based on selected sort option
    uniqueItems.sort((a, b) => {
      if (filters.sort === 'recent') {
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      } else {
        // Top-rated sorting
        return (b.qualityScore ?? 0) - (a.qualityScore ?? 0)
      }
    })

    // Handle pagination
    const startIndex = filters.page * PAGE_SIZE
    const endIndex = startIndex + PAGE_SIZE
    const paginatedItems = uniqueItems.slice(startIndex, endIndex)

    return {
      items: paginatedItems,
      total: uniqueItems.length,
      limit: PAGE_SIZE,
      skip: startIndex,
    }
  }, [
    contentToggles,
    yourWorksData,
    yourAutoGensData,
    allWorksData,
    allAutoGensData,
    userId,
    filters.sort,
    filters.page,
  ])

  const isLoading = yourWorksLoading || yourAutoGensLoading || allWorksLoading || allAutoGensLoading
  const data = combinedData

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
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography component="h1" variant="h5" fontWeight={600}>
              Gallery
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
                    checked={contentToggles.yourWorks}
                    onChange={handleToggleChange('yourWorks')}
                  />
                }
                label="Your works"
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
                    checked={contentToggles.communityWorks}
                    onChange={handleToggleChange('communityWorks')}
                  />
                }
                label="Community works"
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
    </Box>
  )
}
