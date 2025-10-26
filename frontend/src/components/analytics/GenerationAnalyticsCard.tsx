/**
 * Generation Analytics Card Component
 *
 * Displays image generation system performance and usage patterns.
 * Features:
 * - Overview statistics (4 metric cards)
 * - Time range selector
 * - Manual refresh button
 */

import { memo } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import TimerIcon from '@mui/icons-material/Timer'
import PeopleOutlineIcon from '@mui/icons-material/PeopleOutline'
import { useGenerationOverview } from '../../hooks'
import type { GenerationAnalyticsFilters } from '../../types/analytics'
import { usePersistedState } from '../../hooks/usePersistedState'

const DAYS_OPTIONS = [
  { value: 1, label: '1 day' },
  { value: 7, label: '7 days' },
  { value: 30, label: '30 days' },
]

// Default filter values
const DEFAULT_FILTERS: GenerationAnalyticsFilters = {
  days: 7,
  interval: 'hourly',
}

/**
 * Format duration in milliseconds to seconds with 1 decimal
 */
function formatDuration(ms: number): string {
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * Format large numbers with commas
 */
function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

interface MetricCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color?: string
  loading?: boolean
}

const MetricCard = memo(function MetricCard({ title, value, icon, color = 'primary.main', loading }: MetricCardProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        border: 1,
        borderColor: 'divider',
        height: '100%',
      }}
    >
      <Stack spacing={1}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Box sx={{ color, display: 'flex' }}>{icon}</Box>
          <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', fontWeight: 600 }}>
            {title}
          </Typography>
        </Stack>
        {loading ? (
          <Skeleton variant="text" width={100} height={40} />
        ) : (
          <Typography variant="h4" component="div" fontWeight={700} sx={{ color }}>
            {value}
          </Typography>
        )}
      </Stack>
    </Paper>
  )
})

export function GenerationAnalyticsCard() {
  // Persist filters in localStorage
  const [filters, setFilters] = usePersistedState<GenerationAnalyticsFilters>(
    'analytics-generation-filters',
    DEFAULT_FILTERS
  )

  // Fetch data
  const { data, isLoading, error, refetch, isFetching } = useGenerationOverview({
    days: filters.days,
  })

  const handleFilterChange = (key: keyof GenerationAnalyticsFilters, value: number | string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <Card data-testid="generation-analytics-card">
      <CardContent>
        <Stack spacing={3}>
          {/* Header */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" component="h2" fontWeight={600} data-testid="generation-analytics-title">
              Generation Analytics
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
              disabled={isFetching}
              data-testid="generation-analytics-refresh"
            >
              Refresh
            </Button>
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Image generation system performance and usage patterns
          </Typography>

          {/* Filters */}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} data-testid="generation-analytics-filters">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Time Range</InputLabel>
              <Select
                value={filters.days}
                label="Time Range"
                onChange={(e) => handleFilterChange('days', e.target.value as number)}
                inputProps={{ 'data-testid': 'generation-analytics-days-select' }}
              >
                {DAYS_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          {/* Error State */}
          {error && (
            <Alert severity="error" data-testid="generation-analytics-error">
              Failed to load generation analytics: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
          )}

          {/* Overview Metrics */}
          {isLoading ? (
            <Grid container spacing={2} data-testid="generation-analytics-loading">
              {[...Array(4)].map((_, i) => (
                <Grid size={{ xs: 12, sm: 6, md: 3 }} key={i}>
                  <Skeleton variant="rectangular" height={120} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box data-testid="generation-analytics-loaded">
              {data ? (
                <>
                  <Grid container spacing={2} data-testid="generation-analytics-metrics">
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <MetricCard
                    title="Total Generations"
                    value={formatNumber(data.total_requests)}
                    icon={<CheckCircleOutlineIcon />}
                    color="primary.main"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <MetricCard
                    title="Success Rate"
                    value={`${data.success_rate_pct.toFixed(1)}%`}
                    icon={<CheckCircleOutlineIcon />}
                    color={data.success_rate_pct >= 90 ? 'success.main' : 'warning.main'}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <MetricCard
                    title="Avg Duration"
                    value={formatDuration(data.avg_duration_ms)}
                    icon={<TimerIcon />}
                    color="info.main"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <MetricCard
                    title="Unique Users"
                    value={data.unique_users !== undefined ? formatNumber(data.unique_users) : 'N/A'}
                    icon={<PeopleOutlineIcon />}
                    color="secondary.main"
                  />
                </Grid>
              </Grid>

              {/* Detailed Stats */}
              <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }}>
                <Stack spacing={2}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Detailed Statistics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 6, sm: 4 }}>
                      <Typography variant="caption" color="text.secondary">
                        Successful
                      </Typography>
                      <Typography variant="body1" fontWeight={600} color="success.main">
                        {formatNumber(data.successful_generations)}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 4 }}>
                      <Typography variant="caption" color="text.secondary">
                        Failed
                      </Typography>
                      <Typography variant="body1" fontWeight={600} color="error.main">
                        {formatNumber(data.failed_generations)}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 4 }}>
                      <Typography variant="caption" color="text.secondary">
                        Cancelled
                      </Typography>
                      <Typography variant="body1" fontWeight={600} color="warning.main">
                        {formatNumber(data.cancelled_generations)}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 4 }}>
                      <Typography variant="caption" color="text.secondary">
                        P50 Duration
                      </Typography>
                      <Typography variant="body1">{formatDuration(data.p50_duration_ms)}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 4 }}>
                      <Typography variant="caption" color="text.secondary">
                        P95 Duration
                      </Typography>
                      <Typography variant="body1">{formatDuration(data.p95_duration_ms)}</Typography>
                    </Grid>
                    <Grid size={{ xs: 6, sm: 4 }}>
                      <Typography variant="caption" color="text.secondary">
                        P99 Duration
                      </Typography>
                      <Typography variant="body1">{formatDuration(data.p99_duration_ms)}</Typography>
                    </Grid>
                  </Grid>
                </Stack>
              </Paper>
                </>
              ) : (
                <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }} data-testid="generation-analytics-empty">
                  <Typography variant="body2">
                    No generation analytics data available for the selected time range.
                  </Typography>
                  <Typography variant="caption">
                    Try adjusting the time range or ensure generation tracking is enabled.
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Footer Info */}
          {data && (
            <Typography variant="caption" color="text.secondary" data-testid="generation-analytics-info">
              Showing data from last {data.lookback_days} days
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
