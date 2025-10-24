/**
 * React Query hooks for analytics data fetching.
 *
 * Provides hooks for:
 * - Route analytics (cache priorities, performance trends, peak hours)
 * - Generation analytics (overview, trends)
 * - Tag cardinality (popular tags)
 */

import { useQuery } from '@tanstack/react-query'
import { analyticsService } from '../services/analytics-service'
import type {
  CachePrioritiesResponse,
  CachePrioritiesParams,
  PerformanceTrendsResponse,
  PerformanceTrendsParams,
  PeakHoursResponse,
  PeakHoursParams,
  GenerationOverviewResponse,
  GenerationOverviewParams,
  GenerationTrendsResponse,
  GenerationTrendsParams,
  PopularTagsResponse,
  PopularTagsParams,
} from '../types/analytics'

// ============================================================================
// Query Keys
// ============================================================================

export const analyticsKeys = {
  all: ['analytics'] as const,

  // Route analytics
  routes: () => [...analyticsKeys.all, 'routes'] as const,
  cachePriorities: (params?: CachePrioritiesParams) =>
    [...analyticsKeys.routes(), 'cache-priorities', params] as const,
  performanceTrends: (params: PerformanceTrendsParams) =>
    [...analyticsKeys.routes(), 'performance-trends', params] as const,
  peakHours: (params?: PeakHoursParams) =>
    [...analyticsKeys.routes(), 'peak-hours', params] as const,

  // Generation analytics
  generation: () => [...analyticsKeys.all, 'generation'] as const,
  generationOverview: (params?: GenerationOverviewParams) =>
    [...analyticsKeys.generation(), 'overview', params] as const,
  generationTrends: (params?: GenerationTrendsParams) =>
    [...analyticsKeys.generation(), 'trends', params] as const,

  // Tag cardinality
  tags: () => [...analyticsKeys.all, 'tags'] as const,
  popularTags: (params?: PopularTagsParams) =>
    [...analyticsKeys.tags(), 'popular', params] as const,
}

// ============================================================================
// Route Analytics Hooks
// ============================================================================

/**
 * Hook to fetch top N routes recommended for caching.
 *
 * @param params Query parameters for filtering
 * @param options React Query options
 * @returns Query result with cache priorities data
 *
 * @example
 * ```tsx
 * function CachePrioritiesTable() {
 *   const { data, isLoading, error } = useRouteCachePriorities({
 *     n: 20,
 *     days: 7,
 *     system: 'absolute'
 *   })
 *
 *   if (isLoading) return <Skeleton />
 *   if (error) return <ErrorMessage error={error} />
 *   return <Table data={data.routes} />
 * }
 * ```
 */
export function useRouteCachePriorities(
  params?: CachePrioritiesParams,
  options?: { enabled?: boolean; staleTime?: number; gcTime?: number }
) {
  return useQuery<CachePrioritiesResponse>({
    queryKey: analyticsKeys.cachePriorities(params),
    queryFn: () => analyticsService.getRouteCachePriorities(params),
    staleTime: 5 * 60 * 1000, // 5 minutes - analytics data doesn't change rapidly
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  })
}

/**
 * Hook to fetch performance trends for a specific route.
 *
 * @param params Route and time range parameters
 * @param options React Query options
 * @returns Query result with time-series performance data
 *
 * @example
 * ```tsx
 * function PerformanceChart({ route }: { route: string }) {
 *   const { data } = usePerformanceTrends({
 *     route,
 *     days: 30,
 *     granularity: 'daily'
 *   })
 *
 *   return <LineChart data={data?.trends} />
 * }
 * ```
 */
export function usePerformanceTrends(
  params: PerformanceTrendsParams,
  options?: { enabled?: boolean; staleTime?: number; gcTime?: number }
) {
  return useQuery<PerformanceTrendsResponse>({
    queryKey: analyticsKeys.performanceTrends(params),
    queryFn: () => analyticsService.getPerformanceTrends(params),
    enabled: Boolean(params.route), // Only fetch if route is provided
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,
    ...options,
  })
}

/**
 * Hook to fetch peak traffic hours analysis.
 *
 * @param params Optional route and threshold parameters
 * @param options React Query options
 * @returns Query result with peak hours data
 *
 * @example
 * ```tsx
 * function PeakHoursChart() {
 *   const { data } = usePeakHours({ days: 30 })
 *   return <BarChart data={data?.peak_hours} />
 * }
 * ```
 */
export function usePeakHours(
  params?: PeakHoursParams,
  options?: { enabled?: boolean; staleTime?: number; gcTime?: number }
) {
  return useQuery<PeakHoursResponse>({
    queryKey: analyticsKeys.peakHours(params),
    queryFn: () => analyticsService.getPeakHours(params),
    staleTime: 10 * 60 * 1000, // 10 minutes - peak hours change slowly
    gcTime: 15 * 60 * 1000,
    ...options,
  })
}

// ============================================================================
// Generation Analytics Hooks
// ============================================================================

/**
 * Hook to fetch generation overview statistics.
 *
 * @param params Time range parameters
 * @param options React Query options
 * @returns Query result with dashboard metrics
 *
 * @example
 * ```tsx
 * function GenerationDashboard() {
 *   const { data, refetch } = useGenerationOverview({ days: 7 })
 *
 *   return (
 *     <Grid>
 *       <MetricCard title="Total" value={data?.total_requests} />
 *       <MetricCard title="Success Rate" value={`${data?.success_rate_pct}%`} />
 *       <Button onClick={() => refetch()}>Refresh</Button>
 *     </Grid>
 *   )
 * }
 * ```
 */
export function useGenerationOverview(
  params?: GenerationOverviewParams,
  options?: { enabled?: boolean; staleTime?: number; gcTime?: number }
) {
  return useQuery<GenerationOverviewResponse>({
    queryKey: analyticsKeys.generationOverview(params),
    queryFn: () => analyticsService.getGenerationOverview(params),
    staleTime: 2 * 60 * 1000, // 2 minutes - generation stats can change frequently
    gcTime: 5 * 60 * 1000,
    ...options,
  })
}

/**
 * Hook to fetch generation trends over time.
 *
 * @param params Time range and granularity parameters
 * @param options React Query options
 * @returns Query result with time-series generation data
 *
 * @example
 * ```tsx
 * function GenerationTrendsChart() {
 *   const { data } = useGenerationTrends({
 *     days: 7,
 *     interval: 'hourly'
 *   })
 *
 *   return <LineChart data={data?.data_points} />
 * }
 * ```
 */
export function useGenerationTrends(
  params?: GenerationTrendsParams,
  options?: { enabled?: boolean; staleTime?: number; gcTime?: number }
) {
  return useQuery<GenerationTrendsResponse>({
    queryKey: analyticsKeys.generationTrends(params),
    queryFn: () => analyticsService.getGenerationTrends(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000,
    ...options,
  })
}

// ============================================================================
// Tag Cardinality Hooks
// ============================================================================

/**
 * Hook to fetch popular tags by content count.
 *
 * @param params Limit, filter, and threshold parameters
 * @param options React Query options
 * @returns Query result with popular tags list
 *
 * @example
 * ```tsx
 * function PopularTagsList() {
 *   const { data, isLoading } = usePopularTags({
 *     limit: 100,
 *     content_source: 'all',
 *     min_cardinality: 1
 *   })
 *
 *   if (isLoading) return <Skeleton />
 *   return (
 *     <List>
 *       {data?.map(tag => (
 *         <ListItem key={tag.id}>
 *           {tag.name} ({tag.cardinality})
 *         </ListItem>
 *       ))}
 *     </List>
 *   )
 * }
 * ```
 */
export function usePopularTags(
  params?: PopularTagsParams,
  options?: { enabled?: boolean; staleTime?: number; gcTime?: number }
) {
  return useQuery<PopularTagsResponse>({
    queryKey: analyticsKeys.popularTags(params),
    queryFn: () => analyticsService.getPopularTags(params),
    staleTime: 10 * 60 * 1000, // 10 minutes - tag cardinality changes slowly
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  })
}
