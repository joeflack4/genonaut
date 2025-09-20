import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { ContentService } from '../content-service'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

describe('ContentService', () => {
  it('fetches paginated content with filters', async () => {
    const apiClient = new ApiClient()
    const service = new ContentService(apiClient)

    server.use(
      http.get('https://api.example.test/api/v1/content', ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('skip')).toBe('10')
        expect(url.searchParams.get('limit')).toBe('5')
        expect(url.searchParams.get('search')).toBe('abstract')

        return HttpResponse.json({
          items: [
            {
              id: 42,
              title: 'Abstract Sunrise',
              description: 'AI generated art',
              image_url: 'https://example.test/image.png',
              quality_score: 0.92,
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-02T00:00:00Z',
            },
          ],
          total: 1,
          limit: 5,
          skip: 10,
        })
      })
    )

    const result = await service.listContent({ skip: 10, limit: 5, search: 'abstract' })

    expect(result).toEqual({
      items: [
        {
          id: 42,
          title: 'Abstract Sunrise',
          description: 'AI generated art',
          imageUrl: 'https://example.test/image.png',
          qualityScore: 0.92,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-02T00:00:00Z',
        },
      ],
      total: 1,
      limit: 5,
      skip: 10,
    })
  })
})
