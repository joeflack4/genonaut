import { describe, it, expect, beforeEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { TagService } from '../tag-service'
import { ApiClient } from '../api-client'
import type { ApiTag, ApiTagHierarchy, ApiTagDetail, ApiEnhancedPaginatedResponse } from '../../types/api'

const BASE_URL = 'http://localhost:8001'

describe('TagService', () => {
  let tagService: TagService
  let apiClient: ApiClient

  beforeEach(() => {
    apiClient = new ApiClient()
    tagService = new TagService(apiClient)
  })

  describe('getTagHierarchy', () => {
    it('fetches tag hierarchy without ratings', async () => {
      const mockHierarchy: ApiTagHierarchy = {
        nodes: [
          { id: 'Art', name: 'Art', parent: null },
          { id: 'Digital Art', name: 'Digital Art', parent: 'Art' },
        ],
        metadata: {
          totalNodes: 2,
          totalRelationships: 1,
          rootCategories: 1,
          lastUpdated: '2025-01-01T00:00:00Z',
          format: 'flat_array',
          version: '2.0',
        },
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/hierarchy`, () => {
          return HttpResponse.json(mockHierarchy)
        })
      )

      const result = await tagService.getTagHierarchy()
      expect(result).toEqual(mockHierarchy)
      expect(result.nodes).toHaveLength(2)
      expect(result.metadata.version).toBe('2.0')
    })

    it('fetches tag hierarchy with ratings', async () => {
      const mockHierarchy: ApiTagHierarchy = {
        nodes: [
          { id: 'Art', name: 'Art', parent: null, average_rating: 4.5, rating_count: 10 },
        ],
        metadata: {
          totalNodes: 1,
          totalRelationships: 0,
          rootCategories: 1,
          lastUpdated: '2025-01-01T00:00:00Z',
          format: 'flat_array',
          version: '2.0',
        },
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/hierarchy`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('include_ratings')).toBe('true')
          return HttpResponse.json(mockHierarchy)
        })
      )

      const result = await tagService.getTagHierarchy(true)
      expect(result.nodes[0].average_rating).toBe(4.5)
      expect(result.nodes[0].rating_count).toBe(10)
    })
  })

  describe('getTagStatistics', () => {
    it('fetches tag statistics', async () => {
      const mockStats = {
        totalNodes: 127,
        totalRelationships: 123,
        rootCategories: 5,
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/statistics`, () => {
          return HttpResponse.json(mockStats)
        })
      )

      const result = await tagService.getTagStatistics()
      expect(result).toEqual(mockStats)
      expect(result.totalNodes).toBe(127)
    })
  })

  describe('getRootTags', () => {
    it('fetches root tags', async () => {
      const mockTags: ApiTag[] = [
        { id: '1', name: 'Art', metadata: {} },
        { id: '2', name: 'Science', metadata: {} },
      ]

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/roots`, () => {
          return HttpResponse.json(mockTags)
        })
      )

      const result = await tagService.getRootTags()
      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('Art')
    })
  })

  describe('listTags', () => {
    it('fetches paginated tags', async () => {
      const mockResponse: ApiEnhancedPaginatedResponse<ApiTag> = {
        items: [
          { id: '1', name: 'Tag 1', metadata: {}, created_at: '2025-01-01' },
          { id: '2', name: 'Tag 2', metadata: {}, created_at: '2025-01-02' },
        ],
        pagination: {
          page: 1,
          page_size: 20,
          total_count: 2,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        },
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('page')).toBe('1')
          expect(url.searchParams.get('page_size')).toBe('20')
          expect(url.searchParams.get('sort')).toBe('name-asc')
          return HttpResponse.json(mockResponse)
        })
      )

      const result = await tagService.listTags({ page: 1, page_size: 20, sort: 'name-asc' })
      expect(result.items).toHaveLength(2)
      expect(result.pagination.page).toBe(1)
    })
  })

  describe('searchTags', () => {
    it('searches tags by query', async () => {
      const mockResponse: ApiEnhancedPaginatedResponse<ApiTag> = {
        items: [
          { id: '1', name: 'Digital Art', metadata: {} },
        ],
        pagination: {
          page: 1,
          page_size: 20,
          total_count: 1,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        },
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/search`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('q')).toBe('art')
          return HttpResponse.json(mockResponse)
        })
      )

      const result = await tagService.searchTags({ q: 'art', page: 1, page_size: 20 })
      expect(result.items).toHaveLength(1)
      expect(result.items[0].name).toBe('Digital Art')
    })
  })

  describe('getTagDetail', () => {
    it('fetches tag detail without user context', async () => {
      const mockDetail: ApiTagDetail = {
        tag: { id: '1', name: 'Art', metadata: {} },
        parents: [],
        children: [
          { id: '2', name: 'Digital Art', metadata: {} },
        ],
        ancestors: [{ id: '10', name: 'Root', depth: 0 }],
        descendants: [],
        average_rating: 4.5,
        rating_count: 10,
        user_rating: null,
        is_favorite: false,
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/1`, () => {
          return HttpResponse.json(mockDetail)
        })
      )

      const result = await tagService.getTagDetail('1')
      expect(result.tag.name).toBe('Art')
      expect(result.children).toHaveLength(1)
      expect(result.is_favorite).toBe(false)
      expect(result.user_rating).toBeNull()
    })

    it('fetches tag detail with user context', async () => {
      const mockDetail: ApiTagDetail = {
        tag: { id: '1', name: 'Art', metadata: {} },
        parents: [],
        children: [],
        ancestors: [],
        descendants: [],
        average_rating: 4.5,
        rating_count: 10,
        user_rating: 5.0,
        is_favorite: true,
      }

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/1`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json(mockDetail)
        })
      )

      const result = await tagService.getTagDetail('1', 'user-123')
      expect(result.user_rating).toBe(5.0)
      expect(result.is_favorite).toBe(true)
    })
  })

  describe('getTagChildren', () => {
    it('fetches tag children', async () => {
      const mockChildren: ApiTag[] = [
        { id: '2', name: 'Digital Art', metadata: {} },
        { id: '3', name: 'Traditional Art', metadata: {} },
      ]

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/1/children`, () => {
          return HttpResponse.json(mockChildren)
        })
      )

      const result = await tagService.getTagChildren('1')
      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('Digital Art')
    })
  })

  describe('getTagParents', () => {
    it('fetches tag parents', async () => {
      const mockParents: ApiTag[] = [
        { id: '1', name: 'Art', metadata: {} },
      ]

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/2/parents`, () => {
          return HttpResponse.json(mockParents)
        })
      )

      const result = await tagService.getTagParents('2')
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Art')
    })
  })

  describe('rateTag', () => {
    it('submits a tag rating', async () => {
      const mockRating = {
        id: 1,
        user_id: 'user-123',
        tag_id: 'tag-1',
        rating: 4.5,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      server.use(
        http.post(`${BASE_URL}/api/v1/tags/tag-1/rate`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          expect(url.searchParams.get('rating')).toBe('4.5')
          return HttpResponse.json(mockRating)
        })
      )

      const result = await tagService.rateTag('tag-1', { user_id: 'user-123', rating: 4.5 })
      expect(result.rating).toBe(4.5)
      expect(result.user_id).toBe('user-123')
    })
  })

  describe('deleteTagRating', () => {
    it('deletes a tag rating', async () => {
      server.use(
        http.delete(`${BASE_URL}/api/v1/tags/tag-1/rate`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json({ success: true, message: 'Rating deleted successfully' })
        })
      )

      const result = await tagService.deleteTagRating('tag-1', 'user-123')
      expect(result.success).toBe(true)
      expect(result.message).toBe('Rating deleted successfully')
    })
  })

  describe('getUserTagRating', () => {
    it('fetches user tag rating', async () => {
      server.use(
        http.get(`${BASE_URL}/api/v1/tags/tag-1/rating`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json({ rating: 4.0 })
        })
      )

      const result = await tagService.getUserTagRating('tag-1', 'user-123')
      expect(result.rating).toBe(4.0)
    })

    it('returns null for unrated tag', async () => {
      server.use(
        http.get(`${BASE_URL}/api/v1/tags/tag-1/rating`, () => {
          return HttpResponse.json({ rating: null })
        })
      )

      const result = await tagService.getUserTagRating('tag-1', 'user-123')
      expect(result.rating).toBeNull()
    })
  })

  describe('getUserFavorites', () => {
    it('fetches user favorite tags', async () => {
      const mockFavorites: ApiTag[] = [
        { id: '1', name: 'Art', metadata: {} },
        { id: '2', name: 'Science', metadata: {} },
      ]

      server.use(
        http.get(`${BASE_URL}/api/v1/tags/favorites`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json(mockFavorites)
        })
      )

      const result = await tagService.getUserFavorites('user-123')
      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('Art')
    })
  })

  describe('addFavorite', () => {
    it('adds tag to favorites', async () => {
      server.use(
        http.post(`${BASE_URL}/api/v1/tags/tag-1/favorite`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json({ success: true, message: 'Tag added to favorites' })
        })
      )

      const result = await tagService.addFavorite('tag-1', { user_id: 'user-123' })
      expect(result.success).toBe(true)
      expect(result.message).toBe('Tag added to favorites')
    })
  })

  describe('removeFavorite', () => {
    it('removes tag from favorites', async () => {
      server.use(
        http.delete(`${BASE_URL}/api/v1/tags/tag-1/favorite`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json({ success: true, message: 'Tag removed from favorites' })
        })
      )

      const result = await tagService.removeFavorite('tag-1', { user_id: 'user-123' })
      expect(result.success).toBe(true)
      expect(result.message).toBe('Tag removed from favorites')
    })
  })

  describe('getUserTagRatings', () => {
    it('fetches multiple ratings for a user', async () => {
      server.use(
        http.get(`${BASE_URL}/api/v1/tags/ratings`, ({ request }) => {
          const url = new URL(request.url)
          expect(url.searchParams.getAll('tag_ids')).toEqual(['tag-1', 'tag-2'])
          expect(url.searchParams.get('user_id')).toBe('user-123')
          return HttpResponse.json({ ratings: { 'tag-1': 4.5 } })
        })
      )

      const result = await tagService.getUserTagRatings({ user_id: 'user-123', tag_ids: ['tag-1', 'tag-2'] })
      expect(result.ratings['tag-1']).toBe(4.5)
      expect(result.ratings['tag-2']).toBeUndefined()
    })
  })
})
