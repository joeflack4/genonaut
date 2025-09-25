import { useQuery } from '@tanstack/react-query'
import { recommendationService } from '../services'
import type { RecommendationItem } from '../types/domain'

export const recommendationsQueryKey = (userId: number) => ['recommendations', userId]

export function useRecommendations(userId: number, enabled: boolean = true) {
  return useQuery<RecommendationItem[]>({
    queryKey: recommendationsQueryKey(userId),
    queryFn: () => recommendationService.getUserRecommendations(String(userId)),
    enabled,
  })
}
