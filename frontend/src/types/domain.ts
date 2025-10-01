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
  tag?: string | string[]  // Tag filter - single tag or multiple tags
}

// Flagged Content Types
export interface FlaggedContent {
  id: number
  contentItemId: number | null
  contentItemAutoId: number | null
  contentSource: 'regular' | 'auto'
  flaggedText: string
  flaggedWords: string[]
  totalProblemWords: number
  totalWords: number
  problemPercentage: number
  riskScore: number
  creatorId: string
  flaggedAt: string
  reviewed: boolean
  reviewedAt: string | null
  reviewedBy: string | null
  notes: string | null
}

export interface FlaggedContentFilters extends PaginationParams {
  creatorId?: string
  contentSource?: 'regular' | 'auto' | 'all'
  minRiskScore?: number
  maxRiskScore?: number
  reviewed?: boolean
}

export interface ScanRequest {
  contentTypes: ('regular' | 'auto')[]
  forceRescan: boolean
}

export interface ScanResponse {
  itemsScanned: number
  itemsFlagged: number
  processingTimeMs: number
}

export interface ReviewRequest {
  reviewed: boolean
  reviewedBy: string
  notes?: string
}

export interface BulkDeleteRequest {
  ids: number[]
}

export interface BulkDeleteResponse {
  deletedCount: number
  errors: Array<{
    id: number
    error: string
  }>
}

export interface FlaggedContentStats {
  totalFlagged: number
  unreviewedCount: number
  averageRiskScore: number
  highRiskCount: number
  bySource: {
    regular: number
    auto: number
  }
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
