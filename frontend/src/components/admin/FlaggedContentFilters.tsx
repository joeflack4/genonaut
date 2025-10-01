import {
  Box,
  Button,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Stack,
  Switch,
  Typography,
} from '@mui/material'
import type { SelectChangeEvent } from '@mui/material/Select'
import type { FlaggedContentFilters } from '../../types/domain'

interface FlaggedContentFiltersProps {
  filters: FlaggedContentFilters
  onFiltersChange: (filters: FlaggedContentFilters) => void
  onClearFilters: () => void
}

export function FlaggedContentFilters({
  filters,
  onFiltersChange,
  onClearFilters,
}: FlaggedContentFiltersProps) {
  const handleSourceChange = (event: SelectChangeEvent<string>) => {
    onFiltersChange({
      ...filters,
      contentSource: event.target.value as 'regular' | 'auto' | 'all',
      page: 1,
    })
  }

  const handleReviewedChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      reviewed: event.target.checked ? false : undefined,
      page: 1,
    })
  }

  const handleRiskScoreChange = (_event: Event, value: number | number[]) => {
    const [min, max] = value as number[]
    onFiltersChange({
      ...filters,
      minRiskScore: min,
      maxRiskScore: max,
      page: 1,
    })
  }

  const handleSortFieldChange = (event: SelectChangeEvent<string>) => {
    onFiltersChange({
      ...filters,
      sortField: event.target.value,
      page: 1,
    })
  }

  const handleSortOrderChange = (event: SelectChangeEvent<string>) => {
    onFiltersChange({
      ...filters,
      sortOrder: event.target.value as 'asc' | 'desc',
      page: 1,
    })
  }

  const hasActiveFilters =
    filters.contentSource !== 'all' ||
    filters.reviewed !== undefined ||
    filters.minRiskScore !== 0 ||
    filters.maxRiskScore !== 100 ||
    filters.sortField !== 'risk_score' ||
    filters.sortOrder !== 'desc'

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Stack spacing={2}>
          <FormControl fullWidth size="small">
            <InputLabel id="content-source-label">Content Source</InputLabel>
            <Select
              labelId="content-source-label"
              label="Content Source"
              value={filters.contentSource ?? 'all'}
              onChange={handleSourceChange}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="regular">Regular</MenuItem>
              <MenuItem value="auto">Auto-Generated</MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={filters.reviewed === false}
                onChange={handleReviewedChange}
              />
            }
            label="Unreviewed only"
          />

          <Box>
            <Typography variant="body2" gutterBottom>
              Risk Score Range
            </Typography>
            <Slider
              value={[
                filters.minRiskScore ?? 0,
                filters.maxRiskScore ?? 100,
              ]}
              onChange={handleRiskScoreChange}
              valueLabelDisplay="auto"
              min={0}
              max={100}
              marks={[
                { value: 0, label: '0' },
                { value: 25, label: '25' },
                { value: 50, label: '50' },
                { value: 75, label: '75' },
                { value: 100, label: '100' },
              ]}
            />
          </Box>
        </Stack>
      </Box>

      <Box>
        <Typography variant="h6" gutterBottom>
          Sort
        </Typography>
        <Stack spacing={2}>
          <FormControl fullWidth size="small">
            <InputLabel id="sort-field-label">Sort By</InputLabel>
            <Select
              labelId="sort-field-label"
              label="Sort By"
              value={filters.sortField ?? 'risk_score'}
              onChange={handleSortFieldChange}
            >
              <MenuItem value="risk_score">Risk Score</MenuItem>
              <MenuItem value="flagged_at">Flagged Date</MenuItem>
              <MenuItem value="total_problem_words">Problem Count</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth size="small">
            <InputLabel id="sort-order-label">Order</InputLabel>
            <Select
              labelId="sort-order-label"
              label="Order"
              value={filters.sortOrder ?? 'desc'}
              onChange={handleSortOrderChange}
            >
              <MenuItem value="desc">Descending</MenuItem>
              <MenuItem value="asc">Ascending</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Box>

      {hasActiveFilters && (
        <Button variant="outlined" color="secondary" onClick={onClearFilters} fullWidth>
          Clear All Filters
        </Button>
      )}
    </Stack>
  )
}
