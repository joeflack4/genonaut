/**
 * Route Analytics Card Component
 *
 * Displays API endpoint performance metrics and cache priorities.
 * Features:
 * - System selector (Absolute vs Relative ranking)
 * - Time range selector (7, 14, 30, 90 days)
 * - Top N selector (5, 10, 20, 50 routes)
 * - Sortable data table with performance metrics
 * - Color-coded latency indicators
 */

import { useState, useMemo } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
  Chip,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import { useRouteCachePriorities } from '../../hooks'
import type { CacheAnalysisSystem, RouteAnalyticsFilters } from '../../types/analytics'
import { usePersistedState } from '../../hooks/usePersistedState'

const SYSTEM_OPTIONS: { value: CacheAnalysisSystem; label: string; description: string }[] = [
  { value: 'absolute', label: 'Absolute (Production)', description: 'Uses static thresholds' },
  { value: 'relative', label: 'Relative (Development)', description: 'Percentile-based ranking' },
]

const DAYS_OPTIONS = [
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '90 days' },
]

const TOP_N_OPTIONS = [
  { value: 5, label: 'Top 5' },
  { value: 10, label: 'Top 10' },
  { value: 20, label: 'Top 20' },
  { value: 50, label: 'Top 50' },
]

// Default filter values
const DEFAULT_FILTERS: RouteAnalyticsFilters = {
  system: 'absolute',
  days: 7,
  topN: 10,
  minRequests: 10,
  minLatency: 100,
}

/**
 * Get color for latency value based on thresholds.
 * Green: < 100ms, Yellow: 100-500ms, Red: > 500ms
 */
function getLatencyColor(latencyMs: number): string {
  if (latencyMs < 100) return 'success.main'
  if (latencyMs < 500) return 'warning.main'
  return 'error.main'
}

/**
 * Format large numbers with commas (e.g., 1234 -> 1,234)
 */
function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

/**
 * Format percentage with 1 decimal place
 */
function formatPercentage(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`
}

export function RouteAnalyticsCard() {
  // Persist filters in localStorage
  const [filters, setFilters] = usePersistedState<RouteAnalyticsFilters>(
    'analytics-route-filters',
    DEFAULT_FILTERS
  )

  // Fetch data with current filters
  const { data, isLoading, error, refetch, isFetching } = useRouteCachePriorities({
    n: filters.topN,
    days: filters.days,
    system: filters.system,
    min_requests: filters.minRequests,
    min_latency: filters.minLatency,
  })

  // Local state for sorting (client-side)
  const [sortBy, setSortBy] = useState<string>('rank')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Sort routes client-side
  const sortedRoutes = useMemo(() => {
    if (!data?.routes) return []

    const routes = [...data.routes]
    return routes.sort((a, b) => {
      let aVal: number
      let bVal: number

      switch (sortBy) {
        case 'rank':
          // Rank is just the index
          return sortDirection === 'asc' ? 0 : 0
        case 'route':
          return sortDirection === 'asc'
            ? a.route.localeCompare(b.route)
            : b.route.localeCompare(a.route)
        case 'requests':
          aVal = a.avg_hourly_requests
          bVal = b.avg_hourly_requests
          break
        case 'latency':
          aVal = a.avg_p95_latency_ms
          bVal = b.avg_p95_latency_ms
          break
        case 'users':
          aVal = a.avg_unique_users
          bVal = b.avg_unique_users
          break
        case 'priority':
          aVal = 'cache_priority_score' in a ? a.cache_priority_score : a.priority_score
          bVal = 'cache_priority_score' in b ? b.cache_priority_score : b.priority_score
          break
        case 'success_rate':
          aVal = a.success_rate
          bVal = b.success_rate
          break
        default:
          return 0
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    })
  }, [data?.routes, sortBy, sortDirection])

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortDirection('desc') // Default to descending for new column
    }
  }

  const handleFilterChange = (key: keyof RouteAnalyticsFilters, value: CacheAnalysisSystem | number) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <Card data-testid="route-analytics-card">
      <CardContent>
        <Stack spacing={3}>
          {/* Header */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" component="h2" fontWeight={600} data-testid="route-analytics-title">
              Route Analytics
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
              disabled={isFetching}
              data-testid="route-analytics-refresh"
            >
              Refresh
            </Button>
          </Stack>

          <Typography variant="body2" color="text.secondary">
            API endpoint performance metrics and cache priorities
          </Typography>

          {/* Filters */}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} data-testid="route-analytics-filters">
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Analysis System</InputLabel>
              <Select
                value={filters.system}
                label="Analysis System"
                onChange={(e) => handleFilterChange('system', e.target.value as CacheAnalysisSystem)}
                inputProps={{ 'data-testid': 'route-analytics-system-select' }}
              >
                {SYSTEM_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Time Range</InputLabel>
              <Select
                value={filters.days}
                label="Time Range"
                onChange={(e) => handleFilterChange('days', e.target.value as number)}
                inputProps={{ 'data-testid': 'route-analytics-days-select' }}
              >
                {DAYS_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Show</InputLabel>
              <Select
                value={filters.topN}
                label="Show"
                onChange={(e) => handleFilterChange('topN', e.target.value as number)}
                inputProps={{ 'data-testid': 'route-analytics-topn-select' }}
              >
                {TOP_N_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          {/* Data Table */}
          {error && (
            <Alert severity="error" data-testid="route-analytics-error">
              Failed to load route analytics: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
          )}

          {isLoading ? (
            <Stack spacing={1}>
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} variant="rectangular" height={40} />
              ))}
            </Stack>
          ) : data?.routes && data.routes.length > 0 ? (
            <TableContainer component={Paper} variant="outlined" data-testid="route-analytics-table">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Method</TableCell>
                    <TableCell
                      onClick={() => handleSort('route')}
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      Route {sortBy === 'route' && (sortDirection === 'asc' ? '↑' : '↓')}
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('requests')}
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      Req/Hr {sortBy === 'requests' && (sortDirection === 'asc' ? '↑' : '↓')}
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('latency')}
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      P95 Latency {sortBy === 'latency' && (sortDirection === 'asc' ? '↑' : '↓')}
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('users')}
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      Users {sortBy === 'users' && (sortDirection === 'asc' ? '↑' : '↓')}
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('priority')}
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      Priority {sortBy === 'priority' && (sortDirection === 'asc' ? '↑' : '↓')}
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('success_rate')}
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      Success Rate {sortBy === 'success_rate' && (sortDirection === 'asc' ? '↑' : '↓')}
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedRoutes.map((route, index) => {
                    const isTopThree = index < 3
                    const priorityScore =
                      'cache_priority_score' in route ? route.cache_priority_score : route.priority_score

                    return (
                      <TableRow
                        key={`${route.route}-${route.method}-${index}`}
                        sx={{
                          bgcolor: isTopThree ? 'action.hover' : 'inherit',
                          '&:hover': { bgcolor: 'action.selected' },
                        }}
                        data-testid={`route-analytics-row-${index}`}
                      >
                        <TableCell>
                          {isTopThree ? (
                            <Chip label={index + 1} size="small" color="primary" />
                          ) : (
                            index + 1
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip label={route.method} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {route.route}
                        </TableCell>
                        <TableCell align="right">{formatNumber(Math.round(route.avg_hourly_requests))}</TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: getLatencyColor(route.avg_p95_latency_ms), fontWeight: 600 }}
                        >
                          {Math.round(route.avg_p95_latency_ms)}ms
                        </TableCell>
                        <TableCell align="right">{Math.round(route.avg_unique_users)}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600 }}>
                          {formatNumber(Math.round(priorityScore))}
                        </TableCell>
                        <TableCell align="right">{formatPercentage(route.success_rate)}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }} data-testid="route-analytics-empty">
              <Typography variant="body2">
                No route analytics data available for the selected time range.
              </Typography>
              <Typography variant="caption">
                Try adjusting the time range or ensure the analytics collection is running.
              </Typography>
            </Box>
          )}

          {/* Footer Info */}
          {data && (
            <Typography variant="caption" color="text.secondary" data-testid="route-analytics-info">
              Showing {data.total_routes} routes from last {data.lookback_days} days using {data.system} system
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
