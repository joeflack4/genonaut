import { useQuery } from '@tanstack/react-query'
import { galleryService, type GalleryListParams } from '../services'
import type { PaginatedResult, GalleryItem } from '../types/domain'

export const galleryListQueryKey = (params: GalleryListParams = {}) => ['gallery', params]

export function useGalleryList(params: GalleryListParams = {}) {
  return useQuery<PaginatedResult<GalleryItem>>({
    queryKey: galleryListQueryKey(params),
    queryFn: () => galleryService.listGallery(params),
  })
}
