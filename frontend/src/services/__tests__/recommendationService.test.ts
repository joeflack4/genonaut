import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { RecommendationService } from '../recommendation-service'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

describe('RecommendationService', () => {
it('fetches recommendations for a user', async () => {
  const service = new RecommendationService(new ApiClient())

  server.use(
      http.get('https://api.example.test/api/v1/users/1/recommendations', () =>
        HttpResponse.json([
          {
            id: 7,
            user_id: 1,
            content_id: 42,
            algorithm: 'collaborative',
            score: 0.81,
            served_at: null,
            created_at: '2024-01-01T00:00:00Z',
          },
        ])
      )
    )

  const result = await service.getUserRecommendations(1)

    expect(result).toEqual([
      {
        id: 7,
        userId: 1,
        contentId: 42,
        algorithm: 'collaborative',
        score: 0.81,
        servedAt: null,
        createdAt: '2024-01-01T00:00:00Z',
      },
    ])
  })

it('marks a recommendation as served', async () => {
  const service = new RecommendationService(new ApiClient())
  const servedAt = '2024-01-03T12:00:00Z'

    server.use(
      http.post('https://api.example.test/api/v1/recommendations/served', async ({ request }) => {
        const payload = await request.json()
        expect(payload).toEqual({ recommendation_id: 7 })

        return HttpResponse.json({
          id: 7,
          user_id: 1,
          content_id: 42,
          algorithm: 'collaborative',
          score: 0.81,
          served_at: servedAt,
          created_at: '2024-01-01T00:00:00Z',
        })
      })
    )

    const updated = await service.markRecommendationServed(7)

    expect(updated.servedAt).toBe(servedAt)
  })
})
