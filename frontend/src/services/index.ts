import { ApiClient } from './api-client'
import { GalleryService } from './gallery-service'
import { GalleryAutoService } from './gallery-auto-service'
import { UnifiedGalleryService } from './unified-gallery-service'
import { RecommendationService } from './recommendation-service'
import { UserService } from './user-service'
import { ComfyUIService } from './comfyui-service'
import { FlaggedContentService } from './flagged-content-service'

const apiClient = new ApiClient()

export const userService = new UserService(apiClient)
export const galleryService = new GalleryService(apiClient)
export const galleryAutoService = new GalleryAutoService(apiClient)
export const unifiedGalleryService = new UnifiedGalleryService(apiClient)
export const recommendationService = new RecommendationService(apiClient)
export const comfyUIService = new ComfyUIService(apiClient)
export const flaggedContentService = new FlaggedContentService(apiClient)

export type { GalleryListParams } from './gallery-service'
export type { GalleryAutoListParams } from './gallery-auto-service'
export type {
  ComfyUIGenerationCreateRequest,
  ComfyUIGenerationResponse,
  ComfyUIGenerationListParams,
  LoraModel,
  SamplerParams,
  AvailableModel
} from './comfyui-service'
