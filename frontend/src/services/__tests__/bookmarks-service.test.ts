import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { BookmarksService } from '../bookmarks-service'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

describe('BookmarksService', () => {
  let apiClient: ApiClient
  let service: BookmarksService

  beforeEach(() => {
    apiClient = new ApiClient()
    service = new BookmarksService(apiClient)
  })

  describe('transformBookmarkWithContent()', () => {
    it('should transform API bookmark to domain model', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: 'Test note',
                pinned: true,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  description: 'Test description',
                  image_url: '/path/to/image.jpg',
                  path_thumb: '/path/to/thumb.jpg',
                  path_thumbs_alt_res: { '184x272': '/path/184x272.jpg' },
                  content_data: 'data',
                  content_type: 'image',
                  prompt: 'test prompt',
                  quality_score: 0.85,
                  created_at: '2025-01-01T00:00:00Z',
                  updated_at: '2025-01-02T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: ['tag1', 'tag2'],
                },
                user_rating: 4,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0]).toEqual({
        id: 'bookmark-uuid',
        userId: 'user-uuid',
        contentId: 123,
        contentSourceType: 'items',
        note: 'Test note',
        pinned: true,
        isPublic: false,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
        content: {
          id: 123,
          title: 'Test Image',
          description: 'Test description',
          imageUrl: '/path/to/image.jpg',
          pathThumb: '/path/to/thumb.jpg',
          pathThumbsAltRes: { '184x272': '/path/184x272.jpg' },
          contentData: 'data',
          contentType: 'image',
          prompt: 'test prompt',
          qualityScore: 0.85,
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-02T00:00:00Z',
          creatorId: 'creator-uuid',
          creatorUsername: null,
          tags: ['tag1', 'tag2'],
          itemMetadata: null,
          sourceType: 'regular',
        },
        userRating: 4,
      })
    })

    it('should handle null content', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: null,
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content).toBeNull()
      expect(result.items[0].userRating).toBeNull()
    })

    it('should handle null user_rating', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  description: null,
                  image_url: null,
                  path_thumb: null,
                  path_thumbs_alt_res: null,
                  content_data: 'data',
                  content_type: 'image',
                  prompt: null,
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].userRating).toBeNull()
    })

    it('should transform content fields correctly (snake_case to camelCase)', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  description: 'desc',
                  image_url: '/image.jpg',
                  path_thumb: '/thumb.jpg',
                  path_thumbs_alt_res: { '184x272': '/path.jpg' },
                  content_data: 'data',
                  content_type: 'image',
                  prompt: 'prompt',
                  quality_score: 0.9,
                  created_at: '2025-01-01T00:00:00Z',
                  updated_at: '2025-01-02T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: ['tag'],
                },
                user_rating: 5,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0]).toMatchObject({
        userId: 'user-uuid',
        contentId: 123,
        contentSourceType: 'items',
        isPublic: false,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
        userRating: 5,
      })

      expect(result.items[0].content).toMatchObject({
        imageUrl: '/image.jpg',
        pathThumb: '/thumb.jpg',
        pathThumbsAltRes: { '184x272': '/path.jpg' },
        contentData: 'data',
        contentType: 'image',
        qualityScore: 0.9,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
        creatorId: 'creator-uuid',
      })
    })

    it('should set default values for missing optional fields', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  content_data: 'data',
                  content_type: 'image',
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content).toMatchObject({
        description: null,
        imageUrl: null,
        pathThumb: null,
        pathThumbsAltRes: null,
        prompt: null,
        qualityScore: null,
        creatorUsername: null,
        itemMetadata: null,
        sourceType: 'regular',
      })
    })
  })

  describe('transformContentItem()', () => {
    it('should handle null description, imageUrl, pathThumb', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  description: null,
                  image_url: null,
                  path_thumb: null,
                  content_data: 'data',
                  content_type: 'image',
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content?.description).toBeNull()
      expect(result.items[0].content?.imageUrl).toBeNull()
      expect(result.items[0].content?.pathThumb).toBeNull()
    })

    it('should default pathThumbsAltRes to null', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  content_data: 'data',
                  content_type: 'image',
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content?.pathThumbsAltRes).toBeNull()
    })

    it('should handle missing updatedAt (use createdAt as fallback)', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  content_data: 'data',
                  content_type: 'image',
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content?.updatedAt).toBe('2025-01-01T00:00:00Z')
    })

    it('should set creatorUsername to null (not in response)', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  content_data: 'data',
                  content_type: 'image',
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content?.creatorUsername).toBeNull()
    })

    it('should set sourceType to "regular"', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmarks', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 123,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
                content: {
                  id: 123,
                  title: 'Test Image',
                  content_data: 'data',
                  content_type: 'image',
                  quality_score: null,
                  created_at: '2025-01-01T00:00:00Z',
                  creator_id: 'creator-uuid',
                  tags: [],
                },
                user_rating: null,
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listBookmarks('user-uuid')

      expect(result.items[0].content?.sourceType).toBe('regular')
    })
  })

  describe('checkBookmarkStatusBatch()', () => {
    it('should return bookmark status for all bookmarked items', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', async ({ request }) => {
          const body = await request.json() as {
            content_items: Array<{ content_id: number; content_source_type: string }>
          }

          expect(body.content_items).toHaveLength(2)

          return HttpResponse.json({
            bookmarks: {
              '1001-items': {
                id: 'bookmark-1',
                user_id: 'user-uuid',
                content_id: 1001,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
              },
              '1002-items': {
                id: 'bookmark-2',
                user_id: 'user-uuid',
                content_id: 1002,
                content_source_type: 'items',
                note: 'Test note',
                pinned: true,
                is_public: false,
                created_at: '2025-01-02T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            },
          })
        })
      )

      const result = await service.checkBookmarkStatusBatch('user-uuid', [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
      ])

      expect(result).toEqual({
        '1001-items': {
          id: 'bookmark-1',
          userId: 'user-uuid',
          contentId: 1001,
          contentSourceType: 'items',
          note: null,
          pinned: false,
          isPublic: false,
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
        '1002-items': {
          id: 'bookmark-2',
          userId: 'user-uuid',
          contentId: 1002,
          contentSourceType: 'items',
          note: 'Test note',
          pinned: true,
          isPublic: false,
          createdAt: '2025-01-02T00:00:00Z',
          updatedAt: '2025-01-02T00:00:00Z',
        },
      })
    })

    it('should return null for unbookmarked items', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', () => {
          return HttpResponse.json({
            bookmarks: {
              '1001-items': null,
              '1002-items': null,
            },
          })
        })
      )

      const result = await service.checkBookmarkStatusBatch('user-uuid', [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
      ])

      expect(result).toEqual({
        '1001-items': null,
        '1002-items': null,
      })
    })

    it('should handle mixed bookmarked and unbookmarked items', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', () => {
          return HttpResponse.json({
            bookmarks: {
              '1001-items': {
                id: 'bookmark-1',
                user_id: 'user-uuid',
                content_id: 1001,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
              },
              '1002-items': null,
              '1003-auto': null,
            },
          })
        })
      )

      const result = await service.checkBookmarkStatusBatch('user-uuid', [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1002, contentSourceType: 'items' },
        { contentId: 1003, contentSourceType: 'auto' },
      ])

      expect(result).toEqual({
        '1001-items': {
          id: 'bookmark-1',
          userId: 'user-uuid',
          contentId: 1001,
          contentSourceType: 'items',
          note: null,
          pinned: false,
          isPublic: false,
          createdAt: '2025-01-01T00:00:00Z',
          updatedAt: '2025-01-01T00:00:00Z',
        },
        '1002-items': null,
        '1003-auto': null,
      })
    })

    it('should transform API bookmarks to domain Bookmarks correctly', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', () => {
          return HttpResponse.json({
            bookmarks: {
              '1001-items': {
                id: 'bookmark-uuid',
                user_id: 'user-uuid',
                content_id: 1001,
                content_source_type: 'items',
                note: 'Important note',
                pinned: true,
                is_public: true,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            },
          })
        })
      )

      const result = await service.checkBookmarkStatusBatch('user-uuid', [
        { contentId: 1001, contentSourceType: 'items' },
      ])

      expect(result['1001-items']).toMatchObject({
        id: 'bookmark-uuid',
        userId: 'user-uuid',
        contentId: 1001,
        contentSourceType: 'items',
        note: 'Important note',
        pinned: true,
        isPublic: true,
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
      })
    })

    it('should handle different content source types', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', () => {
          return HttpResponse.json({
            bookmarks: {
              '1001-items': {
                id: 'bookmark-items',
                user_id: 'user-uuid',
                content_id: 1001,
                content_source_type: 'items',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
              },
              '1001-auto': {
                id: 'bookmark-auto',
                user_id: 'user-uuid',
                content_id: 1001,
                content_source_type: 'auto',
                note: null,
                pinned: false,
                is_public: false,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
              },
            },
          })
        })
      )

      const result = await service.checkBookmarkStatusBatch('user-uuid', [
        { contentId: 1001, contentSourceType: 'items' },
        { contentId: 1001, contentSourceType: 'auto' },
      ])

      expect(result['1001-items']?.contentSourceType).toBe('items')
      expect(result['1001-auto']?.contentSourceType).toBe('auto')
      expect(result['1001-items']?.id).toBe('bookmark-items')
      expect(result['1001-auto']?.id).toBe('bookmark-auto')
    })

    it('should handle empty content items array', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', () => {
          return HttpResponse.json({
            bookmarks: {},
          })
        })
      )

      const result = await service.checkBookmarkStatusBatch('user-uuid', [])

      expect(result).toEqual({})
    })

    it('should send request to correct endpoint with user_id query param', async () => {
      let requestUrl = ''

      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', ({ request }) => {
          requestUrl = request.url
          return HttpResponse.json({
            bookmarks: {
              '1001-items': null,
            },
          })
        })
      )

      await service.checkBookmarkStatusBatch('test-user-123', [
        { contentId: 1001, contentSourceType: 'items' },
      ])

      expect(requestUrl).toContain('user_id=test-user-123')
    })

    it('should send content items with snake_case field names', async () => {
      let requestBody: unknown = null

      server.use(
        http.post('https://api.example.test/api/v1/bookmarks/check-batch', async ({ request }) => {
          requestBody = await request.json()
          return HttpResponse.json({
            bookmarks: {
              '1001-items': null,
            },
          })
        })
      )

      await service.checkBookmarkStatusBatch('user-uuid', [
        { contentId: 1001, contentSourceType: 'items' },
      ])

      expect(requestBody).toEqual({
        content_items: [
          {
            content_id: 1001,
            content_source_type: 'items',
          },
        ],
      })
    })
  })
})
