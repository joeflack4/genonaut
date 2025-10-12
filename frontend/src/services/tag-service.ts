import { ApiClient } from './api-client'
import type {
  ApiTag,
  ApiTagHierarchy,
  ApiTagStatistics,
  ApiTagDetail,
  ApiTagRating,
  ApiTagRatingValue,
  ApiTagUserRatings,
  ApiEnhancedPaginatedResponse,
  ApiPaginationMeta
} from '../types/api'

export type TagSortOption =
  | 'name-asc'
  | 'name-desc'
  | 'created-asc'
  | 'created-desc'
  | 'updated-asc'
  | 'updated-desc'
  | 'rating-asc'
  | 'rating-desc'

export interface TagListParams {
  page?: number
  page_size?: number
  sort?: TagSortOption
  search?: string
  min_ratings?: number
}

export interface TagSearchParams {
  q: string
  page?: number
  page_size?: number
  sort?: TagSortOption
  min_ratings?: number
}

export interface TagRateParams {
  user_id: string
  rating: number
}

export interface TagFavoriteParams {
  user_id: string
}

export interface TagRatingsParams {
  user_id: string
  tag_ids: string[]
}

export class TagService {
  private readonly api: ApiClient

  constructor(api: ApiClient) {
    this.api = api
  }

  // Hierarchy Endpoints

  async getTagHierarchy(includeRatings: boolean = false): Promise<ApiTagHierarchy> {
    const params = new URLSearchParams()
    if (includeRatings) {
      params.set('include_ratings', 'true')
    }

    const query = params.toString()
    return this.api.get<ApiTagHierarchy>(
      `/api/v1/tags/hierarchy${query ? `?${query}` : ''}`
    )
  }

  async getTagStatistics(): Promise<ApiTagStatistics> {
    return this.api.get<ApiTagStatistics>('/api/v1/tags/statistics')
  }

  async getRootTags(): Promise<ApiTag[]> {
    return this.api.get<ApiTag[]>('/api/v1/tags/roots')
  }

  // Tag CRUD Endpoints

  async listTags(params: TagListParams = {}): Promise<ApiEnhancedPaginatedResponse<ApiTag>> {
    const searchParams = new URLSearchParams()

    if (params.page !== undefined) {
      searchParams.set('page', String(params.page))
    }

    if (params.page_size !== undefined) {
      searchParams.set('page_size', String(params.page_size))
    }

    if (params.sort) {
      searchParams.set('sort', params.sort)
    }

    if (params.search) {
      searchParams.set('search', params.search)
    }

    if (params.min_ratings !== undefined) {
      searchParams.set('min_ratings', String(params.min_ratings))
    }

    const query = searchParams.toString()
    return this.api.get<ApiEnhancedPaginatedResponse<ApiTag>>(
      `/api/v1/tags${query ? `?${query}` : ''}`
    )
  }

  async searchTags(params: TagSearchParams): Promise<ApiEnhancedPaginatedResponse<ApiTag>> {
    const searchParams = new URLSearchParams()
    searchParams.set('q', params.q)

    if (params.page !== undefined) {
      searchParams.set('page', String(params.page))
    }

    if (params.page_size !== undefined) {
      searchParams.set('page_size', String(params.page_size))
    }

    if (params.sort) {
      searchParams.set('sort', params.sort)
    }

    if (params.min_ratings !== undefined) {
      searchParams.set('min_ratings', String(params.min_ratings))
    }

    const query = searchParams.toString()
    return this.api.get<ApiEnhancedPaginatedResponse<ApiTag>>(
      `/api/v1/tags/search?${query}`
    )
  }

  async getTagDetail(tagId: string, userId?: string): Promise<ApiTagDetail> {
    const params = new URLSearchParams()
    if (userId) {
      params.set('user_id', userId)
    }

    const query = params.toString()
    return this.api.get<ApiTagDetail>(
      `/api/v1/tags/${tagId}${query ? `?${query}` : ''}`
    )
  }

  async getTagChildren(tagId: string): Promise<ApiTag[]> {
    return this.api.get<ApiTag[]>(`/api/v1/tags/${tagId}/children`)
  }

  async getTagParents(tagId: string): Promise<ApiTag[]> {
    return this.api.get<ApiTag[]>(`/api/v1/tags/${tagId}/parents`)
  }

  // Rating Endpoints

  async rateTag(tagId: string, params: TagRateParams): Promise<ApiTagRating> {
    const searchParams = new URLSearchParams()
    searchParams.set('user_id', params.user_id)
    searchParams.set('rating', String(params.rating))

    return this.api.post<ApiTagRating>(
      `/api/v1/tags/${tagId}/rate?${searchParams.toString()}`
    )
  }

  async deleteTagRating(tagId: string, userId: string): Promise<{ success: boolean; message: string }> {
    const params = new URLSearchParams()
    params.set('user_id', userId)

    return this.api.delete<{ success: boolean; message: string }>(
      `/api/v1/tags/${tagId}/rate?${params.toString()}`
    )
  }

  async getUserTagRating(tagId: string, userId: string): Promise<ApiTagRatingValue> {
    const params = new URLSearchParams()
    params.set('user_id', userId)

    return this.api.get<ApiTagRatingValue>(
      `/api/v1/tags/${tagId}/rating?${params.toString()}`
    )
  }

  async getUserTagRatings(params: TagRatingsParams): Promise<ApiTagUserRatings> {
    const searchParams = new URLSearchParams()
    searchParams.set('user_id', params.user_id)
    params.tag_ids.forEach(id => searchParams.append('tag_ids', id))

    return this.api.get<ApiTagUserRatings>(
      `/api/v1/tags/ratings?${searchParams.toString()}`
    )
  }

  // Favorites Endpoints

  async getUserFavorites(userId: string): Promise<ApiTag[]> {
    const params = new URLSearchParams()
    params.set('user_id', userId)

    return this.api.get<ApiTag[]>(`/api/v1/tags/favorites?${params.toString()}`)
  }

  async addFavorite(tagId: string, params: TagFavoriteParams): Promise<{ success: boolean; message: string }> {
    const searchParams = new URLSearchParams()
    searchParams.set('user_id', params.user_id)

    return this.api.post<{ success: boolean; message: string }>(
      `/api/v1/tags/${tagId}/favorite?${searchParams.toString()}`
    )
  }

  async removeFavorite(tagId: string, params: TagFavoriteParams): Promise<{ success: boolean; message: string }> {
    const searchParams = new URLSearchParams()
    searchParams.set('user_id', params.user_id)

    return this.api.delete<{ success: boolean; message: string }>(
      `/api/v1/tags/${tagId}/favorite?${searchParams.toString()}`
    )
  }
}
