import { ApiClient } from './api-client'
import type { ApiContentItem, ApiContentQueryParams, ApiPaginatedResponse } from '../types/api'
import type { GalleryItem, PaginatedResult } from '../types/domain'

export type GalleryListParams = ApiContentQueryParams

export class GalleryService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async listGallery(params: GalleryListParams = {}): Promise<PaginatedResult<GalleryItem>> {
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

    if (params.creator_id !== undefined) {
      searchParams.set('creator_id', String(params.creator_id))
    }

    const query = searchParams.toString()

    const response = await this.api.get<ApiPaginatedResponse<ApiContentItem>>(
      `/api/v1/content${query ? `?${query}` : ''}`
    )

    return {
      items: response.items.map(this.transformGalleryItem),
      total: response.total,
      limit: response.limit,
      skip: response.skip,
    }
  }

  private transformGalleryItem(item: ApiContentItem): GalleryItem {
    return {
      id: item.id,
      title: item.title,
      description: item.description ?? null,
      imageUrl: item.image_url ?? null,
      qualityScore: item.quality_score,
      createdAt: item.created_at,
      updatedAt: item.updated_at ?? item.created_at,
      creatorId: item.creator_id,
    }
  }
}
