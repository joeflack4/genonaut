import { ApiClient } from './api-client'
import type {
  ApiBookmarkCategory,
  ApiBookmarkCategoryListResponse,
  ApiBookmarkCategoryQueryParams,
  ApiBookmarkCategoryCreateRequest,
  ApiBookmarkCategoryUpdateRequest,
  ApiBookmarkListResponse,
  ApiBookmarkWithContent
} from '../types/api'
import type {
  BookmarkCategory,
  PaginatedResult,
  BookmarkCategoryQueryParams,
  BookmarkCategoryCreateRequest,
  BookmarkCategoryUpdateRequest,
  BookmarkWithContent,
  BookmarkQueryParams,
  GalleryItem
} from '../types/domain'

export class BookmarkCategoriesService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  /**
   * List categories for a user with optional filtering and sorting
   */
  async listCategories(
    userId: string,
    params: BookmarkCategoryQueryParams = {}
  ): Promise<PaginatedResult<BookmarkCategory>> {
    const searchParams = new URLSearchParams()
    searchParams.set('user_id', userId)

    if (params.skip !== undefined) {
      searchParams.set('skip', String(params.skip))
    }

    if (params.limit !== undefined) {
      searchParams.set('limit', String(params.limit))
    }

    if (params.parentId !== undefined) {
      if (params.parentId === null) {
        searchParams.set('parent_id', 'null')
      } else {
        searchParams.set('parent_id', params.parentId)
      }
    }

    if (params.isPublic !== undefined) {
      searchParams.set('is_public', String(params.isPublic))
    }

    if (params.sortField) {
      searchParams.set('sort_field', params.sortField)
    }

    if (params.sortOrder) {
      searchParams.set('sort_order', params.sortOrder)
    }

    const query = searchParams.toString()

    const response = await this.api.get<ApiBookmarkCategoryListResponse>(
      `/api/v1/bookmark-categories?${query}`
    )

    return {
      items: response.items.map((item) => this.transformCategory(item)),
      total: response.total,
      limit: response.limit,
      skip: response.skip,
    }
  }

  /**
   * Get a single category by ID
   */
  async getCategory(categoryId: string, userId: string): Promise<BookmarkCategory> {
    const response = await this.api.get<ApiBookmarkCategory>(
      `/api/v1/bookmark-categories/${categoryId}?user_id=${userId}`
    )

    return this.transformCategory(response)
  }

  /**
   * Get bookmarks in a category
   */
  async getCategoryBookmarks(
    categoryId: string,
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
      `/api/v1/bookmark-categories/${categoryId}/bookmarks?${query}`
    )

    return {
      items: response.items.map((item) => this.transformBookmarkWithContent(item)),
      total: response.total,
      limit: response.limit,
      skip: response.skip,
    }
  }

  /**
   * Create a new category
   */
  async createCategory(
    userId: string,
    data: BookmarkCategoryCreateRequest
  ): Promise<BookmarkCategory> {
    const apiData: ApiBookmarkCategoryCreateRequest = {
      name: data.name,
      description: data.description,
      color: data.color,
      icon: data.icon,
      parent_id: data.parentId,
      is_public: data.isPublic,
    }

    const response = await this.api.post<ApiBookmarkCategory>(
      `/api/v1/bookmark-categories?user_id=${userId}`,
      apiData
    )

    return this.transformCategory(response)
  }

  /**
   * Update an existing category
   */
  async updateCategory(
    categoryId: string,
    userId: string,
    data: BookmarkCategoryUpdateRequest
  ): Promise<BookmarkCategory> {
    // Build API request, converting undefined to null so JSON.stringify preserves all fields
    const apiData: ApiBookmarkCategoryUpdateRequest = {
      name: data.name ?? null,
      description: data.description ?? null,
      color: data.color ?? null,
      icon: data.icon ?? null,
      parent_id: data.parentId ?? null,
      sort_index: data.sortIndex ?? null,
      is_public: data.isPublic ?? null,
    }

    const response = await this.api.put<ApiBookmarkCategory>(
      `/api/v1/bookmark-categories/${categoryId}?user_id=${userId}`,
      apiData
    )

    return this.transformCategory(response)
  }

  /**
   * Delete a category with optional bookmark migration
   */
  async deleteCategory(
    categoryId: string,
    userId: string,
    targetCategoryId?: string | null,
    deleteAll?: boolean
  ): Promise<void> {
    const params = new URLSearchParams()
    params.set('user_id', userId)

    if (targetCategoryId) {
      params.set('target_category_id', targetCategoryId)
    }

    if (deleteAll !== undefined) {
      params.set('delete_all', String(deleteAll))
    }

    await this.api.delete(`/api/v1/bookmark-categories/${categoryId}?${params.toString()}`)
  }

  /**
   * Transform API category to domain model
   */
  private transformCategory(item: ApiBookmarkCategory): BookmarkCategory {
    return {
      id: item.id,
      userId: item.user_id,
      name: item.name,
      description: item.description,
      color: item.color,
      icon: item.icon,
      coverContentId: item.cover_content_id,
      coverContentSourceType: item.cover_content_source_type,
      parentId: item.parent_id,
      sortIndex: item.sort_index,
      isPublic: item.is_public,
      shareToken: item.share_token,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
    }
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
