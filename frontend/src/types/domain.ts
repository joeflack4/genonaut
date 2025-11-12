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
  pathThumb: string | null
  pathThumbsAltRes: Record<string, string> | null  // Alternate resolution thumbnails keyed by resolution
  contentData: string | null
  contentType: string
  prompt: string | null
  qualityScore: number | null
  createdAt: string
  updatedAt: string
  creatorId: string  // UUID
  creatorUsername: string | null
  tags: string[]
  itemMetadata: Record<string, unknown> | null
  sourceType: 'regular' | 'auto'
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

export type ThumbnailResolutionId =
  | '512x768'
  | '460x691'
  | '410x614'
  | '358x538'
  | '307x461'
  | '256x384'
  | '232x344'
  | '200x304'
  | '184x272'
  | '152x232'

export type ViewMode = 'list' | `grid-${ThumbnailResolutionId}`

export interface ThumbnailResolution {
  id: ThumbnailResolutionId
  width: number
  height: number
  label: string
  scale?: number
}

export interface CheckpointModel {
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
  modelMetadata: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export interface LoraModel {
  id: string  // UUID
  path: string
  filename: string | null
  name: string | null
  version: string | null
  compatibleArchitectures: string | null
  family: string | null
  description: string | null
  rating: number | null
  tags: string[]
  triggerWords: string[]
  optimalCheckpoints: string[]
  modelMetadata: Record<string, unknown>
  createdAt: string
  updatedAt: string
  isCompatible?: boolean | null
  isOptimal?: boolean | null
}

export interface LoraModelPaginationMeta {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface PaginatedLoraModels {
  items: LoraModel[]
  total: number
  pagination: LoraModelPaginationMeta
}

// Bookmark domain types
export interface Bookmark {
  id: string  // UUID
  userId: string  // UUID
  contentId: number
  contentSourceType: string  // 'items' or 'auto'
  note: string | null
  pinned: boolean
  isPublic: boolean
  createdAt: string
  updatedAt: string
}

export interface BookmarkWithContent extends Bookmark {
  content: GalleryItem | null
  userRating: number | null  // 1-5 scale
}

export interface BookmarkCategory {
  id: string  // UUID
  userId: string  // UUID
  name: string
  description: string | null
  color: string | null
  icon: string | null
  coverContentId: number | null
  coverContentSourceType: string | null
  parentId: string | null  // UUID
  sortIndex: number | null
  isPublic: boolean
  shareToken: string | null  // UUID
  createdAt: string
  updatedAt: string
}

export interface BookmarkCategoryCreateRequest {
  name: string
  description?: string
  color?: string
  icon?: string
  parentId?: string  // UUID
  isPublic?: boolean
}

export interface BookmarkCategoryUpdateRequest {
  name?: string
  description?: string
  color?: string
  icon?: string
  parentId?: string  // UUID
  sortIndex?: number
  isPublic?: boolean
}

export interface BookmarkQueryParams {
  skip?: number
  limit?: number
  pinned?: boolean
  isPublic?: boolean
  categoryId?: string  // UUID
  sortField?: string
  sortOrder?: 'asc' | 'desc'
  includeContent?: boolean
}

export interface BookmarkCategoryQueryParams {
  skip?: number
  limit?: number
  parentId?: string | null  // UUID
  isPublic?: boolean
  sortField?: string
  sortOrder?: 'asc' | 'desc'
}
