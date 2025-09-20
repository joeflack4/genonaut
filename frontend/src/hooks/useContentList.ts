import { useQuery } from '@tanstack/react-query'
import { contentService, type ContentListParams } from '../services'
import type { PaginatedResult, ContentItem } from '../types/domain'

export const contentListQueryKey = (params: ContentListParams = {}) => ['content', params]

export function useContentList(params: ContentListParams = {}) {
  return useQuery<PaginatedResult<ContentItem>>({
    queryKey: contentListQueryKey(params),
    queryFn: () => contentService.listContent(params),
  })
}
