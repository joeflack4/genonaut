import { useMutation, useQueryClient } from '@tanstack/react-query'
import { recommendationService } from '../services'
import { recommendationsQueryKey } from './useRecommendations'

export function useServeRecommendation(userId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (recommendationId: number) =>
      recommendationService.markRecommendationServed(recommendationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: recommendationsQueryKey(userId) })
    },
  })
}
