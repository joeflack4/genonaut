/**
 * Analytics API service for route performance, generation metrics, and tag cardinality.
 *
 * Provides methods to fetch analytics data from the backend API:
 * - Route analytics (cache priorities, performance trends, peak hours)
 * - Generation analytics (overview, trends)
 * - Tag cardinality (popular tags)
 */

import { ApiClient } from './api-client'
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

export class AnalyticsService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  // ============================================================================
  // Route Analytics Methods
  // ============================================================================

  /**
   * Get top N routes recommended for caching.
   *
   * @param params Query parameters for filtering and sorting
   * @returns Cache priorities response with routes and metadata
   *
   * @example
   * ```ts
   * const analytics = new AnalyticsService(apiClient)
   * const priorities = await analytics.getRouteCachePriorities({
   *   n: 20,
   *   days: 7,
   *   system: 'absolute'
   * })
   * ```
   */
  async getRouteCachePriorities(
    params?: CachePrioritiesParams
  ): Promise<CachePrioritiesResponse> {
    const queryParams = new URLSearchParams()

    if (params?.n !== undefined) {
      queryParams.set('n', String(params.n))
    }
    if (params?.days !== undefined) {
      queryParams.set('days', String(params.days))
    }
    if (params?.system !== undefined) {
      queryParams.set('system', params.system)
    }
    if (params?.min_requests !== undefined) {
      queryParams.set('min_requests', String(params.min_requests))
    }
    if (params?.min_latency !== undefined) {
      queryParams.set('min_latency', String(params.min_latency))
    }

    const query = queryParams.toString()
    return this.api.get<CachePrioritiesResponse>(
      `/api/v1/analytics/routes/cache-priorities${query ? `?${query}` : ''}`
    )
  }

  /**
   * Get performance trends for a specific route over time.
   *
   * @param params Route and time range parameters
   * @returns Time-series performance data
   *
   * @example
   * ```ts
   * const trends = await analytics.getPerformanceTrends({
   *   route: '/api/v1/content/unified',
   *   days: 30,
   *   granularity: 'daily'
   * })
   * ```
   */
  async getPerformanceTrends(
    params: PerformanceTrendsParams
  ): Promise<PerformanceTrendsResponse> {
    const queryParams = new URLSearchParams()
    queryParams.set('route', params.route)

    if (params.days !== undefined) {
      queryParams.set('days', String(params.days))
    }
    if (params.granularity !== undefined) {
      queryParams.set('granularity', params.granularity)
    }

    const query = queryParams.toString()
    return this.api.get<PerformanceTrendsResponse>(
      `/api/v1/analytics/routes/performance-trends?${query}`
    )
  }

  /**
   * Get peak traffic hours analysis.
   *
   * @param params Optional route and threshold parameters
   * @returns Peak hours data for route(s)
   *
   * @example
   * ```ts
   * // All routes
   * const allPeaks = await analytics.getPeakHours({ days: 30 })
   *
   * // Specific route
   * const routePeaks = await analytics.getPeakHours({
   *   route: '/api/v1/content/unified',
   *   days: 30
   * })
   * ```
   */
  async getPeakHours(params?: PeakHoursParams): Promise<PeakHoursResponse> {
    const queryParams = new URLSearchParams()

    if (params?.route !== undefined) {
      queryParams.set('route', params.route)
    }
    if (params?.days !== undefined) {
      queryParams.set('days', String(params.days))
    }
    if (params?.min_requests !== undefined) {
      queryParams.set('min_requests', String(params.min_requests))
    }

    const query = queryParams.toString()
    return this.api.get<PeakHoursResponse>(
      `/api/v1/analytics/routes/peak-hours${query ? `?${query}` : ''}`
    )
  }

  // ============================================================================
  // Generation Analytics Methods
  // ============================================================================

  /**
   * Get high-level overview of generation activity.
   *
   * @param params Time range parameters
   * @returns Dashboard metrics for generations
   *
   * @example
   * ```ts
   * const overview = await analytics.getGenerationOverview({ days: 7 })
   * console.log(`Success rate: ${overview.success_rate_pct}%`)
   * ```
   */
  async getGenerationOverview(
    params?: GenerationOverviewParams
  ): Promise<GenerationOverviewResponse> {
    const queryParams = new URLSearchParams()

    if (params?.days !== undefined) {
      queryParams.set('days', String(params.days))
    }

    const query = queryParams.toString()
    return this.api.get<GenerationOverviewResponse>(
      `/api/v1/analytics/generation/overview${query ? `?${query}` : ''}`
    )
  }

  /**
   * Get time-series trends for generation metrics.
   *
   * @param params Time range and granularity parameters
   * @returns Time-series generation data
   *
   * @example
   * ```ts
   * const trends = await analytics.getGenerationTrends({
   *   days: 7,
   *   interval: 'hourly'
   * })
   * ```
   */
  async getGenerationTrends(
    params?: GenerationTrendsParams
  ): Promise<GenerationTrendsResponse> {
    const queryParams = new URLSearchParams()

    if (params?.days !== undefined) {
      queryParams.set('days', String(params.days))
    }
    if (params?.interval !== undefined) {
      queryParams.set('interval', params.interval)
    }

    const query = queryParams.toString()
    return this.api.get<GenerationTrendsResponse>(
      `/api/v1/analytics/generation/trends${query ? `?${query}` : ''}`
    )
  }

  // ============================================================================
  // Tag Cardinality Methods
  // ============================================================================

  /**
   * Get most popular tags by content count.
   *
   * @param params Limit, filter, and threshold parameters
   * @returns List of popular tags with cardinality counts
   *
   * @example
   * ```ts
   * const tags = await analytics.getPopularTags({
   *   limit: 100,
   *   content_source: 'all',
   *   min_cardinality: 5
   * })
   * ```
   */
  async getPopularTags(params?: PopularTagsParams): Promise<PopularTagsResponse> {
    const queryParams = new URLSearchParams()

    if (params?.limit !== undefined) {
      queryParams.set('limit', String(params.limit))
    }
    if (params?.content_source !== undefined) {
      queryParams.set('content_source', params.content_source)
    }
    if (params?.min_cardinality !== undefined) {
      queryParams.set('min_cardinality', String(params.min_cardinality))
    }

    const query = queryParams.toString()
    return this.api.get<PopularTagsResponse>(
      `/api/v1/tags/popular${query ? `?${query}` : ''}`
    )
  }
}

// Export singleton instance using the global ApiClient
import { apiClient } from './api-client'
export const analyticsService = new AnalyticsService(apiClient)
