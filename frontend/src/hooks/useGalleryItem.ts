import { useQuery } from '@tanstack/react-query'
import { galleryService } from '../services'
import type { GalleryItem } from '../types/domain'

export const galleryItemQueryKey = (id?: number, sourceType?: 'regular' | 'auto') =>
  ['gallery-item', id, sourceType] as const

export interface UseGalleryItemOptions {
  sourceType?: 'regular' | 'auto'
}

export function useGalleryItem(id?: number, options: UseGalleryItemOptions = {}) {
  const enabled = typeof id === 'number' && Number.isFinite(id)

  return useQuery<GalleryItem>({
    queryKey: galleryItemQueryKey(id, options.sourceType),
    queryFn: () => galleryService.getContentItem(id as number, options),
    enabled,
  })
}
