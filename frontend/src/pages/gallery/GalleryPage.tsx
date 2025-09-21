import { useMemo, useState } from 'react'
import type { SelectChangeEvent } from '@mui/material/Select'
import {
  Box,
  Card,
  CardContent,
  Chip,
  Drawer,
  FormControl,
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
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import { useGalleryList } from '../../hooks'

const PAGE_SIZE = 10
const PANEL_WIDTH = 360

type SortOption = 'recent' | 'top-rated'

interface FiltersState {
  search: string
  sort: SortOption
  page: number
}

const sortOptions: Array<{ value: SortOption; label: string }> = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'top-rated', label: 'Top Rated' },
]

export function GalleryPage() {
  const [searchInput, setSearchInput] = useState('')
  const [filters, setFilters] = useState<FiltersState>({ search: '', sort: 'recent', page: 0 })
  const [optionsOpen, setOptionsOpen] = useState(true)

  const queryParams = useMemo(
    () => ({
      limit: PAGE_SIZE,
      skip: filters.page * PAGE_SIZE,
      search: filters.search,
      sort: filters.sort,
    }),
    [filters]
  )

  const { data, isLoading } = useGalleryList(queryParams)

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

  return (
    <Box component="section" sx={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
      {!optionsOpen && (
        <Tooltip title="Options" enterDelay={300} arrow>
          <IconButton
            aria-label="Options"
            onClick={() => setOptionsOpen(true)}
            sx={{
              position: 'fixed',
              top: (theme) => theme.spacing(2),
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
          transition: (theme) =>
            theme.transitions.create('margin-right', {
              duration: theme.transitions.duration.enteringScreen,
            }),
          mr: { md: optionsOpen ? `${PANEL_WIDTH}px` : 0 },
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
        ModalProps={{ keepMounted: true }}
        onClose={() => setOptionsOpen(false)}
        sx={{
          width: PANEL_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: PANEL_WIDTH },
            boxSizing: 'border-box',
            p: 3,
            gap: 3,
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
          <Typography variant="body2" color="text.secondary">
            Browse the community gallery, refine with filters, and explore the latest additions.
          </Typography>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSearchSubmit}
            aria-label="gallery filters"
          >
            <TextField
              label="Search gallery"
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
        </Stack>
      </Drawer>
    </Box>
  )
}
