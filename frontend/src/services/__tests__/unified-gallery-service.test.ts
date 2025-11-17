import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { UnifiedGalleryService } from '../unified-gallery-service'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

// Create a mutable config object for testing
let mockFeaturesConfig = {
  PAGINATION: {
    USE_CURSOR_PAGINATION: false, // Default to offset mode
    DEFAULT_PAGE_SIZE: 50,
    MAX_PAGE_SIZE: 100,
  },
  VIRTUAL_SCROLLING: {
    ENABLED: false,
    PAGE_SIZE: 200,
  },
}

// Mock the features config
vi.mock('../../config/features', () => ({
  get FEATURES_CONFIG() {
    return mockFeaturesConfig
  },
}))

describe('UnifiedGalleryService', () => {
  let apiClient: ApiClient
  let service: UnifiedGalleryService

  beforeEach(() => {
    apiClient = new ApiClient()
    service = new UnifiedGalleryService(apiClient)
  })

  describe('Offset-based pagination mode (default)', () => {
    it('sends page parameter when no cursor provided', async () => {
      const responseBody = {
        items: [
          {
            id: 3000132,
            title: 'cat',
            content_type: 'image',
            content_data: null,
            path_thumb: '/thumb/cat.jpg',
            created_at: '2025-11-13T00:00:00Z',
            updated_at: '2025-11-13T00:00:00Z',
            creator_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            source_type: 'regular',
          },
        ],
        pagination: {
          page: 2,
          page_size: 50,
          total_count: 100,
          total_pages: 2,
          has_next: false,
          has_previous: true,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 2,
        pageSize: 50,
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('page')).toBe('2')
      expect(url.searchParams.get('page_size')).toBe('50')
      expect(url.searchParams.get('cursor')).toBeNull()
      expect(url.searchParams.get('backward')).toBeNull()
    })

    it('ignores cursor parameter in offset mode', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 3,
        pageSize: 25,
        cursor: 'should-be-ignored-in-offset-mode',
        backward: true,
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('page')).toBe('3')
      expect(url.searchParams.get('page_size')).toBe('25')
      expect(url.searchParams.get('cursor')).toBeNull()
      expect(url.searchParams.get('backward')).toBeNull()
    })

    it('handles content filters correctly', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 1,
        pageSize: 50,
        contentTypes: ['regular', 'auto'],
        creatorFilter: 'user',
        userId: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
        searchTerm: 'test',
        sortField: 'created_at',
        sortOrder: 'desc',
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('page')).toBe('1')
      expect(url.searchParams.get('content_types')).toBe('regular,auto')
      expect(url.searchParams.get('creator_filter')).toBe('user')
      expect(url.searchParams.get('user_id')).toBe('121e194b-4caa-4b81-ad4f-86ca3919d5b9')
      expect(url.searchParams.get('search_term')).toBe('test')
      expect(url.searchParams.get('sort_field')).toBe('created_at')
      expect(url.searchParams.get('sort_order')).toBe('desc')
    })

    it('transforms response data correctly', async () => {
      const responseBody = {
        items: [
          {
            id: 3000132,
            title: 'test image',
            description: 'test description',
            image_url: 'https://example.com/image.jpg',
            content_type: 'image',
            content_data: '{"test": "data"}',
            path_thumb: '/thumb/test.jpg',
            path_thumbs_alt_res: { '256': '/thumb/256/test.jpg' },
            quality_score: 0.95,
            created_at: '2025-11-13T00:00:00Z',
            updated_at: '2025-11-13T00:00:00Z',
            creator_id: '121e194b-4caa-4b81-ad4f-86ca3919d5b9',
            creator_username: 'testuser',
            source_type: 'regular',
            tags: ['tag1', 'tag2'],
            item_metadata: { key: 'value' },
            prompt: 'test prompt',
          },
        ],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 1,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        },
      }

      server.use(
        http.get('https://api.example.test/api/v1/content/unified', () => {
          return HttpResponse.json(responseBody)
        })
      )

      const result = await service.getUnifiedContent({ page: 1 })

      expect(result.items).toHaveLength(1)
      const item = result.items[0]
      expect(item.id).toBe(3000132)
      expect(item.title).toBe('test image')
      expect(item.description).toBe('test description')
      expect(item.imageUrl).toBe('https://example.com/image.jpg')
      expect(item.contentType).toBe('image')
      expect(item.contentData).toBe('{"test": "data"}')
      expect(item.pathThumb).toBe('/thumb/test.jpg')
      expect(item.pathThumbsAltRes).toEqual({ '256': '/thumb/256/test.jpg' })
      expect(item.qualityScore).toBe(0.95)
      expect(item.createdAt).toBe('2025-11-13T00:00:00Z')
      expect(item.updatedAt).toBe('2025-11-13T00:00:00Z')
      expect(item.creatorId).toBe('121e194b-4caa-4b81-ad4f-86ca3919d5b9')
      expect(item.creatorUsername).toBe('testuser')
      expect(item.sourceType).toBe('regular')
      expect(item.tags).toEqual(['tag1', 'tag2'])
      expect(item.itemMetadata).toEqual({ key: 'value' })
      expect(item.prompt).toBe('test prompt')
    })
  })

  describe('Cursor-based pagination mode', () => {
    beforeEach(() => {
      // Enable cursor mode for these tests
      mockFeaturesConfig = {
        PAGINATION: {
          USE_CURSOR_PAGINATION: true, // Enable cursor mode
          DEFAULT_PAGE_SIZE: 50,
          MAX_PAGE_SIZE: 100,
        },
        VIRTUAL_SCROLLING: {
          ENABLED: false,
          PAGE_SIZE: 200,
        },
      }
    })

    afterEach(() => {
      // Reset to default config
      mockFeaturesConfig = {
        PAGINATION: {
          USE_CURSOR_PAGINATION: false, // Back to offset mode
          DEFAULT_PAGE_SIZE: 50,
          MAX_PAGE_SIZE: 100,
        },
        VIRTUAL_SCROLLING: {
          ENABLED: false,
          PAGE_SIZE: 200,
        },
      }
    })

    it('sends cursor and backward parameters when cursor provided', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 2,
          page_size: 50,
          total_count: 100,
          total_pages: 2,
          has_next: false,
          has_previous: true,
          next_cursor: 'eyJpZCI6MzAwMDEwM30=',
          prev_cursor: 'eyJpZCI6MzAwMDEzMn0=',
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      // Need to recreate service to pick up config change
      const service = new UnifiedGalleryService(new ApiClient())
      await service.getUnifiedContent({
        cursor: 'eyJpZCI6MzAwMDEwM30=',
        backward: true,
        pageSize: 50,
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('cursor')).toBe('eyJpZCI6MzAwMDEwM30=')
      expect(url.searchParams.get('backward')).toBe('true')
      expect(url.searchParams.get('page')).toBeNull()
    })

    it('falls back to page when no cursor in cursor mode', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      // Need to recreate service to pick up config change
      const service = new UnifiedGalleryService(new ApiClient())
      await service.getUnifiedContent({
        page: 1,
        pageSize: 50,
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('page')).toBe('1')
      expect(url.searchParams.get('cursor')).toBeNull()
      expect(url.searchParams.get('backward')).toBeNull()
    })
  })

  describe('Content source types', () => {
    it('sends content source types when provided', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 1,
        contentSourceTypes: ['user-regular', 'community-auto'],
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      const sourceTypes = url.searchParams.getAll('content_source_types')
      expect(sourceTypes).toContain('user-regular')
      expect(sourceTypes).toContain('community-auto')
      expect(url.searchParams.get('content_types')).toBeNull()
      expect(url.searchParams.get('creator_filter')).toBeNull()
    })

    it('sends empty string for empty content source types array', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 1,
        contentSourceTypes: [],
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      const sourceTypes = url.searchParams.getAll('content_source_types')
      expect(sourceTypes).toEqual([''])
    })
  })

  describe('Stats functionality', () => {
    it('includes stats when requested', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
        stats: {
          user_regular_count: 10,
          user_auto_count: 20,
          community_regular_count: 30,
          community_auto_count: 40,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      const result = await service.getUnifiedContent({
        page: 1,
        includeStats: true,
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('include_stats')).toBe('true')

      expect(result.stats).toEqual({
        userRegularCount: 10,
        userAutoCount: 20,
        communityRegularCount: 30,
        communityAutoCount: 40,
      })
    })

    it('fetches stats separately', async () => {
      const responseBody = {
        user_regular_count: 15,
        user_auto_count: 25,
        community_regular_count: 35,
        community_auto_count: 45,
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/stats/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      const result = await service.getUnifiedStats('121e194b-4caa-4b81-ad4f-86ca3919d5b9')

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('user_id')).toBe('121e194b-4caa-4b81-ad4f-86ca3919d5b9')

      expect(result).toEqual({
        userRegularCount: 15,
        userAutoCount: 25,
        communityRegularCount: 35,
        communityAutoCount: 45,
      })
    })
  })

  describe('Tag filtering', () => {
    it('handles single tag parameter', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 1,
        tag: 'landscape',
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      expect(url.searchParams.get('tag')).toBe('landscape')
    })

    it('handles multiple tag parameters', async () => {
      const responseBody = {
        items: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        },
      }

      let capturedUrl: string | undefined
      server.use(
        http.get('https://api.example.test/api/v1/content/unified', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json(responseBody)
        })
      )

      await service.getUnifiedContent({
        page: 1,
        tag: ['landscape', 'nature', 'outdoor'],
      })

      expect(capturedUrl).toBeDefined()
      const url = new URL(capturedUrl!)
      const tags = url.searchParams.getAll('tag')
      expect(tags).toContain('landscape')
      expect(tags).toContain('nature')
      expect(tags).toContain('outdoor')
    })
  })
})