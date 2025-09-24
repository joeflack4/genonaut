import { galleryService } from '../services'
import { usePaginatedQuery, type UsePaginatedQueryOptions } from './usePaginatedQuery'
import type { GalleryItem, ContentQueryParams } from '../types/domain'

export interface UseEnhancedGalleryListOptions extends Omit<UsePaginatedQueryOptions<GalleryItem>, 'queryKey' | 'queryFn'> {
  filters?: Omit<ContentQueryParams, 'page' | 'pageSize' | 'cursor' | 'sortField' | 'sortOrder'>
}

export const enhancedGalleryListQueryKey = (params: ContentQueryParams, filters?: UseEnhancedGalleryListOptions['filters']) => [
  'enhanced-gallery',
  'list',
  { ...params, ...filters }
] as const

export function useEnhancedGalleryList(options: UseEnhancedGalleryListOptions = {}) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    queryKey: (params) => enhancedGalleryListQueryKey(params, filters),
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.listGalleryEnhanced(combinedParams)
    }
  })
}

export function useEnhancedGalleryByCreator(
  creatorId: string,
  options: UseEnhancedGalleryListOptions = {}
) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    queryKey: (params) => ['enhanced-gallery', 'by-creator', creatorId, { ...params, ...filters }],
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.getContentByCreatorEnhanced(creatorId, combinedParams)
    }
  })
}

export function useEnhancedPublicGallery(
  options: UseEnhancedGalleryListOptions = {}
) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    queryKey: (params) => ['enhanced-gallery', 'public', { ...params, ...filters }],
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.getPublicContentEnhanced(combinedParams)
    }
  })
}

export function useEnhancedGallerySearch(
  searchTerm: string,
  options: UseEnhancedGalleryListOptions = {}
) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    enabled: Boolean(searchTerm) && (options.enabled !== false),
    queryKey: (params) => ['enhanced-gallery', 'search', searchTerm, { ...params, ...filters }],
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.searchContentEnhanced(searchTerm, combinedParams)
    }
  })
}

export function useEnhancedGalleryByType(
  contentType: string,
  options: UseEnhancedGalleryListOptions = {}
) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    queryKey: (params) => ['enhanced-gallery', 'by-type', contentType, { ...params, ...filters }],
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.getContentByTypeEnhanced(contentType, combinedParams)
    }
  })
}

export function useEnhancedTopRatedGallery(
  options: UseEnhancedGalleryListOptions = {}
) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    queryKey: (params) => ['enhanced-gallery', 'top-rated', { ...params, ...filters }],
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.getTopRatedContentEnhanced(combinedParams)
    }
  })
}

export function useEnhancedRecentGallery(
  options: UseEnhancedGalleryListOptions = {}
) {
  const { filters, ...paginationOptions } = options

  return usePaginatedQuery({
    ...paginationOptions,
    queryKey: (params) => ['enhanced-gallery', 'recent', { ...params, ...filters }],
    queryFn: async (params) => {
      const combinedParams = { ...params, ...filters }
      return galleryService.getRecentContentEnhanced(combinedParams)
    }
  })
}