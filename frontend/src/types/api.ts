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

export interface ApiContentQueryParams {
  skip?: number
  limit?: number
  search?: string
  sort?: 'recent' | 'top-rated'
  creator_id?: string  // UUID
}
