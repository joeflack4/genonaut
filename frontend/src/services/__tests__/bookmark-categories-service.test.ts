import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { BookmarkCategoriesService } from '../bookmark-categories-service'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

describe('BookmarkCategoriesService', () => {
  let apiClient: ApiClient
  let service: BookmarkCategoriesService

  beforeEach(() => {
    apiClient = new ApiClient()
    service = new BookmarkCategoriesService(apiClient)
  })

  describe('transformCategory()', () => {
    it('should transform API category to domain model', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmark-categories', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'category-uuid',
                user_id: 'user-uuid',
                name: 'My Category',
                description: 'Category description',
                color: '#FF5733',
                icon: 'bookmark',
                cover_content_id: 456,
                cover_content_source_type: 'items',
                parent_id: 'parent-uuid',
                sort_index: 1,
                is_public: true,
                share_token: 'share-uuid',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listCategories('user-uuid')

      expect(result.items[0]).toEqual({
        id: 'category-uuid',
        userId: 'user-uuid',
        name: 'My Category',
        description: 'Category description',
        color: '#FF5733',
        icon: 'bookmark',
        coverContentId: 456,
        coverContentSourceType: 'items',
        parentId: 'parent-uuid',
        sortIndex: 1,
        isPublic: true,
        shareToken: 'share-uuid',
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
      })
    })

    it('should handle null description, color, icon', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmark-categories', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'category-uuid',
                user_id: 'user-uuid',
                name: 'My Category',
                description: null,
                color: null,
                icon: null,
                cover_content_id: null,
                cover_content_source_type: null,
                parent_id: null,
                sort_index: null,
                is_public: false,
                share_token: null,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listCategories('user-uuid')

      expect(result.items[0]).toMatchObject({
        description: null,
        color: null,
        icon: null,
      })
    })

    it('should handle null coverContentId, coverContentSourceType', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmark-categories', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'category-uuid',
                user_id: 'user-uuid',
                name: 'My Category',
                description: null,
                color: null,
                icon: null,
                cover_content_id: null,
                cover_content_source_type: null,
                parent_id: null,
                sort_index: null,
                is_public: false,
                share_token: null,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listCategories('user-uuid')

      expect(result.items[0].coverContentId).toBeNull()
      expect(result.items[0].coverContentSourceType).toBeNull()
    })

    it('should handle null parentId, sortIndex, shareToken', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmark-categories', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'category-uuid',
                user_id: 'user-uuid',
                name: 'My Category',
                description: null,
                color: null,
                icon: null,
                cover_content_id: null,
                cover_content_source_type: null,
                parent_id: null,
                sort_index: null,
                is_public: false,
                share_token: null,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listCategories('user-uuid')

      expect(result.items[0].parentId).toBeNull()
      expect(result.items[0].sortIndex).toBeNull()
      expect(result.items[0].shareToken).toBeNull()
    })

    it('should transform all fields correctly (snake_case to camelCase)', async () => {
      server.use(
        http.get('https://api.example.test/api/v1/bookmark-categories', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'category-uuid',
                user_id: 'user-uuid',
                name: 'My Category',
                description: 'desc',
                color: '#FF5733',
                icon: 'bookmark',
                cover_content_id: 456,
                cover_content_source_type: 'items',
                parent_id: 'parent-uuid',
                sort_index: 1,
                is_public: true,
                share_token: 'share-uuid',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-02T00:00:00Z',
              },
            ],
            total: 1,
            limit: 20,
            skip: 0,
          })
        })
      )

      const result = await service.listCategories('user-uuid')

      expect(result.items[0]).toMatchObject({
        userId: 'user-uuid',
        coverContentId: 456,
        coverContentSourceType: 'items',
        parentId: 'parent-uuid',
        sortIndex: 1,
        isPublic: true,
        shareToken: 'share-uuid',
        createdAt: '2025-01-01T00:00:00Z',
        updatedAt: '2025-01-02T00:00:00Z',
      })
    })
  })

  describe('createCategory() request transformation', () => {
    it('should transform domain model to API request format', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmark-categories', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>

          expect(body).toEqual({
            name: 'New Category',
            description: 'Category description',
            color: '#FF5733',
            icon: 'bookmark',
            parent_id: 'parent-uuid',
            is_public: true,
          })

          return HttpResponse.json({
            id: 'new-category-uuid',
            user_id: 'user-uuid',
            name: 'New Category',
            description: 'Category description',
            color: '#FF5733',
            icon: 'bookmark',
            cover_content_id: null,
            cover_content_source_type: null,
            parent_id: 'parent-uuid',
            sort_index: null,
            is_public: true,
            share_token: null,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          })
        })
      )

      await service.createCategory('user-uuid', {
        name: 'New Category',
        description: 'Category description',
        color: '#FF5733',
        icon: 'bookmark',
        parentId: 'parent-uuid',
        isPublic: true,
      })
    })

    it('should handle undefined optional fields', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmark-categories', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>

          expect(body).toEqual({
            name: 'New Category',
            description: undefined,
            color: undefined,
            icon: undefined,
            parent_id: undefined,
            is_public: false,
          })

          return HttpResponse.json({
            id: 'new-category-uuid',
            user_id: 'user-uuid',
            name: 'New Category',
            description: null,
            color: null,
            icon: null,
            cover_content_id: null,
            cover_content_source_type: null,
            parent_id: null,
            sort_index: null,
            is_public: false,
            share_token: null,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          })
        })
      )

      await service.createCategory('user-uuid', {
        name: 'New Category',
        isPublic: false,
      })
    })

    it('should convert camelCase to snake_case', async () => {
      server.use(
        http.post('https://api.example.test/api/v1/bookmark-categories', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>

          expect(body).toHaveProperty('parent_id')
          expect(body).toHaveProperty('is_public')
          expect(body).not.toHaveProperty('parentId')
          expect(body).not.toHaveProperty('isPublic')

          return HttpResponse.json({
            id: 'new-category-uuid',
            user_id: 'user-uuid',
            name: 'New Category',
            description: null,
            color: null,
            icon: null,
            cover_content_id: null,
            cover_content_source_type: null,
            parent_id: 'parent-uuid',
            sort_index: null,
            is_public: true,
            share_token: null,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          })
        })
      )

      await service.createCategory('user-uuid', {
        name: 'New Category',
        parentId: 'parent-uuid',
        isPublic: true,
      })
    })
  })

  describe('updateCategory() request transformation', () => {
    it('should transform partial update to API format', async () => {
      server.use(
        http.put('https://api.example.test/api/v1/bookmark-categories/category-uuid', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>

          expect(body).toEqual({
            name: 'Updated Name',
            description: null,
            color: null,
            icon: null,
            parent_id: null,
            sort_index: null,
            is_public: null,
          })

          return HttpResponse.json({
            id: 'category-uuid',
            user_id: 'user-uuid',
            name: 'Updated Name',
            description: null,
            color: null,
            icon: null,
            cover_content_id: null,
            cover_content_source_type: null,
            parent_id: null,
            sort_index: null,
            is_public: false,
            share_token: null,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          })
        })
      )

      await service.updateCategory('category-uuid', 'user-uuid', {
        name: 'Updated Name',
      })
    })

    it('should only include provided fields', async () => {
      server.use(
        http.put('https://api.example.test/api/v1/bookmark-categories/category-uuid', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>

          expect(body).toHaveProperty('name')
          expect(body).toHaveProperty('is_public')
          expect(Object.keys(body).length).toBe(7)  // name, description, color, icon, parent_id, sort_index, is_public

          return HttpResponse.json({
            id: 'category-uuid',
            user_id: 'user-uuid',
            name: 'Updated Name',
            description: null,
            color: null,
            icon: null,
            cover_content_id: null,
            cover_content_source_type: null,
            parent_id: null,
            sort_index: null,
            is_public: true,
            share_token: null,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          })
        })
      )

      await service.updateCategory('category-uuid', 'user-uuid', {
        name: 'Updated Name',
        isPublic: true,
      })
    })

    it('should handle undefined sortIndex', async () => {
      server.use(
        http.put('https://api.example.test/api/v1/bookmark-categories/category-uuid', async ({ request }) => {
          const body = await request.json() as Record<string, unknown>

          expect(body).toHaveProperty('sort_index')
          expect(body.sort_index).toBeNull()

          return HttpResponse.json({
            id: 'category-uuid',
            user_id: 'user-uuid',
            name: 'Updated Name',
            description: null,
            color: null,
            icon: null,
            cover_content_id: null,
            cover_content_source_type: null,
            parent_id: null,
            sort_index: null,
            is_public: false,
            share_token: null,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          })
        })
      )

      await service.updateCategory('category-uuid', 'user-uuid', {
        name: 'Updated Name',
      })
    })
  })
})
