export interface ApiUser {
  id: string  // UUID
  name: string
  email: string
  is_active: boolean
  avatar_url?: string | null
  created_at?: string
  updated_at?: string
}

export interface ApiUserUpdateRequest {
  name?: string
  email?: string
  preferences?: Record<string, unknown>
}

export interface ApiUserStats {
  total_recommendations: number
  served_recommendations: number
  generated_content: number
  last_active_at?: string
}

export interface ApiContentItem {
  id: number
  title: string
  description?: string | null
  image_url?: string | null
  path_thumb?: string | null
  quality_score: number | null
  created_at: string
  updated_at?: string
  content_type: string
  content_data: string
  item_metadata: Record<string, any>
  creator_id: string  // UUID
  tags: string[]
  is_public: boolean
  is_private: boolean
}

export interface ApiRecommendationItem {
  id: number
  user_id: string  // UUID
  content_id: number
  algorithm: string
  score: number
  served_at: string | null
  created_at: string
}

export interface ApiPaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  skip: number
}

// Enhanced pagination types for the new API
export interface ApiPaginationMeta {
  page: number
  page_size: number
  total_count: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
  next_cursor?: string | null
  prev_cursor?: string | null
}

export interface ApiEnhancedPaginatedResponse<T> {
  items: T[]
  pagination: ApiPaginationMeta
}

export interface ApiEnhancedPaginationParams {
  page?: number
  page_size?: number
  cursor?: string
  sort_field?: string
  sort_order?: 'asc' | 'desc'
}

export interface ApiContentQueryParams {
  skip?: number
  limit?: number
  search?: string
  sort?: 'recent' | 'top-rated'
  creator_id?: string  // UUID
  tag?: string | string[]  // Tag filter - single tag or multiple tags
}

export interface ApiEnhancedContentQueryParams extends ApiEnhancedPaginationParams {
  content_type?: string
  creator_id?: string
  public_only?: boolean
  search_term?: string
  tag?: string | string[]  // Tag filter - single tag or multiple tags
}

// Flagged Content Types
export interface ApiFlaggedContent {
  id: number
  content_item_id: number | null
  content_item_auto_id: number | null
  content_source: 'regular' | 'auto'
  flagged_text: string
  flagged_words: string[]
  total_problem_words: number
  total_words: number
  problem_percentage: number
  risk_score: number
  creator_id: string  // UUID
  flagged_at: string
  reviewed: boolean
  reviewed_at: string | null
  reviewed_by: string | null  // UUID
  notes: string | null
}

export interface ApiFlaggedContentFilters extends ApiEnhancedPaginationParams {
  creator_id?: string
  content_source?: 'regular' | 'auto' | 'all'
  min_risk_score?: number
  max_risk_score?: number
  reviewed?: boolean
}

export interface ApiScanRequest {
  content_types: ('regular' | 'auto')[]
  force_rescan: boolean
}

export interface ApiScanResponse {
  items_scanned: number
  items_flagged: number
  processing_time_ms: number
}

export interface ApiReviewRequest {
  reviewed: boolean
  reviewed_by: string  // UUID
  notes?: string
}

export interface ApiBulkDeleteRequest {
  ids: number[]
}

export interface ApiBulkDeleteResponse {
  deleted_count: number
  errors: Array<{
    id: number
    error: string
  }>
}

export interface ApiFlaggedContentStats {
  total_flagged: number
  unreviewed_count: number
  average_risk_score: number
  high_risk_count: number
  by_source: {
    regular: number
    auto: number
  }
}

export interface ApiCheckpointModel {
  id: string  // UUID
  path: string
  filename: string | null
  name: string | null
  version: string | null
  architecture: string | null
  family: string | null
  description: string | null
  rating: number | null
  tags: string[]
  model_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ApiCheckpointModelListResponse {
  items: ApiCheckpointModel[]
  total: number
}

export interface ApiLoraModel {
  id: string  // UUID
  path: string
  filename: string | null
  name: string | null
  version: string | null
  compatible_architectures: string | null
  family: string | null
  description: string | null
  rating: number | null
  tags: string[]
  trigger_words: string[]
  optimal_checkpoints: string[]
  model_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
  is_compatible?: boolean | null
  is_optimal?: boolean | null
}

export interface ApiLoraModelPaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ApiLoraModelListResponse {
  items: ApiLoraModel[]
  total: number
  pagination?: ApiLoraModelPaginationMeta
}
