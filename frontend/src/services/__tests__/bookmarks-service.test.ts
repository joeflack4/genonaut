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
})
