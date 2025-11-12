import { ApiClient } from './api-client'
import type {
  ApiBookmarkWithContent,
  ApiBookmarkListResponse,
  ApiBookmarkQueryParams
} from '../types/api'
import type {
  BookmarkWithContent,
  PaginatedResult,
  BookmarkQueryParams,
  GalleryItem
} from '../types/domain'

export class BookmarksService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  /**
   * List bookmarks for a user with optional filtering and sorting
   */
  async listBookmarks(
    userId: string,
    params: BookmarkQueryParams = {}
  ): Promise<PaginatedResult<BookmarkWithContent>> {
    const searchParams = new URLSearchParams()
    searchParams.set('user_id', userId)

    if (params.skip !== undefined) {
      searchParams.set('skip', String(params.skip))
    }

    if (params.limit !== undefined) {
      searchParams.set('limit', String(params.limit))
    }

    if (params.pinned !== undefined) {
      searchParams.set('pinned', String(params.pinned))
    }

    if (params.isPublic !== undefined) {
      searchParams.set('is_public', String(params.isPublic))
    }

    if (params.categoryId) {
      searchParams.set('category_id', params.categoryId)
    }

    if (params.sortField) {
      searchParams.set('sort_field', params.sortField)
    }

    if (params.sortOrder) {
      searchParams.set('sort_order', params.sortOrder)
    }

    if (params.includeContent !== undefined) {
      searchParams.set('include_content', String(params.includeContent))
    }

    const query = searchParams.toString()

    const response = await this.api.get<ApiBookmarkListResponse>(
      `/api/v1/bookmarks?${query}`
    )

    return {
      items: response.items.map((item) => this.transformBookmarkWithContent(item)),
      total: response.total,
      limit: response.limit,
      skip: response.skip,
    }
  }

  /**
   * Get a single bookmark by ID
   */
  async getBookmark(bookmarkId: string, userId: string): Promise<BookmarkWithContent> {
    const response = await this.api.get<ApiBookmarkWithContent>(
      `/api/v1/bookmarks/${bookmarkId}?user_id=${userId}`
    )

    return this.transformBookmarkWithContent(response)
  }

  /**
   * Transform API bookmark with content to domain model
   */
  private transformBookmarkWithContent(item: ApiBookmarkWithContent): BookmarkWithContent {
    return {
      id: item.id,
      userId: item.user_id,
      contentId: item.content_id,
      contentSourceType: item.content_source_type,
      note: item.note,
      pinned: item.pinned,
      isPublic: item.is_public,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      content: item.content ? this.transformContentItem(item.content) : null,
      userRating: item.user_rating,
    }
  }

  /**
   * Transform API content item to domain GalleryItem
   */
  private transformContentItem(item: {
    id: number
    title: string
    description?: string | null
    image_url?: string | null
    path_thumb?: string | null
    path_thumbs_alt_res?: Record<string, string> | null
    content_data: string
    content_type: string
    prompt?: string | null
    quality_score: number | null
    created_at: string
    updated_at?: string
    creator_id: string
    tags: string[]
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
      updatedAt: item.updated_at ?? item.created_at,
      creatorId: item.creator_id,
      creatorUsername: null,  // Not included in bookmark content response
      tags: item.tags ?? [],
      itemMetadata: null,
      sourceType: 'regular',  // Will be 'items' or 'auto' from contentSourceType
    }
  }
}
