import { useQuery } from '@tanstack/react-query'
import { unifiedGalleryService } from '../services'

export interface GalleryStats {
  userGalleryCount: number
  userAutoGalleryCount: number
  totalGalleryCount: number
  totalAutoGalleryCount: number
}

export function useGalleryStats(userId: string) {
  return useQuery({
    queryKey: ['gallery-stats', userId],
    queryFn: async (): Promise<GalleryStats> => {
      const stats = await unifiedGalleryService.getUnifiedStats(userId)

      return {
        userGalleryCount: stats.userRegularCount,
        userAutoGalleryCount: stats.userAutoCount,
        totalGalleryCount: stats.communityRegularCount,
        totalAutoGalleryCount: stats.communityAutoCount,
      }
    },
  })
}
