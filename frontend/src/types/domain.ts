export interface User {
  id: number
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
}

export interface RecommendationItem {
  id: number
  userId: number
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
