import { ApiClient } from './api-client'
import type { ApiContentItem, ApiContentQueryParams, ApiPaginatedResponse } from '../types/api'
import type { ContentItem, PaginatedResult } from '../types/domain'

export type ContentListParams = ApiContentQueryParams

export class ContentService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async listContent(params: ContentListParams = {}): Promise<PaginatedResult<ContentItem>> {
    const searchParams = new URLSearchParams()

    if (params.skip !== undefined) {
      searchParams.set('skip', String(params.skip))
    }

    if (params.limit !== undefined) {
      searchParams.set('limit', String(params.limit))
    }

    if (params.search) {
      searchParams.set('search', params.search)
    }

    if (params.sort) {
      searchParams.set('sort', params.sort)
    }

    const query = searchParams.toString()

    const response = await this.api.get<ApiPaginatedResponse<ApiContentItem>>(
      `/api/v1/content${query ? `?${query}` : ''}`
    )

    return {
      items: response.items.map(this.transformContentItem),
      total: response.total,
      limit: response.limit,
      skip: response.skip,
    }
  }

  private transformContentItem(item: ApiContentItem): ContentItem {
    return {
      id: item.id,
      title: item.title,
      description: item.description,
      imageUrl: item.image_url,
      qualityScore: item.quality_score,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
    }
  }
}
