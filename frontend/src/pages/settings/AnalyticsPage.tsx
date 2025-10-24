/**
 * Analytics Page
 *
 * Displays system analytics including:
 * - Route performance and cache priorities
 * - Generation metrics and trends
 * - Tag cardinality statistics with histogram
 */

import { useState } from 'react'
import {
  Box,
  Button,
  Stack,
  Typography,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import { useQueryClient } from '@tanstack/react-query'
import { analyticsKeys } from '../../hooks/useAnalytics'
import { RouteAnalyticsCard } from '../../components/analytics/RouteAnalyticsCard'
import { GenerationAnalyticsCard } from '../../components/analytics/GenerationAnalyticsCard'
import { TagCardinalityCard } from '../../components/analytics/TagCardinalityCard'
import { ErrorBoundary } from '../../components/common/ErrorBoundary'

export function AnalyticsPage() {
  const queryClient = useQueryClient()
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  const handleRefreshAll = () => {
    // Invalidate all analytics queries to force refetch
    queryClient.invalidateQueries({ queryKey: analyticsKeys.all })
    setLastUpdated(new Date())
  }

  return (
    <Stack spacing={4} data-testid="analytics-page-root" sx={{ p: 3 }}>
      {/* Page Header */}
      <Stack spacing={1} data-testid="analytics-header">
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4" component="h1" fontWeight={600} gutterBottom data-testid="analytics-title">
              Analytics
            </Typography>
            <Typography variant="body2" color="text.secondary" data-testid="analytics-subtitle">
              System performance metrics, generation statistics, and content distribution analysis
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshAll}
            data-testid="analytics-refresh-all"
          >
            Refresh All
          </Button>
        </Stack>
        <Typography variant="caption" color="text.secondary" data-testid="analytics-last-updated">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </Typography>
      </Stack>

      {/* Route Analytics Card */}
      <ErrorBoundary
        fallbackMessage="Unable to load route analytics. This section is temporarily unavailable."
        onReset={() => queryClient.invalidateQueries({ queryKey: analyticsKeys.routeAnalytics._def })}
      >
        <RouteAnalyticsCard />
      </ErrorBoundary>

      {/* Generation Analytics Card */}
      <ErrorBoundary
        fallbackMessage="Unable to load generation analytics. This section is temporarily unavailable."
        onReset={() => queryClient.invalidateQueries({ queryKey: analyticsKeys.generationAnalytics._def })}
      >
        <GenerationAnalyticsCard />
      </ErrorBoundary>

      {/* Tag Cardinality Card */}
      <ErrorBoundary
        fallbackMessage="Unable to load tag cardinality analytics. This section is temporarily unavailable."
        onReset={() => queryClient.invalidateQueries({ queryKey: analyticsKeys.tagCardinality._def })}
      >
        <TagCardinalityCard />
      </ErrorBoundary>
    </Stack>
  )
}
