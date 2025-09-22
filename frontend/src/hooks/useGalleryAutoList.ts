import { useQuery } from '@tanstack/react-query'
import { galleryAutoService, type GalleryAutoListParams } from '../services'
import type { PaginatedResult, GalleryItem } from '../types/domain'

export const galleryAutoListQueryKey = (params: GalleryAutoListParams = {}) => ['gallery-auto', params]

export function useGalleryAutoList(params: GalleryAutoListParams = {}) {
  return useQuery<PaginatedResult<GalleryItem>>({
    queryKey: galleryAutoListQueryKey(params),
    queryFn: () => galleryAutoService.listGalleryAuto(params),
  })
}