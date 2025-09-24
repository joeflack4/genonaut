import { ApiClient } from './api-client'
import type {
  ApiContentItem,
  ApiContentQueryParams,
  ApiPaginatedResponse,
  ApiEnhancedPaginatedResponse,
  ApiEnhancedContentQueryParams
} from '../types/api'
import type {
  GalleryItem,
  PaginatedResult,
  EnhancedPaginatedResult,
  ContentQueryParams
} from '../types/domain'

export type GalleryListParams = ApiContentQueryParams
export type EnhancedGalleryListParams = ContentQueryParams

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

  // ========================================
  // Enhanced pagination methods
  // ========================================

  /**
   * List gallery content using the enhanced pagination API
   */
  async listGalleryEnhanced(params: EnhancedGalleryListParams = {}): Promise<EnhancedPaginatedResult<GalleryItem>> {
    const searchParams = new URLSearchParams()

    // Enhanced pagination parameters
    if (params.page !== undefined) {
      searchParams.set('page', String(params.page))
    }

    if (params.pageSize !== undefined) {
      searchParams.set('page_size', String(params.pageSize))
    }

    if (params.cursor) {
      searchParams.set('cursor', params.cursor)
    }

    if (params.sortField) {
      searchParams.set('sort_field', params.sortField)
    }

    if (params.sortOrder) {
      searchParams.set('sort_order', params.sortOrder)
    }

    // Content filtering parameters
    if (params.contentType) {
      searchParams.set('content_type', params.contentType)
    }

    if (params.creatorId) {
      searchParams.set('creator_id', params.creatorId)
    }

    if (params.publicOnly !== undefined) {
      searchParams.set('public_only', String(params.publicOnly))
    }

    if (params.searchTerm) {
      searchParams.set('search_term', params.searchTerm)
    }

    const query = searchParams.toString()

    // Use the enhanced endpoint
    const response = await this.api.get<ApiEnhancedPaginatedResponse<ApiContentItem>>(
      `/api/v1/content/enhanced${query ? `?${query}` : ''}`
    )

    return {
      items: response.items.map(this.transformGalleryItem),
      pagination: {
        page: response.pagination.page,
        pageSize: response.pagination.page_size,
        totalCount: response.pagination.total_count,
        totalPages: response.pagination.total_pages,
        hasNext: response.pagination.has_next,
        hasPrevious: response.pagination.has_previous,
        nextCursor: response.pagination.next_cursor,
        prevCursor: response.pagination.prev_cursor
      }
    }
  }

  /**
   * Get content by creator using enhanced pagination
   */
  async getContentByCreatorEnhanced(
    creatorId: string,
    params: EnhancedGalleryListParams = {}
  ): Promise<EnhancedPaginatedResult<GalleryItem>> {
    return this.listGalleryEnhanced({
      ...params,
      creatorId
    })
  }

  /**
   * Get public content using enhanced pagination
   */
  async getPublicContentEnhanced(
    params: EnhancedGalleryListParams = {}
  ): Promise<EnhancedPaginatedResult<GalleryItem>> {
    return this.listGalleryEnhanced({
      ...params,
      publicOnly: true
    })
  }

  /**
   * Search content using enhanced pagination
   */
  async searchContentEnhanced(
    searchTerm: string,
    params: EnhancedGalleryListParams = {}
  ): Promise<EnhancedPaginatedResult<GalleryItem>> {
    return this.listGalleryEnhanced({
      ...params,
      searchTerm
    })
  }

  /**
   * Get content by type using enhanced pagination
   */
  async getContentByTypeEnhanced(
    contentType: string,
    params: EnhancedGalleryListParams = {}
  ): Promise<EnhancedPaginatedResult<GalleryItem>> {
    return this.listGalleryEnhanced({
      ...params,
      contentType
    })
  }

  /**
   * Get top-rated content using enhanced pagination
   */
  async getTopRatedContentEnhanced(
    params: EnhancedGalleryListParams = {}
  ): Promise<EnhancedPaginatedResult<GalleryItem>> {
    return this.listGalleryEnhanced({
      ...params,
      sortField: 'quality_score',
      sortOrder: 'desc'
    })
  }

  /**
   * Get recent content using enhanced pagination
   */
  async getRecentContentEnhanced(
    params: EnhancedGalleryListParams = {}
  ): Promise<EnhancedPaginatedResult<GalleryItem>> {
    return this.listGalleryEnhanced({
      ...params,
      sortField: 'created_at',
      sortOrder: 'desc'
    })
  }
}
