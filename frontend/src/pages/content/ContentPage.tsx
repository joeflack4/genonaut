import { useMemo, useState } from 'react'
import type { SelectChangeEvent } from '@mui/material/Select'
import {
  Box,
  Card,
  CardContent,
  Chip,
  FormControl,
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
  Typography,
} from '@mui/material'
import { useContentList } from '../../hooks'

const PAGE_SIZE = 10

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

export function ContentPage() {
  const [searchInput, setSearchInput] = useState('')
  const [filters, setFilters] = useState<FiltersState>({ search: '', sort: 'recent', page: 0 })

  const queryParams = useMemo(
    () => ({
      limit: PAGE_SIZE,
      skip: filters.page * PAGE_SIZE,
      search: filters.search,
      sort: filters.sort,
    }),
    [filters]
  )

  const { data, isLoading } = useContentList(queryParams)

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
    <Stack spacing={4} component="section">
      <Stack spacing={1}>
        <Typography component="h1" variant="h4" fontWeight={600} gutterBottom>
          Content Library
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Browse generated content, refine with filters, and explore the latest additions.
        </Typography>
      </Stack>

      <Card>
        <CardContent>
          <Stack
            component="form"
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            alignItems={{ md: 'center' }}
            onSubmit={handleSearchSubmit}
            aria-label="content filters"
          >
            <TextField
              label="Search content"
              variant="outlined"
              fullWidth
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
            <FormControl sx={{ minWidth: 180 }}>
              <InputLabel id="content-sort-label">Sort by</InputLabel>
              <Select
                labelId="content-sort-label"
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
        </CardContent>
      </Card>

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
              No content found. Try adjusting your filters.
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
  )
}
