/**
 * Tag Cardinality Card Component
 *
 * Displays content distribution across tags with tabbed interface.
 *
 * **Tabs:**
 * - **Table (default):** Shows top N tags in table format for Regular and Auto-Generated content
 * - **Visualization:** Shows histograms with statistics for Regular and Auto-Generated content
 *
 * **Features:**
 * - Two separate data sources: Regular Content (items) and Auto-Generated Content (auto)
 * - Top N selectors for each content type (10, 50, 100, 200, 1000, Custom)
 * - Statistics summary for each content type (Visualization tab only)
 * - Histogram visualization with log/linear scale toggle (Visualization tab only)
 * - Popular tags tables (both tabs)
 * - Tab state and filter preferences persisted in localStorage
 */

import { useMemo, lazy, Suspense } from 'react'
import {
  Alert,
  Box,
  Card,
  CardContent,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  Link,
  MenuItem,
  Paper,
  Select,
  Skeleton,
  Stack,
  Switch,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { usePopularTags } from '../../hooks'
import type { CardinalityBucket, TagCardinalityStats, PopularTag, TopNPreset, TagCardinalityFilters, TagCardinalityTab } from '../../types/analytics'
import { usePersistedState } from '../../hooks/usePersistedState'

// Lazy load Recharts for better initial page load performance
const BarChart = lazy(() => import('recharts').then(module => ({ default: module.BarChart })))
const Bar = lazy(() => import('recharts').then(module => ({ default: module.Bar })))
const XAxis = lazy(() => import('recharts').then(module => ({ default: module.XAxis })))
const YAxis = lazy(() => import('recharts').then(module => ({ default: module.YAxis })))
const CartesianGrid = lazy(() => import('recharts').then(module => ({ default: module.CartesianGrid })))
const Tooltip = lazy(() => import('recharts').then(module => ({ default: module.Tooltip })))
const ResponsiveContainer = lazy(() => import('recharts').then(module => ({ default: module.ResponsiveContainer })))
const Cell = lazy(() => import('recharts').then(module => ({ default: module.Cell })))

// Default filter values
const DEFAULT_FILTERS: TagCardinalityFilters = {
  activeTab: 'table' as TagCardinalityTab,
  topNItems: 100,
  topNAuto: 100,
  customLimitItems: null,
  customLimitAuto: null,
  minCardinality: 1,
  logScale: true,
}

// Top N preset options
const TOP_N_OPTIONS: { value: TopNPreset; label: string }[] = [
  { value: 10, label: 'Top 10' },
  { value: 50, label: 'Top 50' },
  { value: 100, label: 'Top 100' },
  { value: 200, label: 'Top 200' },
  { value: 1000, label: 'Top 1000' },
  { value: 'custom', label: 'Custom' },
]

/**
 * Generate dynamic histogram buckets based on actual data range
 */
function generateBuckets(tags: PopularTag[]): { range: string; min: number; max: number }[] {
  if (tags.length === 0) {
    // Return default buckets for empty data
    return [
      { range: '1', min: 1, max: 1 },
      { range: '2-10', min: 2, max: 10 },
      { range: '11-100', min: 11, max: 100 },
      { range: '101-1000', min: 101, max: 1000 },
      { range: '1000+', min: 1001, max: Infinity },
    ]
  }

  const cardinalities = tags.map(t => t.cardinality).sort((a, b) => a - b)
  const minCard = cardinalities[0]
  const maxCard = cardinalities[cardinalities.length - 1]

  // If all values are very similar (within one order of magnitude), use linear buckets
  if (maxCard / minCard < 10) {
    const range = maxCard - minCard
    const bucketSize = Math.ceil(range / 10)
    const buckets: { range: string; min: number; max: number }[] = []

    for (let i = 0; i < 10; i++) {
      const min = minCard + i * bucketSize
      const max = i === 9 ? maxCard : minCard + (i + 1) * bucketSize - 1
      buckets.push({
        range: min === max ? `${formatNumber(min)}` : `${formatNumber(min)}-${formatNumber(max)}`,
        min,
        max,
      })
    }
    return buckets
  }

  // Otherwise, use log-scale buckets
  const logMin = Math.floor(Math.log10(minCard))
  const logMax = Math.ceil(Math.log10(maxCard))
  const buckets: { range: string; min: number; max: number }[] = []

  for (let exp = logMin; exp <= logMax; exp++) {
    const base = Math.pow(10, exp)

    if (exp === logMin && minCard > base) {
      // First bucket starts at actual min
      buckets.push({
        range: `${formatNumber(minCard)}-${formatNumber(Math.pow(10, exp + 1) - 1)}`,
        min: minCard,
        max: Math.pow(10, exp + 1) - 1,
      })
    } else if (exp === logMax) {
      // Last bucket ends at actual max
      const prevMax = buckets.length > 0 ? buckets[buckets.length - 1].max : base - 1
      buckets.push({
        range: `${formatNumber(prevMax + 1)}+`,
        min: prevMax + 1,
        max: Infinity,
      })
    } else {
      // Middle buckets use powers of 10
      buckets.push({
        range: `${formatNumber(base)}-${formatNumber(Math.pow(10, exp + 1) - 1)}`,
        min: base,
        max: Math.pow(10, exp + 1) - 1,
      })
    }
  }

  return buckets
}

/**
 * Bin tags into histogram buckets
 */
function binTags(tags: PopularTag[]): CardinalityBucket[] {
  const bucketDefs = generateBuckets(tags)
  const buckets: CardinalityBucket[] = bucketDefs.map((bucket) => ({
    ...bucket,
    tag_count: 0,
  }))

  tags.forEach((tag) => {
    const bucket = buckets.find(
      (b) => tag.cardinality >= b.min && tag.cardinality <= b.max
    )
    if (bucket) {
      bucket.tag_count++
    }
  })

  return buckets
}

/**
 * Calculate statistics from tag data
 */
function calculateStats(tags: PopularTag[]): TagCardinalityStats {
  if (tags.length === 0) {
    return {
      total_tags: 0,
      tags_with_content: 0,
      most_popular_tag: null,
      median_cardinality: 0,
      p90_cardinality: 0,
    }
  }

  const sortedByCardinality = [...tags].sort((a, b) => b.cardinality - a.cardinality)
  const medianIndex = Math.floor(sortedByCardinality.length / 2)
  const p90Index = Math.floor(sortedByCardinality.length * 0.9)

  return {
    total_tags: tags.length,
    tags_with_content: tags.filter((t) => t.cardinality > 0).length,
    most_popular_tag: sortedByCardinality[0],
    median_cardinality: sortedByCardinality[medianIndex]?.cardinality || 0,
    p90_cardinality: sortedByCardinality[p90Index]?.cardinality || 0,
  }
}

/**
 * Format large numbers with commas
 */
function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

/**
 * Get the effective limit based on top N selection and custom value
 */
function getEffectiveLimit(topN: TopNPreset, customLimit: number | null): number {
  if (topN === 'custom') {
    return customLimit && customLimit >= 1 && customLimit <= 1000 ? customLimit : 100
  }
  return topN
}

/**
 * Top N Selector Component
 */
interface TopNSelectorProps {
  value: TopNPreset
  customValue: number | null
  onValueChange: (value: TopNPreset) => void
  onCustomValueChange: (value: number | null) => void
  testIdPrefix: string
}

function TopNSelector({ value, customValue, onValueChange, onCustomValueChange, testIdPrefix }: TopNSelectorProps) {
  return (
    <Stack direction="row" spacing={2} alignItems="center">
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <InputLabel>Show</InputLabel>
        <Select
          value={value}
          label="Show"
          onChange={(e) => onValueChange(e.target.value as TopNPreset)}
          inputProps={{ 'data-testid': `${testIdPrefix}-select` }}
        >
          {TOP_N_OPTIONS.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      {value === 'custom' && (
        <TextField
          size="small"
          type="number"
          label="Custom Limit"
          value={customValue || ''}
          onChange={(e) => {
            const val = parseInt(e.target.value, 10)
            onCustomValueChange(isNaN(val) ? null : Math.max(1, Math.min(1000, val)))
          }}
          inputProps={{
            min: 1,
            max: 1000,
            'data-testid': `${testIdPrefix}-custom-input`,
          }}
          sx={{ width: 140 }}
          helperText="1-1000"
        />
      )}
    </Stack>
  )
}

/**
 * Table-Only Section Component (for Table tab)
 * Shows only the top N tags table without histogram or stats
 */
interface TableSectionProps {
  title: string
  contentSource: 'regular' | 'auto'
  topN: TopNPreset
  customLimit: number | null
  onTopNChange: (value: TopNPreset) => void
  onCustomLimitChange: (value: number | null) => void
  minCardinality: number
  testIdPrefix: string
}

function TableSection({
  title,
  contentSource,
  topN,
  customLimit,
  onTopNChange,
  onCustomLimitChange,
  minCardinality,
  testIdPrefix,
}: TableSectionProps) {
  const limit = getEffectiveLimit(topN, customLimit)

  // Fetch data
  const { data: tags, isLoading, error } = usePopularTags({
    limit,
    content_source: contentSource,
    min_cardinality: minCardinality,
  })

  // All tags returned by API (already limited by topN parameter)
  const topTags = useMemo(() => {
    if (!tags) return []
    return tags // API already returns the correct limit based on topN
  }, [tags])

  return (
    <Box data-testid={`${testIdPrefix}-section`}>
      <Stack spacing={2}>
        {/* Section Header with TopN Selector */}
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
          <TopNSelector
            value={topN}
            customValue={customLimit}
            onValueChange={onTopNChange}
            onCustomValueChange={onCustomLimitChange}
            testIdPrefix={testIdPrefix + '-topn'}
          />
        </Stack>

        {/* Error State */}
        {error && (
          <Alert severity="error">
            Failed to load {title.toLowerCase()}: {error instanceof Error ? error.message : 'Unknown error'}
          </Alert>
        )}

        {/* Table */}
        {isLoading ? (
          <Stack spacing={1}>
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} variant="rectangular" height={40} />
            ))}
          </Stack>
        ) : topTags.length > 0 ? (
          <TableContainer component={Paper} variant="outlined" data-testid={`${testIdPrefix}-table`}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>Tag Name</TableCell>
                  <TableCell align="right">N items</TableCell>
                  <TableCell align="right">Percentage</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {topTags.map((tag, index) => {
                  const totalCardinality = tags?.reduce((sum, t) => sum + t.cardinality, 0) || 1
                  const percentage = (tag.cardinality / totalCardinality) * 100

                  return (
                    <TableRow
                      key={tag.id}
                      sx={{
                        '&:hover': { bgcolor: 'action.selected' },
                      }}
                      data-testid={`${testIdPrefix}-row-${index}`}
                    >
                      <TableCell>
                        {index + 1}
                      </TableCell>
                      <TableCell>
                        <Link
                          component={RouterLink}
                          to={`/tags/${tag.id}`}
                          underline="hover"
                          color="primary"
                        >
                          {tag.name}
                        </Link>
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>
                        {formatNumber(tag.cardinality)}
                      </TableCell>
                      <TableCell align="right">{percentage.toFixed(2)}%</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }} data-testid={`${testIdPrefix}-empty`}>
            <Typography variant="body2">No data available for {title.toLowerCase()}.</Typography>
          </Box>
        )}
      </Stack>
    </Box>
  )
}

/**
 * Single Histogram Section Component
 */
interface HistogramSectionProps {
  title: string
  contentSource: 'regular' | 'auto'
  topN: TopNPreset
  customLimit: number | null
  onTopNChange: (value: TopNPreset) => void
  onCustomLimitChange: (value: number | null) => void
  minCardinality: number
  logScale: boolean
  testIdPrefix: string
}

function HistogramSection({
  title,
  contentSource,
  topN,
  customLimit,
  onTopNChange,
  onCustomLimitChange,
  minCardinality,
  logScale,
  testIdPrefix,
}: HistogramSectionProps) {
  const limit = getEffectiveLimit(topN, customLimit)

  // Fetch data
  const { data: tags, isLoading, error } = usePopularTags({
    limit,
    content_source: contentSource,
    min_cardinality: minCardinality,
  })

  // Calculate stats and histogram data
  const stats = useMemo(() => (tags ? calculateStats(tags) : null), [tags])
  const histogramData = useMemo(() => (tags ? binTags(tags) : []), [tags])

  // All tags returned by API (already limited by topN parameter)
  const topTags = useMemo(() => {
    if (!tags) return []
    return tags // API already returns the correct limit based on topN
  }, [tags])

  return (
    <Box data-testid={testIdPrefix}>
      <Stack spacing={3}>
        {/* Header with TopN Selector */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
          <Typography variant="h6" component="h3" fontWeight={600} data-testid={`${testIdPrefix}-title`}>
            {title}
          </Typography>
          <TopNSelector
            value={topN}
            customValue={customLimit}
            onValueChange={onTopNChange}
            onCustomValueChange={onCustomLimitChange}
            testIdPrefix={`${testIdPrefix}-topn`}
          />
        </Stack>

        {/* Error State */}
        {error && (
          <Alert severity="error" data-testid={`${testIdPrefix}-error`}>
            Failed to load data: {error instanceof Error ? error.message : 'Unknown error'}
          </Alert>
        )}

        {/* Statistics Summary */}
        {isLoading ? (
          <Skeleton variant="rectangular" height={100} />
        ) : stats ? (
          <Paper elevation={0} sx={{ p: 2, border: 1, borderColor: 'divider' }} data-testid={`${testIdPrefix}-stats`}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
                <Typography variant="caption" color="text.secondary">
                  Total Tags
                </Typography>
                <Typography variant="h6" fontWeight={600}>
                  {formatNumber(stats.total_tags)}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
                <Typography variant="caption" color="text.secondary">
                  With Content
                </Typography>
                <Typography variant="h6" fontWeight={600}>
                  {formatNumber(stats.tags_with_content)}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
                <Typography variant="caption" color="text.secondary">
                  Most Popular
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {stats.most_popular_tag ? `${stats.most_popular_tag.name} (${formatNumber(stats.most_popular_tag.cardinality)})` : 'N/A'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
                <Typography variant="caption" color="text.secondary">
                  Median
                </Typography>
                <Typography variant="h6" fontWeight={600}>
                  {formatNumber(stats.median_cardinality)}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 4, md: 2.4 }}>
                <Typography variant="caption" color="text.secondary">
                  90th Percentile
                </Typography>
                <Typography variant="h6" fontWeight={600}>
                  {formatNumber(stats.p90_cardinality)}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        ) : null}

        {/* Histogram */}
        {isLoading ? (
          <Skeleton variant="rectangular" height={300} />
        ) : histogramData.length > 0 ? (
          <Box data-testid={`${testIdPrefix}-histogram`}>
            <Typography variant="subtitle2" gutterBottom fontWeight={600}>
              Distribution ({logScale ? 'Log' : 'Linear'} Scale)
            </Typography>
            <Suspense fallback={<Skeleton variant="rectangular" height={300} />}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="range"
                    label={{ value: 'Cardinality Range', position: 'insideBottom', offset: -5 }}
                  />
                  <YAxis
                    scale={logScale ? 'log' : 'linear'}
                    domain={logScale ? [1, 'auto'] : [0, 'auto']}
                    label={{ value: 'Number of Tags', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload as CardinalityBucket
                        return (
                          <Paper sx={{ p: 1, border: 1, borderColor: 'divider' }}>
                            <Typography variant="caption">Range: {data.range}</Typography>
                            <br />
                            <Typography variant="body2" fontWeight={600}>
                              {data.tag_count} tags
                            </Typography>
                          </Paper>
                        )
                      }
                      return null
                    }}
                  />
                  <Bar dataKey="tag_count" fill="#8884d8">
                    {histogramData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={`hsl(${210 + index * 10}, 70%, 50%)`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Suspense>
          </Box>
        ) : null}

        {/* Popular Tags Table */}
        {isLoading ? (
          <Stack spacing={1}>
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} variant="rectangular" height={40} />
            ))}
          </Stack>
        ) : topTags.length > 0 ? (
          <Box data-testid={`${testIdPrefix}-table`}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Tag Name</TableCell>
                    <TableCell align="right">N items</TableCell>
                    <TableCell align="right">Percentage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topTags.map((tag, index) => {
                    const totalCardinality = tags?.reduce((sum, t) => sum + t.cardinality, 0) || 1
                    const percentage = (tag.cardinality / totalCardinality) * 100

                    return (
                      <TableRow
                        key={tag.id}
                        sx={{
                          '&:hover': { bgcolor: 'action.selected' },
                        }}
                        data-testid={`${testIdPrefix}-row-${index}`}
                      >
                        <TableCell>
                          {index + 1}
                        </TableCell>
                        <TableCell>
                          <Link
                            component={RouterLink}
                            to={`/tags/${tag.id}`}
                            underline="hover"
                            color="primary"
                          >
                            {tag.name}
                          </Link>
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600 }}>
                          {formatNumber(tag.cardinality)}
                        </TableCell>
                        <TableCell align="right">{percentage.toFixed(2)}%</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }} data-testid={`${testIdPrefix}-empty`}>
            <Typography variant="body2">No data available for {title.toLowerCase()}.</Typography>
          </Box>
        )}
      </Stack>
    </Box>
  )
}

export function TagCardinalityCard() {
  // Persist filters in localStorage
  const [filters, setFilters] = usePersistedState<TagCardinalityFilters>(
    'analytics-tag-cardinality-filters-v2', // New key to avoid conflicts with old format
    DEFAULT_FILTERS
  )

  // Fetch all tags from both sources to calculate total unique tags
  const { data: regularTags } = usePopularTags({
    limit: 10000,
    content_source: 'regular',
    min_cardinality: 1,
  })
  const { data: autoTags } = usePopularTags({
    limit: 10000,
    content_source: 'auto',
    min_cardinality: 1,
  })

  // Calculate total unique tags across both sources
  const totalUniqueTags = useMemo(() => {
    const tagIds = new Set<string>()
    regularTags?.forEach(tag => tagIds.add(tag.id))
    autoTags?.forEach(tag => tagIds.add(tag.id))
    return tagIds.size
  }, [regularTags, autoTags])

  const handleFilterChange = (key: keyof TagCardinalityFilters, value: TopNPreset | number | null | boolean | TagCardinalityTab) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: TagCardinalityTab) => {
    setFilters((prev) => ({ ...prev, activeTab: newValue }))
  }

  return (
    <Card data-testid="tag-cardinality-card">
      <CardContent>
        <Stack spacing={4}>
          {/* Card Header */}
          <Stack spacing={0.5}>
            <Typography variant="h5" component="h2" fontWeight={600} data-testid="tag-cardinality-title">
              Tags
            </Typography>
            {totalUniqueTags > 0 && (
              <Typography variant="body2" color="text.secondary" data-testid="tag-cardinality-total">
                Total tags: {formatNumber(totalUniqueTags)}
              </Typography>
            )}
          </Stack>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={filters.activeTab}
              onChange={handleTabChange}
              data-testid="tag-cardinality-tabs"
            >
              <Tab
                label="Table"
                value="table"
                data-testid="tag-cardinality-tab-table"
              />
              <Tab
                label="Visualization"
                value="visualization"
                data-testid="tag-cardinality-tab-visualization"
              />
            </Tabs>
          </Box>

          {/* Table Tab Content */}
          {filters.activeTab === 'table' && (
            <Grid container spacing={4}>
              {/* Regular Content (Items) */}
              <Grid size={{ xs: 12, lg: 6 }}>
                <TableSection
                  title="Regular Content"
                  contentSource="regular"
                  topN={filters.topNItems}
                  customLimit={filters.customLimitItems}
                  onTopNChange={(value) => handleFilterChange('topNItems', value)}
                  onCustomLimitChange={(value) => handleFilterChange('customLimitItems', value)}
                  minCardinality={filters.minCardinality}
                  testIdPrefix="tag-cardinality-items"
                />
              </Grid>

              {/* Auto-Generated Content */}
              <Grid size={{ xs: 12, lg: 6 }}>
                <TableSection
                  title="Auto-Generated Content"
                  contentSource="auto"
                  topN={filters.topNAuto}
                  customLimit={filters.customLimitAuto}
                  onTopNChange={(value) => handleFilterChange('topNAuto', value)}
                  onCustomLimitChange={(value) => handleFilterChange('customLimitAuto', value)}
                  minCardinality={filters.minCardinality}
                  testIdPrefix="tag-cardinality-auto"
                />
              </Grid>
            </Grid>
          )}

          {/* Visualization Tab Content */}
          {filters.activeTab === 'visualization' && (
            <Stack spacing={3}>
              {/* Log Scale Toggle (only in Visualization tab) */}
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={filters.logScale}
                      onChange={(e) => handleFilterChange('logScale', e.target.checked)}
                      inputProps={{ 'data-testid': 'tag-cardinality-log-scale-toggle' }}
                    />
                  }
                  label="Log Scale"
                />
              </Box>

              {/* Two Column Layout for Histograms */}
              <Grid container spacing={4}>
                {/* Regular Content (Items) */}
                <Grid size={{ xs: 12, lg: 6 }}>
                  <HistogramSection
                    title="Regular Content"
                    contentSource="regular"
                    topN={filters.topNItems}
                    customLimit={filters.customLimitItems}
                    onTopNChange={(value) => handleFilterChange('topNItems', value)}
                    onCustomLimitChange={(value) => handleFilterChange('customLimitItems', value)}
                    minCardinality={filters.minCardinality}
                    logScale={filters.logScale}
                    testIdPrefix="tag-cardinality-items"
                  />
                </Grid>

                {/* Auto-Generated Content */}
                <Grid size={{ xs: 12, lg: 6 }}>
                  <HistogramSection
                    title="Auto-Generated Content"
                    contentSource="auto"
                    topN={filters.topNAuto}
                    customLimit={filters.customLimitAuto}
                    onTopNChange={(value) => handleFilterChange('topNAuto', value)}
                    onCustomLimitChange={(value) => handleFilterChange('customLimitAuto', value)}
                    minCardinality={filters.minCardinality}
                    logScale={filters.logScale}
                    testIdPrefix="tag-cardinality-auto"
                  />
                </Grid>
              </Grid>
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}
