import { useQuery } from '@tanstack/react-query'
import { contentService } from '../services'

export interface ContentStats {
  userContentCount: number
  totalContentCount: number
}

export function useContentStats(userId: number) {
  return useQuery({
    queryKey: ['content-stats', userId],
    queryFn: async (): Promise<ContentStats> => {
      // Get user content count (content created by the user)
      const userContentResponse = await contentService.listContent({
        creator_id: userId,
        limit: 1  // We only need the total count, so minimal data
      })

      // Get total content count (all public content)
      const totalContentResponse = await contentService.listContent({
        limit: 1  // We only need the total count, so minimal data
      })

      return {
        userContentCount: userContentResponse.total,
        totalContentCount: totalContentResponse.total,
      }
    },
  })
}