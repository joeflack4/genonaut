import { useQuery } from '@tanstack/react-query'
import { unifiedGalleryService } from '../services'
import type { UnifiedGalleryParams } from '../services/unified-gallery-service'

export function useUnifiedGallery(params: UnifiedGalleryParams = {}) {
  return useQuery({
    queryKey: ['unified-gallery', params],
    queryFn: () => unifiedGalleryService.getUnifiedContent(params),
    staleTime: 30000, // 30 seconds
    gcTime: 300000, // 5 minutes
    retry: false,
  })
}

export function useUnifiedGalleryStats(userId?: string) {
  return useQuery({
    queryKey: ['unified-gallery-stats', userId],
    queryFn: () => unifiedGalleryService.getUnifiedStats(userId),
    staleTime: 60000, // 1 minute
    gcTime: 300000, // 5 minutes
  })
}
