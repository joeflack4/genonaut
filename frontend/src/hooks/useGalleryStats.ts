import { useQuery } from '@tanstack/react-query'
import { galleryService } from '../services'

export interface GalleryStats {
  userGalleryCount: number
  totalGalleryCount: number
}

export function useGalleryStats(userId: number) {
  return useQuery({
    queryKey: ['gallery-stats', userId],
    queryFn: async (): Promise<GalleryStats> => {
      // Get gallery items created by the current user
      const userGalleryResponse = await galleryService.listGallery({
        creator_id: userId,
        limit: 1,
      })

      // Get total gallery items available to the community
      const totalGalleryResponse = await galleryService.listGallery({
        limit: 1,
      })

      return {
        userGalleryCount: userGalleryResponse.total,
        totalGalleryCount: totalGalleryResponse.total,
      }
    },
  })
}
