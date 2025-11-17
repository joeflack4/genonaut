import { useQuery } from '@tanstack/react-query'
import { unifiedGalleryService } from '../services'
import type { UnifiedGalleryParams } from '../services/unified-gallery-service'

export function useUnifiedGallery(params: UnifiedGalleryParams = {}, enabled: boolean = true) {
  // Build a stable query key that changes when page/cursor changes
  // Include BOTH page and cursor in the key to ensure uniqueness
  const queryKey = ['unified-gallery', {
    ...params,
    // Ensure page is always in the key for proper cache separation
    _pageKey: params.cursor || params.page || 1,
  }]

  console.log('[useUnifiedGallery] Query key:', queryKey)

  return useQuery({
    queryKey,
    queryFn: async () => {
      console.log('[useUnifiedGallery] Fetching with params:', params)
      const result = await unifiedGalleryService.getUnifiedContent(params)
      console.log('[useUnifiedGallery] Received data:', {
        itemsCount: result.items?.length,
        firstItemId: result.items?.[0]?.id,
        firstItemPrompt: result.items?.[0]?.prompt?.substring(0, 50),
        nextCursor: result.nextCursor,
        prevCursor: result.prevCursor,
      })
      return result
    },
    enabled,
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
