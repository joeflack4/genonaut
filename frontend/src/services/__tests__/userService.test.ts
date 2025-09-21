import { http, HttpResponse } from 'msw'
import { server } from '../../test/server'
import { ApiClient } from '../api-client'
import { UserService } from '../user-service'

vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test')

describe('UserService', () => {
  it('fetches the current user', async () => {
    const responseBody = {
      id: 1,
      name: 'Admin',
      email: 'admin@example.com',
      is_active: true,
    }

    server.use(
      http.get('https://api.example.test/api/v1/users/1', () => HttpResponse.json(responseBody))
    )

    const apiClient = new ApiClient()
    const service = new UserService(apiClient)

    const result = await service.getCurrentUser()

    expect(result).toMatchObject({
      id: 1,
      name: 'Admin',
      email: 'admin@example.com',
      isActive: true,
    })
  })

  it('fetches user stats', async () => {
    server.use(
      http.get('https://api.example.test/api/v1/users/1/stats', () =>
        HttpResponse.json({
          total_recommendations: 10,
          served_recommendations: 4,
          generated_content: 6,
          last_active_at: '2024-01-10T12:00:00Z',
        })
      )
    )

    const apiClient = new ApiClient()
    const service = new UserService(apiClient)

    const stats = await service.getUserStats(1)

    expect(stats).toEqual({
      totalRecommendations: 10,
      servedRecommendations: 4,
      generatedContent: 6,
      lastActiveAt: '2024-01-10T12:00:00Z',
    })
  })

  it('updates user profile', async () => {
    server.use(
      http.put('https://api.example.test/api/v1/users/1', async ({ request }) => {
        const payload = await request.json()
        expect(payload).toEqual({ name: 'Updated Admin' })

        return HttpResponse.json({
          id: 1,
          name: 'Updated Admin',
          email: 'admin@example.com',
          is_active: true,
        })
      })
    )

    const apiClient = new ApiClient()
    const service = new UserService(apiClient)

    const updated = await service.updateUser(1, { name: 'Updated Admin' })

    expect(updated.name).toBe('Updated Admin')
  })
})
