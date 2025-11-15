import { ApiClient } from './api-client'
import type {
  ApiBookmarkWithContent,
  ApiBookmarkListResponse,
  ApiBookmarkQueryParams,
  ApiBookmark,
  ApiCategoryMembershipListResponse
} from '../types/api'
import type {
  BookmarkWithContent,
  PaginatedResult,
  BookmarkQueryParams,
  GalleryItem,
  Bookmark
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
   * Check if a content item is bookmarked by the user
   * Returns the bookmark if it exists, null otherwise
   */
  async checkBookmarkStatus(
    userId: string,
    contentId: number,
    contentSourceType: string = 'items'
  ): Promise<Bookmark | null> {
    const response = await this.api.get<{
      bookmarked: boolean
      bookmark: ApiBookmark | null
    }>(
      `/api/v1/bookmarks/check?user_id=${userId}&content_id=${contentId}&content_source_type=${contentSourceType}`
    )

    // If not bookmarked, return null
    if (!response.bookmarked || !response.bookmark) {
      return null
    }

    // Transform to Bookmark
    return {
      id: response.bookmark.id,
      userId: response.bookmark.user_id,
      contentId: response.bookmark.content_id,
      contentSourceType: response.bookmark.content_source_type,
      note: response.bookmark.note,
      pinned: response.bookmark.pinned,
      isPublic: response.bookmark.is_public,
      createdAt: response.bookmark.created_at,
      updatedAt: response.bookmark.updated_at,
    }
  }

  /**
   * Check bookmark status for multiple content items in a single batch request
   * Returns a map of 'contentId-sourceType' to bookmark status
   */
  async checkBookmarkStatusBatch(
    userId: string,
    contentItems: Array<{ contentId: number; contentSourceType: string }>
  ): Promise<Record<string, Bookmark | null>> {
    const response = await this.api.post<{
      bookmarks: Record<string, ApiBookmark | null>
    }>(
      `/api/v1/bookmarks/check-batch?user_id=${userId}`,
      {
        content_items: contentItems.map(item => ({
          content_id: item.contentId,
          content_source_type: item.contentSourceType
        }))
      }
    )

    // Transform API bookmarks to domain Bookmarks
    const result: Record<string, Bookmark | null> = {}
    for (const [key, apiBookmark] of Object.entries(response.bookmarks)) {
      if (apiBookmark) {
        result[key] = {
          id: apiBookmark.id,
          userId: apiBookmark.user_id,
          contentId: apiBookmark.content_id,
          contentSourceType: apiBookmark.content_source_type,
          note: apiBookmark.note,
          pinned: apiBookmark.pinned,
          isPublic: apiBookmark.is_public,
          createdAt: apiBookmark.created_at,
          updatedAt: apiBookmark.updated_at,
        }
      } else {
        result[key] = null
      }
    }

    return result
  }

  /**
   * Create a new bookmark
   */
  async createBookmark(
    userId: string,
    contentId: number,
    contentSourceType: string = 'items',
    options: {
      note?: string
      pinned?: boolean
      isPublic?: boolean
    } = {}
  ): Promise<Bookmark> {
    const response = await this.api.post<ApiBookmark>(
      `/api/v1/bookmarks?user_id=${userId}`,
      {
        content_id: contentId,
        content_source_type: contentSourceType,
        note: options.note,
        pinned: options.pinned ?? false,
        is_public: options.isPublic ?? false,
      }
    )

    return {
      id: response.id,
      userId: response.user_id,
      contentId: response.content_id,
      contentSourceType: response.content_source_type,
      note: response.note,
      pinned: response.pinned,
      isPublic: response.is_public,
      createdAt: response.created_at,
      updatedAt: response.updated_at,
    }
  }

  /**
   * Delete a bookmark
   */
  async deleteBookmark(bookmarkId: string, userId: string): Promise<void> {
    await this.api.delete(`/api/v1/bookmarks/${bookmarkId}?user_id=${userId}`)
  }

  /**
   * Sync bookmark category memberships
   * Updates all category memberships for a bookmark in a single operation
   */
  async syncCategories(
    bookmarkId: string,
    userId: string,
    categoryIds: string[]
  ): Promise<void> {
    await this.api.put(
      `/api/v1/bookmarks/${bookmarkId}/categories/sync?user_id=${userId}`,
      {
        category_ids: categoryIds,
      }
    )
  }

  /**
   * Get all categories that a bookmark belongs to
   */
  async getBookmarkCategories(bookmarkId: string): Promise<string[]> {
    const response = await this.api.get<ApiCategoryMembershipListResponse>(
      `/api/v1/bookmarks/${bookmarkId}/categories`
    )

    return response.items.map((item) => item.category_id)
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
