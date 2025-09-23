import { ApiClient } from './api-client'
import type { ApiRecommendationItem } from '../types/api'
import type { RecommendationItem } from '../types/domain'

export class RecommendationService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async getUserRecommendations(userId: string): Promise<RecommendationItem[]> {
    const recommendations = await this.api.get<ApiRecommendationItem[]>(
      `/api/v1/users/${userId}/recommendations`
    )

    return recommendations.map(this.transformRecommendation)
  }

  async markRecommendationServed(recommendationId: number): Promise<RecommendationItem> {
    const updated = await this.api.post<ApiRecommendationItem, { recommendation_id: number }>(
      '/api/v1/recommendations/served',
      {
        recommendation_id: recommendationId,
      }
    )

    return this.transformRecommendation(updated)
  }

  private transformRecommendation(item: ApiRecommendationItem): RecommendationItem {
    return {
      id: item.id,
      userId: item.user_id,
      contentId: item.content_id,
      algorithm: item.algorithm,
      score: item.score,
      servedAt: item.served_at,
      createdAt: item.created_at,
    }
  }
}
