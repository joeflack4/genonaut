import { ApiClient } from './api-client'
import type { GalleryItem, PaginatedResult } from '../types/domain'

export interface UnifiedGalleryParams {
  page?: number
  pageSize?: number
  contentTypes?: string[]
  creatorFilter?: 'all' | 'user' | 'community'
  contentSourceTypes?: string[]  // NEW: Preferred method - specific combinations like ['user-regular', 'community-auto']
  userId?: string
  searchTerm?: string
  sortField?: string
  sortOrder?: 'asc' | 'desc'
  tag?: string | string[]  // Tag filter - single tag or multiple tags
}

export interface UnifiedGalleryStats {
  userRegularCount: number
  userAutoCount: number
  communityRegularCount: number
  communityAutoCount: number
}

export interface UnifiedGalleryResult extends PaginatedResult<GalleryItem> {
  stats: UnifiedGalleryStats
}

export class UnifiedGalleryService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  async getUnifiedContent(params: UnifiedGalleryParams = {}): Promise<UnifiedGalleryResult> {
    const searchParams = new URLSearchParams()

    if (params.page !== undefined) {
      searchParams.set('page', String(params.page))
    }

    if (params.pageSize !== undefined) {
      searchParams.set('page_size', String(params.pageSize))
    }

    // NEW: Use contentSourceTypes if provided (preferred method)
    if (params.contentSourceTypes !== undefined) {
      // Send each content source type as a separate query parameter
      params.contentSourceTypes.forEach(cst => searchParams.append('content_source_types', cst))
    } else {
      // LEGACY: Use contentTypes and creatorFilter
      // Always set content_types parameter:
      // - If array is not empty, join with comma
      // - If array is empty, send empty string to get no results
      // - If undefined, don't send parameter (backend will default to 'regular,auto')
      if (params.contentTypes !== undefined) {
        searchParams.set('content_types', params.contentTypes.join(','))
      }

      if (params.creatorFilter) {
        searchParams.set('creator_filter', params.creatorFilter)
      }
    }

    if (params.userId) {
      searchParams.set('user_id', params.userId)
    }

    if (params.searchTerm) {
      searchParams.set('search_term', params.searchTerm)
    }

    if (params.sortField) {
      searchParams.set('sort_field', params.sortField)
    }

    if (params.sortOrder) {
      searchParams.set('sort_order', params.sortOrder)
    }

    if (params.tag) {
      if (Array.isArray(params.tag)) {
        // Add multiple tag parameters
        params.tag.forEach(tag => searchParams.append('tag', tag))
      } else {
        // Add single tag parameter
        searchParams.set('tag', params.tag)
      }
    }

    const query = searchParams.toString()

    const response = await this.api.get<{
      items: Array<{
        id: number
        title: string
        description?: string
        image_url?: string
        content_type: string
        content_data: string | null
        path_thumb?: string | null
        quality_score?: number
        created_at: string
        updated_at: string
        creator_id: string
        source_type: 'regular' | 'auto'
        tags?: string[]
        item_metadata?: Record<string, unknown>
      }>
      pagination: {
        page: number
        page_size: number
        total_count: number
        total_pages: number
        has_next: boolean
        has_previous: boolean
      }
      stats: {
        user_regular_count: number
        user_auto_count: number
        community_regular_count: number
        community_auto_count: number
      }
    }>(`/api/v1/content/unified${query ? `?${query}` : ''}`)

    return {
      items: response.items.map((item) => this.transformGalleryItem(item)),
      total: response.pagination.total_count,
      limit: response.pagination.page_size,
      skip: (response.pagination.page - 1) * response.pagination.page_size,
      stats: {
        userRegularCount: response.stats.user_regular_count,
        userAutoCount: response.stats.user_auto_count,
        communityRegularCount: response.stats.community_regular_count,
        communityAutoCount: response.stats.community_auto_count,
      },
    }
  }

  async getUnifiedStats(userId?: string): Promise<UnifiedGalleryStats> {
    const searchParams = new URLSearchParams()

    if (userId) {
      searchParams.set('user_id', userId)
    }

    const query = searchParams.toString()

    const response = await this.api.get<{
      user_regular_count: number
      user_auto_count: number
      community_regular_count: number
      community_auto_count: number
    }>(`/api/v1/content/stats/unified${query ? `?${query}` : ''}`)

    return {
      userRegularCount: response.user_regular_count,
      userAutoCount: response.user_auto_count,
      communityRegularCount: response.community_regular_count,
      communityAutoCount: response.community_auto_count,
    }
  }

  private transformGalleryItem(item: {
    id: number
    title: string
    description?: string
    image_url?: string
    content_type: string
    content_data: string | null
    path_thumb?: string | null
    path_thumbs_alt_res?: Record<string, string> | null
    quality_score?: number
    created_at: string
    updated_at: string
    creator_id: string
    source_type: 'regular' | 'auto'
    tags?: string[]
    item_metadata?: Record<string, unknown>
    creator_username?: string | null
    prompt?: string | null
  }): GalleryItem {
    return {
      id: item.id,
      title: item.title,
      description: item.description ?? null,
      imageUrl: item.image_url ?? null,
      pathThumb: item.path_thumb ?? null,
      pathThumbsAltRes: item.path_thumbs_alt_res ?? null,
      contentData: item.content_data ?? null,
      contentType: item.content_type,
      prompt: item.prompt ?? null,
      qualityScore: item.quality_score,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      creatorId: item.creator_id,
       creatorUsername: item.creator_username ?? null,
      tags: item.tags ?? [],
      itemMetadata: item.item_metadata ?? null,
      sourceType: item.source_type,
    }
  }
}
