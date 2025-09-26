import { useCallback, useMemo } from 'react'
import { useQueryCache, useCacheInvalidation } from './useQueryCache'
import { useComfyUIService } from './useComfyUIService'
import type {
  ComfyUIGenerationCreateRequest,
  ComfyUIGenerationListParams,
} from '../services/comfyui-service'

export function useCachedComfyUIService() {
  const comfyUIService = useComfyUIService()
  const { invalidateKey, invalidatePattern } = useCacheInvalidation()

  // Cached models list
  const {
    data: availableModels,
    loading: modelsLoading,
    error: modelsError,
    refetch: refetchModels,
  } = useQueryCache(
    'comfyui:models',
    () => comfyUIService.listAvailableModels({}),
    {
      ttl: 10 * 60 * 1000, // 10 minutes
      staleWhileRevalidate: true,
      backgroundRefresh: true,
    }
  )

  // Factory functions for generating cache keys
  const getGenerationsListCacheKey = useCallback((params: ComfyUIGenerationListParams) => {
    return `comfyui:generations:${JSON.stringify(params)}`
  }, [])

  const getGenerationCacheKey = useCallback((id: number) => {
    return `comfyui:generation:${id}`
  }, [])

  // Create generation with cache invalidation
  const createGeneration = useCallback(async (request: ComfyUIGenerationCreateRequest) => {
    const result = await comfyUIService.createGeneration(request)

    // Invalidate generations cache to show new generation
    invalidatePattern('comfyui:generations:.*')

    return result
  }, [comfyUIService, invalidatePattern])

  // Cancel generation with cache invalidation
  const cancelGeneration = useCallback(async (id: number) => {
    const result = await comfyUIService.cancelGeneration(id)

    // Invalidate specific generation and lists
    invalidateKey(`comfyui:generation:${id}`)
    invalidatePattern('comfyui:generations:.*')

    return result
  }, [comfyUIService, invalidateKey, invalidatePattern])


  // Prefetch function for background loading
  const prefetchGeneration = useCallback((id: number) => {
    const cacheKey = `comfyui:generation:${id}`
    // This will be handled by the query cache internally
    return cacheKey
  }, [])

  // Helper to invalidate all ComfyUI caches
  const invalidateAllCaches = useCallback(() => {
    invalidatePattern('comfyui:.*')
  }, [invalidatePattern])

  return {
    // Cached data
    availableModels: availableModels || { items: [], pagination: { page: 1, page_size: 50, total_count: 0, total_pages: 0 } },
    modelsLoading,
    modelsError,

    // Cache key generators
    getGenerationsListCacheKey,
    getGenerationCacheKey,

    // Actions with cache management
    createGeneration,
    cancelGeneration,
    refreshModels: refetchModels, // Use the cached version

    // Cache utilities
    prefetchGeneration,
    invalidateAllCaches,

    // Direct service access for non-cached operations
    getGeneration: comfyUIService.getGeneration,
    listGenerations: comfyUIService.listGenerations,
    listAvailableModels: comfyUIService.listAvailableModels,
  }
}

// Separate hooks for cached data access
export function useGenerationsList(params: ComfyUIGenerationListParams) {
  const { getGenerationsListCacheKey } = useCachedComfyUIService()
  const comfyUIService = useComfyUIService()

  const cacheKey = getGenerationsListCacheKey(params)

  return useQueryCache(
    cacheKey,
    () => comfyUIService.listGenerations(params),
    {
      ttl: 2 * 60 * 1000, // 2 minutes
      staleWhileRevalidate: true,
      backgroundRefresh: true,
    }
  )
}

export function useGeneration(id: number) {
  const { getGenerationCacheKey } = useCachedComfyUIService()
  const comfyUIService = useComfyUIService()

  const cacheKey = getGenerationCacheKey(id)

  return useQueryCache(
    cacheKey,
    () => comfyUIService.getGeneration(id),
    {
      ttl: 30 * 1000, // 30 seconds for active generations
      staleWhileRevalidate: true,
      backgroundRefresh: true,
    }
  )
}

// Hook specifically for generation polling with smart refresh intervals
export function useGenerationPolling(id: number, enabled = true) {
  const {
    data: generation,
    loading,
    error,
    refetch,
  } = useGeneration(id)

  // Smart polling based on generation status
  const pollInterval = useMemo(() => {
    if (!enabled || !generation) return null

    switch (generation.status) {
      case 'pending':
      case 'processing':
        return 2000 // Poll every 2 seconds for active generations
      case 'completed':
      case 'failed':
      case 'cancelled':
        return null // Don't poll completed generations
      default:
        return 5000 // Default 5 second polling
    }
  }, [enabled, generation])

  // Set up polling interval
  useMemo(() => {
    if (!pollInterval) return

    const interval = setInterval(() => {
      if (enabled) {
        refetch()
      }
    }, pollInterval)

    return () => clearInterval(interval)
  }, [pollInterval, enabled, refetch])

  return {
    generation,
    loading,
    error,
    refetch,
    isActive: generation?.status === 'pending' || generation?.status === 'processing',
  }
}