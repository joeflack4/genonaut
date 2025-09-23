import { ApiClient } from './api-client'
import type { ApiUser, ApiUserStats, ApiUserUpdateRequest } from '../types/api'
import type { User, UserStats } from '../types/domain'
import { ADMIN_USER_ID } from '../constants/config'

const CURRENT_USER_ID = ADMIN_USER_ID

export class UserService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async getUser(id: string): Promise<User> {
    const apiUser = await this.api.get<ApiUser>(`/api/v1/users/${id}`)
    return this.transformUser(apiUser)
  }

  async getCurrentUser(): Promise<User> {
    return this.getUser(CURRENT_USER_ID)
  }

  async getUserStats(id: string): Promise<UserStats> {
    const stats = await this.api.get<ApiUserStats>(`/api/v1/users/${id}/stats`)
    return this.transformStats(stats)
  }

  async updateUser(id: string, payload: ApiUserUpdateRequest): Promise<User> {
    const apiUser = await this.api.put<ApiUser, ApiUserUpdateRequest>(`/api/v1/users/${id}`, payload)
    return this.transformUser(apiUser)
  }

  private transformUser(apiUser: ApiUser): User {
    return {
      id: apiUser.id,
      name: apiUser.name,
      email: apiUser.email,
      isActive: apiUser.is_active,
      avatarUrl: apiUser.avatar_url ?? null,
      createdAt: apiUser.created_at,
      updatedAt: apiUser.updated_at,
    }
  }

  private transformStats(apiStats: ApiUserStats): UserStats {
    return {
      totalRecommendations: apiStats.total_recommendations,
      servedRecommendations: apiStats.served_recommendations,
      generatedContent: apiStats.generated_content,
      lastActiveAt: apiStats.last_active_at,
    }
  }
}
