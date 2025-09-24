export interface User {
  id: string  // UUID
  name: string
  email: string
  isActive: boolean
  avatarUrl?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface UserStats {
  totalRecommendations: number
  servedRecommendations: number
  generatedContent: number
  lastActiveAt?: string
}

export interface GalleryItem {
  id: number
  title: string
  description: string | null
  imageUrl: string | null
  qualityScore: number | null
  createdAt: string
  updatedAt: string
  creatorId: string  // UUID
}

export interface RecommendationItem {
  id: number
  userId: string  // UUID
  contentId: number
  algorithm: string
  score: number
  servedAt: string | null
  createdAt: string
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  limit: number
  skip: number
}

// Enhanced pagination types for the new system
export interface PaginationMeta {
  page: number
  pageSize: number
  totalCount: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
  nextCursor?: string | null
  prevCursor?: string | null
}

export interface EnhancedPaginatedResult<T> {
  items: T[]
  pagination: PaginationMeta
}

export interface PaginationParams {
  page?: number
  pageSize?: number
  cursor?: string
  sortField?: string
  sortOrder?: 'asc' | 'desc'
}

// Content-specific pagination parameters
export interface ContentQueryParams extends PaginationParams {
  contentType?: string
  creatorId?: string
  publicOnly?: boolean
  searchTerm?: string
}
