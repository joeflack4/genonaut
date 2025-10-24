/**
 * Analytics type definitions for route performance, generation metrics, and tag cardinality.
 *
 * These types correspond to the backend API responses from:
 * - /api/v1/analytics/routes/*
 * - /api/v1/analytics/generation/*
 * - /api/v1/tags/popular
 */

// ============================================================================
// Route Analytics Types
// ============================================================================

/**
 * System type for cache priority analysis.
 * - absolute: Uses static thresholds (production environments)
 * - relative: Uses percentile-based ranking (development environments)
 */
export type CacheAnalysisSystem = 'absolute' | 'relative'

/**
 * Individual route in cache priorities response (absolute system).
 */
export interface RouteCachePriorityAbsolute {
  route: string
  method: string
  query_params_normalized: Record<string, string> | null
  avg_hourly_requests: number
  avg_p95_latency_ms: number
  avg_unique_users: number
  success_rate: number
  total_requests: number
  cache_priority_score: number
}

/**
 * Individual route in cache priorities response (relative system).
 */
export interface RouteCachePriorityRelative {
  route: string
  method: string
  query_params_normalized: Record<string, string> | null
  avg_hourly_requests: number
  avg_p95_latency_ms: number
  avg_unique_users: number
  success_rate: number
  total_requests: number
  priority_score: number
  popularity_percentile: number
  latency_percentile: number
  user_percentile: number
}

/**
 * Union type for route cache priority (can be either absolute or relative).
 */
export type RouteCachePriority = RouteCachePriorityAbsolute | RouteCachePriorityRelative

/**
 * Response from GET /api/v1/analytics/routes/cache-priorities
 */
export interface CachePrioritiesResponse {
  system: CacheAnalysisSystem
  lookback_days: number
  routes: RouteCachePriority[]
  total_routes: number
}

/**
 * Query parameters for cache priorities endpoint.
 */
export interface CachePrioritiesParams {
  n?: number // Number of routes to return (1-100, default 10)
  days?: number // Days of history (1-90, default 7)
  system?: CacheAnalysisSystem // Analysis system (default 'absolute')
  min_requests?: number // Min avg requests/hour for absolute system (default 10)
  min_latency?: number // Min p95 latency for absolute system (default 100)
}

/**
 * Performance trend data point (hourly or daily).
 */
export interface PerformanceTrendDataPoint {
  timestamp: string // ISO 8601 format
  total_requests: number
  successful_requests: number
  client_errors: number
  server_errors: number
  avg_duration_ms: number | null
  p50_duration_ms: number | null
  p95_duration_ms: number | null
  p99_duration_ms: number | null
  unique_users: number | null
  success_rate: number | null
}

/**
 * Response from GET /api/v1/analytics/routes/performance-trends
 */
export interface PerformanceTrendsResponse {
  route: string
  granularity: 'hourly' | 'daily'
  lookback_days: number
  data_points: number
  trends: PerformanceTrendDataPoint[]
}

/**
 * Query parameters for performance trends endpoint.
 */
export interface PerformanceTrendsParams {
  route: string // Required: route to analyze
  days?: number // Days of history (1-90, default 7)
  granularity?: 'hourly' | 'daily' // Data granularity (default 'hourly')
}

/**
 * Peak hour analysis data point.
 */
export interface PeakHourDataPoint {
  route: string
  hour_of_day: number // 0-23
  avg_requests: number
  avg_p95_latency_ms: number | null
  avg_unique_users: number | null
  data_points: number // Number of observations
}

/**
 * Response from GET /api/v1/analytics/routes/peak-hours
 */
export interface PeakHoursResponse {
  route: string | null
  lookback_days: number
  min_requests_threshold: number
  total_patterns: number
  peak_hours: PeakHourDataPoint[]
}

/**
 * Query parameters for peak hours endpoint.
 */
export interface PeakHoursParams {
  route?: string // Optional: filter by specific route
  days?: number // Days of history (7-90, default 30)
  min_requests?: number // Min avg requests (default 50)
}

// ============================================================================
// Generation Analytics Types
// ============================================================================

/**
 * Response from GET /api/v1/analytics/generation/overview
 */
export interface GenerationOverviewResponse {
  lookback_days: number
  total_requests: number
  successful_generations: number
  failed_generations: number
  cancelled_generations: number
  success_rate_pct: number
  avg_duration_ms: number
  p50_duration_ms: number
  p95_duration_ms: number
  p99_duration_ms: number
  total_images_generated: number
  unique_users?: number
  avg_queue_length?: number
}

/**
 * Query parameters for generation overview endpoint.
 */
export interface GenerationOverviewParams {
  days?: number // Days of history (1-90, default 7)
}

/**
 * Generation trend data point (hourly or daily).
 */
export interface GenerationTrendDataPoint {
  timestamp: string // ISO 8601 format
  total_requests: number
  successful_generations: number
  failed_generations: number
  cancelled_generations: number
  success_rate_pct: number
  avg_duration_ms: number
  p95_duration_ms: number
  unique_users: number
  total_images_generated: number
}

/**
 * Response from GET /api/v1/analytics/generation/trends
 */
export interface GenerationTrendsResponse {
  interval: 'hourly' | 'daily'
  lookback_days: number
  total_data_points: number
  data_points: GenerationTrendDataPoint[]
}

/**
 * Query parameters for generation trends endpoint.
 */
export interface GenerationTrendsParams {
  days?: number // Days of history (1-90, default 7)
  interval?: 'hourly' | 'daily' // Data granularity (default 'hourly')
}

// ============================================================================
// Tag Cardinality Types
// ============================================================================

/**
 * Popular tag with cardinality count.
 */
export interface PopularTag {
  id: string
  name: string
  cardinality: number
}

/**
 * Response from GET /api/v1/tags/popular
 */
export type PopularTagsResponse = PopularTag[]

/**
 * Query parameters for popular tags endpoint.
 */
export interface PopularTagsParams {
  limit?: number // Max tags to return (1-10000, default 20)
  content_source?: string // Filter by 'regular' or 'auto' (optional)
  min_cardinality?: number // Minimum content count (default 1)
}

/**
 * Tag cardinality statistics (calculated client-side from popular tags data).
 */
export interface TagCardinalityStats {
  total_tags: number
  tags_with_content: number
  most_popular_tag: PopularTag | null
  median_cardinality: number
  p90_cardinality: number
}

/**
 * Histogram bucket for tag cardinality distribution.
 */
export interface CardinalityBucket {
  range: string // e.g., "1", "2-5", "6-10"
  min_cardinality: number
  max_cardinality: number
  tag_count: number
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * Filter state for route analytics section.
 */
export interface RouteAnalyticsFilters {
  system: CacheAnalysisSystem
  days: number
  topN: number
  minRequests: number
  minLatency: number
}

/**
 * Filter state for generation analytics section.
 */
export interface GenerationAnalyticsFilters {
  days: number
  interval: 'hourly' | 'daily'
}

/**
 * Preset options for top N selector.
 */
export type TopNPreset = 10 | 50 | 100 | 200 | 1000 | 'custom'

/**
 * Active tab in tag cardinality section.
 */
export type TagCardinalityTab = 'table' | 'visualization'

/**
 * Filter state for tag cardinality section.
 * Supports separate views for regular content (items) and auto-generated content (auto).
 * Tabbed interface with Table (default) and Visualization tabs.
 */
export interface TagCardinalityFilters {
  activeTab: TagCardinalityTab // Active tab ('table' or 'visualization')
  topNItems: TopNPreset // Top N selection for regular content
  topNAuto: TopNPreset // Top N selection for auto-generated content
  customLimitItems: number | null // Custom limit for items (1-1000) when topNItems is 'custom'
  customLimitAuto: number | null // Custom limit for auto (1-1000) when topNAuto is 'custom'
  minCardinality: number
  logScale: boolean
}

/**
 * Combined filter state for entire analytics page (for localStorage persistence).
 */
export interface AnalyticsPageFilters {
  route: RouteAnalyticsFilters
  generation: GenerationAnalyticsFilters
  tagCardinality: TagCardinalityFilters
}
