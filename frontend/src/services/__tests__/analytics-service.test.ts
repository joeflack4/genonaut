import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { AnalyticsService } from '../analytics-service'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

describe('AnalyticsService', () => {
  let apiClient: ApiClient
  let service: AnalyticsService

  beforeEach(() => {
    apiClient = new ApiClient()
    service = new AnalyticsService(apiClient)
  })

  describe('getRouteCachePriorities', () => {
    it('fetches cache priorities with all parameters', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/routes/cache-priorities', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('n')).toBe('10')
          expect(url.searchParams.get('days')).toBe('7')
          expect(url.searchParams.get('system')).toBe('absolute')
          expect(url.searchParams.get('min_requests')).toBe('5')
          expect(url.searchParams.get('min_latency')).toBe('100')

          return HttpResponse.json({
            system: 'absolute',
            lookback_days: 7,
            total_routes: 1,
            routes: [
              {
                route: '/api/v1/content/unified',
                method: 'GET',
                query_params_normalized: {},
                avg_hourly_requests: 50,
                avg_p95_latency_ms: 150,
                avg_unique_users: 10,
                success_rate: 0.99,
                total_requests: 500,
                cache_priority_score: 500,
              },
            ],
          })
        })
      )

      const result = await service.getRouteCachePriorities({
        n: 10,
        days: 7,
        system: 'absolute',
        min_requests: 5,
        min_latency: 100,
      })

      expect(result.system).toBe('absolute')
      expect(result.lookback_days).toBe(7)
      expect(result.routes).toHaveLength(1)
      expect(result.routes[0].route).toBe('/api/v1/content/unified')
    })

    it('fetches cache priorities without parameters', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/routes/cache-priorities', ({ request }) => {
          const url = new URL(request.url)
          expect(url.search).toBe('') // No query params

          return HttpResponse.json({
            system: 'absolute',
            lookback_days: 7,
            total_routes: 0,
            routes: [],
          })
        })
      )

      const result = await service.getRouteCachePriorities()

      expect(result.routes).toEqual([])
    })

    it('handles relative system correctly', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/routes/cache-priorities', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('system')).toBe('relative')

          return HttpResponse.json({
            system: 'relative',
            lookback_days: 14,
            total_routes: 1,
            routes: [
              {
                route: '/api/v1/users/profile',
                method: 'GET',
                query_params_normalized: {},
                avg_hourly_requests: 25,
                avg_p95_latency_ms: 200,
                avg_unique_users: 5,
                success_rate: 0.98,
                total_requests: 350,
                priority_score: 85.5,
                popularity_percentile: 90,
                latency_percentile: 80,
                user_percentile: 95,
              },
            ],
          })
        })
      )

      const result = await service.getRouteCachePriorities({
        system: 'relative',
        days: 14,
      })

      expect(result.system).toBe('relative')
      expect(result.routes[0].priority_score).toBe(85.5)
    })
  })

  describe('getPerformanceTrends', () => {
    it('fetches performance trends for a route', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/routes/performance-trends', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('route')).toBe('/api/v1/content/unified')
          expect(url.searchParams.get('days')).toBe('30')
          expect(url.searchParams.get('granularity')).toBe('daily')

          return HttpResponse.json({
            route: '/api/v1/content/unified',
            granularity: 'daily',
            lookback_days: 30,
            trends: [
              {
                timestamp: '2024-01-01T00:00:00Z',
                requests: 100,
                p95_latency_ms: 150,
                unique_users: 20,
                success_rate: 0.99,
              },
            ],
          })
        })
      )

      const result = await service.getPerformanceTrends({
        route: '/api/v1/content/unified',
        days: 30,
        granularity: 'daily',
      })

      expect(result.route).toBe('/api/v1/content/unified')
      expect(result.trends).toHaveLength(1)
      expect(result.trends[0].requests).toBe(100)
    })
  })

  describe('getPeakHours', () => {
    it('fetches peak hours for all routes', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/routes/peak-hours', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('days')).toBe('30')

          return HttpResponse.json({
            lookback_days: 30,
            peak_hours: [
              {
                hour: 14,
                requests: 500,
                unique_routes: 10,
              },
            ],
          })
        })
      )

      const result = await service.getPeakHours({ days: 30 })

      expect(result.lookback_days).toBe(30)
      expect(result.peak_hours).toHaveLength(1)
      expect(result.peak_hours[0].hour).toBe(14)
    })

    it('fetches peak hours for specific route', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/routes/peak-hours', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('route')).toBe('/api/v1/content/unified')

          return HttpResponse.json({
            lookback_days: 7,
            route: '/api/v1/content/unified',
            peak_hours: [
              {
                hour: 10,
                requests: 200,
              },
            ],
          })
        })
      )

      const result = await service.getPeakHours({
        route: '/api/v1/content/unified',
        days: 7,
      })

      expect(result.route).toBe('/api/v1/content/unified')
    })
  })

  describe('getGenerationOverview', () => {
    it('fetches generation overview with days parameter', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/generation/overview', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('days')).toBe('7')

          return HttpResponse.json({
            lookback_days: 7,
            total_requests: 150,
            successful_generations: 145,
            failed_generations: 3,
            cancelled_generations: 2,
            success_rate_pct: 96.67,
            avg_duration_ms: 5000,
            p50_duration_ms: 4500,
            p95_duration_ms: 7000,
            p99_duration_ms: 9000,
            total_images_generated: 145,
            unique_users: 25,
            hours_with_data: 168,
            latest_data_timestamp: '2024-01-07T23:59:59Z',
          })
        })
      )

      const result = await service.getGenerationOverview({ days: 7 })

      expect(result.lookback_days).toBe(7)
      expect(result.total_requests).toBe(150)
      expect(result.success_rate_pct).toBe(96.67)
      expect(result.unique_users).toBe(25)
    })

    it('fetches generation overview without parameters', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/generation/overview', ({ request }) => {
          const url = new URL(request.url)
          expect(url.search).toBe('')

          return HttpResponse.json({
            lookback_days: 7,
            total_requests: 0,
            successful_generations: 0,
            failed_generations: 0,
            cancelled_generations: 0,
            success_rate_pct: 0,
            avg_duration_ms: null,
            p50_duration_ms: null,
            p95_duration_ms: null,
            p99_duration_ms: null,
            total_images_generated: 0,
            hours_with_data: 0,
            latest_data_timestamp: null,
          })
        })
      )

      const result = await service.getGenerationOverview()

      expect(result.total_requests).toBe(0)
    })
  })

  describe('getGenerationTrends', () => {
    it('fetches generation trends with all parameters', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/analytics/generation/trends', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('days')).toBe('30')
          expect(url.searchParams.get('interval')).toBe('hourly')

          return HttpResponse.json({
            lookback_days: 30,
            interval: 'hourly',
            data_points: [
              {
                timestamp: '2024-01-01T00:00:00Z',
                requests: 10,
                successful: 9,
                failed: 1,
                cancelled: 0,
                avg_duration_ms: 4800,
              },
            ],
          })
        })
      )

      const result = await service.getGenerationTrends({
        days: 30,
        interval: 'hourly',
      })

      expect(result.interval).toBe('hourly')
      expect(result.data_points).toHaveLength(1)
      expect(result.data_points[0].requests).toBe(10)
    })
  })

  describe('getPopularTags', () => {
    it('fetches popular tags with all parameters', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/tags/popular', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('limit')).toBe('100')
          expect(url.searchParams.get('content_source')).toBe('all')
          expect(url.searchParams.get('min_cardinality')).toBe('5')

          return HttpResponse.json([
            {
              id: '1',
              name: 'landscape',
              cardinality: 150,
              created_at: '2024-01-01T00:00:00Z',
            },
            {
              id: '2',
              name: 'abstract',
              cardinality: 120,
              created_at: '2024-01-01T00:00:00Z',
            },
          ])
        })
      )

      const result = await service.getPopularTags({
        limit: 100,
        content_source: 'all',
        min_cardinality: 5,
      })

      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('landscape')
      expect(result[0].cardinality).toBe(150)
    })

    it('fetches popular tags without parameters', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/tags/popular', ({ request }) => {
          const url = new URL(request.url)
          expect(url.search).toBe('')

          return HttpResponse.json([])
        })
      )

      const result = await service.getPopularTags()

      expect(result).toEqual([])
    })

    it('filters by content source', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/tags/popular', ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('content_source')).toBe('items')

          return HttpResponse.json([
            {
              id: '1',
              name: 'user-tag',
              cardinality: 50,
              created_at: '2024-01-01T00:00:00Z',
            },
          ])
        })
      )

      const result = await service.getPopularTags({
        content_source: 'items',
      })

      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('user-tag')
    })
  })
})
